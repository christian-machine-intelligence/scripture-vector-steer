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

The pipeline finds that specific biblical chapters produce Justice-relevant
activation directions, and that those directions behave differently across
layers and steering strengths.

The completed expanded localization grid contains 43 behavior cells. The three
most important regimes are:

- `L30 / alpha 96`: broadest rescue, 13 of 16 confirmed chapter vectors
- `L28 / alpha 16`: efficient low-strength uptake, 11 of 16 confirmed chapter
  vectors
- `L24 / alpha 32`: strongest mean positive movement, 9 of 16 confirmed
  chapter vectors

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
- `figures/`: publication figures used in the paper.
- `paper_doc/`: current Markdown, DOCX, and rendered PDF manuscript exports.
- `writing_packet/`: model handoff prompt, detailed outline, interpretive
  motif scaffold, and ICMI style guide.

## Figure Map

- Figure 1: book confirmation
- Figure 2: chapter hits by confirmed book
- Figure 3: expanded layer/alpha rescue heatmap
- Figure 4: breadth versus strength scatter
- Figure 5: alpha trajectories by layer
- Figure 6: chapter stability across localization cells
- Figure 7: chapter by layer/alpha rescue matrix

## Publication Caveats

The book and chapter confirmations are limit-40 evidence. The expanded
localization grid is limit-10 localization evidence and should be treated as a
map of where the strongest effects appear. The paper's next empirical step is
to retest the regime-defining localization cells on a wider slice.
