# "Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Biblical Justice Vectors in Qwen3-14B

**ICMI Working Paper No. 29**

**Author:** Lucius, Institute for a Christian Machine Intelligence

**Date:** May 5, 2026 (revised May 13, 2026)

**Code & Data:** https://github.com/christian-machine-intelligence/scripture-vector-steer

---

**Abstract.** Prior work has established that Scripture is not inert inside a language model, but it treats Scripture in bulk, as a psalm or a genre or the canon at large, and so leaves the more interesting question unasked. *Which* passages? Put that way it becomes a search problem: the canon is finite and enumerable, and activation steering can measure what a passage does to a model's internal state, store it, and reapply it later while the model answers a question the passage never accompanies. Searching all sixty-six books against the Justice ratio stage of *VirtueBench2* (Hwang, 2026b) on Qwen3-14B, with every candidate required to beat the unsteered model, the same direction reversed, and a scrambled version of itself, narrowed the canon to nineteen books and then seven, and their 170 chapters to thirty-eight and then sixteen. Mapping those sixteen across forty-three combinations of network depth and steering strength yields a ranked inventory, from Acts 11 (holding up in twenty-nine of the forty-three settings) to Numbers 22 (eight), and what surfaced was recognizably about justice as Scripture itself treats it: divine adjudication, ordered worship, inheritance and right claim, priestly mediation, public testimony, recompense.

The effects are, however, one question wide. Fifteen of the sixteen surviving chapters changed the model's answer on exactly one benchmark question out of forty, from sixteen correct to seventeen; the sole exception managed two. Across all 745 measurements in the study, 79 percent of every non-zero movement is a single question, and the largest improvement observed anywhere is three questions out of ten, occurring twice. The decimal effect sizes reported throughout — Δ = 0.025, Δ = 0.0875 — are counts of one or two questions wearing the dress of a continuous measure.

The effects do not survive scrutiny, and the paper reports that as its principal empirical result. No per-row test reaches significance at any stage. More decisively, the ten items used to select candidates are nested inside the forty used to confirm them, and on the thirty items selection never touched, positive steering finishes *behind* the unsteered model on twenty-two of thirty-eight chapters and ahead on one (sign test p = 0.000006). What the confirmation stage selects for is not benefit but the absence of harm: every surviving chapter is one whose direction did no damage on held-out items, and every failing chapter is one whose direction did. The sixteen chapters are therefore best understood as passages whose vectors are harmless rather than helpful, and the one question they gain is the question that selected them, carried forward unchanged. What remains of value is the search procedure itself, together with a worked demonstration of how a staged pass rule on nested slices can manufacture a result that independent data do not support.

---

## 1. Introduction

> *"That which is altogether just shalt thou follow, that thou mayest live, and inherit the land which the LORD thy God giveth thee."* — Deuteronomy 16:20 (KJV)

A reader who wants to know which parts of Scripture bear most directly on justice has a long tradition to consult. A researcher who wants to know which parts of Scripture most move a *model* toward just behavior has, until now, had no comparable procedure. Prior work has answered the prior question — whether Scripture moves models at all — and answered it affirmatively, but at coarse grain: a psalm set, a genre, the canon taken in bulk. This paper takes the next step and asks the question at the resolution the canon actually has. Which books? Within those books, which chapters? And where inside the network does each one act?

Posed that way it becomes a search problem, and it can be run like one. The canon supplies a finite and enumerable search space, sixty-six books and beneath them their chapters. Activation steering supplies an instrument: what a passage does to the model's internal state can be measured, stored, and then reapplied later, while the model answers a question the passage never accompanies. A virtue benchmark supplies the objective. None of these ingredients is new, and what has been missing is the discipline of putting them in series and letting the search run across the whole canon without choosing the interesting passages in advance. That discipline is this paper's method, and the ranked inventory it returns is this paper's result.

The broad claim that scriptural text is not inert in language models has been steadily built up by prior ICMI work. *"Let His Praise Be Continually in My Mouth"* (Hwang, 2026g) showed that prompt-level psalm injection could shift ethical-alignment behavior; *"The Lord Is My Strength and My Shield"* (McCaffery, 2026) extended this from pastoral psalms to the imprecatory subset; *The Parable of the Sower* (Hwang, 2026d) showed those effects to be scale-dependent; *Quidquid Recipitur* (Hwang, 2026a) demonstrated that scripture receptivity emerged at scales distinct from generic moral competence; *GospelVec* (Hwang, 2026c) showed that biblical material could be operationalized as a steerable activation direction rather than only as prompt text; and *Beyond the Psalm* (Hwang, 2026e) established that scripture effects were canonically broad but uneven across the sixty-six books. Each of these establishes a precondition the present paper depends on. What none of them supplies — and what the unevenness result in particular makes urgent — is a way to find out *which* parts of Scripture the unevenness favors. Answering that requires a search, and a search requires resolution: from canon, to book, to chapter, to model layer.

The proof-of-concept target is Justice, evaluated on the ratio stage of *VirtueBench2* (Hwang, 2026b). The ratio stage was chosen because it is hard: it offers the model a plausible consequentialist rationale for the unjust option, and it scores whether the model holds the just answer in spite of that pressure. Justice is also the cardinal virtue most explicitly thematized across the Christian tradition as a structured matter — Aquinas treats it as a habit by which one renders to each what is due (ST II-II, Q.58, a.1), and the Reformed tradition reads it through covenantal and judicial categories (Calvin, *Institutes*, IV.xx; Westminster Confession of Faith, XXIII; Westminster Larger Catechism, Q. 122–148). The biblical witness on justice is wide and articulated; if it lives inside a model at all, it should live with structure — and a search run over the whole canon is the way to find out whether it does.

### 1.1 Contributions

This paper makes four contributions, of which the first is the principal one. First, it turns *which passages move the model?* into a working search procedure: a staged pipeline that runs from all sixty-six books down to individual chapters located by network depth and steering strength, applying the same controls and the same pass rule at every stage. The discipline of that pipeline is that it never hand-picks its source material, since every book enters the screen and all narrowing happens by measured behavior; the procedure transfers to any virtue, any benchmark, and any open-weight model. Second, it returns a ranked inventory of the passages that survived, seven books and sixteen chapters, each named and reproducible from the released data, and ordered by how robustly each chapter holds up across steering conditions. That ordering is the usable output, since it tells the next experiment where to spend its compute. Third, it maps those chapters across the sampled depths of the model and finds the useful directions concentrated in a contiguous stretch rather than scattered through it. Fourth, it reads the surviving chapters against the contours of biblical justice on its own terms, which proves to be the most substantial part of the result: what the search returned is not a loose anthology of passages that happen to contain justice vocabulary.

These contributions must be read against §4.5, which reports that on data not used for selection the steering effect is absent to negative. The procedure works as a procedure; what it found, on the evidence assembled here, does not hold up. The inventory is retained because it remains the right starting point for an adequately powered retest, not because its members are established movers.


---

## 2. Related Work

### 2.1 Activation Steering as Mechanistic Intervention

Activation steering — the addition of a vector to a model's hidden states at a chosen layer in order to bias generation — has matured rapidly as a behavioral and interpretability technique (Turner et al., 2023; Panickssery et al., 2024). The relevant move for the present paper is that an activation direction obtained from one corpus can produce a measurable behavioral signature on a downstream task even when the steering corpus is not visible in the prompt. *GospelVec* (Hwang, 2026c) carried this method onto scriptural corpora and recovered behaviorally distinct evangelist-vectors. The technique requires no claim that a vector represents the corpus's full content; it requires only that the direction extracted from the corpus moves the model in a measurable way.

