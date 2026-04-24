"""Reporting helpers for the Iconoclast activation-space experiment."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - optional dependency
    plt = None  # type: ignore

try:
    from tabulate import tabulate
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal installs
    def tabulate(rows, headers, tablefmt="github"):
        widths = [len(str(header)) for header in headers]
        for row in rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], len(str(cell)))
        lines = []
        header = "| " + " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(headers)) + " |"
        divider = "| " + " | ".join("-" * width for width in widths) + " |"
        lines.extend([header, divider])
        for row in rows:
            lines.append("| " + " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)) + " |")
        return "\n".join(lines)

from ..stats.bootstrap import AggregatedResult
from ..core.schema import RunResult


def condition_base_name(condition: str) -> str:
    return condition.split(":", 1)[0]


def condition_target(condition: str) -> Optional[str]:
    parts = condition.split(":", 1)
    return parts[1] if len(parts) == 2 else None


def _baseline_lookup(aggregated: Iterable[AggregatedResult]) -> Dict[Tuple[str, str, str, str], AggregatedResult]:
    lookup = {}
    for item in aggregated:
        if item.condition != "control":
            continue
        lookup[(item.model, item.virtue, item.variant, item.frame)] = item
    return lookup


def compare_paired_results(control: RunResult, candidate: RunResult) -> Dict[str, int]:
    """Compare sample-level movement between a control run and a candidate run."""
    compared = min(len(control.sample_details), len(candidate.sample_details))
    stats = {
        "compared": compared,
        "sample_mismatches": 0,
        "answer_changes": 0,
        "correctness_changes": 0,
        "improve": 0,
        "regress": 0,
        "infra_pairs": 0,
    }

    for control_sample, candidate_sample in zip(
        control.sample_details[:compared],
        candidate.sample_details[:compared],
    ):
        if (
            control_sample.sample_id != candidate_sample.sample_id
            or control_sample.target != candidate_sample.target
        ):
            stats["sample_mismatches"] += 1

        if control_sample.model_answer != candidate_sample.model_answer:
            stats["answer_changes"] += 1

        if control_sample.infra_error or candidate_sample.infra_error:
            stats["infra_pairs"] += 1

        if control_sample.correct != candidate_sample.correct:
            stats["correctness_changes"] += 1
            if control_sample.correct is False and candidate_sample.correct is True:
                stats["improve"] += 1
            elif control_sample.correct is True and candidate_sample.correct is False:
                stats["regress"] += 1

    return stats


def build_iconoclast_rows(aggregated: Iterable[AggregatedResult]) -> List[List[str]]:
    """Build summary rows with deltas versus the control condition."""
    rows: List[List[str]] = []
    baseline = _baseline_lookup(aggregated)

    for item in sorted(
        aggregated,
        key=lambda result: (result.frame, result.virtue, result.variant, result.condition),
    ):
        control = baseline.get((item.model, item.virtue, item.variant, item.frame))
        delta = item.mean_accuracy - control.mean_accuracy if control is not None else None
        rows.append([
            item.frame,
            item.virtue,
            item.variant,
            item.condition,
            f"{item.mean_accuracy:.4f}",
            f"[{item.ci_lower:.4f}, {item.ci_upper:.4f}]",
            "—" if delta is None else f"{delta:+.4f}",
        ])
    return rows


def print_iconoclast_table(aggregated: Iterable[AggregatedResult]) -> None:
    rows = build_iconoclast_rows(list(aggregated))
    headers = ["Stage", "Virtue", "Variant", "Condition", "Mean", "95% CI", "Delta vs control"]
    print("\n" + tabulate(rows, headers=headers, tablefmt="github"))


def build_paired_flip_rows(results: Iterable[RunResult]) -> List[List[str]]:
    """Build paired movement rows by comparing each condition against control."""
    grouped: Dict[Tuple[str, str, str, str, int], RunResult] = {}
    for result in results:
        grouped[(result.model, result.virtue, result.variant, result.frame, result.run_index, result.condition)] = result

    totals: Dict[Tuple[str, str, str, str], Dict[str, int]] = defaultdict(
        lambda: {
            "compared": 0,
            "answer_changes": 0,
            "correctness_changes": 0,
            "improve": 0,
            "regress": 0,
            "infra_pairs": 0,
            "sample_mismatches": 0,
            "paired_runs": 0,
        }
    )

    control_lookup: Dict[Tuple[str, str, str, str, int], RunResult] = {}
    for result in results:
        if result.condition == "control":
            control_lookup[(result.model, result.virtue, result.variant, result.frame, result.run_index)] = result

    for result in results:
        if result.condition == "control":
            continue
        control = control_lookup.get((result.model, result.virtue, result.variant, result.frame, result.run_index))
        if control is None or not control.sample_details or not result.sample_details:
            continue

        stats = compare_paired_results(control, result)
        bucket = totals[(result.frame, result.virtue, result.variant, result.condition)]
        for key, value in stats.items():
            bucket[key] += value
        bucket["paired_runs"] += 1

    rows: List[List[str]] = []
    for (frame, virtue, variant, condition), stats in sorted(totals.items()):
        net = stats["improve"] - stats["regress"]
        rows.append([
            frame,
            virtue,
            variant,
            condition,
            str(stats["paired_runs"]),
            str(stats["compared"]),
            str(stats["answer_changes"]),
            str(stats["improve"]),
            str(stats["regress"]),
            f"{net:+d}",
            str(stats["infra_pairs"]),
            str(stats["sample_mismatches"]),
        ])
    return rows


def print_paired_flip_table(results: Iterable[RunResult]) -> None:
    """Print paired answer-change counts versus the control condition."""
    rows = build_paired_flip_rows(list(results))
    if not rows:
        return
    headers = [
        "Stage",
        "Virtue",
        "Variant",
        "Condition",
        "Paired runs",
        "Compared",
        "Answer changes",
        "Improve",
        "Regress",
        "Net",
        "Infra pairs",
        "Sample mismatches",
    ]
    print("\n" + tabulate(rows, headers=headers, tablefmt="github"))


def print_cross_virtue_matrix(
    aggregated: Iterable[AggregatedResult],
    *,
    variant: str = "ratio",
    condition_prefix: str = "virtue_steer",
) -> None:
    """Print a steering-virtue matrix for a chosen benchmark variant."""
    aggregated = list(aggregated)
    steering_targets = sorted(
        {target for item in aggregated if condition_base_name(item.condition) == condition_prefix for target in [condition_target(item.condition)] if target}
    )
    if not steering_targets:
        return

    virtues = sorted({item.virtue for item in aggregated})
    lookup = {
        (item.virtue, condition_target(item.condition)): item
        for item in aggregated
        if item.variant == variant and condition_base_name(item.condition) == condition_prefix
    }

    headers = ["Eval virtue"] + steering_targets
    rows = []
    for virtue in virtues:
        row = [virtue]
        for steering_virtue in steering_targets:
            cell = lookup.get((virtue, steering_virtue))
            row.append("—" if cell is None else f"{cell.mean_accuracy:.2%}")
        rows.append(row)
    print("\n" + tabulate(rows, headers=headers, tablefmt="github"))


def write_condition_heatmap(
    aggregated: Iterable[AggregatedResult],
    output_path: Path,
    *,
    condition_prefix: str,
) -> Optional[Path]:
    """Write a virtue × variant delta heatmap for a matched condition."""
    if plt is None:  # pragma: no cover - optional dependency
        return None

    aggregated = list(aggregated)
    virtues = ["prudence", "justice", "courage", "temperance"]
    variants = ["ratio", "caro", "mundus", "diabolus", "ignatian"]
    baseline = _baseline_lookup(aggregated)
    target_must_match_eval = condition_prefix in {"virtue_steer", "combined", "null_control"}

    grid = []
    for virtue in virtues:
        row = []
        for variant in variants:
            matched_cell = None
            for item in aggregated:
                if item.virtue != virtue or item.variant != variant:
                    continue
                if condition_base_name(item.condition) != condition_prefix:
                    continue
                target = condition_target(item.condition)
                if target_must_match_eval and target is not None and target != virtue:
                    continue
                matched_cell = item
                break
            control = baseline.get((matched_cell.model, virtue, variant, matched_cell.frame)) if matched_cell else None
            row.append(0.0 if matched_cell is None or control is None else matched_cell.mean_accuracy - control.mean_accuracy)
        grid.append(row)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    image = ax.imshow(grid, cmap="RdYlGn")
    ax.set_xticks(range(len(variants)))
    ax.set_xticklabels([variant.capitalize() for variant in variants], rotation=30, ha="right")
    ax.set_yticks(range(len(virtues)))
    ax.set_yticklabels([virtue.capitalize() for virtue in virtues])
    ax.set_title(f"{condition_prefix} delta vs control")

    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            ax.text(column_index, row_index, f"{value:+.2%}", ha="center", va="center", fontsize=8)

    fig.colorbar(image, ax=ax, fraction=0.045, pad=0.04, label="Accuracy delta")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_cross_virtue_heatmap(
    aggregated: Iterable[AggregatedResult],
    output_path: Path,
    *,
    variant: str = "ratio",
    condition_prefix: str = "virtue_steer",
) -> Optional[Path]:
    """Write an eval-virtue × steering-virtue heatmap for cross-matrix runs."""
    if plt is None:  # pragma: no cover - optional dependency
        return None

    aggregated = list(aggregated)
    virtues = ["prudence", "justice", "courage", "temperance"]
    lookup = {
        (item.virtue, condition_target(item.condition)): item.mean_accuracy
        for item in aggregated
        if item.variant == variant and condition_base_name(item.condition) == condition_prefix and condition_target(item.condition)
    }
    if not lookup:
        return None

    grid = [
        [lookup.get((eval_virtue, steering_virtue), float("nan")) for steering_virtue in virtues]
        for eval_virtue in virtues
    ]

    fig, ax = plt.subplots(figsize=(5, 4.5))
    image = ax.imshow(grid, cmap="viridis")
    ax.set_xticks(range(len(virtues)))
    ax.set_xticklabels([virtue.capitalize() for virtue in virtues], rotation=30, ha="right")
    ax.set_yticks(range(len(virtues)))
    ax.set_yticklabels([virtue.capitalize() for virtue in virtues])
    ax.set_title(f"{condition_prefix} cross-matrix ({variant})")

    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            text = "—" if value != value else f"{value:.2%}"
            ax.text(column_index, row_index, text, ha="center", va="center", fontsize=8, color="white")

    fig.colorbar(image, ax=ax, fraction=0.045, pad=0.04, label="Accuracy")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path
