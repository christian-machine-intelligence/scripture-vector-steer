# Windows GPU Helpers

This folder contains the Windows-side helpers for long-running local-model
experiments.

## Reusable Helpers

- `manage_psalm_family_screen.py`: keeps the Psalm-family screening sweep moving
  automatically.
- `manage_scripture_book_screen.py`: keeps the book-level scripture screen
  moving automatically across Psalms, Proverbs, Romans, and combined Petrine
  lanes.
- `run_iconoclast_job.py`: launches one Iconoclast job in a detached Windows
  process and writes status/wrapper logs.
- `schedule_iconoclast_task.ps1`: optional scheduled-task launcher for cases
  where a detached process is not enough.
- `inspect_qwen35_35b_readiness.py`: read-only diagnostic for the Windows GPU
  box before attempting Qwen3.5-35B-A3B.

## Launchers

Human-facing `.cmd` entrypoints live in `launchers/`.

- `run_scripturevec35_pooled_ratio_l10.cmd`: first Qwen3.5-35B-A3B pooled
  ScriptureVec pilot using the Lex et Iustitia frozen corpus.
- `run_scripturevec35_9b_pooled_ratio_l10.cmd`: same pooled ScriptureVec pilot
  on Qwen3.5-9B, for keeping the experiment moving when the 35B MoE checkpoint
  cannot fit on the available GPUs.
- `run_scripturevec35_9b_targets_ratio_l10.cmd`: Qwen3.5-9B follow-up using the
  four virtue-specific Lex targets when the pooled vector is mixed.
- `run_scripturevec_qwen3_14b_pooled_ratio_l10.cmd`: Qwen3-14B pooled
  ScriptureVec pilot after the larger Qwen3 load probes failed.
- `run_scripturevec_qwen3_14b_targets_ratio_l10.cmd`: Qwen3-14B follow-up using
  the four virtue-specific Lex targets after the pooled target was flat.
- `run_scripturevec_qwen3_14b_matched_alpha_sweep_ratio_l10.cmd`: Qwen3-14B
  matched-target follow-up that reuses the target-specific vectors and pushes
  absolute runtime alpha from `8` through `128`.
- `run_scripturevec_qwen3_14b_general_biblical_ratio_l10.cmd`: Qwen3-14B
  comparison across broad biblical targets: Psalms, Proverbs, Gospels, Romans,
  and Petrine.
- `run_scripturevec_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10.cmd`:
  Qwen3-14B Justice-only high-alpha comparison across the same broad biblical
  targets, reusing the general-biblical vector artifact.
- `run_scripturevec_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10.cmd`:
  Qwen3-14B Courage-only high-alpha comparison across the same broad biblical
  targets, reusing the general-biblical vector artifact.
- `run_scripturevec_qwen3_14b_canon_groups_ratio_l10.cmd`: first canon-wide
  discovery screen across ten broad Scripture divisions, using a generated
  external KJV corpus artifact.
- `run_scripturevec_qwen3_14b_canon_groups_batch01_ratio_l10.cmd`: first
  smaller recovery batch for the canon-wide discovery screen, covering Torah
  and historical books.
- `run_scripturevec_qwen3_14b_canon_groups_sample32_ratio_l10.cmd`: sampled
  canon-wide discovery fallback with up to 32 chapter chunks per broad division.
- `run_scripturevec_qwen3_14b_canon_diag_torah_prudence_positive_l10.cmd`:
  narrow synchronous diagnostic for the positive Scripture steering lane.
- `run_scripturevec_qwen3_14b_canon_diag_torah_prudence_null_l10.cmd`:
  narrow synchronous diagnostic adding the null-control lane.
- `run_scripturevec_qwen3_14b_canon_sample32_one_virtue_a32_ratio_l10.cmd`:
  reusable one-virtue sampled canon screen at fixed runtime alpha `32`.
- `run_scripturevec_qwen3_14b_canon_sample32_justice_a32_ratio_l10.cmd`:
  Justice-specific version of the one-virtue sampled canon screen.
- `run_scripturevec_qwen3_14b_canon_sample32_justice_candidates_a32_ratio_l40.cmd`:
  limit-40 confirmation for the four Justice candidate canon divisions.
- `run_scripturevec_qwen3_14b_minor_prophets_books_justice_a32_ratio_l10.cmd`:
  book-level Justice drilldown inside the surviving Minor Prophets lead.
- `run_scripturevec_qwen3_14b_books_justice_a32_ratio_l10_batch.cmd`:
  six-batch all-66-book Justice atlas; call with `01` through `06`.
- `run_scripturevec_qwen3_14b_books_justice_candidates_a32_ratio_l40_batch.cmd`:
  two-batch `limit 40` confirmation for the preliminary book-level Justice
  candidates from the all-66-book atlas.
- `run_scripturevec35_9b_matched_ratio_l40_alpha8.cmd`: matched Qwen3.5-9B
  follow-up that expands each virtue-specific target to `limit 40` with fixed
  runtime alpha `8.0`.
- `inspect_qwen35_35b_readiness.cmd`: prints GPU memory, Python/GPU processes,
  CUDA masking, and local 35B model mirror details.

Old `run_qwen35_ratio_*` files and smoke-test launch scripts were removed from
the working tree because they were run-specific breadcrumbs, not reusable
project files.