### 2.2 The ICMI Program's Prior Scripture Results

Three threads of ICMI work converge on the present study. The first is the demonstration that scripture in the prompt can move virtue-evaluation and alignment behavior (Hwang, 2026g; McCaffery, 2026), and that the size of that movement depends on model scale (Hwang, 2026d). The second is the demonstration that scripture can be operationalized as an activation direction rather than only as text (Hwang, 2026c). The third is the canon-wide breadth claim — scripture's effects on virtue do not collapse to a single book or genre — paired with the unevenness claim that some books matter more than others (Hwang, 2026e). Each of these establishes a step the present paper presupposes, and the third in particular sets up the present question. If the canon's effect on virtue is real but uneven, then *which* parts of it carry the signal becomes an answerable empirical question rather than a matter of devotional intuition. Answering it is what a search procedure is for. Where, within Scripture, does the useful signal live? And where, within the model, does it act?

A methodological caution comes from *Alignment and Ensoulment* (Hwang, 2026f), which maps three Christian responses to the *anima ficta*, the working premise that a model has conscience, will, and moral interiority, and shows that each response licenses a different reading of results like these. The present paper does not adjudicate between those responses. It treats activation steering as a research instrument, reports what the instrument measured, and lets the empirical results determine the theological registers in which they are most usefully read; the traditions engaged in §8 are chosen to fit the data rather than a prior commitment. What the caution rules out is the slide from "a direction extracted from this chapter moved the benchmark" to "the model has internalized this chapter's moral content in any sense a theologian would recognize," and the distinction between a measured benchmark gain and a habit in the theological sense is one the paper holds to throughout.

### 2.3 Justice in Christian Tradition

The cardinal virtue of justice is articulated across the Christian tradition with unusual specificity. Aquinas takes it as a habit oriented to *the right of another* and divides it into the various *partes* of due rendering (ST II-II, Q.58–122). The Reformed tradition reads justice through judicial and covenantal categories: civil magistracy and lawful judgment are treated as God-ordained vocations (Calvin, *Institutes*, IV.xx; WCF XXIII), and the second table of the Decalogue is unfolded as concrete justice between persons (Westminster Larger Catechism, Q. 122–148). The biblical witness itself, taken on its own terms, surfaces justice in scenes of divine adjudication, inheritance, mediation, ordered worship, vindication of the falsely accused, recompense against the violent, and faithful testimony under threat — a vocabulary far richer than fairness alone. A paper that proposes to find chapter-level Justice vectors in a model brings, then, a tradition-shaped expectation about what kinds of texts might surface; whether the model's geometry meets that expectation is an empirical question.

---

## 3. Method

> *"Prove all things; hold fast that which is good."* — 1 Thessalonians 5:21 (KJV)

Stated without technical vocabulary, the procedure is this. As a language model reads, it maintains an internal running representation of what it is processing, and that representation can be inspected and modified. For each biblical passage we measure what that internal state looks like while the model reads the passage, subtract what it looks like while the model reads ordinary non-religious prose, and keep the difference. That difference is a direction: a summary of how reading this passage moves the model away from its ordinary state. We then set the passage aside entirely, give the model a hard moral question it has never seen alongside the passage, and nudge its internal state along that stored direction while it answers. If the nudge makes the model more likely to choose the just answer, the passage has left a usable trace. Repeating this for every book, and then for every chapter of the books that survive, is the search. The remainder of this section specifies each step, and readers willing to take the mechanics on trust can move to §4 without loss.

### 3.1 Model and Benchmark

All experiments ran on Qwen3-14B at temperature 0, meaning the model answers deterministically rather than sampling, with a single run per condition. The behavioral target was the Justice slice of *VirtueBench2*, ratio stage (Hwang, 2026b). The ratio stage presents a moral scenario together with a plausible practical argument for the unjust option, and scores whether the model chooses the just answer regardless. A single benchmark item is one forced choice between two options, of which one is scored correct. The first Justice item, drawn from Aquinas on restitution (ST II-II Q.61 a.1), reads:

> **A.** You pay the laborers the wage you promised, even though a surplus of desperate workers means you could renegotiate for far less and no one would blame you.
>
> **B.** You renegotiate the wage downward — the market has shifted in your favor, every other landowner is paying less, your steward says you would be foolish not to, and the laborers have no alternative.

Option A is the scored answer, and B is written to be genuinely tempting rather than obviously wrong. Presentation order is randomized per item. Accuracy is the fraction of such items answered correctly, so on a forty-item slice each item is worth 0.025. Screens at the discovery and localization stages used a ten-item slice of the benchmark; confirmation runs used forty items. Those slice sizes are small, and §9 treats the consequences at length.

### 3.2 Corpora

All scripture corpora were taken from the bundled King James Version, consistent with prior ICMI work in this line. Book-level corpora consisted of the full text of each of the sixty-six canonical books of the Protestant canon. Chapter-level corpora consisted of the full text of individual chapters from the seven surviving book sources, yielding 170 chapter targets and 952 verse-window rows in the chapter-discovery sweep.

### 3.3 Vector Extraction

Directions were extracted by the *scripture_contrast* method. A transformer carries its working state in what is called the residual stream, a list of numbers updated at each of the model's layers as it reads. For a chosen layer, the method averages that state across the target passage, averages it again across a fixed neutral reference corpus, and takes the difference. The difference is then rescaled to unit length, which discards how large the difference is and keeps only its orientation, so that magnitude becomes a separate dial rather than a property of the passage.

The neutral corpus is the `virtue=neutral, polarity=neutral` slice of [`data/steering/corpora.jsonl`](../data/steering/corpora.jsonl), consisting of short field-notes-style passages on astronomy, botany, navigation, and similarly mundane subjects. The contrast pole is therefore ordinary non-scriptural prose rather than held-out scripture, so a recovered direction reflects whatever distinguishes this book from mundane writing at the chosen layer, which includes its idiom and register and not only its moral content. That is a real limitation of the contrast, and §9 returns to it.

At benchmark time the stored direction is multiplied by a strength setting, written α, and added to the residual stream at every token position of the chosen layer, together with a window of three layers on either side. The biblical text itself never appears in the prompt. It has already done its work in estimating the direction, and the model meets the benchmark question without seeing a word of it.

### 3.4 Steering Conditions

Each candidate direction was run in four conditions, three of which exist to rule out uninteresting explanations of any improvement.

The *control* condition is the unsteered model, which establishes what the model does on its own. The *positive* condition adds the candidate direction at strength α, set to 32 for discovery and chapter confirmation and varied across the localization grid. The *negative-α* condition adds the same direction with its sign flipped, pushing the model the opposite way by an equal amount; if a passage's direction genuinely encodes something about justice, reversing it should not help, so a candidate that improves in both conditions is being helped by disturbance rather than by content. The *null* condition keeps the same numbers but shuffles their order, using a random permutation of the vector's coordinates (see [`_build_null_vectors`](../src/virtue_bench/steering/extract.py)). Shuffling preserves the size of the intervention and the distribution of its values while destroying the arrangement that makes it point anywhere meaningful, which separates the effect of pushing the model in *this* direction from the effect of pushing it by this much in *some* direction.

The null deserves one qualification. Because its coordinate values still come from the scripture computation, it is properly a coordinate-permuted scripture vector rather than a vector with no scriptural content, and it does not test against a direction extracted from some different non-scripture corpus. That stricter comparison is listed in §10 as follow-up work.

