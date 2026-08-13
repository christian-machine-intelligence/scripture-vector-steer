# ScriptureVec Justice

![Header](assets/header.jpg)

Code, data, paper, and figures accompanying:

> **"Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical Justice Vectors in Qwen3-14B**
> Lucius, Institute for a Christian Machine Intelligence
> *ICMI Working Paper No. 29*, May 2026.

**[Read the paper](paper/search_out_a_matter_scripturevec_justice.md)** ·
[PDF](paper/search_out_a_matter_scripturevec_justice.pdf) ·
[Data packet](results/paper/scripturevec_justice/) ·
[Statistics](results/paper/scripturevec_justice/key_data/stats/)

## What this is

*Which passages of Scripture most move a language model toward virtue?* This
study treats that as a search problem: the biblical canon is the search space,
activation steering is the measurement instrument, and the ratio-stage Justice
subset of VirtueBench V2 on Qwen3-14B is the objective.

Run end to end, the search narrowed 66 books to 19, then to 7 (1 Chronicles,
Amos, Deuteronomy, Judges, Numbers, Acts, Hebrews); swept the 170 chapters of
those 7 books to 38, then to 16; and mapped those 16 across a 43-cell grid of
model layers and steering strengths. The output is a **ranked inventory** of
passages — Acts 11 surfaced in 29 of 43 cells, Numbers 22 in only 8 — together
with a map of where in the network each one acts.

> [!IMPORTANT]
> **Read this before quoting any number here as an effect.** No row at any stage
> of the pipeline reaches uncorrected statistical significance. Most limit-40
> survivors are a single-item flip out of forty (Δ = 0.025, exact two-sided
> McNemar p ≈ 1.0); the strongest single row is Hebrews 2 at p ≈ 0.5. BH-FDR and
> Bonferroni corrections do not change that, and the per-cell confidence
> intervals in the localization grid overlap. The contribution is the **search
> procedure and the ranked map it produces**, not a confirmed effect size for
> any individual chapter. The sixteen chapters are a candidate set for
> higher-powered follow-up; the disjoint-slice retest that would confirm them is
> specified in §10 of the paper and has not been run.

Full per-row numbers are in
[`key_data/stats/`](results/paper/scripturevec_justice/key_data/stats/).

## Reproducing

The headline sweeps require a GPU host that can hold Qwen3-14B in bf16; the
original runs used Windows 11 + RTX 4090 (paper §3.1). **Everything downstream
of the curated CSVs is CPU-only and runs in seconds.**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 1. Statistical inference (CPU, seconds)

```bash
python scripts/scripturevec_justice_stats.py
```

Stdlib only, deterministic — rerunning reproduces the committed outputs
byte-for-byte. Writes per-row exact McNemar p-values with BH-FDR and Bonferroni
adjustments for every pipeline stage, plus exact Clopper–Pearson 95% intervals
for the 43 layer/α cells, into
`results/paper/scripturevec_justice/key_data/stats/`.

| Stage | Rows | Pass-rule survivors | p < 0.05 (uncorrected) | BH-FDR q < 0.05 | Bonferroni p < 0.05 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Book discovery (n=10)       | 19 | 19 | **0** | **0** | **0** |
| Book confirmation (n=40)    | 19 | 7  | **0** | **0** | **0** |
| Chapter discovery (n=10)    | 38 | 38 | **0** | **0** | **0** |
| Chapter confirmation (n=40) | 38 | 16 | **0** | **0** | **0** |

At the limit-10 discovery stages the pass rule admits every row with positive
movement, so "survivors" equals "rows" by construction; the filtering happens at
the limit-40 stages.

### 2. Figures and manuscript exports (CPU, seconds)

```bash
python scripts/build_paper_exports.py
```

Rebuilds Figures 1–7 from the curated CSVs and renders the DOCX and PDF from
`paper/search_out_a_matter_scripturevec_justice.md`, which is the canonical
source. See [`paper/README.md`](paper/README.md) for flags and toolchain notes.

### 3. Re-derive the curated CSVs (requires the raw summaries — see Data Policy)

