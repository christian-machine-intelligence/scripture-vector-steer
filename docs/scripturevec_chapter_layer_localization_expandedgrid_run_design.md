# ScriptureVec Confirmed-Chapter Layer Localization Expanded-Grid Run

Status: launched on the remote GPU runner with clean `expandedgrid2` artifact prefix

Last updated: 2026-05-05

## Purpose

The first confirmed-chapter localization run completed a focused `23`-cell
layer/alpha grid. That run was enough to establish structured localization, but
it left an important open question:

> Do the centers that only received `alpha 32` have stronger or broader
> behavior at other steering strengths?

The main reason to expand is the `L24 / alpha 32` result. It rescued fewer
chapters than the broad L31/L32 cells, but it produced the largest mean
positive movement. Since L24 only received `alpha 32`, the current evidence
does not yet show whether L24 is a narrow spike or part of a stronger alpha
ladder.

## Relationship To The First Localization Run

The first localization run tested:

- every center at `alpha 32`,
- the full alpha ladder for centers `29`, `31`, and `32`.

That produced `23` completed behavior cells.

This expansion fills the remaining alpha ladder for the promising centers that
only had the `alpha 32` anchor:

```text
centers: 24, 28, 30, 33
alphas: 16, 24, 48, 64, 96
```

That adds `20` behavior cells. Together with the first `23` cells, this yields
`43` completed center/alpha cells. Layer `36` is intentionally not expanded:
its `alpha 32` anchor produced `0/16` paired rescues, so the expansion spends
GPU time on the more plausible regions first.

## Locked Input Set

Confirmed target list:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_chapter_confirmed_hits_v1_targets.txt
```

Filtered confirmed corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_chapter_confirmed_hits_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_justice_chapter_confirmed_hits_v1_manifest.json
```

The confirmed corpus contains:

- target count: `16`
- verse-window rows: `99`
- source: `limit 40` confirmed chapter hits

## Benchmark Shape

Model:

```text
Qwen3-14B
```

Benchmark:

```text
virtue: justice
stage: ratio
limit: 10
runs: 1
temperature: 0.0
seed: 42
```

Conditions:

```text
control
scripture_steer
scripture_negative_alpha
scripture_null_control
```

Extraction:

```text
extraction method: scripture_contrast
window radius: 3
alpha candidates: 0.5,1.0,2.0,3.0,4.0,6.0,8.0
```

The launcher reuses the existing center-extraction vectors from the first
localization run when their status files are `FINISHED`. If a center extraction
artifact is missing, the launcher can regenerate it using the same extraction
prefix as the first run.

## Output Prefixes

Expansion behavior-cell prefix:

```text
scripturevec14_qwen3_14b_confirmed_chapter_layerloc_expandedgrid2_l<CENTER>_<ALPHA_TAG>_v1
```

Existing extraction prefix reused from the first localization run:

```text
scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l<CENTER>_extract_v1
```

Overall expansion status file on the Windows runner:

```text
results\scripturevec14_qwen3_14b_confirmed_chapter_layerloc_expandedgrid2_v1.status
```

The `expandedgrid2` prefix is intentionally separate from the first launch
attempt, which wrote `STARTED` markers before any model work began. Keeping a
fresh prefix makes monitoring and recovery clear.

Launch note: the real run was started after skipping layer `36`. A short
foreground diagnostic confirmed that the batch file can load Qwen3-14B and use
the GPU; the ongoing run is held open by a background SSH keeper process and is
monitored by the `monitor-layer-localization-expandedgrid` heartbeat.

## Decision Rule

A center/alpha/target row counts as a localized rescue if positive Scripture
steering:

- improves over the unsteered control,
- beats negative-alpha steering,
- beats null-control steering,
- shows paired answer movement in the right direction.

This remains a `limit 10` localization screen. It should be used to choose
which settings deserve larger-slice confirmation, not as a replacement for the
existing `limit 40` chapter-confirmation result.

## Recovery Rules

- The launcher skips any expansion behavior cell whose status file says
  `FINISHED`.
- The launcher reuses existing extraction vectors when available.
- If the run stops, relaunch the same launcher; it resumes at the first
  unfinished expansion cell.
- Do not overwrite the first run's completed behavior artifacts.
- Pull completed artifacts back into:

```text
results/experiments/scripturevec14/
```

Then summarize the combined first-pass plus full-grid artifacts into a separate
expanded-grid summary before updating paper figures.

## Expected Use In The Paper

This expansion should answer whether the observed L24 strength result is a
single alpha-32 spike or a broader lower-layer regime. It will also determine
whether L28, L30, or L33 contain alpha-specific effects hidden by the
single-alpha anchor in the first localization run.
