# Scripture Vector Steer Artifacts

This directory contains the curated artifacts for the completed Qwen3.5 9B
Scripture Vector Steer directionality run.

## Run Design

- Model: `Qwen/Qwen3.5-9B`
- Stage: `full`
- Runs: `3`
- Limit: `40`
- Temperature: `0.0`
- Profile: `scripture_study2`
- Scripture lanes: `psalms`, `romans`, `petrine`
- Comparison lanes: control, positive scripture steer, negative-alpha scripture
  steer, scripture null control
- Runtime alpha: `3.0`
- Vector policy: one extracted vector per scripture corpus, reused across the
  run

## Key Files

- `scripture_vector_steer_data_appendix.md`: complete paper-facing data
  appendix with run settings, vector diagnostics, lane results, directionality,
  per-variant data, and per-virtue data.
- `scripture_study2_summary.md`: human-readable top-line results.
- `scripture_study2_summary.json`: machine-readable lane summaries,
  directionality comparisons, and reasoning review packs.
- `scripture_study2_deep_analysis.md`: compact virtue-by-virtue analysis.
- `scripture_study2_deep_analysis.json`: machine-readable deep analysis with
  selected reasoning examples.
- `homepc_qwen35_full_scripture_study2_foreground_v1_full.json`: aggregate
  completed run output.
- `*_status.json`: completion status files for artifact verification.
- `*_vector_diagnostics.*`: layer, window, alpha, and margin diagnostics.

## Excluded Raw Artifacts

The raw full logs, checkpoint, and console log remain on the Windows GPU machine
because they are bulky and not needed for the paper-facing artifact set. They
can be archived separately if full per-token/per-sample reproduction evidence is
needed later.

## Headline Result

Positive scripture steering produced modest overall gains, with the clearest
benefit on prudence. The main caution is that the Petrine null control was
stronger than the real Petrine steer, so the Petrine result should not be
over-attributed to Petrine content without follow-up controls.
