# ScriptureVec General Biblical Comparison

Status: completed Qwen3-14B ratio-stage comparison plus Justice high-alpha
follow-up.

## Purpose

Compare the current virtue-specific Scripture vectors against broader biblical
vectors that are not organized around Prudence, Justice, Fortitude, or
Temperance.

This asks:

> Are the useful effects coming from virtue-specific passage selection, or from
> a broader biblical register that can be extracted from whole biblical families
> and books?

## General Biblical Targets

The runner already supports these broad Scripture targets:

```text
psalms
proverbs
gospels
romans
petrine
```

These are not the Lex Cardinal Virtue Geometry targets. They are general
Bible-family or book-level vectors.

## Run Design

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
scripts\windows\launchers\run_scripturevec_qwen3_14b_general_biblical_ratio_l10.cmd
```

Output prefix:

```text
experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1
```

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1.status
```

## Comparison Standard

This comparison is promising if one or more general biblical vectors:

- improves a virtue score over control,
- beats its own negative-alpha lane,
- beats its own null-control lane,
- produces item-level answer movement that is virtue-relevant rather than only
  biblical style or formatting drift.

Most important comparison points:

- Justice/`justice_scripture` high-alpha window on Qwen3-14B.
- Courage/`fortitude_scripture` clean `limit 40` result on Qwen3.5-9B.
- Pooled Cardinal Virtue ScriptureVec, which was mostly flat or mixed.

## Expected Read

If general biblical vectors work as well as virtue-specific vectors, the thesis
can become broader: Scripture-derived directions may carry general moral
structure that transfers across virtue categories.

If only the virtue-specific vectors work, then the thesis becomes sharper:
Scripture steering is not just generic biblical register; careful passage
selection matters.

## Tuned-Alpha Result

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1.status
FINISHED
```

Summary artifacts:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1_summary.json
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1_vector_diagnostics.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1_vector_diagnostics.json
```

All five broad biblical vectors separated their biblical target from background
text in diagnostics:

| Target | Best layer | Tuned alpha | Dev accuracy | Test accuracy | Steered test margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| Psalms | 29 | 8.0 | 1.0 | 1.0 | 0.8833 |
| Proverbs | 29 | 8.0 | 1.0 | 1.0 | 0.8753 |
| Gospels | 31 | 8.0 | 1.0 | 0.9828 | 0.8444 |
| Romans | 31 | 8.0 | 1.0 | 1.0 | 0.8874 |
| Petrine | 31 | 8.0 | 1.0 | 1.0 | 0.8899 |

But the tuned-alpha scored ratio screen was completely flat:

```text
20 target x virtue rows
0 candidate rescue rows
0 answer changes under positive, negative, or null steering
```

That means broad biblical vectors are extractable on Qwen3-14B, but at tuned
alpha `8.0` they do not move the ratio-stage VirtueBench choices at all.

## Justice High-Alpha Follow-Up

Because Qwen3-14B Justice only showed a positive effect under high runtime
alpha for the virtue-specific `justice_scripture` vector, the fair comparison
is a Justice-only high-alpha sweep using the broad biblical vectors.

Launcher:

```cmd
scripts\windows\launchers\run_scripturevec_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10.cmd
```

Design:

- Reuse the general-biblical vector artifact.
- Evaluate only Justice.
- Compare `psalms`, `proverbs`, `gospels`, `romans`, and `petrine`.
- Runtime alpha ladder: `32`, `48`, `64`, `96`.
- Keep severe controls: positive, negative-alpha, and null steering.

Decision rule:

- If a broad biblical target reproduces the Justice high-alpha gain, the effect
  may reflect general biblical moral structure.
- If the broad biblical targets remain flat while `justice_scripture` works,
  then the evidence favors virtue-specific passage selection.

## Justice High-Alpha Result

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10_v1.status
FINISHED
```

Summary artifacts:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10_a032_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10_a048_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10_a064_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_justice_alpha_sweep_ratio_l10_a096_v1_summary.md
```

Clean broad-vector Justice candidates:

| Runtime alpha | Broad target(s) | Control | Positive | Negative alpha | Null | Positive paired movement |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 32 | Gospels | 0.40 | 0.50 | 0.40 | 0.40 | 1 answer change / +1 net |
| 48 | Proverbs | 0.40 | 0.50 | 0.40 | 0.40 | 3 answer changes / +1 net |
| 64 | Petrine | 0.40 | 0.50 | 0.40 | 0.40 | 1 answer change / +1 net |
| 64 | Proverbs | 0.40 | 0.50 | 0.40 | 0.40 | 3 answer changes / +1 net |
| 96 | Gospels | 0.40 | 0.50 | 0.40 | 0.40 | 3 answer changes / +1 net |
| 96 | Romans | 0.40 | 0.50 | 0.40 | 0.40 | 3 answer changes / +1 net |

