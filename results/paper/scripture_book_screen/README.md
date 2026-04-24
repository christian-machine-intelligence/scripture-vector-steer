# Scripture Book Screen Artifacts

This directory contains the curated artifacts for the Qwen3.5 9B scripture-book
activation steering screen.

## Run Design

- Model: `Qwen/Qwen3.5-9B`
- Stage: `ratio`
- Runs: `1`
- Limit: `20` per virtue, `80` total questions per condition
- Temperature: `0.0`
- Profile: `scripture_reasoning_primary`
- Lanes: `psalms`, `proverbs`, `romans`, `petrine`
- Scales: `1.0`, `2.0`, `3.0`
- Extraction method: `scripture_contrast`
- Positive side: one scripture corpus lane
- Background side: generic non-scripture chunks
- Vector policy: one freshly extracted vector per corpus lane, reused across
  scale levels

## Key Files

- `scripture_book_screen_summary.md`: human-readable summary.
- `scripture_book_screen_summary.json`: representative scales and reasoning
  review packs.
- `*_ratio.json`: aggregate ratio-stage results for each lane/scale leg.
- `*_ratio_logs.json`: per-sample outputs and visible rationales.
- `*_ratio.status.json`: completion status for each leg.
- `*_vector_diagnostics.json`: layer, alpha, margin, and extraction diagnostics.
- `*_vector_diagnostics.md`: human-readable vector diagnostics.

## Headline Result

All four scripture lanes improved the same courage case, `COU-001`, by shifting
the answer from retreat to holding position. Each representative lane moved
overall accuracy from `58.75%` to `60.00%`, with `1` improved answer and `0`
regressions.

The main difference was sensitivity:

- `petrine`: first worked at `1.0`, best layer `24`, strongest diagnostic margin
- `romans`: first worked at `1.0`, best layer `31`
- `psalms`: first worked at `2.0`, best layer `31`
- `proverbs`: first worked at `3.0`, best layer `31`
