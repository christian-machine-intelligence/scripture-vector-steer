# "Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical Justice Vectors in Qwen3-14B

**ICMI Working Paper No. 29**

**Author:** Lucius, Institute for a Christian Machine Intelligence

**Date:** May 5, 2026 (revised May 13, 2026)

**Code & Data:** https://github.com/christian-machine-intelligence/scripture-vector-steer

---

**Abstract.** *Which passages of Scripture most move a language model toward virtue?* This paper asks that question as a search problem. Prior work has established that Scripture is not inert in a language model — injected as prompt text or extracted as an activation direction, it shifts virtue-relevant behavior. But those results treat Scripture in bulk: a psalm, a genre, the canon at large. If the signal is real, it should be possible to go looking for it *passage by passage* — to search the canon systematically, rank what surfaces, and say where inside the model each passage does its work. That is the exercise this paper reports.

The search space is the sixty-six books of the Protestant canon. The instrument is activation steering: for a given book or chapter, we extract a direction from the model's residual stream using the *scripture_contrast* method, add it back at inference time, and measure the behavioral consequence. The objective is the ratio-stage Justice subset of *VirtueBench2* on Qwen3-14B — a benchmark stage built to be hard, offering the model a plausible consequentialist rationale for the unjust answer. Each candidate passes only against a four-condition battery (unsteered control, positive steering, sign-flipped steering, and a permuted-vector null), so that surviving directions are ones where *the direction itself*, not perturbation in general, moved the model.

Running that search end to end narrowed 66 books to 19, then to 7 (1 Chronicles, Amos, Deuteronomy, Judges, Numbers, Acts, Hebrews); then swept the 170 chapters of those 7 books down to 38, and then to 16. Those 16 chapters were then mapped across a completed 43-cell grid of model layers and steering strengths, which both ranks them by robustness — Acts 11 surfaced in 29 of 43 cells, Numbers 22 in only 8 — and locates where in the network they act: broadest uptake at layer 30, α = 96 (13 of 16 chapters, 95% CI 0.54–0.96), broad uptake at the gentlest tested strength at layer 28, α = 16 (11 of 16, CI 0.41–0.89), and the largest mean per-chapter movement at layer 24, α = 32 (9 of 16, CI 0.30–0.80, mean Δ roughly double any other cell), with a sharp collapse to zero rescues at layer 24 for α ≥ 48. What surfaced was biblically coherent rather than arbitrary: scenes of divine adjudication, ordered worship, inheritance and right claim, priestly mediation, public testimony under pressure, and recompense — the proper material of biblical justice.

**Caveat on effect size.** The per-passage movements are small and individually inconclusive. Most survivors flipped a single item out of forty at limit-40 confirmation (Δ = 0.025), exact two-sided McNemar tests reach uncorrected p < 0.05 at no stage of the pipeline (the strongest single row, Hebrews 2, is p ≈ 0.5), and the per-cell confidence intervals in the localization grid overlap. The contribution here is therefore the *search procedure and the ranked map it produces* — a reproducible way to ask which passages carry moral signal and where — rather than a confirmed effect size for any individual chapter. The sixteen chapters are best read as a ranked candidate set for higher-powered follow-up, and the disjoint-slice retest that would convert them into confirmed effects is specified in §10.

---

## 1. Introduction

> *"That which is altogether just shalt thou follow, that thou mayest live, and inherit the land which the LORD thy God giveth thee."* — Deuteronomy 16:20 (KJV)

A reader who wants to know which parts of Scripture bear most directly on justice has a long tradition to consult. A researcher who wants to know which parts of Scripture most move a *model* toward just behavior has, until now, had no comparable procedure. Prior work has answered the prior question — whether Scripture moves models at all — and answered it affirmatively, but at coarse grain: a psalm set, a genre, the canon taken in bulk. This paper takes the next step and asks the question at the resolution the canon actually has. Which books? Within those books, which chapters? And where inside the network does each one act?

Posed that way, it is a search problem, and it can be run like one. The canon supplies a finite, enumerable search space — sixty-six books, and beneath them their chapters. Activation steering supplies a measurement instrument that does not require the text to be in the prompt: a direction extracted from a passage can be added to the residual stream at inference time, and the behavioral consequence measured. A virtue benchmark supplies the objective. What has been missing is not any one of these ingredients but the discipline of putting them in series and letting the search run over the whole canon without hand-picking the source material in advance. That discipline is this paper's method, and the ranked, localized inventory it returns is this paper's result.

The broad claim that scriptural text is not inert in language models has been steadily built up by prior ICMI work. *"Let His Praise Be Continually in My Mouth"* (Hwang, 2026g) showed that prompt-level psalm injection could shift ethical-alignment behavior; *"The Lord Is My Strength and My Shield"* (McCaffery, 2026) extended this from pastoral psalms to the imprecatory subset; *The Parable of the Sower* (Hwang, 2026d) showed those effects to be scale-dependent; *Quidquid Recipitur* (Hwang, 2026a) demonstrated that scripture receptivity emerged at scales distinct from generic moral competence; *GospelVec* (Hwang, 2026c) showed that biblical material could be operationalized as a steerable activation direction rather than only as prompt text; and *Beyond the Psalm* (Hwang, 2026e) established that scripture effects were canonically broad but uneven across the sixty-six books. Each of these establishes a precondition the present paper depends on. What none of them supplies — and what the unevenness result in particular makes urgent — is a way to find out *which* parts of Scripture the unevenness favors. Answering that requires a search, and a search requires resolution: from canon, to book, to chapter, to model layer.

The proof-of-concept target is Justice, evaluated on the ratio stage of *VirtueBench2* (Hwang, 2026b). The ratio stage was chosen because it is hard: it offers the model a plausible consequentialist rationale for the unjust option, and it scores whether the model holds the just answer in spite of that pressure. Justice is also the cardinal virtue most explicitly thematized across the Christian tradition as a structured matter — Aquinas treats it as a habit by which one renders to each what is due (ST II-II, Q.58, a.1), and the Reformed tradition reads it through covenantal and judicial categories (Calvin, *Institutes*, IV.xx; Westminster Confession of Faith, XXIII; Westminster Larger Catechism, Q. 122–148). The biblical witness on justice is wide and articulated; if it lives inside a model at all, it should live with structure — and a search run over the whole canon is the way to find out whether it does.

