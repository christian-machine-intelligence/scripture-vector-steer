#!/usr/bin/env python3
"""Per-row statistical tests for the ScriptureVec Justice pipeline.

Reads the curated paper-facing CSVs in
``results/paper/scripturevec_justice/key_data/`` and emits exact McNemar
p-values plus Benjamini--Hochberg (FDR) and Bonferroni adjusted p-values
for every condition at every pipeline stage. Cell-level rescue counts
from the layer/alpha localization grid are reported with Clopper--Pearson
95% binomial confidence intervals.

The discordant-pair counts are reconstructed from the ``positive_paired``
field ("X chg / +Y net"): X is total discordant pairs (b + c), Y is the
signed net (b - c), so b = (X + Y) / 2 wrong-to-right flips and
c = (X - Y) / 2 right-to-wrong flips. The exact McNemar test uses the
two-sided binomial mass for k = min(b, c) under H0: p = 0.5.

Outputs land in ``results/paper/scripturevec_justice/key_data/stats/``:

- ``book_discovery_l10_stats.csv``     paired exact + BH/Bonferroni
- ``book_confirmation_l40_stats.csv``  same for the 19 candidates
- ``chapter_discovery_l10_stats.csv``  same for the 38 hits
- ``chapter_confirmation_l40_stats.csv`` same for the 38 candidates
- ``layer_alpha_cell_cis.csv``         Clopper-Pearson 95% CI per cell
- ``stats_summary.json``               machine-readable rollup
"""

from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

KEY_DATA = Path(__file__).resolve().parents[1] / "results" / "paper" / "scripturevec_justice" / "key_data"
STATS_DIR = KEY_DATA / "stats"


# ---------------------------------------------------------------------------
# Exact tests (no scipy dependency)
# ---------------------------------------------------------------------------