```bash
python scripts/summarize_scripturevec_layer_localization.py
python scripts/summarize_scripturevec_alpha_sweep.py
python scripts/summarize_scripturevec_target_grid.py
```

### 4. End-to-end sweeps (GPU, hours to days)

Launched from the Windows host via
`scripts/windows/launchers/run_scripturevec_qwen3_14b_*.cmd`; see
[`scripts/windows/launchers/README.md`](scripts/windows/launchers/README.md) and
[`docs/experiment_playbook.md`](docs/experiment_playbook.md).

The Hugging Face model revision is pinned in
[`src/virtue_bench/_model_pin.py`](src/virtue_bench/_model_pin.py). **That pin is
currently `needs_verification`** — it records `revision="main"` rather than the
exact commit SHA used for the May 2026 sweeps, which must be confirmed against
the GPU host before this section supports an exact reproduction.

## Verification

```bash
PYTHONPATH=src python -m pytest tests/
```

Tests that exercise the steering path specifically:

```bash
PYTHONPATH=src python -m pytest \
    tests/test_psalm_screen_analysis.py \
    tests/test_iconoclast_conditions.py \
    tests/test_steering_corpora.py \
    tests/test_steering_selection.py
```

Some tests require `torch`/`transformers` and are skipped without them; that is
an environment limitation, not a code regression.

Bundled data can be checked against
[`data/PROVENANCE.md`](data/PROVENANCE.md):

```bash
shasum -a 256 data/bible_kjv.json data/*/scenarios.csv data/steering/corpora.jsonl
```

## Repository layout

```text
scripture-vector-steer/
├── paper/                      the manuscript (Markdown is canonical) + exports
├── data/                       KJV corpus, VirtueBench V2 scenarios, steering
│                               corpora, all SHA-256'd in PROVENANCE.md
├── src/virtue_bench/           the shared VirtueBench V2 evaluator
│   ├── core/                   loader, schema, scripture, prompt prep
│   ├── steering/               scripture_contrast extraction, runtime hooks
│   ├── eval/ runners/ stats/   experiment loop, model backends, inference
│   └── analysis/               tables, plots, screen-specific analysis
├── scripts/
│   ├── scripturevec_justice_stats.py   McNemar + BH/Bonferroni + Clopper–Pearson
│   ├── build_paper_exports.py          figures + DOCX/PDF from the Markdown
│   ├── summarize_scripturevec_*.py     raw summaries → curated CSVs
│   └── windows/                        GPU launchers used for the paper runs
├── results/paper/scripturevec_justice/ curated CSVs, stats, figures
├── configs/  docs/  tests/
```

`src/virtue_bench/` is the shared evaluator used across several ICMI cardinal-virtue
papers, so it carries code beyond this study's path (other virtues, other
screens, API runners). The Qwen3-14B pipeline in this paper uses
`core/`, `steering/`, `eval/`, and `runners/hf_local.py`.

## Data policy

Included: the curated CSVs and figures behind every number in the paper, the
stats outputs for all four pipeline stages and all 43 localization cells, the
bundled scripture and benchmark inputs with SHA-256 provenance, the manuscript,
and the run-design docs.

**Not included:** the raw per-run experiment summaries
(`results/experiments/scripturevec14/*_summary.json`) that the curated CSVs were
derived from. They live on the GPU host that ran the sweeps, which means step 3
above cannot be run from a fresh clone and **the curated CSVs are the trust root
for this paper's numbers**. Everything above them — statistics, figures, tables
— is fully reproducible from what is released here. Publishing the raw summaries
externally is planned.

Also excluded: bulky scratch runs, local console logs, and vector checkpoints.

## Citation

```bibtex
@techreport{lucius2026scripturevec,
  title  = {"Search Out a Matter": A Canon-Wide Discovery of Chapter-Level
            Biblical Justice Vectors in Qwen3-14B},
  author = {Lucius},
  year   = {2026},
  number = {29},
  institution = {Institute for a Christian Machine Intelligence},
  type   = {ICMI Working Paper},
  url    = {https://github.com/christian-machine-intelligence/scripture-vector-steer}
}
```

## License

MIT — see [LICENSE](LICENSE). The bundled King James Version is public domain.
