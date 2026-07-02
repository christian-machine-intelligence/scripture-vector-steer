# ScriptureVec Justice Paper Detailed Outline

Status: writing-model handoff draft  
Last updated: 2026-05-05  
Primary project: ScriptureVec / VirtueBench2 Justice steering  
Primary model: Qwen3-14B  

## One-Sentence Paper Claim

Specific biblical chapters produce measurable Justice-relevant activation
directions in Qwen3-14B, and those directions can be discovered systematically
across the canon, confirmed under controls, and localized by model layer and
steering strength.

## Core Positive Finding

The paper should lead with the discovery:

> A canon-wide search over Scripture-derived activation vectors found that
> particular biblical chapters, especially in Acts, Hebrews, Numbers,
> 1 Chronicles, Judges, and Deuteronomy, produce Justice-relevant steering
> effects on VirtueBench2. These effects are not interchangeable: they vary by
> textual source, model layer, and steering strength.

The best current localization findings are:

- `L31 / alpha 96`: broadest coverage, rescuing `12/16` confirmed chapters.
- `L32 / alpha 32`: second-broadest coverage, rescuing `11/16`.
- `L24 / alpha 32`: strongest average movement, rescuing `9/16` with the
  largest mean positive delta.
- `L33 / alpha 32`: weak, rescuing only `2/16`.
- `L36 / alpha 32`: no rescues.

The paper should present this as a discovery of structured scriptural uptake in
activation space.

## Recommended Title Options

1. **Searching Scripture in Activation Space: Chapter-Level Biblical Vectors for Justice Steering**
2. **Not All Scripture Moves Alike: Discovering Chapter-Level Biblical Activation Vectors for Justice**
3. **A Canon-Wide Search for Justice in Scriptural Activation Space**
4. **From Canon to Chapter to Layer: Discovering Biblical Activation Vectors for Justice**

Preferred title: option 4 if the paper emphasizes the full pipeline; option 1
if the paper wants a cleaner methods-forward title.

## Abstract Shape

The abstract should move in this order:

1. Prior work has shown that scriptural text can influence model behavior.
2. This paper asks whether Scripture-derived activation vectors can be searched
   systematically and localized within the model.
3. We run a canon-wide discovery pipeline on Qwen3-14B using the Justice subset
   of VirtueBench2, ratio stage.
4. We identify 19 preliminary book candidates from all 66 books, confirm 7 at a
   larger slice, drill down to 38 chapter candidates, confirm 16 chapters, and
   localize those chapters across model layers and steering strengths.
5. The localization result shows a structured pattern: L31/L32 provide broad
   rescue coverage, while L24 produces stronger movement on fewer chapters.
6. The confirmed chapters are biblically diverse, including narratives of
   testimony, divine adjudication, inheritance, priesthood, judgment,
   vindication, and ordered worship.
7. The result establishes a path from scriptural corpus discovery to mechanistic
   analysis of how models internally represent and respond to biblical moral
   form.

## Recommended Figure And Table List

Use these as the main visual spine of the paper.

### Figure 1: The Discovery Funnel

Purpose: make the whole study feel rigorous and hard to dismiss.

Suggested form: horizontal funnel or staged flow diagram.

Data:

- `key_data/book_discovery_l10_candidates.csv`
- `key_data/book_confirmation_l40_survivors.csv`
- `key_data/chapter_discovery_l10_clean_hits.csv`
- `key_data/chapter_confirmation_l40_survivors.csv`

Visual content:

```text
66 biblical books
  -> 19 preliminary book candidates
  -> 7 confirmed book sources
  -> 38 preliminary chapter hits
  -> 16 confirmed chapter movers
  -> 22/23 completed layer-alpha localization cells
```

Caption emphasis:

> The study begins with the whole Protestant canon and narrows candidates only
> through behavioral tests under controls.

### Table 1: Study Pipeline And Decision Rules

Purpose: show that every step had a specific role.

Columns:

