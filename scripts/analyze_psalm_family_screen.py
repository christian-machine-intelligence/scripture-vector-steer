#!/usr/bin/env python3
"""Summarize Psalm-family screening runs and prepare reasoning review packs."""

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

from virtue_bench.analysis.psalm_screen import (
    build_reasoning_review_pack,
    choose_representative_scale,
    load_run_results,
    load_vector_diagnostics,
    summarize_psalm_lane,
)


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
    """Only include mechanically completed attempts in the screen summary."""

    required_paths = [
        results_dir / f"{prefix}_run.status.json",
        results_dir / f"{prefix}_ratio.status.json",
        results_dir / f"{prefix}_ratio.json",
        results_dir / f"{prefix}_ratio_logs.json",
        results_dir / f"{prefix}_vector_diagnostics.json",
        results_dir / f"{prefix}_vector_diagnostics.md",
    ]
    if any(not path.exists() for path in required_paths):
        return False

    run_status = _read_json(results_dir / f"{prefix}_run.status.json")
    ratio_status = _read_json(results_dir / f"{prefix}_ratio.status.json")
    return (
        run_status.get("state") == "completed"
        and ratio_status.get("state") == "completed"
    )


def _build_markdown_report(report: dict, *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "## Representative scales",
    ]

    for family, summary in sorted(report["representative_scales"].items()):
        lines.extend(
            [
                f"### {family}",
                "",
                f"- Scale: `{summary.get('alpha_scale')}`",
                f"- Control vs lane: `{_format_percent(summary.get('control_accuracy'))}` -> `{_format_percent(summary.get('candidate_accuracy'))}`",
                f"- Delta vs control: `{_format_delta(summary.get('delta_vs_control'))}`",
                f"- Answer changes / improves / regresses: `{summary.get('answer_changes')}` / `{summary.get('improvements')}` / `{summary.get('regressions')}`",
                f"- Best layer: `{summary.get('diagnostics', {}).get('best_layer')}`",
                f"- Layer window: `{summary.get('diagnostics', {}).get('layer_window')}`",
                f"- Tuned alpha: `{summary.get('diagnostics', {}).get('alpha')}`",
                f"- Steered test margin: `{summary.get('diagnostics', {}).get('steered_test_margin')}`",
                "",
                "- Per-virtue deltas:",
            ]
        )
        for virtue, delta in sorted(summary.get("per_virtue_delta", {}).items()):
            lines.append(f"  - `{virtue}`: `{_format_delta(delta)}`")
        lines.append("")

    lines.append("## Reasoning review packs")
    for family, review in sorted(report["reasoning_review"].items()):
        lines.extend(
            [
                f"### {family}",
                "",
                f"- Changed-answer cases: `{len(review.get('changed_cases', []))}`",
                f"- Same-answer rationale-shift candidates: `{len(review.get('same_answer_candidates', []))}`",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Psalm-family screening runs.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=_default_results_dir(),
        help="Directory containing Iconoclast result artifacts",
    )
    parser.add_argument(
        "--glob",
        type=str,
        default="*psalm_family*_ratio_logs.json",
        help="Glob pattern for detailed run logs under the results directory",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="psalm_family_screen_summary",
        help="Prefix for the summary JSON and Markdown files",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Psalm Family Screening Summary",
        help="Markdown report title",
    )
    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Include partial or failed attempts instead of requiring completed status files",
    )
    args = parser.parse_args()

    summaries_by_family = defaultdict(list)
    review_packs = {}
    skipped_incomplete = []

    for logs_path in sorted(args.results_dir.glob(args.glob)):
        prefix = logs_path.name.removesuffix("_ratio_logs.json")
        if not args.include_incomplete and not _is_completed_run(args.results_dir, prefix):
            skipped_incomplete.append(prefix)
            continue
        diagnostics_path = args.results_dir / f"{prefix}_vector_diagnostics.json"
        if not diagnostics_path.exists():
            continue
        results = load_run_results(logs_path)
        diagnostics = load_vector_diagnostics(diagnostics_path)
        scripture_conditions = sorted({
            result.condition
            for result in results
            if result.condition.startswith("scripture_steer:")
        })
        for condition in scripture_conditions:
            summary = summarize_psalm_lane(
                results,
                candidate_condition=condition,
                diagnostics=diagnostics,
            )
            summary["logs_path"] = str(logs_path)
            summary["diagnostics_path"] = str(diagnostics_path)
            summaries_by_family[summary["family_label"]].append(summary)

    representative_scales = {}
    for family, summaries in summaries_by_family.items():
        chosen = choose_representative_scale(summaries)
        if chosen is None:
            continue
        representative_scales[family] = chosen
        review_packs[family] = build_reasoning_review_pack(
            load_run_results(Path(chosen["logs_path"])),
            candidate_condition=chosen["condition"],
        )

    report = {
        "representative_scales": representative_scales,
        "reasoning_review": review_packs,
        "skipped_incomplete": skipped_incomplete,
    }

    output_json = args.results_dir / f"{args.output_prefix}.json"
    output_md = args.results_dir / f"{args.output_prefix}.md"
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    output_md.write_text(_build_markdown_report(report, title=args.title), encoding="utf-8")

    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")


if __name__ == "__main__":
    main()
