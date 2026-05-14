# Disjoint-Slice Retest Outputs

This directory is the landing point for the disjoint-slice (b) retest
described in [`scripts/disjoint_slice/README.md`](../../../../../scripts/disjoint_slice/README.md).

## Expected files after Lucius runs the launchers

| File | Source |
| --- | --- |
| `scripturevec14_qwen3_14b_disjoint_l40_o40_L30_a96_v1_summary.json` | `scripts/disjoint_slice/run_disjoint_L30_a96.cmd` on the GPU host |
| `scripturevec14_qwen3_14b_disjoint_l40_o40_L28_a16_v1_summary.json` | `scripts/disjoint_slice/run_disjoint_L28_a16.cmd` on the GPU host |
| `scripturevec14_qwen3_14b_disjoint_l40_o40_L24_a32_v1_summary.json` | `scripts/disjoint_slice/run_disjoint_L24_a32.cmd` on the GPU host |

## Then derived by the analyze script

After the three summary JSONs are in place, run from any CPU env with
the repo cloned:

```bash
python scripts/disjoint_slice/analyze_disjoint_slice.py
```

It writes alongside the summaries:

- `per_row_disjoint_stats.csv` — per-(chapter × cell) row with control /
  positive / negative-α / null accuracies, reconstructed `(b, c)`
  discordant pairs, exact two-sided McNemar p-values, BH-FDR q, and
  Bonferroni adjusted p.
- `cohort_comparison.csv` — per-chapter rollup vs. the nested-slice
  numbers, with a headline `promoted | candidate | demoted` decision.
- `disjoint_slice_summary.json` — machine-readable rollup.

The three derived files are what the next paper revision will cite when
deciding whether each candidate chapter survives a real disjoint-slice
confirmation.
