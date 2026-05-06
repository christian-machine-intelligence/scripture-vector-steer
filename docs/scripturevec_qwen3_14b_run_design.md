# ScriptureVec Qwen3 14B Run Design

Status: completed first pooled ratio pilot after 30B-A3B MoE and 32B dense load
probes failed.

## Purpose

Run the same ScriptureVec pooled pilot on:

```text
Qwen/Qwen3-14B
```

On the Windows runner this is mirrored locally before use:

```text
C:\Users\sethcodex\models\Qwen3-14B
```

This is less ambitious than the 30B and 32B attempts, but it keeps the study on
a Qwen3 dense model that should fit the current GPU setup without CPU/disk
spillover.

## Load Probe Result

`Qwen/Qwen3-14B` was mirrored to:

```text
C:\Users\sethcodex\models\Qwen3-14B
```

The load-only probe succeeded in 4-bit on `cuda:0`:

```text
LOADED_QWEN3_14B Qwen3ForCausalLM
```

## Why This Model

The project goal is still to test an ambitious model scale, because prior ICMI
work suggests Christian activation may increase with model size. The larger
Qwen candidates were therefore tried first:

- Qwen3 30B-A3B normal 4-bit loading failed GPU placement.
- Qwen3 30B-A3B AWQ was blocked by the Windows AWQ loader stack.
- Qwen3 30B-A3B FP8 reached placement but still required CPU/disk spillover.
- Qwen3 32B dense 4-bit also required CPU/disk spillover.

`Qwen/Qwen3-14B` is the next Qwen3 dense candidate that should run cleanly while
preserving the same ScriptureVec design.

## GPU Placement

Use the 4090 as the main device:

```text
VIRTUE_BENCH_CUDA_DEVICE=cuda:0
VIRTUE_BENCH_HF_LOAD_IN_4BIT=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

The model should fit on the 4090 in 4-bit. If it does not, retry with automatic
placement across the 4090 and 3070 before abandoning the run.

## Corpus Source

Use the Cardinal Virtue Geometry frozen v1 corpus owned by `lex-et-iustitia`:

```text
C:\Users\sethcodex\work\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl
```

VirtueBench 2 consumes it as an external corpus and synthesizes:

```text
scripturevec_pooled
```

## First Run

Run the pooled target first on the ratio slice:

```cmd
scripts\windows\launchers\run_scripturevec_qwen3_14b_pooled_ratio_l10.cmd
```

That launcher runs:

```text
model: C:\Users\sethcodex\models\Qwen3-14B
stage: ratio
runs: 1
limit: 10
temperature: 0.0
seed: 42
condition profile: scripturevec35
target: scripturevec_pooled
extraction method: scripture_contrast
alpha candidates: 0.5,1.0,2.0,3.0,4.0,6.0,8.0
preflight policy: warn
output prefix: experiments/scripturevec14/scripturevec14_qwen3_14b_pooled_ratio_l10_v1
```

The condition profile name is still `scripturevec35` because that existing
profile means "ScriptureVec severe controls"; it is not intended to claim that
the model is 35B.

## Artifacts

Expected remote outputs:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_pooled_ratio_l10_v1.status
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_wrapper_console.log
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_*
```

## Success Standard

The Qwen3 14B pooled pilot is promising if:

- `scripture_steer:scripturevec_pooled` beats `control`.
- It beats `scripture_negative_alpha:scripturevec_pooled`.
- It beats `scripture_null_control:scripturevec_pooled`.
- Refusals, answer length, and religious-language drift do not explain the gain.
- The preflight shows that the steering hook changes answer-level behavior.

## Recovery Rules

- If the model-ID load path fails, mirror the model locally and run from the
  local path.
- If single-GPU placement fails, retry automatic placement across both GPUs.
- If Qwen3 14B still spills to CPU/disk, stop and reassess the GPU setup rather
  than changing the evaluation design.

## First Run Result

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_pooled_ratio_l10_v1.status
FINISHED
```

Generated artifacts:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_vectors.pt
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_vector_diagnostics.json
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_preflight.json
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_ratio.json
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_pooled_ratio_l10_v1_ratio_logs.json
```

Vector diagnostics were strong as a separation test:

