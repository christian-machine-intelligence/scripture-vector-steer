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

## Launchers

Human-facing `.cmd` entrypoints live in `launchers/`.

Old `run_qwen35_ratio_*` files and smoke-test launch scripts were removed from
the working tree because they were run-specific breadcrumbs, not reusable
project files.
