# Vector Diagnostics: homepc_qwen35_ratio_scripture_book_romans_x300_v1

- Model: `Qwen3.5-9B`
- Extraction method: `scripture_contrast`
- Targets: `romans`

## Target Ranking
- by dev accuracy: `romans` (1.0000)
- by dev margin: `romans` (0.9301)
- by steered dev accuracy: `romans` (1.0000)
- by test accuracy: `romans` (1.0000)
- by steered test margin: `romans` (1.0094)
- by test accuracy steered: `romans` (1.0000)

## Target Details
### romans

- Best layer: `31` via `specificity_within_accuracy_tolerance`
- Layer window: `[28, 29, 30, 31]`
- Tuned alpha: `3.0` via `specificity_within_accuracy_tolerance`
- Dev accuracy / margin: `1.0` / `0.9300969243049622`
- Steered dev accuracy / margin: `1.0` / `1.018261194229126`
- Test accuracy / steered test accuracy: `1.0` / `1.0`
- Steered test margin: `1.0094221830368042`
- Train/dev/test examples: `53` / `6` / `6`
- Psalm families: n/a
- Psalm vector sets: whole configured target
- Top layers by dev accuracy: `L31` (1.0000), `L30` (1.0000), `L29` (1.0000), `L28` (1.0000), `L27` (1.0000)
- Top layers by dev margin: `L31` (0.9301), `L24` (0.9080), `L25` (0.8936), `L30` (0.8929), `L21` (0.8545)
- Top alphas by dev accuracy: `3` (1.0000), `2` (1.0000), `1.5` (1.0000), `1` (1.0000), `0.75` (1.0000)
- Top alphas by dev margin: `3` (1.0183), `2` (0.9904), `1.5` (0.9759), `1` (0.9609), `0.75` (0.9530)
