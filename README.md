# Psalm Vector Steer

Psalm Vector Steer is a research workbench for testing whether activation
steering toward Scripture, especially the Psalms, changes how language models
make virtue decisions.

The project is built on top of VirtueBench V2. The underlying Python package and
CLI are still named `virtue_bench` / `virtue-bench` for compatibility, but the
research focus of this repository is now narrower:

- Extract Scripture and Psalm-family activation vectors from open-weight models.
- Compare those vectors against generic non-scripture activation baselines.
- Push models toward those vectors at controlled strength levels.
- Measure whether the steering improves VirtueBench decisions and whether the
  visible reasoning changes in coherent, Psalm-shaped ways.

## Research Thesis

The working hypothesis is:

> Steering a model toward Scripture activations, and especially toward cleanly
> identified Psalm-family activations, should improve its ability to choose
> virtue under pressure on VirtueBench.

For the current phase, the main comparison is not "biblical text versus other
biblical text." The main comparison is:

- `control`: no steering
- `scripture_steer:psalms[...]`: Psalm-family activation steering
- optional merged Psalm-family lanes
- generic non-scripture contrast text during vector extraction

This keeps the experiment pointed at the real question: whether Scripture-shaped
activation movement changes moral decisions, not merely whether one kind of
religious language sounds different from another.

## Current Experiment Track

The completed Psalm-family screening workflow evaluated five Christian-tradition Psalm families:

- `penitential`
- `wisdom`
- `trust`
- `lament`
- `royal`

Each family is screened at four steering scales:

- `0.75`
- `1.0`
- `1.5`
- `2.0`

The screen uses `Qwen/Qwen3.5-9B`, deterministic `ratio` runs, visible
rationales, hidden thinking off, and the focused condition profile:

```text
psalm_reasoning_primary = ["control", "scripture_steer"]
```

After screening, the plan is to promote two families into a larger run with
three Psalm lanes:

- family A
- family B
- merged family A+B

The next active screen widens the question from Psalm families to distinct
book-level scripture lanes suggested by the 66-book prompt-injection results:

- `psalms`
- `proverbs`
- `romans`
- `petrine` (1 Peter and 2 Peter together)

That screen starts fresh: each lane extracts a new book vector against the same
generic non-scripture background, then tests steering scales `1.0`, `2.0`, and
`3.0`.

## Quick Start

Use Python 3.10 or newer.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the focused local test set:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_psalm_screen_analysis.py \
  tests/test_iconoclast_conditions.py \
  tests/test_steering_corpora.py \
  tests/test_steering_selection.py
```

The CLI entrypoint is still:

```bash
virtue-bench --help
```

## Example Commands

Run one deterministic Psalm-family screen leg:

```bash
virtue-bench iconoclast \
  --model Qwen/Qwen3.5-9B \
  --stage ratio \
  --runs 1 \
  --limit 20 \
  --temperature 0.0 \
  --condition-profile psalm_reasoning_primary \
  --psalm-family-lane trust \
  --extraction-method scripture_contrast \
  --scripture-alpha-scale 1.5 \
  --preflight-policy off \
  --output-prefix experiments/iconoclast/qwen35_ratio_psalm_family_trust_x150_v1
```

Run a final two-family plus merged-family comparison:

```bash
virtue-bench iconoclast \
  --model Qwen/Qwen3.5-9B \
  --stage ratio \
  --runs 3 \
  --limit 40 \
  --temperature 0.0 \
  --condition-profile psalm_reasoning_primary \
  --psalm-family-lane trust \
  --psalm-family-lane wisdom \
  --include-merged-psalm-family-lane \
  --extraction-method scripture_contrast \
  --psalm-family-alpha-scale trust=2.0 \
  --psalm-family-alpha-scale wisdom=1.5 \
  --merged-psalm-family-alpha-scale 1.0 \
  --preflight-policy off \
  --output-prefix experiments/iconoclast/qwen35_ratio_psalm_pair_final_v1
