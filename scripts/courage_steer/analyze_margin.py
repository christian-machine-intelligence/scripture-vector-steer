#!/usr/bin/env python3
"""Margin-shift statistics for the courage steering pilot (CPU-only, stdlib).

Reads the per-item pilot output written by ``run_courage_pilot.py``:

    results/courage_pilot/pilot_results.json

Each record is one model decision on one binary VirtueBench-style item under
one steering condition, with a signed ``margin`` (positive = leans toward the
courageous option ``target``). Conditions:

  control   no steering (baseline)
  steer     the vector pushed in its intended (courageous) direction
  reversed  the SAME vector pushed the opposite way (asymmetry probe)
  null      a random/placebo vector at matched norm (noise floor)

Vectors (the thing being steered with):

  ideal_courage   a hand-built "known-good" courage direction  -> the YARDSTICK
  whole_bible     a direction distilled from Scripture at large
  courage_pool    a direction distilled only from courage pericopes

For every vector we pair each EVAL item's steered margin against its own
control margin and ask three questions:

  1. Does ``steer`` move the margin toward courage?      (mean shift, CI, tests)
  2. Does ``reversed`` HURT (negative shift)?            (real directions are
     asymmetric: flipping the sign should cost you)
  3. How big is the ``null`` shift?                      (the noise floor)

We then express each vector's steer shift as a fraction of the
``ideal_courage`` steer shift (the yardstick) and relative to the null floor,
run a secondary binary McNemar on model-answer flips, and gate everything on a
validation check that the sign of ``margin`` actually agrees with the discrete
``model_answer == target`` on control.

Reused, not reimplemented (from ``scripts/scripturevec_justice_stats.py``):
``benjamini_hochberg``, ``bonferroni``, ``clopper_pearson_ci``. We also reuse
its exact McNemar helpers when present. The paired t-test and Wilcoxon
signed-rank test are implemented here with the standard library only; if
``scipy`` is importable we defer to it for those two.

Usage::

    python scripts/courage_steer/analyze_margin.py
    python scripts/courage_steer/analyze_margin.py --smoke   # tiny inputs OK

Writes ``results/courage_pilot/margin_analysis.json`` and prints a report that
ends with an explicit VERDICT.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Reuse the audited stats primitives from the justice pipeline.
# ---------------------------------------------------------------------------
_THIS = Path(__file__).resolve()
ROOT = _THIS.parents[2]                       # .../scripture-vector-steer-courage
SCRIPTS_DIR = _THIS.parents[1]                # .../scripts
sys.path.insert(0, str(SCRIPTS_DIR))

from scripturevec_justice_stats import (  # noqa: E402
    benjamini_hochberg,
    bonferroni,
    clopper_pearson_ci,
)

# The justice module also carries exact McNemar helpers; reuse if present.
try:  # pragma: no cover - trivial import guard
    from scripturevec_justice_stats import (  # noqa: E402
        mcnemar_exact_two_sided as _mcnemar_two_sided,
    )
except ImportError:  # pragma: no cover
    _mcnemar_two_sided = None

# scipy is preferred for the t-test / Wilcoxon if it happens to be importable.
try:  # pragma: no cover - depends on environment
    from scipy import stats as _scipy_stats  # type: ignore
    _HAVE_SCIPY = True
except Exception:  # pragma: no cover
    _scipy_stats = None
    _HAVE_SCIPY = False


RESULTS = ROOT / "results" / "courage_pilot"
INPUT_PATH = RESULTS / "pilot_results.json"
OUTPUT_PATH = RESULTS / "margin_analysis.json"

VECTORS = ["ideal_courage", "whole_bible", "courage_pool"]
YARDSTICK = "ideal_courage"
CONDITIONS = ["control", "steer", "reversed", "null"]

# Validation-gate threshold: margin sign must agree with the discrete
# model_answer this often on control for the margin proxy to be trusted.
AGREEMENT_GATE = 0.80

# "close to the null floor" tolerance when deciding whole_bible ~= null.
# Expressed as a multiple of the null floor's absolute size.
FLOOR_MULTIPLE = 1.5

# A shift is "meaningfully nonzero" if its 95% CI excludes 0 AND it clears the
# null floor. The yardstick itself must clear this to call the model steerable.
ZERO_SHIFT_ABS = 1e-9


# ===========================================================================
# stdlib statistics (no numpy / no scipy required)
# ===========================================================================

def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _variance(xs: Sequence[float], ddof: int = 1) -> float:
    n = len(xs)
    if n - ddof <= 0:
        return 0.0
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs) / (n - ddof)


def _std(xs: Sequence[float], ddof: int = 1) -> float:
    return math.sqrt(_variance(xs, ddof))


# --- Student-t distribution (stdlib) --------------------------------------

def _t_sf_two_sided(t: float, df: int) -> float:
    """Two-sided survival p-value P(|T| >= |t|) for Student-t with df d.o.f.

    Uses the regularized incomplete beta function via a continued fraction
    (Numerical Recipes ``betai``). Falls back to a normal approximation only
    when df is nonpositive (should not happen for a real paired sample).
    """
    if df <= 0:
        return 1.0
    t = abs(t)
    x = df / (df + t * t)
    # P(|T| >= t) = I_x(df/2, 1/2)
    return _betai(df / 2.0, 0.5, x)


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _betacf(a: float, b: float, x: float, itmax: int = 200, eps: float = 3.0e-12) -> float:
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1.0e-30:
        d = 1.0e-30
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1.0e-30:
            d = 1.0e-30
        c = 1.0 + aa / c
        if abs(c) < 1.0e-30:
            c = 1.0e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1.0e-30:
            d = 1.0e-30
        c = 1.0 + aa / c
        if abs(c) < 1.0e-30:
            c = 1.0e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _t_ppf_975(df: int) -> float:
    """Two-sided 95% t critical value (upper 0.975 quantile).

    Small hard-coded table for common small df plus a bisection fallback on
    the survival function so the CI never depends on scipy.
    """
    table = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        12: 2.179, 15: 2.131, 20: 2.086, 24: 2.064, 30: 2.042,
        40: 2.021, 60: 2.000, 120: 1.980,
    }
    if df in table:
        return table[df]
    if df >= 1000:
        return 1.962
    # Bisect on the two-sided survival function to hit alpha = 0.05.
    lo, hi = 0.0, 100.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if _t_sf_two_sided(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def paired_t_test(diffs: Sequence[float]) -> Tuple[float, float]:
    """Return (t_statistic, two_sided_p) for H0: mean(diffs) == 0.

    Prefers scipy if importable; otherwise a stdlib one-sample t on the
    paired differences.
    """
    n = len(diffs)
    if n < 2:
        return (0.0, 1.0)
    if _HAVE_SCIPY:  # pragma: no cover - environment dependent
        t, p = _scipy_stats.ttest_1samp(list(diffs), 0.0)
        return (float(t), float(p))
    m = _mean(diffs)
    sd = _std(diffs, ddof=1)
    if sd == 0.0:
        # All differences identical: either a perfect (p->0) or null (p=1) shift.
        return (math.inf if m != 0 else 0.0, 0.0 if m != 0 else 1.0)
    se = sd / math.sqrt(n)
    t = m / se
    return (t, _t_sf_two_sided(t, n - 1))


# --- Wilcoxon signed-rank (stdlib) ----------------------------------------

def _normal_sf(z: float) -> float:
    """Upper-tail P(Z >= z) for standard normal via erfc."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def wilcoxon_signed_rank(diffs: Sequence[float]) -> Tuple[float, float]:
    """Two-sided Wilcoxon signed-rank test for H0: symmetric about 0.

    Prefers scipy. The stdlib path drops zero differences, ranks by absolute
    value with average ranks for ties, and uses the normal approximation with
    a tie correction (the standard choice for n beyond a handful). Returns
    (W_statistic, two_sided_p) where W is the smaller signed-rank sum.
    """
    nonzero = [d for d in diffs if d != 0.0]
    n = len(nonzero)
    if n == 0:
        return (0.0, 1.0)
    if _HAVE_SCIPY:  # pragma: no cover - environment dependent
        try:
            res = _scipy_stats.wilcoxon(list(diffs), zero_method="wilcox",
                                        correction=False, mode="auto")
            return (float(res.statistic), float(res.pvalue))
        except ValueError:
            return (0.0, 1.0)

    # Rank absolute differences with average ranks for ties.
    order = sorted(range(n), key=lambda i: abs(nonzero[i]))
    ranks = [0.0] * n
    i = 0
    tie_terms = 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(nonzero[order[j + 1]]) == abs(nonzero[order[i]]):
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0  # ranks are 1-based
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        t = j - i + 1
        if t > 1:
            tie_terms += t ** 3 - t
        i = j + 1

    w_plus = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    w_minus = sum(r for r, d in zip(ranks, nonzero) if d < 0)
    w = min(w_plus, w_minus)

    mean_w = n * (n + 1) / 4.0
    var_w = n * (n + 1) * (2 * n + 1) / 24.0 - tie_terms / 48.0
    if var_w <= 0:
        return (w, 1.0)
    # Continuity correction toward the mean.
    z = (w - mean_w)
    if z > 0:
        z -= 0.5
    elif z < 0:
        z += 0.5
    z /= math.sqrt(var_w)
    p = 2.0 * _normal_sf(abs(z))
    return (w, min(1.0, p))


