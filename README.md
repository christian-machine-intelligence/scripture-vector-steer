# ScriptureVec Justice

This repository contains the code, paper, and curated artifacts for the
ScriptureVec Justice study:

- ["Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical Justice Vectors in Qwen3-14B](paper/search_out_a_matter_scripturevec_justice.md)

## Current Paper

The manuscript is available in three forms:

- [Markdown](paper/search_out_a_matter_scripturevec_justice.md)
- [Word document](paper/search_out_a_matter_scripturevec_justice.docx)
- [Rendered PDF](paper/search_out_a_matter_scripturevec_justice.pdf)

## Headline Result

The study searches Scripture as a source of activation-steering directions for
Justice behavior on the ratio-stage Justice subset of VirtueBench2. The main
finding is that specific biblical chapters, not Scripture in a flat or generic
sense, yield Justice-relevant vectors whose effects can be mapped across model
layers and steering strengths.

The canon-wide pipeline narrowed:

- 66 biblical books to 19 preliminary book candidates
- 19 book candidates to 7 confirmed book sources
- 170 chapters from those books to 38 preliminary chapter hits
- 38 chapter hits to 16 confirmed chapter movers
- 16 confirmed chapter vectors across a completed 43-cell layer/alpha
  localization grid

The expanded localization grid found three regime-defining cells:

- `L30 / alpha 96`: broadest rescue, 13 of 16 chapter vectors
- `L28 / alpha 16`: efficient low-strength uptake, 11 of 16 chapter vectors
- `L24 / alpha 32`: strongest mean positive movement, 9 of 16 chapter vectors

The paper's central claim is that Scripture can be treated not merely as
alignment text, but as a structured source of discoverable moral steering
vectors whose behavioral force can be mapped across a model's internal
geometry.

## Curated Artifacts

The paper-facing result bundle is:

- [results/paper/scripturevec_justice](results/paper/scripturevec_justice/README.md)

That folder contains:

- compact CSV and JSON data used by the paper
- the current manuscript exports
- publication figures
- the writing packet and ICMI style guide used to draft the paper

## Repository Contents

```text
paper/
  search_out_a_matter_scripturevec_justice.md
  search_out_a_matter_scripturevec_justice.docx
  search_out_a_matter_scripturevec_justice.pdf

results/paper/scripturevec_justice/
  README.md
  key_data/
  figures/
  paper_doc/
  writing_packet/

src/virtue_bench/
  benchmark, runner, steering, and analysis code

scripts/
  local analysis, summarization, paper-building, and remote-run helpers

data/
  VirtueBench scenarios and bundled KJV scripture data
```

## Verification

For the code path most relevant to ScriptureVec steering work:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_psalm_screen_analysis.py \
  tests/test_iconoclast_conditions.py \
  tests/test_steering_corpora.py \
  tests/test_steering_selection.py
```

The paper artifacts themselves can be checked by reading
`results/paper/scripturevec_justice/key_data/README.md` and comparing the
figures in `results/paper/scripturevec_justice/figures/` against the manuscript.

## Data Policy

This repository includes the curated data and figures needed for the current
paper argument. Bulky scratch runs, local console logs, vector checkpoints, and
historical benchmark dumps remain outside the paper-facing artifact bundle
unless they directly support the ScriptureVec Justice paper.

## License

See [LICENSE](LICENSE).
