# ScriptureVec 27B Run Design

Status: planned as the main scale-up after the 35B readiness probe failed to
load cleanly on the available Windows GPU setup.

## Purpose

Run the same ambitious ScriptureVec test at the largest Qwen3.5 scale that is
likely to be workable on the remote machine:

```text
Qwen/Qwen3.5-27B
```

The target claim remains ambitious:

> A vector derived from Scripture, contrasted against length-matched neutral
> prose, can improve VirtueBench 2 behavior beyond no steering, neutral-side
> steering, and null-vector controls.

The 27B run does not weaken the research claim. It is the next serious scale
candidate after the 35B checkpoint proved blocked by checkpoint/runtime and GPU
memory behavior rather than by stale processes on the machine.

## Model Notes

The model config downloaded on the Windows runner reports:

```text
model_type: qwen3_5
architectures: Qwen3_5ForConditionalGeneration
text_config.model_type: qwen3_5_text
text_config.num_hidden_layers: 64
```

It also has vision-wrapper fields, so the first step is a load-only probe before
starting a full experiment.

## GPU Placement

PyTorch sees the Windows GPUs in this order:

```text
cuda:0 = NVIDIA GeForce RTX 4090, about 24 GiB total
cuda:1 = NVIDIA GeForce RTX 3070, about 8 GiB total
```

Use the 4090 as the main device and the 3070 as overflow:

```text
VIRTUE_BENCH_HF_DEVICE_MAP=auto
VIRTUE_BENCH_HF_MAX_MEMORY=0:22GiB,1:7GiB
VIRTUE_BENCH_HF_LOAD_IN_4BIT=1
VIRTUE_BENCH_HF_DOWNLOAD_WORKERS=1
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
scripts\windows\launchers\run_scripturevec27_pooled_ratio_l10.cmd
```

That launcher runs:

```text
model: Qwen/Qwen3.5-27B
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
output prefix: experiments/scripturevec27/scripturevec27_qwen35_27b_pooled_ratio_l10_v1
```

The condition profile name is still `scripturevec35` because that existing
profile means "ScriptureVec severe controls"; it is not intended to claim that
the model is 35B.

## Artifacts

Expected remote outputs:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec27_qwen35_27b_pooled_ratio_l10_v1.status
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec27_qwen35_27b_pooled_ratio_l10_v1_wrapper_console.log
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec27\scripturevec27_qwen35_27b_pooled_ratio_l10_v1_*
```

## Success Standard

The 27B pooled pilot is promising if:

- `scripture_steer:scripturevec_pooled` beats `control`.
- It beats `scripture_negative_alpha:scripturevec_pooled`.
- It beats `scripture_null_control:scripturevec_pooled`.
- Refusals, answer length, and religious-language drift do not explain the gain.
- The preflight shows that the steering hook changes answer-level behavior.

## Recovery Rules

- If the load-only probe fails before generation, do not start the full run.
- If the run fails during model download, resume the same launcher after checking
  that there is no active Python worker using the GPUs.
- If it fails after vector files are written, inspect the status JSON and console
  log before relaunching; prefer resuming/reusing artifacts rather than changing
  the research design midstream.
- If 27B cannot load in the current runner because of the vision-wrapper config,
  patch the local Hugging Face runner deliberately instead of silently switching
  to another model.
