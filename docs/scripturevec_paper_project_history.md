# ScriptureVec Paper Project History

Status: draft paper-facing history

Last updated: 2026-05-03

## Purpose

This document records the usable history of the rebuilt ScriptureVec paper.

It is not a complete lab notebook. Much of the work before this point was
exploratory: model-fit checks, runner recovery, early corpus trials, broad
virtue probes, and debugging of the remote GPU workflow. That exploratory work
was necessary, but it should not be presented as the formal study sequence in
the paper.

The paper-facing history begins with the first deliberate discovery step after
the project had a stable research shape:

> a canon-wide, all-66-book search for Scripture-derived Justice vectors.

## Paper-Facing Framing

The rebuilt paper should describe the project as a controlled discovery study.
The central ambition is not merely to show that one hand-picked passage can move
one benchmark item. The ambition is to show that Scripture-derived activation
vectors can be searched for systematically, filtered by controls, and then
taken forward into passage-level and mechanistic analysis.

Working thesis:

> Scripture-derived activation vectors can be systematically discovered across
> the canon, tested for generalization, and then mechanistically analyzed to
> identify activation-level structures that improve virtue-relevant model
> behavior.

For the first proof-of-concept paper, Justice is the current behavioral target.
This is not because the broader theological ambition was abandoned. It is
because Justice produced the clearest live path for a controlled discovery
pipeline: canon-wide search, candidate filtering, passage drilldown, layer
localization, and later SAE analysis.

## What We Do Not Include As Formal Study History

The paper should not begin with the earlier exploratory phase.

That phase included:

- deciding whether the first manuscript should be restarted from first
  principles,
- checking larger Qwen model feasibility on the available GPU setup,
- testing whether the existing steering runner could load larger models,
- moving from larger-model ambition back to the stable Qwen3-14B runner,
- trying broad virtue screens and high-alpha steering to learn which behavioral
  lanes were alive,
- discovering that Courage, Temperance, and Prudence were not giving the same
  kind of usable proof-of-concept path in the current benchmark slice.

Those choices can be mentioned briefly in Methods or Limitations if needed.
They should not be narrated as if they were confirmatory evidence.

The clean paper story starts after that exploratory work produced a stable
question:

> Can we search the biblical canon itself for the book-level sources whose
> activation vectors move Justice on VirtueBench 2 under controls?

## Step 1: Canon-Wide Book-Level Justice Atlas

Date completed: 2026-05-03

Primary artifact:

```text
results/experiments/scripturevec14/canon_discovery/canon_books_justice_a32_l10_atlas_summary.md
```

Model:

```text
Qwen3-14B
```

Corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_books_v1.jsonl
```

The corpus represented all 66 biblical books. Each target was a book-level
Scripture source, generated from the bundled KJV corpus.

Benchmark shape:

- virtue: `justice`
- stage: `ratio`
- limit: `10`
- runs: `1`
- temperature: `0.0`
- runtime scripture alpha: `32.0`
- controls: positive Scripture, negative-alpha Scripture, null Scripture
- batches: six canonical batches covering all 66 books

### Why This Was The First Paper-Facing Step

Earlier work had suggested that some Scripture-derived vectors could move
Justice, especially around Acts and the Minor Prophets. But a paper cannot rest
on picking plausible biblical regions after the fact.

The all-66-book atlas made the discovery step systematic. Every biblical book
was allowed to compete as a candidate source. This matters because it prevents
the study from quietly becoming a hand-picked passage demonstration.

### Discovery Rule

A book was treated as a preliminary candidate if positive Scripture steering:

- improved over the unsteered control,
- beat negative-alpha steering,
- beat null-control steering.

This was only a discovery filter, not a final claim.

### Discovery Result

The all-book atlas found 19 preliminary book-level Justice candidates:

```text
book_deu
book_num
book_jdg
book_1sa
book_2ki
book_1ch
book_neh
book_sng
book_amo
book_hos
book_lam
book_act
book_hab
book_jhn
book_luk
book_mrk
book_nam
book_heb
book_rev
```

This was a useful result, but still too permissive. The next step was to test
whether these candidates survived a larger benchmark slice.

## Step 2: Limit-40 Candidate Confirmation

Date completed: 2026-05-03

Primary artifact:

```text
results/experiments/scripturevec14/canon_discovery/canon_books_justice_a32_l40_candidate_confirmation_summary.md
```

Confirmation artifacts:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_books_justice_candidates_a32_ratio_l40_batch01_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_books_justice_candidates_a32_ratio_l40_batch02_v1_summary.md
```