def _binom_coeff(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def _binom_pmf(k: int, n: int, p: float = 0.5) -> float:
    return _binom_coeff(n, k) * (p ** k) * ((1 - p) ** (n - k))


def mcnemar_exact_two_sided(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value with H0: p = 0.5 on b + c discordants.

    For b == c == 0 the test is undefined; we return p = 1.0 because no
    information is available against the null.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(_binom_pmf(i, n, 0.5) for i in range(k + 1))
    return min(1.0, 2.0 * tail)


def mcnemar_exact_one_sided(b: int, c: int, direction: str = "positive") -> float:
    """One-sided exact McNemar p-value.

    direction="positive" tests H1: b > c (positive steering moves items
    from wrong to right more often than the reverse).
    """
    n = b + c
    if n == 0:
        return 1.0
    if direction == "positive":
        return sum(_binom_pmf(i, n, 0.5) for i in range(b, n + 1))
    return sum(_binom_pmf(i, n, 0.5) for i in range(c, n + 1))


def _binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0 if k < n else 1.0
    return sum(_binom_pmf(i, n, p) for i in range(0, k + 1))


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Exact two-sided Clopper-Pearson confidence interval for Binomial(n, p).

    Bisects directly on the binomial CDF: the lower bound is the p that
    makes P(X >= k | n, p) = alpha / 2, and the upper bound is the p that
    makes P(X <= k | n, p) = alpha / 2. Avoids any scipy dependency.
    """
    if n == 0:
        return (0.0, 1.0)
    if k == 0:
        lo = 0.0
    else:
        # Lower bound: largest p such that P(X >= k | n, p) <= alpha/2,
        # equivalently 1 - P(X <= k - 1 | n, p) = alpha/2.
        lo = _bisect_p(lambda p: 1.0 - _binom_cdf(k - 1, n, p), alpha / 2)
    if k == n:
        hi = 1.0
    else:
        # Upper bound: smallest p such that P(X <= k | n, p) <= alpha/2.
        hi = _bisect_p(lambda p: _binom_cdf(k, n, p), alpha / 2, decreasing=True)
    return (lo, hi)


def _bisect_p(fn, target: float, decreasing: bool = False) -> float:
    """Bisection on p in [0, 1] to find p with fn(p) ~= target."""
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        value = fn(mid)
        below = value < target
        if decreasing:
            below = not below
        if below:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Multiple-comparison corrections
# ---------------------------------------------------------------------------

def benjamini_hochberg(pvalues: List[float]) -> List[float]:
    """Return BH-adjusted (q) values that preserve input order."""
    m = len(pvalues)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    cumulative_min = 1.0
    for rank, idx in enumerate(reversed(order), start=1):
        r = m - rank + 1
        raw = pvalues[idx] * m / r
        cumulative_min = min(cumulative_min, raw)
        adjusted[idx] = min(1.0, cumulative_min)
    return adjusted


def bonferroni(pvalues: List[float]) -> List[float]:
    m = len(pvalues)
    return [min(1.0, p * m) for p in pvalues]


# ---------------------------------------------------------------------------
# Discordant-pair reconstruction from "X chg / +Y net"
# ---------------------------------------------------------------------------

PAIRED_RE = re.compile(r"\s*(-?\d+)\s*chg\s*/\s*([+\-]?\d+)\s*net\s*")


def parse_paired(field: str) -> Tuple[int, int]:
    """Return (b = wrong->right, c = right->wrong) from a paired string."""
    if not field:
        return (0, 0)
    match = PAIRED_RE.match(field)
    if not match:
        return (0, 0)
    discordant = int(match.group(1))
    net = int(match.group(2))
    if discordant < 0 or abs(net) > discordant or (discordant - net) % 2 != 0:
        return (0, 0)
    b = (discordant + net) // 2
    c = (discordant - net) // 2
    return (b, c)


# ---------------------------------------------------------------------------
# Input reading
# ---------------------------------------------------------------------------

@dataclass
class StageRow:
    stage: str
    target: str
    reference: str
    survived: Optional[str]
    paired_field: str
    control_accuracy: Optional[float]
    positive_accuracy: Optional[float]
    negative_accuracy: Optional[float]
    null_accuracy: Optional[float]


def _read_rows(path: Path, has_survived: bool) -> List[StageRow]:
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        out: List[StageRow] = []
        for row in reader:
            out.append(
                StageRow(
                    stage=row.get("stage", ""),
                    target=row.get("target", ""),
                    reference=row.get("reference", row.get("target", "")),
                    survived=row.get("survived") if has_survived else None,
                    paired_field=row.get("positive_paired", ""),
                    control_accuracy=_safe_float(row.get("control_accuracy")),
                    positive_accuracy=_safe_float(row.get("positive_accuracy")),
                    negative_accuracy=_safe_float(row.get("negative_accuracy")),
                    null_accuracy=_safe_float(row.get("null_accuracy")),
                )
            )
    return out


def _safe_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Per-stage analysis
# ---------------------------------------------------------------------------

STAGE_SOURCES = [
    ("book_discovery_l10",       "book_discovery_l10_candidates.csv",        10, False),
    ("book_confirmation_l40",    "book_confirmation_l40_all_candidates.csv", 40, True),
    ("chapter_discovery_l10",    "chapter_discovery_l10_clean_hits.csv",     10, False),
    ("chapter_confirmation_l40", "chapter_confirmation_l40_all_candidates.csv", 40, True),
]


def _stage_records(rows: Iterable[StageRow], slice_n: int):
    records = []
    for row in rows:
        b, c = parse_paired(row.paired_field)
        p_two = mcnemar_exact_two_sided(b, c)
        p_one = mcnemar_exact_one_sided(b, c, direction="positive")
        records.append({
            "target": row.target,
            "reference": row.reference,
            "survived": row.survived,
            "slice_n": slice_n,
            "control_accuracy": row.control_accuracy,
            "positive_accuracy": row.positive_accuracy,
            "negative_accuracy": row.negative_accuracy,
            "null_accuracy": row.null_accuracy,
            "paired_field": row.paired_field,
            "b_wrong_to_right": b,
            "c_right_to_wrong": c,
            "discordant_pairs": b + c,
            "p_value_two_sided": p_two,
            "p_value_one_sided": p_one,
        })
    p_values = [r["p_value_two_sided"] for r in records]
    bh = benjamini_hochberg(p_values)
    bon = bonferroni(p_values)
    for record, q, b_adj in zip(records, bh, bon):
        record["p_bh_fdr_adjusted"] = q
        record["p_bonferroni_adjusted"] = b_adj
    return records


def _write_stage_csv(path: Path, records):
    fieldnames = [
        "target", "reference", "survived", "slice_n",
        "control_accuracy", "positive_accuracy",
        "negative_accuracy", "null_accuracy",
        "paired_field", "b_wrong_to_right", "c_right_to_wrong",
        "discordant_pairs",
        "p_value_two_sided", "p_value_one_sided",
        "p_bh_fdr_adjusted", "p_bonferroni_adjusted",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {k: record.get(k) for k in fieldnames}
            for key in ("p_value_two_sided", "p_value_one_sided",
                        "p_bh_fdr_adjusted", "p_bonferroni_adjusted"):
                value = row[key]
                if value is None:
                    continue
                row[key] = f"{value:.6f}"
            writer.writerow(row)


def _significant_count(records, key: str, threshold: float = 0.05) -> int:
    return sum(1 for r in records if r[key] is not None and r[key] < threshold)


# ---------------------------------------------------------------------------
# Cell-level binomial CIs
# ---------------------------------------------------------------------------

def _cell_cis():
    path = KEY_DATA / "layer_alpha_cells.csv"
    records = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            n = int(row.get("rows", 16))
            k = int(row.get("paired_rescues", 0))
            lo, hi = clopper_pearson_ci(k, n)
            records.append({
                "center_layer": int(row["center_layer"]),
                "alpha": int(float(row["alpha"])),
                "rows": n,
                "paired_rescues": k,
                "rescue_proportion": k / n if n else 0.0,
                "ci_lower": lo,
                "ci_upper": hi,
                "mean_positive_delta": _safe_float(row.get("mean_positive_delta")) or 0.0,
            })
    return records


def _write_cell_csv(path: Path, records):
    fieldnames = [
        "center_layer", "alpha", "rows", "paired_rescues",
        "rescue_proportion", "ci_lower", "ci_upper", "mean_positive_delta",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for key in ("rescue_proportion", "ci_lower", "ci_upper", "mean_positive_delta"):
                row[key] = f"{row[key]:.4f}"
            writer.writerow(row)


def _regime_ci_overlap(cells):
    by_key = {(c["center_layer"], c["alpha"]): c for c in cells}
    regimes = {
        "L30/a96": (30, 96),
        "L28/a16": (28, 16),
        "L24/a32": (24, 32),
        "L31/a96": (31, 96),
        "L32/a32": (32, 32),
        "L30/a64": (30, 64),
        "L31/a48": (31, 48),
    }
    out = {}
    for name, key in regimes.items():
        cell = by_key.get(key)
        if cell is None:
            continue
        out[name] = {
            "paired_rescues": cell["paired_rescues"],
            "rows": cell["rows"],
            "proportion": cell["rescue_proportion"],
            "ci_lower": cell["ci_lower"],
            "ci_upper": cell["ci_upper"],
            "mean_positive_delta": cell["mean_positive_delta"],
        }
    return out


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def sign_test_exact(up: int, down: int) -> float:
    """Exact two-sided sign test on the non-tied rows."""
    n = up + down
    if n == 0:
        return 1.0
    observed = max(up, down)
    tail = sum(_binom_coeff(n, k) for k in range(observed, n + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


HELD_OUT_SOURCES = [
    ("books", "book_discovery_l10_candidates.csv", "book_confirmation_l40_all_candidates.csv", "reference"),
    ("chapters", "chapter_discovery_l10_clean_hits.csv", "chapter_confirmation_l40_all_candidates.csv", "target"),
]


def _held_out_analysis():
    """Compare positive steering against control on the items NOT used to select candidates.

    Candidates enter the limit-40 stage because positive steering beat the
    controls on items 0-9, and because the sampler is deterministic those ten
    items sit *inside* the forty. Items 10-39 are therefore the only part of
    the confirmation run that is independent of the selection. Differencing the
    two stages recovers each condition's score on that held-out remainder.
    """
    out = {}
    for label, l10_file, l40_file, key in HELD_OUT_SOURCES:
        l10 = {r[key]: r for r in csv.DictReader((KEY_DATA / l10_file).open(newline=""))}
        rows = list(csv.DictReader((KEY_DATA / l40_file).open(newline="")))
        ahead = behind = tied = 0
        survivor_ahead = survivor_behind = survivor_tied = 0
        details = []
        for r in rows:
            if r[key] not in l10:
                continue
            a = l10[r[key]]
            pos = round(float(r["positive_accuracy"]) * 40) - round(float(a["positive_accuracy"]) * 10)
            ctl = round(float(r["control_accuracy"]) * 40) - round(float(a["control_accuracy"]) * 10)
            diff = pos - ctl
            ahead += diff > 0
            behind += diff < 0
            tied += diff == 0
            if r.get("survived") == "yes":
                survivor_ahead += diff > 0
                survivor_behind += diff < 0
                survivor_tied += diff == 0
            details.append({
                "target": r[key],
                "positive_correct_items_10_39": pos,
                "control_correct_items_10_39": ctl,
                "difference": diff,
                "survived": r.get("survived", ""),
            })
        _write_held_out_csv(STATS_DIR / f"held_out_items_{label}.csv", details)
        out[label] = {
            "rows": len(details),
            "held_out_items": 30,
            "positive_ahead_of_control": ahead,
            "positive_behind_control": behind,
            "tied": tied,
            "sign_test_p": round(sign_test_exact(ahead, behind), 6),
            "survivors_ahead": survivor_ahead,
            "survivors_behind": survivor_behind,
            "survivors_tied": survivor_tied,
        }
    return out


def _write_held_out_csv(path: Path, details):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "target",
                "positive_correct_items_10_39",
                "control_correct_items_10_39",
                "difference",
                "survived",
            ],
        )
        writer.writeheader()
        for row in details:
            writer.writerow(row)


def main():
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {"stages": {}}

    for stage, filename, slice_n, has_survived in STAGE_SOURCES:
        rows = _read_rows(KEY_DATA / filename, has_survived=has_survived)
        records = _stage_records(rows, slice_n)
        _write_stage_csv(STATS_DIR / f"{stage}_stats.csv", records)
        summary["stages"][stage] = {
            "slice_n": slice_n,
            "row_count": len(records),
            "candidates_with_positive_movement": sum(
                1 for r in records if r["b_wrong_to_right"] > r["c_right_to_wrong"]
            ),
            "significant_uncorrected_p05": _significant_count(records, "p_value_two_sided"),
            "significant_bh_fdr_q05": _significant_count(records, "p_bh_fdr_adjusted"),
            "significant_bonferroni_p05": _significant_count(records, "p_bonferroni_adjusted"),
        }

    cells = _cell_cis()
    _write_cell_csv(STATS_DIR / "layer_alpha_cell_cis.csv", cells)
    summary["layer_alpha_cell_cis"] = _regime_ci_overlap(cells)
    summary["held_out_items"] = _held_out_analysis()
    summary["interpretation"] = {
        "rescue_rule": (
            "A row counts as a paired rescue iff positive_acc > max(control, negative, "
            "null) strictly and the net item-level paired movement (b - c) is positive."
        ),
        "test_notes": (
            "Per-row p-values use the exact two-sided McNemar test reconstructed from "
            "the (b, c) discordant pairs implicit in the 'X chg / +/-Y net' field. "
            "Family corrections are applied within each stage."
        ),
        "ci_notes": (
            "Cell rescue counts use exact two-sided Clopper-Pearson 95% intervals on "
            "Binomial(rows = 16 chapters, p)."
        ),
        "held_out_notes": (
            "Items 0-9 select the candidates and are nested inside the limit-40 slice, "
            "so items 10-39 are the only independent part of the confirmation run. "
            "Positive steering is compared against control on that remainder alone. "
            "This is the paper's cleanest test of whether the effect is real, and it "
            "is the one the paper's headline rests on: see paper section 4.5."
        ),
    }

    (STATS_DIR / "stats_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote stage CSVs and {STATS_DIR / 'stats_summary.json'}")


if __name__ == "__main__":
    main()