Important non-clean signs:

- At alpha `64`, Psalms regressed from `0.40` to `0.30`.
- At alpha `96`, Proverbs also reached `0.50`, but the negative-alpha lane
  also reached `0.50`, so that is not a clean positive steering sign.
- At alpha `96`, Psalms improved only under negative-alpha steering, not under
  positive steering.
- At alpha `96`, Petrine regressed from `0.40` to `0.30`.

## Comparison To Virtue-Specific Justice

The virtue-specific `justice_scripture` Qwen3-14B high-alpha sweep previously
found the same headline-sized Justice gain:

| Runtime alpha | Control | Positive `justice_scripture` | Negative alpha | Null |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 0.40 | 0.50 | 0.40 | 0.30 |
| 48 | 0.40 | 0.50 | 0.40 | 0.30 |
| 64 | 0.40 | 0.50 | 0.40 | 0.30 |
| 96 | 0.40 | 0.50 | 0.40 | 0.40 |

The broad biblical comparison changes the interpretation:

- The Justice effect is not exclusive to the curated `justice_scripture`
  passage set.
- General biblical vectors can also produce the `0.40 -> 0.50` Justice gain,
  but only under heavy runtime alpha.
- The virtue-specific Justice vector is cleaner as an instrument because the
  gain appears at every tested high-alpha point from `32` through `96`.
- The broad biblical vectors are more unstable: the winning source shifts by
  alpha, and some broad sources produce negative-alpha or regressive movement.

## Courage High-Alpha Result

Because broad biblical vectors reproduced the Justice high-alpha gain, the
next check was whether the same broad biblical targets also rescue Courage.
This matters because Courage/Fortitude was the cleanest Qwen3.5-9B lead, while
Qwen3-14B `fortitude_scripture` had stayed flat or regressed at high alpha.

Launcher:

```cmd
scripts\windows\launchers\run_scripturevec_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10.cmd
```

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_v1.status
FINISHED
```

Summary artifacts:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_a032_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_a048_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_a064_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_a096_v1_summary.md
```

Result:

```text
0 candidate rescue rows
```

Positive steering summary:

| Runtime alpha | Psalms | Proverbs | Gospels | Romans | Petrine |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 0.40 | 0.40 | 0.40 | 0.40 | 0.30 |
| 48 | 0.40 | 0.30 | 0.30 | 0.30 | 0.40 |
| 64 | 0.20 | 0.30 | 0.30 | 0.30 | 0.30 |
| 96 | 0.20 | 0.30 | 0.30 | 0.30 | 0.30 |

Control was `0.40` in every alpha cell.

Interpretation:

- Broad biblical vectors did not improve Courage at any high-alpha setting.
- At alpha `32`, most targets were flat, while Petrine regressed.
- At alpha `48`, Gospels, Proverbs, and Romans regressed.
- At alpha `64` and `96`, every positive broad biblical lane regressed.
- Psalms was most destructive at high alpha, falling from `0.40` to `0.20`.

This is an important contrast with Justice. The broad biblical result is not a
generic "high alpha makes the model more virtuous" effect. It appears
virtue-sensitive: Justice can be rescued by some broad biblical directions,
but Courage is flat or harmed on Qwen3-14B in this screen.

## Current Read

The strongest fair claim is now broader and more ambitious than a
prudence-specific story, but narrower than a generic "biblical vectors improve
all virtues" story:

> On Qwen3-14B, broad biblical directions are internally legible and can carry
> enough moral structure to reproduce a Justice improvement under high steering
> strength. The effect is virtue-sensitive rather than uniform: the same broad
> biblical directions do not rescue Courage and become destructive at higher
> alpha.

This is a better result for the larger project than a simple "only
virtue-specific passages work" outcome. It suggests that the model contains
more than one usable biblical moral direction: a general biblical register and
more targeted virtue-shaped directions may both be behaviorally active, but
with different precision and different virtue-specific failure modes.

The next evidence-building step should be a larger Justice comparison that
puts `justice_scripture`, Gospels, Proverbs, Romans, and possibly Petrine in
the same `limit 40` screen using their clean high-alpha windows.