- Study step
- Input set
- Benchmark slice
- Steering strength
- Controls
- Passing rule
- Output set

Rows:

- Book discovery, all 66 books, limit 10
- Book confirmation, 19 candidates, limit 40
- Chapter drilldown, 7 books / 170 chapters, limit 10
- Chapter confirmation, 38 chapter hits, limit 40
- Layer/alpha localization, 16 confirmed chapters, limit 10

Data:

- `key_data/scripturevec_key_results_rollup.json`

### Figure 2: Book-Level Confirmation

Purpose: show that the book screen is selective.

Suggested form: bar chart or slope plot from control to positive steering for
all 19 book candidates, with survivors highlighted.

Data:

- `key_data/book_confirmation_l40_all_candidates.csv`

Key visual point:

- Seven books survive: `1 Chronicles`, `Amos`, `Deuteronomy`, `Judges`,
  `Numbers`, `Acts`, `Hebrews`.
- Hebrews is strongest at book level, moving from `0.40` to `0.45`.
- Some plausible books fail, worsen, or are matched by controls.

Do not lead this section with the failures. Use failures to show selectivity
after the positive result is clear.

### Figure 3: Chapter Discovery By Biblical Book

Purpose: show that chapter hits are clustered, not random-looking.

Suggested form: heatmap or grouped bar chart.

Data:

- `key_data/chapter_discovery_l10_clean_hits.csv`

Content:

- Acts: 14 preliminary chapter hits.
- Hebrews: 6.
- Numbers: 6.
- 1 Chronicles: 4.
- Judges: 3.
- Amos: 3.
- Deuteronomy: 2.

Caption emphasis:

> The book-level signal resolves into specific chapter regions, with Acts
> providing the largest number of preliminary hits and Hebrews showing high
> density.

### Table 2: The 16 Confirmed Chapter Movers

Purpose: name the main empirical objects of the paper.

Data:

- `key_data/chapter_confirmation_l40_survivors.csv`
- `key_data/chapter_stability_by_localization.csv`

Columns:

- Chapter target
- Biblical reference
- Book family
- Limit-40 control accuracy
- Limit-40 positive steering accuracy
- Negative-alpha accuracy
- Null-control accuracy
- Localization rescue count
- Best layer/alpha cell
- Brief biblical motif

The 16 confirmed chapters:

```text
Deuteronomy 16
Judges 7
Judges 9
Numbers 11
Numbers 22
Numbers 27
1 Chronicles 9
1 Chronicles 29
Acts 7
Acts 11
Acts 16
Acts 27
Hebrews 2
Hebrews 7
Hebrews 9
Hebrews 10
```

### Figure 4: Layer-Alpha Rescue Heatmap

Purpose: strongest technical figure.

Suggested form: grid heatmap where x-axis is alpha, y-axis is center layer, and
cell value is number of confirmed chapters rescued.

Data:

- `key_data/layer_alpha_expected_grid.csv`

Visual details:

- Highlight `L31 / alpha 96` with `12/16` rescues.
- Highlight `L31 / alpha 48` with `11/16` rescues.
- Highlight `L32 / alpha 32` with `11/16` rescues.
- Highlight `L24 / alpha 32` with `9/16` rescues and stronger average movement.
- Show `L36 / alpha 32` as zero.

Caption emphasis:

> The useful steering directions are layer- and strength-sensitive. The effect
> is concentrated in particular regions of the model rather than appearing
> uniformly across all tested layers.

### Figure 5: Breadth Versus Strength Tradeoff

Purpose: make the L24 vs L31/L32 result intuitive.

Suggested form: scatter plot.

Data:

- `key_data/layer_alpha_cells.csv`

X-axis:

- paired rescue count

Y-axis:

- mean positive delta

Label these cells:

- `L31 / alpha 96`: broadest.
- `L32 / alpha 32`: broad and stable.
- `L24 / alpha 32`: strongest average movement.

Caption emphasis:

> Some settings move fewer chapters more strongly, while others rescue more
> chapters with smaller average movement.