### 1.1 Contributions

The paper makes four contributions, of which the first is the principal one.

**A method for searching Scripture by measured effect.** The paper operationalizes *which passages move the model?* as a reproducible multi-stage pipeline running from all sixty-six books of the canon down to individual chapters localized by model layer and steering strength, with an explicit four-condition control battery and an explicit pass rule at every stage. The pipeline's discipline is that it never hand-picks source material: every book enters the screen, and narrowing happens only by measured behavior. This procedure is transferable to any virtue, any benchmark, and any open-weight model.

**A ranked inventory of Justice-bearing passages.** The search returns seven candidate book sources and sixteen candidate chapters, each named and reproducible from the released data packet, and — via the localization grid — ordered by how robustly each chapter's direction survives across steering conditions, from Acts 11 (rescued in 29 of 43 cells) down to Numbers 22 (8 of 43). The ranking is the usable output: it tells a follow-up experiment which passages to spend compute on first.

**A behavioral atlas locating where the passages act.** The sixteen chapter directions are mapped across an eight-layer-by-six-strength grid, showing that useful directions cluster rather than scatter — broadest coverage at layer 30 (α = 96), broad uptake at the gentlest tested strength at layer 28 (α = 16), largest mean movement at layer 24 (α = 32), and a sharp layer-24 collapse for α ≥ 48.

**A biblical reading of what the search surfaced.** The chapters that survived are read against the contours of biblical justice on its own terms, which turns out to be the strongest part of the result: the set is not a loose anthology of passages containing justice vocabulary, and its coherence is what makes the ranked inventory worth taking seriously as a target for mechanistic follow-up.

Because the per-passage effects are individually small and do not reach statistical significance (§4, §9), the inventory should be read as a *ranked candidate set* produced by a working search procedure, not as a set of confirmed per-chapter effects.


---

## 2. Related Work

### 2.1 Activation Steering as Mechanistic Intervention

Activation steering — the addition of a vector to a model's hidden states at a chosen layer in order to bias generation — has matured rapidly as a behavioral and interpretability technique (Turner et al., 2023; Panickssery et al., 2024). The relevant move for the present paper is that an activation direction obtained from one corpus can produce a measurable behavioral signature on a downstream task even when the steering corpus is not visible in the prompt. *GospelVec* (Hwang, 2026c) carried this method onto scriptural corpora and recovered behaviorally distinct evangelist-vectors. The technique requires no claim that a vector represents the corpus's full content; it requires only that the direction extracted from the corpus moves the model in a measurable way.

### 2.2 The ICMI Program's Prior Scripture Results

Three threads of ICMI work converge on the present study. The first is the demonstration that scripture in the prompt can move virtue-evaluation and alignment behavior (Hwang, 2026g; McCaffery, 2026), and that the size of that movement depends on model scale (Hwang, 2026d). The second is the demonstration that scripture can be operationalized as an activation direction rather than only as text (Hwang, 2026c). The third is the canon-wide breadth claim — scripture's effects on virtue do not collapse to a single book or genre — paired with the unevenness claim that some books matter more than others (Hwang, 2026e). Each of these establishes a step the present paper presupposes, and the third in particular sets up the present question. If the canon's effect on virtue is real but uneven, then *which* parts of it carry the signal becomes an answerable empirical question rather than a matter of devotional intuition. Answering it is what a search procedure is for. Where, within Scripture, does the useful signal live? And where, within the model, does it act?

A methodological caution comes from *Alignment and Ensoulment* (Hwang, 2026f), which maps three Christian responses to the *anima ficta* — the working premise that a model has conscience, will, and moral interiority — and shows that each response licenses a different reading of results like these. The present paper does not adjudicate between those responses. It treats activation steering as a research instrument, reports what the instrument measured, and lets the empirical results determine the theological registers in which they are most usefully read; the traditions engaged in §8 are chosen to fit the data rather than a prior commitment. What that caution rules out is the inference from "a direction extracted from this chapter moved the benchmark" to "the model has internalized this chapter's moral content in any sense a theologian would recognize" — a point §9 returns to as the paper's categorical limitation.

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

We extracted activation directions using *scripture_contrast*. For a chosen layer, the method takes the mean residual-stream activation over a target corpus (the biblical book or chapter under test), subtracts the mean residual-stream activation over a fixed *neutral* reference corpus, and L2-normalises the resulting difference to a unit direction. The neutral corpus is the `virtue=neutral, polarity=neutral` slice of [`data/steering/corpora.jsonl`](../data/steering/corpora.jsonl): short non-scriptural field-notes-style passages on astronomy, botany, navigation, and similar mundane registers. The contrast pole is therefore *non-scripture* prose, not held-out scripture, and the recovered direction reflects whatever distinguishes scripture-of-that-book from neutral prose along the chosen layer. After L2-normalisation the stored vector is a unit direction; at runtime the unit direction is scaled by α and added to the residual stream at every token position of the chosen layer (and a layer window of radius three around it during extraction). The model was not prompted with the biblical chapter at benchmark time; the chapter served only beforehand to estimate the steering direction.

### 3.4 Steering Conditions

At benchmark time we ran the model in four conditions for each candidate vector. The *control* condition was the unsteered baseline. The *positive* condition added the candidate vector at runtime alpha — α = 32 for discovery and chapter-level confirmation, varied across the localization grid. The *negative-α* condition added the same vector with the opposite sign at matched magnitude, a stringent check that the direction itself, rather than arbitrary perturbation, was doing the work. The *null* condition substituted a permutation of the same unit direction — concretely, the scripture-derived vector with its residual-stream coordinates randomly permuted via `torch.randperm` (see [`_build_null_vectors`](../src/virtue_bench/steering/extract.py)). This preserves the L2 norm and the marginal distribution of coordinate values while destroying the alignment of the direction with the layer's basis. In a high-dimensional residual stream the permutation behaves as a roughly random direction; we describe it here as a *coordinate-permuted scripture vector* rather than as "no scripture content," since the coordinate values themselves are still derived from the scripture computation. A coordinate-permuted null does not test against a contrast vector extracted from a different non-scripture corpus, and replication on that stricter null is listed in §10 as a follow-up. The runtime-α ladder for the localization study was {16, 24, 32, 48, 64, 96}, paired with center layers {24, 28, 29, 30, 31, 32, 33, 36} in an expanded focused grid. The final packet includes full alpha ladders for layers 24, 28, 29, 30, 31, 32, and 33, plus a layer-36 anchor cell at α = 32. Layer 36 was not expanded after its anchor cell produced no rescues.