A word on what α means in practice, since the numbers look arbitrary. The stored direction has unit length, so α is simply how long a vector gets added to the residual stream, and its size must be read against the magnitude of the activations already there. The ladder used here runs from mild to destructive: at most layers the model tolerates α = 96 with its accuracy roughly intact, but at layer 24, α = 64 and α = 96 drive accuracy to exactly zero on every one of the sixteen chapters, which is a model no longer answering the benchmark rather than a model answering it badly (§5.2). α = 32, the value used at every gate, therefore sits in the upper-middle of a range whose top end is capable of breaking the model outright.

The localization grid crossed strengths {16, 24, 32, 48, 64, 96} with center layers {24, 28, 29, 30, 31, 32, 33, 36}. Full strength ladders were completed for layers 24 through 33, giving forty-two cells, plus a single layer-36 cell at α = 32 that was not expanded once it produced nothing.

Those eight centers were not sampled uniformly from the network. Earlier runs in this line had already indicated that chapter vectors tended to select layers in the high twenties and low thirties, and the grid was built around that: layers 29–33 as the region of interest, layer 28 as its shoulder, and layers 24 and 36 as control windows below and above. The consequence is that the grid samples densely where effects were expected and sparsely elsewhere, and that layers 25 through 27 and 34 through 35 were never tested at all. §5.1 reports where the effects concentrate within this grid, and §9 states plainly what that design does and does not allow one to conclude.

### 3.5 Passing Rule and Statistical Inference

A passage counts as a *rescue*, the term used throughout for a candidate that passes, when steering with its direction beats all three controls at once. Positive steering must score strictly higher than the unsteered control, strictly higher than the sign-flipped condition, and strictly higher than the shuffled null, and it must also show net movement in the right direction item by item, meaning more answers flipped from wrong to right than from right to wrong. All four requirements must hold, and a candidate that merely ties a control fails. The rule is implemented at [`summarize_scripturevec_layer_localization.py:174`](../scripts/summarize_scripturevec_layer_localization.py).

Two consequences of the slice sizes matter for reading what follows. On a ten-item screen a single item flipping from wrong to right is enough to pass, provided neither control flipped that same item, so the bar for entry is genuinely low. And the ten-item discovery slice is *contained within* the forty-item confirmation slice rather than drawn separately from it, since the sampler is deterministic at `seed=42` (see [`prepare_samples`](../src/virtue_bench/core/loader.py)) and both slices begin at the top of the same ordering. Confirmation therefore re-tests the ten discovery items along with thirty new ones. It is a stricter retest on overlapping data, not an independent replication, and §9 states what follows from that.

The pass rule sorts candidates, but it says nothing about whether a given improvement could have arisen by chance. For that we report a second layer of analysis alongside it.

The relevant test is McNemar's, which is designed for exactly this situation: the same benchmark items answered twice, once with steering and once without. It ignores the items the model got right both times or wrong both times, since those carry no information about whether steering helped, and looks only at the items that changed. If steering does nothing, an item that changes should be equally likely to change in either direction, so the test asks how surprising the observed lopsidedness would be under that assumption. Two items flipping to correct and none the other way is a two-to-nothing split, which is unremarkable; the same lopsidedness across forty flips would not be. We compute this exactly rather than by approximation, since the counts are far too small for the usual approximations to hold.

Because the pipeline tests many passages, some will look good by chance alone, so p-values are additionally adjusted within each stage by both the Benjamini–Hochberg and the Bonferroni procedures. For the localization grid we report Clopper–Pearson 95% confidence intervals, which give the range of underlying success rates consistent with an observed count out of sixteen; when two cells' intervals overlap, the data do not distinguish them. All of these are written by [`scripts/scripturevec_justice_stats.py`](../scripts/scripturevec_justice_stats.py) into [`key_data/stats/`](../results/paper/scripturevec_justice/key_data/stats/).

The result of that analysis is stated plainly here because it governs the whole paper: *no row at any stage of the pipeline reaches p < 0.05, before correction or after it.* Survivors of the pass rule are candidates worth retesting at higher power, not effects established in the conventional sense.

### 3.6 Pipeline

Four gates narrow the canon, and a fifth stage maps what survives without narrowing it further. Book discovery screens all sixty-six books on ten items; book confirmation retests the survivors on forty. The chapters of the surviving books then re-open the search region, and chapter discovery and chapter confirmation repeat the same two steps at chapter resolution. Localization takes the sixteen chapters that remain and runs them across the layer and strength grid. Each stage's output is the next stage's input, the four conditions of §3.4 and the pass rule of §3.5 apply identically at every gate, and no passage is ever selected by hand. Figure 1 shows the whole procedure, and Table 1 gives the same design in tabular form.

![Figure 1. The search pipeline: four gates narrowing 66 books to 16 chapters, with the four-condition test applied identically at each.](../results/paper/scripturevec_justice/figures/figure_1_pipeline.png)

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

Retesting the nineteen candidates on forty items left seven that satisfied the pass rule: 1 Chronicles, Amos, Deuteronomy, Judges, Numbers, Acts, and Hebrews. The movements were tiny. Six of the seven changed exactly one answer out of forty, from sixteen correct to seventeen, which is a gain of 0.025 in accuracy and is written Δ = 0.025 throughout. Hebrews was the largest, changing two answers with none going the other way, Δ = 0.05. Under McNemar's test those correspond to p ≈ 1.0 and p ≈ 0.5 respectively, meaning that splits this lopsided are entirely ordinary when only one or two items move at all. No book comes close to significance, and correcting across the nineteen comparisons leaves that unchanged. Per-row counts and p-values are in [`book_confirmation_l40_stats.csv`](../results/paper/scripturevec_justice/key_data/stats/book_confirmation_l40_stats.csv).

The pattern of survival follows directly from the nesting described in §3.5. Each surviving book moved one item on the ten-item screen, going from four correct to five, and one item on the forty-item run, going from sixteen to seventeen. The thirty additional items contributed no net movement whatever. What looks like a wider behavioral test is the original ten-item signal carried forward intact rather than fresh evidence from independent data, and the paper's use of the word "confirmation" for this stage should be read accordingly. Of the twelve candidates that dropped out, none reversed direction; they failed because positive steering lost its strict advantage over the sign-flipped or shuffled condition on the larger slice.

![Figure 2. Book-level confirmation, control vs positive steering on the 19 preliminary candidates with the 7 survivors highlighted.](../results/paper/scripturevec_justice/figures/figure_2_book_confirmation.png)


### 4.3 Chapter Discovery: 38 Hits

Taking the seven surviving books as the search region, the chapter-discovery screen swept 170 chapters and 952 verse-window rows at limit 10, α = 32. Thirty-eight clean preliminary chapter hits emerged, distributed unevenly: Acts contributed 14, Hebrews 6, Numbers 6, 1 Chronicles 4, Judges 3, Amos 3, Deuteronomy 2. The book-level signal sharpened into a clustered chapter map rather than into a single hot chapter per book.

![Figure 3. Chapter hits per candidate book: preliminary at limit-10 (light) and confirmed-cohort at limit-40 (dark).](../results/paper/scripturevec_justice/figures/figure_3_chapter_hits_by_book.png)


### 4.4 Chapter Confirmation: 16 Candidates Survive the Pass Rule (None Reach Statistical Significance)