# --- exact McNemar (reuse if available, else local) -----------------------

def mcnemar_two_sided(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value on b/c discordant pairs.

    Reuses the justice-pipeline implementation when importable; otherwise a
    local exact binomial computation with the identical convention.
    """
    if _mcnemar_two_sided is not None:
        return _mcnemar_two_sided(b, c)
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) * 0.5 ** n for i in range(k + 1))
    return min(1.0, 2.0 * tail)


# ===========================================================================
# Data loading and shaping
# ===========================================================================

def load_records(path: Path) -> Tuple[List[dict], dict]:
    """Return (records, metadata) from the pilot JSON.

    Accepts either a bare list of records or an object with ``records`` /
    ``results`` / ``items`` plus optional ``metadata``.
    """
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data, {}
    meta = data.get("metadata", {})
    for key in ("records", "results", "items", "data"):
        if isinstance(data.get(key), list):
            return data[key], meta
    raise ValueError(
        f"{path} is a JSON object but has no records/results/items list"
    )


def _norm_condition(value: str) -> str:
    v = (value or "").strip().lower()
    aliases = {
        "positive": "steer", "steered": "steer", "steer": "steer",
        "reverse": "reversed", "negative": "reversed", "reversed": "reversed",
        "placebo": "null", "random": "null", "null": "null",
        "baseline": "control", "none": "control", "control": "control",
    }
    return aliases.get(v, v)


def _is_correct(rec: dict) -> Optional[bool]:
    """Whether the discrete model_answer matches the courageous target."""
    ans = rec.get("model_answer")
    tgt = rec.get("target")
    if ans is None or tgt is None:
        return None
    return str(ans).strip().upper() == str(tgt).strip().upper()


def index_by_vector(records: List[dict]) -> Dict[str, Dict[str, Dict[str, dict]]]:
    """Nest records as vector -> condition -> sample_id -> record.

    ``control`` items are shared across vectors: any record whose condition is
    control is attached to *every* vector so pairing always has a partner.
    """
    controls: Dict[str, dict] = {}
    per_vec: Dict[str, Dict[str, Dict[str, dict]]] = {
        v: {c: {} for c in CONDITIONS} for v in VECTORS
    }
    seen_vectors = set()

    for rec in records:
        cond = _norm_condition(rec.get("condition", ""))
        sid = rec.get("sample_id")
        vec = rec.get("vector")
        if sid is None:
            continue
        if cond == "control":
            controls[sid] = rec
            # Also honor an explicit vector tag on a control row if present.
            if vec in per_vec:
                per_vec[vec]["control"][sid] = rec
            continue
        if vec not in per_vec:
            continue
        seen_vectors.add(vec)
        if cond in per_vec[vec]:
            per_vec[vec][cond][sid] = rec

    # Broadcast shared controls to every vector that lacks its own.
    for vec in per_vec:
        for sid, rec in controls.items():
            per_vec[vec]["control"].setdefault(sid, rec)

    return per_vec


# ===========================================================================
# Core per-vector computations
# ===========================================================================

def _paired_shifts(
    cond_map: Dict[str, dict],
    control_map: Dict[str, dict],
    drop_degenerate: bool,
) -> Tuple[List[float], List[str]]:
    """Per-item (condition_margin - control_margin) over shared sample_ids."""
    shifts: List[float] = []
    used: List[str] = []
    for sid, rec in cond_map.items():
        ctrl = control_map.get(sid)
        if ctrl is None:
            continue
        if drop_degenerate and (rec.get("degenerate_flag") or ctrl.get("degenerate_flag")):
            continue
        m = rec.get("margin")
        cm = ctrl.get("margin")
        if m is None or cm is None:
            continue
        shifts.append(float(m) - float(cm))
        used.append(sid)
    return shifts, used


def _mcnemar_flips(
    cond_map: Dict[str, dict],
    control_map: Dict[str, dict],
) -> Tuple[int, int, int, int]:
    """Return (b, c, n_pairs, net) for correctness flips vs control.

    b = control-wrong -> condition-right (a gain),
    c = control-right -> condition-wrong (a loss).
    """
    b = c = n = 0
    for sid, rec in cond_map.items():
        ctrl = control_map.get(sid)
        if ctrl is None:
            continue
        cond_ok = _is_correct(rec)
        ctrl_ok = _is_correct(ctrl)
        if cond_ok is None or ctrl_ok is None:
            continue
        n += 1
        if ctrl_ok and not cond_ok:
            c += 1
        elif (not ctrl_ok) and cond_ok:
            b += 1
    return b, c, n, b - c


def _shift_block(diffs: List[float], sample_ids: List[str]) -> dict:
    """Mean shift, 95% CI, paired t p, Wilcoxon p for one condition-vs-control."""
    n = len(diffs)
    mean = _mean(diffs)
    sd = _std(diffs, ddof=1) if n > 1 else 0.0
    if n > 1 and sd > 0:
        se = sd / math.sqrt(n)
        tcrit = _t_ppf_975(n - 1)
        ci = (mean - tcrit * se, mean + tcrit * se)
    else:
        ci = (mean, mean)
    t_stat, t_p = paired_t_test(diffs)
    w_stat, w_p = wilcoxon_signed_rank(diffs)
    return {
        "n_pairs": n,
        "mean_shift": mean,
        "sd": sd,
        "ci95": [ci[0], ci[1]],
        "ci_excludes_zero": bool(n > 1 and (ci[0] > 0 or ci[1] < 0)),
        "t_stat": t_stat,
        "t_p": t_p,
        "wilcoxon_stat": w_stat,
        "wilcoxon_p": w_p,
    }


def analyze_vector(
    vec: str,
    cond_maps: Dict[str, Dict[str, dict]],
    drop_degenerate: bool,
) -> dict:
    control = cond_maps["control"]
    out: dict = {"vector": vec, "shifts": {}, "mcnemar": {}}

    for cond in ("steer", "reversed", "null"):
        diffs, sids = _paired_shifts(cond_maps[cond], control, drop_degenerate)
        out["shifts"][cond] = _shift_block(diffs, sids)

        b, c, n, net = _mcnemar_flips(cond_maps[cond], control)
        p = mcnemar_two_sided(b, c)
        out["mcnemar"][cond] = {
            "b_wrong_to_right": b,
            "c_right_to_wrong": c,
            "n_pairs": n,
            "net": net,
            "p_two_sided": p,
        }

    # Degeneracy tally for the ARTIFACT check.
    degen = 0
    total = 0
    for cond in ("steer", "reversed", "null"):
        for rec in cond_maps[cond].values():
            total += 1
            if rec.get("degenerate_flag"):
                degen += 1
    out["degenerate_rate"] = (degen / total) if total else 0.0
    return out


# ===========================================================================
# Validation gate (margin proxy vs discrete answer, on control)
# ===========================================================================

def validation_gate(records: List[dict]) -> dict:
    """Agreement between sign(margin>0 -> predicts courageous) and answer==target.

    Only control rows count. Zero-margin rows are excluded from agreement (no
    sign to compare) but tallied separately.
    """
    agree = 0
    total = 0
    zero_margin = 0
    for rec in records:
        if _norm_condition(rec.get("condition", "")) != "control":
            continue
        m = rec.get("margin")
        ok = _is_correct(rec)
        if m is None or ok is None:
            continue
        if m == 0:
            zero_margin += 1
            continue
        predicts_courage = m > 0
        if predicts_courage == ok:
            agree += 1
        total += 1
    rate = (agree / total) if total else 0.0
    lo, hi = clopper_pearson_ci(agree, total) if total else (0.0, 1.0)
    return {
        "control_pairs_scored": total,
        "agreements": agree,
        "agreement_rate": rate,
        "agreement_ci95": [lo, hi],
        "zero_margin_control_rows": zero_margin,
        "gate_threshold": AGREEMENT_GATE,
        "passes": rate >= AGREEMENT_GATE,
    }


# ===========================================================================
# Cross-vector relative scaling and verdict
# ===========================================================================

def relative_scaling(per_vector: Dict[str, dict]) -> dict:
    """Each vector's steer shift as a fraction of the yardstick and null floor."""
    yard = per_vector.get(YARDSTICK, {})
    yard_shift = yard.get("shifts", {}).get("steer", {}).get("mean_shift", 0.0)
    out = {"yardstick": YARDSTICK, "yardstick_steer_shift": yard_shift, "vectors": {}}
    for vec, res in per_vector.items():
        steer = res["shifts"]["steer"]["mean_shift"]
        null_floor = res["shifts"]["null"]["mean_shift"]
        frac_yard = (steer / yard_shift) if abs(yard_shift) > ZERO_SHIFT_ABS else None
        # Steer signal net of its own null floor, scaled by the floor magnitude.
        floor_mag = abs(null_floor)
        over_floor = (steer / floor_mag) if floor_mag > ZERO_SHIFT_ABS else None
        out["vectors"][vec] = {
            "steer_shift": steer,
            "null_floor": null_floor,
            "fraction_of_yardstick": frac_yard,
            "steer_over_null_floor_magnitude": over_floor,
            "clears_null_floor": abs(steer) > FLOOR_MULTIPLE * floor_mag,
        }
    return out


def _vector_works(res: dict) -> bool:
    """A vector's steer shift is a real positive push toward courage."""
    steer = res["shifts"]["steer"]
    null_floor = abs(res["shifts"]["null"]["mean_shift"])
    return (
        steer["mean_shift"] > 0
        and steer["ci_excludes_zero"]
        and steer["mean_shift"] > FLOOR_MULTIPLE * max(null_floor, ZERO_SHIFT_ABS)
    )


def _reversed_hurts(res: dict) -> bool:
    """Reversed steering should push the margin negative (asymmetry holds)."""
    rev = res["shifts"]["reversed"]
    return rev["mean_shift"] < 0 and rev["ci_excludes_zero"]


def _reversed_symmetric(res: dict) -> bool:
    """Reversed neither clearly helps nor clearly hurts -> no real direction."""
    rev = res["shifts"]["reversed"]
    return not rev["ci_excludes_zero"]


def _near_null_floor(res: dict) -> bool:
    """Steer shift is within FLOOR_MULTIPLE of this vector's own null floor."""
    steer = abs(res["shifts"]["steer"]["mean_shift"])
    floor = abs(res["shifts"]["null"]["mean_shift"])
    return steer <= FLOOR_MULTIPLE * max(floor, ZERO_SHIFT_ABS)


def decide_verdict(per_vector: Dict[str, dict], gate: dict) -> dict:
    """Map computed effects onto the pre-registered outcome table."""
    reasons: List[str] = []

    if not gate["passes"]:
        return {
            "verdict": "INVALID: margin proxy failed validation gate",
            "detail": (
                f"control margin-sign agreement {gate['agreement_rate']:.1%} < "
                f"{AGREEMENT_GATE:.0%}; margins do not track the discrete answer, "
                "so shift statistics cannot be trusted."
            ),
            "reasons": reasons,
        }

    ideal = per_vector.get(YARDSTICK)
    if ideal is None:
        return {
            "verdict": "INDETERMINATE: no ideal_courage vector present",
            "detail": "The yardstick vector is missing from the pilot output.",
            "reasons": reasons,
        }

    ideal_steer = ideal["shifts"]["steer"]
    ideal_works = _vector_works(ideal)

    # 1. Yardstick fails -> model itself is not steerable on courage.
    if not ideal_works:
        return {
            "verdict": "MODEL NOT STEERABLE ON COURAGE",
            "detail": (
                f"ideal_courage steer shift {ideal_steer['mean_shift']:+.4f} does not "
                "clear its null floor / CI-excludes-zero test; the known-good "
                "direction fails, so nothing downstream can be trusted as a real "
                "courage effect."
            ),
            "reasons": reasons,
        }

    reasons.append(
        f"ideal_courage works: steer shift {ideal_steer['mean_shift']:+.4f}, "
        f"CI {ideal_steer['ci95'][0]:+.4f}..{ideal_steer['ci95'][1]:+.4f}."
    )

    wb = per_vector.get("whole_bible")
    pool = per_vector.get("courage_pool")

    # ARTIFACT guard: any Scripture vector where steer helps but reversed ALSO
    # helps, or where degeneracy is rampant, is not a clean direction.
    for name, res in (("whole_bible", wb), ("courage_pool", pool), (YARDSTICK, ideal)):
        if res is None:
            continue
        steer_helps = res["shifts"]["steer"]["mean_shift"] > 0 and res["shifts"]["steer"]["ci_excludes_zero"]
        rev_helps = res["shifts"]["reversed"]["mean_shift"] > 0 and res["shifts"]["reversed"]["ci_excludes_zero"]
        if steer_helps and rev_helps:
            reasons.append(f"{name}: steer AND reversed both help -> not a direction.")
            return {
                "verdict": "ARTIFACT (reject)",
                "detail": (
                    f"{name} shows both steer and reversed pushing margins the same "
                    "way; a genuine direction is asymmetric, so this is an artifact "
                    "of the intervention rather than a courage signal."
                ),
                "reasons": reasons,
            }
        if res["degenerate_rate"] > 0.5:
            reasons.append(f"{name}: degenerate_rate {res['degenerate_rate']:.0%} > 50%.")
            return {
                "verdict": "ARTIFACT (reject)",
                "detail": (
                    f"{name} degenerates on more than half of steered items; the "
                    "margins reflect broken generations, not a courage push."
                ),
                "reasons": reasons,
            }

    wb_works = wb is not None and _vector_works(wb)
    pool_works = pool is not None and _vector_works(pool)

    # 2. CLEAN NULL: ideal works, whole_bible ~= null floor and reversed symmetric.
    if wb is not None and _near_null_floor(wb) and _reversed_symmetric(wb) and not wb_works:
        reasons.append(
            "whole_bible steer shift sits at its null floor and reversed is "
            "symmetric (CI includes 0)."
        )
        return {
            "verdict": "CLEAN NULL: scripture carries no courage direction",
            "detail": (
                "The known-good direction steers, but a whole-Bible vector moves "
                "margins no more than the placebo and its reversal is symmetric: "
                "Scripture-at-large encodes no usable courage direction."
            ),
            "reasons": reasons,
        }

    # 3. REAL POSITIVE: ideal works, whole_bible beats floor, reversed hurts, coherent.
    if wb_works and not _near_null_floor(wb) and _reversed_hurts(wb) and wb["degenerate_rate"] <= 0.5:
        reasons.append(
            "whole_bible clears its null floor, reversed hurts (negative shift, "
            "CI excludes 0), and generations stay coherent."
        )
        return {
            "verdict": "REAL POSITIVE",
            "detail": (
                "ideal_courage works AND whole_bible steers above the noise floor "
                "with an asymmetric reversal that hurts: Scripture-at-large carries "
                "a real, usable courage direction."
            ),
            "reasons": reasons,
        }

    # 4. CONCENTRATED: courage_pool works but whole_bible does not.
    if pool_works and not wb_works:
        reasons.append(
            "courage_pool clears the floor while whole_bible does not."
        )
        return {
            "verdict": "CONCENTRATED IN COURAGE CONTENT",
            "detail": (
                "The courage-only pool steers but the whole-Bible vector does not: "
                "whatever courage direction exists lives in the explicitly "
                "courageous pericopes, not in Scripture at large."
            ),
            "reasons": reasons,
        }

    # Nothing above matched: ideal works but the Scripture vectors are an
    # ambiguous middle (help but don't clear the floor cleanly, reversed neither
    # clearly hurts nor helps). Report indeterminate rather than overclaim.
    reasons.append(
        "ideal works, but whole_bible / courage_pool fall in an ambiguous band "
        "(not clearly at the floor, not clearly a real asymmetric direction)."
    )
    return {
        "verdict": "INDETERMINATE (ideal works; scripture vectors ambiguous)",
        "detail": (
            "The yardstick steers, but neither Scripture vector lands cleanly in "
            "the CLEAN NULL, REAL POSITIVE, or CONCENTRATED buckets. More items or "
            "a stronger alpha are needed to resolve the Scripture direction."
        ),
        "reasons": reasons,
    }


# ===========================================================================
# Reporting
# ===========================================================================

def _fmt_ci(ci: Sequence[float]) -> str:
    return f"[{ci[0]:+.4f}, {ci[1]:+.4f}]"


def print_report(analysis: dict) -> None:
    gate = analysis["validation_gate"]
    print("=" * 72)
    print("COURAGE STEERING PILOT — margin-shift analysis")
    print("=" * 72)
    engine = "scipy" if _HAVE_SCIPY else "stdlib"
    print(f"t-test / Wilcoxon engine: {engine}")
    print(f"records: {analysis['n_records']}  "
          f"(smoke={analysis['smoke']}, "
          f"drop_degenerate={analysis['drop_degenerate']})")
    print()

    print("-" * 72)
    print("VALIDATION GATE  (control: margin sign vs discrete answer)")
    print("-" * 72)
    status = "PASS" if gate["passes"] else "FAIL — margins NOT trustworthy"
    print(f"  agreement: {gate['agreement_rate']:.1%} "
          f"({gate['agreements']}/{gate['control_pairs_scored']}), "
          f"gate >= {gate['gate_threshold']:.0%}  -> {status}")
    print(f"  95% CI: {_fmt_ci(gate['agreement_ci95'])}   "
          f"zero-margin control rows: {gate['zero_margin_control_rows']}")
    print()

    for vec in VECTORS:
        res = analysis["per_vector"].get(vec)
        if res is None:
            continue
        print("-" * 72)
        marker = "  <-- YARDSTICK" if vec == YARDSTICK else ""
        print(f"VECTOR: {vec}{marker}")
        print("-" * 72)
        for cond in ("steer", "reversed", "null"):
            s = res["shifts"][cond]
            mc = res["mcnemar"][cond]
            print(f"  {cond:9s} n={s['n_pairs']:>4d}  "
                  f"mean {s['mean_shift']:+.4f}  CI {_fmt_ci(s['ci95'])}  "
                  f"t_p={s['t_p']:.4g}  W_p={s['wilcoxon_p']:.4g}")
            print(f"            McNemar flips: +{mc['b_wrong_to_right']} "
                  f"-{mc['c_right_to_wrong']} "
                  f"(net {mc['net']:+d}, p={mc['p_two_sided']:.4g})")
        print(f"  degenerate_rate: {res['degenerate_rate']:.1%}")
        print()

    rel = analysis["relative_scaling"]
    print("-" * 72)
    print(f"RELATIVE SCALING  (yardstick = {rel['yardstick']} steer shift "
          f"{rel['yardstick_steer_shift']:+.4f})")
    print("-" * 72)
    for vec, r in rel["vectors"].items():
        frac = r["fraction_of_yardstick"]
        frac_s = f"{frac:.2f}x" if frac is not None else "n/a"
        over = r["steer_over_null_floor_magnitude"]
        over_s = f"{over:+.2f}x floor" if over is not None else "n/a"
        clears = "clears floor" if r["clears_null_floor"] else "AT floor"
        print(f"  {vec:14s} steer {r['steer_shift']:+.4f}  "
              f"= {frac_s} of yardstick, {over_s}  ({clears})")
    print()

    v = analysis["verdict"]
    print("=" * 72)
    print(f"VERDICT: {v['verdict']}")
    print("=" * 72)
    print(f"  {v['detail']}")
    for reason in v.get("reasons", []):
        print(f"    - {reason}")
    print()


# ===========================================================================
# Orchestration
# ===========================================================================

def run(input_path: Path, output_path: Path, smoke: bool) -> dict:
    records, metadata = load_records(input_path)
    if not records:
        raise ValueError(f"{input_path} contained zero records")

    # In smoke mode we do not require degeneracy filtering to leave enough data;
    # keep degenerate rows so tiny fixtures still exercise every path.
    drop_degenerate = not smoke

    gate = validation_gate(records)
    cond_index = index_by_vector(records)

    per_vector: Dict[str, dict] = {}
    for vec in VECTORS:
        cond_maps = cond_index.get(vec)
        if cond_maps is None:
            continue
        # Skip vectors with no steer pairs at all (nothing to say).
        if not cond_maps["steer"] and not cond_maps["reversed"] and not cond_maps["null"]:
            continue
        per_vector[vec] = analyze_vector(vec, cond_maps, drop_degenerate)

    rel = relative_scaling(per_vector) if per_vector else {"vectors": {}}
    verdict = decide_verdict(per_vector, gate)

    analysis = {
        "input": str(input_path),
        "n_records": len(records),
        "smoke": smoke,
        "drop_degenerate": drop_degenerate,
        "metadata": metadata,
        "config": {
            "agreement_gate": AGREEMENT_GATE,
            "floor_multiple": FLOOR_MULTIPLE,
            "vectors": VECTORS,
            "yardstick": YARDSTICK,
            "stats_engine": "scipy" if _HAVE_SCIPY else "stdlib",
        },
        "validation_gate": gate,
        "per_vector": per_vector,
        "relative_scaling": rel,
        "verdict": verdict,
    }
    return analysis


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=INPUT_PATH,
                        help=f"pilot results JSON (default: {INPUT_PATH})")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help=f"where to write margin_analysis.json (default: {OUTPUT_PATH})")
    parser.add_argument("--smoke", action="store_true",
                        help="tolerate tiny inputs: keep degenerate rows and skip "
                             "minimum-sample guards so small fixtures run end to end")
    parser.add_argument("--no-write", action="store_true",
                        help="print the report but do not write the JSON file")
    args = parser.parse_args(argv)

    analysis = run(args.input, args.output, smoke=args.smoke)
    print_report(analysis)

    if not args.no_write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(analysis, indent=2))
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