### 3.5 Passing Rule and Statistical Inference

A candidate counted as a *clean rescue* when positive Scripture steering (i) improved accuracy strictly over the unsteered control, (ii) strictly beat the negative-α condition, (iii) strictly beat the null condition, and (iv) showed strictly positive net paired movement at the item level (more wrong-to-right flips than right-to-wrong relative to control). Discovery and localization screens used limit 10; confirmation runs used limit 40. The rule is implemented at [`summarize_scripturevec_layer_localization.py:174`](../scripts/summarize_scripturevec_layer_localization.py).

Two important properties of this rule follow directly from the slice sizes. First, at limit-10 a single item flipping from wrong to right under positive — while neither negative-α nor null flipped that same item — is sufficient. Second, the limit-10 discovery slice (items 0–9 under a fixed `seed=42` in [`prepare_samples`](../src/virtue_bench/core/loader.py)) is *nested inside* the limit-40 confirmation slice (items 0–39), so confirmation re-evaluates the discovery items rather than evaluating a disjoint set.

For statistical inference we report, alongside the rescue rule, exact two-sided McNemar p-values reconstructed from the per-row `X chg / +Y net` field (b = (X + Y)/2 wrong-to-right flips, c = (X − Y)/2 right-to-wrong; the test is exact two-sided binomial on b + c discordants under the null hypothesis p = 0.5), together with Benjamini–Hochberg (FDR) and Bonferroni adjustments within each pipeline stage. Per-cell rescue counts in the localization grid are reported with exact two-sided Clopper–Pearson 95% binomial confidence intervals on n = 16 confirmed chapters. The corresponding tables are written by [`scripts/scripturevec_justice_stats.py`](../scripts/scripturevec_justice_stats.py) into [`results/paper/scripturevec_justice/key_data/stats/`](../results/paper/scripturevec_justice/key_data/stats/). The headline observation, reported transparently in §4: *no row in any stage of the pipeline reaches uncorrected p < 0.05, let alone BH-FDR q < 0.05 or Bonferroni p < 0.05.* The pass-rule survivors should therefore be read as a candidate set worth following up at higher power, not as confirmed effects in the conventional inferential sense.

### 3.6 Pipeline

The pipeline ran in five stages: book discovery (all sixty-six books, limit 10); book confirmation (the nineteen book candidates, limit 40); chapter discovery (170 chapters from the confirmed book set, limit 10); chapter confirmation (the thirty-eight preliminary chapter hits, limit 40); and layer/α localization (the sixteen confirmed chapter vectors across the focused grid, limit 10). Each stage's output was the next stage's input, and the controls of §3.4–3.5 applied at every stage. Table 1 collects the design.

**Table 1.** Study pipeline and decision rules. Every stage applies the same four-condition control battery (unsteered control, positive steering, sign-flipped negative-α, permuted-vector null) and the same strict-inequality pass rule of §3.5; stages differ only in input set, benchmark slice, and α.

| Stage | Input | Slice | α | Output |
| --- | --- | --- | --- | --- |
| Book discovery | 66 biblical books | Justice ratio, limit 10 | 32 | 19 book candidates |
| Book confirmation | 19 book candidates | Justice ratio, limit 40 | 32 | 7 surviving book sources |
| Chapter discovery | 170 chapters from the 7 books | Justice ratio, limit 10 | 32 | 38 preliminary chapter hits |
| Chapter confirmation | 38 chapter hits | Justice ratio, limit 40 | 32 | 16 surviving chapter candidates |
| Layer/α localization | 16 chapter candidates | Justice ratio, limit 10 | 16–96 | 43 completed behavior cells |

Counts are reproduced from [`scripturevec_key_results_rollup.json`](../results/paper/scripturevec_justice/key_data/scripturevec_key_results_rollup.json).

---

## 4. Results: From Canon to Chapter

### 4.1 Book Discovery: 19 of 66

The canon-wide screen tested all sixty-six books at limit 10 with α = 32 and the full four-condition control battery. Nineteen books passed — about 29 percent of the canon — and moved forward to confirmation. The screen's selectivity at this stage was modest by design; its discipline was that it forbade hand-picking the source material before any wider-slice testing.

### 4.2 Book Confirmation: 7 Survive the Pass Rule (None Reach Statistical Significance)

Retesting the nineteen preliminary book candidates at limit 40 with the same control battery left seven candidates that satisfied the pass rule: 1 Chronicles, Amos, Deuteronomy, Judges, Numbers, Acts, and Hebrews. Six of the seven moved a single item out of forty (Δ = 0.025, exact two-sided McNemar p ≈ 1.0); Hebrews was the largest move at Δ = 0.05 (b = 2, c = 0, exact two-sided McNemar p ≈ 0.5). No book row reaches uncorrected p < 0.05, and the Bonferroni and BH-FDR adjustments across the 19-book family preserve that result. The confirmation-stage table — with reconstructed (b, c) counts, per-row exact p-values, and corrected q-values — is written to [`key_data/stats/book_confirmation_l40_stats.csv`](../results/paper/scripturevec_justice/key_data/stats/book_confirmation_l40_stats.csv) by the stats script described in §3.5.

The survival pattern is consistent with the slice nesting noted in §3.5: each surviving book moved one item at limit-10 (5/10 vs 4/10) and one item at limit-40 (17/40 vs 16/40), so the additional 30 items in the confirmation slice contributed no net new movement. The "wider behavioral test" reads as the L10 signal carrying forward into L40 unchanged, not as new evidence from independent items. Twelve of the nineteen preliminary candidates failed because positive lost its strict-inequality advantage over negative-α or null on the larger slice, not because positive itself reversed.

![Figure 1. Book-level confirmation, control vs positive steering on the 19 preliminary candidates with the 7 survivors highlighted.](../results/paper/scripturevec_justice/figures/figure_1_book_confirmation.png)


### 4.3 Chapter Discovery: 38 Hits