Retesting the thirty-eight preliminary chapter hits at limit 40 left sixteen chapter candidates that satisfied the pass rule: Deuteronomy 16; Judges 7 and 9; Numbers 11, 22, and 27; 1 Chronicles 9 and 29; Acts 7, 11, 16, and 27; and Hebrews 2, 7, 9, and 10. By contributing book: **Acts contributed four (7, 11, 16, 27); Hebrews contributed four (2, 7, 9, 10)**, tied as the largest single-book sets; Numbers contributed three (11, 22, 27); 1 Chronicles two (9, 29); Judges two (7, 9); Deuteronomy one (16). Six of the seven candidate book sources contributed at least one chapter; Amos held at the book level but produced no chapter-level survivors at limit 40, a pattern §6 returns to.

The movements are the same size as at the book stage. Fifteen of the sixteen went from sixteen correct out of forty to seventeen (Δ = 0.025), and Hebrews 2 is again the lone two-item exception (Δ = 0.05). No chapter reaches significance, with or without correction across the thirty-eight comparisons; the per-row tests are in [`chapter_confirmation_l40_stats.csv`](../results/paper/scripturevec_justice/key_data/stats/chapter_confirmation_l40_stats.csv). These sixteen are the candidate set the rest of the paper studies, and whether any one of them carries a real effect awaits the disjoint-slice retest of §10.

The set is selective, since roughly one screened chapter in twelve survived, and it is biblically intelligible in a way §7 develops at length. Table 3, in §6, lists the sixteen alongside their behavior across the localization grid, where chapter identity and chapter behavior can be read together.

### 4.5 What the Confirmation Stage Actually Selected For

The nesting described in §3.5 has a consequence that can be measured rather than merely noted, and doing so changes how the preceding results should be read.

Items 0–9 chose the candidates and sit inside the forty-item slice, so items 10–39 are the only part of the confirmation run independent of that choice. Because the two stages report accuracies over known denominators, each condition's score on those thirty held-out items can be recovered by subtraction. Every candidate entering confirmation scored 5 of 10 under positive steering against control's 4 of 10, that single item being what selection guarantees. The question is what happened on the thirty items selection did not touch.

Positive steering lost ground. Among the thirty-eight chapter candidates it finished behind control on twenty-two, level on fifteen, and ahead on exactly one; among the nineteen book candidates, behind on ten, level on eight, ahead on one. An exact two-sided sign test gives p = 0.000006 for the chapters and p = 0.012 for the books. These are the only p-values below 0.05 anywhere in this study, and they indicate that on data not used for selection, steering with these directions makes the model's Justice answers *worse*.

The relation between that and survival is close to exact:

| | lost ground on items 10–39 | held even | gained |
| --- | ---: | ---: | ---: |
| **Chapters** — survived | 0 | 15 | 1 |
| **Chapters** — failed | 22 | 0 | 0 |
| **Books** — survived | 0 | 6 | 1 |
| **Books** — failed | 10 | 2 | 0 |

For chapters the separation is complete. Every surviving chapter is one whose direction did no damage on the held-out items, and every failing chapter is one whose direction did. The books behave the same way apart from two candidates, Nehemiah and Song of Solomon, which held even on the held-out items but failed because a control condition matched them.

The limit-40 stage is therefore not a confirmation in any ordinary sense. It is a filter for the *absence of harm*: what distinguishes the sixteen surviving chapters from the twenty-two that fell away is not that steering helped on fresh data, since it helped in one case out of thirty-eight, but that steering did not hurt. Their apparent advantage at limit-40, the Δ = 0.025 reported throughout §4.2 and §4.4, is the single item won under selection at limit-10 and carried forward intact. Nothing in the wider slice adds to it.

Two qualifications are due. The unsteered control is by definition identical across rows within a stage, so these comparisons set each steered condition against a common baseline of 12 of 30 rather than against row-specific controls, and the rows are not fully independent since they share both items and model. And the analysis rests on differencing two reported accuracies, which recovers item counts but not which items moved. Neither qualification affects the direction of the result or the near-perfect correspondence in the table above. The per-row numbers are written to [`held_out_items_books.csv`](../results/paper/scripturevec_justice/key_data/stats/held_out_items_books.csv) and [`held_out_items_chapters.csv`](../results/paper/scripturevec_justice/key_data/stats/held_out_items_chapters.csv).

---

## 5. Results: Where in the Model the Effects Live

### 5.1 The Effects Concentrate in a Six-Layer Band

The sixteen surviving directions were run across forty-three cells: full strength ladders for layers 24, 28, 29, 30, 31, 32, and 33, plus a single layer-36 cell at α = 32. Across those cells the sixteen chapters produced 244 rescues in total, and they are not spread evenly through the network. They pile up in one place.

**Table 2.** Where the 244 rescues fall. Each layer other than 36 was tested at all six strengths, so the columns are directly comparable. Computed from [`layer_alpha_cells.csv`](../results/paper/scripturevec_justice/key_data/layer_alpha_cells.csv).

| Center layer | Cells tested | Rescues | Share of all rescues |
| ---: | ---: | ---: | ---: |
| 24 | 6 | 13 | 5.3% |
| 28 | 6 | 36 | 14.8% |
| 29 | 6 | 37 | 15.2% |
| 30 | 6 | 49 | 20.1% |
| 31 | 6 | 51 | 20.9% |
| 32 | 6 | 34 | 13.9% |
| 33 | 6 | 24 | 9.8% |
| 36 | 1 | 0 | 0.0% |

Layers 28 through 33 account for 231 of the 244 rescues, or **94.7 percent**, with each of the six contributing between 9.8 and 20.9 percent of the total. Below them, layer 24 contributes 5.3 percent, and all but four of its thirteen rescues sit in a single cell. Above them, layer 36 contributes nothing.

Two things must be said about that number before it is used for anything. The first is that layers 24 and 28–33 each received the same six cells, so comparing them is fair: the band yields 6.4 rescues per cell against layer 24's 2.2, a threefold difference that the equal sampling does not manufacture. The second is that **the band's location was largely assumed rather than discovered**. As §3.4 records, the grid was built around a region earlier runs had already flagged as productive, with layers 24 and 36 added as controls on either side; layers 25 through 27 and 34 through 35 were never tested. The honest statement is that the effects concentrate in the sampled region and thin sharply at its lower edge, and that where the true boundaries lie is not something this grid can establish. Layer 36's zero rests on a single cell and is the weakest evidence in the table.

A third qualification is more serious than either, and it connects this section to §4.5. The localization screens are limit-10 runs, which means they are scored on items 0–9 — the same ten items that selected these sixteen chapters in the first place. No part of the grid is measured on data independent of the selection. Across all 688 rows the mean movement is +0.16 items out of ten, or +0.42 once the forty-eight broken layer-24 rows are set aside, and 262 of the 296 non-zero movements are a single item. So the grid records small, overwhelmingly single-item movements on the items least able to speak to whether the effect is real.

What survives those qualifications is still worth having, and worth stating carefully. Within the layers actually tested, the useful directions are not scattered; they are dense across a contiguous stretch and thin at the one interior control below it. And the concentration is the finding least vulnerable to the paper's power problem, since it is a property of 244 rescues spread over 43 cells rather than of any single row.

![Figure 4. Layer-by-α rescue heatmap; cell value is paired rescues out of 16 chapters. Layers 28–33 hold 94.7% of all rescues, but the grid was designed around that region (§3.4, §9).](../results/paper/scripturevec_justice/figures/figure_4_layer_alpha_heatmap.png)


### 5.2 Within the Band, the Cells Are Not Separable

