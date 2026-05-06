# ScriptureVec Chapter Drilldown Preliminary Results

Status: preliminary stored result

Last updated: 2026-05-03

## Purpose

This document records the result of the strict-survivor chapter screen for the
rebuilt ScriptureVec Justice paper.

The screen asks:

> After the all-66-book atlas and limit-40 book confirmation identified seven
> book-level Justice sources, which chapters inside those books produce clean
> Justice-moving Scripture vectors?

This is a discovery result, not the final paper result. The candidates below
should be confirmed at a larger benchmark slice before being treated as stable
evidence.

## Input Source Set

The chapter screen was restricted to the seven books that survived book-level
confirmation:

- `1 Chronicles`
- `Amos`
- `Deuteronomy`
- `Judges`
- `Numbers`
- `Acts`
- `Hebrews`

Near-miss books are intentionally held for later. They should remain a separate
rescue/exploratory screen, not part of this strict-survivor result.

## Run Shape

Primary design artifact:

```text
docs/scripturevec_chapter_drilldown_run_design.md
```

Corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_survivor_chapters_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_justice_survivor_chapters_v1_manifest.json
```

Corpus shape:

- chapter targets: `170`
- verse-window rows: `952`
- books: `7`
- chapter window size: `6` verses

Model and benchmark:

- model: `Qwen3-14B`
- virtue: `justice`
- stage: `ratio`
- limit: `10`
- runs: `1`
- temperature: `0.0`
- runtime scripture alpha: `32.0`
- controls: unsteered control, positive Scripture steering,
  negative-alpha Scripture steering, null-control Scripture steering

Operational note:

- `chapter_num_03` repeatedly stalled in early batch-01 attempts.
- The completed screen therefore used `batch01_skip03_v2`, which omits
  Numbers 3 and treats it as a stability diagnostic.

## Artifact Set

The completed per-batch summaries are:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch01_skip03_v2_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch02_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch03_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch04_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch05_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch06_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch07_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch08_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch09_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch10_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch11_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch12_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch13_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch14_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch15_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch16_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch17_v1_summary.md
```

## Decision Rule

A chapter was treated as a clean preliminary hit if positive Scripture steering:

- improved over the unsteered control,
- beat negative-alpha steering,
- beat null-control steering,
- showed paired answer movement in the right direction.

In practice, all clean hits below moved Justice from `0.40` to `0.50` while
the controls did not reproduce the same improvement.

## Clean Preliminary Hits

The strict-survivor chapter screen found `38` clean preliminary Justice hits:

| Book | Clean chapter hits | Count |
| --- | --- | ---: |
| Acts | `1`, `2`, `3`, `4`, `6`, `7`, `8`, `10`, `11`, `14`, `16`, `24`, `27`, `28` | `14` |
| Hebrews | `1`, `2`, `5`, `7`, `9`, `10` | `6` |
| Numbers | `8`, `9`, `11`, `22`, `27`, `31` | `6` |
| 1 Chronicles | `3`, `9`, `13`, `29` | `4` |
| Judges | `7`, `9`, `15` | `3` |
| Amos | `2`, `3`, `7` | `3` |
| Deuteronomy | `9`, `16` | `2` |

## Interpretation

The result does not look like generic Bible text indiscriminately improves
Justice. The chapter-level pattern is much more specific:

- Acts is the strongest source by total number of clean hits.
- Hebrews is especially promising by density, with six clean hits in a short
  book and a strong prior book-level confirmation result.
- Numbers remains important because it produced several clean hits and was
  already a book-level survivor.
- Amos is surprisingly efficient: three hits in a nine-chapter book.
- Deuteronomy is not broadly active, but it contains sharp local pockets.
- Judges and 1 Chronicles provide additional non-prophetic, narrative/historical
  candidates.

The current study shape is therefore:

> A canon-wide search identified book-level Justice sources; chapter drilldown
> inside those sources found a nonrandom-looking set of passage regions whose
> Scripture-derived vectors improve Justice under controls.

## Cautions

This screen used `limit 10`, so it is best understood as a candidate-discovery
step. It is not yet sufficient for a final paper claim.

Some chapters produced movement but were not clean because controls moved too
or because the result looked unstable. These should be treated as diagnostics,
not evidence:

```text
Numbers 19
Numbers 34
Deuteronomy 15
1 Chronicles 6
1 Chronicles 17
1 Chronicles 26
```

Numbers 3 remains a separate stability diagnostic because it repeatedly stalled
the early batch-01 run.

## Immediate Next Step

Keep the near-miss rescue corpus aside for now.

The next mainline step should be a larger confirmation run for the `38` clean
strict-survivor chapter hits, using the same controls and a larger benchmark
slice.

Confirmation design:

```text
docs/scripturevec_chapter_confirmation_run_design.md
```

Only candidates that survive confirmation should move into layer localization
and mechanistic analysis. Passage-window narrowing can be considered later, but
it is not required before locking the chapter-level paper narrative.