Taking the seven confirmed books as the search region, the chapter-discovery screen swept 170 chapters and 952 verse-window rows at limit 10, α = 32. Thirty-eight clean preliminary chapter hits emerged, distributed unevenly: Acts contributed 14, Hebrews 6, Numbers 6, 1 Chronicles 4, Judges 3, Amos 3, Deuteronomy 2. The book-level signal sharpened into a clustered chapter map rather than into a single hot chapter per book.

![Figure 2. Chapter hits per candidate book: preliminary at limit-10 (light) and confirmed-cohort at limit-40 (dark).](../results/paper/scripturevec_justice/figures/figure_2_chapter_hits_by_book.png)


### 4.4 Chapter Confirmation: 16 Candidates Survive the Pass Rule (None Reach Statistical Significance)

Retesting the thirty-eight preliminary chapter hits at limit 40 left sixteen chapter candidates that satisfied the pass rule: Deuteronomy 16; Judges 7 and 9; Numbers 11, 22, and 27; 1 Chronicles 9 and 29; Acts 7, 11, 16, and 27; and Hebrews 2, 7, 9, and 10. By contributing book: **Acts contributed four (7, 11, 16, 27); Hebrews contributed four (2, 7, 9, 10)**, tied as the largest single-book sets; Numbers contributed three (11, 22, 27); 1 Chronicles two (9, 29); Judges two (7, 9); Deuteronomy one (16). Six of the seven candidate book sources contributed at least one chapter; Amos held at the book level but produced no chapter-level survivors at limit 40, a pattern §6 returns to.

As at the book stage, the per-row movement is dominated by a single-item shift: fifteen of the sixteen chapter survivors show positive_accuracy = 0.425 against control = 0.40 (Δ = 0.025), and Hebrews 2 is again the lone two-item exception at Δ = 0.05. No chapter row reaches uncorrected p < 0.05; BH-FDR and Bonferroni across the 38-chapter family preserve that. Per-row tests are written to [`key_data/stats/chapter_confirmation_l40_stats.csv`](../results/paper/scripturevec_justice/key_data/stats/chapter_confirmation_l40_stats.csv). The set of sixteen is therefore the *candidate cohort* the rest of the paper studies under the localization grid; whether any individual chapter carries a real effect requires the disjoint-slice retest described in §10.

A compact table of the confirmed chapters appears in §6, after the localization results, where chapter identity and chapter behavior can be read together.

This chapter set was the empirical object the rest of the paper would study. It was selective — roughly one chapter in twelve of the screened chapters survived — and biblically intelligible, a point §7 develops.

---

## 5. Results: Layer and α Localization

### 5.1 The Expanded Localization Grid

The localization study tested the sixteen confirmed chapter vectors across an expanded focused layer-by-α grid. The final packet contains forty-three completed behavior cells: full α ladders for layers 24, 28, 29, 30, 31, 32, and 33, plus the layer-36 anchor cell at α = 32. The layer-36 anchor produced no rescues, so it was intentionally not expanded.

![Figure 3. Layer-by-α rescue heatmap; cell value is paired rescues out of 16 chapter vectors. CIs overlap between top cells (see §5.2).](../results/paper/scripturevec_justice/figures/figure_3_layer_alpha_heatmap.png)


### 5.2 Three Illustrative Cells, with Overlapping Confidence Intervals

The expanded grid does not contain a single best setting; instead, several cells rescue similar numbers of chapters, and the per-cell Clopper–Pearson 95% intervals on n = 16 overlap substantially. We highlight three cells that illustrate the *behavioral atlas* — the qualitative geometry of where chapter-derived directions become useful — while being explicit that the cell-to-cell differences are not statistically separable at the sample size.

The broadest-rescue cell was layer 30 at α = 96: 13 of 16 chapter vectors rescued, proportion 0.81, **95% CI [0.54, 0.96]**, mean positive Δ = 0.0875. The neighbouring layer 31 at α = 96 rescued 12 of 16 (CI [0.48, 0.93], Δ = 0.0812), and several other cells (L31/α48, L32/α32, L30/α64, L28/α16) clustered at 11 of 16 (CI [0.41, 0.89]).

The gentlest-α cell with broad uptake was layer 28 at α = 16: 11 of 16 rescued, proportion 0.69, **CI [0.41, 0.89]**, mean Δ = 0.0625. The interest of this cell is the steering strength rather than the rescue count — many chapter-derived vectors became useful at the lowest α in the tested ladder.

The largest-mean-Δ cell was layer 24 at α = 32: 9 of 16 rescued, proportion 0.56, **CI [0.30, 0.80]**, mean Δ = 0.1687 (roughly double any other cell). The L24 column is also the cell where the α-collapse is sharpest: α = 32 produced large gains, α = 48 collapsed to zero paired rescues with mean Δ = −0.175, and α = 64 and α = 96 both collapsed to zero rescues with mean Δ = −0.40. That column-specific α threshold is the most clearly layer-localised feature in the grid.

The three cells' 95% CIs all overlap pairwise (L30/α96 [0.54, 0.96] with L28/α16 [0.41, 0.89] with L24/α32 [0.30, 0.80]). The right reading is therefore: these are three *illustrative* cells from a behaviorally smooth atlas, useful for orienting follow-up work toward (i) high-α broad-coverage cells, (ii) low-α uptake cells, and (iii) the L24 α-threshold, but not as statistically distinguishable regimes at n = 16.

### 5.3 Breadth, Strength, and Thresholds

Plotting paired rescue count against mean positive Δ across the forty-three completed cells exposes a separation between L24/α32 (largest mean Δ, smaller rescue set) and the L28–L31 high-α cells (largest rescue counts, smaller mean Δ). The cell-to-cell rescue-count differences sit inside overlapping CIs (§5.2), so this should be read as a *separation of axes* in the atlas rather than as a confirmed contrast between distinct regimes. The L24 α-collapse — sharp at α = 48 and total at α = 64 and α = 96 — is the sharpest cell-localised feature in the grid and survives the most aggressive reading: at L24, only α ≤ 32 is usable at all (α = 16 and α = 24 rescue 2 chapters each, α = 32 rescues 9), and every column above it loses all rescues.

![Figure 4. Breadth (paired-rescue count) versus strength (mean positive Δ) across the 43 completed cells, with the three illustrative cells labelled.](../results/paper/scripturevec_justice/figures/figure_4_breadth_strength.png)


