#!/usr/bin/env python3
"""Analyse the three disjoint-slice retest summaries.

Run after the three Windows launchers under ``scripts/disjoint_slice/`` have
finished and the three summary JSONs have been copied into
``results/paper/scripturevec_justice/key_data/disjoint_slice/``.

Outputs (written next to the input JSONs):

- ``per_row_disjoint_stats.csv``
- ``cohort_comparison.csv``
- ``disjoint_slice_summary.json``

The script is CPU-only and uses stdlib + the exact-McNemar machinery
from ``scripts/scripturevec_justice_stats.py``.

Decision rules applied per (chapter, cell) row:

1. **Pass rule** (paper §3.5): positive_acc strictly beats max(control,
   negative, null) AND positive_net > 0.
2. **Per-row significance**: exact two-sided McNemar p < 0.05.
3. **Family-corrected**: BH-FDR q < 0.05 across the 48 disjoint-slice
   rows (16 chapters x 3 cells).

Per-chapter headline decisions (rolled up from the per-row table):

- ``promoted``: passes rule (1) on at least one cell *and* reaches
  BH q < 0.05 on at least one cell.
- ``candidate``: passes rule (1) on at least one cell, but no row
  reaches BH q < 0.05.
- ``demoted``: fails rule (1) on every cell.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Reuse the exact tests + BH/Bonferroni from PR1's stats script.
from scripturevec_justice_stats import (  # type: ignore  # noqa: E402
    benjamini_hochberg,
    bonferroni,
    mcnemar_exact_one_sided,
    mcnemar_exact_two_sided,
)


DISJOINT_DIR = REPO_ROOT / "results" / "paper" / "scripturevec_justice" / "key_data" / "disjoint_slice"
NESTED_STABILITY = REPO_ROOT / "results" / "paper" / "scripturevec_justice" / "key_data" / "chapter_stability_by_localization.csv"
NESTED_CONFIRMATION = REPO_ROOT / "results" / "paper" / "scripturevec_justice" / "key_data" / "chapter_confirmation_l40_survivors.csv"


SUMMARY_RE = re.compile(
    r"scripturevec14_qwen3_14b_disjoint_l40_o40_L(?P<center>\d+)_a(?P<alpha>\d+)_v1_summary\.json$"
)


CHAPTER_TARGETS = [
    "chapter_deu_16", "chapter_jdg_07", "chapter_jdg_09",
    "chapter_num_11", "chapter_num_22", "chapter_num_27",
    "chapter_1ch_09", "chapter_1ch_29",
    "chapter_act_07", "chapter_act_11", "chapter_act_16", "chapter_act_27",
    "chapter_heb_02", "chapter_heb_07", "chapter_heb_09", "chapter_heb_10",
]


# ---------------------------------------------------------------------------
# Summary-JSON parsing
# ---------------------------------------------------------------------------

def _condition_parts(condition: str) -> Tuple[str, Optional[str]]:
    if ":" not in condition:
        return condition, None
    base, target = condition.split(":", 1)
    return base, target


def _index_rows(rows: List[dict]) -> Dict[Tuple[str, Optional[str]], dict]:
    out: Dict[Tuple[str, Optional[str]], dict] = {}
    for row in rows:
        base, target = _condition_parts(str(row.get("condition")))
        out[(base, target)] = row
    return out


def _paired_stats(control: Optional[dict], candidate: Optional[dict]) -> Optional[Tuple[int, int]]:
    """Return (b, c): (wrong->right, right->wrong) flips relative to control."""
    if not control or not candidate:
        return None
    c_samples = control.get("sample_details") or []
    s_samples = candidate.get("sample_details") or []
    compared = min(len(c_samples), len(s_samples))
    b = c = 0
    for cs, ss in zip(c_samples[:compared], s_samples[:compared]):
        c_ok = cs.get("correct")
        s_ok = ss.get("correct")
        if c_ok is False and s_ok is True:
            b += 1
        elif c_ok is True and s_ok is False:
            c += 1
    return (b, c)


def _load_cell(path: Path) -> Optional[dict]:
    m = SUMMARY_RE.search(path.name)
    if not m:
        return None
    center = int(m.group("center"))
    alpha = int(m.group("alpha"))
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of rows in {path}, got {type(payload).__name__}")
    indexed = _index_rows(payload)
    control = indexed.get(("control", None))
    if control is None:
        raise ValueError(f"Missing control row in {path}")
    cell = {
        "center_layer": center,
        "alpha": alpha,
        "source_file": path.name,
        "control_accuracy": control.get("accuracy"),
        "n_items": len(control.get("sample_details") or []),
        "rows": [],
    }
    for target in CHAPTER_TARGETS:
        pos = indexed.get(("scripture_steer", target))
        neg = indexed.get(("scripture_negative_alpha", target))
        nul = indexed.get(("scripture_null_control", target))
        if not (pos and neg and nul):
            cell["rows"].append({
                "target": target,
                "control_accuracy": control.get("accuracy"),
                "positive_accuracy": None,
                "negative_accuracy": None,
                "null_accuracy": None,
                "b_wrong_to_right": None,
                "c_right_to_wrong": None,
                "paired_rescue": False,
                "p_value_two_sided": None,
                "p_value_one_sided": None,
                "note": "missing condition",
            })
            continue
        paired = _paired_stats(control, pos)
        b, c = paired if paired else (0, 0)
        pos_acc = pos.get("accuracy")
        neg_acc = neg.get("accuracy")
        null_acc = nul.get("accuracy")
        ctrl_acc = control.get("accuracy")
        is_rescue = (
            pos_acc is not None and ctrl_acc is not None
            and pos_acc > ctrl_acc
            and pos_acc > max(v for v in [ctrl_acc, neg_acc, null_acc] if v is not None)
            and b > c
        )
        cell["rows"].append({
            "target": target,
            "control_accuracy": ctrl_acc,
            "positive_accuracy": pos_acc,
            "negative_accuracy": neg_acc,
            "null_accuracy": null_acc,
            "b_wrong_to_right": b,
            "c_right_to_wrong": c,
            "discordant_pairs": b + c,
            "paired_rescue": is_rescue,
            "p_value_two_sided": mcnemar_exact_two_sided(b, c),
            "p_value_one_sided": mcnemar_exact_one_sided(b, c, "positive"),
        })
    return cell


# ---------------------------------------------------------------------------
# Cross-reference with nested-slice numbers
# ---------------------------------------------------------------------------

def _load_nested_stability() -> Dict[str, int]:
    out: Dict[str, int] = {}
    if not NESTED_STABILITY.exists():
        return out
    with NESTED_STABILITY.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out[row["target"]] = int(row["paired_rescue_count"])
    return out


def _load_nested_confirmation() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    if not NESTED_CONFIRMATION.exists():
        return out
    with NESTED_CONFIRMATION.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out[row["target"]] = {
                "control_accuracy": float(row["control_accuracy"]),
                "positive_accuracy": float(row["positive_accuracy"]),
                "positive_delta": float(row["positive_delta"]),
                "negative_accuracy": float(row["negative_accuracy"]),
                "null_accuracy": float(row["null_accuracy"]),
                "paired_field": row["positive_paired"],
            }
    return out


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _write_per_row_csv(path: Path, all_rows: List[dict]) -> None:
    p_two_list = [r["p_value_two_sided"] for r in all_rows if r["p_value_two_sided"] is not None]
    bh_lookup = dict(zip(
        [i for i, r in enumerate(all_rows) if r["p_value_two_sided"] is not None],
        benjamini_hochberg(p_two_list),
    ))
    bon_lookup = dict(zip(
        [i for i, r in enumerate(all_rows) if r["p_value_two_sided"] is not None],
        bonferroni(p_two_list),
    ))
    fieldnames = [
        "target", "center_layer", "alpha",
        "control_accuracy", "positive_accuracy",
        "negative_accuracy", "null_accuracy",
        "b_wrong_to_right", "c_right_to_wrong", "discordant_pairs",
        "paired_rescue",
        "p_value_two_sided", "p_value_one_sided",
        "p_bh_fdr_adjusted", "p_bonferroni_adjusted",
        "note",
    ]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for i, row in enumerate(all_rows):
            out = {k: row.get(k) for k in fieldnames}
            out["p_bh_fdr_adjusted"] = bh_lookup.get(i)
            out["p_bonferroni_adjusted"] = bon_lookup.get(i)
            for key in ("p_value_two_sided", "p_value_one_sided",
                        "p_bh_fdr_adjusted", "p_bonferroni_adjusted"):
                if out[key] is not None:
                    out[key] = f"{out[key]:.6f}"
            w.writerow(out)


def _decide(rows_for_target: List[dict]) -> str:
    rescue_cells = [r for r in rows_for_target if r.get("paired_rescue")]
    if not rescue_cells:
        return "demoted"
    sig = [r for r in rescue_cells if r.get("p_bh_fdr_adjusted") is not None and r["p_bh_fdr_adjusted"] < 0.05]
    return "promoted" if sig else "candidate"


def _write_cohort_csv(path: Path, all_rows: List[dict], nested_stability: Dict[str, int],
                     nested_confirmation: Dict[str, dict]) -> None:
    by_target: Dict[str, List[dict]] = {t: [] for t in CHAPTER_TARGETS}
    for row in all_rows:
        by_target[row["target"]].append(row)
    fieldnames = [
        "target",
        "nested_paired_rescue_count_out_of_43",
        "nested_l40_positive_delta",
        "disjoint_L30a96_paired_rescue",
        "disjoint_L28a16_paired_rescue",
        "disjoint_L24a32_paired_rescue",
        "disjoint_min_bh_fdr_q",
        "decision",
    ]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for target in CHAPTER_TARGETS:
            rows = by_target[target]
            by_cell = {(r["center_layer"], r["alpha"]): r for r in rows}
            row = {
                "target": target,
                "nested_paired_rescue_count_out_of_43": nested_stability.get(target, ""),
                "nested_l40_positive_delta": nested_confirmation.get(target, {}).get("positive_delta", ""),
                "disjoint_L30a96_paired_rescue": _yn(by_cell.get((30, 96))),
                "disjoint_L28a16_paired_rescue": _yn(by_cell.get((28, 16))),
                "disjoint_L24a32_paired_rescue": _yn(by_cell.get((24, 32))),
                "disjoint_min_bh_fdr_q": _min_bh(rows),
                "decision": _decide(rows),
            }
            w.writerow(row)


def _yn(row: Optional[dict]) -> str:
    if not row:
        return ""
    return "yes" if row.get("paired_rescue") else "no"


def _min_bh(rows: List[dict]) -> str:
    qs = [r.get("p_bh_fdr_adjusted") for r in rows if r.get("p_bh_fdr_adjusted") is not None]
    if not qs:
        return ""
    return f"{min(qs):.6f}"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    if not DISJOINT_DIR.exists():
        print(f"ERROR: {DISJOINT_DIR} does not exist. Copy the three disjoint-slice summary JSONs there.")
        return 1
    summary_files = sorted(p for p in DISJOINT_DIR.glob("*_summary.json") if SUMMARY_RE.search(p.name))
    if not summary_files:
        print(f"ERROR: no disjoint-slice summary JSONs found in {DISJOINT_DIR}.")
        return 1

    cells = [c for c in (_load_cell(p) for p in summary_files) if c]
    all_rows: List[dict] = []
    for cell in cells:
        for row in cell["rows"]:
            all_rows.append({**row, "center_layer": cell["center_layer"], "alpha": cell["alpha"]})

    # Per-row CSV with FDR-corrected p-values.
    per_row_path = DISJOINT_DIR / "per_row_disjoint_stats.csv"
    _write_per_row_csv(per_row_path, all_rows)

    # Re-load the per-row CSV with adjusted p-values so cohort can use them.
    with per_row_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        full_rows = []
        for r in reader:
            r["paired_rescue"] = r["paired_rescue"] == "True"
            for k in ("p_value_two_sided", "p_value_one_sided",
                      "p_bh_fdr_adjusted", "p_bonferroni_adjusted"):
                r[k] = float(r[k]) if r.get(k) else None
            r["center_layer"] = int(r["center_layer"])
            r["alpha"] = int(r["alpha"])
            full_rows.append(r)

    nested_stability = _load_nested_stability()
    nested_confirmation = _load_nested_confirmation()

    cohort_path = DISJOINT_DIR / "cohort_comparison.csv"
    _write_cohort_csv(cohort_path, full_rows, nested_stability, nested_confirmation)

    summary = {
        "disjoint_slice_offset": 40,
        "disjoint_slice_limit": 40,
        "disjoint_slice_items_covered": "40..79",
        "cells_evaluated": [
            {"center_layer": c["center_layer"], "alpha": c["alpha"],
             "control_accuracy": c["control_accuracy"], "n_items": c["n_items"]}
            for c in cells
        ],
        "rows": len(all_rows),
        "rescue_count": sum(1 for r in full_rows if r["paired_rescue"]),
        "rescue_with_bh_fdr_under_05": sum(
            1 for r in full_rows
            if r["paired_rescue"] and r.get("p_bh_fdr_adjusted") is not None
            and r["p_bh_fdr_adjusted"] < 0.05
        ),
        "rescue_with_bonferroni_under_05": sum(
            1 for r in full_rows
            if r["paired_rescue"] and r.get("p_bonferroni_adjusted") is not None
            and r["p_bonferroni_adjusted"] < 0.05
        ),
    }
    by_target: Dict[str, List[dict]] = {t: [] for t in CHAPTER_TARGETS}
    for r in full_rows:
        by_target[r["target"]].append(r)
    summary["promoted_chapters"] = [t for t in CHAPTER_TARGETS if _decide(by_target[t]) == "promoted"]
    summary["candidate_chapters"] = [t for t in CHAPTER_TARGETS if _decide(by_target[t]) == "candidate"]
    summary["demoted_chapters"] = [t for t in CHAPTER_TARGETS if _decide(by_target[t]) == "demoted"]

    summary_path = DISJOINT_DIR / "disjoint_slice_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {per_row_path.name}, {cohort_path.name}, {summary_path.name}")
    print(json.dumps({
        "rescue_count": summary["rescue_count"],
        "rescue_with_bh_fdr_under_05": summary["rescue_with_bh_fdr_under_05"],
        "promoted": len(summary["promoted_chapters"]),
        "candidate": len(summary["candidate_chapters"]),
        "demoted": len(summary["demoted_chapters"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