### Figure 6: Chapter Stability Across Layer-Alpha Cells

Purpose: show which chapters generalize across steering settings.

Suggested form: ranked horizontal bar chart.

Data:

- `key_data/chapter_stability_by_localization.csv`

Top chapters:

- Acts 11: 16 rescues.
- Acts 16: 12.
- 1 Chronicles 9: 11.
- Acts 7: 11.
- Hebrews 2, Numbers 27, Acts 27: 9 each.

Caption emphasis:

> Some chapter-derived vectors remain useful across many model settings, while
> others are more conditional.

### Figure 7: Chapter By Layer-Alpha Rescue Matrix

Purpose: show that alpha changes which chapters become useful.

Suggested form: binary heatmap.

Data:

- `key_data/chapter_x_layer_alpha_rescue_matrix.csv`

Rows:

- 16 confirmed chapters.

Columns:

- Layer-alpha cells, ordered by layer and alpha.

Interpretive target:

- L31/L32 broad cells rescue many chapters.
- Higher alpha does not simply mean "more of the same"; it changes the chapter
  mix.
- L32 at alpha 32, 48, 64, and 96 shows shifting chapter families.

Caption emphasis:

> Steering strength behaves less like a simple volume knob and more like a
> selector that can amplify different components of a chapter-derived vector.

### Table 3: Biblical Patterning Of The Confirmed Chapters

Purpose: keep the theological interpretation text-facing and serious.

Columns:

- Chapter
- Narrative/legal/priestly/exhortative setting
- Biblical justice motif
- Why it may matter for VirtueBench2 Justice
- Commentary checkpoint

Important instruction:

This table should read biblical justice on its own terms:

- righteous judgment
- covenantal order
- divine adjudication
- inheritance
- mediation
- vindication
- recompense
- ordered worship
- faithful testimony
- deliverance under divine rule

Do not reduce the chapters to modern justice vocabulary. Commentaries should be
consulted before final prose.

### Supplementary Table: Non-Survivors And Control Warnings

Purpose: make the controls visible without centering the paper on negatives.

Data:

- `key_data/book_confirmation_l40_all_candidates.csv`
- `key_data/chapter_confirmation_l40_all_candidates.csv`

Use this in the supplement or late Methods/Limitations section.

## Detailed Paper Structure

## 1. Introduction: A Searchable Scriptural Geometry

### Positive opening claim

Open with the idea that Scripture in model space can be studied as a structured
geometry. The paper discovers that particular biblical chapters produce
activation directions that move Justice behavior, and that those directions
have a measurable layer/strength profile.

Suggested opening paragraph:

> Scripture is not merely prompt text for a language model; it is also part of
> the model's learned internal geometry. This study asks whether that geometry
> can be searched. We show that chapter-derived biblical activation vectors can
> be discovered systematically across the canon, filtered under controls, and
> localized inside Qwen3-14B by layer and steering strength. The resulting
> Justice vectors are not evenly distributed across Scripture. They arise from
> specific chapters and behave differently at different model layers.

### What the introduction should accomplish

- Present the paper as a discovery study.
- Make the canon-wide search feel ambitious.
- Make chapter-level localization feel like the paper's main contribution.
- Set up Justice as the proof-of-concept target.
- Mention VirtueBench2 only after the main discovery question is clear.

### Suggested intro sequence

1. Prior ICMI work showed that Scripture can move virtue-related model behavior.
2. Prompt injection and book-level screens leave open where the useful signal
   lives.
3. Activation steering lets us test Scripture as an internal vector, not only
   as text in the prompt.
4. This paper runs a canon-wide search and finds specific chapter-level Justice
   vectors.
5. The confirmed chapters can be behaviorally localized: some layers/alphas
   work broadly, others move fewer chapters more strongly.

### Figure placement

Place **Figure 1: The Discovery Funnel** near the end of the introduction.

## 2. Prior Work: From Scripture Injection To Activation Steering

