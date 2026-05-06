# Windows Launchers

These are reusable Windows GPU entrypoints for long-running local-model
experiments. Older one-off launch scripts were debugging breadcrumbs from failed
or superseded runs and were removed from the public repository.

Run these from Windows by double-clicking or from `cmd.exe`.

## Current Launchers

- `start_psalm_family_screen_manager.cmd`: preferred launcher for the active
  five-family by four-scale Psalm screen. It starts the autonomous manager,
  which advances legs, relaunches stale attempts, and writes the final summary.
- `start_scripture_book_screen_manager.cmd`: preferred launcher for the
  book-level scripture screen across Psalms, Proverbs, Romans, and combined
  Petrine lanes at `1.0`, `2.0`, and `3.0`.
Each launcher derives the repo root from its own location, so the Windows
checkout can be named either `virtue-bench-2` or `psalm-vector-steer`.
