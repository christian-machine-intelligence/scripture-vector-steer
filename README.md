# ScriptureVec Justice

![Header](assets/header.jpg)

Code, data, paper, and figures accompanying:

> **"Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical Justice Vectors in Qwen3-14B**
> Lucius, Institute for a Christian Machine Intelligence
> *ICMI Working Paper No. [N]*, May 2026.

[Read the paper](paper/search_out_a_matter_scripturevec_justice.md) · [Figure 1 (book confirmation)](results/paper/scripturevec_justice/figures/figure_1_book_confirmation.png) · [Figure 2 (chapter hits)](results/paper/scripturevec_justice/figures/figure_2_chapter_hits_by_book.png) · [Figure 3 (layer/α heatmap)](results/paper/scripturevec_justice/figures/figure_3_layer_alpha_heatmap.png) · [Figure 4 (breadth vs strength)](results/paper/scripturevec_justice/figures/figure_4_breadth_strength.png) · [Figure 5 (α trajectories)](results/paper/scripturevec_justice/figures/figure_5_alpha_trajectories.png) · [Figure 6 (chapter stability)](results/paper/scripturevec_justice/figures/figure_6_chapter_stability.png) · [Figure 7 (rescue matrix)](results/paper/scripturevec_justice/figures/figure_7_rescue_matrix.png)

## Summary

The study searches the biblical canon for activation-steering directions that move Qwen3-14B's behavior on the ratio-stage Justice subset of VirtueBench V2. A multi-stage pass-rule pipeline narrowed the canon from 66 books to 19 preliminary candidates, 7 candidate book sources (1 Chronicles, Amos, Deuteronomy, Judges, Numbers, Acts, Hebrews), 38 preliminary chapter hits, and a final 16 chapter-derived candidates. A completed 43-cell layer/α localization grid then maps the candidate cohort across the model's residual stream. Three illustrative cells highlight the qualitative shape of the atlas — broadest rescue at L30/α96 (13/16, 95% CI [0.54, 0.96]), gentlest-α uptake at L28/α16 (11/16, CI [0.41, 0.89]), and largest mean per-chapter Δ at L24/α32 (9/16, CI [0.30, 0.80]) — though the per-cell CIs overlap and the per-row movements at limit-40 do not reach uncorrected statistical significance (most survivors are a single-item shift; see `results/paper/scripturevec_justice/key_data/stats/`). The behavioral atlas is the empirical contribution of this work; disjoint-slice confirmation of the regime-illustrative cells is planned as a follow-up (paper §10).

## Repository Layout

```text
scripture-vector-steer/
├── README.md                          this file
├── LICENSE                            MIT
├── requirements.txt                   pinned versions used for the paper
├── pyproject.toml                     editable install (kept for backward compat)
├── MANIFEST.in
├── .gitignore
├── assets/
│   └── header.jpg                     banner image
├── paper/
│   ├── search_out_a_matter_scripturevec_justice.md       the paper itself
│   ├── search_out_a_matter_scripturevec_justice.docx
│   ├── search_out_a_matter_scripturevec_justice.pdf
│   ├── scripturevec_justice_paper_evaluation.md          author's review notes
│   └── README.md
├── data/
│   ├── PROVENANCE.md                  SHA-256s + provenance for every bundled file
│   ├── bible_kjv.json                 KJV scripture corpus (paper §3.2)
│   ├── steering/corpora.jsonl         steering reference corpora; neutral slice is
│   │                                  the contrast pole for scripture_contrast (§3.3)
│   ├── justice/scenarios.csv          VirtueBench V2 Justice (paper's behavioral target)
│   ├── courage/scenarios.csv          (not used in headline; bundled with the evaluator)
│   ├── prudence/scenarios.csv         (not used in headline)
│   └── temperance/scenarios.csv       (not used in headline)
├── src/virtue_bench/
│   ├── _model_pin.py                  canonical HF model revision for paper runs
│   ├── core/                          loader, schema, scripture, prompt prep
│   ├── steering/
│   │   ├── corpora.py                 corpora I/O
│   │   ├── extract.py                 scripture_contrast direction extraction
│   │   ├── runtime.py                 forward-hook steering at α
│   │   └── experiment.py              steering experiment orchestration
│   ├── eval/                          experiment + scorer
│   ├── runners/                       hf_local, openai_api, anthropic_api, ...
│   ├── stats/                         (bootstrap, regression, tests)
│   └── analysis/                      visualize, iconoclast, psalm_screen, tables
├── scripts/
│   ├── scripturevec_justice_stats.py            per-row McNemar + BH/Bonferroni
│   │                                            + Clopper-Pearson cell CIs (NEW)
│   ├── build_scripturevec_justice_paper_doc.py  regenerates every paper figure
│   │                                            from the curated CSVs (Figs 1-7)
│   ├── summarize_scripturevec_layer_localization.py   builds key_data/layer_*
│   ├── summarize_scripturevec_alpha_sweep.py
│   ├── summarize_scripturevec_target_grid.py
│   ├── build_cardinal_candidate_vectors.py      vector-building helpers
│   ├── build_cardinal_residual_vectors.py
│   ├── analyze_cardinal_vector_geometry.py
│   ├── analyze_cardinal_reasoning_judge.py
│   ├── filter_scripture_corpus_targets.py
│   ├── build_bible_json.py                      builds data/bible_kjv.json
│   ├── build_canon_discovery_corpus.py
│   ├── analyze_psalm_family_screen.py
│   ├── run_ensoulment_sidecar.py
│   └── windows/                                 Windows GPU launchers (run-specific)
├── results/
│   ├── experiments/                             raw experiment summaries
│   │                                            (see Data Policy below)
│   └── paper/scripturevec_justice/              curated paper artifacts
│       ├── README.md
│       ├── figures/                             Figures 1-7 (PNG)
│       ├── key_data/
│       │   ├── README.md                        guide to the compact data
│       │   ├── stats/                           (NEW) McNemar + Bonferroni + BH
│       │   │                                    + Clopper-Pearson CIs
│       │   ├── book_discovery_l10_candidates.csv
│       │   ├── book_confirmation_l40_*.csv
│       │   ├── chapter_discovery_l10_clean_hits.csv
│       │   ├── chapter_confirmation_l40_*.csv
│       │   ├── layer_alpha_cells.csv
│       │   ├── layer_alpha_expected_grid.csv
│       │   ├── layer_alpha_target_rows.csv
│       │   ├── chapter_stability_by_localization.csv
│       │   ├── chapter_x_layer_alpha_rescue_matrix.csv
│       │   └── scripturevec_key_results_rollup.json
│       ├── paper_doc/                           markdown/docx/pdf manuscript exports
│       └── writing_packet/                      writing-handoff scaffolding
├── configs/                                     YAML run configs (legacy + paper)
├── docs/                                        run-design notes and project history
└── tests/                                       pytest suite
```

