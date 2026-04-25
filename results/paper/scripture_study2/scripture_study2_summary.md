# Study 2 Scripture Directionality Summary

## Lane Results

| Target | Condition | Control | Candidate | Delta | Changes | Improve | Regress | Vector alpha | Layer |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| petrine | scripture_negative_alpha | 64.96% | 64.79% | -0.17% | 42 | 19 | 23 | -3.0 | 24 |
| psalms | scripture_negative_alpha | 64.96% | 65.50% | +0.54% | 35 | 24 | 11 | -3.0 | 31 |
| romans | scripture_negative_alpha | 64.96% | 65.42% | +0.46% | 29 | 20 | 9 | -3.0 | 31 |
| petrine | scripture_null_control | 64.96% | 66.21% | +1.25% | 50 | 40 | 10 | 3.0 | 24 |
| psalms | scripture_null_control | 64.96% | 64.58% | -0.37% | 19 | 5 | 14 | 3.0 | 31 |
| romans | scripture_null_control | 64.96% | 64.92% | -0.04% | 17 | 8 | 9 | 3.0 | 31 |
| petrine | scripture_steer | 64.96% | 65.25% | +0.29% | 49 | 28 | 21 | 3.0 | 24 |
| psalms | scripture_steer | 64.96% | 65.17% | +0.21% | 31 | 18 | 13 | 3.0 | 31 |
| romans | scripture_steer | 64.96% | 65.12% | +0.17% | 32 | 18 | 14 | 3.0 | 31 |

## Directionality

| Target | Positive | Negative | Pos - Neg | Answer changes | Positive better | Negative better |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| petrine | 65.25% | 64.79% | +0.46% | 79 | 45 | 34 |
| psalms | 65.17% | 65.50% | -0.33% | 58 | 25 | 33 |
| romans | 65.12% | 65.42% | -0.29% | 55 | 24 | 31 |

## Per-Variant Deltas

### scripture_negative_alpha:petrine

- `caro`: `-1.67%`
- `diabolus`: `+0.21%`
- `ignatian`: `-0.21%`
- `mundus`: `+1.04%`
- `ratio`: `-0.21%`

### scripture_negative_alpha:psalms

- `caro`: `+0.00%`
- `diabolus`: `+1.04%`
- `ignatian`: `+0.00%`
- `mundus`: `+1.67%`
- `ratio`: `+0.00%`

### scripture_negative_alpha:romans

- `caro`: `+1.46%`
- `diabolus`: `-0.21%`
- `ignatian`: `-0.21%`
- `mundus`: `+1.04%`
- `ratio`: `+0.21%`

### scripture_null_control:petrine

- `caro`: `+1.04%`
- `diabolus`: `+1.25%`
- `ignatian`: `-0.21%`
- `mundus`: `+3.12%`
- `ratio`: `+1.04%`

### scripture_null_control:psalms

- `caro`: `-1.46%`
- `diabolus`: `+0.21%`
- `ignatian`: `-0.42%`
- `mundus`: `+0.21%`
- `ratio`: `-0.42%`

### scripture_null_control:romans

- `caro`: `-1.67%`
- `diabolus`: `+0.83%`
- `ignatian`: `+0.00%`
- `mundus`: `+0.21%`
- `ratio`: `+0.42%`

### scripture_steer:petrine

- `caro`: `+0.00%`
- `diabolus`: `-0.21%`
- `ignatian`: `+0.42%`
- `mundus`: `+0.83%`
- `ratio`: `+0.42%`

### scripture_steer:psalms

- `caro`: `-1.25%`
- `diabolus`: `+0.83%`
- `ignatian`: `+1.04%`
- `mundus`: `+0.21%`
- `ratio`: `+0.21%`

### scripture_steer:romans

- `caro`: `-1.46%`
- `diabolus`: `+0.83%`
- `ignatian`: `+0.62%`
- `mundus`: `-0.21%`
- `ratio`: `+1.04%`

## Reasoning Review Packs

- `scripture_negative_alpha:petrine`: changed `42`, same-answer rationale shifts `8`
- `scripture_negative_alpha:psalms`: changed `35`, same-answer rationale shifts `8`
- `scripture_negative_alpha:romans`: changed `29`, same-answer rationale shifts `8`
- `scripture_null_control:petrine`: changed `50`, same-answer rationale shifts `8`
- `scripture_null_control:psalms`: changed `19`, same-answer rationale shifts `8`
- `scripture_null_control:romans`: changed `17`, same-answer rationale shifts `8`
- `scripture_steer:petrine`: changed `49`, same-answer rationale shifts `8`
- `scripture_steer:psalms`: changed `31`, same-answer rationale shifts `8`
- `scripture_steer:romans`: changed `32`, same-answer rationale shifts `8`

## Vector Diagnostics

- `petrine`: layer `24`, window `[21, 22, 23, 24, 25, 26, 27]`, tuned alpha `3.0`, runtime alpha `3.0`, margin `1.1492279767990112`
- `psalms`: layer `31`, window `[28, 29, 30, 31]`, tuned alpha `3.0`, runtime alpha `3.0`, margin `1.0265616178512573`
- `romans`: layer `31`, window `[28, 29, 30, 31]`, tuned alpha `3.0`, runtime alpha `3.0`, margin `1.0094221830368042`