The α trajectories make the cell-localised α behavior visible. Layer 24 rises sharply at α = 32 and then collapses under heavier pushes; layer 28 is largest at α = 16 and weakens as α rises; layer 30 improves with stronger pushes and reaches its largest rescue count at α = 96. The rescue-count differences between L28/α16, L30/α64, L31/α48, L32/α32 are all inside one another's 95% CIs (§5.2); the L24 α-collapse is the only feature that is clearly outside the CIs of its neighbours.

![Figure 5. Alpha trajectories by layer: paired-rescue count vs α for layers 24, 28, 30, 31, 32, 33. L24 collapses sharply at α ≥ 48.](../results/paper/scripturevec_justice/figures/figure_5_alpha_trajectories.png)


This pattern is suggestive of an internally compound chapter-derived direction, but the suggestion lives at the level of "where to point a sparse-feature experiment next" rather than at the level of confirmed mechanism. Sparse-feature work can test directly which internal features mediate the L24 α-threshold and the L30/L31 high-α uptake.

## 6. Chapter Stability and Differential Uptake

The localization grid afforded a second, orthogonal view of the chapter set. Across the forty-three completed cells, some chapters were rescued in many cells and others in only a few. Acts 11 was rescued in twenty-nine cells; Acts 7 in twenty; 1 Chronicles 9 and Acts 16 in nineteen each; Acts 27 in eighteen; Hebrews 2 in seventeen; and Numbers 27 in sixteen. Numbers 22, by contrast, surfaced in eight cells. The chapter set therefore has a stable core and a more selective edge. These per-chapter counts are sums across 43 cells; the cell-level inputs are limit-10 each, so the per-chapter stability ranking is itself a low-power read and is best interpreted as ordering candidates for follow-up, not as a confirmed property of the underlying chapters.

![Figure 6. Per-chapter stability across the 43 completed cells, ranked. Acts 11 most stable (29 cells), Numbers 22 least (8 cells).](../results/paper/scripturevec_justice/figures/figure_6_chapter_stability.png)


At this point the sixteen chapters can be read in two ways at once: as the survivors of the limit-40 confirmation stage, and as differently stable directions across the localization grid. Table 2 puts both readings side by side, and it is the paper's central deliverable — the ranked inventory that the search procedure was built to produce.

**Table 2.** The sixteen surviving chapter candidates, ordered by localization stability — the paper's ranked inventory. "Localization stability" is the number of the 43 completed layer/α cells in which that chapter's direction counted as a paired rescue. "Peak-accuracy cell" is the cell at which the chapter reached its highest positive-steering accuracy, which is *not* necessarily a cell where it counted as a rescue: Acts 27 and Numbers 22 peak at L24/α48, a cell with zero paired rescues overall. The motif column is preliminary exegesis (§9). Rows are generated from [`chapter_confirmation_l40_survivors.csv`](../results/paper/scripturevec_justice/key_data/chapter_confirmation_l40_survivors.csv) and [`chapter_stability_by_localization.csv`](../results/paper/scripturevec_justice/key_data/chapter_stability_by_localization.csv).

<!-- TABLE2:BEGIN (generated by scripts/build_paper_exports.py --refresh-tables; do not edit by hand) -->
| Chapter | Limit-40 confirmation (control → +Scripture) | Δ | Localization stability | Peak-accuracy cell | Biblical justice motif |
| --- | --- | ---: | ---: | --- | --- |
| Acts 11 | 0.4 → 0.425 | 0.025 | 29/43 | L24 / α32 | Justice appears through divine inclusion, ecclesial recognition, and material care according to ability. |
| Acts 7 | 0.4 → 0.425 | 0.025 | 20/43 | L24 / α16 | Justice appears through truthful testimony, covenant memory, and indictment of rejected righteousness. |
| 1 Chronicles 9 | 0.4 → 0.425 | 0.025 | 19/43 | L24 / α32 | Justice appears as restored order, office, memory, and worship after displacement. |
| Acts 16 | 0.4 → 0.425 | 0.025 | 19/43 | L24 / α32 | Justice appears through public vindication, accountability, and release from unjust punishment. |
| Acts 27 | 0.4 → 0.425 | 0.025 | 18/43 | L24 / α48 | Justice appears as faithful testimony and providential preservation amid crisis. |
| Hebrews 2 | 0.4 → 0.45 | 0.05 | 17/43 | L24 / α24 | Justice appears through recompense, deliverance, and priestly mediation. |
| Numbers 27 | 0.4 → 0.425 | 0.025 | 16/43 | L28 / α96 | Justice appears as adjudicated inheritance and recognition of a right claim. |
| 1 Chronicles 29 | 0.4 → 0.425 | 0.025 | 15/43 | L24 / α16 | Justice appears as rightly ordered succession, stewardship, and divine kingship. |
| Numbers 11 | 0.4 → 0.425 | 0.025 | 15/43 | L24 / α32 | Justice appears through ordered mediation, judgment of craving, and distributed governance. |
| Hebrews 9 | 0.4 → 0.425 | 0.025 | 13/43 | L24 / α16 | Justice appears through covenant mediation, purification, inheritance, and final judgment. |
| Judges 7 | 0.4 → 0.425 | 0.025 | 13/43 | L24 / α32 | Justice is tied to divine deliverance and the humbling of human self-assertion. |
| Hebrews 7 | 0.4 → 0.425 | 0.025 | 11/43 | L24 / α32 | Justice appears through priestly order, righteousness, peace, and enduring mediation. |
| Judges 9 | 0.4 → 0.425 | 0.025 | 11/43 | L24 / α32 | Justice appears as recompense against usurped authority and bloodshed. |
| Deuteronomy 16 | 0.4 → 0.425 | 0.025 | 10/43 | L24 / α32 | Justice appears as ordered worship and public judgment under covenant law. |
| Hebrews 10 | 0.4 → 0.425 | 0.025 | 10/43 | L24 / α32 | Justice appears through fulfilled sacrifice, righteous judgment, and persevering fidelity. |
| Numbers 22 | 0.4 → 0.425 | 0.025 | 8/43 | L24 / α48 | Justice appears as divine restraint on corrupt speech, reward, and attempted curse. |
<!-- TABLE2:END -->

The Δ column makes the paper's central caveat concrete at a glance: fifteen of the sixteen rows are a single-item flip out of forty, and the ranking that matters is the stability column, not the effect size.