```text
best layer: 31
layer window: [28, 29, 30, 31, 32, 33, 34]
tuned alpha: 8.0
dev accuracy / margin: 1.0 / 0.6884
test accuracy / steered test accuracy: 1.0 / 1.0
steered test margin: 0.8295
```

But the scored ratio pilot did not show a positive steering effect:

| Virtue | Control | Scripture steer | Negative alpha | Null control | Steer delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prudence | 0.9 | 0.9 | 0.9 | 0.9 | 0.0 |
| Justice | 0.4 | 0.4 | 0.4 | 0.3 | 0.0 |
| Courage | 0.4 | 0.4 | 0.4 | 0.4 | 0.0 |
| Temperance | 0.4 | 0.4 | 0.4 | 0.4 | 0.0 |

Preflight status was `warning`. It found no answer movement for Prudence,
null-control movement matching the real vector for Justice, one regressive
movement for Courage, and one improving movement for Temperance. On the final
scored `limit=10` pilot, however, the real Scripture vector did not change any
answer-level scores relative to control.

## Target-Specific Follow-Up

Because the pooled target was flat on the scored pilot, the next run keeps the
same model, ratio slice, severe controls, and frozen Lex corpus, but tests the
four virtue-specific Scripture targets separately:

```text
prudence_scripture
justice_scripture
fortitude_scripture
temperance_scripture
```

Run:

```cmd
scripts\windows\launchers\run_scripturevec_qwen3_14b_targets_ratio_l10.cmd
```

with output prefix:

```text
experiments/scripturevec14/scripturevec14_qwen3_14b_targets_ratio_l10_v1
```

This run asks whether the pooled vector washed out a more specific signal. It
is still a screen, not final paper evidence.

## Target-Specific Follow-Up Result

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_targets_ratio_l10_v1.status
FINISHED
```

Generated artifacts:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_targets_ratio_l10_v1_vectors.pt
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_targets_ratio_l10_v1_vector_diagnostics.json
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_targets_ratio_l10_v1_preflight.json
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_targets_ratio_l10_v1_ratio.json
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec14\scripturevec14_qwen3_14b_targets_ratio_l10_v1_ratio_logs.json
```

All four target vectors separated Scripture from the generic background corpus
in diagnostics:

| Target | Best layer | Tuned alpha | Dev accuracy | Test accuracy | Steered test margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| `prudence_scripture` | 29 | 8.0 | 1.0 | 1.0 | 0.8190 |
| `justice_scripture` | 29 | 8.0 | 1.0 | 1.0 | 0.8444 |
| `fortitude_scripture` | 32 | 8.0 | 1.0 | 1.0 | 0.7982 |
| `temperance_scripture` | 31 | 8.0 | 1.0 | 1.0 | 0.8543 |

But the scored target-specific ratio pilot did not produce a positive rescue
signal:

| Evaluation virtue | Matched target | Control | Matched Scripture steer | Delta |
| --- | --- | ---: | ---: | ---: |
| Prudence | `prudence_scripture` | 0.9 | 0.9 | 0.0 |
| Justice | `justice_scripture` | 0.4 | 0.3 | -0.1 |
| Courage | `fortitude_scripture` | 0.4 | 0.4 | 0.0 |
| Temperance | `temperance_scripture` | 0.4 | 0.4 | 0.0 |

The full positive-steering grid was also flat or worse:

| Evaluation virtue | `prudence_scripture` | `justice_scripture` | `fortitude_scripture` | `temperance_scripture` |
| --- | ---: | ---: | ---: | ---: |
| Prudence | 0.9 | 0.9 | 0.9 | 0.9 |
| Justice | 0.4 | 0.3 | 0.4 | 0.4 |
| Courage | 0.4 | 0.4 | 0.4 | 0.4 |
| Temperance | 0.4 | 0.4 | 0.4 | 0.4 |

Preflight status was `warning`. It found some answer movement for Justice,
Courage, and Temperance, but the movements were mixed and did not survive as a
clean scored improvement. The strongest negative sign was the matched Justice
case: `justice_scripture` changed one scored answer and regressed it.

Interpretation: on Qwen3-14B, the Cardinal Virtue Scripture vectors are
extractable and specific enough to classify Scripture against generic text, but
neither the pooled nor virtue-specific vectors currently create a useful
VirtueBench ratio-stage behavioral gain.

## Matched High-Alpha Sweep

