# Vector Diagnostics: homepc_qwen35_ratio_scripture_book_petrine_x300_v1

- Model: `Qwen3.5-9B`
- Extraction method: `scripture_contrast`
- Targets: `petrine`

## Target Ranking
- by dev accuracy: `petrine` (1.0000)
- by dev margin: `petrine` (0.9500)
- by steered dev accuracy: `petrine` (1.0000)
- by test accuracy: `petrine` (1.0000)
- by steered test margin: `petrine` (1.1492)
- by test accuracy steered: `petrine` (1.0000)

## Target Details
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
