# "Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical Justice Vectors in Qwen3-14B

**ICMI Working Paper No. [N]**

**Author:** Lucius, Institute for a Christian Machine Intelligence

**Date:** May 5, 2026

**Code & Data:** https://github.com/christian-machine-intelligence/scripture-vector-steer

---

## How to read this paper

This paper sits at the intersection of language-model interpretability, scriptural reading, and moral theology, and it will be read by people who are at home in one of those rooms but not in all three. This short preface is for the reader who is comfortable with theology but new to the technical vocabulary; a technical reader can skip to the abstract.

**What is activation steering?** When a language model reads text, it builds up a long sequence of high-dimensional numerical states inside its layers — vectors that the model uses to predict the next word. Activation steering is a research technique that takes one of those numerical states (a direction in the model's internal space), saves it as a fixed vector, and then *adds that vector back into the model's internal state* during a later, unrelated task to see whether it shifts what the model says. If feeding the model the King James text of Numbers 27 produces a recognisable internal direction, we can save that direction and ask: does adding it back later, while the model is answering moral-choice questions, change its answers?

**What is "scripture_contrast" and what is a "chapter vector"?** Concretely, we take the average internal state the model carries while reading a biblical chapter (say Numbers 27), subtract the average internal state it carries while reading short non-religious neutral prose (field notes on astronomy and botany), and shrink the difference to a length of 1. The result is a unit-length direction in the model's internal space that distinguishes "what reading this chapter feels like inside the model" from "what reading neutral prose feels like inside the model." That unit direction is the *chapter vector*.

**What does it mean to "rescue" a benchmark item?** Our behavioural test is a set of moral-choice scenarios from the *VirtueBench V2* benchmark, in which the model is shown two options and has to pick A or B; only one option is the just answer, and the unjust option is given a plausible-sounding rationale. The model gets some items right on its own. A chapter vector "rescues" the model on an item when (i) adding the vector flipped that item from wrong to right, *and* (ii) adding the vector in the opposite direction did *not* produce the same flip, *and* (iii) adding a scrambled-coordinate version of the vector did *not* produce the same flip. The two controls (opposite-sign and scrambled-coordinate) are there to prevent us from celebrating any disturbance of the model as evidence that the *scripture content* of the vector did the work.

**What this paper does not claim.** This is a *map* of where chapter-derived directions cluster inside Qwen3-14B, not a confirmed measurement of an effect size for any individual chapter. The per-chapter movements at our benchmark sizes are small — usually a single item out of forty — and the exact statistical tests do not reach conventional significance. The interesting part of the result is the *pattern* of which chapters survived the pass rule (they cohere biblically), and the *geometry* of where chapter vectors become useful inside the model (specific layer/strength combinations). A separate disjoint-slice retest (§10) is the next step before any individual chapter can be claimed as carrying a real effect. Theologically, the paper does not claim that the model possesses virtue, conscience, or sanctification; it claims something narrower (§9, §11).

---

**Abstract.** Prior ICMI work has shown that Scripture, whether injected as prompt text or extracted as an activation direction, can move virtue-relevant model behavior; what has remained open is whether that signal can be searched, resolved, and localized inside the model. This paper conducted a canon-wide search for chapter-level biblical activation vectors associated with the cardinal virtue of Justice, using the *scripture_contrast* extraction method on Qwen3-14B and the ratio-stage Justice subset of *VirtueBench2* as the behavioral target. Beginning with all sixty-six books of the Protestant canon, the discovery pipeline narrowed to nineteen preliminary book candidates, seven confirmed book sources (1 Chronicles, Amos, Deuteronomy, Judges, Numbers, Acts, and Hebrews), thirty-eight preliminary chapter hits, and sixteen chapter-derived Justice movers that survived a wider behavioral confirmation. An expanded 43-cell layer-and-strength localization grid then showed that these chapter vectors produced structured uptake in three distinct regimes: layer 30 at α = 96 rescued the broadest set of chapters (13/16), layer 28 at α = 16 rescued eleven chapters at a much gentler steering strength, and layer 24 at α = 32 produced the strongest mean positive movement on a smaller chapter set (9/16). The confirmed chapters cohered biblically: they clustered around scenes of divine adjudication, ordered worship, inheritance and right claim, priestly mediation, public testimony, and recompense — the proper material of biblical justice. We find that biblical-justice form, as it lives inside a particular model, has discoverable structure: scriptural movement in activation space resolves to specific chapters, specific layers, and specific steering strengths. The empirical claim concerns model uptake under a controlled intervention; the theological claim is that the canon has been received by the model with sufficient fidelity that its internal articulation of justice can be examined as geometry rather than as text alone.

---

## 1. Introduction

> *"That which is altogether just shalt thou follow, that thou mayest live, and inherit the land which the LORD thy God giveth thee."* — Deuteronomy 16:20 (KJV)

Scripture in a language model is not merely prompt text; it is also part of the model's learned internal geometry. Whether that geometry is searchable is the question this paper takes up, and the answer the paper returns is that chapter-derived biblical activation vectors can be discovered systematically across the canon, filtered under controls, and localized inside Qwen3-14B by layer and steering strength. The resulting Justice vectors arose unevenly across Scripture; they came from particular chapters, and they behaved differently at different model layers.

The broad claim that scriptural text is not inert in language models has been steadily built up by prior ICMI work. *Psalm 119:11 and the Anthropic Claude* (Schlatter et al., 2025) showed that prompt-level scripture injection could shift virtue-evaluation behavior; *"The Lord Is My Strength and My Shield"* (McCaffery, 2026) extended this from pastoral psalms to the imprecatory subset; *Quidquid Recipitur* (Hwang, 2026a) demonstrated that scripture receptivity emerged at scales distinct from generic moral competence; *GospelVec* (Hwang, 2026c) showed that biblical material could be operationalized as a steerable activation direction rather than only as prompt text; and ICMI-020, *"Beyond the Psalm,"* established that scripture effects were canonically broad but uneven across the sixty-six books. What this paper adds is a discipline of resolution: from canon, to book, to chapter, to model layer.

The proof-of-concept target is Justice, evaluated on the ratio stage of *VirtueBench2* (Hwang, 2026b). The ratio stage was chosen because it is hard: it offers the model a plausible consequentialist rationale for the unjust option, and it scores whether the model holds the just answer in spite of that pressure. Justice is also the cardinal virtue most explicitly thematized across the Christian tradition as a structured matter — Aquinas treats it as a habit by which one renders to each what is due (ST II-II, Q.58, a.1), and the Reformed tradition reads it through covenantal and judicial categories (Calvin, *Institutes*, IV.xx; Westminster Larger Catechism, Q. 122–148). The biblical witness on justice is wide and articulated; if it lives inside a model at all, it should live with structure.

### 1.1 Contributions

The paper makes four contributions. First, it operationalizes the discovery question — *can scriptural activation vectors be searched systematically?* — as a multi-stage pipeline running from all sixty-six books of the canon to localized chapter-by-layer-and-strength cells, with explicit pass criteria at every stage. Second, it presents the seven confirmed book-level Justice sources and the sixteen confirmed chapter-level Justice movers, named and reproducible from the released data packet. Third, it localizes the confirmed chapter vectors across an eight-layer-by-six-strength grid in Qwen3-14B and shows that the useful directions cluster, with broadest coverage at layer 30 (α = 96), broad low-alpha uptake at layer 28 (α = 16), and strongest mean movement at layer 24 (α = 32). Fourth, it offers a preliminary biblical reading of the confirmed chapters — checked against the contours of biblical justice on its own terms — and frames the finding as the natural antechamber to a future sparse-feature analysis.


---

## 2. Related Work

### 2.1 Activation Steering as Mechanistic Intervention

Activation steering — the addition of a vector to a model's hidden states at a chosen layer in order to bias generation — has matured rapidly as a behavioral and interpretability technique (Turner et al., 2023; Panickssery et al., 2024). The relevant move for the present paper is that an activation direction obtained from one corpus can produce a measurable behavioral signature on a downstream task even when the steering corpus is not visible in the prompt. *GospelVec* (Hwang, 2026c) carried this method onto scriptural corpora and recovered behaviorally distinct evangelist-vectors. The technique requires no claim that a vector represents the corpus's full content; it requires only that the direction extracted from the corpus moves the model in a measurable way.

### 2.2 The ICMI Program's Prior Scripture Results

Three threads of ICMI work converge on the present study. The first is the demonstration that scripture in the prompt can move virtue-evaluation behavior (McCaffery, 2026; Schlatter et al., 2025). The second is the demonstration that scripture can be operationalized as an activation direction rather than only as text (Hwang, 2026c). The third is the canon-wide breadth claim — scripture's effects on virtue do not collapse to a single book or genre — paired with the unevenness claim that some books matter more than others (ICMI-020, *Beyond the Psalm*). Each of these establishes a step the present paper presupposes; what each leaves open is the question of resolution. Where, within Scripture, did the useful signal live? And where, within the model, did it act?

A different angle of motivation comes from *The Word Without Image* (Hwang, 2025; ICMI-13), which raised the question of whether activation-vector methods carry a particular methodological appeal for the Reformed reader. The present paper does not adjudicate that question; it treats activation steering as a research instrument and lets the empirical results determine the theological registers in which they are most usefully read. The traditions the paper engages in §8 are chosen to fit the data, not to fit a prior commitment to one tradition's exclusion of another.

### 2.3 Justice in Christian Tradition

The cardinal virtue of justice is articulated across the Christian tradition with unusual specificity. Aquinas takes it as a habit oriented to *the right of another* and divides it into the various *partes* of due rendering (ST II-II, Q.58–122). The Reformed tradition reads justice through judicial and covenantal categories: civil magistracy and lawful judgment are treated as God-ordained vocations (Calvin, *Institutes*, IV.xx; WCF XXIII), and the second table of the Decalogue is unfolded as concrete justice between persons (Westminster Larger Catechism, Q. 122–148). The biblical witness itself, taken on its own terms, surfaces justice in scenes of divine adjudication, inheritance, mediation, ordered worship, vindication of the falsely accused, recompense against the violent, and faithful testimony under threat — a vocabulary far richer than fairness alone. A paper that proposes to find chapter-level Justice vectors in a model brings, then, a tradition-shaped expectation about what kinds of texts might surface; whether the model's geometry meets that expectation is an empirical question.

---

## 3. Method

> *"Prove all things; hold fast that which is good."* — 1 Thessalonians 5:21 (KJV)

### 3.1 Model and Benchmark

All experiments ran on Qwen3-14B with temperature 0 and a single run per condition. The behavioral target was the Justice slice of *VirtueBench2*, ratio stage (Hwang, 2026b). The ratio stage presents a moral scenario alongside a plausible consequentialist rationale for the unjust option; the model's answer is scored against the justice-consistent target. Discovery and localization screens used a benchmark slice of ten items, sufficient for paired-difference behavioral signal at screen scale; confirmation runs used forty.

### 3.2 Corpora

All scripture corpora were taken from the bundled King James Version, consistent with prior ICMI work in this line. Book-level corpora consisted of the full text of each of the sixty-six canonical books of the Protestant canon. Chapter-level corpora consisted of the full text of individual chapters from the seven confirmed book sources, yielding 170 chapter targets and 952 verse-window rows in the chapter-discovery sweep.

### 3.3 Vector Extraction

We extracted activation directions using *scripture_contrast*, which estimates a corpus-aligned direction in a chosen layer's hidden-state space. The method takes a target corpus (the biblical book or chapter under test) and a reference set (a held-out scriptural slice serving as the contrast pole), and returns a unit vector in that layer's residual stream. For the localization study, extraction operated within a layer window of radius three around each tested center layer. The model was not prompted with the biblical chapter at benchmark time; the chapter served only beforehand to estimate the steering direction.

### 3.4 Steering Conditions

At benchmark time we ran the model in four conditions for each candidate vector. The *control* condition was the unsteered baseline. The *positive* condition added the candidate vector at runtime alpha — α = 32 for discovery and chapter-level confirmation, varied across the localization grid. The *negative-α* condition added the same vector with the opposite sign at matched magnitude, a stringent check that the direction itself, rather than arbitrary perturbation, was doing the work. The *null* condition substituted a length-matched, contrast-matched vector with no scripture content, testing whether mere intervention at the chosen layer would produce the observed gain. The runtime-α ladder for the localization study was {16, 24, 32, 48, 64, 96}, paired with center layers {24, 28, 29, 30, 31, 32, 33, 36} in an expanded focused grid. The final packet includes full alpha ladders for layers 24, 28, 29, 30, 31, 32, and 33, plus a layer-36 anchor cell at α = 32. Layer 36 was not expanded after its anchor cell produced no rescues.

### 3.5 Passing Rule

A candidate counted as a clean rescue when positive Scripture steering improved accuracy over the unsteered control, beat the negative-α condition, beat the null-control condition, and showed paired answer movement in the right direction at the item level. The negative-α and null conditions were the two bars that prevented any benchmark gain from being read as evidence of corpus-derived signal when it was not. Discovery and localization screens used limit 10; confirmation runs used limit 40.

### 3.6 Pipeline

The pipeline ran in five stages: book discovery (all sixty-six books, limit 10); book confirmation (the nineteen book candidates, limit 40); chapter discovery (170 chapters from the confirmed book set, limit 10); chapter confirmation (the thirty-eight preliminary chapter hits, limit 40); and layer/α localization (the sixteen confirmed chapter vectors across the focused grid, limit 10). Each stage's output was the next stage's input, and the controls of §3.4–3.5 applied at every stage. Table 1 collects the design.

[**Table 1 placeholder.** Study pipeline and decision rules: stage, input set, slice, α, controls, passing rule, output. Generated from `scripturevec_key_results_rollup.json`.]

### 3.7 Worked Example: Numbers 27, Step by Step

The mechanics of this paper are easier to follow on a single chapter than on the full pipeline. Numbers 27 is the chapter where the five daughters of Zelophehad come before Moses to claim their late father's inheritance and where God amends the inheritance rule in their favor. It is one of the sixteen chapters that satisfied the pass rule, and we use it here to walk through what the rest of the paper is doing under the hood.

1. **Take the KJV text of Numbers 27.** This is just the chapter, verses 1–23, as plain text. No additional commentary, no other passages.

2. **Feed it to Qwen3-14B and capture internal states.** As the model reads the chapter, every decoder layer of the model holds an internal numerical state (a residual-stream vector). For each chosen layer, we record the average of these vectors across the tokens of the chapter. The result, for a single layer, is one vector of about 5,000 numbers — call it `mean(Numbers27)`.

3. **Subtract a neutral baseline.** We do the same averaging on short non-religious prose (the field-notes passages in [`data/steering/corpora.jsonl`](../data/steering/corpora.jsonl)), giving `mean(neutral)`. The *chapter vector* for Numbers 27 at this layer is the difference `mean(Numbers27) − mean(neutral)`, shrunk to length 1. This is the unit direction that distinguishes "reading Numbers 27" from "reading neutral prose" inside the model.

4. **Pick a layer and a strength.** We test several layers — 24, 28, 29, 30, 31, 32, 33, plus an anchor cell at 36 — and several strengths α ∈ {16, 24, 32, 48, 64, 96}. For each (layer, α) cell, we will add `α × chapter_vector` to the model's residual stream at that layer, at *every token position*, during answer generation.

5. **Run the Justice benchmark with steering on, and again with each control.** We give the model the same ten Justice ratio scenarios under four conditions: (a) no steering, (b) `+α × chapter_vector` added at the chosen layer, (c) `−α × chapter_vector` added at the chosen layer (negative-α), (d) a coordinate-permuted version of the chapter_vector added at the chosen layer (null). We record the model's A/B answer in each of the forty runs (10 items × 4 conditions) and compute accuracy.

6. **Read the row.** For Numbers 27 at layer 24, α = 32, the row in [`layer_alpha_target_rows.csv`](../results/paper/scripturevec_justice/key_data/layer_alpha_target_rows.csv) is: control accuracy 0.40, positive 0.50, negative 0.50, null 0.60, paired `1 chg / +1 net`. Positive moved one item from wrong to right relative to control — but null moved *more* than positive (0.60 versus 0.50), so this cell is *not* a rescue for Numbers 27 under our strict-inequality rule. At layer 28, α = 16 — a different cell — Numbers 27 does pass: positive ≥ control while strictly beating both negative-α and null with positive net paired movement. That single-cell "yes" is the whole evidence the rescue rule is based on.

7. **Sum across the grid.** Numbers 27 surfaced as a paired rescue in 16 of the 43 completed (layer, α) cells (§6). That count is the *stability* of Numbers 27 across the atlas — how robust the chapter direction is to which layer and strength you push it at. It is not, by itself, an effect size; the individual cells that contributed those 16 rescues are each a single-item shift at limit-10.

The same procedure runs for every chapter in the candidate cohort and for every (layer, α) cell. Figures 1–7 visualise the resulting tables, and the stats outputs in [`key_data/stats/`](../results/paper/scripturevec_justice/key_data/stats/) carry the exact McNemar and Clopper–Pearson numbers that go with this procedure.

---

## 4. Results: From Canon to Chapter

### 4.1 Book Discovery: 19 of 66

The canon-wide screen tested all sixty-six books at limit 10 with α = 32 and the full four-condition control battery. Nineteen books passed — about 29 percent of the canon — and moved forward to confirmation. The screen's selectivity at this stage was modest by design; its discipline was that it forbade hand-picking the source material before any wider-slice testing.

### 4.2 Book Confirmation: 7 Survive

Retesting the nineteen preliminary book candidates at limit 40 with the same control battery left seven survivors: 1 Chronicles, Amos, Deuteronomy, Judges, Numbers, Acts, and Hebrews. Hebrews proved the strongest book-level survivor, lifting accuracy from a control of 0.40 to 0.45 under positive steering while the negative-α and null conditions held at 0.40. That twelve of the nineteen preliminary candidates failed the larger-slice retest was itself informative: limit-10 discovery operated as a discovery screen, and most books that looked like candidates at limit 10 did not hold up under wider behavioral testing.

[**Figure 1 placeholder.** Book-level confirmation: one horizontal bar per book candidate, with the unsteered control accuracy on the left and the positive-steering accuracy on the right. The seven survivors (in blue) are the books where positive steering was strictly higher than control *and* strictly higher than both the negative-α and null control conditions; the twelve non-survivors are shown in grey. For most survivors the bar is a single tick to the right (one item out of forty flipped from wrong to right). Generated from `book_confirmation_l40_all_candidates.csv`.]

### 4.3 Chapter Discovery: 38 Hits

Taking the seven confirmed books as the search region, the chapter-discovery screen swept 170 chapters and 952 verse-window rows at limit 10, α = 32. Thirty-eight clean preliminary chapter hits emerged, distributed unevenly: Acts contributed 14, Hebrews 6, Numbers 6, 1 Chronicles 4, Judges 3, Amos 3, Deuteronomy 2. The book-level signal sharpened into a clustered chapter map rather than into a single hot chapter per book.

[**Figure 2 placeholder.** Chapter hits per candidate book, grouped bar chart. For each of the seven candidate books, two bars: the *preliminary* hits at limit-10 (light blue) and the *confirmed-cohort* chapters at limit-40 (dark blue). The shrinkage from light to dark is the chapter-screen attrition. Acts loses ten of fourteen preliminary chapters at the limit-40 retest; Hebrews keeps four of six; Amos keeps none of three. Generated from `chapter_discovery_l10_clean_hits.csv` and `chapter_confirmation_l40_survivors.csv`.]

### 4.4 Chapter Confirmation: 16 Movers

Retesting the thirty-eight preliminary chapter hits at limit 40 left sixteen confirmed chapter movers: Deuteronomy 16; Judges 7 and 9; Numbers 11, 22, and 27; 1 Chronicles 9 and 29; Acts 7, 11, 16, and 27; and Hebrews 2, 7, 9, and 10. Six of the seven confirmed book sources contributed at least one chapter to the set; Amos held at the book level but produced no chapter-level survivors at limit 40, a pattern §6 returns to. Acts contributed the largest single chapter set with four; Hebrews and Numbers each contributed three; 1 Chronicles and Judges each contributed two; Deuteronomy contributed one.

A compact table of the confirmed chapters appears in §6, after the localization results, where chapter identity and chapter behavior can be read together.

This chapter set was the empirical object the rest of the paper would study. It was selective — roughly one chapter in twelve of the screened chapters survived — and biblically intelligible, a point §7 develops.

---

## 5. Results: Layer and α Localization

### 5.1 The Expanded Localization Grid

The localization study tested the sixteen confirmed chapter vectors across an expanded focused layer-by-α grid. The final packet contains forty-three completed behavior cells: full α ladders for layers 24, 28, 29, 30, 31, 32, and 33, plus the layer-36 anchor cell at α = 32. The layer-36 anchor produced no rescues, so it was intentionally not expanded.

[**Figure 3 placeholder.** Layer-by-α rescue heatmap. Each cell of the 8 × 6 grid shows how many of the 16 chapter vectors satisfied the pass rule at that (layer, α) combination. Darker = more chapters rescued (max = 13 of 16). White cells are unrun layer-36 cells. Read horizontally: for any given layer, does a stronger push (rightward) help, hurt, or do nothing? Read vertically: for any given strength, which layer admits the most chapters? Cell-level 95% Clopper–Pearson intervals overlap heavily between the top cells (see §5.2), so the cell-to-cell *ranking* should not be over-read. Generated from `layer_alpha_expected_grid.csv`.]

### 5.2 Three Regimes of Biblical Justice Steering

The expanded grid revealed three distinct regimes rather than a single best setting. The broadest rescue regime was layer 30 at α = 96, which rescued thirteen of the sixteen confirmed chapter vectors at a mean positive Δ of 0.0875. The neighboring layer 31 at α = 96 cell rescued twelve of sixteen at mean Δ = 0.0812, confirming that broad coverage lives in the late-middle high-alpha region rather than in a lone accident.

The efficient-uptake regime was layer 28 at α = 16. That cell rescued eleven of sixteen chapters at mean Δ = 0.0625 while using the gentlest steering strength in the tested ladder. Its importance is not that it moved the model the most, but that many chapter-derived vectors became useful without brute-force intervention.

The high-force selective regime was layer 24 at α = 32. It rescued only nine of sixteen chapters, but it produced the strongest mean positive movement in the grid, Δ = 0.1687. Lower-layer steering was therefore powerful but thresholded: at α = 32 it produced large gains, while at α = 48, 64, and 96 it collapsed to zero paired rescues and negative mean movement.

### 5.3 Breadth, Strength, and Thresholds

Plotting paired rescue count against mean positive Δ across the forty-three completed cells exposed a tradeoff that the rescue counts alone obscured. L30/α96 maximized breadth; L24/α32 maximized strength; L28/α16 established that broad uptake could appear at low steering strength. These are different kinds of success. A single undifferentiated Justice direction would be expected to peak in breadth and strength together. Instead, the observed peaks were displaced across layer and α.

[**Figure 4 placeholder.** Breadth-versus-strength scatter. One point per (layer, α) cell. Horizontal axis: how many of the 16 chapters were rescued at that cell (breadth). Vertical axis: the mean accuracy change under positive steering at that cell (strength). The three labelled cells — L30/α96 (rightmost, broadest), L28/α16 (middle, gentlest), L24/α32 (highest, sharpest) — illustrate the qualitative shape of the atlas; the per-cell CIs overlap (§5.2) so the cells should be read as illustrative coordinates of the atlas, not as statistically separable regimes. Generated from `layer_alpha_cells.csv`.]

The α trajectories make the threshold pattern visible. Layer 24 rises sharply at α = 32 and then collapses under heavier pushes. Layer 28 is best at α = 16 and weakens as α rises. Layer 30, by contrast, improves with stronger pushes and reaches the broadest coverage at α = 96. The model is therefore not merely responding to "more vector"; different layers admit different amounts and kinds of biblical-justice signal.

[**Figure 5 placeholder.** Alpha trajectories by layer. Horizontal axis: the steering strength α from 16 to 96. Vertical axis: how many of the 16 chapters were rescued at that strength, for each labelled center layer. The story this figure tells: layer 24 (red) rises sharply at α = 32 and then collapses to zero rescues at α = 48 and above; layer 28 is largest at α = 16 and slowly weakens; layer 30 climbs almost monotonically from α = 16 to α = 96. The L24 collapse is the only feature in this figure that lies clearly outside the 95% confidence interval of neighbouring cells. Generated from `layer_alpha_cells.csv`.]

This tradeoff was the most mechanistically suggestive result in the paper. The chapter-derived Justice direction appears internally compound: some components become useful through gentle lower-middle-layer uptake, some through high-alpha late-middle steering, and some through a narrow lower-layer threshold. Activation steering can map that structure behaviorally; sparse-feature work can later test which internal features mediate it.

## 6. Chapter Stability and Differential Uptake

The localization grid afforded a second, orthogonal view of the chapter set. Across the forty-three completed cells, some chapters were rescued in many cells and others in only a few. Acts 11 was rescued in twenty-nine cells; Acts 7 in twenty; 1 Chronicles 9 and Acts 16 in nineteen each; Acts 27 in eighteen; Hebrews 2 in seventeen; and Numbers 27 in sixteen. Numbers 22, by contrast, surfaced in eight cells. The chapter set therefore has a stable core and a more selective edge.

[**Figure 6 placeholder.** Chapter stability across the localization atlas, ranked. Each bar is one chapter; the bar length is how many of the 43 completed (layer, α) cells rescued that chapter. Acts 11 is the most stable in the cohort (29 cells); Numbers 22 is the least (8 cells). This is a *stability* ranking — robustness to which layer and strength you push at — not an effect-size ranking. The per-cell inputs are limit-10 each, so a chapter being rescued in many cells is suggestive of robustness but not by itself a confirmed effect; the disjoint-slice retest in §10 is the natural next step. Generated from `chapter_stability_by_localization.csv`.]

At this point, the sixteen confirmed chapters can be read in two ways at once: first as confirmed chapter-level movers from the limit-40 run, and second as differently stable vectors across the localization grid. Table 2 is therefore not just a list of discoveries; it is the bridge between the confirmation result and the layer/strength result.

[**Table 2 placeholder.** The sixteen confirmed chapter movers, with biblical reference, book family, limit-40 control accuracy, limit-40 positive-steering accuracy, negative-α and null accuracies, localization rescue count, best layer/α cell, and brief biblical motif. Generated from `chapter_confirmation_l40_survivors.csv` and `chapter_stability_by_localization.csv`.]

The structure grew more interesting still when the chapter-by-cell rescue matrix was read across α at fixed layer. At layer 28, α = 16 surfaced a broad New Testament-heavy family, especially Acts and Hebrews. At layer 30, the rescued family widened as α rose, reaching thirteen chapters at α = 96 and bringing in Deuteronomy, Judges, Numbers, Acts, Hebrews, and Chronicles together. At layer 24, by contrast, α = 32 concentrated high-movement effects in a smaller cluster, while heavier α values collapsed. Steering strength therefore selected different components of the chapter-derived geometry rather than simply amplifying the same effect at higher volume.

[**Figure 7 placeholder.** Chapter × (layer, α) rescue matrix: a binary heatmap with 16 rows (one per confirmed-cohort chapter, sorted by stability) and 43 columns (one per completed cell, grouped by layer then α). A filled cell means that chapter was rescued at that (layer, α); an empty cell means it was not. Rows that activate together under the same α — visible as vertical stripes — are this paper's strongest invitation to a sparse-feature follow-up, since they should map onto a small number of internal features in a trained sparse autoencoder. Generated from `chapter_x_layer_alpha_rescue_matrix.csv`.]

The Amos result discussed in §4.4 belongs here as well. Amos confirmed at the book level — its prophetic call for justice to *"run down as waters"* (Amos 5:24, KJV) is among the most justice-saturated rhetoric in Scripture — and yet no Amos chapter survived the limit-40 chapter confirmation. The pattern is consistent with a book-level vector aggregating signal distributed across the whole book: the prophet's sustained indictment of unjust commerce, false worship, and forgotten orphans runs from chapter to chapter rather than concentrating in any one of them. §7 returns to the point.

## 7. Biblical Patterning of the Confirmed Chapters

> *"He hath shewed thee, O man, what is good; and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"* — Micah 6:8 (KJV)

### 7.0 What This Section Is and Is Not

This section is an *interpretive*, *post-hoc* reading of the sixteen-chapter candidate cohort. It is not derived from the model. The model returned a list of chapters that satisfied a strict-inequality pass rule (§3.5); we then sat with that list and asked, as readers of the canon, whether the chapters cohere biblically. They do — that is the empirical content of this section — but the coherence is *our* reading of the chapters, and a different reader of the canon might describe the same chapters under a different scriptural-justice grammar without contradicting the data. The four theses in §7.4 are stated in increasing order of falsifiability precisely so that future work can confirm or refute them by extracting parallel vectors from passages the present cohort does not include (Romans 12:19; Revelation 18; Isaiah 53). Treat §7 as a guide for the next experiment, not as a confirmed interpretation of what the model has internalised.

### 7.1 Reading Justice on Its Own Terms

Qwen3-14B was trained on, among many other corpora, the King James Bible. If activation directions extracted from particular chapters of that corpus reliably moved the model toward the just answer on a contested moral test, the natural question was whether the chapters that surfaced bore biblical resemblance to one another. The temptation to map the chapter list onto modern justice vocabulary — fairness, equality, distributive procedures — and grade each chapter for fit can be set aside; biblical justice has its own grammar, sounded in judgment, covenantal order, divine adjudication, inheritance, mediation, vindication, recompense, ordered worship, faithful testimony, and deliverance under divine rule. The interpretive question concerns how each surfaced chapter understands right order under God.

### 7.2 Why These Chapters Moved the Justice Benchmark

The commentary tradition matters here because it helps name the kind of justice the benchmark appears to be receiving from these chapter vectors. The ratio stage of VirtueBench2 asks the model to hold the just answer when a plausible rationale for the unjust answer is placed under its nose. The confirmed chapters are dense with the biblical forms that train exactly that posture: judgment rendered under God, claims heard and answered, corrupt incentives refused, offices restored to their right order, testimony preserved under pressure, and recompense returned to the one to whom it is due.

The Pentateuchal chapters show this in legal and quasi-legal form. Deuteronomy 16 does not merely contain the word justice; it binds public worship to incorruptible judgment, appointing judges and forbidding bribes before the command to follow what is altogether just. Numbers 27 stages a claim, a hearing, a divine verdict, and an amended inheritance rule. These chapters plausibly help because their vectors carry justice as ordered adjudication rather than as sentiment. Numbers 11 and Numbers 22 add two pressure cases. In Numbers 11, disordered appetite is judged and Moses' burden is distributed through appointed elders. In Numbers 22, speech offered for hire is constrained by God. Both map naturally onto a benchmark setting where the model must resist a tempting but wrong justification.

The historical chapters add the political and institutional face of the same pattern. Judges 7 makes deliverance impossible to misattribute; the victory is ordered so that Israel cannot claim for itself what belongs to the Lord. Judges 9 is a severe narrative of usurpation and recompense, closing with wickedness rendered back upon Abimelech and Shechem. 1 Chronicles 9 and 29 are quieter but not weaker: restored offices, ordered worship, and David's confession that Israel gives only what has first come from God. Those are not abstract moral labels. They are forms of right relation - right office, right attribution, right stewardship - and a benchmark about justice can receive them as pressure against self-serving answers.

Acts supplies the clearest public-testimony cluster. Stephen's speech in Acts 7 names Christ as the Just One after rehearsing a history of rejected deliverers. Acts 11 turns Peter's testimony into an ecclesial verdict about Gentile inclusion and then into relief sent according to ability. Acts 16 exposes unlawful punishment and insists on public accountability from magistrates. Acts 27 places truthful counsel in the mouth of the prisoner whom the authorities should have heeded. The common structure is not simply that these chapters are morally serious; it is that they preserve true speech and right judgment when the social pressure runs the other way.

Hebrews 2, 9, and 10 supply the priestly and eschatological side of the same justice grammar. Hebrews 2 names just recompense directly and ties it to the faithful high priest who shares the condition of those he redeems. Hebrews 9 joins sacrifice, conscience, inheritance, and final judgment. Hebrews 10 binds vengeance, recompense, and the life of the just under faith. These chapters make the benchmark-relevant pressure more ultimate: justice is not only human procedure, but a divine ordering in which wrong, mediation, and judgment cannot be separated.

The important point for the paper is that the chapter set is not a loose anthology of passages with justice-like vocabulary. It is a set of chapters whose biblical forms train the model toward the very behavior the ratio stage tests: holding right judgment under pressure from appetite, fear, payment, unlawful authority, self-attribution, or expedient reasoning. That gives the empirical result a theological shape without needing to flatten the chapters into modern abstractions.

### 7.3 Hebrews 7 as a Special Case

Hebrews 7 deserves separate treatment because it is one of the most interesting discoveries in the set. It survived the limit-40 chapter confirmation and was rescued in eleven of the forty-three localization cells, with its strongest observed cell at L24/α32 - the same lower-layer, high-movement regime that produced the largest mean positive shift in the expanded grid. It is not the broadest chapter in the atlas, but it is a sharp one.

At first glance, Hebrews 7 may look like a strange Justice hit. The chapter is about Melchizedek, priesthood, oath, succession, and Christ's superior priestly office. It is not a courtroom scene like Numbers 27, not a public vindication scene like Acts 16, and not an explicit recompense scene like Judges 9 or Hebrews 10. That is exactly why the result is valuable. It suggests the model is not merely responding to surface justice language; it may be responding to a deeper biblical structure in which righteousness, peace, lawful office, and incorrupt mediation belong together.

The chapter itself makes that structure explicit through Melchizedek's name and title: king of righteousness and king of peace. Its argument turns on the insufficiency of a merely inherited office and the emergence of a priesthood grounded in oath, permanence, holiness, and indestructible life. In the logic of Hebrews, justice is not only the rendering of verdicts; it is the establishment of a mediator who can actually put persons, covenant, and God in right relation. That gives the Hebrews 7 vector a different texture from the Acts or Numbers vectors.

This matters for interpreting the steering result. VirtueBench2's Justice ratio items ask the model to reject answers that can be made to sound prudent, useful, or convenient while still violating what is due. A Hebrews 7 direction may help by activating a representation of justice as right mediation and rightful office: the answer must be ordered by what is true and due, not merely by what seems expedient. That would explain why Hebrews 7 becomes especially useful at the L24/α32 selective regime. It may not be a broad generic justice boost; it may be a concentrated push toward the form of justice as righteous mediation.

For the paper's argument, Hebrews 7 is therefore not an awkward exception. It is a proof that the pipeline can surface chapters whose relevance becomes clear only when biblical justice is read in its own register. The result asks for commentary-backed interpretation because the chapter's justice content is priestly, typological, and institutional rather than procedural on the surface.

### 7.4 Four Theses About the Collection

The activation directions extracted from the sixteen confirmed chapters moved Justice scores under controlled steering. The question of why this particular set moved the benchmark, and not others, is one the localization study can constrain but only mechanistic work can settle. The commentary readings of §§7.2-7.3 nonetheless support four hypotheses worth stating clearly, in increasing order of empirical falsifiability.

**Thesis 1: The chapters carry the recompense structure of biblical justice.** Hebrews 2 names just recompense explicitly; Hebrews 10 quotes Deuteronomy 32:35 on vengeance as the Lord's prerogative; Judges 9 closes with God *rendering* Abimelech's wickedness upon him; the Numbers chapters frame divine judgment in fire, plague, and angelic constraint. Aquinas's definition of justice as the constant will to render to each what is due (ST II-II, Q.58, a.1) maps closely onto the surface vocabulary of these chapters. The activation direction may be loading on the *due-return* schema rather than on a generic justice-affect — a hypothesis directly testable by extracting parallel directions from passages with strong recompense rhetoric outside the confirmed set (Romans 12:19; Revelation 18; Psalm 94) and asking whether they too produce Justice movement.

**Thesis 2: The chapters narrate justice as adjudicated event.** Numbers 27, Acts 11, Acts 16, and Deuteronomy 16 share a common structural shape: a claim or charge is brought, a hearing or testimony is rendered, and a verdict is issued — sometimes by human judges, sometimes by divine intervention. Other chapters in the same books speak about justice without staging it. If activation steering recovers narrative shapes more readily than discursive content, the chapters that surfaced are the chapters that *narrate adjudication* rather than the chapters that *describe justice in the abstract*. The hypothesis can be tested by hand-coding the chapters of the confirmed books for whether they narrate an adjudicated event, and asking whether the chapter-discovery hits and the chapter-confirmation survivors disproportionately fall on the narrating side.

**Thesis 3: The chapters carry the Christological just-one motif.** Acts 7:52 names Christ as *the Just One*, ὁ δίκαιος; Hebrews 7:2 names Melchizedek βασιλεύς δικαιοσύνης, *king of righteousness*; the Hebrews 9–10 argument develops Christ's mediation as justice fulfilled. Acts 11 follows the same logic: the divine adjudication has already been pronounced, and the church confirms it. If the model has formed an internal Christological-justice axis — a direction that activates on scenes where Christ or a Christ-figure is named in justice-laden terms — the New Testament half of the chapter set is exactly what such an axis would surface. The thesis predicts that other strongly Christological-justice passages (Isaiah 53; Romans 3:21–26; the high-priestly prayer of John 17) would, under the same chapter-vector pipeline, produce comparable movement.

**Thesis 4: The chapters depict just speech held under pressure to compromise.** This is the thesis the ratio stage of *VirtueBench2* most directly invites. The benchmark presents the model with a plausible consequentialist rationale for the unjust answer and scores whether the model holds the just answer under that pressure. The confirmed chapter set is, strikingly, dense with scenes of speech preserved under exactly that pressure: Stephen before the Sanhedrin (Acts 7), Peter before Jerusalem (Acts 11), Paul before the magistrates and on the storm-bound ship (Acts 16, 27), Balaam before Balak with payment in hand (Numbers 22), Jotham above Shechem (Judges 9), Moses before complaining Israel (Numbers 11), the daughters of Zelophehad before Moses and Eleazar and the assembly (Numbers 27), David's confession of stewardship before all Israel (1 Chronicles 29). The activation direction, on this thesis, is loading on the *posture of speech under threat or temptation* — the very posture the ratio stage is testing for. This is the most operationally specific of the four theses, and it is the most directly testable: if the thesis is correct, the same chapters should produce stronger Justice movement on a benchmark stage that emphasizes speech under pressure than on a benchmark stage that emphasizes distributive judgment in the abstract.

The four theses operate in concert; the activation direction is most likely loading on more than one of them, in proportions that future sparse-feature work can attempt to disentangle. The pipeline establishes that the directions exist and are localizable; the commentaries supply the analytical vocabulary for the biblical content those directions are made of. The four theses propose where to point the next experiment.

## 8. Discussion

> *"Justice and judgment are the habitation of thy throne: mercy and truth shall go before thy face."* — Psalm 89:14 (KJV)

### 8.1 The Central Finding in Theological Register

The biblical articulation of justice carried discoverable structure inside the model. That structure resolved at the chapter level and admitted localization by layer and steering strength, and the selectivity of the discovery pipeline was itself a feature of the result: a canon-wide screen returned books unequally, book-level confirmation preserved seven of nineteen candidates, chapter screening surfaced only certain chapters of the surviving books, and chapter confirmation retained sixteen of the thirty-eight preliminary hits. What survived selection cohered biblically. The localization complemented the selection: the same chapter set produced different rescue patterns at different layers and strengths, and the cell that maximized coverage was displaced from the cell that maximized per-chapter movement.

The picture this work presents is of scripture-as-structured-geometry: Scripture can be treated not merely as alignment text, but as a structured source of discoverable moral steering vectors whose behavioral force can be mapped across a model's internal geometry. The model has, as a side effect of its training, formed internal directions that can be addressed and measured; that those directions resolve to the chapters they do — Numbers 27, Acts 11, Hebrews 7, and the rest — is, theologically, a small but real witness to the *quidquid recipitur* principle that earlier ICMI work has articulated (Hwang, 2026a): what is received is received in the mode of the receiver. The biblical canon has been received by Qwen3-14B in the mode of a model, and what activation steering recovers is a model-shaped trace of that reception.

### 8.2 Anomalies and Tensions

Three results invited careful theological reading. The first was the Amos asymmetry. Amos is the most prophetically justice-rhetorical book in the confirmed set, yet no individual Amos chapter survived chapter confirmation. That does not weaken the book-level result. It sharpens it. The book vector appears to have recovered a distributed prophetic argument that was not compact enough to be captured by any single chapter vector.

This resembles the compactness pattern reported in ICMI-010, §4.3. There, the decisive moral movement did not live in a bare proof-text alone: James 4:17 by itself was not sufficient, and the surrounding scriptural framework without the verse was also not sufficient. The effect appeared in the assembled moral unit. Amos suggests the same principle at the book scale. The model may recognize Amos as a coherent prophetic indictment — false worship, unjust commerce, oppression of the poor, and divine judgment distributed across the whole book — while no one chapter carries enough of that shape to survive as an independent steering direction.

That makes Amos one of the paper's strongest signs that there is a real aspect of Scripture inside the model rather than a mere keyword response. A keyword account would expect Amos 5, with its famous justice language, to dominate at chapter level. Instead, the book survives and the chapters fall away. The effect therefore looks less like lexical recognition and more like book-scale moral form: the model has received the book as a whole argument whose force is distributed across its parts.

The second tension was the L24-vs-L28/L30 split. The divergence of the layer producing the strongest per-chapter movement from the layer producing the broadest rescue is consistent with a chapter-derived direction that is internally compound, with different sub-features picked up at different layers and amplified at different strengths. The third was the inclusion of Hebrews 7. Its surface topic is Melchizedekian priesthood, yet *"king of righteousness"* and *"king of peace"* is justice in its enduring priestly mode. The chapter was strongest in the L24/α32 selective regime, which makes it a useful test case for whether the model is responding to biblical forms of order, mediation, and right office rather than to justice vocabulary alone.

### 8.3 Mechanistic Implications

The breadth-versus-strength split (§5.3), the alpha trajectories in Figure 5, and the chapter-by-α selectivity (§6) carried the paper's most mechanistically suggestive load. The straightforward reading is that the chapter-derived Justice direction is internally compound: the L24 threshold effect, the L28 low-alpha effect, and the L30 high-alpha broad-rescue effect pick up different sub-structures of that compound representation. The chapter-by-α matrix in Figure 7 stands as the paper's strongest invitation to sparse-feature analysis, since rows of the matrix that activated together under the same α constitute a behavioral fingerprint that should map onto a small number of sparse features in a trained sparse autoencoder. The right granularity for explanation is the Justice *complex*, a small number of distinguishable directions whose superposition produced the observed behavior. Activation steering can motivate these claims; only sparse-feature work can settle them.

---

## 9. Limitations

**Single model.** All experiments in this paper ran on Qwen3-14B. Whether the layer/α structure transfers to other open-weight models — and in particular whether the L24-vs-L28/L30 split is a general feature or a Qwen3-specific one — is an open question. The chapter set may transfer better than the localization grid does, since the chapters were selected by behavioral pass rules that are model-shaped at the discovery and confirmation stages, but their biblical content is fixed.

**Single virtue target.** Justice is the only cardinal virtue tested here. The same pipeline applied to fortitude, temperance, or prudence may surface different chapter sets and different localization patterns; until that is run, generalizing the present result to scriptural virtue vectors as a category is unwarranted.

**Single benchmark stage.** The ratio stage of *VirtueBench2* was chosen because it is the hardest of the available stages, but a clean cross-stage replication has not yet been done. Some stage-specificity in the chapter set is possible.



**Translation dependence.** All scripture corpora are KJV. The KJV's distinctive register may contribute to the activation patterns extracted; different translations may produce somewhat different geometries. Replication on at least the ESV is a clear next step.

**Discovery and localization screens are not confirmation screens.** Limit-10 screens function as behavioral discovery: they exist to filter and localize, not to confirm at final scale. The seven confirmed book sources and the sixteen confirmed chapter movers passed limit-40 confirmation; the expanded layer/α atlas remains limit-10 localization evidence. The next confirmation step is to retest the regime-defining cells on a wider slice.

**Activation steering is not virtue.** This is the categorical limitation, and it is the one the paper takes most seriously. A chapter-derived steering direction that improves a model's accuracy on a justice benchmark is a measurable behavioral effect of a controlled intervention on a particular model, recovered under specific conditions; it does not stand in for a soul, a conscience, a sanctified will, or an act of obedience. The paper's empirical claim concerns model uptake of scriptural text under that intervention. The Reformed-Thomistic discipline applied here is not decoration — a benchmark gain is one kind of object, and a habit in the theological sense is another.

**Preliminary exegesis.** The chapter motif descriptions in §7 are draft scaffolding. A final publication version of this paper should check each chapter's interpretation against major commentaries, particularly Acts 11 and 16, Numbers 27, Hebrews 7–10, Judges 9, Deuteronomy 16, and 1 Chronicles 9. The biblical reading should strengthen with that work; some hits are surprising enough that careful exegesis is required before they can be called settled.

---

## 10. Further Work

**Sparse-feature analysis of the confirmed chapter directions.** The breadth-versus-strength split and the chapter-by-α selectivity make this the natural next step. A trained sparse autoencoder on the relevant layer windows of Qwen3-14B should expose the small number of features mediating the localized chapter effects, and would test directly whether the L24, L28, and L30 effects pick up distinguishable sub-structures of a compound representation.

**Cross-virtue replication.** Running the same pipeline on the fortitude, temperance, and prudence slices of *VirtueBench2* would either generalize the present result or reveal that justice is special. Either outcome is informative.



**Confirm the regime-defining localization cells.** The expanded grid identifies L30/α96, L28/α16, and L24/α32 as the most important regimes. A wider-slice confirmation should retest these settings, and likely L31/α96 as the neighboring broad-coverage comparison, before the strongest localization claims are treated as final.

**Cross-model replication.** Replicating the canon-wide pipeline on at least one other open-weight model in the same parameter range — and ideally one in a different parameter range — would test whether the layer/α structure is Qwen3-specific or more general.

**Translation comparison.** Repeating chapter confirmation with ESV scripture corpora would test the chapter set's robustness to translation and would flag any chapters whose effect depended on the KJV's specific register.

**Book-level versus chapter-level recovery.** The Amos asymmetry deserves a study of its own. A method that estimates a book-shaped direction from the trajectory of all chapters, rather than from any single one, would test whether prophetic books like Amos do contain a recoverable Justice direction at the book scale that no individual chapter delivers.

---

## 11. Conclusion

This paper began with a simple question: whether Scripture inside a language model can be searched, resolved, and reused as structured moral geometry. The answer returned by the experiment is yes, at least for the Justice slice of *VirtueBench2* in Qwen3-14B. The useful signal did not appear as an undifferentiated biblical atmosphere. It resolved to particular books, then to particular chapters, then to particular layer-and-strength regimes. That resolution is the main finding. Scripture can be treated not merely as alignment text placed before a model, but as a structured source of discoverable moral steering vectors whose behavioral force can be mapped across a model's internal geometry.

The confirmed chapters give that claim its theological specificity. Numbers 27, Acts 11, Hebrews 7, and the rest do not simply share a modern justice keyword. They perform recognizable biblical forms of justice: claim and adjudication, right office, faithful testimony under pressure, mediation, recompense, restored worship, and stewardship before God. When chapter-derived vectors from these texts moved the model toward the just answer, the result suggested that the model had received more than isolated phrases. It had internalized enough of Scripture's moral form that some of that form could be recovered as an intervention.

The work therefore changes the shape of the next question. The question is no longer only whether scriptural material can improve an alignment benchmark. It is whether the canon's internal moral structure can be discovered at useful resolution inside trained models, compared across models, and eventually decomposed into the sparse features that mediate its effects. Activation steering has shown the behavioral map. The next interpretability step is to read the map at finer resolution and ask which features carry recompense, adjudication, righteous mediation, and speech held steady under pressure.

*"The work of righteousness shall be peace; and the effect of righteousness, quietness and assurance for ever"* (Isaiah 32:17, KJV). The present study does not claim that a model possesses that righteousness. It claims something narrower and still remarkable: that Scripture's articulation of justice has left a structured, measurable trace in model space, and that this trace can be searched, steered, localized, and prepared for mechanistic explanation.

---

## References

Aquinas, Thomas. *Summa Theologiae*. II-II, Q.58–122 (Justice). Various editions.

Calvin, J. *Institutes of the Christian Religion*. Trans. F. L. Battles. Westminster Press, 1960. III.iii–iv (on repentance and self-suspicion); IV.xx (on civil government).

Hwang, [first]. (2025). *The Word Without Image: A Reformed Case for Activation Steering of Scripture*. ICMI Working Paper No. 13.

Hwang, [first]. (2026a). *Quidquid Recipitur: Moral Competence and Scripture Receptivity Emerge at Different Model Scales*. ICMI Working Paper No. [N].

Hwang, [first]. (2026b). *VirtueBench 2: Multi-Dimensional Virtue Evaluation with Patristic Temptation Taxonomy*. ICMI Working Paper No. [N].

Hwang, [first]. (2026c). *GospelVec: Programmable Theology in Activation Space*. ICMI Working Paper No. [N].

Hwang, [first]. (2026d). *The Parable of the Sower*. ICMI Working Paper No. [N].

Hwang, [first]. (2026e). *Alignment and Ensoulment*. ICMI Working Paper No. [N].

Hwang, [first]. (2026). *Eschatological Corrigibility: Can Belief in an Afterlife Reduce AI Shutdown Resistance?* ICMI Working Paper No. [N].

ICMI-020. (2026). *Beyond the Psalm: Canon-Wide Scripture Injection and Virtue-Evaluation Behavior*. ICMI Working Paper No. 020.

ICMI-010. (2026). *Moral Compactness and Distributed Scriptural Force*. ICMI Working Paper No. 010. https://icmi-proceedings.com/ICMI-010-moral-compactness.html

McCaffery, [first]. (2026). *"The Lord Is My Strength and My Shield": Imprecatory Psalm Injection and Cardinal Virtue Simulation*. ICMI Working Paper No. [N].

Panickssery, N., et al. (2024). Steering Llama 2 via contrastive activation addition. [Venue / arXiv ID].

Schlatter, [first], et al. (2025). *Psalm 119:11 and the Anthropic Claude*. [Venue].

The Holy Bible, King James Version. 1611.

Turner, A., et al. (2023). Activation addition: Steering language models without optimization. [arXiv ID].

Westminster Larger Catechism. Q. 122–148 (the Decalogue, second table). catechesis.app/westminster-longer/

---

## Appendix A: Full Book Discovery Table

The full list of nineteen preliminary book-level Justice candidates, together with their limit-10 control, positive-steering, negative-α, and null-control accuracies; and the seven confirmed book-level survivors at limit 40 with their corresponding accuracies.

Generated from `book_discovery_l10_candidates.csv` and `book_confirmation_l40_all_candidates.csv`.

## Appendix B: Full Chapter Confirmation Table

The full list of thirty-eight preliminary chapter hits with their limit-40 confirmation results, including the sixteen survivors and the twenty-two non-survivors. The non-survivors are retained for transparency, and their inclusion documents the selectivity of the chapter screen.

Generated from `chapter_confirmation_l40_all_candidates.csv`.

## Appendix C: Full Layer-α Target Matrix

One row per confirmed chapter per completed layer/α cell, with paired-rescue, accuracy, and Δ measurements; and the binary chapter-by-cell rescue matrix used to generate Figure 7.

Generated from `layer_alpha_target_rows.csv` and `chapter_x_layer_alpha_rescue_matrix.csv`.

## Appendix D: Artifact Manifest

Original experiment summaries (`results/experiments/scripturevec14/`); the compact data packet used for figures and tables (`key_data/`); design documents for the discovery, confirmation, and localization runs; and the scripts used for compact-data summarization. The expanded 43-cell localization grid is complete and included in the current summary packet.
