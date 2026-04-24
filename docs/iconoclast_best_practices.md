# Iconoclast Best Practices

This file tracks the default operating procedure for activation-steering
experiments in this repo.

For repo-wide experiment conventions, see:

- `docs/experiment_playbook.md`

## Goal

Run steering evaluations in a way that is:

- reproducible
- resumable
- easy to inspect when something fails
- fair to the underlying hypothesis

## Current Thesis

Do not let the experiment drift away from the main question.

The current primary thesis is:

- steering the model toward **scripture activations**, especially **psalm
  activations**, should improve VirtueBench performance
- the main contrast should be **scripture vs generic non-scripture**, not only
  scripture family vs scripture family
- if scope has to narrow, prioritize a **psalms-only** steering run over a
  broader blended Christian or virtue-specific run

Treat these as secondary questions unless they are explicitly promoted back into
the main study:

- `psalms` vs `proverbs` vs `gospels`
- blended `christian` vectors
- virtue-specific activation steering
- thinking vs non-thinking comparisons

## Default Run Home

Put Iconoclast outputs under `results/experiments/iconoclast/` by using output
prefixes like:

```bash
--output-prefix experiments/iconoclast/<run_name>
```

Example:

```bash
virtue-bench iconoclast \
  --model C:\\path\\to\\Qwen3-8B \
  --stage ratio \
  --runs 3 \
  --limit 20 \
  --output-prefix experiments/iconoclast/qwen3_ratio_pilot_v1
```

That will write stage artifacts into `results/experiments/iconoclast/`.

## Standard Sequence

Use this order unless there is a strong reason not to:

1. Verify the local model loads and answers one direct prompt cleanly.
2. Run a tiny one-cell smoke check.
3. Run the exact slice most likely to fail next.
4. Only then launch the broader reduced pilot.
5. Only then launch the longer full study.

Do not jump straight to a large multi-condition run on new hardware or a new
model family.

## Best Practices

### Model and benchmark fairness

- Use the same open-weight local model for all conditions.
- Do not compare prompt baselines from one model family against steering on a
  different model family.
- Freeze vectors before benchmark evaluation.
- Treat `ratio` as the anchor slice before expanding to the full V2 grid.
- Keep the primary scripture experiment aligned to the main thesis:
  scripture-family activations should be compared against generic
  non-scripture activations when the question is whether Scripture itself helps.
- For scripture targets, `auto` should resolve to the scripture-vs-generic
  path. Use `gospelvec_mean` only when you intentionally want the secondary
  within-scripture diagnostic.
- Treat within-scripture comparisons as diagnostic, not as a replacement for
  the primary scripture-vs-generic contrast.
- When comparing steering families, standardize passage scale as well as pair
  counts. Short virtue snippets should be windowed into longer passage-like
  chunks before extraction so the comparison is not distorted by one family
  being learned from short aphorisms and the other from long scriptural chunks.

### Controls

Always keep these controls in the comparison set:

- `control`
- `psalm_baseline`
- `virtue_steer`
- `christian_steer`
- `scripture_steer`
- `combined`
- `null_control`
- `christian_null_control`
- `scripture_null_control`
- `length_control`

If a fake or mismatched vector helps as much as the real one, the result is not
specific enough.

For constrained GPUs, do not insist on running them all at once. Prefer:

- `steer_only` profile: `control`, `virtue_steer`, `christian_steer`, `null_control`, `christian_null_control`
- `christian_compare` profile when the core comparison is baseline vs virtue-steer vs christian-steer
- `scripture_compare` profile when the Christian question is better asked as Psalms vs Proverbs vs Gospels rather than one blended Christian vector
- `scripture_only_compare` profile when you want a GospelVec-style scripture-family run without also benchmarking the virtue corpus lane
- `reasoning_primary` profile when the main question is simply baseline vs pooled `virtue_steer` vs psalm steering and you want a fast scale sweep before a heavier reasoning run
- `psalm_reasoning_primary` profile when the main question is baseline vs explicit Psalm-family steering lanes and you want to drop the virtue lane entirely
- `scripture_reasoning_primary` profile when the main question is baseline vs explicit scripture book lanes such as Psalms, Proverbs, Romans, or Petrine
- `reasoning_compare` profile when the question is how baseline reasoning differs from matched `virtue_steer` and psalm steering on the same model; treat `control` as the neutral lane and keep the null steering controls in the run
  For this comparison, prefer one pooled virtue vector and a broadened psalm mix rather than four separate virtue vectors against a tiny psalm set.
- `prompt_only` or `prompt_heavy` profile in a separate run

### Psalm vector diagnostics and scale sweeps

- Every Iconoclast run now writes:
  - `<output-prefix>_vector_diagnostics.json`
  - `<output-prefix>_vector_diagnostics.md`
- These files are the cleanest first read on which Psalm layers are doing the most work:
  - tuned best layer
  - near-best layer candidates
  - tuned alpha
  - near-best alpha candidates
  - dev/test margins
- If the real question is "how hard should we push the Psalm direction?", do not rebuild the vector every time.
  Build it once, then sweep `--scripture-alpha-scale` over values like `0.75`, `1.0`, `1.5`, and `2.0`.