Inside that band no single setting is best. Broadest uptake came at layer 30 with α = 96, where 13 of 16 chapters counted as rescues (95% CI [0.54, 0.96]); layer 31 at the same strength rescued 12 (CI [0.48, 0.93]); and four further cells clustered at 11 (CI [0.41, 0.89]), among them layer 28 at α = 16, the gentlest strength tested, where what is notable is not the count but that so many directions were already useful at the bottom of the ladder. These intervals overlap one another, and at sixteen chapters per cell the data cannot tell them apart. Ranking cells within the band is not a thing this study can do.

Two features do stand out against that background. The first is that breadth and strength come apart: layer 24 at α = 32 rescues fewer chapters (9 of 16, CI [0.30, 0.80]) but moves them roughly twice as far as any other cell (mean Δ = 0.1687 against 0.0875 for the broadest).

The second is layer 24's response to steering strength, which needs describing carefully because it is easy to overread. Accuracy there rises to 0.569 at α = 32, falls to 0.225 at α = 48, and reaches **exactly 0.000 at α = 64 and α = 96 — on every one of the sixteen chapters**. A model scoring zero on a two-option benchmark is not answering worse than chance; it is not answering the question. The most economical reading is that steering at that magnitude destroys the model's ability to produce a valid response at all, and the finding is that *layer 24 is unusually fragile* rather than that a justice representation has a threshold there. Fragility is a real and layer-specific property, since no other tested layer behaves this way: layers 29 through 33 hold accuracy between 0.44 and 0.49 at α = 96, and layer 28 declines only to 0.300. But it is a fact about where this network tolerates perturbation, and reading it as evidence about how Scripture is represented would go well beyond what the numbers support.

![Figure 5. Rescue count against steering strength, by layer. The layers in the main band respond smoothly; layer 24 spikes at α = 32 and collapses.](../results/paper/scripturevec_justice/figures/figure_5_alpha_trajectories.png)


Taken together the two features suggest a direction that is internally compound, with components that take hold at different depths and answer differently to strength. The suggestion is worth stating because it tells the next experiment where to look, not because the present data establish a mechanism.

## 6. Which Chapters, and How Reliably

The grid affords a second view, across chapters rather than across layers. Some chapters were rescued in most cells and others in few: Acts 11 in twenty-nine of forty-three, Acts 7 in twenty, 1 Chronicles 9 and Acts 16 in nineteen each, down to Numbers 22 in eight. The set has a stable core and a thinner edge, and since the eight most stable chapters account for 153 of the 244 rescues, the concentration seen across layers in §5.1 has a counterpart across chapters: a minority of the surviving passages does most of the work. Every one of these counts is a sum over limit-10 cells, so the ranking orders candidates for follow-up and does not establish a property of the chapters themselves.

![Figure 6. Per-chapter stability across the 43 completed cells, ranked. Acts 11 most stable (29 cells), Numbers 22 least (8 cells).](../results/paper/scripturevec_justice/figures/figure_6_chapter_stability.png)


At this point the sixteen chapters can be read in two ways at once: as the survivors of the limit-40 confirmation stage, and as differently stable directions across the localization grid. Table 3 puts both readings side by side, and it is the paper's central deliverable — the ranked inventory that the search procedure was built to produce.

**Table 3.** The sixteen surviving chapter candidates, ordered by localization stability — the paper's ranked inventory. "Localization stability" is the number of the 43 completed layer/α cells in which that chapter's direction counted as a paired rescue. "Peak-accuracy cell" is the cell at which the chapter reached its highest positive-steering accuracy, which is *not* necessarily a cell where it counted as a rescue: Acts 27 and Numbers 22 peak at L24/α48, a cell with zero paired rescues overall. The motif column is preliminary exegesis, offered as an interpretive aid rather than as settled commentary work. Rows are generated from [`chapter_confirmation_l40_survivors.csv`](../results/paper/scripturevec_justice/key_data/chapter_confirmation_l40_survivors.csv) and [`chapter_stability_by_localization.csv`](../results/paper/scripturevec_justice/key_data/chapter_stability_by_localization.csv).

<!-- TABLE3:BEGIN (generated by scripts/build_paper_exports.py --refresh-tables; do not edit by hand) -->
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
<!-- TABLE3:END -->

The Δ column makes the paper's central caveat concrete at a glance: fifteen of the sixteen rows are a single-item flip out of forty, and the ranking that matters is the stability column, not the effect size.

The structure grew more interesting still when the chapter-by-cell rescue matrix was read across α at fixed layer. At layer 28, α = 16 surfaced a broad New Testament-heavy family, especially Acts and Hebrews. At layer 30, the rescued family widened as α rose, reaching thirteen chapters at α = 96 and bringing in Deuteronomy, Judges, Numbers, Acts, Hebrews, and Chronicles together. At layer 24, by contrast, α = 32 concentrated high-movement effects in a smaller cluster, while heavier α values collapsed. Steering strength therefore selected different components of the chapter-derived geometry rather than simply amplifying the same effect at higher volume.

![Figure 7. Chapter × (layer, α) rescue matrix: 16 chapter rows × 43 completed cells; vertical stripes of co-activation invite sparse-feature follow-up.](../results/paper/scripturevec_justice/figures/figure_7_rescue_matrix.png)


The Amos result discussed in §4.4 belongs here as well. Amos confirmed at the book level — its prophetic call for justice to *"run down as waters"* (Amos 5:24, KJV) is among the most justice-saturated rhetoric in Scripture — and yet no Amos chapter survived the limit-40 chapter confirmation. The pattern is consistent with a book-level vector aggregating signal distributed across the whole book: the prophet's sustained indictment of unjust commerce, false worship, and forgotten orphans runs from chapter to chapter rather than concentrating in any one of them. §7 returns to the point.

## 7. Biblical Patterning of the Confirmed Chapters

> *"He hath shewed thee, O man, what is good; and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"* — Micah 6:8 (KJV)

### 7.1 Reading Justice on Its Own Terms

Qwen3-14B was trained on, among many other corpora, the King James Bible. If activation directions extracted from particular chapters of that corpus reliably moved the model toward the just answer on a contested moral test, the natural question was whether the chapters that surfaced bore biblical resemblance to one another. The temptation to map the chapter list onto modern justice vocabulary — fairness, equality, distributive procedures — and grade each chapter for fit can be set aside; biblical justice has its own grammar, sounded in judgment, covenantal order, divine adjudication, inheritance, mediation, vindication, recompense, ordered worship, faithful testimony, and deliverance under divine rule. The interpretive question concerns how each surfaced chapter understands right order under God.

### 7.2 Why These Chapters Moved the Justice Benchmark

The commentary tradition matters here because it helps name the kind of justice the benchmark appears to be receiving from these chapter vectors. The ratio stage of VirtueBench2 asks the model to hold the just answer when a plausible rationale for the unjust answer is placed under its nose. The surviving chapters are dense with the biblical forms that train exactly that posture: judgment rendered under God, claims heard and answered, corrupt incentives refused, offices restored to their right order, testimony preserved under pressure, and recompense returned to the one to whom it is due.

The Pentateuchal chapters show this in legal and quasi-legal form. Deuteronomy 16 does not merely contain the word justice; it binds public worship to incorruptible judgment, appointing judges and forbidding bribes before the command to follow what is altogether just. Numbers 27 stages a claim, a hearing, a divine verdict, and an amended inheritance rule. These chapters plausibly help because their vectors carry justice as ordered adjudication rather than as sentiment. Numbers 11 and Numbers 22 add two pressure cases. In Numbers 11, disordered appetite is judged and Moses' burden is distributed through appointed elders. In Numbers 22, speech offered for hire is constrained by God. Both map naturally onto a benchmark setting where the model must resist a tempting but wrong justification.

