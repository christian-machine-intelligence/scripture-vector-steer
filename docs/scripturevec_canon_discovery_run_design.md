# ScriptureVec Canon Discovery Run Design

Status: sampled canon-division discovery screen complete; Justice candidate
confirmation complete; all-66-book Justice atlas complete; book-candidate
`limit 40` confirmation complete.

## Ambition

The goal is not to narrow the thesis. The goal is to search Scripture broadly
enough to find the biblical sources whose activation vectors generalize.

Working thesis:

> Scripture-derived activation vectors can be systematically discovered across
> the canon, tested for generalization, and then mechanistically analyzed to
> identify activation-level structures that improve virtue-relevant model
> behavior.

The SAE step comes after this discovery and generalization stage. We should
not spend mechanism budget on weak or unstable behavioral effects.

## Why Start With Canon Divisions

A one-shot 66-book by four-virtue by multi-alpha screen is possible in
principle, but it is expensive enough to encourage bad shortcuts. The first
screen should cover all Scripture while keeping the target count manageable.

So the first pass uses ten broad canon-division targets:

| Target | Books |
| --- | --- |
| `canon_torah` | Genesis, Exodus, Leviticus, Numbers, Deuteronomy |
| `canon_history` | Joshua through Esther |
| `canon_wisdom` | Job, Psalms, Proverbs, Ecclesiastes, Song of Solomon |
| `canon_major_prophets` | Isaiah, Jeremiah, Lamentations, Ezekiel, Daniel |
| `canon_minor_prophets` | Hosea through Malachi |
| `canon_gospels` | Matthew, Mark, Luke, John |
| `canon_acts` | Acts |
| `canon_pauline` | Romans through Philemon |
| `canon_general_epistles` | Hebrews, James, 1-2 Peter, 1-3 John, Jude |
| `canon_revelation` | Revelation |

This is still a true canon-wide screen: every KJV chapter belongs to exactly
one target. Hits from this screen become book-level or passage-level follow-ups.

## Corpus Artifact

The external corpus is generated from the bundled KJV file:

```text
data/bible_kjv.json
```

Generator:

```text
scripts/build_canon_discovery_corpus.py
```

Generated artifacts:

```text
results/experiments/scripturevec14/canon_discovery/canon_groups_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_groups_v1_manifest.json
```

Each JSONL row is one chapter chunk with:

- `target` / `corpus`
- source book and chapter
- chapter text

The vector extractor will still re-chunk if needed for model length.

## First Screen

Model:

```text
C:\Users\sethcodex\models\Qwen3-14B
```

Benchmark slice:

```text
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
alpha candidates: 0.5,1.0,2.0,3.0,4.0,6.0,8.0
```

Launcher:

```cmd
scripts\windows\launchers\run_scripturevec_qwen3_14b_canon_groups_ratio_l10.cmd
```

Output prefix:

```text
experiments/scripturevec14/scripturevec14_qwen3_14b_canon_groups_ratio_l10_v2
```

## Batching Adjustment

The first scientifically intended screen remains the same, but operationally
it should run in smaller batches. The ten-target `v2` launch successfully
loaded Qwen3-14B in 4-bit mode, then became stale during vector extraction
before writing vector diagnostics. The likely issue is the amount of activation
extraction requested at once, not the model or corpus definition.

The recovery design keeps all ten canon divisions but runs them as five smaller
batches:

| Batch | Targets | Prefix |
| --- | --- | --- |
| 01 | `canon_torah`, `canon_history` | `scripturevec14_qwen3_14b_canon_groups_batch01_ratio_l10_v1` |
| 02 | `canon_wisdom`, `canon_major_prophets` | `scripturevec14_qwen3_14b_canon_groups_batch02_ratio_l10_v1` |
| 03 | `canon_minor_prophets`, `canon_gospels` | `scripturevec14_qwen3_14b_canon_groups_batch03_ratio_l10_v1` |
| 04 | `canon_acts`, `canon_pauline` | `scripturevec14_qwen3_14b_canon_groups_batch04_ratio_l10_v1` |
| 05 | `canon_general_epistles`, `canon_revelation` | `scripturevec14_qwen3_14b_canon_groups_batch05_ratio_l10_v1` |

This still covers every KJV chapter exactly once at the corpus-design level.
The batches only reduce how many activation vectors are extracted in a single
GPU job.

If even two large divisions are too heavy, use the sampled canon-division
screen:

```text
results/experiments/scripturevec14/canon_discovery/canon_groups_sample32_v1.jsonl
```

This samples up to 32 chapters per canon division, spread deterministically
across the division. It is the correct discovery-screen fallback: it can find
candidate canon regions while keeping full-corpus extraction for confirmation
rather than initial search.

## Decision Rules

A first-pass candidate is interesting if positive steering:

- improves over control,
- beats negative-alpha steering,
- beats null-control steering,
- has paired answer movement in the right direction.

But this first screen is only discovery. A candidate becomes a serious
behavioral result only if it survives larger and stricter follow-up.

## Follow-Up Ladder

1. Canon-division screen at tuned alpha.
2. High-alpha replay for promising virtues or source families, reusing frozen
   vectors.
3. Book-level drilldown inside winning canon divisions.
4. Passage or chapter-window drilldown inside winning books.
5. Locked `limit 40` confirmation with no further tuning.
6. SAE/mechanistic analysis on the strongest confirmed vector.

