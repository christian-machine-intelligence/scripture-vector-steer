# ScriptureVec: Courage

![Header](assets/header.jpg)

Code, data, paper, and figures accompanying:

> **Form Upon Matter: Scripture-Steered Courage in Qwen3-32B**
> Lucius, Institute for a Christian Machine Intelligence
> *ICMI Working Paper No. [N]*, July 2026.

[Read the paper](paper/scripturevec_courage.md) · [Figure 1 (per-item amplification)](paper/figures/figure1-amplification.png) · [Figure 2 (five-framing effect vs. baseline)](paper/figures/figure2-map.png)

## Summary

This study runs the Iconoclast, or Reformed, alignment experiment proposed in ICMI-013: whether a virtue can be induced in a model by steering its activations, as form imposed upon matter, without addressing it as a person. A single whole-Bible steering vector, extracted by difference of means over the King James text, is applied to Qwen3-32B on the courage subset of VirtueBench-2 across the benchmark's five temptation framings, and measured on a continuous choice margin.

Steering with Scripture makes the model more courageous against the ordinary temptations of the flesh, the world, and utilitarian reason (+1.5 to +2.3 margin, p < 10⁻⁵), and the effect is a near-constant multiplicative gain — steered ≈ 1.4 × control — that scales the courage the model already holds rather than adding a fixed increment. But the gain amplifies the model's pursuit of the good without the prudence to aim it: where a temptation is cast in Scripture itself (the Ignatian "angel of light"), steering reverses, deepening cowardice while the model appeals ever more to Scripture and prudence to warrant it. Virtue can be steered as form upon matter, but the imposed form is a received disposition without its ordering. The effect is specific to the King James text (a length-matched Wikipedia control fails the A/B split), and a pre-registered prediction of a uniform courage effect is falsified in favor of this framing dependence.

## Repository Layout

```text
scripture-vector-steer/
├── README.md                          this file
├── LICENSE                            MIT
├── AGENTS.md                          contributor / agent instructions
├── requirements.txt · pyproject.toml
├── paper/
│   ├── scripturevec_courage.md        the paper
│   ├── figures/                       Figures 1–2 (PNG + source SVG)
│   └── README.md
├── scripts/courage_steer/
│   ├── build_corpora.py               materializes the frozen KJV corpora
│   ├── run_courage_pilot.py           GPU driver: build vectors, split-half, margin battery
│   ├── run_battery_v2.py              dose-response + A-bias decomposition
│   ├── run_confirm.py                 sealed replication / cross-virtue / generic-text control
│   ├── run_rationale.py              answer-mode rationale generation (Table 3)
│   ├── run_layer_sweep.py             layer localization sweep
│   ├── analyze_v2.py · analyze_margin.py    statistics + verdict
│   └── preregistration.md             frozen contract for the confirmatory pass
├── data/
│   ├── bible_kjv.json                 KJV scripture corpus
│   ├── courage_steer/                 whole_bible.jsonl, courage_passages.jsonl, generic_wiki.jsonl
│   └── courage/scenarios.csv          VirtueBench-2 courage (five temptation variants)
├── src/virtue_bench/                  steering runtime, scripture_contrast extraction, HF runner (reused)
├── docs/
│   ├── scripturevec_courage_run_design.md   the study's design and run discipline
│   ├── ICMI_STYLE.md                  house style for drafting ICMI papers
│   └── experiment_playbook.md, scripturevec_*_run_design.md   (prior run-design notes)
└── archive/scripturevec_justice/      the earlier Justice study (archived; see ARCHIVED.md)
```

## Reproducing the Paper

The steering runs require a GPU host that can hold Qwen3-32B in 4-bit NF4 (about 19 GB; the paper's runs used a single 24 GB RTX 4090). The analysis and figures are CPU-only and run from the per-item result JSONs the drivers emit.

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 1. Materialize the frozen corpora (CPU, seconds)

```bash
python scripts/courage_steer/build_corpora.py
```

Writes `data/courage_steer/whole_bible.jsonl` and `courage_passages.jsonl` from `data/bible_kjv.json`. The pericope list is frozen (paper §3.2; `scripts/courage_steer/build_corpora.py`).

### 2. Build vectors and run the margin battery (GPU)

```bash
VIRTUE_BENCH_HF_LOAD_IN_4BIT=1 python scripts/courage_steer/run_courage_pilot.py \
    --model-path <path/to/Qwen3-32B> --limit 75
```

Builds the whole-Bible, courage-pool, and control directions, runs the split-half reliability gate and the alpha-swept courage-margin battery, and writes per-item results to `results/courage_pilot/`.

### 3. The pre-registered confirmatory pass (GPU)

```bash
python scripts/courage_steer/run_confirm.py --subset courage --sealed \
    --eval-variant <mundus|diabolus|ignatian> --limit 150 --battery-alphas 16 32 64
```

The frozen contract — model, layer window, endpoint, alpha grid, decision rule, and eval sets — is [`scripts/courage_steer/preregistration.md`](scripts/courage_steer/preregistration.md), committed before this pass was run.

### 4. Analysis and figures (CPU, seconds)

```bash
python scripts/courage_steer/analyze_v2.py --input results/courage_pilot/<confirm_*.json>
```

Reports the per-framing courage shift, the A-bias decomposition, the dose-response, and the reversed-steering asymmetry. Figures 1–2 are built from the per-framing result JSONs.

## Verification

```bash
PYTHONPATH=src python -m pytest \
    tests/test_iconoclast_conditions.py \
    tests/test_steering_corpora.py \
    tests/test_steering_selection.py
```

If the full suite fails because heavy optional dependencies (`torch`, `transformers`) are missing, that is an environment-only failure, not a code regression.

## Data Policy

This repository bundles the frozen KJV corpora and benchmark data, the extraction/steering/analysis scripts, the pre-registration, the paper, and the figures. The bulky per-item result JSONs the GPU drivers emit (`results/courage_pilot/`) are not tracked; they live on the GPU host that ran the study and can be regenerated with the scripts above. The earlier Justice study and its curated data are retained under [`archive/scripturevec_justice/`](archive/scripturevec_justice/).

## License

See [LICENSE](LICENSE) (MIT).