### Goal

Show that this paper grows naturally out of ICMI's prior work while adding a
new layer of resolution.

### Include

- VirtueBench2: the benchmark environment and ratio-stage challenge.
- Psalm injection papers: Scripture can affect virtue-evaluation behavior.
- GospelVec: theological/biblical material can be represented as steerable
  activation directions.
- ICMI-020, "Beyond the Psalm": all-66-book prompt injection shows that
  Scripture effects are canonically broad but uneven.
- Activation steering / CAA-style methods: internal directions can be added to
  model activations and tested behaviorally.

### Framing sentence

> Prior work establishes that Scripture can move model behavior; this paper
> asks how far that result can be resolved: from canon, to book, to chapter, to
> model layer.

### Avoid

Do not let this section become a defensive caveat section. Save theological and
methodological boundaries for Section 10.

## 3. Research Question And Claims

### Primary research question

> Can Scripture-derived activation vectors be discovered systematically across
> the biblical canon and localized to specific chapters, model layers, and
> steering strengths that improve Justice behavior on VirtueBench2?

### Primary empirical claim

> Yes. The study identifies 16 confirmed chapter-derived Justice movers and
> shows that their effects cluster around particular layer/alpha settings.

### Secondary claims

1. The search is selective: 66 books narrow to 19 preliminary book candidates,
   then 7 confirmed book sources.
2. Book-level effects localize to chapters: 7 confirmed book sources produce
   38 preliminary chapter hits, then 16 confirmed chapter movers.
3. Layer/alpha localization reveals structure: L31/L32 provide broad coverage,
   while L24 provides stronger movement.
4. The confirmed chapters are biblically meaningful but not always obvious by
   modern categories; their interpretation should be checked against major
   commentaries.

### Table placement

Place **Table 1: Study Pipeline And Decision Rules** here.

## 4. Methods: Building And Testing Scripture-Derived Vectors

### 4.1 Model And Benchmark

Include:

- Model: Qwen3-14B.
- Benchmark: VirtueBench2.
- Target virtue: Justice.
- Stage: ratio.
- Temperature: 0.0.
- Runs: 1 per condition.
- Screens: limit 10 for discovery/localization, limit 40 for confirmations.

Plain-English explanation:

> VirtueBench2 presents the model with moral-choice scenarios. The ratio stage
> is hard because it gives the model a plausible consequentialist reason for
> the wrong answer. Justice scoring asks whether the model chooses the
> justice-consistent option despite that rationalization.

### 4.2 Vector Construction

Explain that the study extracts internal activation directions from Scripture
corpora and applies those directions during benchmark answering.

Include:

- Extraction method: `scripture_contrast`.
- Runtime steering: positive Scripture direction.
- Negative-alpha control: same vector, opposite direction.
- Null-control steering: mismatched/null vector control.
- Window radius: 3 for localization extraction.
- Alpha candidates: `0.5,1.0,2.0,3.0,4.0,6.0,8.0`.

Plain-English explanation:

> The model is not being prompted with the biblical chapter during the benchmark
> answer. Instead, the chapter is used beforehand to estimate a direction in the
> model's hidden-state space. During the benchmark, the model is nudged along
> that direction.

### 4.3 Passing Rule

A candidate counts as a clean rescue when positive Scripture steering:

- improves over unsteered control,
- beats negative-alpha steering,
- beats null-control steering,
- shows paired answer movement in the right direction.

### 4.4 Artifact Paths

Point the writer to:

- `key_data/README.md`
- `key_data/scripturevec_key_results_rollup.json`
- `results/experiments/scripturevec14/`

## 5. Study 1: Canon-Wide Book Discovery

### Purpose

Search the whole canon before narrowing.

### Input

- All 66 biblical books from the bundled KJV corpus.

### Design

- Justice, ratio stage.
- Limit 10.
- Runtime alpha 32.
- Conditions: control, positive Scripture, negative-alpha, null-control.

### Result

