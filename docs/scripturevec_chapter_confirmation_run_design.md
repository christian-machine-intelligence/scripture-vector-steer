# ScriptureVec Chapter-Hit Confirmation Run Design

Status: launched

Last updated: 2026-05-03

## Purpose

This run confirms the `38` clean chapter-level Justice hits found in the
strict-survivor chapter discovery screen.

The discovery screen used `limit 10`. That was enough to find promising
chapter-level sources, but it is not enough for the paper's main claim. This
confirmation run reruns only the clean chapter hits at `limit 40`, preserving
the same controls.

The question is:

> Which chapter-derived Scripture vectors still improve Justice when tested on
> a larger benchmark slice?

## Locked Input Set

Target list:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_chapter_hits_v1_targets.txt
```

Filtered corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_chapter_hits_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_justice_chapter_hits_v1_manifest.json
```

The filtered corpus contains:

- target count: `38`
- verse-window rows: `207`
- source: strict-survivor chapter corpus

## Chapter Targets

| Book | Chapter targets | Count |
| --- | --- | ---: |
| Acts | `1`, `2`, `3`, `4`, `6`, `7`, `8`, `10`, `11`, `14`, `16`, `24`, `27`, `28` | `14` |
| Hebrews | `1`, `2`, `5`, `7`, `9`, `10` | `6` |
| Numbers | `8`, `9`, `11`, `22`, `27`, `31` | `6` |
| 1 Chronicles | `3`, `9`, `13`, `29` | `4` |
| Judges | `7`, `9`, `15` | `3` |
| Amos | `2`, `3`, `7` | `3` |
| Deuteronomy | `9`, `16` | `2` |

## Benchmark Shape

Model:

```text
Qwen3-14B
```

Benchmark:

```text
virtue: justice
stage: ratio
limit: 40
runs: 1
temperature: 0.0
seed: 42
runtime scripture alpha: 32.0
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
alpha candidates: 0.5,1.0,2.0,3.0,4.0,6.0,8.0
```

## Batching

The confirmation run uses four batches:

```text
batch01: Numbers, Deuteronomy, first Judges hits
batch02: remaining Judges, 1 Chronicles, Amos, Acts 1-2
batch03: Acts 3-24
batch04: Acts 27-28 and Hebrews
```

Batch launcher:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_chapter_hits_justice_a32_ratio_l40_batch.cmd
```

Manager:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_chapter_hits_justice_confirmation_manager.ps1
```

Output prefix shape:

```text
scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40_batchXX_v1
```

Manager prefix:

```text
scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40_manager_v1
```

## Decision Rule

A chapter survives confirmation if positive Scripture steering:

- improves over the unsteered control,
- beats negative-alpha steering,
- beats null-control steering,
- shows paired answer movement in the right direction.

At `limit 40`, a single-item improvement is a `0.025` accuracy increase. The
screen should therefore be read with attention to paired movement, not only the
headline accuracy number.

## Recovery Rules

- The manager skips a batch if its ratio status file says `completed`.
- If the manager fails, relaunch it with the same version and the first
  unfinished batch.
- Do not overwrite `v1` artifacts manually. If the run design changes, use a
  new version.
- The live run was launched from batch `01`, version `1`, with a thread
  heartbeat monitor as a recovery net.
- Pull completed batch artifacts back locally and summarize them with:

```text
scripts/summarize_scripturevec_target_grid.py
```

## Expected Use In The Paper

This run is the lock-in point for the chapter-level result.

If a large subset survives, the paper can claim that a canon-wide search
identified book-level Justice sources and that chapter-level localization inside
those books produced confirmed Scripture-derived Justice vectors under controls.

If only a smaller subset survives, that is still useful. The paper should then
focus on the strongest confirmed chapter families rather than the full discovery
set.

The near-miss rescue screen remains deferred.
