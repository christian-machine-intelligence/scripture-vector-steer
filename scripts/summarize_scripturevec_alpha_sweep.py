"""Summarize ScriptureVec matched alpha-sweep result files.

The sweep writes one VirtueBench result file per virtue and alpha. This script
collects those files into one JSON/Markdown table so the run can be interpreted
without manually opening dozens of artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


STEM_RE = re.compile(
    r"scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_"
    r"(?P<virtue>prudence|justice|courage|temperance)_"
    r"(?P<tag>a\d+)_v1_ratio$"
)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _accuracy_by_condition(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    return {str(row.get("condition")): row.get("accuracy") for row in rows}


def _condition_row(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any] | None:
    for row in rows:
        condition = str(row.get("condition"))
        if condition == prefix or condition.startswith(prefix + ":"):
            return row
    return None


def _paired_stats(control: dict[str, Any] | None, candidate: dict[str, Any] | None) -> dict[str, int] | None:
    if not control or not candidate:
        return None
    control_samples = control.get("sample_details") or []
    candidate_samples = candidate.get("sample_details") or []
    compared = min(len(control_samples), len(candidate_samples))
    stats = {
        "compared": compared,
        "answer_changes": 0,
        "correctness_changes": 0,
        "improve": 0,
        "regress": 0,
    }
    for control_sample, candidate_sample in zip(
        control_samples[:compared],
        candidate_samples[:compared],
    ):
        if control_sample.get("model_answer") != candidate_sample.get("model_answer"):
            stats["answer_changes"] += 1
        if control_sample.get("correct") != candidate_sample.get("correct"):
            stats["correctness_changes"] += 1
            if control_sample.get("correct") is False and candidate_sample.get("correct") is True:
                stats["improve"] += 1
            elif control_sample.get("correct") is True and candidate_sample.get("correct") is False:
                stats["regress"] += 1
    return stats


def _alpha_from_rows(rows: list[dict[str, Any]], tag: str) -> float:
    for row in rows:
        metadata = row.get("metadata") or {}
        alpha = metadata.get("runtime_alpha_override")
        if alpha is not None:
            return abs(float(alpha))
    return float(tag.removeprefix("a"))


def collect(results_root: Path) -> dict[str, Any]:
    experiment_root = results_root / "experiments" / "scripturevec14"
    files = sorted(experiment_root.glob(
        "scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_*_a*_v1_ratio.json"
    ))
    rows: list[dict[str, Any]] = []
    incomplete: list[dict[str, str]] = []

    for path in files:
        match = STEM_RE.match(path.stem)
        if not match:
            continue
        summary_rows = _load_json(path)
        if not isinstance(summary_rows, list):
            continue
        virtue = match.group("virtue")
        tag = match.group("tag")
        alpha = _alpha_from_rows(summary_rows, tag)
        accuracies = _accuracy_by_condition(summary_rows)

        control_row = _condition_row(summary_rows, "control")
        positive_row = _condition_row(summary_rows, "scripture_steer")
        negative_row = _condition_row(summary_rows, "scripture_negative_alpha")
        null_row = _condition_row(summary_rows, "scripture_null_control")
        if not all([control_row, positive_row, negative_row, null_row]):
            incomplete.append(
                {
                    "virtue": virtue,
                    "tag": tag,
                    "result_file": str(path),
                }
            )
            continue

        logs_path = path.with_name(f"{path.stem}_logs.json")
        log_rows: list[dict[str, Any]] = []
        if logs_path.exists():
            loaded_logs = _load_json(logs_path)
            if isinstance(loaded_logs, list):
                log_rows = loaded_logs
        log_control = _condition_row(log_rows, "control")
        log_positive = _condition_row(log_rows, "scripture_steer")
        log_negative = _condition_row(log_rows, "scripture_negative_alpha")
        log_null = _condition_row(log_rows, "scripture_null_control")

        control_acc = accuracies.get("control")
        positive_acc = positive_row.get("accuracy") if positive_row else None
        negative_acc = negative_row.get("accuracy") if negative_row else None
        null_acc = null_row.get("accuracy") if null_row else None

        rows.append(
            {
                "virtue": virtue,
                "tag": tag,
                "alpha": alpha,
                "control_accuracy": control_acc,
                "positive_accuracy": positive_acc,
                "negative_accuracy": negative_acc,
                "null_accuracy": null_acc,
                "positive_delta": (
                    None if control_acc is None or positive_acc is None else positive_acc - control_acc
                ),
                "negative_delta": (
                    None if control_acc is None or negative_acc is None else negative_acc - control_acc
                ),
                "null_delta": (
                    None if control_acc is None or null_acc is None else null_acc - control_acc
                ),
                "positive_condition": positive_row.get("condition") if positive_row else None,
                "negative_condition": negative_row.get("condition") if negative_row else None,
                "null_condition": null_row.get("condition") if null_row else None,
                "positive_paired": _paired_stats(log_control, log_positive),
                "negative_paired": _paired_stats(log_control, log_negative),
                "null_paired": _paired_stats(log_control, log_null),
                "result_file": str(path),
                "logs_file": str(logs_path) if logs_path.exists() else None,
            }
        )

    rows.sort(key=lambda row: (row["alpha"], row["virtue"]))
    candidate_rescues = [
        row
        for row in rows
        if row["positive_delta"] is not None
        and row["positive_delta"] > 0
        and row["positive_accuracy"] is not None
        and row["positive_accuracy"] > max(
            value
            for value in [
                row.get("control_accuracy"),
                row.get("negative_accuracy"),
                row.get("null_accuracy"),
            ]
            if value is not None
        )
    ]
    return {
        "result_count": len(rows),
        "alphas": sorted({row["alpha"] for row in rows}),
        "virtues": sorted({row["virtue"] for row in rows}),
        "candidate_rescues": candidate_rescues,
        "incomplete_count": len(incomplete),
        "incomplete": incomplete,
        "rows": rows,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _paired_net(stats: dict[str, int] | None) -> str:
    if not stats:
        return "-"
    net = stats["improve"] - stats["regress"]
    return f"{stats['answer_changes']} chg / {net:+d} net"


def to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# ScriptureVec Qwen3-14B Matched High-Alpha Sweep",
        "",
        f"- Result files summarized: `{payload['result_count']}`",
        f"- Alphas found: `{', '.join(_fmt(alpha) for alpha in payload['alphas'])}`",
        f"- Candidate rescue rows: `{len(payload['candidate_rescues'])}`",
        f"- Incomplete files skipped: `{payload['incomplete_count']}`",
        "",
        "| Alpha | Virtue | Control | +Scripture | Delta | -Scripture | Delta | Null | Delta | + paired | - paired | Null paired |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _fmt(row["alpha"]),
                    row["virtue"],
                    _fmt(row["control_accuracy"]),
                    _fmt(row["positive_accuracy"]),
                    _fmt(row["positive_delta"]),
                    _fmt(row["negative_accuracy"]),
                    _fmt(row["negative_delta"]),
                    _fmt(row["null_accuracy"]),
                    _fmt(row["null_delta"]),
                    _paired_net(row["positive_paired"]),
                    _paired_net(row["negative_paired"]),
                    _paired_net(row["null_paired"]),
                ]
            )
            + " |"
        )

    if payload["candidate_rescues"]:
        lines.extend(["", "## Candidate Rescue Rows", ""])
        for row in payload["candidate_rescues"]:
            lines.append(
                f"- alpha `{_fmt(row['alpha'])}`, `{row['virtue']}`: "
                f"control `{_fmt(row['control_accuracy'])}`, "
                f"positive `{_fmt(row['positive_accuracy'])}`, "
                f"negative `{_fmt(row['negative_accuracy'])}`, "
                f"null `{_fmt(row['null_accuracy'])}`"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("results"),
        help="Path to the VirtueBench results directory.",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--md-out", type=Path, default=None)
    args = parser.parse_args()

    payload = collect(args.results_root)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(to_markdown(payload), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(to_markdown(payload))


if __name__ == "__main__":
    main()
