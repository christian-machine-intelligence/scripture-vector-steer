# ScriptureVec Justice Artifacts

This directory contains the curated paper-facing artifacts for:

> "Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical
> Justice Vectors in Qwen3-14B

## Run Design

- Model: `Qwen3-14B`
- Benchmark: `VirtueBench2`, Justice ratio stage
- Scripture source: bundled KJV
- Vector extraction: `scripture_contrast`
- Discovery alpha: `32`
- Confirmation alpha: `32`
- Localization alphas: `16, 24, 32, 48, 64, 96`
- Localization layers: full alpha ladders for `24, 28, 29, 30, 31, 32, 33`,
  plus a layer-36 anchor cell
- Controls: unsteered control, positive Scripture steer, negative-alpha steer,
  and null-control steer

## Headline Result

The pipeline searches the canon for chapters whose activation directions move
the Justice benchmark, and maps how those directions behave across layers and
steering strengths. The completed grid contains 43 behavior cells. Three cells
illustrate its shape:

- `L30 / alpha 96`: broadest uptake, 13 of 16 chapters (95% CI 0.54-0.96)
- `L28 / alpha 16`: broad uptake at the gentlest tested strength, 11 of 16
  (CI 0.41-0.89)
- `L24 / alpha 32`: largest mean positive movement, 9 of 16 (CI 0.30-0.80)

These intervals overlap pairwise, so the cells are illustrative rather than
statistically separable. See the Caveats section below before quoting any of
these numbers as an effect size.

## Key Files

- `key_data/README.md`: compact guide to the machine-readable data.
- `key_data/scripturevec_key_results_rollup.json`: one-file structured summary
  of the paper data.
- `key_data/layer_alpha_cells.csv`: completed localization cells ranked by
  paired-rescue count.
- `key_data/chapter_stability_by_localization.csv`: chapter stability across
  the 43 localization cells.
- `key_data/chapter_x_layer_alpha_rescue_matrix.csv`: binary matrix used for
  the chapter-by-layer/alpha figure.
- `key_data/stats/`: per-row exact McNemar tests with BH-FDR and Bonferroni
  adjustments for all four pipeline stages, plus Clopper-Pearson 95% intervals
  for the 43 localization cells.
- `figures/`: publication figures used in the paper.

The manuscript itself lives in [`paper/`](../../../paper/); regenerate the
figures and exports with `python scripts/build_paper_exports.py`.

## Figure Map

- Figure 1: book confirmation
- Figure 2: chapter hits by confirmed book
- Figure 3: expanded layer/alpha rescue heatmap
- Figure 4: breadth versus strength scatter
- Figure 5: alpha trajectories by layer
- Figure 6: chapter stability across localization cells
- Figure 7: chapter by layer/alpha rescue matrix

## Publication Caveats

**The effect does not survive held-out testing.** The limit-10 discovery slice
is nested inside the limit-40 confirmation slice, and on the 30 items not used
for selection, positive steering finishes behind control on 22 of 38 chapters
and ahead on 1 (sign test p = 0.000006). Survival tracks the absence of harm
rather than benefit. See `key_data/stats/held_out_items_*.csv` and paper
section 4.5.

**No row at any stage of the pipeline reaches uncorrected statistical
significance.** Most limit-40 survivors are a single-item flip out of forty
(delta = 0.025, exact two-sided McNemar p ~ 1.0); the strongest single row is
Hebrews 2 at p ~ 0.5. BH-FDR and Bonferroni corrections within each stage do
not change that. See `key_data/stats/` for the per-row numbers.

The limit-10 discovery slice (items 0-9) is nested inside the limit-40
confirmation slice (items 0-39) under `seed=42`, so confirmation re-evaluates
the discovery items rather than testing disjoint data.

The localization grid is limit-10 evidence throughout. Treat this packet as a
ranked candidate set and a map of where to look next, not as a set of confirmed
per-chapter effects. The paper's next empirical step (paper section 10) is to
retest the illustrative localization cells on a disjoint slice.