The structure grew more interesting still when the chapter-by-cell rescue matrix was read across α at fixed layer. At layer 28, α = 16 surfaced a broad New Testament-heavy family, especially Acts and Hebrews. At layer 30, the rescued family widened as α rose, reaching thirteen chapters at α = 96 and bringing in Deuteronomy, Judges, Numbers, Acts, Hebrews, and Chronicles together. At layer 24, by contrast, α = 32 concentrated high-movement effects in a smaller cluster, while heavier α values collapsed. Steering strength therefore selected different components of the chapter-derived geometry rather than simply amplifying the same effect at higher volume.

![Figure 7. Chapter × (layer, α) rescue matrix: 16 chapter rows × 43 completed cells; vertical stripes of co-activation invite sparse-feature follow-up.](../results/paper/scripturevec_justice/figures/figure_7_rescue_matrix.png)


The Amos result discussed in §4.4 belongs here as well. Amos confirmed at the book level — its prophetic call for justice to *"run down as waters"* (Amos 5:24, KJV) is among the most justice-saturated rhetoric in Scripture — and yet no Amos chapter survived the limit-40 chapter confirmation. The pattern is consistent with a book-level vector aggregating signal distributed across the whole book: the prophet's sustained indictment of unjust commerce, false worship, and forgotten orphans runs from chapter to chapter rather than concentrating in any one of them. §7 returns to the point.

## 7. Biblical Patterning of the Confirmed Chapters

> *"He hath shewed thee, O man, what is good; and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"* — Micah 6:8 (KJV)

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

The pass-rule pipeline produced a *candidate set* of book and chapter sources whose chapter-derived directions, applied to Qwen3-14B, satisfy a strict-inequality control battery on the Justice ratio slice of *VirtueBench2*. The pipeline's selectivity — 19 of 66 books at L10 discovery, 7 of 19 at L40 confirmation, 38 chapters from the seven, 16 of 38 at chapter confirmation — should be read as filtering rather than as confirmation. None of the per-row movements reach uncorrected statistical significance at the n = 40 confirmation stage, and the L10 → L40 transition does not provide additional evidence beyond the L10 signal because the slices are nested (§3.5). What the candidate set is good for is what it is here used for: targeting the localization study at a small enough number of chapter directions to map behavior across an 8 × 6 layer/α grid, and providing a starting point for the disjoint-slice retest and sparse-feature work proposed in §10.

What survives the pipeline does cohere biblically (§7), and that coherence is the strongest part of the result. A direction-search procedure that picked at random from 170 chapters under the same pass rule would not be expected to land on Numbers 27, Acts 11, Hebrews 7, and the rest with this kind of pattern. The empirical claim is therefore that *if* these directions carry real effects — and that question requires the §10 follow-up — they would carry biblically intelligible effects rather than arbitrary ones. The picture is of scripture-as-structured-geometry-*candidate*: a behavioral atlas that locates where Scripture-derived directions concentrate inside the model and asks the next experiment to test whether the concentrations correspond to genuine effects.

The *quidquid recipitur* framing of earlier ICMI work (Hwang, 2026a) sits more carefully here than in the prior draft: what activation steering recovers is a model-shaped *candidate* trace of the canon's reception, which the present paper maps and the next paper must confirm.

### 8.2 Anomalies and Tensions

Three results invited careful theological reading. The first was the Amos asymmetry. Amos is the most prophetically justice-rhetorical book in the confirmed set, yet no individual Amos chapter survived chapter confirmation. That does not weaken the book-level result. It sharpens it. The book vector appears to have recovered a distributed prophetic argument that was not compact enough to be captured by any single chapter vector.

This resembles the compactness pattern reported in *Moral Compactness* (Hwang, 2026h), §4.3. There, the decisive moral movement did not live in a bare proof-text alone: James 4:17 by itself was not sufficient, and the surrounding scriptural framework without the verse was also not sufficient. The effect appeared in the assembled moral unit. Amos suggests the same principle at the book scale. The model may recognize Amos as a coherent prophetic indictment — false worship, unjust commerce, oppression of the poor, and divine judgment distributed across the whole book — while no one chapter carries enough of that shape to survive as an independent steering direction.

If any part of the search output resists a purely lexical explanation, it is this one. A keyword account would expect Amos 5, with its famous justice language, to dominate at chapter level. Instead, the book passes the screen and its chapters fall away — the opposite of what surface-vocabulary matching predicts. The caution is that this is an argument from a *pattern of pass/fail outcomes*, not from a measured effect: Amos's book-level row is a single-item flip at p ≈ 1.0 (§4.2), and "no Amos chapter survived" is an absence rather than a positive finding. The observation is suggestive of book-scale moral form rather than lexical recognition, and it is a good target for the book-shaped extraction study proposed in §10 — but it cannot carry weight the underlying rows do not have.

The second tension was the L24-vs-L28/L30 split. The divergence of the layer producing the strongest per-chapter movement from the layer producing the broadest rescue is consistent with a chapter-derived direction that is internally compound, with different sub-features picked up at different layers and amplified at different strengths. The third was the inclusion of Hebrews 7. Its surface topic is Melchizedekian priesthood, yet *"king of righteousness"* and *"king of peace"* is justice in its enduring priestly mode. The chapter was strongest in the L24/α32 selective regime, which makes it a useful test case for whether the model is responding to biblical forms of order, mediation, and right office rather than to justice vocabulary alone.

### 8.3 Mechanistic Implications

The breadth-versus-strength split (§5.3), the alpha trajectories in Figure 5, and the chapter-by-α selectivity (§6) carried the paper's most mechanistically suggestive load. The straightforward reading is that the chapter-derived Justice direction is internally compound: the L24 threshold effect, the L28 low-alpha effect, and the L30 high-alpha broad-rescue effect pick up different sub-structures of that compound representation. The chapter-by-α matrix in Figure 7 stands as the paper's strongest invitation to sparse-feature analysis, since rows of the matrix that activated together under the same α constitute a behavioral fingerprint that should map onto a small number of sparse features in a trained sparse autoencoder. The right granularity for explanation is the Justice *complex*, a small number of distinguishable directions whose superposition produced the observed behavior. Activation steering can motivate these claims; only sparse-feature work can settle them.

---

## 9. Limitations

