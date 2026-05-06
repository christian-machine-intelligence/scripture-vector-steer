# ScriptureVec Chapter Drilldown Run Design

Status: completed preliminary screen

Last updated: 2026-05-03

## Purpose

This run moves from book-level Justice candidates to chapter-level Justice
discovery.

The prior all-66-book atlas found seven book-level survivors:

- `1 Chronicles`
- `Amos`
- `Deuteronomy`
- `Judges`
- `Numbers`
- `Acts`
- `Hebrews`

The chapter drilldown asks:

> Which chapters inside those seven books produce the most stable
> Justice-moving Scripture vectors?

## Corpus

Generated corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_survivor_chapters_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_justice_survivor_chapters_v1_manifest.json
```

Generator:

```text
scripts/build_canon_discovery_corpus.py
```

Generation shape:

```text
mode: chapters
book ids: 1CH, AMO, DEU, JDG, NUM, ACT, HEB
chapter window verses: 6
```

This creates one target per chapter, such as `chapter_heb_11`, but splits each
chapter into verse windows underneath the target. That keeps the scored unit at
the chapter level while giving vector extraction more than one text chunk where
possible.

Corpus size:

- chapter targets: `170`
- verse-window rows: `952`
- biblical books: `7`

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

There are 170 chapter targets, so the screen runs in 17 batches of 10 targets.

Batch launcher:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_chapters_justice_a32_ratio_l10_batch.cmd
```

Sequential all-batch launcher:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_chapters_justice_a32_ratio_l10_all.cmd
```

Python sequential manager used for launch:

```text
scripts/windows/run_scripturevec_chapter_justice_screen.py
scripts/windows/launchers/start_scripturevec_qwen3_14b_chapters_justice_manager.cmd
```

Output prefix shape:

```text
scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batchXX_v1
```

Manager prefix:

```text
scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_all_v2
```

Operational note:

- `batch01_v1` and `batch01_v2` both stalled reproducibly during
  `scripture_steer:chapter_num_03`.
- `all_v2` therefore uses `batch01_skip03_v1`, which covers Numbers 1-2 and
  Numbers 4-10.
- `chapter_num_03` should be treated as a separate stability diagnostic, not as
  a blocker for the full chapter screen.

## Decision Rule

A chapter is a preliminary passage lead if positive Scripture steering:

- improves over control,
- beats negative-alpha steering,
- beats null-control steering,
- has paired answer movement in the right direction.

This is a discovery screen only. Surviving chapters should be confirmed at
`limit 40` before they become paper-facing results.

## Recovery Rules

- The all-batch launcher skips batches whose `.status` file says `FINISHED`.
- If the manager fails at a batch, relaunch the all-batch launcher; it should
  continue after finished batches.
- Do not overwrite `v1` artifacts manually. If the design changes, create a
  `v2` prefix.
- Treat this screen as chapter discovery, not final confirmation.

## Completion Result

The strict-survivor chapter screen completed across all 17 batches, with
`chapter_num_03` held out as a stability diagnostic.

Preliminary result artifact:

```text
docs/scripturevec_chapter_drilldown_preliminary_results.md
```

The screen found `38` clean preliminary Justice hits across the seven
book-level survivors:

- Acts: `14`
- Hebrews: `6`
- Numbers: `6`
- 1 Chronicles: `4`
- Judges: `3`
- Amos: `3`
- Deuteronomy: `2`

## Next Step After Completion

Keep the near-miss rescue screen held for later. The immediate mainline next
step is to confirm the `38` clean strict-survivor chapter hits at a larger
benchmark slice, using the same positive, negative-alpha, and null controls.

Only chapters that survive that larger confirmation run should move into
passage-window narrowing, layer localization, and mechanistic analysis.
