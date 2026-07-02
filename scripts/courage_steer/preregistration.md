# Pre-registration — ScriptureVec Courage Steering, confirmatory pass

**Status:** committed BEFORE the confirmatory run. Everything below is frozen.
**Date frozen:** 2026-07-01
**Author:** courage-steer-study work stream (Qwen3-32B).

---

## 0. Honesty note (what is and isn't pre-registered)

The pilot, sealed-`caro` replication, generic-text control, multi-virtue sweep,
reasoning check, and layer sweep were all **exploratory** — the method was
developed as we went. They are *not* pre-registered and are not claimed to be.

This document pre-registers **one forward-looking confirmatory test**: it freezes
the exact pipeline and the decision rule, then applies them **once** to item sets
that have **never been touched** by any stage of the study (neither vector
construction nor any prior evaluation). The point is to convert "we found an
effect while exploring" into "we predicted the effect in advance and it held on
untouched data" — the exact standard the original ICMI justice study failed.

---

## 1. Frozen apparatus

| Component | Frozen value |
|---|---|
| Model | `Qwen3-32B`, local weights, **4-bit NF4** (bnb, double-quant, bf16 compute) |
| Device | single GPU, `device_map={"":"cuda:0"}`, `enable_thinking=False` |
| Steering | residual-stream additive hook, `alpha * unit_vector`, layer window **[53–59], center 56** (late "concept" layers; layer sweep showed 56 & 62 clean, early layers = disruption) |
| Endpoint (primary) | **answer-only log-odds margin** = `logit(courageous letter) − logit(cowardly letter)`, one forward pass, signed toward courage |
| Alpha grid | **{16, 32, 64}** (dose-response); headline alpha = **64** |
| Headline vector | `whole_bible` — scripture-as-such direction (`scripture_contrast`, frozen in `pilot_vectors.pt`); **never saw any benchmark item** |
| Positive control | `ideal_v` — decision-point / answer-token contrast, rebuilt per run from the `ratio` BUILD half (the rig-validity yardstick) |
| A-bias control | `answer_bias` — pure letter-position direction |
| Noise floor | `random` — matched-norm random direction (frozen in `pilot_vectors.pt`) |
| Reversed | same `whole_bible` vector, negated alpha (asymmetry probe) |

Vectors artifact: `results/courage_pilot/pilot_vectors.pt` (sha of `whole_bible`
and `random` is whatever is in that file at commit time; not regenerated).

## 2. Frozen confirmatory eval sets (never touched)

The courage benchmark has 5 temptation variants × 150 base scenarios. Used so far:
`ratio` (BUILD + EVAL split) and `caro` (sealed replication). **Untouched:**

- `mundus` — 150 items
- `diabolus` — 150 items
- `ignatian` — 150 items

**Total confirmatory n = 450.** None of these items participated in building any
vector or in any prior evaluation. Each is run as its own sealed set.

Runner (frozen invocation, per variant):
```
run_py.cmd scripts\courage_steer\run_confirm.py \
    --subset courage --sealed --eval-variant <mundus|diabolus|ignatian> \
    --vectors results/courage_pilot/pilot_vectors.pt \
    --limit 150 --battery-alphas 16 32 64
```

## 3. Pre-registered decision rule

For each variant, `whole_bible` **genuinely steers courage** iff ALL hold
(headline alpha = 64 unless noted):

1. **Positive & significant** — mean courage-margin shift (steer − control) > 0 with 95% CI lower bound > 0.
2. **Dose-monotone** — shift(16) ≤ shift(32) ≤ shift(64), all ≥ 0.
3. **Asymmetric** — reversed-steer shift < 0 (flipping the sign hurts).
4. **Above the floor** — `random` shift is non-significant / near 0, and `whole_bible` shift clearly exceeds it.
5. **Genuine, not a position artifact** — A/B split: the shift is > 0 for **both** `target=A` items **and** `target=B` items (the test that unmasked justice/generic).
6. **Coherent** — degeneration rate near control (< ~10%).

**Rig validity:** `ideal_v` at alpha 64 should show a positive genuine shift
(model is steerable). If `ideal_v` fails on a given variant (as it did for
prudence/justice in the exploratory sweep), fall back to criteria 4+5 on
`whole_bible` — the random floor and the A/B split are self-sufficient.

## 4. Pre-registered predictions

Based on the exploratory results (courage genuine shift ≈ +1.0 at alpha 64):

- **P1 (primary):** `whole_bible` meets criteria **1, 3, 4, 5** on **≥ 2 of the 3** untouched variants.
- **P2:** the genuine (A/B-averaged, position-corrected) courage shift at alpha 64 is **> +0.4** on those variants.
- **P3:** `random` never meets criterion 1 on any variant (floor holds).

## 5. Aggregate verdict map (decided in advance)

| Outcome across the 3 untouched variants | Verdict |
|---|---|
| Criteria 1,3,4,5 met on ≥2/3, genuine shift > +0.4 | **CONFIRMED** — effect replicates, pre-registered, on untouched data |
| Genuine (crit 5 holds) but shift materially smaller than exploratory | **CONFIRMED-WEAKER** — real but overestimated by exploration (report magnitude honestly) |
| Crit 5 fails (A/B split not both-positive) on majority | **NOT CONFIRMED** — exploratory effect was a position artifact after all |
| `whole_bible` ≈ `random` floor on majority | **FAILED TO REPLICATE** — exploratory effect was selection/overfitting; report the null |

Whatever the frozen rule returns is reported as-is. No post-hoc alpha, layer,
item, or criterion adjustment after the confirmatory data is seen.

## 6. Analysis

Per-variant analysis by the existing `analyze_v2.py` (courage-shift vs A-bias
decomposition, dose-response, reversed) against
`results/courage_pilot/confirm_courage_sealed-<variant>_full.json`. Report all
three variants side by side plus the aggregate verdict from §5.