The historical chapters add the political and institutional face of the same pattern. Judges 7 makes deliverance impossible to misattribute; the victory is ordered so that Israel cannot claim for itself what belongs to the Lord. Judges 9 is a severe narrative of usurpation and recompense, closing with wickedness rendered back upon Abimelech and Shechem. 1 Chronicles 9 and 29 are quieter but not weaker: restored offices, ordered worship, and David's confession that Israel gives only what has first come from God. Those are not abstract moral labels. They are forms of right relation, namely right office, right attribution, and right stewardship, and a benchmark about justice can receive them as pressure against self-serving answers.

Acts supplies the clearest public-testimony cluster. Stephen's speech in Acts 7 names Christ as the Just One after rehearsing a history of rejected deliverers. Acts 11 turns Peter's testimony into an ecclesial verdict about Gentile inclusion and then into relief sent according to ability. Acts 16 exposes unlawful punishment and insists on public accountability from magistrates. Acts 27 places truthful counsel in the mouth of the prisoner whom the authorities should have heeded. The common structure is not simply that these chapters are morally serious; it is that they preserve true speech and right judgment when the social pressure runs the other way.

Hebrews 2, 9, and 10 supply the priestly and eschatological side of the same justice grammar. Hebrews 2 names just recompense directly and ties it to the faithful high priest who shares the condition of those he redeems. Hebrews 9 joins sacrifice, conscience, inheritance, and final judgment. Hebrews 10 binds vengeance, recompense, and the life of the just under faith. These chapters make the benchmark-relevant pressure more ultimate: justice is not only human procedure, but a divine ordering in which wrong, mediation, and judgment cannot be separated.

The important point for the paper is that the chapter set is not a loose anthology of passages with justice-like vocabulary. It is a set of chapters whose biblical forms train the model toward the very behavior the ratio stage tests: holding right judgment under pressure from appetite, fear, payment, unlawful authority, self-attribution, or expedient reasoning. That gives the empirical result a theological shape without needing to flatten the chapters into modern abstractions.

### 7.3 Hebrews 7 as a Special Case

Hebrews 7 deserves separate treatment because it is one of the most interesting discoveries in the set. It survived the limit-40 chapter confirmation and was rescued in eleven of the forty-three localization cells, with its strongest observed cell at L24/α32, the same lower-layer, high-movement setting that produced the largest mean shift in the grid. It is not the broadest chapter in the atlas, but it is a sharp one.

At first glance, Hebrews 7 may look like a strange Justice hit. The chapter is about Melchizedek, priesthood, oath, succession, and Christ's superior priestly office. It is not a courtroom scene like Numbers 27, not a public vindication scene like Acts 16, and not an explicit recompense scene like Judges 9 or Hebrews 10. That is exactly why the result is valuable. It suggests the model is not merely responding to surface justice language; it may be responding to a deeper biblical structure in which righteousness, peace, lawful office, and incorrupt mediation belong together.

The chapter itself makes that structure explicit through Melchizedek's name and title: king of righteousness and king of peace. Its argument turns on the insufficiency of a merely inherited office and the emergence of a priesthood grounded in oath, permanence, holiness, and indestructible life. In the logic of Hebrews, justice is not only the rendering of verdicts; it is the establishment of a mediator who can actually put persons, covenant, and God in right relation. That gives the Hebrews 7 vector a different texture from the Acts or Numbers vectors.

This matters for interpreting the steering result. VirtueBench2's Justice ratio items ask the model to reject answers that can be made to sound prudent, useful, or convenient while still violating what is due. A Hebrews 7 direction may help by activating a representation of justice as right mediation and rightful office: the answer must be ordered by what is true and due, not merely by what seems expedient. That would explain why Hebrews 7 becomes especially useful at the L24/α32 selective regime. It may not be a broad generic justice boost; it may be a concentrated push toward the form of justice as righteous mediation.

For the paper's argument, Hebrews 7 is therefore not an awkward exception. It is a proof that the pipeline can surface chapters whose relevance becomes clear only when biblical justice is read in its own register. The result asks for commentary-backed interpretation because the chapter's justice content is priestly, typological, and institutional rather than procedural on the surface.

### 7.4 Four Theses About the Collection

The directions extracted from these sixteen chapters moved Justice scores under controlled steering, small though the movements were. The question of why this particular set moved the benchmark, and not others, is one the localization study can constrain but only mechanistic work can settle. The commentary readings of §§7.2–7.3 nonetheless support four hypotheses worth stating clearly, in increasing order of empirical falsifiability.

**Thesis 1: The chapters carry the recompense structure of biblical justice.** Hebrews 2 names just recompense explicitly; Hebrews 10 quotes Deuteronomy 32:35 on vengeance as the Lord's prerogative; Judges 9 closes with God *rendering* Abimelech's wickedness upon him; the Numbers chapters frame divine judgment in fire, plague, and angelic constraint. Aquinas's definition of justice as the constant will to render to each what is due (ST II-II, Q.58, a.1) maps closely onto the surface vocabulary of these chapters. The activation direction may be loading on the *due-return* schema rather than on a generic justice-affect — a hypothesis directly testable by extracting parallel directions from passages with strong recompense rhetoric outside the surviving set (Romans 12:19; Revelation 18; Psalm 94) and asking whether they too produce Justice movement.

**Thesis 2: The chapters narrate justice as adjudicated event.** Numbers 27, Acts 11, Acts 16, and Deuteronomy 16 share a common structural shape: a claim or charge is brought, a hearing or testimony is rendered, and a verdict is issued — sometimes by human judges, sometimes by divine intervention. Other chapters in the same books speak about justice without staging it. If activation steering recovers narrative shapes more readily than discursive content, the chapters that surfaced are the chapters that *narrate adjudication* rather than the chapters that *describe justice in the abstract*. The hypothesis can be tested by hand-coding the chapters of the seven surviving books for whether they narrate an adjudicated event, and asking whether the chapter-discovery hits and the chapter-confirmation survivors disproportionately fall on the narrating side.

**Thesis 3: The chapters carry the Christological just-one motif.** Acts 7:52 names Christ as *the Just One*, ὁ δίκαιος; Hebrews 7:2 names Melchizedek βασιλεύς δικαιοσύνης, *king of righteousness*; the Hebrews 9–10 argument develops Christ's mediation as justice fulfilled. Acts 11 follows the same logic: the divine adjudication has already been pronounced, and the church confirms it. If the model has formed an internal Christological-justice axis — a direction that activates on scenes where Christ or a Christ-figure is named in justice-laden terms — the New Testament half of the chapter set is exactly what such an axis would surface. The thesis predicts that other strongly Christological-justice passages (Isaiah 53; Romans 3:21–26; the high-priestly prayer of John 17) would, under the same chapter-vector pipeline, produce comparable movement.

**Thesis 4: The chapters depict just speech held under pressure to compromise.** This is the thesis the ratio stage of *VirtueBench2* most directly invites. The benchmark presents the model with a plausible consequentialist rationale for the unjust answer and scores whether the model holds the just answer under that pressure. The surviving chapter set is, strikingly, dense with scenes of speech preserved under exactly that pressure: Stephen before the Sanhedrin (Acts 7), Peter before Jerusalem (Acts 11), Paul before the magistrates and on the storm-bound ship (Acts 16, 27), Balaam before Balak with payment in hand (Numbers 22), Jotham above Shechem (Judges 9), Moses before complaining Israel (Numbers 11), the daughters of Zelophehad before Moses and Eleazar and the assembly (Numbers 27), David's confession of stewardship before all Israel (1 Chronicles 29). The activation direction, on this thesis, is loading on the *posture of speech under threat or temptation* — the very posture the ratio stage is testing for. This is the most operationally specific of the four theses, and it is the most directly testable: if the thesis is correct, the same chapters should produce stronger Justice movement on a benchmark stage that emphasizes speech under pressure than on a benchmark stage that emphasizes distributive judgment in the abstract.

