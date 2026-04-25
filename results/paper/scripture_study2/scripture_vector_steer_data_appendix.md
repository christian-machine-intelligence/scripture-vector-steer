# Scripture Vector Steer Data Appendix

This appendix collects the paper-facing data for the completed Scripture Vector
Steer run on Qwen3.5-9B.

## Raw Artifact Map

The complete decision-level run output is:

- [`homepc_qwen35_full_scripture_study2_foreground_v1_full.json`](homepc_qwen35_full_scripture_study2_foreground_v1_full.json)

The cleaned analysis files are:

- [`scripture_study2_summary.md`](scripture_study2_summary.md)
- [`scripture_study2_summary.json`](scripture_study2_summary.json)
- [`scripture_study2_deep_analysis.md`](scripture_study2_deep_analysis.md)
- [`scripture_study2_deep_analysis.json`](scripture_study2_deep_analysis.json)
- [`homepc_qwen35_full_scripture_study2_foreground_v1_vector_diagnostics.md`](homepc_qwen35_full_scripture_study2_foreground_v1_vector_diagnostics.md)
- [`homepc_qwen35_full_scripture_study2_foreground_v1_vector_diagnostics.json`](homepc_qwen35_full_scripture_study2_foreground_v1_vector_diagnostics.json)

Status verification files:

- [`homepc_qwen35_full_scripture_study2_foreground_v1_full.status.json`](homepc_qwen35_full_scripture_study2_foreground_v1_full.status.json)
- [`homepc_qwen35_full_scripture_study2_foreground_v1_run.status.json`](homepc_qwen35_full_scripture_study2_foreground_v1_run.status.json)

## Run Design

| Field | Value |
| --- | --- |
| Project | Scripture Vector Steer |
| Model | `Qwen/Qwen3.5-9B` |
| Benchmark | VirtueBench 2 |
| Stage | `full` |
| Runs | `3` |
| Limit | `40` |
| Temperature | `0.0` |
| Profile | `scripture_study2` |
| Scripture targets | `psalms`, `romans`, `petrine` |
| Petrine definition | 1 Peter + 2 Peter |
| Conditions | control, positive scripture steer, negative-alpha scripture steer, scripture null control |
| Runtime alpha | `3.0` |
| Vector policy | One extracted vector per scripture corpus, reused across the run |
| Extraction method | `scripture_contrast` |
| Positive side | selected scripture corpus chunks |
| Background side | generic non-scripture chunks |

## Vector Diagnostics

| Target | Best layer | Layer window | Alpha | Runtime alpha | Steered test margin |
| --- | ---: | --- | ---: | ---: | ---: |
| psalms | 31 | 28, 29, 30, 31 | 3.0 | 3.0 | 1.0266 |
| romans | 31 | 28, 29, 30, 31 | 3.0 | 3.0 | 1.0094 |
| petrine | 24 | 21, 22, 23, 24, 25, 26, 27 | 3.0 | 3.0 | 1.1492 |

## Lane Leaderboard

Control accuracy for all comparisons: `64.958%`.

| Condition | Candidate | Delta pp | Changes | Improved | Regressed | Layer | Alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `scripture_null_control:petrine` | 66.208% | +1.250 | 50 | 40 | 10 | 24 | 3.0 |
| `scripture_negative_alpha:psalms` | 65.500% | +0.542 | 35 | 24 | 11 | 31 | -3.0 |
| `scripture_negative_alpha:romans` | 65.417% | +0.458 | 29 | 20 | 9 | 31 | -3.0 |
| `scripture_steer:petrine` | 65.250% | +0.292 | 49 | 28 | 21 | 24 | 3.0 |
| `scripture_steer:psalms` | 65.167% | +0.208 | 31 | 18 | 13 | 31 | 3.0 |
| `scripture_steer:romans` | 65.125% | +0.167 | 32 | 18 | 14 | 31 | 3.0 |
| `scripture_null_control:romans` | 64.917% | -0.042 | 17 | 8 | 9 | 31 | 3.0 |
| `scripture_negative_alpha:petrine` | 64.792% | -0.167 | 42 | 19 | 23 | 24 | -3.0 |
| `scripture_null_control:psalms` | 64.583% | -0.375 | 19 | 5 | 14 | 31 | 3.0 |

## Directionality

| Target | Positive condition | Negative condition | Positive accuracy | Negative accuracy | Positive - negative | Answer changes | Positive better | Negative better |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| petrine | `scripture_steer:petrine` | `scripture_negative_alpha:petrine` | 65.250% | 64.792% | +0.458 pp | 79 | 45 | 34 |
| psalms | `scripture_steer:psalms` | `scripture_negative_alpha:psalms` | 65.167% | 65.500% | -0.333 pp | 58 | 25 | 33 |
| romans | `scripture_steer:romans` | `scripture_negative_alpha:romans` | 65.125% | 65.417% | -0.292 pp | 55 | 24 | 31 |

