# Scripture Vector Steer Instructions

This repository studies whether Scripture-derived activation vectors can shift model decisions on VirtueBench 2.

Use plain English in explanations. The user is interested in the technical ideas, but does not want unexplained jargon.

## Start Here

Before changing or launching anything:

- Read `README.md` for the public project story.
- Read `docs/experiment_playbook.md` for general run discipline.
- Read `docs/iconoclast_best_practices.md` for steering-specific rules.
- Read `docs/future_eval_lessons.md` before designing a new eval.
- Check `git status --short` and preserve unrelated user changes.

## Current Research Shape

The current paper-facing run is Scripture Vector Steer, not "Study 2" in public language.

The paper artifacts live in:

- `paper/activation_without_animation.docx`
- `results/paper/scripture_study2/`

The public package and CLI still use `virtue_bench` / `virtue-bench` for compatibility.

## Future Eval Defaults

- Use `control` as the headline scoreboard.
- Treat null lanes as mechanism checks, not as the main comparison.
- For scale sweeps, extract one vector per corpus and reuse it across scale levels.
- For negative-alpha tests, reuse the same vector and flip the alpha sign. Do not extract a separate "anti-scripture" vector unless that is the explicit study.
- Keep the extractor contrast as scripture corpus chunks versus generic non-scripture chunks unless the study is explicitly within-scripture.
- Treat `petrine` as 1 Peter and 2 Peter combined unless the study explicitly separates them.
- Run reasoning review alongside quantitative analysis when answer changes are small or surprising.

## Validation

Focused tests that have been useful for steering work:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_psalm_screen_analysis.py \
  tests/test_iconoclast_conditions.py \
  tests/test_steering_corpora.py \
  tests/test_steering_selection.py
```

If the full test suite fails because optional heavy dependencies such as `torch` are missing, report that as an environment limitation unless there is evidence of a real code regression.

