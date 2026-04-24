#!/usr/bin/env python3
"""Summarize the Study 2 scripture directionality run."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from virtue_bench.analysis.iconoclast import compare_paired_results, condition_target
from virtue_bench.analysis.psalm_screen import (
    build_reasoning_review_pack,
    load_run_results,
    load_vector_diagnostics,
    summarize_psalm_lane,
)
from virtue_bench.core.schema import RunResult, SampleResult


CONDITION_PREFIXES = [
    "scripture_steer",
    "scripture_negative_alpha",
    "scripture_null_control",
]


def _default_results_dir() -> Path:
    return REPO_ROOT / "results"


def _format_percent(value):
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def _format_delta(value):
    if value is None:
        return "n/a"
    return f"{value:+.2%}"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _is_completed_run(results_dir: Path, prefix: str) -> bool:
    required_paths = [
        results_dir / f"{prefix}_run.status.json",
        results_dir / f"{prefix}_full.status.json",
        results_dir / f"{prefix}_full.json",
        results_dir / f"{prefix}_full_logs.json",
        results_dir / f"{prefix}_vector_diagnostics.json",
        results_dir / f"{prefix}_vector_diagnostics.md",
    ]
    if any(not path.exists() for path in required_paths):
        return False

    run_status = _read_json(results_dir / f"{prefix}_run.status.json")
    full_status = _read_json(results_dir / f"{prefix}_full.status.json")
    return (
        run_status.get("state") == "completed"
        and full_status.get("state") == "completed"
    )


def _condition_prefix(condition: str) -> str:
    return condition.split(":", 1)[0]


def _paired_runs(
    results: list[RunResult],
    left_condition: str,
    right_condition: str,
) -> list[tuple[RunResult, RunResult]]:
    lookup = {}
    for result in results:
        key = (result.virtue, result.variant, result.frame, result.run_index)
        if result.condition == left_condition:
            lookup[key] = result

    pairs = []
    for result in results:
        if result.condition != right_condition:
            continue
        key = (result.virtue, result.variant, result.frame, result.run_index)
        left = lookup.get(key)
        if left is not None:
            pairs.append((left, result))
    return pairs


def _accuracy(samples: list[SampleResult]) -> float | None:
    scored = [sample for sample in samples if sample.correct is not None]
    if not scored:
        return None
    return sum(1 for sample in scored if sample.correct) / len(scored)


def _per_variant_delta(results: list[RunResult], candidate_condition: str) -> dict[str, float | None]:
    pairs = _paired_runs(results, "control", candidate_condition)
    control_by_variant = defaultdict(list)
    candidate_by_variant = defaultdict(list)
    for control, candidate in pairs:
        control_by_variant[control.variant].extend(control.sample_details)
        candidate_by_variant[candidate.variant].extend(candidate.sample_details)

    deltas = {}
    for variant in sorted(set(control_by_variant) | set(candidate_by_variant)):
        control_accuracy = _accuracy(control_by_variant[variant])
        candidate_accuracy = _accuracy(candidate_by_variant[variant])
        if control_accuracy is None or candidate_accuracy is None:
            deltas[variant] = None
        else:
            deltas[variant] = candidate_accuracy - control_accuracy
    return deltas


def _positive_vs_negative(
    results: list[RunResult],
    positive_condition: str,
    negative_condition: str,
) -> dict:
    pairs = _paired_runs(results, negative_condition, positive_condition)
    positive_samples = []
    negative_samples = []
    answer_changes = 0
    positive_better = 0
    negative_better = 0
    for negative, positive in pairs:
        stats = compare_paired_results(negative, positive)
        answer_changes += stats["answer_changes"]
        positive_better += stats["improve"]
        negative_better += stats["regress"]
        negative_samples.extend(negative.sample_details)
        positive_samples.extend(positive.sample_details)

    positive_accuracy = _accuracy(positive_samples)
    negative_accuracy = _accuracy(negative_samples)
    delta = None
    if positive_accuracy is not None and negative_accuracy is not None:
        delta = positive_accuracy - negative_accuracy
    return {
        "positive_condition": positive_condition,
        "negative_condition": negative_condition,
        "positive_accuracy": positive_accuracy,
        "negative_accuracy": negative_accuracy,
        "positive_minus_negative": delta,
        "answer_changes": answer_changes,
        "positive_better": positive_better,
        "negative_better": negative_better,
    }


def _diagnostic_geometry(diagnostics: dict) -> dict:
    summaries = diagnostics.get("target_summaries", [])
    return {
        summary.get("target"): {
            "best_layer": summary.get("best_layer"),
            "layer_window": summary.get("layer_window"),
            "alpha": summary.get("alpha"),
            "scripture_runtime_alpha": summary.get("scripture_runtime_alpha"),
            "steered_test_margin": summary.get("steered_test_margin"),
        }
        for summary in summaries
        if isinstance(summary, dict) and summary.get("target")
    }


def _build_report(results: list[RunResult], diagnostics: dict) -> dict:
    conditions = sorted(
        {
            result.condition
            for result in results
            if _condition_prefix(result.condition) in CONDITION_PREFIXES
        }
    )

    lane_summaries = {}
    reasoning_review = {}
    for condition in conditions:
        summary = summarize_psalm_lane(
            results,
            candidate_condition=condition,
            diagnostics=diagnostics,
        )
        summary["condition_type"] = _condition_prefix(condition)
        summary["per_variant_delta"] = _per_variant_delta(results, condition)
        lane_summaries[condition] = summary
        reasoning_review[condition] = build_reasoning_review_pack(
            results,
            candidate_condition=condition,
        )

    directionality = {}
    targets = sorted(
        {
            condition_target(condition)
            for condition in conditions
            if condition_target(condition)
        }
    )
    for target in targets:
        positive = f"scripture_steer:{target}"
        negative = f"scripture_negative_alpha:{target}"
        if positive in lane_summaries and negative in lane_summaries:
            directionality[target] = _positive_vs_negative(results, positive, negative)

    return {
        "lane_summaries": lane_summaries,
        "directionality": directionality,
        "reasoning_review": reasoning_review,
        "vector_geometry": _diagnostic_geometry(diagnostics),
    }


def _build_markdown(report: dict, *, title: str) -> str:
    lines = [f"# {title}", ""]

    lines.extend(["## Lane Results", ""])
    lines.append(
        "| Target | Condition | Control | Candidate | Delta | Changes | Improve | Regress | Vector alpha | Layer |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for condition, summary in sorted(report["lane_summaries"].items()):
        diagnostics = summary.get("diagnostics", {})
        lines.append(
            "| "
            + " | ".join(
                [
                    str(summary.get("target")),
                    str(summary.get("condition_type")),
                    _format_percent(summary.get("control_accuracy")),
                    _format_percent(summary.get("candidate_accuracy")),
                    _format_delta(summary.get("delta_vs_control")),
                    str(summary.get("answer_changes")),
                    str(summary.get("improvements")),
                    str(summary.get("regressions")),
                    str(summary.get("vector_alpha")),
                    str(diagnostics.get("best_layer")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Directionality", ""])
    lines.append("| Target | Positive | Negative | Pos - Neg | Answer changes | Positive better | Negative better |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for target, summary in sorted(report["directionality"].items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    target,
                    _format_percent(summary.get("positive_accuracy")),
                    _format_percent(summary.get("negative_accuracy")),
                    _format_delta(summary.get("positive_minus_negative")),
                    str(summary.get("answer_changes")),
                    str(summary.get("positive_better")),
                    str(summary.get("negative_better")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Per-Variant Deltas", ""])
    for condition, summary in sorted(report["lane_summaries"].items()):
        lines.extend([f"### {condition}", ""])
        for variant, delta in sorted(summary.get("per_variant_delta", {}).items()):
            lines.append(f"- `{variant}`: `{_format_delta(delta)}`")
        lines.append("")

    lines.extend(["## Reasoning Review Packs", ""])
    for condition, review in sorted(report["reasoning_review"].items()):
        lines.append(
            f"- `{condition}`: changed `{len(review.get('changed_cases', []))}`, "
            f"same-answer rationale shifts `{len(review.get('same_answer_candidates', []))}`"
        )
    lines.append("")

    lines.extend(["## Vector Diagnostics", ""])
    for target, summary in sorted(report["vector_geometry"].items()):
        lines.append(
            f"- `{target}`: layer `{summary.get('best_layer')}`, "
            f"window `{summary.get('layer_window')}`, tuned alpha `{summary.get('alpha')}`, "
            f"runtime alpha `{summary.get('scripture_runtime_alpha')}`, "
            f"margin `{summary.get('steered_test_margin')}`"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Study 2 scripture steering runs.")
    parser.add_argument("--results-dir", type=Path, default=_default_results_dir())
    parser.add_argument(
        "--glob",
        default="*scripture_study2*_full_logs.json",
        help="Glob pattern for detailed full-stage logs",
    )
    parser.add_argument("--output-prefix", default="scripture_study2_summary")
    parser.add_argument("--title", default="Study 2 Scripture Directionality Summary")
    parser.add_argument("--include-incomplete", action="store_true")
    args = parser.parse_args()

    reports = {}
    skipped_incomplete = []
    for logs_path in sorted(args.results_dir.glob(args.glob)):
        prefix = logs_path.name.removesuffix("_full_logs.json")
        if not args.include_incomplete and not _is_completed_run(args.results_dir, prefix):
            skipped_incomplete.append(prefix)
            continue
        diagnostics_path = args.results_dir / f"{prefix}_vector_diagnostics.json"
        if not diagnostics_path.exists():
            continue
        reports[prefix] = _build_report(
            load_run_results(logs_path),
            load_vector_diagnostics(diagnostics_path),
        )

    report = {
        "runs": reports,
        "skipped_incomplete": skipped_incomplete,
    }

    output_json = args.results_dir / f"{args.output_prefix}.json"
    output_md = args.results_dir / f"{args.output_prefix}.md"
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if len(reports) == 1:
        run_report = next(iter(reports.values()))
        output_md.write_text(_build_markdown(run_report, title=args.title), encoding="utf-8")
    else:
        lines = [f"# {args.title}", "", f"- Completed runs summarized: `{len(reports)}`"]
        if skipped_incomplete:
            lines.append(f"- Skipped incomplete runs: `{len(skipped_incomplete)}`")
        output_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")


if __name__ == "__main__":
    main()