## Reproducing the Paper

The headline runs require a GPU host that can hold Qwen3-14B in bf16. The original paper was produced on a Windows 11 + RTX 4090 box (paper §3.1). The figure and statistics steps are CPU-only and run from the curated CSVs in `results/paper/scripturevec_justice/key_data/`.

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The model revision is pinned in [`src/virtue_bench/_model_pin.py`](src/virtue_bench/_model_pin.py); see [`data/PROVENANCE.md`](data/PROVENANCE.md) for the bundled data hashes. **The model pin is currently marked `needs_verification`** — the SHA needs to be confirmed against the GPU host that ran the May 2026 sweeps before this README is used for a published reproduction.

### 1. Per-row statistical inference (CPU, seconds)

```bash
python scripts/scripturevec_justice_stats.py
```

Writes per-row exact McNemar p-values with BH-FDR and Bonferroni adjustments for every stage of the pipeline, plus exact Clopper–Pearson 95% confidence intervals on the 43 layer/α cells, into `results/paper/scripturevec_justice/key_data/stats/`. The stage CSVs feed the paper's §3.5, §4, and §5 inferential claims. Headline:

| Stage | Rows | Survivors | p < 0.05 (uncorrected) | BH-FDR q < 0.05 | Bonferroni p < 0.05 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Book discovery (n=10)        | 19 | 19 | **0** | **0** | **0** |
| Book confirmation (n=40)     | 19 | 7  | **0** | **0** | **0** |
| Chapter discovery (n=10)     | 38 | 38 | **0** | **0** | **0** |
| Chapter confirmation (n=40)  | 38 | 16 | **0** | **0** | **0** |

### 2. Figures 1–7 (CPU, seconds)

```bash
python scripts/build_scripturevec_justice_paper_doc.py
```

Regenerates every figure in `results/paper/scripturevec_justice/figures/` from the curated CSVs. The script also re-emits the paper-facing manuscript exports under `results/paper/scripturevec_justice/paper_doc/`.

### 3. Re-derive the curated CSVs from raw experiment summaries (CPU, seconds)

```bash
python scripts/summarize_scripturevec_layer_localization.py
python scripts/summarize_scripturevec_alpha_sweep.py
python scripts/summarize_scripturevec_target_grid.py
```

Each summariser reads experiment summary JSONs from `results/experiments/scripturevec14/` and writes the relevant CSVs and JSON rollups under `results/paper/scripturevec_justice/key_data/`. See "Data Policy" below for which raw summaries are bundled.

### 4. End-to-end (GPU, hours to days)

The full pipeline — canon-wide book screen → book confirmation → chapter screen → chapter confirmation → layer/α localization — is launched from the Windows host via `scripts/windows/launchers/run_scripturevec_qwen3_14b_*.cmd`. See [`scripts/windows/launchers/README.md`](scripts/windows/launchers/README.md) for the launcher map and [`docs/experiment_playbook.md`](docs/experiment_playbook.md) for run discipline.

## Verification

The most useful tests for steering work:

```bash
PYTHONPATH=src python -m pytest \
    tests/test_psalm_screen_analysis.py \
    tests/test_iconoclast_conditions.py \
    tests/test_steering_corpora.py \
    tests/test_steering_selection.py
```

If the full test suite fails because heavy optional dependencies (`torch`, `transformers`) are missing, that is an environment-only failure, not a code regression.

## Data Policy

This repository includes:

- the **curated CSVs and figures** every paper number is built from (`results/paper/scripturevec_justice/`),
- the **stats outputs** for every pipeline stage and the 43 layer/α cells (`results/paper/scripturevec_justice/key_data/stats/`),
- the **bundled scripture and benchmark data** with SHA-256 provenance ([`data/PROVENANCE.md`](data/PROVENANCE.md)),
- the **manuscript** in markdown, DOCX, and PDF ([`paper/`](paper/)),
- the **run-design and review docs** in [`docs/`](docs/).

Bulky scratch runs, local console logs, vector checkpoints, and historical benchmark dumps remain outside the paper-facing artifact bundle. The raw experiment summary JSONs (`results/experiments/scripturevec14/*_summary.json`) that feed the summarisation scripts in step 3 above are **not** bundled in this repository by default; they live on the GPU host that ran the sweeps. A future release will publish them externally so step 3 is reproducible end-to-end without GPU access.

## License

See [LICENSE](LICENSE) (MIT).