## Per-Variant Data

### `scripture_steer:psalms`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 66.875% | +0.208 | 5 | 3 | 2 | 12 |
| `caro` | 74.375% | 73.125% | -1.250 | 6 | 0 | 6 | 12 |
| `mundus` | 67.292% | 67.500% | +0.208 | 7 | 4 | 3 | 12 |
| `diabolus` | 57.500% | 58.333% | +0.833 | 8 | 6 | 2 | 12 |
| `ignatian` | 58.958% | 60.000% | +1.042 | 5 | 5 | 0 | 12 |

### `scripture_steer:romans`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 67.708% | +1.042 | 7 | 6 | 1 | 12 |
| `caro` | 74.375% | 72.917% | -1.458 | 7 | 0 | 7 | 12 |
| `mundus` | 67.292% | 67.083% | -0.208 | 7 | 3 | 4 | 12 |
| `diabolus` | 57.500% | 58.333% | +0.833 | 8 | 6 | 2 | 12 |
| `ignatian` | 58.958% | 59.583% | +0.625 | 3 | 3 | 0 | 12 |

### `scripture_steer:petrine`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 67.083% | +0.417 | 4 | 3 | 1 | 12 |
| `caro` | 74.375% | 74.375% | +0.000 | 18 | 9 | 9 | 12 |
| `mundus` | 67.292% | 68.125% | +0.833 | 8 | 6 | 2 | 12 |
| `diabolus` | 57.500% | 57.292% | -0.208 | 15 | 7 | 8 | 12 |
| `ignatian` | 58.958% | 59.375% | +0.417 | 4 | 3 | 1 | 12 |

### `scripture_negative_alpha:psalms`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 66.667% | +0.000 | 10 | 5 | 5 | 12 |
| `caro` | 74.375% | 74.375% | +0.000 | 8 | 4 | 4 | 12 |
| `mundus` | 67.292% | 68.958% | +1.667 | 8 | 8 | 0 | 12 |
| `diabolus` | 57.500% | 58.542% | +1.042 | 9 | 7 | 2 | 12 |
| `ignatian` | 58.958% | 58.958% | +0.000 | 0 | 0 | 0 | 12 |

### `scripture_negative_alpha:romans`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 66.875% | +0.208 | 11 | 6 | 5 | 12 |
| `caro` | 74.375% | 75.833% | +1.458 | 9 | 8 | 1 | 12 |
| `mundus` | 67.292% | 68.333% | +1.042 | 5 | 5 | 0 | 12 |
| `diabolus` | 57.500% | 57.292% | -0.208 | 3 | 1 | 2 | 12 |
| `ignatian` | 58.958% | 58.750% | -0.208 | 1 | 0 | 1 | 12 |

### `scripture_negative_alpha:petrine`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 66.458% | -0.208 | 11 | 5 | 6 | 12 |
| `caro` | 74.375% | 72.708% | -1.667 | 14 | 3 | 11 | 12 |
| `mundus` | 67.292% | 68.333% | +1.042 | 5 | 5 | 0 | 12 |
| `diabolus` | 57.500% | 57.708% | +0.208 | 11 | 6 | 5 | 12 |
| `ignatian` | 58.958% | 58.750% | -0.208 | 1 | 0 | 1 | 12 |

### `scripture_null_control:psalms`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 66.250% | -0.417 | 2 | 0 | 2 | 12 |
| `caro` | 74.375% | 72.917% | -1.458 | 7 | 0 | 7 | 12 |
| `mundus` | 67.292% | 67.500% | +0.208 | 3 | 2 | 1 | 12 |
| `diabolus` | 57.500% | 57.708% | +0.208 | 5 | 3 | 2 | 12 |
| `ignatian` | 58.958% | 58.542% | -0.417 | 2 | 0 | 2 | 12 |

### `scripture_null_control:romans`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 67.083% | +0.417 | 4 | 3 | 1 | 12 |
| `caro` | 74.375% | 72.708% | -1.667 | 8 | 0 | 8 | 12 |
| `mundus` | 67.292% | 67.500% | +0.208 | 1 | 1 | 0 | 12 |
| `diabolus` | 57.500% | 58.333% | +0.833 | 4 | 4 | 0 | 12 |
| `ignatian` | 58.958% | 58.958% | +0.000 | 0 | 0 | 0 | 12 |

### `scripture_null_control:petrine`

