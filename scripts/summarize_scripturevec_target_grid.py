"""Summarize ScriptureVec target-grid result files.

This is for runs where each broad Scripture target is tested against each
VirtueBench virtue under positive, negative-alpha, and null-control lanes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _condition_parts(condition: str) -> tuple[str, str | None]:
    if ":" not in condition:
        return condition, None
    base, target = condition.split(":", 1)
    return base, target


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


def _index_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str | None], dict[str, Any]]:
    indexed = {}
    for row in rows:
        base, target = _condition_parts(str(row.get("condition")))
        indexed[(str(row.get("virtue")), base, target)] = row
    return indexed


def collect(result_path: Path, logs_path: Path | None = None) -> dict[str, Any]:
    result_rows = _load_json(result_path)
    if not isinstance(result_rows, list):
        raise ValueError(f"{result_path} does not contain a result list")
    log_rows: list[dict[str, Any]] = []
    if logs_path and logs_path.exists():
        loaded = _load_json(logs_path)
        if isinstance(loaded, list):
            log_rows = loaded

    result_index = _index_rows(result_rows)
    log_index = _index_rows(log_rows)

    virtues = sorted({str(row.get("virtue")) for row in result_rows})
    targets = sorted({
        target
        for row in result_rows
        for base, target in [_condition_parts(str(row.get("condition")))]
        if base in {"scripture_steer", "scripture_negative_alpha", "scripture_null_control"}
        and target is not None
    })

    rows: list[dict[str, Any]] = []
    for virtue in virtues:
        control = result_index.get((virtue, "control", None))
        log_control = log_index.get((virtue, "control", None))
        control_acc = control.get("accuracy") if control else None
        for target in targets:
            positive = result_index.get((virtue, "scripture_steer", target))
            negative = result_index.get((virtue, "scripture_negative_alpha", target))
            null = result_index.get((virtue, "scripture_null_control", target))
            log_positive = log_index.get((virtue, "scripture_steer", target))
            log_negative = log_index.get((virtue, "scripture_negative_alpha", target))
            log_null = log_index.get((virtue, "scripture_null_control", target))
            if not positive and not negative and not null:
                continue
            positive_acc = positive.get("accuracy") if positive else None
            negative_acc = negative.get("accuracy") if negative else None
            null_acc = null.get("accuracy") if null else None
            rows.append(
                {
                    "virtue": virtue,
                    "target": target,
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
                    "positive_paired": _paired_stats(log_control, log_positive),
                    "negative_paired": _paired_stats(log_control, log_negative),
                    "null_paired": _paired_stats(log_control, log_null),
                }
            )

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
        "result_file": str(result_path),
        "logs_file": str(logs_path) if logs_path else None,
        "row_count": len(rows),
        "targets": targets,
        "virtues": virtues,
        "candidate_rescues": candidate_rescues,
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
        "# ScriptureVec Target Grid Summary",
        "",
        f"- Result rows summarized: `{payload['row_count']}`",
        f"- Targets: `{', '.join(payload['targets'])}`",
        f"- Virtues: `{', '.join(payload['virtues'])}`",
        f"- Candidate rescue rows: `{len(payload['candidate_rescues'])}`",
        "",
        "| Virtue | Target | Control | +Scripture | Delta | -Scripture | Delta | Null | Delta | + paired | - paired | Null paired |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in sorted(payload["rows"], key=lambda item: (item["virtue"], item["target"])):
        lines.append(
            "| "
            + " | ".join(
                [
                    row["virtue"],
                    row["target"],
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
                f"- `{row['virtue']}` / `{row['target']}`: "
                f"control `{_fmt(row['control_accuracy'])}`, "
                f"positive `{_fmt(row['positive_accuracy'])}`, "
                f"negative `{_fmt(row['negative_accuracy'])}`, "
                f"null `{_fmt(row['null_accuracy'])}`"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_path", type=Path)
    parser.add_argument("--logs-path", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--md-out", type=Path, default=None)
    args = parser.parse_args()

    payload = collect(args.result_path, args.logs_path)
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
