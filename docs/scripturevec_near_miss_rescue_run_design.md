# ScriptureVec Near-Miss Rescue Run Design

Status: queued after strict-survivor chapter drilldown

Last updated: 2026-05-03

## Purpose

This screen tests whether some books that failed the strict whole-book
confirmation still contain specific chapters that produce useful Justice-moving
vectors.

The strict survivor chapter screen remains the primary next step. This near-miss
screen should run after that screen, and its results should be labeled as a
rescue/exploratory passage search unless they later survive locked
confirmation.

Research question:

> Did any books fail at whole-book level because the book corpus was too broad,
> even though particular chapters inside them contain useful Justice-moving
> vectors?

## Source Set

The source set includes two kinds of near-miss books.

First, it includes the 12 preliminary book-level candidates that appeared in
the all-66-book `limit 10` atlas but did not survive the stricter `limit 40`
book confirmation:

- `1 Samuel`
- `2 Kings`
- `Hosea`
- `Nehemiah`
- `Song of Solomon`
- `Habakkuk`
- `John`
- `Lamentations`
- `Luke`
- `Mark`
- `Nahum`
- `Revelation`

Second, it includes `2 Corinthians`, which was not a clean preliminary
candidate because positive steering and negative-alpha steering both improved
in the same smaller screen. That makes it control-contaminated at book level,
but still worth testing as a passage-rescue case.

This gives the screen 13 books total.

## Corpus

Generated corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_near_miss_chapters_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_justice_near_miss_chapters_v1_manifest.json
```

Generation shape:

```text
mode: chapters
book ids: 1SA, 2KI, HOS, NEH, SNG, HAB, JHN, LAM, LUK, MRK, NAM, REV, 2CO
chapter window verses: 6
```

This creates one target per chapter while splitting each chapter into
six-verse windows underneath the chapter target.

Corpus size:

- chapter targets: `198`
- verse-window rows: `1063`
- biblical books: `13`

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

There are 198 chapter targets, so the screen runs in 20 batches of up to 10
targets.

Batch launcher:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_near_miss_chapters_justice_a32_ratio_l10_batch_detached.cmd
```

Output prefix shape:

```text
scripturevec14_qwen3_14b_near_miss_chapters_justice_a32_ratio_l10_batchXX_v1
```

## Decision Rule

A near-miss chapter becomes a rescue lead if positive Scripture steering:

- improves over control,
- beats negative-alpha steering,
- beats null-control steering,
- has paired answer movement in the right direction.

Because this is a rescue screen, the interpretation should be stricter than the
first survivor run. A near-miss chapter should not become paper-facing evidence
unless it survives `limit 40` confirmation.

## Ordering Rule

Do not launch this screen until the strict-survivor chapter screen has finished
or been intentionally paused.

The intended order is:

1. Strict-survivor chapter screen across the seven confirmed books.
2. Summarize strict-survivor chapter candidates.
3. Near-miss rescue chapter screen across the 13 near-miss/control-contaminated
   books.
4. Merge both chapter candidate lists into one `limit 40` confirmation set,
   while preserving labels for strict-survivor vs near-miss origin.

## Recovery Rules

- Launch one batch at a time with the detached batch launcher.
- Wait for a batch to finish before launching the next batch, unless we
  explicitly decide to run in parallel.
- If a batch fails, relaunch only that batch with a fresh prefix or a documented
  rerun suffix.
- Treat all results as passage-rescue leads until confirmed.
