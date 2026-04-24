# Vector Diagnostics: homepc_qwen35_ratio_scripture_book_psalms_x300_v1

- Model: `Qwen3.5-9B`
- Extraction method: `scripture_contrast`
- Targets: `psalms`

## Target Ranking
- by dev accuracy: `psalms` (1.0000)
- by dev margin: `psalms` (0.9544)
- by steered dev accuracy: `psalms` (1.0000)
- by test accuracy: `psalms` (1.0000)
- by steered test margin: `psalms` (1.0266)
- by test accuracy steered: `psalms` (1.0000)

## Target Details
### psalms

- Best layer: `31` via `specificity_within_accuracy_tolerance`
- Layer window: `[28, 29, 30, 31]`
- Tuned alpha: `3.0` via `specificity_within_accuracy_tolerance`
- Dev accuracy / margin: `1.0` / `0.9544323682785034`
- Steered dev accuracy / margin: `1.0` / `1.0481116771697998`
- Test accuracy / steered test accuracy: `1.0` / `1.0`
- Steered test margin: `1.0265616178512573`
- Train/dev/test examples: `265` / `33` / `33`
- Psalm families: n/a
- Psalm vector sets: whole configured target
- Top layers by dev accuracy: `L31` (1.0000), `L30` (1.0000), `L29` (1.0000), `L28` (1.0000), `L27` (1.0000)
- Top layers by dev margin: `L31` (0.9544), `L24` (0.9103), `L25` (0.9047), `L30` (0.9006), `L22` (0.8511)
- Top alphas by dev accuracy: `3` (1.0000), `2` (1.0000), `1.5` (1.0000), `1` (1.0000), `0.75` (1.0000)
- Top alphas by dev margin: `3` (1.0481), `2` (1.0186), `1.5` (1.0039), `1` (0.9880), `0.75` (0.9793)
