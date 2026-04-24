# Iconoclast Results Home

Legacy location for Iconoclast outputs.

Prefer using:

- `results/experiments/iconoclast/`

Use this folder as the default home for activation-steering experiment outputs.

## Naming Convention

If you use this legacy path, launch Iconoclast runs with output prefixes like:

```bash
--output-prefix iconoclast/<run_name>
```

Examples:

```bash
--output-prefix iconoclast/qwen3_smoke_v1
--output-prefix iconoclast/qwen3_ratio_pilot_v1
--output-prefix iconoclast/qwen3_full_v1
```

That causes result files to land here as:

- `results/iconoclast/<run_name>_ratio.json`
- `results/iconoclast/<run_name>_ratio_logs.json`
- `results/iconoclast/<run_name>_ratio_checkpoint.json`
- `results/iconoclast/<run_name>_ratio.status.json`
- `results/iconoclast/<run_name>_vectors.pt`

## What Belongs Here

- Iconoclast benchmark outputs
- steering vector artifacts for those runs
- resumable checkpoints
- stage status files

## What Does Not Need to Live Here

- ad hoc remote shell transcripts
- one-off scratch notes
- unrelated baseline runs

For operating guidance, see:

- `docs/experiment_playbook.md`
- `docs/iconoclast_best_practices.md`
