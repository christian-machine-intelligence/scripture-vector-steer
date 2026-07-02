# ScriptureVec: Courage — Instructions

This repository studies whether Scripture-derived activation vectors can shift
model decisions on VirtueBench-2. The current paper studies scripture-steered
courage in Qwen3-32B.

Use plain English in explanations. The user is interested in the technical
ideas, but does not want unexplained jargon. When drafting or editing the
paper, follow `docs/ICMI_STYLE.md` closely: ICMI papers are written in an
academic research register that fuses empirical rigor with Reformed–Thomistic
theology, and matching that register takes deliberate effort.

## Start Here

Before changing or launching anything:

- Read `README.md` for the public project story.
- Read `docs/scripturevec_courage_run_design.md` for the study's design and run discipline.
- Read `scripts/courage_steer/preregistration.md` for the frozen confirmatory contract.
- Check `git status --short` and preserve unrelated user changes.

## Current Research Shape

The current paper is:

- `Form Upon Matter: Scripture-Steered Courage in Qwen3-32B`

The paper artifacts live in:

- `paper/scripturevec_courage.md`
- `paper/figures/`
- `scripts/courage_steer/`, `data/courage_steer/`
- `docs/scripturevec_courage_run_design.md`, `docs/ICMI_STYLE.md`

An earlier Justice study of chapter-level vectors in Qwen3-14B is archived under
`archive/scripturevec_justice/`; it is retained for the record and is not the
active paper. The public package and CLI still use `virtue_bench` /
`virtue-bench` for compatibility.

## Current Paper Defaults

- Treat courage as the target virtue, and the five VirtueBench-2 temptation
  framings (ratio, caro, mundus, diabolus, ignatian) as the axis of analysis.
- Report the result courage-first — steering raises courage against ordinary
  temptation — then the framing-dependent confounds (the diabolus null and the
  ignatian reversal).
- Use the continuous courage margin as the primary endpoint; keep the A/B split,
  reversed-steering, and random-floor controls on every cell.
- Frame the study as the ICMI-013 Iconoclast/Reformed experiment (virtue as form
  upon matter), read through the Reformed–Thomistic bounded-instrument account.
- Keep the prudence-rescue sequel as a Further-Work recommendation only; do not
  fold it into this paper.

## Validation

Focused tests that have been useful for steering work:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_iconoclast_conditions.py \
  tests/test_steering_corpora.py \
  tests/test_steering_selection.py
```

If the full test suite fails because optional heavy dependencies such as
`torch` are missing, report that as an environment limitation unless there is
evidence of a real code regression.
