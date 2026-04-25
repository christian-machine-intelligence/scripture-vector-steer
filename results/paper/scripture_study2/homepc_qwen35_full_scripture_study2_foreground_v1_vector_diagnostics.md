# Vector Diagnostics: homepc_qwen35_full_scripture_study2_foreground_v1

- Model: `Qwen3.5-9B`
- Extraction method: `scripture_contrast`
- Targets: `psalms, romans, petrine`

## Target Ranking
- by dev accuracy: `psalms` (1.0000), `romans` (1.0000), `petrine` (1.0000)
- by dev margin: `psalms` (0.9544), `petrine` (0.9500), `romans` (0.9301)
- by steered dev accuracy: `psalms` (1.0000), `romans` (1.0000), `petrine` (1.0000)
- by test accuracy: `psalms` (1.0000), `romans` (1.0000), `petrine` (1.0000)
- by steered test margin: `petrine` (1.1492), `psalms` (1.0266), `romans` (1.0094)
- by test accuracy steered: `psalms` (1.0000), `romans` (1.0000), `petrine` (1.0000)

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

### petrine

- Best layer: `24` via `specificity_within_accuracy_tolerance`
- Layer window: `[21, 22, 23, 24, 25, 26, 27]`
- Tuned alpha: `3.0` via `specificity_within_accuracy_tolerance`
- Dev accuracy / margin: `1.0` / `0.9499921798706055`
- Steered dev accuracy / margin: `1.0` / `1.1746137142181396`
- Test accuracy / steered test accuracy: `1.0` / `1.0`
- Steered test margin: `1.1492279767990112`
- Train/dev/test examples: `23` / `2` / `2`
- Psalm families: n/a
- Psalm vector sets: whole configured target
- Top layers by dev accuracy: `L31` (1.0000), `L30` (1.0000), `L29` (1.0000), `L28` (1.0000), `L27` (1.0000)
- Top layers by dev margin: `L24` (0.9500), `L25` (0.9350), `L31` (0.9009), `L21` (0.8957), `L30` (0.8951)
- Top alphas by dev accuracy: `3` (1.0000), `2` (1.0000), `1.5` (1.0000), `1` (1.0000), `0.75` (1.0000)
- Top alphas by dev margin: `3` (1.1746), `2` (1.1123), `1.5` (1.0763), `1` (1.0374), `0.75` (1.0170)
