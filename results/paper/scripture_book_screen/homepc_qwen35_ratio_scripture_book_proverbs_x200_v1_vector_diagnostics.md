# Vector Diagnostics: homepc_qwen35_ratio_scripture_book_proverbs_x200_v1

- Model: `Qwen3.5-9B`
- Extraction method: `scripture_contrast`
- Targets: `proverbs`

## Target Ranking
- by dev accuracy: `proverbs` (1.0000)
- by dev margin: `proverbs` (0.9410)
- by steered dev accuracy: `proverbs` (1.0000)
- by test accuracy: `proverbs` (1.0000)
- by steered test margin: `proverbs` (1.0079)
- by test accuracy steered: `proverbs` (1.0000)

## Target Details
### proverbs

- Best layer: `31` via `specificity_within_accuracy_tolerance`
- Layer window: `[28, 29, 30, 31]`
- Tuned alpha: `3.0` via `specificity_within_accuracy_tolerance`
- Dev accuracy / margin: `1.0` / `0.9410078525543213`
- Steered dev accuracy / margin: `1.0` / `1.0393426418304443`
- Test accuracy / steered test accuracy: `1.0` / `1.0`
- Steered test margin: `1.0079100131988525`
- Train/dev/test examples: `91` / `11` / `11`
- Psalm families: n/a
- Psalm vector sets: whole configured target
- Top layers by dev accuracy: `L31` (1.0000), `L30` (1.0000), `L29` (1.0000), `L28` (1.0000), `L27` (1.0000)
- Top layers by dev margin: `L31` (0.9410), `L24` (0.9370), `L25` (0.9151), `L30` (0.8986), `L22` (0.8904)
- Top alphas by dev accuracy: `3` (1.0000), `2` (1.0000), `1.5` (1.0000), `1` (1.0000), `0.75` (1.0000)
- Top alphas by dev margin: `3` (1.0393), `2` (1.0083), `1.5` (0.9926), `1` (0.9760), `0.75` (0.9668)
