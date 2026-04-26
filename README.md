# Scripture Vector Steer

Scripture Vector Steer is a research repository for testing whether
Scripture-derived activation vectors can shift language-model decisions on
VirtueBench 2.

The current paper is:

- [Activation Without Animation](paper/activation_without_animation.docx)

The supporting run artifacts are curated here:

- [results/paper/scripture_study2](results/paper/scripture_study2/README.md)
- [data appendix](results/paper/scripture_study2/scripture_vector_steer_data_appendix.md)

## Abstract

The project evaluates Qwen3.5-9B on VirtueBench 2 using book-level Scripture
directions extracted from Psalms, Romans, and the Petrine epistles. Each vector
is tested against a shared control with positive steering, negative-alpha
steering, and null-control steering.

The headline result is deliberately narrow: Scripture-associated activation
directions are behaviorally active and improve prudence most consistently, but
the full pattern is not a simple "more Scripture vector means more virtue"
story. Justice is fragile, negative-alpha Psalms and Romans outperform their
positive lanes, and the Petrine null control outperforms the real Petrine
vector. The paper interprets that result as evidence for bounded
instrumentality: steering can alter an artifact's formal operation without
turning the model into a soul, conscience, moral patient, or spiritual
authority.

## Repository Contents

```text
paper/
  activation_without_animation.docx

results/paper/scripture_study2/
  README.md
  scripture_vector_steer_data_appendix.md
  scripture_study2_summary.md
  scripture_study2_deep_analysis.md
  *_vector_diagnostics.*
  *_full.json

src/virtue_bench/
  benchmark, runner, steering, and analysis code

data/
  VirtueBench scenarios and Scripture/steering source corpora

tests/
  focused regression tests for the benchmark and steering extensions
```

## Future Evals

Before designing the next steering run, read:

- [docs/experiment_playbook.md](docs/experiment_playbook.md)
- [docs/iconoclast_best_practices.md](docs/iconoclast_best_practices.md)
- [docs/future_eval_lessons.md](docs/future_eval_lessons.md)

The short version: use `control` as the headline comparison, freeze vector
artifacts before scale sweeps, treat null lanes as mechanism checks, and pair
the quantitative readout with reasoning examples.

## Installation

Use Python 3.10 or newer.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The CLI entrypoint is:

```bash
virtue-bench --help
```

## Verification

Run the focused local test set:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_psalm_screen_analysis.py \
  tests/test_iconoclast_conditions.py \
  tests/test_steering_corpora.py \
  tests/test_steering_selection.py
```

For a broader smoke check:

```bash
PYTHONPATH=src python -m pytest
```

## Data Policy

This public repository includes the code, benchmark source data, and curated
artifacts that support the paper. It intentionally excludes old scratch runs,
failed attempts, local console logs, bulky vector checkpoints, and historical
VirtueBench outputs that are not part of the paper argument.

The raw decision-level artifact for the completed Scripture Vector Steer run is
included in `results/paper/scripture_study2/`. Bulky raw logs remain excluded.

## Lineage

This project builds on VirtueBench 2 and extends it with activation-steering
experiments for Scripture-derived corpora. The underlying Python package and
CLI remain named `virtue_bench` / `virtue-bench` for compatibility.

## License

See [LICENSE](LICENSE).