## Recovery Rules

- Do not overwrite this prefix; create a `v2` prefix if rerunning the design.
- If launch fails before artifacts are written, inspect wrapper log and status
  before relaunch.
- If a single alpha or batch fails later, relaunch only that batch with a fresh
  prefix.
- Treat ratio-stage hits as leads, not final paper claims.

## Launch Notes

- `v1` failed during model loading because the new background wrapper launch
  did not set the 4-bit Qwen loading environment used by the earlier Qwen3-14B
  launchers. This is an operational failure, not a scientific result.
- `v2` preserves the same scientific design and adds the required 4-bit GPU
  environment before invoking the background wrapper.
- The ten-target `v2` launch loaded the model but did not survive vector
  extraction. Continue with the five-batch design above.
- Batch 01 also became stale during vector extraction, so the next operational
  fallback is the `sample32` canon-division screen.
- The `sample32` ten-target detached run succeeded at vector extraction, but
  the all-in-one preflight/scoring grid became stale after its first probe.
  Narrow synchronous diagnostics showed that positive steering and null-control
  scoring both work when isolated.
- The stable run shape is now one virtue at a time, reusing the frozen
  `sample32` vector artifact, with preflight disabled for discovery and
  positive, negative-alpha, and null controls kept in the benchmark stage.

## First Sample32 Alpha-32 Results

Completed one-virtue screens:

```text
scripturevec14_qwen3_14b_canon_sample32_justice_a32_ratio_l10_v1
scripturevec14_qwen3_14b_canon_sample32_courage_a32_ratio_l10_v1
scripturevec14_qwen3_14b_canon_sample32_temperance_a32_ratio_l10_v1
scripturevec14_qwen3_14b_canon_sample32_prudence_a32_ratio_l10_v1
```

Summary artifact:

```text
results/experiments/scripturevec14/canon_discovery/canon_sample32_a32_four_virtue_summary.md
```

The first useful leads are Justice-specific. At `limit 10` and fixed runtime
alpha `32`, four canon divisions improved Justice from `0.40` to `0.50` while
their negative-alpha and null-control lanes did not match the positive
improvement:

- `canon_acts`
- `canon_gospels`
- `canon_minor_prophets`
- `canon_revelation`

Courage, Temperance, and Prudence had no positive candidate rows in this
screen. Prudence appears ceilinged at `0.90` control accuracy for this
`limit 10` slice.

Next confirmation step:

```text
scripturevec14_qwen3_14b_canon_sample32_justice_candidates_a32_ratio_l40_v1
```

This expands only the four Justice candidate divisions to `limit 40`, keeping
the same positive, negative-alpha, and null-control comparison.

## Justice Candidate Confirmation

The `limit 40` Justice candidate confirmation narrowed the lead set:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_canon_sample32_justice_candidates_a32_ratio_l40_v1_summary.md
```

Surviving candidate rows:

| Target | Control | Positive | Negative | Null | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| `canon_acts` | `0.40` | `0.42` | `0.40` | `0.35` | weakly survives |
| `canon_minor_prophets` | `0.40` | `0.42` | `0.40` | `0.40` | weakly survives |

`canon_gospels` and `canon_revelation` did not survive the larger slice: their
positive lanes matched control, and their null controls reached `0.42`.

The next step is therefore:

1. Treat Acts as a weakly surviving one-book lead for later chapter/passage
   drilldown.
2. Split Minor Prophets into book-level targets before spending mechanism
   budget.

Book-level corpus artifact:

```text
results/experiments/scripturevec14/canon_discovery/canon_books_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_books_v1_manifest.json
```

Minor Prophets book-level launcher:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_minor_prophets_books_justice_a32_ratio_l10.cmd
```

All-66-book Justice atlas launcher:

```text
scripts/windows/launchers/run_scripturevec_qwen3_14b_books_justice_a32_ratio_l10_batch.cmd
```

This is the thorough book-level search. It runs Justice only, in six canonical
batches of eleven books each, using the `canon_books_v1.jsonl` corpus and the
same positive, negative-alpha, and null-control design.

The all-66-book `limit 10` atlas completed and found 19 preliminary
book-level Justice candidates:

```text
results/experiments/scripturevec14/canon_discovery/canon_books_justice_a32_l10_atlas_summary.md
```

The next filter was `limit 40` confirmation for those 19 candidates in two
smaller batches.

## All-Book Justice Candidate Confirmation

Confirmation artifact:

```text
results/experiments/scripturevec14/canon_discovery/canon_books_justice_a32_l40_candidate_confirmation_summary.md
```

The stricter `limit 40` candidate confirmation narrowed the 19 preliminary
book-level Justice candidates to seven clean survivors:

| Book target | Control | Positive | Negative | Null | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| `book_1ch` | `0.40` | `0.42` | `0.38` | `0.35` | survives |
| `book_amo` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_deu` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_jdg` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_num` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_act` | `0.40` | `0.42` | `0.40` | `0.40` | survives |
| `book_heb` | `0.40` | `0.45` | `0.40` | `0.40` | strongest survivor |

Hebrews is the strongest book-level candidate so far. It moved two items in
the right direction on the `limit 40` slice while both controls stayed flat.

The next research step is chapter or passage-window drilldown inside these
seven surviving books. Only after stable chapters/passages survive confirmation
should we spend time on layer localization and SAE analysis.