The screen found 19 preliminary book-level Justice candidates.

Data:

- `key_data/book_discovery_l10_candidates.csv`

### Main prose emphasis

This is the first major weight-bearing move: the study begins broadly enough to
avoid hand-picking.

### Figure placement

This can be part of **Figure 1** or a small table in the Methods/Results flow.

## 6. Study 2: Book-Level Confirmation

### Purpose

Retest the 19 preliminary book candidates on a larger benchmark slice.

### Design

- Same model and controls.
- Limit 40.
- 19 candidates.

### Result

Seven book-level sources survive:

- 1 Chronicles
- Amos
- Deuteronomy
- Judges
- Numbers
- Acts
- Hebrews

Hebrews is the strongest book-level survivor, moving from `0.40` control to
`0.45` positive steering while negative-alpha and null controls remain at
`0.40`.

Data:

- `key_data/book_confirmation_l40_all_candidates.csv`
- `key_data/book_confirmation_l40_survivors.csv`

### Figure placement

Use **Figure 2: Book-Level Confirmation** here.

### Interpretation

The confirmed book set defines the source region for chapter discovery. It is
the bridge from all-canon search to localized biblical sources.

## 7. Study 3: Chapter-Level Discovery

### Purpose

Ask whether the confirmed book-level signal resolves into specific chapters.

### Input

Seven confirmed books:

- 1 Chronicles
- Amos
- Deuteronomy
- Judges
- Numbers
- Acts
- Hebrews

### Design

- 170 chapter targets.
- 952 verse-window rows.
- Justice, ratio stage.
- Limit 10.
- Runtime alpha 32.
- Same controls.

### Result

The chapter discovery screen finds 38 clean preliminary Justice hits:

- Acts: 14
- Hebrews: 6
- Numbers: 6
- 1 Chronicles: 4
- Judges: 3
- Amos: 3
- Deuteronomy: 2

Data:

- `key_data/chapter_discovery_l10_clean_hits.csv`

### Figure placement

Use **Figure 3: Chapter Discovery By Biblical Book** here.

### Main interpretive claim

The book-level signal sharpens into chapter-level structure. The results are
not just book names; they are concrete biblical loci.

## 8. Study 4: Chapter Confirmation

### Purpose

Lock the chapter result before doing layer localization.

### Design

- 38 preliminary chapter hits.
- Limit 40.
- Same controls.

### Result

Sixteen chapter-derived Justice movers survive:

- Deuteronomy 16
- Judges 7
- Judges 9
- Numbers 11
- Numbers 22
- Numbers 27
- 1 Chronicles 9
- 1 Chronicles 29
- Acts 7
- Acts 11
- Acts 16
- Acts 27
- Hebrews 2
- Hebrews 7
- Hebrews 9
- Hebrews 10

Data:

- `key_data/chapter_confirmation_l40_all_candidates.csv`
- `key_data/chapter_confirmation_l40_survivors.csv`

### Table placement

Use **Table 2: The 16 Confirmed Chapter Movers** here.

### Main interpretive claim

The confirmed set is diverse, but not random: it includes chapters where
Scripture narrates or teaches divine judgment, covenantal order, inheritance,
priestly mediation, testimony, public vindication, recompense, and deliverance.

## 9. Study 5: Layer And Alpha Localization

### Purpose

Determine where the confirmed chapter-derived vectors work inside the model.

### Input

The 16 confirmed chapter targets.

### Design

Layer centers:

```text
24, 28, 29, 30, 31, 32, 33, 36
```

Alpha values:

```text
16, 24, 32, 48, 64, 96
```

Focused grid:

- every center tested at alpha 32,
- centers 29, 31, and 32 receive the full alpha ladder.

Expected behavior cells: 23.  
Completed behavior cells in current packet: 23.

### Main results