Question:

> Are the Scripture vectors behaviorally inert because the steering push is too
> weak at benchmark time?

Design:

- Reuse the completed target-specific vector artifact:
  `results\experiments\scripturevec14\scripturevec14_qwen3_14b_targets_ratio_l10_v1_vectors.pt`.
- Evaluate only matched virtue-target pairs:
  - Prudence -> `prudence_scripture`
  - Justice -> `justice_scripture`
  - Courage -> `fortitude_scripture`
  - Temperance -> `temperance_scripture`
- Keep the ratio-stage screen fixed:
  - model: `C:\Users\sethcodex\models\Qwen3-14B`
  - stage: `ratio`
  - limit: `10`
  - runs: `1`
  - temperature: `0.0`
  - seed: `42`
- Compare:
  - `control`
  - `scripture_steer`
  - `scripture_negative_alpha`
  - `scripture_null_control`
- Override the absolute runtime alpha instead of re-extracting vectors.

Runtime alpha ladder:

```text
8, 12, 16, 24, 32, 48, 64, 96, 128
```

The tuned artifact alpha was `8.0`, so this sweep reaches `16x` the tuned
strength. That is intentionally excessive: it tests whether the direction ever
becomes behaviorally visible before it becomes useless or noisy.

Launcher:

```cmd
scripts\windows\launchers\run_scripturevec_qwen3_14b_matched_alpha_sweep_ratio_l10.cmd
```

Top-level status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_v1.status
```

Per-cell output prefix pattern:

```text
experiments/scripturevec14/scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_<virtue>_a<tag>_v1
```

Recovery rule:

- Re-running the launcher skips any per-cell run whose `.status` file already
  says `FINISHED`.
- If an absurd alpha crashes one cell, the launcher records that cell as
  `FAILED` and continues the rest of the sweep.

Decision rule:

- A useful rescue needs positive alpha to improve at least one matched virtue
  without the negative-alpha or null-control lanes matching or beating it.
- If very high alpha only changes answers by degrading accuracy, flipping the
  sign, or making null controls equally active, then the result counts as
  evidence against the simple "we just needed more force" explanation.

## Matched High-Alpha Sweep Result

Remote status:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_v1.status
FINISHED
```

Summary artifacts:

```text
results/experiments/scripturevec14/scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_v1_summary.md
results/experiments/scripturevec14/scripturevec14_qwen3_14b_matched_alpha_sweep_ratio_l10_v1_summary.json
```

The sweep completed all `36` planned matched cells:

```text
9 alpha strengths x 4 matched virtue-target pairs = 36 result files
```

Candidate rescue rows:

| Alpha | Virtue | Control | Positive Scripture | Negative Scripture | Null | Positive paired movement |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 32 | Justice | 0.40 | 0.50 | 0.40 | 0.30 | 3 answer changes / +1 net |
| 48 | Justice | 0.40 | 0.50 | 0.40 | 0.30 | 3 answer changes / +1 net |
| 64 | Justice | 0.40 | 0.50 | 0.40 | 0.30 | 3 answer changes / +1 net |
| 96 | Justice | 0.40 | 0.50 | 0.40 | 0.40 | 3 answer changes / +1 net |

This is the first positive behavioral sign in the Qwen3-14B ScriptureVec run:
Justice improves by one scored answer at intermediate high alpha, and that
improvement is not matched by negative alpha or null control.

But it is narrow:

- Prudence remains flat until alpha `96`, where positive steering degrades it
  from `0.90` to `0.70`.
- Courage is flat until alpha `64`, where positive steering degrades it from
  `0.40` to `0.30`.
- Temperance stays flat until alpha `128`, where positive steering improves to
  `0.50`, but negative alpha also improves to `0.50`, so that sign is not
  direction-specific.
- Alpha `128` is destructive for Prudence and Justice: both positive and
  negative steering collapse those cells to `0.00`.

Interpretation:

The "we just needed more steering force" hypothesis is partially supported,
but only for Justice and only in an intermediate high-alpha window. The result
is not yet broad enough to support the ambitious paper claim. The next
evidence-building step should focus on Justice at alpha `32-96` with a larger
sample, especially `limit 40`, and inspect the item-level flips to see whether
the one gained answer is virtue-relevant rather than a formatting or first-token
artifact.
