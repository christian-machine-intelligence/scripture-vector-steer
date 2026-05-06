# ScriptureVec 35B Readiness Results

Date: 2026-05-01

## Question

Can the Windows GPU box run the ScriptureVec experiment with Qwen3.5-35B, and are old files or stale GPU processes blocking it?

## Short answer

The machine is not blocked by stale GPU processes. The 4090 was free, the 3070 only had normal display/background memory use, and no model-running process was listed before the probes.

The blocker is checkpoint/loader compatibility and memory behavior for Qwen3.5-35B in the current hook-based Transformers runner.

## Machine state checked

- Windows GPU box reachable over SSH as `sethcodex@100.65.14.37`.
- Remote repo: `C:\Users\sethcodex\work\virtue-bench-2`.
- PyTorch sees the GPUs in the right order for the runner:
  - `cuda:0`: NVIDIA GeForce RTX 4090, about 24 GiB total.
  - `cuda:1`: NVIDIA GeForce RTX 3070, about 8 GiB total.
- `CUDA_VISIBLE_DEVICES` was not set.
- No stale Python/model process was holding the GPUs before the probes.

## Model files found or downloaded

- Existing full Qwen checkpoint:
  - `C:\Users\sethcodex\models\Qwen3.5-35B-A3B`
  - 14 safetensor shards
  - about 67 GiB
  - config reports `qwen3_5_moe`
- Downloaded AWQ checkpoint:
  - `C:\Users\sethcodex\models\Qwen3.5-35B-A3B-AWQ-4bit`
  - about 24.5 GiB downloaded
  - source: `cyankiwi/Qwen3.5-35B-A3B-AWQ-4bit`
- Downloaded language-only checkpoint:
  - `C:\Users\sethcodex\models\Qwen3.5-35B-A3B-LMonly`
  - about 69.3 GiB downloaded
  - source: `ChuGyouk/Qwen3.5-35B-A3B-LMonly`

## Probes run

1. Full Qwen3.5-35B-A3B with 4-bit auto placement.
   - Failed before scoring.
   - Error: some modules were dispatched to CPU/disk, which the 4-bit bitsandbytes path refuses.

2. Full Qwen3.5-35B-A3B text-only class with manual key mapping.
   - Got further than the original launcher.
   - Failed with CUDA out-of-memory on the 4090 during bitsandbytes conversion.

3. AWQ 4-bit checkpoint.
   - The checkpoint weights loaded onto the GPUs.
   - Not usable in the current Transformers class: packed expert tensors were reported as unexpected, while the runner expected fused expert tensors such as `gate_up_proj` and `down_proj`.

4. Language-only checkpoint with 4-bit loading.
   - Auto placement still tried to spill to CPU/disk.
   - Manual GPU splits still failed with CUDA out-of-memory on the 4090 during conversion.

5. Language-only checkpoint with 8-bit CPU offload.
   - Got through weight loading.
   - Failed in bitsandbytes/Accelerate conversion/dispatch on Windows.
   - A small runtime patch got past the first `SCB`/`CB` field mismatch, but the model then failed with automatic conversion issues in the weight report.

## Current conclusion

Qwen3.5-35B is not currently runnable for this ScriptureVec activation-steering experiment on this two-GPU Windows setup using the existing Transformers hook runner.

This is not because GPU memory is being stolen by old processes. It is because the available 35B checkpoints either:

- are too large during bitsandbytes conversion for the 4090+3070 setup,
- require CPU/disk offload that the 4-bit path refuses,
- or use packed quantized tensor layouts that do not match the current Qwen3.5 MoE Transformers class.

## Best next options

1. Keep the paper-facing 9B run as the current reliable local model.
2. Try Qwen3.5-27B or another smaller Qwen3.5 model as the ambitious-but-runnable scale-up.
3. Use a larger single GPU or multi-GPU box with more VRAM for true 35B hook-based activation work.
4. Treat vLLM/SGLang as generation-only options, not direct replacements for this activation-steering pipeline, unless we redesign the method away from internal hooks.