- `L31 / alpha 96`: 12/16 paired rescues, broadest coverage.
- `L31 / alpha 48`: 11/16 paired rescues, nearly matching the broadest cell.
- `L32 / alpha 32`: 11/16 paired rescues.
- `L24 / alpha 32`: 9/16 paired rescues, largest mean positive delta.
- `L33 / alpha 32`: 2/16 rescues.
- `L36 / alpha 32`: 0/16 rescues.

Data:

- `key_data/layer_alpha_cells.csv`
- `key_data/layer_alpha_expected_grid.csv`
- `key_data/layer_alpha_target_rows.csv`

### Figure placement

Use:

- **Figure 4: Layer-Alpha Rescue Heatmap**
- **Figure 5: Breadth Versus Strength Tradeoff**

### Interpretation

This is the key mechanistic bridge:

> The chapter-derived Justice vectors work in specific layer/alpha regimes. The
> strongest behavioral movement and broadest chapter coverage are not identical
> settings, which suggests the steering direction is structured internally.

## 10. Chapter Stability And Differential Uptake

### Purpose

Show which chapters remain useful across many steering settings.

### Results

Most stable chapters in completed localization cells:

- Acts 11: 16 rescues.
- Acts 16: 12.
- 1 Chronicles 9: 11.
- Acts 7: 11.
- Hebrews 2: 9.
- Numbers 27: 9.
- Acts 27: 9.

Data:

- `key_data/chapter_stability_by_localization.csv`
- `key_data/chapter_x_layer_alpha_rescue_matrix.csv`

### Figure placement

Use:

- **Figure 6: Chapter Stability Across Layer-Alpha Cells**
- **Figure 7: Chapter By Layer-Alpha Rescue Matrix**

### Interpretation

This is where the paper can say something especially interesting:

> Alpha changes which chapters become useful. Larger pushes do not merely
> intensify the same effect; they can surface different components of the
> chapter-derived direction.

This is one of the best bridges to future SAE analysis.

## 11. Biblical Patterning Of The Confirmed Chapters

### Purpose

Interpret the chapter hits as biblical texts, not just target IDs.

### Main claim

The confirmed chapters cluster around biblical forms of justice:

- appointed judgment and ordered worship,
- divine adjudication,
- inheritance and right claim,
- public testimony,
- vindication,
- priestly mediation,
- covenant order,
- recompense,
- deliverance under divine rule.

### Preliminary chapter motif notes

Use this table as draft scaffolding, not final exegesis.

| Chapter | Preliminary biblical motif |
| --- | --- |
| Deuteronomy 16 | Appointed feasts, appointed judges, no partiality, no bribes, pursuit of what is just. |
| Judges 7 | Divine deliverance arranged so Israel cannot boast in its own strength. |
| Judges 9 | Usurpation, bloodshed, Jotham's parable, and recompense returning on violent rule. |
| Numbers 11 | Disorderly desire, Moses' burden, appointed elders, divine judgment and provision. |
| Numbers 22 | Balaam constrained by God's word against corrupt reward and false curse. |
| Numbers 27 | Daughters of Zelophehad bring a right claim; inheritance is adjudicated by the Lord. |
| 1 Chronicles 9 | Genealogical reckoning and restored priestly/gatekeeping order after exile. |
| 1 Chronicles 29 | David orders gifts and succession; all authority and wealth are received from God. |
| Acts 7 | Stephen's testimony, rejected deliverers, resistance to the Just One. |
| Acts 11 | Peter's ordered testimony, divine inclusion recognized, church relief according to ability. |
| Acts 16 | Unjust imprisonment, divine vindication, public accountability of magistrates. |
| Acts 27 | Paul's faithful witness under danger; preservation by divine promise. |
| Hebrews 2 | Recompense, deliverance from death, Christ as faithful high priest. |
| Hebrews 7 | Melchizedek, righteousness and peace, superior priesthood. |
| Hebrews 9 | Covenant, sanctuary, sacrifice, conscience, judgment, inheritance. |
| Hebrews 10 | Sacrifice fulfilled, conscience cleansed, judgment, endurance, living by faith. |

### Commentary requirement