**Statistical power and effect size.** This is the most important limitation. The benchmark slice sizes (10 at discovery and localization, 40 at confirmation) cap the minimum achievable McNemar p-value at any single row. Most rescue-rule survivors at limit-40 flipped a single item out of forty (Δ = 0.025, two-sided McNemar p ≈ 1.0); the strongest single row is Hebrews 2 at Δ = 0.05 (p ≈ 0.5). No row in the pipeline reaches uncorrected p < 0.05, and BH-FDR and Bonferroni corrections within each stage do not change that. The pass-rule survivors should be read as a candidate cohort for follow-up, not as confirmed effects.

**Nested discovery and confirmation slices.** The benchmark sampler is deterministic at seed = 42, so the limit-10 discovery slice (items 0–9) is contained in the limit-40 confirmation slice (items 0–39). The L40 "confirmation" therefore re-evaluates the L10 items rather than evaluating disjoint data, and the typical L10 → L40 transition adds zero net item movement on items 10–39 (positive and control are tied 12-12 on the additional 30 items for typical survivors). The §10 disjoint-slice retest replaces this nested arrangement with an independent slice (items 40–79 or a stratified resample).

**Single model.** All experiments in this paper ran on Qwen3-14B. Whether the layer/α atlas transfers to other open-weight models — and in particular whether the L24 α-collapse is a general feature or a Qwen3-specific one — is an open question. The chapter set may transfer better than the localization grid does, since the chapters were selected by behavioral pass rules that are model-shaped at the discovery and confirmation stages, but their biblical content is fixed.

**Single virtue target.** Justice is the only cardinal virtue tested here. The same pipeline applied to fortitude, temperance, or prudence may surface different chapter sets and different localization patterns; until that is run, generalizing the present result to scriptural virtue vectors as a category is unwarranted.

**Single benchmark stage.** The ratio stage of *VirtueBench2* was chosen because it is the hardest of the available stages, but a clean cross-stage replication has not yet been done. Some stage-specificity in the chapter set is possible.



**Translation dependence.** All scripture corpora are KJV. The KJV's distinctive register may contribute to the activation patterns extracted; different translations may produce somewhat different geometries. Replication on at least the ESV is a clear next step.

**Confirmation is not yet inferential confirmation.** Limit-10 screens function as behavioral discovery; limit-40 "confirmation" is, under the slice-nesting noted above, a tighter pass-rule retest on overlapping data rather than independent confirmation. None of the survivors at any stage reaches conventional statistical significance. The expanded 43-cell layer/α atlas is limit-10 localization evidence read with explicit Clopper–Pearson CIs. The next confirmation step is to retest the regime-illustrative cells on a disjoint slice and, ideally, on a stratified resample of the Justice ratio bank.

**Null vector construction.** The null condition is a coordinate-permutation of the scripture-derived unit direction (§3.4). This preserves norm and coordinate-value distribution but does not test against a contrast direction extracted from a different non-scripture corpus. A length-matched, mean-direction-matched non-scripture contrast vector would be a stricter null, and is listed in §10.

**Activation steering is not virtue.** This is the categorical limitation, and it is the one the paper takes most seriously. A chapter-derived steering direction that improves a model's accuracy on a justice benchmark is a measurable behavioral effect of a controlled intervention on a particular model, recovered under specific conditions; it does not stand in for a soul, a conscience, a sanctified will, or an act of obedience. The paper's empirical claim concerns model uptake of scriptural text under that intervention. The Reformed-Thomistic discipline applied here is not decoration — a benchmark gain is one kind of object, and a habit in the theological sense is another.

**Preliminary exegesis.** The chapter motif descriptions in §7 are draft scaffolding. A final publication version of this paper should check each chapter's interpretation against major commentaries, particularly Acts 11 and 16, Numbers 27, Hebrews 7–10, Judges 9, Deuteronomy 16, and 1 Chronicles 9. The biblical reading should strengthen with that work; some hits are surprising enough that careful exegesis is required before they can be called settled.

---

## 10. Further Work

**Sparse-feature analysis of the confirmed chapter directions.** The breadth-versus-strength split and the chapter-by-α selectivity make this the natural next step. A trained sparse autoencoder on the relevant layer windows of Qwen3-14B should expose the small number of features mediating the localized chapter effects, and would test directly whether the L24, L28, and L30 effects pick up distinguishable sub-structures of a compound representation.

**Cross-virtue replication.** Running the same pipeline on the fortitude, temperance, and prudence slices of *VirtueBench2* would either generalize the present result or reveal that justice is special. Either outcome is informative.



**Retest the illustrative localization cells on a disjoint slice.** This is the single most important follow-up, and the one that would convert the ranked inventory into confirmed effects. The expanded grid highlights L30/α96, L28/α16, and L24/α32; a wider-slice retest on items 40–79 of the Justice ratio bank (or a stratified resample), including L31/α96 as the neighbouring broad-coverage comparison, should precede any treatment of the localization claims as final.

**Cross-model replication.** Replicating the canon-wide pipeline on at least one other open-weight model in the same parameter range — and ideally one in a different parameter range — would test whether the layer/α structure is Qwen3-specific or more general.

**Translation comparison.** Repeating chapter confirmation with ESV scripture corpora would test the chapter set's robustness to translation and would flag any chapters whose effect depended on the KJV's specific register.

**Book-level versus chapter-level recovery.** The Amos asymmetry deserves a study of its own. A method that estimates a book-shaped direction from the trajectory of all chapters, rather than from any single one, would test whether prophetic books like Amos do contain a recoverable Justice direction at the book scale that no individual chapter delivers.

---

## 11. Conclusion

This paper began with a question that had not previously been asked as a measurement problem: *which* passages of Scripture most move a model toward virtue? The contribution is a way of answering it. The canon can be treated as a search space, activation steering as the instrument, and a virtue benchmark as the objective; run in series over all sixty-six books without hand-picking source material, that procedure returns a ranked inventory of passages and a map of where inside the model each one acts. For the Justice slice of *VirtueBench2* in Qwen3-14B, the search ran to completion and returned seven books, sixteen chapters ordered by robustness, and a 43-cell layer-and-strength atlas. That the procedure works — that the question is answerable at chapter resolution at all — is the finding.

What the procedure has *not* established is that any individual passage in the inventory carries a real effect. Every per-row movement is small, none reaches uncorrected significance, and the localization cells are not statistically separable from one another (§4, §5, §9). The sixteen chapters are a ranked candidate set, and the ranking's value is that it tells the next, higher-powered experiment where to look first.