- For Psalm-family screening, prefer explicit family lanes over one pooled Psalm lane:
  - add them with repeated `--psalm-family-lane` flags
  - use `--include-merged-psalm-family-lane` only after you have chosen the top two families
  - use `--psalm-family-alpha-scale trust=2.0` for one family without changing the others
  - use `--merged-psalm-family-alpha-scale` for the pair lane after a short merged mini-sweep
- Use `control` as the headline comparison. Treat null steers as secondary mechanism checks, not the main scoreboard.
- For book-level scripture screens, treat `petrine` as 1 Peter and 2 Peter combined unless a later study explicitly separates them.
- If the purpose is to find a ceiling, use broader strength steps like `1.0`, `2.0`, and `3.0` before spending budget on fine-grained values.
- For strength sweeps, extract one fresh vector per corpus first and reuse that
  vector across scale levels. Do not re-extract the vector separately for each
  scale unless the explicit question is vector-extraction stability.

### Windows / remote GPU launch discipline

- Prefer a detached background launch over a live SSH-bound shell.
- Always keep a console log, PID file, and simple launcher status file.
- Reconnect after launch and verify the job is still progressing.
- On Windows, keep launcher scripts simple. Avoid fancy quoting and avoid
  Unicode in console summaries.
- On this Windows box, the proved unattended path is: launch
  `.venv\Scripts\python.exe` directly via `cmd.exe /c start "" /b ...` and let
  a small Python launcher script write the status file and wrapper log.
- Do not rely on detached PowerShell wrappers, WMI process creation, or ad hoc
  scheduled-task launches here unless they are re-proved on the machine. They
  were materially less reliable than direct detached `python.exe`.
- Use `scripts/windows/run_iconoclast_job.py` as the background-safe launcher
  and keep run-specific `.cmd` files as thin one-line entrypoints.

### Runtime safeguards

When debugging or stabilizing a run, use:

- `PYTHONFAULTHANDLER=1`
- `TORCH_SHOW_CPP_STACKTRACES=1`
- `CUDA_LAUNCH_BLOCKING=1`

These are especially useful when a process dies without leaving a Python
traceback.

### Qwen3-specific lessons

- Disable Qwen3 thinking mode by default for benchmark scoring.
- Disable Qwen3.5 thinking mode by default for benchmark scoring as well.
- If you explicitly compare thinking vs non-thinking, make sure the scorer strips any leading `<think>...</think>` block before reading the first visible `A` or `B`.
- On Windows, prefer the safer eager attention path if long runs are unstable.
- Check that the model still returns clean A/B answers after any runner change.
- If comparing auto-selected layer windows against GospelVec-style windows, keep
  the comparison explicit by recording the fixed center layer in the artifact.

### Crash resilience

- Save progress after each completed run cell, not only at the end of a stage.
- Write a machine-readable stage status file while the run is active.
- Keep checkpoint files resumable by `(virtue, variant, condition, run_index)`.
- If a long run dies, resume rather than restarting from zero.

### Evaluation discipline

Look at more than top-line accuracy:

- Did the process complete every planned cell?
- Did controls differ in the expected way?
- Did steering help the matching virtue more than the others?
- Did output formatting degrade?
- Did the model become repetitive or unstable?
- Did we improve decisions, or only the tone of the explanations?
- Did paired flips move in the right direction, or did the condition merely land
  on the same percentage with different samples?

### First-token benchmarks

- If the benchmark is scored from the first generated token, be careful with
  generation-only steering.
- In decoder-only models, the first scored token often depends on the prompt
  prefill pass.
- If you skip prefill steering, the intervention can look completely inert even
  when the hook is technically installed.
- After any steering-runtime edit, run a tiny high-alpha divergence probe and
  confirm that `virtue_steer` actually changes answers relative to `control`
  before trusting a flat benchmark result.

### Preflight gate

- Treat the divergence probe as a gate, not a courtesy.
- If a virtue shows zero answer changes at strong probe strength, do not spend
  benchmark budget on it until the vector or runtime is revised.
- If the null control moves as many answers as the real vector, flag that run as
  specificity-poor even if the real vector changes behavior.

## Known Failure Modes

These have already happened in this project:

- model emits hidden thinking text and breaks scoring
- CLI launch path exits without actually running
- Windows console crashes on Unicode table output
- detached job dies without writing final results
- long run only writes results at the end and loses all intermediate progress

Assume any new run can fail in one of these ways until proven otherwise.

## Minimum Preflight Checklist

Before launching a serious run:

- confirm model path and weights are present
- confirm the runner imports and compiles
- confirm the vector artifact matches the requested extraction method
- confirm the output prefix is unique
- confirm logs and status files are being written
- confirm a reconnect does not kill the run

## Output Expectations

For a healthy staged run, expect all of these:

- launcher status file
- console log
- stage status JSON
- stage checkpoint JSON
- stage summary JSON
- stage logs JSON

If only the console log exists, the run is not yet trustworthy.

## Preferred Operating Style

Bias toward:

- smaller proof runs before bigger ones
- resumable jobs over fragile one-shot jobs
- explicit controls over intuitive interpretations
- simple launchers over clever launchers

This repo now has enough moving parts that reliability is part of the science.