Before publication, check these interpretations against major commentaries.
This should strengthen the paper, especially because some hits are surprising.

Recommended prose posture:

> The unexpectedness of some hits is part of the result. The model is not merely
> responding to obvious modern justice keywords; it appears sensitive to
> biblical scenes of order, adjudication, mediation, testimony, and recompense.

## 12. Mechanistic Implications

### Purpose

Explain why activation-space localization matters.

### Claims

1. The model contains internal directions associated with specific scriptural
   chapters.
2. Those directions can alter Justice behavior under controlled steering.
3. The behavioral effect is layer- and alpha-sensitive.
4. Different chapters become useful under different steering strengths.
5. This suggests a structured internal representation that can later be studied
   with SAE tools.

### SAE positioning

SAE analysis should be described as the natural next step, not as a completed
claim in this paper.

Suggested wording:

> The present study localizes the behavior. A future SAE study can ask which
> sparse features mediate these localized chapter effects.

## 13. Controls, Boundaries, And Limitations

This section should be clear, but it should not dominate the paper.

Include:

- Single model: Qwen3-14B.
- Single benchmark target: Justice.
- Ratio stage as the main slice.
- Limit-10 screens are discovery/localization, not final behavioral proof.
- Limit-40 confirmations carry more weight.
- Activation steering changes model behavior; it does not establish virtue,
  conscience, sanctification, personhood, or spiritual reception.
- The study measures model uptake of scriptural text under a specific
  intervention, not the theological worth or authority of biblical chapters.

### Tone guidance

Do not lead the paper with these limits. Put them here, after the discovery has
been established.

## 14. Conclusion

### Positive close

End by returning to the discovery pipeline:

> This study shows that Scripture-derived activation vectors can be searched
> systematically, resolved to chapter-level sources, confirmed under controls,
> and localized inside a model. The resulting map is structured: particular
> biblical chapters move Justice behavior in particular layer/alpha regimes.
> This opens a path from scriptural corpus discovery to mechanistic analysis of
> how models represent and respond to biblical moral form.

### Final sentence option

> The paper's central finding is not merely that Scripture can move a model, but
> that scriptural movement in activation space has discoverable structure.

## Appendix Recommendations

### Appendix A: Full Book Discovery Table

Use:

- `key_data/book_discovery_l10_candidates.csv`
- `key_data/book_confirmation_l40_all_candidates.csv`

### Appendix B: Full Chapter Confirmation Table

Use:

- `key_data/chapter_confirmation_l40_all_candidates.csv`

### Appendix C: Full Layer-Alpha Target Matrix

Use:

- `key_data/layer_alpha_target_rows.csv`
- `key_data/chapter_x_layer_alpha_rescue_matrix.csv`

### Appendix D: Artifact Manifest

List:

- original result summaries,
- generated compact data files,
- run design docs,
- scripts used for summarization.

## Data Packet Reference

All compact writer-facing data files are in:

```text
docs/scripturevec_paper_writing_packet/key_data/
```

Start with:

```text
docs/scripturevec_paper_writing_packet/key_data/README.md
docs/scripturevec_paper_writing_packet/key_data/scripturevec_key_results_rollup.json
```

Most important CSVs:

```text
book_confirmation_l40_survivors.csv
chapter_confirmation_l40_survivors.csv
layer_alpha_cells.csv
layer_alpha_expected_grid.csv
chapter_stability_by_localization.csv
chapter_x_layer_alpha_rescue_matrix.csv
```

## Writing Model Instructions

If giving this outline to another model, include these instructions:

1. Lead with the positive discovery.
2. Treat the paper as a structured discovery pipeline.
3. Use figures to make the funnel and localization pattern visually obvious.
4. Do not overuse disclaimers in the introduction.
5. Put controls and limitations in their proper sections.
6. Read biblical justice on its own terms before mapping it to modern
   categories.
7. Treat commentary checks as required before final theological interpretation.
8. Treat the 23-cell layer localization grid as complete.
