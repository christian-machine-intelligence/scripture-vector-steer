# ScriptureVec Qwen3 32B Run Design

Status: load probe failed on the available 4090 + 3070 GPU setup.

## Purpose

Run the same ScriptureVec pooled pilot on:

```text
Qwen/Qwen3-32B
```

On the Windows runner this is mirrored locally before use:

```text
C:\Users\sethcodex\models\Qwen3-32B
```

This is an ambitious Qwen fallback because it is a dense 32.8B-parameter model.
Unlike the MoE model, all of its model capacity is active on each prompt. That
fits the project concern that Christian activation may increase with model
scale better than dropping immediately to a much smaller dense model.

## Why This Model

The Qwen3 30B-A3B family was attractive because of its large total parameter
count, but the available loaders still needed more GPU memory than the Windows
4090 + 3070 setup could provide. `Qwen/Qwen3-32B` is larger in active parameters
and should have a better chance of fitting through standard BitsAndBytes 4-bit
loading.

## Load Probe Result

The local mirror completed successfully and its config identified the model as:

```text
model_type: qwen3
architecture: Qwen3ForCausalLM
```

However, both the conservative placement (`0:23GiB,1:7GiB`) and a near-maximum
placement (`0:24GiB,1:8GiB`) still required Transformers to dispatch some
modules to CPU or disk. Because CPU/disk spillover would make this run slow and
harder to interpret, this model was not used for the benchmark.

## GPU Placement

PyTorch sees the Windows GPUs in this order:

```text
cuda:0 = NVIDIA GeForce RTX 4090, about 24 GiB total
cuda:1 = NVIDIA GeForce RTX 3070, about 8 GiB total
```

Use automatic placement across both GPUs:

```text
VIRTUE_BENCH_HF_DEVICE_MAP=auto
VIRTUE_BENCH_HF_MAX_MEMORY=0:23GiB,1:7GiB
VIRTUE_BENCH_HF_LOAD_IN_4BIT=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

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
scripts\windows\launchers\run_scripturevec_qwen3_32b_pooled_ratio_l10.cmd
```

That launcher runs:

```text
model: C:\Users\sethcodex\models\Qwen3-32B
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
output prefix: experiments/scripturevec32/scripturevec32_qwen3_32b_pooled_ratio_l10_v1
```

The condition profile name is still `scripturevec35` because that existing
profile means "ScriptureVec severe controls"; it is not intended to claim that
the model is 35B.

## Artifacts

Expected remote outputs:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec32_qwen3_32b_pooled_ratio_l10_v1.status
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec32_qwen3_32b_pooled_ratio_l10_v1_wrapper_console.log
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec32\scripturevec32_qwen3_32b_pooled_ratio_l10_v1_*
```

## Success Standard

The Qwen3 32B pooled pilot is promising if:

- `scripture_steer:scripturevec_pooled` beats `control`.
- It beats `scripture_negative_alpha:scripturevec_pooled`.
- It beats `scripture_null_control:scripturevec_pooled`.
- Refusals, answer length, and religious-language drift do not explain the gain.
- The preflight shows that the steering hook changes answer-level behavior.

## Recovery Rules

- If the load-only probe fails before generation, do not start the full run.
- If download fails, resume after checking that no Python worker is using the
  GPUs.
- If the model spills to CPU/disk under 4-bit placement, do not run the study
  until we decide whether that slow/offloaded mode is scientifically acceptable.
- If Qwen3 32B cannot be placed across the GPUs, fall back to
  `Qwen/Qwen3-14B` dense rather than changing the evaluation design.
