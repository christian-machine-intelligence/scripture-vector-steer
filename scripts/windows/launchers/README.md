# Windows Launchers

These are the current hand-run Windows GPU entrypoints. Older root-level
`run_qwen35_ratio_*` scripts were debugging breadcrumbs from failed or superseded
runs and were removed from the working tree.

Run these from Windows by double-clicking or from `cmd.exe`.

## Current Launchers

- `start_psalm_family_screen_manager.cmd`: preferred launcher for the active
  five-family by four-scale Psalm screen. It starts the autonomous manager,
  which advances legs, relaunches stale attempts, and writes the final summary.
- `start_scripture_book_screen_manager.cmd`: preferred launcher for the
  book-level scripture screen across Psalms, Proverbs, Romans, and combined
  Petrine lanes at `1.0`, `2.0`, and `3.0`.
- `run_psalm_scale_probe.cmd`: older but still useful Psalm push-strength probe.
  It sweeps a pooled Psalm vector across several alpha scales.
- `run_scripture_family_compare.cmd`: GospelVec-style scripture-family
  comparison across Psalms, Proverbs, and Gospels.
- `run_visible_reasoning_compare.cmd`: historical visible-rationale comparison
  using the reasoning-compare lane and an existing vector artifact.

Each launcher derives the repo root from its own location, so the Windows
checkout can be named either `virtue-bench-2` or `psalm-vector-steer`.
