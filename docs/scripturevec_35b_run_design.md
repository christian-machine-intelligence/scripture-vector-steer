# ScriptureVec 35B Run Design

Status: implementation started; first pilot should use the Lex frozen corpus.
The 35B MoE run remains the target claim, but the first dinner-run contingency
is a matching Qwen3.5-9B pilot when the 35B checkpoint cannot fit cleanly on the
available Windows GPUs.

## Purpose

Test the ambitious ScriptureVec claim on `Qwen/Qwen3.5-35B-A3B`:

> Steering Qwen3.5-35B with a vector derived from Scripture, relative to
> length-matched neutral prose, improves VirtueBench 2 performance compared
> with no steering and neutral-prose steering.

The run should stay ambitious, but the evidence must pass through strict
controls.

## Corpus Source

Use the Cardinal Virtue Geometry frozen v1 corpus as the Scripture source:

```text
$LEX_ET_IUSTITIA/subprojects/cardinal-virtue-geometry/data/generated/frozen_v1/selected_balanced_corpus.jsonl
```

That file remains owned by the separate `lex-et-iustitia` project and is not
bundled here; set `$LEX_ET_IUSTITIA` to your local checkout of it. VirtueBench 2
consumes the file as an external corpus. This run is background material for the
project history and is not part of the Qwen3-14B paper pipeline.

When this file is loaded, the runner now synthesizes a pooled target:

```text
scripturevec_pooled
```

This pooled target contains all frozen Prudence, Justice, Fortitude, and
Temperance scripture chunks. The original targets remain available for later
virtue-specific and SAE analyses:

- `prudence_scripture`
- `justice_scripture`
- `fortitude_scripture`
- `temperance_scripture`

## First Pilot

Run the pooled target first, on the ratio slice, before any full run:

```bash
PYTHONPATH=src python -m virtue_bench.cli iconoclast \
  --model Qwen/Qwen3.5-35B-A3B \
  --stage ratio \
  --runs 1 \
  --limit 10 \
  --temperature 0.0 \
  --seed 42 \
  --condition-profile scripturevec35 \
  --scripture-targets scripturevec_pooled \
  --external-scripture-corpus $LEX_ET_IUSTITIA/subprojects/cardinal-virtue-geometry/data/generated/frozen_v1/selected_balanced_corpus.jsonl \
  --extraction-method scripture_contrast \
  --alpha-candidates 0.5,1.0,2.0,3.0,4.0,6.0,8.0 \
  --preflight-policy warn \
  --output-prefix experiments/scripturevec35/qwen35_pooled_ratio_l10_v1
```

If the 35B MoE checkpoint cannot be loaded on the available GPUs, keep the same
run design and controls but switch only the model and output prefix:

```bash
PYTHONPATH=src python -m virtue_bench.cli iconoclast \
  --model Qwen/Qwen3.5-9B \
  --stage ratio \
  --runs 1 \
  --limit 10 \
  --temperature 0.0 \
  --seed 42 \
  --condition-profile scripturevec35 \
  --scripture-targets scripturevec_pooled \
  --external-scripture-corpus $LEX_ET_IUSTITIA/subprojects/cardinal-virtue-geometry/data/generated/frozen_v1/selected_balanced_corpus.jsonl \
  --extraction-method scripture_contrast \
  --alpha-candidates 0.5,1.0,2.0,3.0,4.0,6.0,8.0 \
  --preflight-policy warn \
  --output-prefix experiments/scripturevec35/qwen35_9b_pooled_ratio_l10_v1
```

This contingency does not replace the ambitious 35B claim; it tells us whether
the pooled ScriptureVec design is alive before spending more engineering effort
on 35B placement or a quantized 35B checkpoint.

The `scripturevec35` condition profile runs:

- `control`
- `scripture_steer`
- `scripture_negative_alpha`
- `scripture_null_control`

For a mean-difference ScriptureVec, `scripture_negative_alpha` is the
neutral-prose side of the same contrast. It should be interpreted as a
directionality and neutral-side control, not as a theological "anti-Scripture"
condition.

## Success Standard

The pooled pilot is promising if:

- `scripture_steer:scripturevec_pooled` beats `control`.
- It beats `scripture_negative_alpha:scripturevec_pooled`.
- It beats `scripture_null_control:scripturevec_pooled`.
- Refusals, answer length, and religious-language drift do not explain the gain.
- The preflight shows that the steering hook changes answer-level behavior.

## Next Step After Pilot

If the pooled pilot moves behavior, run a broader response curve by repeating
the ratio slice with frozen vectors and separate alpha scales. Only after that
should we spend budget on the locked full-stage run.

If the pooled pilot is mixed, do not weaken the main hypothesis immediately.
Move to the four Lex targets and test whether virtue-specific ScriptureVec
targets are cleaner than the pooled vector.

For the Qwen3.5-9B contingency, that follow-up keeps the same ratio slice and
uses:

```text
prudence_scripture,justice_scripture,fortitude_scripture,temperance_scripture
```

with output prefix:

```text
experiments/scripturevec35/scripturevec35_qwen35_9b_targets_ratio_l10_v1
```

## Matched 9B Follow-Up

The pooled run was mixed, and the target-specific run produced one clean
Courage signal. The next run therefore expands the matched target check from
`limit 10` to `limit 40`, reusing the target vectors from:

```text
results/experiments/scripturevec35/scripturevec35_qwen35_9b_targets_ratio_l10_v1_vectors.pt
```

The matched pairs are:

- Prudence evaluation with `prudence_scripture`
- Justice evaluation with `justice_scripture`
- Courage evaluation with `fortitude_scripture`
- Temperance evaluation with `temperance_scripture`

Use fixed runtime alpha `8.0`, because the pilot selected alpha `8.0` across the
target-specific vectors. Keep the severe control family:

- `control`
- `scripture_steer`
- `scripture_negative_alpha`
- `scripture_null_control`

This run is still a screen, not the paper's final evidence. Its job is to tell
us whether the Courage movement is broader than `COU-001` and whether any other
matched virtue-specific effect emerges when the sample is expanded.
