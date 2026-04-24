# Experiments Results Home

Use this directory as the top-level home for future experiment families.

## Structure

Create one subfolder per experiment family:

- `results/experiments/iconoclast/`
- `results/experiments/prompting/`
- `results/experiments/finetune/`
- `results/experiments/ablations/`

## Naming Convention

Prefer output prefixes like:

```bash
--output-prefix experiments/<family>/<run_name>
```

Examples:

```bash
--output-prefix experiments/iconoclast/qwen3_ratio_pilot_v1
--output-prefix experiments/prompting/psalm_baseline_v1
```

For Iconoclast specifically, the CLI now defaults to a timestamped prefix under
`experiments/iconoclast/` if no `--output-prefix` is supplied.

## Purpose

This directory is meant to keep experiment outputs organized across multiple
evaluation families, not just one method.

For operating guidance, see:

- `docs/experiment_playbook.md`
