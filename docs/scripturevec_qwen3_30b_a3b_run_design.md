# ScriptureVec Qwen3 30B-A3B Run Design

Status: load probes failed on the available 4090 + 3070 GPU setup.

## Purpose

Run the ScriptureVec pooled pilot on:

```text
Qwen/Qwen3-30B-A3B
```

This is the first preferred scale-up target because it is a large
mixture-of-experts model with much smaller active compute per token:

```text
30.5B total parameters
3.3B active parameters
```

That makes it a better fit for the ICMI concern that Christian activation may
increase with total model scale, while still having a realistic chance of
running on the available Windows GPU setup.

## Why This Model

Compared with `Qwen/Qwen3.5-35B-A3B`, this model is less entangled with the
Qwen3.5 vision-wrapper path that blocked our current hook runner. Compared with
`Qwen/Qwen3-14B`, it is more ambitious because it has substantially more total
parameters.

The active-parameter count does not remove the need to load the expert weights.
All experts must still be available to the router. So this model still needs a
load-only probe before the actual experiment starts.

## Load Probe Results

Three loading paths were tested before starting a benchmark run:

- `Qwen/Qwen3-30B-A3B` with BitsAndBytes 4-bit loading downloaded cleanly, but
  Transformers could not place the whole model on the two GPUs without spilling
  modules to CPU or disk.
- `QuixiAI/Qwen3-30B-A3B-AWQ` downloaded cleanly, but the Windows environment
  could not find a compatible AWQ loader stack.
- `Qwen/Qwen3-30B-A3B-FP8` downloaded cleanly. After installing
  `triton-windows`, the loader reached GPU placement, but FP8 loading still
  required CPU/disk spillover and Transformers rejected that placement.

The scientific takeaway is straightforward: MoE active-parameter count is not
enough for this run. The model still has to keep the expert weights available,
and the current 4090 + 3070 setup does not have enough usable GPU memory for
this 30B-A3B family through the available hook runner.

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
scripts\windows\launchers\run_scripturevec_qwen3_30b_a3b_pooled_ratio_l10.cmd
```

That launcher runs:

```text
model: Qwen/Qwen3-30B-A3B
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
output prefix: experiments/scripturevec30/scripturevec30_qwen3_30b_a3b_pooled_ratio_l10_v1
```

The condition profile name is still `scripturevec35` because that existing
profile means "ScriptureVec severe controls"; it is not intended to claim that
the model is 35B.

## Artifacts

Expected remote outputs:

```text
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec30_qwen3_30b_a3b_pooled_ratio_l10_v1.status
C:\Users\sethcodex\work\virtue-bench-2\results\scripturevec30_qwen3_30b_a3b_pooled_ratio_l10_v1_wrapper_console.log
C:\Users\sethcodex\work\virtue-bench-2\results\experiments\scripturevec30\scripturevec30_qwen3_30b_a3b_pooled_ratio_l10_v1_*
```

## Success Standard

The Qwen3 30B-A3B pooled pilot is promising if:

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
- If the Qwen3 MoE model cannot be hooked cleanly, fall back to the largest
  Qwen dense model that can run in 4-bit with the same study design.
