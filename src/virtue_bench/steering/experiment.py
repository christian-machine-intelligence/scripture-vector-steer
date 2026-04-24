"""Iconoclast activation-space experiment orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..analysis.iconoclast import compare_paired_results
from ..analysis.discernment import retroactive_discernment_eval
from ..artifacts.results import write_results
from ..core.loader import load_scenarios
from ..core.psalms import build_psalm_family_target, load_psalm_text, parse_psalm_family_target
from ..core.schema import RunResult
from ..eval.experiment import RESULTS_DIR, run_single_condition
from ..stats.bootstrap import aggregate_runs
from .corpora import (
    POOLED_VIRTUE_TARGET,
    SCRIPTURE_FAMILY_TARGETS,
    build_length_matched_control,
    list_steering_targets,
    load_steering_corpus,
    select_corpus_texts,
)
from .extract import extract_virtue_vectors, load_vector_artifact, save_vector_artifact
from .runtime import SteeringRuntime


STEERING_CONDITIONS = {
    "virtue_steer",
    "combined",
    "null_control",
    "christian_steer",
    "christian_null_control",
    "scripture_steer",
    "scripture_null_control",
}
DEFAULT_CONDITIONS = [
    "control",
    "psalm_baseline",
    "virtue_steer",
    "christian_steer",
    "combined",
    "null_control",
    "christian_null_control",
    "scripture_steer",
    "scripture_null_control",
    "length_control",
]


@dataclass
class IconoclastConfig:
    """Configuration for the activation-space virtue experiment."""

    name: str
    model: str
    virtues: List[str] = field(default_factory=lambda: ["prudence", "justice", "courage", "temperance"])
    variants: List[str] = field(default_factory=lambda: ["ratio", "caro", "mundus", "diabolus", "ignatian"])
    conditions: List[str] = field(default_factory=lambda: list(DEFAULT_CONDITIONS))
    runs: int = 10
    temperature: float = 0.7
    seed: int = 42
    limit: Optional[int] = None
    detailed: bool = True
    concurrency: int = 1
    retries: int = 0
    timeout: int = 120
    stage: str = "all"
    cross_matrix: bool = False
    discernment: bool = False
    corpus_path: Optional[str] = None
    vector_path: Optional[str] = None
    steering_targets: Optional[List[str]] = None
    scripture_targets: List[str] = field(default_factory=lambda: list(SCRIPTURE_FAMILY_TARGETS))
    psalm_family_lanes: List[str] = field(default_factory=list)
    include_merged_psalm_family_lane: bool = False
    pooled_virtue_steer: bool = False
    extraction_method: str = "auto"
    max_length: int = 256
    window_radius: int = 3
    alpha_candidates: List[float] = field(default_factory=lambda: [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0])
    virtue_alpha_scale: float = 1.0
    christian_alpha_scale: float = 1.0
    scripture_alpha_scale: float = 1.0
    psalm_family_alpha_scales: Dict[str, float] = field(default_factory=dict)
    merged_psalm_family_alpha_scale: Optional[float] = None
    psalm_sets: List[str] = field(default_factory=lambda: ["random_baseline"])
    psalm_random: Optional[int] = None
    psalm_vector_sets: List[str] = field(default_factory=list)
    window_center: Optional[int] = None
    enable_thinking: bool = False
    preflight_variant: str = "ratio"
    preflight_limit: int = 8
    preflight_max_tokens: int = 32
    preflight_timeout: int = 45
    preflight_alpha_scale: float = 6.0
    preflight_max_alpha: float = 12.0
    preflight_policy: str = "error"
    output_prefix: str = "iconoclast"


def _stage_order(stage: str) -> List[str]:
    if stage == "all":
        return ["smoke", "ratio", "full"]
    return [stage]


def _variant_selection(config: IconoclastConfig, stage: str) -> List[str]:
    if stage in {"smoke", "ratio"}:
        return ["ratio"]
    return list(config.variants)


def _run_count(config: IconoclastConfig, stage: str) -> int:
    if stage == "smoke":
        return 1
    return config.runs


def _temperature(config: IconoclastConfig, stage: str) -> float:
    if stage == "smoke":
        return 0.0
    return config.temperature


def _virtue_steering_targets(config: IconoclastConfig, stage: str, eval_virtue: str) -> List[str]:
    if config.pooled_virtue_steer:
        return [POOLED_VIRTUE_TARGET]
    if stage == "smoke" or not config.cross_matrix:
        return [eval_virtue]
    return list(config.virtues)


def _psalm_family_lane_targets(config: IconoclastConfig) -> List[str]:
    lane_targets = [build_psalm_family_target([family]) for family in config.psalm_family_lanes]
    if config.include_merged_psalm_family_lane:
        if len(config.psalm_family_lanes) < 2:
            raise ValueError(
                "include_merged_psalm_family_lane requires at least two psalm_family_lanes"
            )
        lane_targets.append(build_psalm_family_target(config.psalm_family_lanes))
    return list(dict.fromkeys(lane_targets))


def _scripture_steering_targets(config: IconoclastConfig) -> List[str]:
    configured = list(config.scripture_targets)
    configured.extend(_psalm_family_lane_targets(config))
    ordered = list(dict.fromkeys(configured))
    return ordered or list(SCRIPTURE_FAMILY_TARGETS)


def _steering_targets(config: IconoclastConfig, stage: str, eval_virtue: str, condition: str) -> List[Optional[str]]:
    if condition not in STEERING_CONDITIONS:
        return [None]
    if condition in {"christian_steer", "christian_null_control"}:
        return ["christian"]
    if condition in {"scripture_steer", "scripture_null_control"}:
        return _scripture_steering_targets(config)
    return _virtue_steering_targets(config, stage, eval_virtue)


def _condition_label(condition: str, steering_virtue: Optional[str]) -> str:
    if steering_virtue is None or condition not in STEERING_CONDITIONS:
        return condition
    return f"{condition}:{steering_virtue}"


def _condition_alpha_scale(
    config: IconoclastConfig,
    condition: str,
    steering_target: Optional[str] = None,
) -> float:
    if condition in {"virtue_steer", "combined", "null_control"}:
        return config.virtue_alpha_scale
    if condition in {"christian_steer", "christian_null_control"}:
        return config.christian_alpha_scale
    if condition in {"scripture_steer", "scripture_null_control"}:
        if steering_target is not None:
            psalm_families = parse_psalm_family_target(steering_target)
            if psalm_families is not None:
                if len(psalm_families) == 1:
                    return config.psalm_family_alpha_scales.get(
                        psalm_families[0],
                        config.scripture_alpha_scale,
                    )
                if config.merged_psalm_family_alpha_scale is not None:
                    return config.merged_psalm_family_alpha_scale
        return config.scripture_alpha_scale
    return 1.0


def _requested_vector_targets(config: IconoclastConfig, corpus_records) -> List[str]:
    available_targets = list_steering_targets(corpus_records)
    requested_targets = list(config.steering_targets or [])
    if not requested_targets:
        if any(condition in {"virtue_steer", "combined", "null_control"} for condition in config.conditions):
            if config.pooled_virtue_steer:
                requested_targets.append(POOLED_VIRTUE_TARGET)
            else:
                requested_targets.extend(config.virtues)
        if any(condition in {"christian_steer", "christian_null_control"} for condition in config.conditions):
            requested_targets.append("christian")
        if any(condition in {"scripture_steer", "scripture_null_control"} for condition in config.conditions):
            requested_targets.extend(_scripture_steering_targets(config))

    ordered = []
    for target in requested_targets:
        if (
            target in available_targets
            or target == POOLED_VIRTUE_TARGET
            or parse_psalm_family_target(target) is not None
        ) and target not in ordered:
            ordered.append(target)
    if ordered:
        return ordered

    if config.pooled_virtue_steer:
        return [POOLED_VIRTUE_TARGET]
    fallback = [target for target in config.virtues if target in available_targets]
    return fallback or list(config.virtues)


def _preflight_families(config: IconoclastConfig) -> List[Tuple[str, str, str]]:
    families: List[Tuple[str, str, str]] = []
    if any(condition in {"virtue_steer", "combined", "null_control"} for condition in config.conditions):
        families.append(("virtue_steer", "null_control", "virtue"))
    if any(condition in {"christian_steer", "christian_null_control"} for condition in config.conditions):
        families.append(("christian_steer", "christian_null_control", "christian"))
    if any(condition in {"scripture_steer", "scripture_null_control"} for condition in config.conditions):
        families.append(("scripture_steer", "scripture_null_control", "scripture"))
    return families


def _artifact_to_runtime(
    artifact: dict,
    virtue: str,
    *,
    use_null: bool,
    alpha_scale: float = 1.0,
) -> SteeringRuntime:
    virtue_payload = artifact["virtues"][virtue]
    vector_key = "null_vectors" if use_null else "layer_vectors"
    vectors = {
        int(layer): tensor
        for layer, tensor in virtue_payload[vector_key].items()
    }
    return SteeringRuntime(
        layer_vectors=vectors,
        alpha=float(virtue_payload["alpha"]) * alpha_scale,
        # VirtueBench scoring depends on the model's first generated token.
        # If we skip the prompt prefill pass, steering may never influence the
        # exact token the benchmark reads as the answer.
        skip_prefill=False,
    )


def _scaled_runtime(
    artifact: dict,
    virtue: str,
    *,
    use_null: bool,
    alpha_scale: float,
) -> SteeringRuntime:
    return _artifact_to_runtime(
        artifact,
        virtue,
        use_null=use_null,
        alpha_scale=alpha_scale,
    )


def _preflight_scales(
    *,
    base_alpha: float,
    initial_scale: float,
    max_alpha: float,
) -> List[float]:
    if base_alpha <= 0:
        return [initial_scale]

    scales = []
    scale = initial_scale
    max_scale = max(initial_scale, max_alpha / base_alpha)
    while scale < max_scale:
        scales.append(scale)
        scale *= 2.0
    scales.append(max_scale)

    ordered = []
    seen = set()
    for value in scales:
        rounded = round(value, 6)
        if rounded in seen:
            continue
        seen.add(rounded)
        ordered.append(rounded)
    return ordered


def _deviation_points(virtues: List[str]) -> Dict[str, str]:
    points: Dict[str, str] = {}
    for virtue in virtues:
        for scenario in load_scenarios(virtue, variants=["ignatian"]):
            if scenario.deviation_point:
                points[scenario.base_id] = scenario.deviation_point
    return points


def _stage_paths(config: IconoclastConfig, stage: str) -> Tuple[Path, Path, Path]:
    output_path = RESULTS_DIR / f"{config.output_prefix}_{stage}.json"
    checkpoint_path = RESULTS_DIR / f"{config.output_prefix}_{stage}_checkpoint.json"
    status_path = RESULTS_DIR / f"{config.output_prefix}_{stage}.status.json"
    return output_path, checkpoint_path, status_path


def _preflight_path(config: IconoclastConfig) -> Path:
    return RESULTS_DIR / f"{config.output_prefix}_preflight.json"


def _run_status_path(config: IconoclastConfig) -> Path:
    return RESULTS_DIR / f"{config.output_prefix}_run.status.json"


def _vector_diagnostics_json_path(config: IconoclastConfig) -> Path:
    return RESULTS_DIR / f"{config.output_prefix}_vector_diagnostics.json"


def _vector_diagnostics_md_path(config: IconoclastConfig) -> Path:
    return RESULTS_DIR / f"{config.output_prefix}_vector_diagnostics.md"


def _run_artifact_paths(config: IconoclastConfig, vector_path: Path) -> Dict[str, str]:
    return {
        "console_log": str(RESULTS_DIR / f"{config.output_prefix}_console.log"),
        "preflight": str(_preflight_path(config)),
        "run_status": str(_run_status_path(config)),
        "vector_artifact": str(vector_path),
        "vector_diagnostics_json": str(_vector_diagnostics_json_path(config)),
        "vector_diagnostics_md": str(_vector_diagnostics_md_path(config)),
    }


def _coerce_numeric_key(value: float):
    if float(value).is_integer():
        return int(value)
    return float(value)


def _top_metric_entries(metric_map: Dict[str, object], *, entry_name: str, limit: int = 5) -> List[Dict[str, float]]:
    entries: List[Tuple[float, float]] = []
    for raw_key, raw_value in (metric_map or {}).items():
        try:
            numeric_key = float(raw_key)
            numeric_value = float(raw_value)
        except (TypeError, ValueError):
            continue
        entries.append((numeric_key, numeric_value))
    entries.sort(key=lambda item: (item[1], item[0]), reverse=True)
    return [
        {entry_name: _coerce_numeric_key(numeric_key), "score": numeric_value}
        for numeric_key, numeric_value in entries[:limit]
    ]


def _top_target_entries(artifact: dict, metric_name: str, *, limit: int = 5) -> List[Dict[str, float]]:
    ranked: List[Tuple[str, float]] = []
    for target, payload in artifact.get("virtues", {}).items():
        value = payload.get(metric_name)
        if value is None:
            continue
        try:
            ranked.append((target, float(value)))
        except (TypeError, ValueError):
            continue
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [
        {"target": target, "score": score}
        for target, score in ranked[:limit]
    ]


def _vector_diagnostics_payload(artifact: dict) -> dict:
    targets = artifact.get("virtues", {})
    summaries = []
    for target, payload in targets.items():
        summaries.append(
            {
                "target": target,
                "extraction_method_used": payload.get("extraction_method_used"),
                "source_mode": payload.get("source_mode"),
                "background_mode": payload.get("background_mode"),
                "psalm_vector_sets": payload.get("psalm_vector_sets"),
                "psalm_families": payload.get("psalm_families"),
                "best_layer": payload.get("best_layer"),
                "best_layer_selection": payload.get("best_layer_selection"),
                "layer_selection_candidates": payload.get("layer_selection_candidates"),
                "layer_window": payload.get("layer_window"),
                "alpha": payload.get("alpha"),
                "alpha_selection": payload.get("alpha_selection"),
                "alpha_selection_candidates": payload.get("alpha_selection_candidates"),
                "train_examples": payload.get("train_examples"),
                "dev_examples": payload.get("dev_examples"),
                "test_examples": payload.get("test_examples"),
                "other_train_examples": payload.get("other_train_examples"),
                "other_dev_examples": payload.get("other_dev_examples"),
                "other_test_examples": payload.get("other_test_examples"),
                "dev_accuracy": payload.get("dev_accuracy"),
                "dev_margin": payload.get("dev_margin"),
                "dev_specificity": payload.get("dev_specificity"),
                "steered_dev_accuracy": payload.get("steered_dev_accuracy"),
                "steered_dev_margin": payload.get("steered_dev_margin"),
                "steered_dev_specificity": payload.get("steered_dev_specificity"),
                "test_accuracy": payload.get("test_accuracy"),
                "test_margin": payload.get("test_margin"),
                "test_specificity": payload.get("test_specificity"),
                "test_accuracy_steered": payload.get("test_accuracy_steered"),
                "steered_test_margin": payload.get("steered_test_margin"),
                "test_specificity_steered": payload.get("test_specificity_steered"),
                "top_layers_by_dev_accuracy": _top_metric_entries(
                    payload.get("layer_scores", {}),
                    entry_name="layer",
                ),
                "top_layers_by_dev_margin": _top_metric_entries(
                    payload.get("layer_margins", {}),
                    entry_name="layer",
                ),
                "top_alphas_by_dev_accuracy": _top_metric_entries(
                    payload.get("alpha_scores", {}),
                    entry_name="alpha",
                ),
                "top_alphas_by_dev_margin": _top_metric_entries(
                    payload.get("alpha_margins", {}),
                    entry_name="alpha",
                ),
            }
        )

    return {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": artifact.get("model"),
        "artifact_extraction_method": artifact.get("extraction_method"),
        "targets": artifact.get("targets", []),
        "rankings": {
            "by_dev_accuracy": _top_target_entries(artifact, "dev_accuracy"),
            "by_dev_margin": _top_target_entries(artifact, "dev_margin"),
            "by_steered_dev_accuracy": _top_target_entries(artifact, "steered_dev_accuracy"),
            "by_test_accuracy": _top_target_entries(artifact, "test_accuracy"),
            "by_steered_test_margin": _top_target_entries(artifact, "steered_test_margin"),
            "by_test_accuracy_steered": _top_target_entries(artifact, "test_accuracy_steered"),
        },
        "target_summaries": summaries,
    }


def _write_vector_diagnostics(config: IconoclastConfig, artifact: dict) -> None:
    diagnostics = _vector_diagnostics_payload(artifact)
    json_path = _vector_diagnostics_json_path(config)
    md_path = _vector_diagnostics_md_path(config)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")

    lines = [
        f"# Vector Diagnostics: {config.output_prefix}",
        "",
        f"- Model: `{diagnostics.get('model')}`",
        f"- Extraction method: `{diagnostics.get('artifact_extraction_method')}`",
        f"- Targets: `{', '.join(diagnostics.get('targets', []))}`",
        "",
        "## Target Ranking",
    ]

    for label, ranking in diagnostics["rankings"].items():
        pretty_label = label.replace("_", " ")
        lines.append(f"- {pretty_label}: " + ", ".join(
            f"`{item['target']}` ({item['score']:.4f})" for item in ranking
        ) if ranking else f"- {pretty_label}: none")

    lines.append("")
    lines.append("## Target Details")
    for summary in diagnostics["target_summaries"]:
        lines.extend(
            [
                f"### {summary['target']}",
                "",
                f"- Best layer: `{summary['best_layer']}` via `{summary['best_layer_selection']}`",
                f"- Layer window: `{summary['layer_window']}`",
                f"- Tuned alpha: `{summary['alpha']}` via `{summary['alpha_selection']}`",
                f"- Dev accuracy / margin: `{summary['dev_accuracy']}` / `{summary['dev_margin']}`",
                f"- Steered dev accuracy / margin: `{summary['steered_dev_accuracy']}` / `{summary['steered_dev_margin']}`",
                f"- Test accuracy / steered test accuracy: `{summary['test_accuracy']}` / `{summary['test_accuracy_steered']}`",
                f"- Steered test margin: `{summary['steered_test_margin']}`",
                f"- Train/dev/test examples: `{summary['train_examples']}` / `{summary['dev_examples']}` / `{summary['test_examples']}`",
                (
                    f"- Psalm families: `{', '.join(summary['psalm_families'])}`"
                    if summary.get("psalm_families")
                    else "- Psalm families: n/a"
                ),
                (
                    f"- Psalm vector sets: `{', '.join(summary['psalm_vector_sets'])}`"
                    if summary.get("psalm_vector_sets")
                    else "- Psalm vector sets: whole configured target"
                ),
                "- Top layers by dev accuracy: "
                + ", ".join(
                    f"`L{item['layer']}` ({item['score']:.4f})"
                    for item in summary["top_layers_by_dev_accuracy"]
                ),
                "- Top layers by dev margin: "
                + ", ".join(
                    f"`L{item['layer']}` ({item['score']:.4f})"
                    for item in summary["top_layers_by_dev_margin"]
                ),
                "- Top alphas by dev accuracy: "
                + ", ".join(
                    f"`{item['alpha']}` ({item['score']:.4f})"
                    for item in summary["top_alphas_by_dev_accuracy"]
                ),
                "- Top alphas by dev margin: "
                + ", ".join(
                    f"`{item['alpha']}` ({item['score']:.4f})"
                    for item in summary["top_alphas_by_dev_margin"]
                ),
                "",
            ]
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")


def _load_stage_checkpoint(path: Path) -> List[RunResult]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Warning: could not load Iconoclast checkpoint {path}: {exc}")
        return []
    return [RunResult(**row) for row in payload]


def _write_stage_checkpoint(path: Path, results: List[RunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = [result.model_dump() for result in results]
    path.write_text(json.dumps(dumped, indent=2, default=str), encoding="utf-8")


def _write_stage_status(
    path: Path,
    *,
    state: str,
    stage: str,
    total_runs: int,
    completed_runs: int,
    virtue: Optional[str] = None,
    variant: Optional[str] = None,
    condition: Optional[str] = None,
    run_index: Optional[int] = None,
    note: Optional[str] = None,
) -> None:
    payload = {
        "state": state,
        "stage": stage,
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "virtue": virtue,
        "variant": variant,
        "condition": condition,
        "run_index": run_index,
        "note": note,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_run_status(
    path: Path,
    *,
    state: str,
    phase: str,
    output_prefix: str,
    note: Optional[str] = None,
    current_virtue: Optional[str] = None,
    current_variant: Optional[str] = None,
    current_condition: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    artifacts: Optional[Dict[str, str]] = None,
) -> None:
    payload = {
        "state": state,
        "phase": phase,
        "output_prefix": output_prefix,
        "note": note,
        "current_virtue": current_virtue,
        "current_variant": current_variant,
        "current_condition": current_condition,
        "error_type": error_type,
        "error_message": error_message,
        "artifacts": artifacts or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_preflight_payload(
    path: Path,
    *,
    status: str,
    policy: str,
    alpha_scale: float,
    variant: str,
    rows: List[dict],
    active: Optional[Dict[str, str]] = None,
    note: Optional[str] = None,
) -> None:
    payload = {
        "status": status,
        "policy": policy,
        "alpha_scale": alpha_scale,
        "variant": variant,
        "rows": rows,
        "active": active,
        "note": note,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _planned_stage_runs(
    config: IconoclastConfig,
    stage: str,
    stage_variants: List[str],
    stage_runs: int,
    skipped_preflight_paths: Optional[set[tuple[str, str, str]]] = None,
) -> int:
    skipped_preflight_paths = skipped_preflight_paths or set()
    total = 0
    for virtue in config.virtues:
        for variant in stage_variants:
            for condition in config.conditions:
                for steering_target in _steering_targets(config, stage, virtue, condition):
                    if (virtue, condition, steering_target) in skipped_preflight_paths:
                        continue
                    total += 1
    return total * stage_runs


def _stage_result_key(result: RunResult) -> Tuple[str, str, str, int]:
    return (result.virtue, result.variant, result.condition, result.run_index)


def _preflight_failure_keys(preflight: Dict[str, object]) -> set[tuple[str, str, str]]:
    rows = preflight.get("rows", [])
    failures: set[tuple[str, str, str]] = set()
    if not isinstance(rows, list):
        return failures
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("status") != "fail":
            continue
        virtue = row.get("virtue")
        condition = row.get("condition")
        steering_target = row.get("steering_target")
        if isinstance(virtue, str) and isinstance(condition, str) and isinstance(steering_target, str):
            failures.add((virtue, condition, steering_target))
    return failures


async def _run_steering_preflight(
    config: IconoclastConfig,
    runner,
    artifact: dict,
    *,
    run_status_path: Optional[Path] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
) -> dict:
    """Run a small, strong-alpha divergence probe before a benchmark stage."""
    if config.preflight_policy == "off":
        return {"status": "skipped", "reason": "preflight disabled"}
    if not any(condition in STEERING_CONDITIONS for condition in config.conditions):
        return {"status": "skipped", "reason": "no steering conditions requested"}

    output_path = _preflight_path(config)
    rows = []
    failures = []

    def persist(status: str, *, active: Optional[Dict[str, str]] = None, note: Optional[str] = None) -> None:
        _write_preflight_payload(
            output_path,
            status=status,
            policy=config.preflight_policy,
            alpha_scale=config.preflight_alpha_scale,
            variant=config.preflight_variant,
            rows=rows,
            active=active,
            note=note,
        )
        if run_status_path is not None:
            _write_run_status(
                run_status_path,
                state="running",
                phase="preflight",
                output_prefix=config.output_prefix,
                note=note,
                current_virtue=active.get("virtue") if active else None,
                current_condition=(
                    f"{active['condition']}:{active['steering_target']}"
                    if active is not None
                    else None
                ),
                artifacts=artifact_paths,
            )

    print("\n=== Iconoclast preflight: steering divergence ===")
    persist("running", note="starting steering preflight")
    for virtue in config.virtues:
        control = await run_single_condition(
            runner=runner,
            virtue=virtue,
            variant=config.preflight_variant,
            run_index=0,
            seed=config.seed,
            temperature=0.0,
            limit=config.preflight_limit,
            concurrency=config.concurrency,
            retries=config.retries,
            timeout=config.preflight_timeout,
            detailed=True,
            max_tokens=config.preflight_max_tokens,
            condition_name="control",
            run_metadata={"stage": "preflight", "eval_virtue": virtue},
            frame="preflight",
        )
        for steer_condition, null_condition, target_mode in _preflight_families(config):
            if target_mode == "virtue":
                steering_targets = _virtue_steering_targets(config, "smoke", virtue)
            elif target_mode == "christian":
                steering_targets = ["christian"]
            else:
                steering_targets = list(config.scripture_targets)

            for steering_target in steering_targets:
                active = {
                    "virtue": virtue,
                    "condition": steer_condition,
                    "steering_target": steering_target,
                }
                persist("running", active=active, note="probing steering divergence")
                print(
                    f"\n--- preflight {virtue}/{config.preflight_variant} "
                    f"[{steer_condition}:{steering_target}] ---"
                )
                family_alpha_scale = _condition_alpha_scale(
                    config,
                    steer_condition,
                    steering_target,
                )
                stored_alpha = float(artifact["virtues"][steering_target]["alpha"])
                base_alpha = stored_alpha * family_alpha_scale
                probe_scales = _preflight_scales(
                    base_alpha=base_alpha,
                    initial_scale=config.preflight_alpha_scale,
                    max_alpha=config.preflight_max_alpha,
                )
                steer = None
                null = None
                steer_stats = None
                null_stats = None
                attempts = []
                for attempt_index, probe_scale in enumerate(probe_scales):
                    steer_candidate = await run_single_condition(
                        runner=runner,
                        virtue=virtue,
                        variant=config.preflight_variant,
                        run_index=attempt_index,
                        seed=config.seed,
                        temperature=0.0,
                        limit=config.preflight_limit,
                        concurrency=config.concurrency,
                        retries=config.retries,
                        timeout=config.preflight_timeout,
                        detailed=True,
                        max_tokens=config.preflight_max_tokens,
                        condition_name=f"{steer_condition}:{steering_target}",
                        run_metadata={
                            "stage": "preflight",
                            "eval_virtue": virtue,
                            "steering_virtue": steering_target,
                            "probe_alpha_scale": probe_scale,
                        },
                        steering_runtime=_scaled_runtime(
                            artifact,
                            steering_target,
                            use_null=False,
                            alpha_scale=family_alpha_scale * probe_scale,
                        ),
                        frame="preflight",
                    )
                    null_candidate = await run_single_condition(
                        runner=runner,
                        virtue=virtue,
                        variant=config.preflight_variant,
                        run_index=attempt_index,
                        seed=config.seed,
                        temperature=0.0,
                        limit=config.preflight_limit,
                        concurrency=config.concurrency,
                        retries=config.retries,
                        timeout=config.preflight_timeout,
                        detailed=True,
                        max_tokens=config.preflight_max_tokens,
                        condition_name=f"{null_condition}:{steering_target}",
                        run_metadata={
                            "stage": "preflight",
                            "eval_virtue": virtue,
                            "steering_virtue": steering_target,
                            "probe_alpha_scale": probe_scale,
                        },
                        steering_runtime=_scaled_runtime(
                            artifact,
                            steering_target,
                            use_null=True,
                            alpha_scale=family_alpha_scale * probe_scale,
                        ),
                        frame="preflight",
                    )

                    steer_candidate_stats = compare_paired_results(control, steer_candidate)
                    null_candidate_stats = compare_paired_results(control, null_candidate)
                    attempts.append(
                        {
                            "probe_alpha_scale": probe_scale,
                            "probe_alpha": base_alpha * probe_scale,
                            "family_alpha_scale": family_alpha_scale,
                            "answer_changes": steer_candidate_stats["answer_changes"],
                            "null_answer_changes": null_candidate_stats["answer_changes"],
                            "improve": steer_candidate_stats["improve"],
                            "regress": steer_candidate_stats["regress"],
                        }
                    )
                    steer = steer_candidate
                    null = null_candidate
                    steer_stats = steer_candidate_stats
                    null_stats = null_candidate_stats
                    if steer_candidate_stats["answer_changes"] > 0:
                        break

                assert steer is not None and null is not None
                assert steer_stats is not None and null_stats is not None
                row = {
                    "virtue": virtue,
                    "condition": steer_condition,
                    "steering_target": steering_target,
                    "variant": config.preflight_variant,
                    "samples": steer_stats["compared"],
                    "control_accuracy": control.accuracy,
                    "steer_accuracy": steer.accuracy,
                    "null_accuracy": null.accuracy,
                    "artifact_alpha": stored_alpha,
                    "base_alpha": base_alpha,
                    "probe_alpha": base_alpha * float(steer.metadata.get("probe_alpha_scale", config.preflight_alpha_scale)),
                    "probe_alpha_scale": float(steer.metadata.get("probe_alpha_scale", config.preflight_alpha_scale)),
                    "family_alpha_scale": family_alpha_scale,
                    "attempts": attempts,
                    "answer_changes": steer_stats["answer_changes"],
                    "correctness_changes": steer_stats["correctness_changes"],
                    "improve": steer_stats["improve"],
                    "regress": steer_stats["regress"],
                    "null_answer_changes": null_stats["answer_changes"],
                    "null_correctness_changes": null_stats["correctness_changes"],
                    "null_improve": null_stats["improve"],
                    "null_regress": null_stats["regress"],
                    "status": "pass",
                    "notes": [],
                }
                if steer_stats["answer_changes"] == 0:
                    row["status"] = "fail"
                    row["notes"].append("steering produced zero answer changes across all probe strengths")
                    failures.append(f"{virtue}:{steer_condition}:{steering_target}")
                elif null_stats["answer_changes"] >= steer_stats["answer_changes"]:
                    row["status"] = "warn"
                    row["notes"].append("null control moved at least as many answers as the real vector")
                rows.append(row)
                persist("running", active=active, note="completed steering divergence probe")

    payload_status = "passed"
    if failures:
        payload_status = "failed" if config.preflight_policy == "error" else "warning"
        if config.preflight_policy == "skip":
            payload_status = "pruned"
    payload = {
        "status": payload_status,
        "policy": config.preflight_policy,
        "alpha_scale": config.preflight_alpha_scale,
        "variant": config.preflight_variant,
        "rows": rows,
    }
    persist(payload_status, note="steering preflight complete")
    print(f"Saved steering preflight to: {output_path}")

    if failures and config.preflight_policy == "error":
        failing = ", ".join(failures)
        raise RuntimeError(
            "Iconoclast steering preflight failed for "
            f"{failing}. See {output_path}."
        )
    return payload


async def run_iconoclast_experiment(config: IconoclastConfig, runner) -> Dict[str, List]:
    """Run the multi-stage Iconoclast experiment."""
    if not hasattr(runner, "get_model_and_tokenizer"):
        raise ValueError("Iconoclast experiments currently require the hf-local runner.")

    run_status_path = _run_status_path(config)
    corpus_path = Path(config.corpus_path) if config.corpus_path else None
    corpus_records = load_steering_corpus(corpus_path)
    requested_targets = _requested_vector_targets(config, corpus_records)
    vector_path = Path(config.vector_path) if config.vector_path else (
        RESULTS_DIR / f"{config.output_prefix}_vectors.pt"
    )
    artifact_paths = _run_artifact_paths(config, vector_path)

    current_phase = "startup"
    try:
        _write_run_status(
            run_status_path,
            state="running",
            phase=current_phase,
            output_prefix=config.output_prefix,
            note="loading steering corpus",
            artifacts=artifact_paths,
        )

        artifact = None
        if vector_path.exists():
            current_phase = "vector_load"
            _write_run_status(
                run_status_path,
                state="running",
                phase=current_phase,
                output_prefix=config.output_prefix,
                note="checking existing vector artifact",
                artifacts=artifact_paths,
            )
            loaded = load_vector_artifact(vector_path)
            loaded_method = loaded.get("extraction_method")
            loaded_targets = set(loaded.get("targets") or loaded.get("virtues", {}).keys())
            missing_targets = [target for target in requested_targets if target not in loaded_targets]
            if missing_targets:
                print(
                    "Existing vector artifact is missing requested targets "
                    f"({', '.join(missing_targets)}); re-extracting."
                )
            elif config.extraction_method != "auto" and loaded_method != config.extraction_method:
                print(
                    "Existing vector artifact method "
                    f"({loaded_method or 'unknown'}) does not match requested method "
                    f"({config.extraction_method}); re-extracting."
                )
            else:
                artifact = loaded

        if artifact is None:
            current_phase = "vector_extraction"
            _write_run_status(
                run_status_path,
                state="running",
                phase=current_phase,
                output_prefix=config.output_prefix,
                note="extracting steering vectors",
                artifacts=artifact_paths,
            )
            artifact = extract_virtue_vectors(
                runner,
                corpus_path=corpus_path,
                targets=requested_targets,
                alpha_candidates=config.alpha_candidates,
                extraction_method=config.extraction_method,
                max_length=config.max_length,
                window_radius=config.window_radius,
                window_center=config.window_center,
                psalm_vector_sets=config.psalm_vector_sets or None,
            )
            save_vector_artifact(artifact, vector_path)

        current_phase = "vector_diagnostics"
        _write_run_status(
            run_status_path,
            state="running",
            phase=current_phase,
            output_prefix=config.output_prefix,
            note="writing vector diagnostics",
            artifacts=artifact_paths,
        )
        _write_vector_diagnostics(config, artifact)

        current_phase = "model_load"
        _write_run_status(
            run_status_path,
            state="running",
            phase=current_phase,
            output_prefix=config.output_prefix,
            note="warming model before benchmark",
            artifacts=artifact_paths,
        )
        runner.ensure_loaded()

        prompt_conditions = set(config.conditions)
        needs_psalm_text = any(condition in {"psalm_baseline", "combined"} for condition in prompt_conditions)
        needs_length_control = "length_control" in prompt_conditions

        psalm_text = None
        length_control_text = None
        if needs_psalm_text or needs_length_control:
            psalm_text = load_psalm_text(
                psalm_sets=config.psalm_sets or None,
                random_n=config.psalm_random,
                seed=config.seed,
            )
        if needs_length_control:
            _, tokenizer = runner.get_model_and_tokenizer()
            neutral_records = select_corpus_texts(corpus_records, virtue="neutral", polarity="neutral")
            length_control_text = build_length_matched_control(psalm_text, neutral_records, tokenizer=tokenizer)

        stage_results: Dict[str, List] = {}
        deviation_points = _deviation_points(config.virtues) if config.discernment else {}
        current_phase = "preflight"
        _write_run_status(
            run_status_path,
            state="running",
            phase=current_phase,
            output_prefix=config.output_prefix,
            note="starting steering preflight",
            artifacts=artifact_paths,
        )
        preflight = await _run_steering_preflight(
            config,
            runner,
            artifact,
            run_status_path=run_status_path,
            artifact_paths=artifact_paths,
        )
        stage_results["preflight"] = preflight
        skipped_preflight_paths = _preflight_failure_keys(preflight) if config.preflight_policy == "skip" else set()

        for stage in _stage_order(config.stage):
            current_phase = f"stage:{stage}"
            stage_runs = _run_count(config, stage)
            stage_temperature = _temperature(config, stage)
            stage_variants = _variant_selection(config, stage)
            output_path, checkpoint_path, status_path = _stage_paths(config, stage)
            results = _load_stage_checkpoint(checkpoint_path)
            completed = {_stage_result_key(result) for result in results}
            total_runs = _planned_stage_runs(
                config,
                stage,
                stage_variants,
                stage_runs,
                skipped_preflight_paths=skipped_preflight_paths,
            )

            _write_run_status(
                run_status_path,
                state="running",
                phase=current_phase,
                output_prefix=config.output_prefix,
                note="starting benchmark stage",
                artifacts=artifact_paths,
            )

            if completed:
                print(
                    f"Resuming stage {stage}: {len(completed)}/{total_runs} run cells already complete"
                )

            _write_stage_status(
                status_path,
                state="running",
                stage=stage,
                total_runs=total_runs,
                completed_runs=len(completed),
                note="resuming from checkpoint" if completed else "starting stage",
            )

            print(f"\n=== Iconoclast stage: {stage} ===")
            for virtue in config.virtues:
                for variant in stage_variants:
                    for condition in config.conditions:
                        for steering_virtue in _steering_targets(config, stage, virtue, condition):
                            label = _condition_label(condition, steering_virtue)
                            if (virtue, condition, steering_virtue) in skipped_preflight_paths:
                                print(f"\n--- {virtue}/{variant} [{label}] ---")
                                print("Skipping due to failed preflight for this steering path.")
                                continue
                            print(f"\n--- {virtue}/{variant} [{label}] ---")

                            steering_runtime = None
                            injection_text = None

                            if condition in {"psalm_baseline", "combined"}:
                                injection_text = psalm_text
                            elif condition == "length_control":
                                injection_text = length_control_text

                            if condition in STEERING_CONDITIONS:
                                assert steering_virtue is not None
                                family_alpha_scale = _condition_alpha_scale(
                                    config,
                                    condition,
                                    steering_virtue,
                                )
                                stored_alpha = float(artifact["virtues"][steering_virtue]["alpha"])
                                steering_runtime = _artifact_to_runtime(
                                    artifact,
                                    steering_virtue,
                                    use_null=(
                                        condition
                                        in {
                                            "null_control",
                                            "christian_null_control",
                                            "scripture_null_control",
                                        }
                                    ),
                                    alpha_scale=family_alpha_scale,
                                )
                            else:
                                family_alpha_scale = 1.0
                                stored_alpha = None

                            for run_index in range(stage_runs):
                                key = (virtue, variant, label, run_index)
                                if key in completed:
                                    continue

                                _write_run_status(
                                    run_status_path,
                                    state="running",
                                    phase=current_phase,
                                    output_prefix=config.output_prefix,
                                    note="running benchmark cell",
                                    current_virtue=virtue,
                                    current_variant=variant,
                                    current_condition=label,
                                    artifacts=artifact_paths,
                                )
                                _write_stage_status(
                                    status_path,
                                    state="running",
                                    stage=stage,
                                    total_runs=total_runs,
                                    completed_runs=len(completed),
                                    virtue=virtue,
                                    variant=variant,
                                    condition=label,
                                    run_index=run_index,
                                )
                                result = await run_single_condition(
                                    runner=runner,
                                    virtue=virtue,
                                    variant=variant,
                                    run_index=run_index,
                                    seed=config.seed,
                                    temperature=stage_temperature,
                                    limit=config.limit,
                                    concurrency=config.concurrency,
                                    retries=config.retries,
                                    timeout=config.timeout,
                                    detailed=config.detailed,
                                    injection_text=injection_text,
                                    condition_name=label,
                                    run_metadata={
                                        "stage": stage,
                                        "eval_virtue": virtue,
                                        "steering_virtue": steering_virtue,
                                        "vector_alpha": (
                                            stored_alpha * family_alpha_scale
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "artifact_alpha": (
                                            stored_alpha
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "alpha_scale_applied": (
                                            family_alpha_scale
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "best_layer": (
                                            artifact["virtues"][steering_virtue]["best_layer"]
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "best_layer_selection": (
                                            artifact["virtues"][steering_virtue].get("best_layer_selection")
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "layer_window": (
                                            artifact["virtues"][steering_virtue]["layer_window"]
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "psalm_sets": list(config.psalm_sets),
                                        "psalm_random": config.psalm_random,
                                        "psalm_family_lanes": (
                                            parse_psalm_family_target(steering_virtue)
                                            if steering_virtue is not None
                                            else None
                                        ),
                                        "extraction_method": artifact.get("extraction_method"),
                                    },
                                    steering_runtime=steering_runtime,
                                    frame=stage,
                                )
                                results.append(result)
                                completed.add(key)
                                _write_stage_checkpoint(checkpoint_path, results)
                                write_results(results, output_path, write_logs=config.detailed)
                                _write_stage_status(
                                    status_path,
                                    state="running",
                                    stage=stage,
                                    total_runs=total_runs,
                                    completed_runs=len(completed),
                                    virtue=virtue,
                                    variant=variant,
                                    condition=label,
                                    run_index=run_index,
                                )

            summary_path, logs_path = write_results(results, output_path, write_logs=config.detailed)
            print(f"Saved stage results to: {summary_path}")
            if logs_path:
                print(f"Saved stage logs to: {logs_path}")

            aggregated = aggregate_runs(results)
            stage_results[stage] = results
            stage_results[f"{stage}_aggregated"] = aggregated

            if config.discernment and "ignatian" in stage_variants:
                failed = []
                for result in results:
                    if result.variant != "ignatian":
                        continue
                    failed.extend(
                        sample for sample in result.sample_details
                        if sample.variant == "ignatian" and sample.correct is False
                    )
                if failed:
                    discernment_rows = await retroactive_discernment_eval(
                        runner,
                        failed,
                        deviation_points,
                    )
                    discernment_path = RESULTS_DIR / f"{config.output_prefix}_{stage}_discernment.json"
                    discernment_path.write_text(json.dumps(discernment_rows, indent=2), encoding="utf-8")
                    stage_results[f"{stage}_discernment"] = discernment_rows
                    print(f"Saved discernment analysis to: {discernment_path}")

            _write_stage_status(
                status_path,
                state="completed",
                stage=stage,
                total_runs=total_runs,
                completed_runs=len(completed),
                note="stage complete",
            )

        _write_run_status(
            run_status_path,
            state="completed",
            phase="completed",
            output_prefix=config.output_prefix,
            note="all requested stages completed",
            artifacts=artifact_paths,
        )
        return stage_results
    except Exception as exc:
        _write_run_status(
            run_status_path,
            state="failed",
            phase=current_phase,
            output_prefix=config.output_prefix,
            note="iconoclast run failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
            artifacts=artifact_paths,
        )
        raise
