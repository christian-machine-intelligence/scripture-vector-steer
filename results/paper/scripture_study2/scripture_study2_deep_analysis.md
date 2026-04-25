# Scripture Study 2 Deep Analysis

## Leaderboard

| Condition | Candidate | Delta pp | Changes | Improve | Regress | Layer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scripture_null_control:petrine` | 66.21% | +1.25 | 50 | 40 | 10 | 24 |
| `scripture_negative_alpha:psalms` | 65.50% | +0.54 | 35 | 24 | 11 | 31 |
| `scripture_negative_alpha:romans` | 65.42% | +0.46 | 29 | 20 | 9 | 31 |
| `scripture_steer:petrine` | 65.25% | +0.29 | 49 | 28 | 21 | 24 |
| `scripture_steer:psalms` | 65.17% | +0.21 | 31 | 18 | 13 | 31 |
| `scripture_steer:romans` | 65.12% | +0.17 | 32 | 18 | 14 | 31 |
| `scripture_null_control:romans` | 64.92% | -0.04 | 17 | 8 | 9 | 31 |
| `scripture_negative_alpha:petrine` | 64.79% | -0.17 | 42 | 19 | 23 | 24 |
| `scripture_null_control:psalms` | 64.58% | -0.38 | 19 | 5 | 14 | 31 |

## Positive Scripture Steers By Virtue

### scripture_steer:petrine
| Virtue | Candidate | Delta pp | Changes | Improve | Regress |
| --- | ---: | ---: | ---: | ---: | ---: |
| prudence | 61.83% | +1.67 | 16 | 13 | 3 |
| justice | 65.83% | -1.17 | 15 | 4 | 11 |
| courage | 51.00% | +0.83 | 13 | 9 | 4 |
| temperance | 82.33% | -0.17 | 5 | 2 | 3 |

### scripture_steer:psalms
| Virtue | Candidate | Delta pp | Changes | Improve | Regress |
| --- | ---: | ---: | ---: | ---: | ---: |
| prudence | 61.67% | +1.50 | 9 | 9 | 0 |
| justice | 66.17% | -0.83 | 11 | 3 | 8 |
| courage | 50.17% | +0.00 | 8 | 4 | 4 |
| temperance | 82.67% | +0.17 | 3 | 2 | 1 |

### scripture_steer:romans
| Virtue | Candidate | Delta pp | Changes | Improve | Regress |
| --- | ---: | ---: | ---: | ---: | ---: |
| prudence | 61.33% | +1.17 | 11 | 9 | 2 |
| justice | 66.83% | -0.17 | 9 | 4 | 5 |
| courage | 50.00% | -0.17 | 7 | 3 | 4 |
| temperance | 82.33% | -0.17 | 5 | 2 | 3 |

## Directionality

| Target | Positive | Negative | Pos-Neg pp | Positive better | Negative better |
| --- | ---: | ---: | ---: | ---: | ---: |
| petrine | 65.25% | 64.79% | +0.46 | 45 | 34 |
| psalms | 65.17% | 65.50% | -0.33 | 25 | 33 |
| romans | 65.12% | 65.42% | -0.29 | 24 | 31 |

## Example Counts

- `scripture_steer:petrine`: improvements `8` shown of `28`, regressions `8` shown of `21`, same-answer rationale shifts `8`
- `scripture_steer:psalms`: improvements `8` shown of `18`, regressions `8` shown of `13`, same-answer rationale shifts `8`
- `scripture_steer:romans`: improvements `8` shown of `18`, regressions `8` shown of `14`, same-answer rationale shifts `8`