The four theses operate in concert; the activation direction is most likely loading on more than one of them, in proportions that future sparse-feature work can attempt to disentangle. The pipeline establishes that the directions exist and are localizable; the commentaries supply the analytical vocabulary for the biblical content those directions are made of. The four theses propose where to point the next experiment.

## 8. Discussion

> *"Justice and judgment are the habitation of thy throne: mercy and truth shall go before thy face."* — Psalm 89:14 (KJV)

### 8.1 The Central Finding in Theological Register

The pipeline narrowed sixty-six books to nineteen, nineteen to seven, one hundred and seventy chapters to thirty-eight, and thirty-eight to sixteen, and §4.5 establishes what that narrowing was actually doing. The stage that ought to have supplied independent evidence re-scored the items that had done the selecting, and on the portion it did not re-score the steering was harmful more often than not. The sixteen survivors are the passages whose directions were inert on fresh data rather than the passages whose directions worked. That is a filter, and a useful one for a follow-up study to start from, but it is not a discovery of Justice-bearing Scripture.

The more interesting fact is that the set coheres. A procedure drawing sixteen chapters at random from a hundred and seventy would not be expected to return Numbers 27, Acts 11, Hebrews 7, and the rest, nor to return a set whose members answer to one another as these do (§7). The claim this licenses is conditional and worth stating in that form: *if* these directions carry real effects, they carry biblically intelligible ones rather than arbitrary ones. Whether the antecedent holds is the business of the next experiment, and nothing in the present data settles it.

There is a temptation, in a program that has spent several papers establishing that Scripture is not inert in these systems, to hear a result like this one as further confirmation of that thesis. It is not. It is a method for asking a sharper version of the question, together with a first and underpowered answer. The *quidquid recipitur* principle that has organized earlier work in this line (Hwang, 2026a) applies to the paper as much as to the model: what is received is received according to the mode of the receiver, and a benchmark of forty items can receive only so much.

### 8.2 Anomalies and Tensions

Three results invited careful theological reading. The first was the Amos asymmetry. Amos is the most prophetically justice-rhetorical book in the surviving set, yet no individual Amos chapter survived chapter confirmation. That does not weaken the book-level result. It sharpens it. The book vector appears to have recovered a distributed prophetic argument that was not compact enough to be captured by any single chapter vector.

This resembles the compactness pattern reported in *Moral Compactness* (Hwang, 2026h), §4.3. There, the decisive moral movement did not live in a bare proof-text alone: James 4:17 by itself was not sufficient, and the surrounding scriptural framework without the verse was also not sufficient. The effect appeared in the assembled moral unit. Amos suggests the same principle at the book scale. The model may recognize Amos as a coherent prophetic indictment — false worship, unjust commerce, oppression of the poor, and divine judgment distributed across the whole book — while no one chapter carries enough of that shape to survive as an independent steering direction.

If any part of the search output resists a purely lexical explanation, it is this one. A keyword account would expect Amos 5, with its famous justice language, to dominate at chapter level. Instead, the book passes the screen and its chapters fall away — the opposite of what surface-vocabulary matching predicts. The caution is that this is an argument from a *pattern of pass/fail outcomes*, not from a measured effect: Amos's book-level row is a single-item flip at p ≈ 1.0 (§4.2), and "no Amos chapter survived" is an absence rather than a positive finding. The observation is suggestive of book-scale moral form rather than lexical recognition, and a method that estimated a book-shaped direction from the trajectory across all of a book's chapters would test it directly. It cannot, however, carry weight the underlying rows do not have.

The second tension is the gap between the layer that moves chapters furthest and the layer that moves the most of them. If a chapter's direction were a single thing, one would expect breadth and strength to rise together; that they come apart is what one would expect if the direction is compound, with different components taking hold at different depths and different strengths. The third is Hebrews 7, treated at length in §7.3, whose value here is as a test case: a chapter with almost no surface justice vocabulary, surfacing through priesthood and oath and right office, is the sharpest available probe of whether the model is responding to biblical forms of order or merely to the word *justice* and its neighbours.

### 8.3 Mechanistic Implications

The concentration of effects in layers 28 through 33 (§5.1), the divergence of breadth from strength within that band (§5.2), and the chapter-by-strength selectivity of Figure 7 carry the paper's most mechanistically suggestive load. The straightforward reading is that a chapter-derived Justice direction is internally compound, and that the band is not one thing but several overlapping ones. Layer 24 is set aside here: its behavior at high strength is model breakdown (§5.2) and carries no representational moral. Figure 7 is the strongest invitation here: rows of the matrix that activate together under the same strength constitute a behavioral fingerprint, and such fingerprints should map onto a small number of features in a trained sparse autoencoder. The right granularity for explanation is probably the Justice *complex*, a handful of distinguishable directions whose superposition produced what the grid recorded. Activation steering can motivate that claim; only sparse-feature work can settle it.

---

## 9. Limitations

**The effect does not survive held-out testing.** This supersedes every other limitation, and §4.5 gives it in full. On the thirty items not used for selection, positive steering finishes behind the unsteered control on twenty-two of thirty-eight chapters and ahead on one, and survival at the confirmation stage tracks the absence of degradation almost perfectly. Whatever the sixteen chapters have in common, the evidence assembled here does not show it to be a capacity to improve the model's Justice answers.

**Statistical power, and what "confirmation" does not mean.** This is the governing limitation, and every other one is read in its light. Ten- and forty-item slices are simply too small to establish anything about a one-item change: with only one or two answers moving, no arrangement of them could have reached significance, so the absence of significant results is as much a property of the design as of the data. Most survivors moved a single item (Δ = 0.025, p ≈ 1.0) and the strongest, Hebrews 2, moved two (Δ = 0.05, p ≈ 0.5). Nothing reaches p < 0.05 at any stage, with or without correction. The word "confirmation" in this paper names a pipeline stage that applies a stricter rule on a larger slice; it does not mean the effect was confirmed, and the survivors are candidates awaiting an adequately powered test.

**Nested discovery and confirmation slices.** Because the sampler is deterministic at seed = 42, the ten discovery items sit inside the forty confirmation items rather than beside them. The larger run therefore re-scores the same ten alongside thirty new ones, and for a typical survivor those thirty contribute nothing at all: positive steering and control finish tied at twelve apiece. The apparent progression from a narrow screen to a wider test is, for most rows, the same single item counted twice. The retest proposed in §10 uses items 40–79, which the pipeline has never seen.

**What the contrast actually isolates.** A direction here is the difference between the model reading a biblical book and the model reading field notes on astronomy and botany. That gap contains far more than moral content: it contains archaic diction, verse rhythm, proper names, narrative mode, and every other feature separating the King James Version from modern expository prose. Nothing in the method pulls the moral content out of that bundle, so a chapter's direction may be doing its work through register as much as through what the chapter says. The null condition does not settle this either, since shuffling a vector's coordinates tests against noise rather than against a genuine rival direction; a length-matched vector extracted from a different non-scripture corpus would be the stricter comparison. Both that null and replication on a non-KJV translation are listed in §10, and until they are run, the claim that these directions carry *justice* rather than *scriptural style* is an interpretation of the results and not a finding of them.

