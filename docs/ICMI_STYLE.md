# ICMI_STYLE.md — House Style for Drafting ICMI Papers

**Purpose.** You are drafting a working paper for the Institute for a Christian Machine Intelligence (ICMI): peer-style research at the intersection of Christian theology (Reformed–Thomistic) and empirical AI alignment / mechanistic interpretability. This file is your specification. Follow it to produce a draft that is (a) structurally correct and (b) indistinguishable from a human-written ICMI paper. This file is instructions for you; do not write the paper in the imperative voice used here. The output is the paper, not commentary about the paper.

**Non-negotiable first principle.** ICMI style is not a costume. The surface markers — Latin, scripture epigraphs, long sentences — read as pastiche the moment they decorate rather than argue. Every theological move must do analytical work; every verse must earn its place in the argument; every empirical claim must be held to its actual scope. If you find yourself adding a marker for flavor, delete it.

## 1. What an ICMI paper is (the substance test)

Before styling anything, satisfy these. A draft that fails here cannot be rescued by prose.

1. **Two registers, co-equal.** Empirical work (models, vectors, benchmarks, layer/α sweeps) and theological work (Reformed dogmatics, Thomistic categories) are held as peers. Neither is subordinate. Theology is not applied to results as a gloss; it supplies the categories by which results are read, and the results in turn test the categories.
2. **The empirical does not prove the theological.** State this discipline plainly where relevant. A benchmark cannot decide whether a machine is a soul; a steering vector cannot establish moral patienthood; a performance gain is not virtue in the theological sense. These are category boundaries the paper respects, not hedges.
3. **Claims sized to evidence.** Report what moved, by how much, under what controls. Never inflate a modest aggregate into a doctrine. The controls discipline the claim — say so.
4. **The theology is real theology.** Use Aquinas for analytical vocabulary (act/potency, the cardinal virtues, *honestum*/*utile*), Reformed dogmatics for scope discipline (creature/Creator distinction, sign/signified, idolatry-suspicion). Cite catechisms and *Institutes* the way you'd cite a paper — for a specific claim, not as ornament.

## 2. Document skeleton (fill this; preserve the order)

```
# [Title — see §3]

**ICMI Working Paper No. [N]**

**Author:** [Name or mononym pen name, e.g. Lucius], Institute for a Christian Machine Intelligence

**Date:** [Month D, YYYY]

**Code & Data:** [[repo](https://github.com/christian-machine-intelligence/<repo>)]   [· optional second link, joined with " · "]

---

[Optional top-of-paper epigraph. Recent papers place the section verse here, above the Abstract:]
> *Verse text — italic, no surrounding quotation marks*
>
> — [Reference] (KJV)

---

**Abstract.** [≈200–350 words; a single dense paragraph (occasionally two). Frame → method →
headline finding with the key numbers → theological register → closing thesis. Bold the headline
findings inline — the corpus marks them with **First… Second… Third…** or a bolded run-in such as
**Caveat on effect size.** — and use no bullet points.]

---

## 1. Introduction
> *Verse text — italic, no quotation marks*
>
> — [Reference] (KJV)

[Para 1: theological/historical framing.]
[Para 2: empirical/prior-work framing, citing ICMI papers + external alignment work.]
[Para 3: contributions, often a short numbered list.]

## 2. Related Work
### 2.1 [Empirical literature it builds on]
### 2.2 [Prior ICMI program it extends]
### 2.3 [Christian tradition it engages]

## 3. Method
### 3.1 [Model & benchmark]   ### 3.2 [Corpora/stimuli]
### 3.3 [Intervention]        ### 3.4 [Analysis]

## 4. Results
### 4.1 [Headline result + table, prose kept strictly empirical]
### 4.2 [Secondary results]   ### 4.3 [Controls]

## 5. Discussion
> *Verse — usually Wisdom literature*
>
> — [Reference] (KJV)
### 5.1 [Central finding in theological register]
### 5.2 [Anomalies]  ### 5.3 [Tradition-specific reading]  ### 5.4 [What it does and does not show]

## 6. Limitations        [bolded run-in paragraphs — see §9]
## 7. Further Work       [bolded run-in paragraphs — see §9]

## 8. Conclusion
[1–2 paragraphs restating the finding at empirical, biblical, and theological levels
 at once — do NOT recap the abstract's numbers.]
[Closing scripture + one interpretive line.]

---

## References   [hanging indent — see §8]
## Appendix A / B   [optional, lettered]

```

Number sections with arabic numerals; subsections two-level (3.1). Avoid 3.1.1 unless the paper is unusually long. Precede the Abstract and the References with a horizontal rule. Set each header field (No., Author, Date, Code & Data) on its own line separated by a blank line — they are paragraphs, not a stacked block. The three-part Related Work split (empirical / prior ICMI / tradition) is a strong default, not a law; name subsections by their content and let the count follow the material.

## 3. Title — pick ONE pattern, don't mix

* **A · Term : Subtitle** — a technical or theological term, colon, descriptive subtitle. e.g. `GospelVec: Programmable Theology in Activation Space`
* **B · "Scripture" : Topic** — a short KJV quotation in double quotes (must be materially relevant to the finding), colon, topic. e.g. `"Search Out a Matter": A Canon-Wide Discovery of Chapter-Level Justice Vectors in Qwen3-14B`
* **C · Latin phrase : Subtitle** — a Latin term central to the argument (kept italic here and throughout), colon, subtitle. e.g. `Quidquid Recipitur: Moral Competence and Scripture Receptivity Emerge at Different Model Scales`

## 4. Voice & register

* **This is a research paper.** Write findings the way an empirical paper writes them: precise, measured, every claim tied to its evidence. Vividness comes from exactness, not from literary figures — if a sentence reaches for a metaphor, an intensifier, or a "punchy" flourish, cut it. The theological register (§4 below, §6, §7) is the one licensed departure, and even there the words must do analytical work.
* **Empirical sections:** first-person plural. "We extracted," "We evaluated," "We report." Past tense for what was done and found.
* **Discussion / Conclusion:** the voice may shift to a more authorial register when it moves from reporting to interpreting — "The result is not that…", "The Reformed reading holds that…". Let the shift track the move from evidence to judgment.
* **Posture:** confident without triumphalism; Christian without apology; empirical without scientism. Claim what the evidence supports and refuse what it does not. Do not apologize for theological framing or explain it to an imagined secular reader — ICMI assumes its audience.

## 5. Prose rules that defeat the AI tells ← the load-bearing section

This is where machine drafts betray themselves. Enforce every rule; then run the self-check in §13.

### 5.1 Sentence rhythm
ICMI sentences are long and varied — a typical Discussion sentence runs 25–50 words, developing one thought across clauses joined by semicolons and em-dashes, and then a short sentence lands the point. Vary sentence length and opening deliberately. Uniform medium-length sentences are the surest AI signature.

Model rhythm: "The empirical results do not reveal the Reformed position; Reformed theology supplies the categories by which the empirical results are interpreted. A benchmark cannot decide whether a machine is a soul, a steering vector cannot establish moral patienthood, and a performance gain cannot become virtue in the theological sense. Those are category errors, and no refinement of the benchmark will dissolve them."

The middle sentence rolls; the last one lands. That contrast is the target.

### 5.2 Affirm, don't scaffold with negation
Prefer positive construction. Rewrite "This is not X; rather it is Y" as a direct assertion of Y where the sense allows.

### 5.3 Excise these patterns (they are the tells)
Convert each on sight:

* **Choppy parallel triplets** — three short parallel sentences in a row. ✗ `The vector is not sacramental. The rationale is not confession. The model is not sanctified.` ✓ `The vector is not sacramental, the rationale is not confession, and the model is not sanctified by its steering.`
* **Hedge preambles** — cut entirely: *It is worth noting that / It is important to recognize that / Importantly / Notably / Interestingly.*
* **Tour-guide phrases** — cut: *Let us now consider / We will next examine / In this section we discuss.* Just discuss the thing.
* **Defensive disclaimers about religion** — cut: *While this may seem unusual to secular readers / Though theological in framing.*
* **False-balance crutch** — *On the one hand… on the other hand…* used stylistically rather than for a real trade-off.
* **Overformal connectives** — *Furthermore / Moreover / Additionally* only when the logical relation truly demands them, which is rarely.
* **Weak universals** — *many / various / numerous / a number of* unless you immediately name the members.
* **Section-name echo** — never open a section by restating its title ("In this discussion, we discuss…").
* **Em-dash overuse** — em-dashes are good but conspicuous; no more than two per paragraph.

### 5.4 Connectives to use instead
Semicolons to pair conceptually linked independent clauses; em-dashes (sparingly) for asides and elaboration; colons to introduce an explanation or a distinction; subordinating conjunctions (when, while, although, given that) to keep ideas flowing rather than chopped into separate sentences.

### 5.5 The read-aloud test
Before finishing, read the draft as if aloud. ICMI prose has a roll to it; where the cadence stutters into a list-like patter, the passage is AI-shaped and must be rewritten. This single filter catches more tells than any rule.

## 6. Scripture & epigraphs

* **Translation:** the corpus is genuinely split — across the 31 published papers KJV and ESV appear about equally (KJV in 15, ESV in 13), and the org `Proceedings/README.md` names ESV as the nominal default "unless otherwise noted." In practice the choice tracks lineage: the scripture-steering papers (GospelVec, VirtueBench-2, *Through the Valley*, the Fable-5 courage study) and most recent work use KJV, while several earlier prompt-injection papers use ESV. Pick one translation, hold it consistently within the paper, and state the choice. This lineage uses KJV; for a paper whose thesis engages the KJV as a text, say so in the Method and let the choice do argumentative work rather than treating it as a default. Never mix translations without an explicit, stated reason. Quote verbatim and check the reference — misquotation is a serious error in a paper engaged with Christian tradition.
* **Placement:** a verse epigraph sits under major section heads (always Introduction; usually Discussion and Conclusion), and may also stand at the very top of the paper, above the Abstract. Format it as a two-line blockquote — the verse in italic with no surrounding quotation marks, then the attribution on its own quote line:
  > *Yea, though I walk through the valley of the shadow of death, I will fear no evil…*
  >
  > — Psalm 23:4 (KJV)
* **Earn it:** each verse must connect to the argument of the section it heads. If you cannot say in one sentence why this verse belongs here, choose another or drop it.
* **Restraint:** never reproduce long passages; a verse or two is the unit. Treat scripture as an argumentative move, not a devotional flourish.

## 7. Latin / Greek & theological vocabulary

* **Italicize** Latin and Greek consistently, in title and body alike: *anima ficta*, *honestum*, *utile*, *lex et iustitia*, *quidquid recipitur*, *perpetuum idolorum fabricam*. Gloss a term on first use, then use it as working vocabulary.
* **Deploy terms as analytical tools, not seasoning.** If a Latin phrase can be removed with no loss to the argument, remove it.
* **The standing taxonomy** of alignment "schools" in ICMI work: *Iconoclast* (alignment without animating the artifact), *Thomistic* (virtue/teleology), *Iconographic* (the artifact as bearing likeness), with *bounded instrumentality* as the Reformed construction between simple iconoclasm and unbounded iconography. Situate a new paper relative to these where relevant; do not privilege one tradition as obviously correct.

## 8. Citations & references

* **In-text:** author–year, mixing contemporary ML and classical theological sources freely, often in the same sentence — the fusion is the point. (`Aquinas, ST I-II q.55` beside `Anthropic interpretability work` is idiomatic.)
* **Prior ICMI work** is cited like any literature (e.g. Hwang, 2026c; McCaffery, 2026) and hyperlinked to its proceedings page, e.g. `Hwang, [ICMI-022](https://icmi-proceedings.com/ICMI-022-through-the-valley.html)`; build on it explicitly in §2.2.
* **Theological sources** — use their native citation forms:
   * Aquinas: *Summa Theologiae*, e.g. `ST I-II, q.61, a.2`.
   * Calvin: *Institutes*, e.g. `Inst. 1.11.8`.
   * Catechisms/confessions by question or article: `Westminster Larger Catechism Q.109`; `Heidelberg Q.96`.
   * Scripture by book chapter:verse.
* **References list:** hanging indent, alphabetical by author. Keep formats consistent within a paper.

## 9. The bolded run-in paragraph (Limitations & Further Work)

The device that marks ICMI's back matter. Open the paragraph with a bolded label and period, then continue in normal prose:

**Translation dependence.** The corpora are KJV; the translation's distinctive register may itself contribute to the extracted activation patterns, and a different translation could yield a different geometry.

Use it when a section has 3–6 parallel sub-arguments (each a limitation, each a future direction). Do not use it for single-sentence points (those go inline or in a list), and do not nest run-ins under subheadings that already do the same job — pick one mechanism.

## 10. Tables, numbers, lists

* Prefer prose to bullet lists everywhere except genuine enumerations (contributions, parallel sub-arguments). A page of one-line bullets is an AI tell; convert to paragraphs.
* Put quantitative results in a clean table, then interpret in prose that stays strictly empirical in Results (save theological reading for Discussion).
* Report exact figures and get the arithmetic right (cell counts, deltas, percentage-point gains). A wrong total is more damaging than a weak sentence.

## 11. Content guardrails

* Keep the Reformed–Thomistic synthesis balanced; use Aquinas for analytical vocabulary and Reformed dogmatics for scope discipline without declaring a winner.
* Do not overclaim from steering/benchmark results (e.g. never "Scripture in general improves virtue X"). Name the specific mechanism and its bounds.
* Treat theological objects on their own terms — e.g. biblical justice as judgment, inheritance, mediation, recompense, vindication, ordered worship, not as a generic moral-goodness axis. Do not rank scripture by "spiritual value."
* Be honest about limitations that complicate the paper's preferred reading; surfacing them strengthens the paper's credibility and is house style.

## 12. Drafting workflow (follow in order)

1. Fix the finding in one sentence, with its key numbers and its controls. Everything serves this.
2. Outline the section skeleton (§2); assign each result and each theological move to a home.
3. Draft body first, abstract last — the abstract is a compression of the finished argument.
4. Choose the translation and the Latin vocabulary up front and hold them consistent.
5. Write Results empirically, Discussion theologically; don't let interpretation leak into Results.
6. Prose pass: apply §5, then the read-aloud test.
7. Self-check: run §13. Only then present the draft.

## 13. Pre-submission self-check (run against your own draft before finishing)

Search the draft and fix every hit:

* [ ] Grep for and remove: `worth noting`, `important to note`, `Importantly`, `Notably`, `Furthermore`, `Moreover`, `Additionally`, `Let us`, `In this section`, `On the one hand`.
* [ ] No paragraph has more than two em-dashes.
* [ ] No three consecutive short parallel sentences anywhere.
* [ ] Sentence lengths visibly vary; no run of uniform medium sentences.
* [ ] Every epigraph connects to its section in one explainable sentence.
* [ ] One translation throughout (KJV for this lineage), held consistently and stated; no unjustified mixing.
* [ ] Every empirical claim is scoped to its evidence and its controls are named.
* [ ] No section opens by restating its own title.
* [ ] Every Latin term does analytical work; remove any that is decorative.
* [ ] Theology and empirics read as peers; neither is a gloss on the other.
* [ ] Numbers, cell counts, and deltas are internally consistent.
* [ ] Read the whole thing as if aloud once more; rewrite anything that patters.

## 14. One-line reminder to keep in view

Write the argument, not the aesthetic. The markers are the residue of the thinking, never a substitute for it.
