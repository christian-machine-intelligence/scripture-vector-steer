# ScriptureVec Paper Key Data Guide

Compact, machine-readable extracts backing every number in the ScriptureVec
Justice paper. They are derived from per-run experiment summaries under
`results/experiments/scripturevec14`, which are **not bundled** in this
repository (see the Data Policy section of the top-level README) — so these CSVs
are the trust root for the paper's numbers.

Per-row statistical inference for each stage lives in [`stats/`](stats/), written
by `scripts/scripturevec_justice_stats.py`.

## Topline Counts

- book_discovery_l10_candidate_count: `19`
- book_confirmation_l40_candidate_count: `19`
- book_confirmation_l40_survivor_count: `7`
- chapter_discovery_l10_clean_hit_count: `38`
- chapter_confirmation_l40_candidate_count: `38`
- chapter_confirmation_l40_survivor_count: `16`
- layer_localization_completed_cells: `43`
- layer_localization_expected_cells: `43`
- layer_localization_rows: `688`
- layer_localization_paired_rescue_count: `244`

## Files

- `book_discovery_l10_candidates.csv`: The 19 preliminary book-level Justice candidates from the all-66-book discovery atlas.
- `book_confirmation_l40_all_candidates.csv`: All 19 preliminary book candidates retested at limit 40, including survivors and failures.
- `book_confirmation_l40_survivors.csv`: The seven book-level candidates that survived limit-40 confirmation.
- `chapter_discovery_l10_clean_hits.csv`: The 38 clean preliminary chapter hits from the seven confirmed book sources.
- `chapter_confirmation_l40_all_candidates.csv`: All 38 chapter candidates retested at limit 40.
- `chapter_confirmation_l40_survivors.csv`: The 16 confirmed chapter movers used for layer localization.
- `layer_alpha_cells.csv`: Completed layer/alpha localization cells, ranked by rescue count.
- `layer_alpha_expected_grid.csv`: The completed expanded localization grid in planned order.
- `chapter_stability_by_localization.csv`: How often each confirmed chapter was rescued across completed localization cells.
- `layer_alpha_target_rows.csv`: One row per chapter per completed layer/alpha cell.
- `chapter_x_layer_alpha_rescue_matrix.csv`: Plot-ready binary matrix for chapter-by-cell rescue heatmaps.
- `scripturevec_key_results_rollup.json`: One-file structured summary of the packet.

## How to Read These Numbers

The expanded localization grid is complete. The broadest-coverage cell is
`L30 / alpha 96` (13 paired rescues of 16, mean positive delta 0.0875); the
largest-movement cell is `L24 / alpha 32` (9 rescues, mean delta 0.1687); the
broadest cell at the gentlest strength is `L28 / alpha 16` (11 rescues).

**These cells are not statistically separable.** Their Clopper-Pearson 95%
intervals overlap pairwise (`stats/layer_alpha_cell_cis.csv`), and no per-row
test at any pipeline stage reaches uncorrected p < 0.05
(`stats/*_stats.csv`). Read the packet as a ranked candidate set and a map of
where chapter-derived directions concentrate — not as measured per-chapter
effect sizes.

Two column meanings that are easy to misread:

- `best_center_layer` / `best_alpha` in `chapter_stability_by_localization.csv`
  identify the cell where a chapter reached its highest positive-steering
  **accuracy**. That is not necessarily a cell where it counted as a rescue:
  Acts 27 and Numbers 22 both peak at `L24 / alpha 48`, a cell with zero paired
  rescues overall.
- `paired_rescue_count` sums across 43 limit-10 cells, so it is a robustness
  ranking, not a significance measure.
