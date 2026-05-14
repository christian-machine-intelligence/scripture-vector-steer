# Disjoint-Slice Retest for the Three Regime-Illustrative Cells

This directory contains the launchers and analysis script for the
follow-up experiment listed as the next confirmation step in
[paper §10](../../paper/search_out_a_matter_scripturevec_justice.md)
and the (b) follow-up named in the PR1 stats commit.

## Hi Lucius — short version

The paper is in good shape after PR1 / PR2 / PR3, but there's one
empirical gap that a careful reviewer is going to notice immediately,
and we'd rather close it ourselves than have to defend it in review.
This experiment closes it.

**The gap.** Our "confirmation" stage at limit-40 is not statistically
independent of our discovery stage at limit-10. Both stages share the
same first 10 benchmark items because the sampler in `prepare_samples`
is deterministic at seed=42 — `--limit 10` evaluates items 0–9,
`--limit 40` evaluates items 0–39, so confirmation is just discovery
plus 30 more items on top. The arithmetic shows the 30 new items
contribute essentially no movement for the typical survivor (positive
12, control 12). So the funnel narrative (66 → 19 → 7 → 38 → 16) reads
like a sequence of tightening independent tests, but mechanically it's
one test run at two slice sizes.

**Why a reviewer will catch this.** A reasonably skeptical reader
will read §3.5 / §4.2 / §4.4, notice that the discovery and
confirmation share items 0–9, and then go straight to the PR1 stats
output showing zero rows reach uncorrected p < 0.05 at any stage.
That combination is hard to defend: small effects, on overlapping
slices, with no inferential pass-through. Without the disjoint-slice
retest the paper has to retreat fully to the "behavioural atlas, not
confirmed effects" framing for every individual chapter.

**What this retest does.** It evaluates the 16 candidate chapter
directions at the three regime-illustrative cells against items
**40–79** of the Justice ratio bank — 40 items the chapters were never
screened on. Same model, same vectors, same four-condition controls,
same strict pass rule. If chapters survive on the fresh slice, that's
real upgrade evidence — we can promote them to confirmed effects in
the next paper revision and the funnel narrative recovers its
epistemic shape. If they don't, that's also a real result and we
publish it: the paper becomes a method-development contribution
(*how to search the canon for moral steering directions*) plus an
honest behavioural atlas, which is smaller but more durable than the
current framing.

**Three possible outcomes for your paper:**

| Outcome | What it means | What changes in the paper |
| --- | --- | --- |
| Most chapters *promoted* (pass rule + BH q < 0.05 on ≥1 cell) | Real evidence the directions carry effects | Discussion claims individual chapter effects; §7 readings get more weight |
| Most chapters *candidate* (pass rule but no significance) | Directions move things but at the noise floor | Stay with PR1's "candidate cohort" framing; minor edits |
| Most chapters *demoted* (fail rule on all 3 cells) | The cohort doesn't survive an independent test | Paper restructures around method + atlas, candidate cohort gets named as non-survivors honestly. Smaller claim, more defensible. |

The runs are about 2–3 hours each on the 4090 (single GPU), three
total. Detail and the exact commands are below.

## Why this exists

The current paper's L40 "confirmation" stage is not statistically
independent of the L10 discovery stage. The benchmark sampler in
[`prepare_samples`](../../src/virtue_bench/core/loader.py) is
deterministic at `seed=42` and just truncates a fixed ordering, so:

- discovery at `--limit 10`     evaluates items `0..9`
- confirmation at `--limit 40`  evaluates items `0..39` — a **superset**

The L10 → L40 transition is therefore a tighter pass-rule retest on
overlapping data, not a fresh test on independent items. On the
additional 30 items in the L40 slice the typical survivor adds **zero**
net paired movement (positive 12, control 12 — see paper §4.2/§4.4 for
the arithmetic). Combined with the per-row exact-McNemar p-values
emitted by [`scripturevec_justice_stats.py`](../scripturevec_justice_stats.py)
showing zero significant rows at any stage, the candidate cohort of 16
chapter directions needs a real disjoint-slice test before any
individual chapter can be claimed as carrying a confirmed effect.

This retest evaluates the 16 chapter directions at the three
regime-illustrative cells (paper §5.2) against **items 40–79** of the
Justice ratio bank — 40 items the chapters were never screened on —
using the same four-condition control battery and the same strict
pass rule.

## What gets run

Three CLI invocations, one per regime-illustrative cell. Each launcher
runs all 16 chapter targets at the cell's `(center_layer, runtime_alpha)`
and writes a single `_summary.json` to
`results/experiments/scripturevec14_disjoint_slice/`.

| Launcher                          | Center layer | Runtime α | Cell role                |
| --------------------------------- | -----------: | --------: | ------------------------ |
| `run_disjoint_L30_a96.cmd`        | 30           | 96        | broadest rescue          |
| `run_disjoint_L28_a16.cmd`        | 28           | 16        | gentlest α with broad uptake |
| `run_disjoint_L24_a32.cmd`        | 24           | 32        | largest mean per-chapter Δ |

