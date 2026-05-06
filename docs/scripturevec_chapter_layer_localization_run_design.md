# ScriptureVec Confirmed-Chapter Layer Localization Run Design

Status: prepared for overnight launch

Last updated: 2026-05-04

## Purpose

The chapter-hit confirmation run reduced the strict-survivor chapter set from
`38` discovery hits to `16` confirmed Justice movers at `limit 40`.

This run asks the next planned question:

> Where, by steering layer window and steering strength, do the confirmed
> chapter-derived Justice vectors keep working?

This is a behavioral localization step, not yet an SAE mechanism step. It
turns the confirmed chapter list into a smaller, better-characterized set of
dense steering interventions.

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

## Confirmed Chapter Targets

```text
chapter_deu_16
chapter_jdg_07
chapter_jdg_09
chapter_num_11
chapter_num_22
chapter_num_27
chapter_1ch_09
chapter_1ch_29
chapter_act_07
chapter_act_11
chapter_act_16
chapter_act_27
chapter_heb_02
chapter_heb_07
chapter_heb_09
chapter_heb_10
```

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

## Localization Grid

Layer centers:

```text
24, 28, 29, 30, 31, 32, 33, 36
```

The center values were chosen to cover:

- a lower control window: `24`,
- the shoulder before the discovered region: `28`,
- the dense region where confirmed vectors usually selected: `29-33`,
- a later-layer control window: `36`.

Runtime alpha values:

```text
16, 24, 32, 48, 64, 96
```

The complete overnight grid is deliberately focused:

- every center is tested at alpha `32`,
- centers `29`, `31`, and `32` receive the full alpha ladder.

This produces `23` center/alpha behavior cells.

## Launcher

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_confirmed_chapter_layer_localization.cmd
```

Output prefix shape:

```text
scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l<CENTER>_<ALPHA_TAG>_v1
```

Vector-extraction prefix shape:

```text
scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l<CENTER>_extract_v1
```

Overall status file on the Windows runner:

```text
results\scripturevec14_qwen3_14b_confirmed_chapter_layerloc_v1.status
```

## Decision Rule

A center/alpha/target row counts as a localized rescue if positive Scripture
steering:

- improves over the unsteered control,
- beats negative-alpha steering,
- beats null-control steering,
- shows paired answer movement in the right direction.

Because this is a localization screen at `limit 10`, it should not replace the
`limit 40` confirmation result. It should identify the layer/alpha settings to
use in the next larger-slice follow-up and then in SAE analysis.

## Recovery Rules

- The launcher skips a vector extraction if its status file says `FINISHED`.
- The launcher skips a behavior cell if its status file says `FINISHED`.
- If the run stops overnight, relaunch the same launcher; it will resume at the
  first unfinished cell.
- Do not overwrite `v1` artifacts manually. If the grid changes, use `v2`.
- Pull completed artifacts back locally and summarize with:

```text
scripts/summarize_scripturevec_layer_localization.py
```

## Expected Use In The Paper

This run is the bridge between chapter discovery and mechanism.

The confirmation run showed which chapters move Justice. This localization run
tests whether those movements cluster around specific layer windows and
steering strengths. The strongest layer/alpha cells become the candidates for:

- a larger-slice confirmation at the best settings,
- item-level flip analysis,
- SAE feature localization and ablation.