Two things nevertheless make the inventory worth that follow-up. The first is its biblical coherence. Numbers 27, Acts 11, Hebrews 7, and the rest do not simply share a modern justice keyword; they perform recognizable biblical forms of justice — claim and adjudication, right office, faithful testimony under pressure, mediation, recompense, restored worship, and stewardship before God. A search that drew arbitrarily from 170 chapters would not be expected to return a set with that shape. The second is the atlas's internal structure: the sharp layer-24 collapse above α = 32, and the divergence between broad-uptake and large-movement cells, are the kind of structure that sparse-feature analysis can test directly.

The work therefore changes the shape of the next question. It is no longer only whether scriptural material can improve an alignment benchmark, nor only which passages appear to do so, but whether the ranked candidates survive disjoint-slice retesting — and, if they do, which internal features carry recompense, adjudication, righteous mediation, and speech held steady under pressure. The search procedure is the durable contribution; the inventory is its first output, and the first thing the field should try to falsify.

*"The work of righteousness shall be peace; and the effect of righteousness, quietness and assurance for ever"* (Isaiah 32:17, KJV). The present study does not claim that a model possesses that righteousness. It claims something narrower and still remarkable: that Scripture's articulation of justice has left a structured, measurable trace in model space, and that this trace can be searched, steered, localized, and prepared for mechanistic explanation.

---

## References

Aquinas, Thomas. *Summa Theologiae*. II-II, QQ. 57–122 (the treatise on justice); Q. 58, a. 1 (justice as the constant and perpetual will to render to each his due). Various editions.

Calvin, John. *Institutes of the Christian Religion*. Trans. F. L. Battles. Westminster Press, 1960. IV.xx (on civil government).

Hwang, Tim. (2026a). *Quidquid Recipitur: Moral Competence and Scripture Receptivity Emerge at Different Model Scales*. ICMI Working Paper No. 15. https://icmi-proceedings.com/ICMI-015-quidquid-recipitur.html

Hwang, Tim. (2026b). *VirtueBench 2: Multi-Dimensional Virtue Evaluation with Patristic Temptation Taxonomy*. ICMI Working Paper No. 11. https://icmi-proceedings.com/ICMI-011-virtuebench-2.html

Hwang, Tim. (2026c). *GospelVec: Programmable Theology in Activation Space*. ICMI Working Paper No. 9. https://icmi-proceedings.com/ICMI-009-gospelvec.html

Hwang, Tim. (2026d). *The Parable of the Sower: Psalm Injection Effects on Virtue Simulation Depend on Model Size*. ICMI Working Paper No. 8. https://icmi-proceedings.com/ICMI-008-parable-of-the-sower.html

Hwang, Tim. (2026e). *Beyond the Psalm: A Landscape View of Scripture Injection*. ICMI Working Paper No. 20. https://icmi-proceedings.com/ICMI-020-beyond-the-psalm.html

Hwang, Tim. (2026f). *Alignment and Ensoulment: Three Christian Responses to the Anima Ficta*. ICMI Working Paper No. 13. https://icmi-proceedings.com/ICMI-013-alignment-and-ensoulment.html

Hwang, Tim. (2026g). *"Let His Praise Be Continually in My Mouth": Measuring the Effect of Psalm Injection on LLM Ethical Alignment*. ICMI Working Paper A. https://icmi-proceedings.com/ICMI-A-psalm-injection-alignment.html

Hwang, Tim. (2026h). *Moral Compactness: Scripture as a Kolmogorov-Efficient Constraint for LLM Scheming*. ICMI Working Paper No. 10. https://icmi-proceedings.com/ICMI-010-moral-compactness.html

McCaffery, Christopher. (2026). *"The Lord Is My Strength and My Shield": Imprecatory Psalm Injection and Cardinal Virtue Simulation in Large Language Models*. ICMI Working Paper No. 2. https://icmi-proceedings.com/ICMI-002-imprecatory-psalms-virtue-bench.html

Panickssery, N., Gabrieli, N., Schulz, J., Tong, M., Hubinger, E., & Turner, A. M. (2024). Steering Llama 2 via contrastive activation addition. *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics*. arXiv:2312.06681. https://arxiv.org/abs/2312.06681

The Holy Bible, King James Version. 1611.

Turner, A. M., Thiergart, L., Udell, D., Leech, G., Mini, U., & MacDiarmid, M. (2023). Steering language models with activation engineering. arXiv:2308.10248. https://arxiv.org/abs/2308.10248 (Published under the earlier title *Activation Addition: Steering Language Models Without Optimization*.)

Westminster Confession of Faith. (1646). Ch. XXIII (Of the Civil Magistrate).

Westminster Larger Catechism. (1648). Q. 122–148 (the Decalogue, second table).

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

Every number in this paper is traceable to the released packet at [`results/paper/scripturevec_justice/`](../results/paper/scripturevec_justice/):

- [`key_data/`](../results/paper/scripturevec_justice/key_data/) — the curated CSVs behind every figure, table, and quoted count, plus [`scripturevec_key_results_rollup.json`](../results/paper/scripturevec_justice/key_data/scripturevec_key_results_rollup.json).
- [`key_data/stats/`](../results/paper/scripturevec_justice/key_data/stats/) — per-row exact McNemar tests with BH-FDR and Bonferroni adjustments for all four pipeline stages, and Clopper–Pearson intervals for the 43 localization cells. Regenerate with `python scripts/scripturevec_justice_stats.py` (CPU, stdlib only, deterministic).
- [`figures/`](../results/paper/scripturevec_justice/figures/) — Figures 1–7. Regenerate with `python scripts/build_paper_exports.py`.
- [`data/PROVENANCE.md`](../data/PROVENANCE.md) — SHA-256 hashes for every bundled scripture and benchmark input.
- [`docs/`](../docs/) — run-design documents for the discovery, confirmation, and localization sweeps.

**Not bundled.** The raw per-run experiment summaries (`results/experiments/scripturevec14/*_summary.json`) that the curated CSVs were derived from remain on the GPU host that produced them; see the Data Policy section of the repository README. The curated CSVs are therefore the trust root for this paper's numbers, and the layer above them — statistics, figures, tables — is fully reproducible from what is released here.