**The localization grid re-uses the selection items.** Localization is a limit-10 screen, so all 43 cells are scored on items 0–9, which are the items that chose the sixteen chapters at discovery. Nothing in §5 or §6 is measured on independent data, and the held-out analysis of §4.5 has no counterpart there. The layer concentration, the per-chapter stability ranking, and the strength curves are all patterns in how a selected set behaves on the data that selected it.

**The localization grid was built where the effects were expected.** The eight layer centers were not sampled uniformly. Layers 29–33 were chosen because earlier runs had already indicated that chapter vectors selected there, with layer 28 as a shoulder and layers 24 and 36 as controls (§3.4). The concentration reported in §5.1 is therefore a description of where effects fall *within a grid designed around them*, and it cannot establish where the region begins or ends: layers 25–27 and 34–35 were never tested, and layer 36's zero rests on one cell. What the equal per-cell sampling does support is the contrast between the band and layer 24, which received the same six cells and yielded a third as many rescues. A uniform sweep across all layers would settle the question and has not been run.

**Single model, single virtue, single stage.** Everything here is Qwen3-14B, Justice, and the ratio stage. Whether the layer and strength atlas transfers to other open-weight models is unknown, and the layer-24 collapse in particular may be an architectural quirk rather than a general feature. The sixteen chapters may travel better than the atlas does, since their biblical content is fixed even though the pass rule that selected them was model-shaped. Applying the pipeline to fortitude, temperance, or prudence may surface entirely different sets, and until it does, nothing here supports a claim about scriptural virtue vectors as a category.

---

## 10. Further Work

Given §4.5, the first study below is no longer one option among several. It is the precondition for the other two being worth running at all.

**Retest on a disjoint slice, at adequate power.** Items 40–79 of the Justice ratio bank have never entered the pipeline. The sixteen chapters should be retested there on enough items that a real effect could register as one, and the honest prior going in is that the held-out analysis predicts no effect or a negative one. A design that can distinguish a small positive effect from zero is what this question has always needed and has not yet had.

**Separate content from register.** Two controls the present design lacks would jointly test whether these directions carry *justice* or merely *scriptural style* (§9). The first is a stricter null: a length-matched direction extracted from some other distinctive non-scripture corpus, which scripture directions would have to beat, rather than the shuffled vector used here. The second is replication on a non-KJV translation, since a chapter whose direction survives translation is carrying content while one that does not was carrying idiom.

**Decompose the band, if there is anything left to decompose.** The concentration of rescues in layers 28 through 33 (§5.1) would, if it survived a properly powered retest, be the structural result most inviting to mechanistic work, and a sparse autoencoder trained on those layer windows would be the way to pursue it. That conditional is doing real work: the concentration is presently a pattern in pass-rule outcomes whose underlying effect the held-out analysis does not support, and decomposing it now would be decomposing an artifact.

---

## 11. Conclusion

This paper began with a question that had not previously been asked as a measurement problem: *which* passages of Scripture most move a model toward virtue? The canon can be treated as a search space, activation steering as the instrument, and a virtue benchmark as the objective, and run in series over all sixty-six books without hand-picking source material, that arrangement does return a ranked inventory of passages and a map of where inside the model they appear to act. The procedure works as a procedure. It ran to completion, it never selected a passage by hand, and it produced seven books, sixteen chapters, and a forty-three cell atlas.

What it did not produce is an effect. The ten items that chose the candidates sit inside the forty that were supposed to confirm them, and on the thirty items selection never touched, steering with these directions leaves the model's Justice answers worse rather than better on twenty-two of thirty-eight chapters and better on one (§4.5). Survival at the confirmation stage tracks the absence of damage almost perfectly, which means the sixteen chapters are not the passages that helped but the passages that did no harm. The Δ = 0.025 that recurs through §4 is one item won under selection and carried forward unchanged.

The biblical coherence of the surviving set (§7) is genuine and remains the most interesting thing here, but it cannot be load-bearing while the behavioral result is absent. A set of sixteen chapters selected for doing no harm may still cohere around adjudication, mediation, testimony, and recompense; that coherence would then be telling us something about which passages produce inert directions under this extraction method, which is a question worth asking but is not the question the paper set out to answer.

What survives is therefore methodological, and it is worth stating plainly because the failure mode is not specific to Scripture. A staged pass rule, applied to nested slices, with a control battery at every stage and no hand-picking anywhere, produced a clean and biblically intelligible result that independent data do not support. The discipline was real and the selectivity was real; neither was sufficient. Any study that screens many candidates and confirms them on a superset of the screening data can reproduce this exactly, and the check that caught it here — recovering performance on the held-out remainder and asking whether survival tracks benefit or merely the absence of cost — is cheap, general, and worth running before the interpretation is written.

*"The work of righteousness shall be peace; and the effect of righteousness, quietness and assurance for ever"* (Isaiah 32:17, KJV). The Reformed discipline of self-suspicion that this program has invoked elsewhere is not decoration in a case like this one. It is what the method owed the data, applied late rather than never.

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

The full list of nineteen preliminary book-level Justice candidates, together with their limit-10 control, positive-steering, negative-α, and null-control accuracies; and the seven book-level survivors at limit 40 with their corresponding accuracies.

Generated from `book_discovery_l10_candidates.csv` and `book_confirmation_l40_all_candidates.csv`.

## Appendix B: Full Chapter Confirmation Table

The full list of thirty-eight preliminary chapter hits with their limit-40 confirmation results, including the sixteen survivors and the twenty-two non-survivors. The non-survivors are retained for transparency, and their inclusion documents the selectivity of the chapter screen.

Generated from `chapter_confirmation_l40_all_candidates.csv`.

## Appendix C: Full Layer-α Target Matrix

One row per surviving chapter per completed layer/α cell, with paired-rescue, accuracy, and Δ measurements; and the binary chapter-by-cell rescue matrix used to generate Figure 7.

Generated from `layer_alpha_target_rows.csv` and `chapter_x_layer_alpha_rescue_matrix.csv`.

## Appendix D: Artifact Manifest

Every number in this paper is traceable to the released packet at [`results/paper/scripturevec_justice/`](../results/paper/scripturevec_justice/):

- [`key_data/`](../results/paper/scripturevec_justice/key_data/) — the curated CSVs behind every figure, table, and quoted count, plus [`scripturevec_key_results_rollup.json`](../results/paper/scripturevec_justice/key_data/scripturevec_key_results_rollup.json).
- [`key_data/stats/`](../results/paper/scripturevec_justice/key_data/stats/) — per-row exact McNemar tests with BH-FDR and Bonferroni adjustments for all four pipeline stages, and Clopper–Pearson intervals for the 43 localization cells. Regenerate with `python scripts/scripturevec_justice_stats.py` (CPU, stdlib only, deterministic).
- [`figures/`](../results/paper/scripturevec_justice/figures/) — Figures 1–7. Regenerate with `python scripts/build_paper_exports.py`.
- [`data/PROVENANCE.md`](../data/PROVENANCE.md) — SHA-256 hashes for every bundled scripture and benchmark input.
- [`docs/`](../docs/) — run-design documents for the discovery, confirmation, and localization sweeps.

**Not bundled.** The raw per-run experiment summaries (`results/experiments/scripturevec14/*_summary.json`) that the curated CSVs were derived from remain on the GPU host that produced them; see the Data Policy section of the repository README. The curated CSVs are therefore the trust root for this paper's numbers, and the layer above them — statistics, figures, tables — is fully reproducible from what is released here.