The 16 chapter targets are the same set that survived the L40 pass rule
(paper §4.4): `chapter_deu_16`, `chapter_jdg_07`, `chapter_jdg_09`,
`chapter_num_11`, `chapter_num_22`, `chapter_num_27`, `chapter_1ch_09`,
`chapter_1ch_29`, `chapter_act_07`, `chapter_act_11`, `chapter_act_16`,
`chapter_act_27`, `chapter_heb_02`, `chapter_heb_07`, `chapter_heb_09`,
`chapter_heb_10`.

Each invocation uses `--sample-offset 40 --limit 40`, which evaluates
items 40–79 (`prepare_samples` applies offset *after* the deterministic
A/B randomisation, see [`loader.py:84`](../../src/virtue_bench/core/loader.py),
so the A/B positions on items 40–79 match what the full bank would
present at those indices).

## How to run (on Lucius's home-pc GPU)

The launchers follow the existing `scripts/windows/launchers/` convention:
they derive the repo root from their own location and look for a venv
under `%REPO%\.venv\`, with a fallback to the canonical
`C:\Users\sethcodex\work\virtue-bench-2\.venv\` path used by the prior
runs.

The launchers also need:

1. **Path to the Qwen3-14B model.** Defaults to `C:\Users\sethcodex\models\Qwen3-14B`
   (matches the existing launchers and the path in
   [`src/virtue_bench/_model_pin.py`](../../src/virtue_bench/_model_pin.py)).
   Override by setting `MODEL_PATH` before invoking.

2. **Path to the chapter corpus** (`canon_justice_survivor_chapters_v1.jsonl`)
   used in the original chapter-confirmation runs. Defaults to
   `%REPO%\results\experiments\scripturevec14\canon_discovery\canon_justice_survivor_chapters_v1.jsonl`,
   which is where the existing chapter-confirmation launchers wrote it.
   Override by setting `CORPUS_PATH` before invoking.

Run from `cmd.exe` on the Windows GPU box:

```cmd
cd C:\Users\sethcodex\work\virtue-bench-2

REM each launcher takes a couple of hours on a single RTX 4090
scripts\disjoint_slice\run_disjoint_L30_a96.cmd
scripts\disjoint_slice\run_disjoint_L28_a16.cmd
scripts\disjoint_slice\run_disjoint_L24_a32.cmd
```

They are independent — run them serially (single GPU) or in parallel on
separate GPUs by setting `VIRTUE_BENCH_CUDA_DEVICE=cuda:N` for each.

## What gets committed back to the repo

After all three runs finish, copy the three summary JSONs into the
public repo at:

```
results/paper/scripturevec_justice/key_data/disjoint_slice/
    scripturevec14_qwen3_14b_disjoint_l40_o40_L30_a96_v1_summary.json
    scripturevec14_qwen3_14b_disjoint_l40_o40_L28_a16_v1_summary.json
    scripturevec14_qwen3_14b_disjoint_l40_o40_L24_a32_v1_summary.json
```

Then from any CPU environment with the repo cloned:

```bash
python scripts/disjoint_slice/analyze_disjoint_slice.py
```

This writes:

- `results/paper/scripturevec_justice/key_data/disjoint_slice/per_row_disjoint_stats.csv`
  — per-(chapter × cell) row with control / positive / negative-α / null
  accuracies on the disjoint slice, the reconstructed `(b, c)` discordant
  pair counts, exact two-sided McNemar p-values, and BH-FDR + Bonferroni
  adjustments across the 48-row family.
- `results/paper/scripturevec_justice/key_data/disjoint_slice/cohort_comparison.csv`
  — for each chapter: nested-slice rescue count (out of the 43 original
  cells), disjoint-slice pass on each of the 3 regime cells, headline
  decision (`promoted | candidate | demoted`).
- `results/paper/scripturevec_justice/key_data/disjoint_slice/disjoint_slice_summary.json`
  — machine-readable rollup the next paper revision can cite.

These three artifacts are what the paper will be rewritten around.

## Decision rule the paper will apply

For each of the 16 chapters and each of the 3 cells:

1. **Pass rule (same as paper §3.5).** positive_acc strictly beats max(control, negative, null), AND positive_net > 0.
2. **Per-row significance.** exact two-sided McNemar p < 0.05.
3. **Family-corrected.** BH-FDR q < 0.05 over the 48 disjoint-slice rows.

Headlines the analyze script will emit:

- *promoted*: chapter passes rule (1) on ≥1 cell and reaches BH q < 0.05 on
  ≥1 cell. The paper will reframe these as confirmed-effect chapters.
- *candidate*: passes rule (1) on ≥1 cell but no row reaches BH q < 0.05.
  These stay as candidates and the paper retreats to the
  behavioural-atlas claim for them.
- *demoted*: fails rule (1) on all 3 cells. The paper will remove these
  from the cohort and the Discussion will name them as candidates that
  did not survive a disjoint-slice retest.

If most chapters land in *demoted* — the more likely outcome given the
per-row movements are at the noise floor — that is itself the result
the paper will publish, and the present pass-rule cohort will be
reframed throughout as a method-development contribution rather than as
an empirical inventory of justice-relevant chapters.
