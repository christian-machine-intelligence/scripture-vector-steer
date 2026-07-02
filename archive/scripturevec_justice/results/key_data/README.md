# ScriptureVec Paper Key Data Guide

This folder contains compact, AI-readable data extracts for drafting the ScriptureVec Justice paper. The files are derived from local experiment artifacts under `results/experiments/scripturevec14`.

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

## Important Note

The expanded localization grid is complete. The strongest broad-coverage cell is `L30 / alpha 96`, with 13 paired rescues out of 16 confirmed chapter vectors and mean positive delta 0.0875. The strongest high-movement cell remains `L24 / alpha 32`, with 9 paired rescues and mean positive delta 0.1687. The most efficient low-alpha cell is `L28 / alpha 16`, with 11 paired rescues at a much gentler steering strength. This supports the paper's central claim that specific biblical chapter vectors form a structured layer-and-strength map rather than a flat Scripture effect.