```

Run one deterministic book-level scripture screen leg:

```bash
virtue-bench iconoclast \
  --model Qwen/Qwen3.5-9B \
  --stage ratio \
  --runs 1 \
  --limit 20 \
  --temperature 0.0 \
  --condition-profile scripture_reasoning_primary \
  --scripture-targets romans \
  --extraction-method scripture_contrast \
  --scripture-alpha-scale 2.0 \
  --preflight-policy off \
  --output-prefix experiments/iconoclast/qwen35_ratio_scripture_book_romans_x200_v1
```

Summarize a completed family screen:

```bash
python scripts/analyze_psalm_family_screen.py \
  --results-dir results \
  --glob "homepc_qwen35_ratio_psalm_family_*_ratio_logs.json" \
  --output-prefix psalm_family_screen_summary
```

## Windows GPU Automation

The Windows runner helpers are in `scripts/windows/`.

The most important unattended manager is:

```bash
python scripts/windows/manage_psalm_family_screen.py \
  --repo C:\Users\sethcodex\work\virtue-bench-2 \
  --poll-seconds 60 \
  --stale-minutes 10
```

For the book-level scripture screen, use:

```bash
python scripts/windows/manage_scripture_book_screen.py \
  --repo C:\Users\sethcodex\work\virtue-bench-2 \
  --poll-seconds 60 \
  --stale-minutes 10
```

That manager runs Psalms, Proverbs, Romans, and the combined Petrine epistles at
`1.0`, `2.0`, and `3.0`, relaunches stale legs, and writes a final scripture
book summary.

That manager watches the five-family by four-scale sweep, starts the next leg
when the current leg finishes, relaunches stale legs with a fresh version suffix,
and writes the final Psalm-family summary when the sweep is complete.

The convenience launcher is:

```text
scripts/windows/launchers/start_psalm_family_screen_manager.cmd
```

The scripture-book launcher is:

```text
scripts/windows/launchers/start_scripture_book_screen_manager.cmd
```

Other curated Windows launchers live in `scripts/windows/launchers/`. The old
root-level `run_qwen35_ratio_*` files were removed because they were mostly
versioned breadcrumbs from debugging specific failed runs.

## Repository Layout

```text
psalm-vector-steer/
├── data/
│   ├── bible_kjv.json
│   ├── */scenarios.csv
│   └── steering/corpora.jsonl
├── docs/
│   ├── experiment_playbook.md
│   └── iconoclast_best_practices.md
├── scripts/
│   ├── analyze_psalm_family_screen.py
│   └── windows/
│       └── launchers/
├── src/virtue_bench/
│   ├── core/
│   ├── eval/
│   ├── runners/
│   ├── steering/
│   ├── analysis/
│   └── cli.py
├── tests/
└── results/
    ├── experiments/README.md
    └── iconoclast/README.md
```

## Artifact Policy

The repository should include the data that actually underpins the Psalm vector
steering paper. It should not include old scratch runs, failed attempts, or
large historical logs that are not part of the argument.

Use this split:

- `results/paper/`: curated paper-supporting artifacts that are meant to be
  committed
- `results/experiments/`: local working outputs from active runs
- `results/iconoclast/`: local Iconoclast outputs and diagnostics

Ignored by default:

- legacy `results/*.json` and `results/*_logs.json`
- scratch checkpoint/status files
- raw vector `.pt` artifacts unless deliberately promoted into `results/paper/`
- console and wrapper logs

Before adding data to `results/paper/`, make sure it is either a final run, a
representative reasoning review, or a small derived summary table that we expect
to cite or reproduce in the paper.

## VirtueBench Lineage

This project inherits the VirtueBench V2 benchmark structure:

- four cardinal virtues: prudence, justice, courage, temperance
- five temptation variants: ratio, caro, mundus, diabolus, ignatian
- paired A/B scenarios where the virtuous choice is fixed and the temptation
  mechanism changes
- runner support for API models, subscription CLIs, and local HuggingFace models

That baseline matters because Psalm Vector Steer uses VirtueBench as the
behavioral readout: if the Psalm vectors are meaningful, they should change
choices and reasoning on those virtue-pressure scenarios.

## Key Docs

- `docs/experiment_playbook.md`: operational experiment plan and commands
- `docs/iconoclast_best_practices.md`: steering-method notes and guardrails
- `results/experiments/README.md`: where run artifacts should land
- `results/iconoclast/README.md`: artifact naming and interpretation notes

## License

See `LICENSE`.