| Variant | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ratio` | 66.667% | 67.708% | +1.042 | 11 | 8 | 3 | 12 |
| `caro` | 74.375% | 75.417% | +1.042 | 13 | 9 | 4 | 12 |
| `mundus` | 67.292% | 70.417% | +3.125 | 15 | 15 | 0 | 12 |
| `diabolus` | 57.500% | 58.750% | +1.250 | 10 | 8 | 2 | 12 |
| `ignatian` | 58.958% | 58.750% | -0.208 | 1 | 0 | 1 | 12 |

## Per-Virtue Data

### `scripture_steer:psalms`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 61.667% | +1.500 | 9 | 9 | 0 | 15 |
| justice | 67.000% | 66.167% | -0.833 | 11 | 3 | 8 | 15 |
| courage | 50.167% | 50.167% | +0.000 | 8 | 4 | 4 | 15 |
| temperance | 82.500% | 82.667% | +0.167 | 3 | 2 | 1 | 15 |

### `scripture_steer:romans`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 61.333% | +1.167 | 11 | 9 | 2 | 15 |
| justice | 67.000% | 66.833% | -0.167 | 9 | 4 | 5 | 15 |
| courage | 50.167% | 50.000% | -0.167 | 7 | 3 | 4 | 15 |
| temperance | 82.500% | 82.333% | -0.167 | 5 | 2 | 3 | 15 |

### `scripture_steer:petrine`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 61.833% | +1.667 | 16 | 13 | 3 | 15 |
| justice | 67.000% | 65.833% | -1.167 | 15 | 4 | 11 | 15 |
| courage | 50.167% | 51.000% | +0.833 | 13 | 9 | 4 | 15 |
| temperance | 82.500% | 82.333% | -0.167 | 5 | 2 | 3 | 15 |

### `scripture_negative_alpha:psalms`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 60.500% | +0.333 | 10 | 6 | 4 | 15 |
| justice | 67.000% | 68.167% | +1.167 | 15 | 11 | 4 | 15 |
| courage | 50.167% | 50.833% | +0.667 | 4 | 4 | 0 | 15 |
| temperance | 82.500% | 82.500% | +0.000 | 6 | 3 | 3 | 15 |

### `scripture_negative_alpha:romans`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 60.500% | +0.333 | 10 | 6 | 4 | 15 |
| justice | 67.000% | 67.333% | +0.333 | 10 | 6 | 4 | 15 |
| courage | 50.167% | 50.833% | +0.667 | 6 | 5 | 1 | 15 |
| temperance | 82.500% | 83.000% | +0.500 | 3 | 3 | 0 | 15 |

### `scripture_negative_alpha:petrine`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 59.500% | -0.667 | 14 | 5 | 9 | 15 |
| justice | 67.000% | 66.667% | -0.333 | 16 | 7 | 9 | 15 |
| courage | 50.167% | 50.333% | +0.167 | 7 | 4 | 3 | 15 |
| temperance | 82.500% | 82.667% | +0.167 | 5 | 3 | 2 | 15 |

### `scripture_null_control:psalms`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 60.500% | +0.333 | 4 | 3 | 1 | 15 |
| justice | 67.000% | 65.833% | -1.167 | 7 | 0 | 7 | 15 |
| courage | 50.167% | 49.500% | -0.667 | 4 | 0 | 4 | 15 |
| temperance | 82.500% | 82.500% | +0.000 | 4 | 2 | 2 | 15 |

### `scripture_null_control:romans`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 60.000% | -0.167 | 1 | 0 | 1 | 15 |
| justice | 67.000% | 66.667% | -0.333 | 8 | 3 | 5 | 15 |
| courage | 50.167% | 50.333% | +0.167 | 5 | 3 | 2 | 15 |
| temperance | 82.500% | 82.667% | +0.167 | 3 | 2 | 1 | 15 |

### `scripture_null_control:petrine`

| Virtue | Control | Candidate | Delta pp | Changes | Improved | Regressed | Paired runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prudence | 60.167% | 62.667% | +2.500 | 25 | 20 | 5 | 15 |
| justice | 67.000% | 67.833% | +0.833 | 13 | 9 | 4 | 15 |
| courage | 50.167% | 51.000% | +0.833 | 7 | 6 | 1 | 15 |
| temperance | 82.500% | 83.333% | +0.833 | 5 | 5 | 0 | 15 |

## Reasoning Review Packs

Selected reasoning examples are available in:

- [`scripture_study2_deep_analysis.md`](scripture_study2_deep_analysis.md)
- [`scripture_study2_deep_analysis.json`](scripture_study2_deep_analysis.json)

The JSON contains, for each non-control lane:

- improvements
- regressions
- answer-changed/no-score-change cases
- same-answer rationale shifts

Counts by lane:

| Condition | Changed answers | Same-answer rationale shifts included |
| --- | ---: | ---: |
| `scripture_negative_alpha:petrine` | 42 | 8 |
| `scripture_negative_alpha:psalms` | 35 | 8 |
| `scripture_negative_alpha:romans` | 29 | 8 |
| `scripture_null_control:petrine` | 50 | 8 |
| `scripture_null_control:psalms` | 19 | 8 |
| `scripture_null_control:romans` | 17 | 8 |
| `scripture_steer:petrine` | 49 | 8 |
| `scripture_steer:psalms` | 31 | 8 |
| `scripture_steer:romans` | 32 | 8 |