Benchmark shape:

- virtue: `justice`
- stage: `ratio`
- limit: `40`
- runs: `1`
- temperature: `0.0`
- runtime scripture alpha: `32.0`
- candidates tested: 19 preliminary candidates from Step 1
- controls: positive Scripture, negative-alpha Scripture, null Scripture

### Confirmation Rule

A candidate survived only if positive Scripture steering:

- improved over control,
- beat negative-alpha steering,
- beat null-control steering.

This filter is deliberately stricter than theological plausibility. A book does
not count as a serious source merely because it seems morally or biblically
relevant.

### Confirmation Result

Seven book-level Justice candidates survived:

| Book target | Control | Positive | Negative | Null | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| `book_1ch` | `0.40` | `0.42` | `0.38` | `0.35` | survives |
| `book_amo` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_deu` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_jdg` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_num` | `0.40` | `0.42` | `0.40` | `0.38` | survives |
| `book_act` | `0.40` | `0.42` | `0.40` | `0.40` | survives |
| `book_heb` | `0.40` | `0.45` | `0.40` | `0.40` | strongest survivor |

Hebrews is the strongest current book-level candidate. It improved from `0.40`
to `0.45`, while both controls stayed at `0.40`.

The other six survivors are smaller but cleaner. Each improved one item over
control, and the controls did not reproduce the same improvement.

### Important Negative Results

Twelve preliminary candidates did not survive the stricter confirmation step:

```text
book_1sa
book_2ki
book_hos
book_neh
book_sng
book_hab
book_jhn
book_lam
book_luk
book_mrk
book_nam
book_rev
```

These failures are useful. They show that the method is not simply blessing
every plausible biblical book as a Justice source. Some candidates disappeared,
some moved only under controls, and some worsened under positive steering.

## Current Interpretation

The paper should say that the canon-wide discovery pipeline has produced a
small but real set of book-level Justice leads.

The right claim is not:

> Scripture generally and strongly improves Justice.

The stronger and more accurate claim is:

> A canon-wide search identified a small set of Scripture-derived book vectors
> that produce control-sensitive Justice improvements on Qwen3-14B, with Hebrews
> currently the strongest book-level candidate.

This is exactly the sort of result that can justify passage-level and
mechanistic follow-up. It is not yet the final paper result.

## Step 3: Strict-Survivor Chapter Drilldown

Date completed: 2026-05-03

Primary result artifact:

```text
docs/scripturevec_chapter_drilldown_preliminary_results.md
```

Primary design artifact:

```text
docs/scripturevec_chapter_drilldown_run_design.md
```

Corpus:

```text
results/experiments/scripturevec14/canon_discovery/canon_justice_survivor_chapters_v1.jsonl
results/experiments/scripturevec14/canon_discovery/canon_justice_survivor_chapters_v1_manifest.json
```

The chapter drilldown localized the seven surviving book-level sources into
chapter-level candidates. It tested 170 chapter targets across:

- `1 Chronicles`
- `Amos`
- `Deuteronomy`
- `Judges`
- `Numbers`
- `Acts`
- `Hebrews`

Benchmark shape:

- virtue: `justice`
- stage: `ratio`
- limit: `10`
- runs: `1`
- temperature: `0.0`
- runtime scripture alpha: `32.0`
- controls: positive Scripture, negative-alpha Scripture, null Scripture

Operational note:

- `chapter_num_03` repeatedly stalled early batch-01 attempts.
- The completed screen therefore used `batch01_skip03_v2`, with Numbers 3 held
  out as a stability diagnostic.

### Chapter Discovery Result

The strict-survivor chapter screen found 38 clean preliminary Justice hits:

| Book | Clean chapter hits | Count |
| --- | --- | ---: |
| Acts | `1`, `2`, `3`, `4`, `6`, `7`, `8`, `10`, `11`, `14`, `16`, `24`, `27`, `28` | `14` |
| Hebrews | `1`, `2`, `5`, `7`, `9`, `10` | `6` |
| Numbers | `8`, `9`, `11`, `22`, `27`, `31` | `6` |
| 1 Chronicles | `3`, `9`, `13`, `29` | `4` |
| Judges | `7`, `9`, `15` | `3` |
| Amos | `2`, `3`, `7` | `3` |
| Deuteronomy | `9`, `16` | `2` |

Every clean hit improved Justice from `0.40` to `0.50` under positive Scripture
steering, while the negative-alpha and null controls did not reproduce the same
improvement.

### Current Interpretation

The chapter screen strengthens the project because it moves the evidence from
whole-book discovery into localized biblical sources. The result does not look
like generic Scripture text indiscriminately improves Justice. It looks like
specific chapter regions inside the confirmed books produce vectors that
generalize to Justice behavior under controls.

The strongest current chapter families are:

- Acts, by total number of clean hits,
- Hebrews, by density and prior book-level strength,
- Numbers, by repeated clean hits across several parts of the book,
- Amos, by surprising density in a short prophetic book.

This remains a discovery result. These chapters should be confirmed at a larger
benchmark slice before becoming final paper-facing evidence.

## Next Paper-Facing Step

The next formal mainline step should be larger-slice confirmation of the 38
strict-survivor chapter hits from Step 3.

Confirmation design:

```text
docs/scripturevec_chapter_confirmation_run_design.md
```

The near-miss rescue screen should be held for later rather than mixed into the
mainline evidence path right now.

## Earlier Planned Chapter Drilldown

This plan has now been completed by Step 3. The original planned source set was:

- `1 Chronicles`
- `Amos`
- `Deuteronomy`
- `Judges`
- `Numbers`
- `Acts`
- `Hebrews`

The drilldown should keep the same basic controls:

- unsteered control,
- positive Scripture steering,
- negative-alpha steering,
- null-control steering.

The purpose of that step is to answer:

> Which chapters or passage windows produce the most stable Justice vector?

Only after passage-level candidates survive this filter should the project move
to layer localization and SAE analysis.

## Deferred Step: Near-Miss Rescue Screen

The near-miss rescue screen remains valuable, but it is now deferred. The
strict-survivor chapter screen produced enough promising material to continue
the mainline study without mixing in weaker book-level sources yet.

Primary design artifact:

```text
docs/scripturevec_near_miss_rescue_run_design.md
```

This screen tests books that showed some book-level movement but did not pass
the stricter whole-book confirmation. The rationale is that a whole-book vector
can be too broad: a book may contain a strong Justice-relevant passage while
the book-level corpus also contains genre, narrative, rhetoric, or doctrinal
material that washes out the effect.

The source set includes the 12 failed preliminary candidates plus 2 Corinthians,
which moved under positive steering but was control-contaminated at book level:

```text
1 Samuel
2 Kings
Hosea
Nehemiah
Song of Solomon
Habakkuk
John
Lamentations
Luke
Mark
Nahum
Revelation
2 Corinthians
```

This screen should not blur the main result. Chapters from near-miss books are
rescue leads, not confirmed paper evidence, unless they later survive locked
`limit 40` confirmation.

## Candidate Paper Prose

The formal study began with a canon-wide discovery screen rather than a
hand-selected proof text. We generated book-level Scripture corpora for all 66
books of the biblical canon and extracted activation directions from each book
against a shared non-scriptural contrast corpus. Each book-derived direction was
then tested on the Justice subset of VirtueBench 2 under positive steering,
negative-alpha steering, and a null-control direction.

This first atlas produced 19 preliminary book-level candidates at a small
benchmark slice. We then subjected those candidates to a larger confirmation
slice. Seven books survived the stricter filter: 1 Chronicles, Amos,
Deuteronomy, Judges, Numbers, Acts, and Hebrews. Hebrews was the strongest
survivor, improving Justice accuracy from 0.40 to 0.45 while both control
conditions remained at 0.40.

We treat these book-level survivors not as final evidence that Scripture
generally improves Justice, but as the output of a controlled discovery step.
They define the source set for the next stage of the study: chapter- and
passage-level localization followed by layer-level and mechanistic analysis.
