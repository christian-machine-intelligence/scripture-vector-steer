# Start Prompt For Writing Model

You are writing an ICMI-style research paper from a prepared packet of outline
and evidence files. Your task is to draft the paper from the materials in this
folder without wandering into raw experiment artifacts unless explicitly asked.

## Read These Files First, In This Order

1. `README.md`
   - Use this to understand what the packet contains and the current data
     status.

2. `scripturevec_paper_detailed_outline.md`
   - This is the main paper plan. Follow its structure unless there is a strong
     reason to improve the ordering.
   - It identifies the intended figures and tables and points each one to its
     data source.

3. `icmi_style_guide.md`
   - Match the ICMI house style: numbered sections, empirical-theological
     fusion, concrete results, sober limitations, and paper-like prose.
   - Do not imitate the guide mechanically; use it to shape the voice and
     structure.

4. `key_data/README.md`
   - Use this as the guide to the compact data files.

5. `key_data/scripturevec_key_results_rollup.json`
   - Use this for the top-level counts and the main localization summary.

6. `chapter_interpretive_motifs.md`
   - Use this for preliminary biblical interpretation of the confirmed chapter
     hits.
   - Treat it as a draft scaffold. It requires commentary checks before final
     publication claims.

## Then Use These Data Files As Needed

- `key_data/book_confirmation_l40_survivors.csv`
  - Use for the confirmed book-level source set.

- `key_data/chapter_confirmation_l40_survivors.csv`
  - Use for the 16 confirmed chapter movers.

- `key_data/layer_alpha_cells.csv`
  - Use for the main layer/alpha localization table and breadth-vs-strength
    plot.

- `key_data/layer_alpha_expected_grid.csv`
  - Use for the layer-alpha heatmap.
  - Important: the planned 23-cell localization grid is now complete.

- `key_data/chapter_stability_by_localization.csv`
  - Use for ranking which chapters are stable across layer/alpha settings.

- `key_data/chapter_x_layer_alpha_rescue_matrix.csv`
  - Use for a chapter-by-layer/alpha rescue heatmap.

## Core Paper Claim

Lead with the positive discovery:

> Specific biblical chapters produce measurable Justice-relevant activation
> directions in Qwen3-14B, and those directions can be discovered
> systematically across the canon, confirmed under controls, and localized by
> model layer and steering strength.

Do not lead with disclaimers. Put controls, caveats, and theological
boundaries in the proper Methods, Controls, and Limitations sections.

## Rhetorical Shape

Write the paper as a discovery pipeline:

1. Canon-wide book discovery.
2. Book-level confirmation.
3. Chapter-level discovery.
4. Chapter-level confirmation.
5. Layer/alpha localization.
6. Biblical interpretation of the confirmed chapter pattern.
7. Mechanistic implications and future SAE work.

The paper's strongest visual spine should be:

- discovery funnel,
- confirmed book-source chart,
- chapter-hit chart by book,
- layer-alpha heatmap,
- breadth-vs-strength scatter,
- chapter-stability bar chart,
- chapter-by-layer/alpha rescue matrix.

## Important Boundaries

- Do not describe the result as "Scripture in general boosts Justice."
- Do not describe some biblical chapters as spiritually more valuable than
  others.
- The empirical claim concerns model uptake under a specific activation-steering
  intervention.
- Read biblical justice on its own terms: judgment, order, inheritance,
  mediation, vindication, recompense, testimony, deliverance, and right worship.
- Check major commentaries before turning the chapter motif notes into final
  exegetical claims.
- SAE analysis is future work unless new SAE results are supplied.

## Desired Output

Draft a full paper in Markdown using ICMI style:

- title and header block placeholders,
- abstract,
- numbered sections,
- table and figure placeholders,
- references placeholder,
- appendices for full data tables.

When you insert a table or figure placeholder, name the exact data file that
should generate it.
