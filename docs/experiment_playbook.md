# Experiment Playbook

This file is the general runbook for model-evaluation experiments in this repo.

Use it for any future experiment family, not just Iconoclast.

## Purpose

Make experiments:

- reproducible
- resumable
- inspectable when they fail
- comparable across runs

## Default Results Layout

Put experiment outputs under:

- `results/experiments/<family>/`

Examples:

- `results/experiments/iconoclast/`
- `results/experiments/prompting/`
- `results/experiments/finetune/`
- `results/experiments/ablations/`

When possible, choose output prefixes like:

```bash
--output-prefix experiments/<family>/<run_name>
```

## Standard Run Sequence

Use this order by default:

1. Verify the model and runner on one direct prompt.
2. Run a tiny smoke check.
3. Run the exact slice most likely to fail next.
4. Run the reduced pilot.
5. Run the longer full experiment.

Do not jump straight to a large multi-condition run on new hardware, a new
model family, or a newly edited runner.

## Universal Best Practices

### Reliability first

- Prefer resumable jobs over one-shot jobs.
- Save progress incrementally, not only at the end.
- Write machine-readable status files while the run is live.
- Keep console logs for every serious run.

### Remote execution discipline

- Prefer detached/background jobs over live SSH-bound shells.
- After launch, disconnect and reconnect once to make sure the job survives.
- Keep launch scripts simple and easy to inspect.
- Avoid avoidable quoting complexity, especially on Windows.
- On the current Windows GPU machine, the safest proved pattern is a detached
  direct `python.exe` launch, with Python itself responsible for writing the
  run status and wrapper log.

### Crash diagnosis

When a run is unstable, bias toward:

- `PYTHONFAULTHANDLER=1`
- `TORCH_SHOW_CPP_STACKTRACES=1`
- `CUDA_LAUNCH_BLOCKING=1`

The goal is to turn silent death into visible failure.

### Evaluation discipline

Always ask:

- Did the full planned run complete?
- Did the controls behave as expected?
- Did the intervention help in the intended way?
- Did output quality degrade?
- Did the run produce artifacts we can trust?
- Did the intervention change specific decisions, or only the topline percentage?

Do not rely on a single top-line metric.

### First-token scored benchmarks

- If the benchmark is scored from the model's first generated token, validate
  that the intervention can actually influence that token.
- A hook can be "installed" and still be effectively inert if it is applied too
  late in the generation path.
- After any hook or runtime change, run a tiny strong-intervention sanity check
  and confirm that steered outputs diverge from control at the answer level.

### Steering preflight

- For steering experiments, run a small high-alpha divergence probe before the
  real benchmark stage.
- Treat zero answer changes under a strong probe as a failed preflight, not as a
  negative scientific result.
- Record the probe as its own artifact so later readers can distinguish
  "inert intervention" from "intervention failed to help."

### Memory-aware staging

- On 24 GB GPUs, separate steer-only conditions from prompt-heavy conditions.
- Do not mix a lightweight steering slice with known OOM-prone prompt baselines
  if the heavier arms can turn the whole run partial.
- Prefer one clean steer-only pilot plus one clean prompt-baseline pilot over a
  single muddied run.

## Minimum Preflight Checklist

Before a serious run:

- confirm model weights are present
- confirm the runner imports and compiles
- confirm the requested output prefix is unique
- confirm logs and status files are being written
- confirm the run can survive a reconnect

## Expected Artifacts

A healthy experiment should usually have:

- launcher status file
- console log
- machine-readable stage status
- checkpoint file
- summary results
- detailed logs

If only a console log exists, the run is usually not robust enough yet.

## Family-Specific Runbooks

Use this file as the top-level guide, then keep experiment-family details in
separate files.

Current family-specific runbooks:

- `docs/iconoclast_best_practices.md`
