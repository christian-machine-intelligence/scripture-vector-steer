"""Summarize ScriptureVec confirmed-chapter layer/alpha localization results."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any


STEM_RE = re.compile(
    r"scripturevec14_qwen3_14b_confirmed_chapter_layerloc_"
    r"(?:(?P<variant>fullgrid|expandedgrid|expandedgrid2)_)?"
    r"l(?P<center>\d+)_"
    r"(?P<tag>a\d+)_v1_ratio$"
)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _condition_parts(condition: str) -> tuple[str, str | None]:
    if ":" not in condition:
        return condition, None
    base, target = condition.split(":", 1)
    return base, target


def _index_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str | None], dict[str, Any]]:
    indexed = {}
    for row in rows:
        base, target = _condition_parts(str(row.get("condition")))
        indexed[(base, target)] = row
    return indexed


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
    for control_sample, candidate_sample in zip(control_samples[:compared], candidate_samples[:compared]):
        if control_sample.get("model_answer") != candidate_sample.get("model_answer"):
            stats["answer_changes"] += 1
        if control_sample.get("correct") != candidate_sample.get("correct"):
            stats["correctness_changes"] += 1
            if control_sample.get("correct") is False and candidate_sample.get("correct") is True:
                stats["improve"] += 1
            elif control_sample.get("correct") is True and candidate_sample.get("correct") is False:
                stats["regress"] += 1
    return stats


def _paired_net(stats: dict[str, int] | None) -> int | None:
    if not stats:
        return None
    return int(stats["improve"]) - int(stats["regress"])


def _paired_label(stats: dict[str, int] | None) -> str:
    if not stats:
        return "-"
    return f"{stats['answer_changes']} chg / {_paired_net(stats):+d} net"


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _alpha_from_rows(rows: list[dict[str, Any]], tag: str) -> float:
    for row in rows:
        metadata = row.get("metadata") or {}
        alpha = metadata.get("runtime_alpha_override")
        if alpha is not None:
            return abs(float(alpha))
    return float(tag.removeprefix("a"))


def collect(results_root: Path) -> dict[str, Any]:
    experiment_root = results_root / "experiments" / "scripturevec14"
    files = sorted(
        [
            *experiment_root.glob("scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l*_a*_v1_ratio.json"),
            *experiment_root.glob("scripturevec14_qwen3_14b_confirmed_chapter_layerloc_fullgrid_l*_a*_v1_ratio.json"),
            *experiment_root.glob("scripturevec14_qwen3_14b_confirmed_chapter_layerloc_expandedgrid_l*_a*_v1_ratio.json"),
            *experiment_root.glob("scripturevec14_qwen3_14b_confirmed_chapter_layerloc_expandedgrid2_l*_a*_v1_ratio.json"),
        ]
    )
    rows: list[dict[str, Any]] = []
    incomplete: list[dict[str, str]] = []

    for path in files:
        match = STEM_RE.match(path.stem)
        if not match:
            continue
        result_rows = _load_json(path)
        if not isinstance(result_rows, list):
            continue
        center = int(match.group("center"))
        tag = match.group("tag")
        alpha = _alpha_from_rows(result_rows, tag)
        indexed = _index_rows(result_rows)
        control = indexed.get(("control", None))
        if not control:
            incomplete.append({"result_file": str(path), "reason": "missing control"})
            continue

        logs_path = path.with_name(f"{path.stem}_logs.json")
        log_rows: list[dict[str, Any]] = []
        if logs_path.exists():
            loaded_logs = _load_json(logs_path)
            if isinstance(loaded_logs, list):
                log_rows = loaded_logs
        log_index = _index_rows(log_rows)
        log_control = log_index.get(("control", None))

        targets = sorted({
            target
            for base, target in indexed
            if base in {"scripture_steer", "scripture_negative_alpha", "scripture_null_control"}
            and target is not None
        })
        for target in targets:
            positive = indexed.get(("scripture_steer", target))
            negative = indexed.get(("scripture_negative_alpha", target))
            null = indexed.get(("scripture_null_control", target))
            if not positive or not negative or not null:
                incomplete.append({"result_file": str(path), "target": target, "reason": "missing condition"})
                continue

            control_acc = control.get("accuracy")
            positive_acc = positive.get("accuracy")
            negative_acc = negative.get("accuracy")
            null_acc = null.get("accuracy")
            positive_paired = _paired_stats(log_control, log_index.get(("scripture_steer", target)))
            negative_paired = _paired_stats(log_control, log_index.get(("scripture_negative_alpha", target)))
            null_paired = _paired_stats(log_control, log_index.get(("scripture_null_control", target)))
            positive_delta = None if control_acc is None or positive_acc is None else positive_acc - control_acc
            row = {
                "center": center,
                "alpha": alpha,
                "tag": tag,
                "target": target,
                "control_accuracy": control_acc,
                "positive_accuracy": positive_acc,
                "negative_accuracy": negative_acc,
                "null_accuracy": null_acc,
                "positive_delta": positive_delta,
                "negative_delta": None if control_acc is None or negative_acc is None else negative_acc - control_acc,
                "null_delta": None if control_acc is None or null_acc is None else null_acc - control_acc,
                "positive_paired": positive_paired,
                "negative_paired": negative_paired,
                "null_paired": null_paired,
                "result_file": str(path),
                "logs_file": str(logs_path) if logs_path.exists() else None,
            }
            positive_net = _paired_net(positive_paired)
            row["is_accuracy_rescue"] = (
                positive_delta is not None
                and positive_delta > 0
                and positive_acc is not None
                and positive_acc > max(value for value in [control_acc, negative_acc, null_acc] if value is not None)
            )
            row["is_paired_rescue"] = bool(row["is_accuracy_rescue"] and positive_net is not None and positive_net > 0)
            rows.append(row)

    rows.sort(key=lambda row: (row["center"], row["alpha"], row["target"]))

    by_cell: dict[tuple[int, float], dict[str, Any]] = {}
    for row in rows:
        key = (row["center"], row["alpha"])
        cell = by_cell.setdefault(
            key,
            {
                "center": row["center"],
                "alpha": row["alpha"],
                "row_count": 0,
                "accuracy_rescues": 0,
                "paired_rescues": 0,
                "positive_delta_values": [],
                "targets": [],
            },
        )
        cell["row_count"] += 1
        cell["accuracy_rescues"] += int(bool(row["is_accuracy_rescue"]))
        cell["paired_rescues"] += int(bool(row["is_paired_rescue"]))
        if row["positive_delta"] is not None:
            cell["positive_delta_values"].append(row["positive_delta"])
        if row["is_paired_rescue"]:
            cell["targets"].append(row["target"])

    cell_rows = []
    for cell in by_cell.values():
        deltas = cell.pop("positive_delta_values")
        cell["mean_positive_delta"] = mean(deltas) if deltas else None
        cell_rows.append(cell)
    cell_rows.sort(key=lambda row: (row["paired_rescues"], row["accuracy_rescues"], row["mean_positive_delta"] or -99), reverse=True)

    by_target: dict[str, dict[str, Any]] = {}
    for row in rows:
        target = row["target"]
        current = by_target.setdefault(
            target,
            {
                "target": target,
                "accuracy_rescues": 0,
                "paired_rescues": 0,
                "best_positive_accuracy": None,
                "best_cell": None,
            },
        )
        current["accuracy_rescues"] += int(bool(row["is_accuracy_rescue"]))
        current["paired_rescues"] += int(bool(row["is_paired_rescue"]))
        best = current["best_positive_accuracy"]
        if row["positive_accuracy"] is not None and (best is None or row["positive_accuracy"] > best):
            current["best_positive_accuracy"] = row["positive_accuracy"]
            current["best_cell"] = {
                "center": row["center"],
                "alpha": row["alpha"],
                "control_accuracy": row["control_accuracy"],
                "positive_accuracy": row["positive_accuracy"],
                "negative_accuracy": row["negative_accuracy"],
                "null_accuracy": row["null_accuracy"],
                "positive_paired": row["positive_paired"],
            }
    target_rows = sorted(
        by_target.values(),
        key=lambda row: (
            row["paired_rescues"],
            row["accuracy_rescues"],
            row["best_positive_accuracy"] or -1,
            row["target"],
        ),
        reverse=True,
    )

    return {
        "result_file_count": len({row["result_file"] for row in rows}),
        "row_count": len(rows),
        "centers": sorted({row["center"] for row in rows}),
        "alphas": sorted({row["alpha"] for row in rows}),
        "accuracy_rescue_count": sum(int(bool(row["is_accuracy_rescue"])) for row in rows),
        "paired_rescue_count": sum(int(bool(row["is_paired_rescue"])) for row in rows),
        "incomplete_count": len(incomplete),
        "incomplete": incomplete,
        "by_cell": cell_rows,
        "by_target": target_rows,
        "rows": rows,
    }


def to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# ScriptureVec Confirmed-Chapter Layer Localization Summary",
        "",
        f"- Result files summarized: `{payload['result_file_count']}`",
        f"- Rows summarized: `{payload['row_count']}`",
        f"- Centers found: `{', '.join(_fmt(value) for value in payload['centers'])}`",
        f"- Alphas found: `{', '.join(_fmt(value) for value in payload['alphas'])}`",
        f"- Accuracy rescue rows: `{payload['accuracy_rescue_count']}`",
        f"- Paired rescue rows: `{payload['paired_rescue_count']}`",
        f"- Incomplete rows skipped: `{payload['incomplete_count']}`",
        "",
        "## Best Center/Alpha Cells",
        "",
        "| Center | Alpha | Rows | Accuracy rescues | Paired rescues | Mean positive delta | Paired rescue targets |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for cell in payload["by_cell"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _fmt(cell["center"]),
                    _fmt(cell["alpha"]),
                    _fmt(cell["row_count"]),
                    _fmt(cell["accuracy_rescues"]),
                    _fmt(cell["paired_rescues"]),
                    _fmt(cell["mean_positive_delta"]),
                    ", ".join(f"`{target}`" for target in cell["targets"]) or "-",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Target Stability",
            "",
            "| Target | Accuracy rescues | Paired rescues | Best cell | Best control | Best +Scripture | Best -Scripture | Best null | Best + paired |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for target in payload["by_target"]:
        best = target.get("best_cell") or {}
        best_label = "-" if not best else f"L{best['center']} / alpha {best['alpha']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{target['target']}`",
                    _fmt(target["accuracy_rescues"]),
                    _fmt(target["paired_rescues"]),
                    best_label,
                    _fmt(best.get("control_accuracy")),
                    _fmt(best.get("positive_accuracy")),
                    _fmt(best.get("negative_accuracy")),
                    _fmt(best.get("null_accuracy")),
                    _paired_label(best.get("positive_paired")),
                ]
            )
            + " |"
        )

    paired_rows = [row for row in payload["rows"] if row["is_paired_rescue"]]
    if paired_rows:
        lines.extend(["", "## Paired Rescue Rows", ""])
        for row in paired_rows:
            lines.append(
                f"- `L{row['center']}` alpha `{_fmt(row['alpha'])}` / `{row['target']}`: "
                f"control `{_fmt(row['control_accuracy'])}`, "
                f"positive `{_fmt(row['positive_accuracy'])}`, "
                f"negative `{_fmt(row['negative_accuracy'])}`, "
                f"null `{_fmt(row['null_accuracy'])}`, "
                f"+ paired `{_paired_label(row['positive_paired'])}`"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("results"))
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
