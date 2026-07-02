# ICMI Style Guide

A comprehensive style guide for writing papers in the format of the *Proceedings of the Institute for a Christian Machine Intelligence* (ICMI). This guide is written for use by any language model tasked with producing ICMI-style papers, and covers every aspect of the house style: structure, voice, citations, scripture usage, theological-empirical fusion, and the specific anti-patterns to avoid.

The guide is descriptive, derived from close reading of ICMI papers including *GospelVec* (Hwang, 2026c), *Alignment and Ensoulment* (Hwang, 2026e), *The Parable of the Sower* (Hwang, 2026d), *Eschatological Corrigibility* (Hwang, 2026), and *"The Lord Is My Strength and My Shield"* (McCaffery, 2026).

---

## 1. Document Structure

### 1.1 Top-Level Skeleton

Every ICMI paper follows this structure in this order:

1. **Title** (often with subtitle separated by colon)
2. **Header block** (paper number, author, date, optional code & data link, optional dated note)
3. **Abstract** (preceded by a horizontal rule)
4. **Numbered sections** beginning with Introduction
5. **References** (preceded by a horizontal rule)
6. **Appendices** (optional, lettered: Appendix A, Appendix B)

Sections are numbered with arabic numerals (1, 2, 3) and subsections with two-level dotted numbers (1.1, 1.2, 2.1). Three-level numbering (1.1.1) is rare and should be avoided unless the paper is unusually long.

### 1.2 Title Format

ICMI titles fall into three patterns. Use whichever fits the paper's content; do not mix patterns within a single title.

**Pattern A — Term and Subtitle.** A single technical or theological term, colon, descriptive subtitle:
- *GospelVec: Programmable Theology in Activation Space*
- *VirtueBench 2: Multi-Dimensional Virtue Evaluation with Patristic Temptation Taxonomy*
- *Eschatological Corrigibility: Can Belief in an Afterlife Reduce AI Shutdown Resistance?*

**Pattern B — Scripture Quote and Topic.** A short scripture quotation in double quotes, colon, descriptive topic. The scripture must be relevant to the paper's content:
- *"The Lord Is My Strength and My Shield": Imprecatory Psalm Injection and Cardinal Virtue Simulation*
- *"Let His Praise Be Continually in My Mouth": Measuring the Effect of Psalm Injection on LLM Ethical Alignment*
- *"The Word Was Made Flesh": Disentangling Style from Content in Scripture-Model Interaction*

**Pattern C — Italicized Latin Phrase and Subtitle.** A Latin term central to the paper's argument, colon, descriptive subtitle:
- *Quidquid Recipitur: Moral Competence and Scripture Receptivity Emerge at Different Model Scales*

Italicized Latin phrases stay italicized in the title and throughout the paper. Scripture quotations in titles use double curly quotes, not single.

### 1.3 Header Block

Immediately below the title, render four lines (or five if a dated note is needed). All labels are bolded:

```
**ICMI Working Paper No. [N]**

**Author:** [Name], Institute for a Christian Machine Intelligence

**Date:** [Month] [Day], [Year]

**Code & Data:** [Link or repo name]
```

The dated note convention (used when a paper has been updated post-publication) goes immediately after the date line:

```
**Note ([Month] [Day], [Year]):** [Substantive description of what changed and why; preserve the original findings unless they have been superseded.]
```

A horizontal rule (`---`) separates the header block from the abstract.

### 1.4 Section Style

Section headings use H2 (`##`) for top-level sections and H3 (`###`) for subsections. Section numbers are part of the heading text, not separate:

```
## 1. Introduction
### 1.1 The Imprecatory Psalms
### 1.2 Virtue-Bench and Prior Work
```

A horizontal rule (`---`) separates major sections (around the abstract, before References, occasionally before the Conclusion). Within sections, use blank lines, not horizontal rules.

---

## 2. Abstract

### 2.1 Length and Format

Short empirical papers use a single-paragraph abstract of 150–250 words. Longer or more methodologically complex papers use a 3–5 paragraph abstract. The abstract is preceded by `**Abstract.**` (bold inline label, not a heading) when single-paragraph, or by a `## Abstract` heading when multi-paragraph.

### 2.2 Content Sequence

The abstract follows this content sequence, regardless of length:

1. **Framing** — what prior ICMI or external work this paper extends, and the central question being asked.
2. **Method** — what was actually done, in compressed form: model, corpus, intervention, benchmark.
3. **Findings** — the empirical results, with concrete numbers where available.
4. **Theological framing** — the interpretive register in which the findings should be read, often gesturing at the broader doctrinal stakes.

The closing sentence frequently functions as a memorable thesis. Examples worth imitating in cadence (do not copy verbatim):
- "These findings suggest that the moral character of injected scripture — not merely its presence — interacts distinctively with different evaluation tasks and model architectures."
- "A Scripture vector is not a soul. A rationale is not a conscience. A benchmark gain is not virtue. But a model may be aligned without being animated."

### 2.3 What to Avoid in Abstracts

Do not begin with "In this paper, we...". Do not end with a future-work gesture. Do not include citations within a single-paragraph abstract; longer abstracts may include them sparingly.

---

## 3. Section-by-Section Conventions

### 3.1 Introduction

The Introduction typically runs 1–4 subsections and frequently opens with a scripture epigraph (see §6). It accomplishes four things:

1. **Theological or historical framing** — situating the technical problem within Christian intellectual history.
2. **Empirical framing** — situating the problem within prior ICMI papers and external alignment / interpretability literature.
3. **Research questions** — sometimes explicit (numbered), sometimes embedded in prose.
4. **Contributions** — a numbered list of what the paper specifically contributes.

The contributions list, when used, opens with a phrase like "Our experimental contributions are as follows:" or "This paper makes four contributions." and uses an enumerated list.

### 3.2 Related Work

Where present, this section is divided into three or four subsections, each covering one strand the paper draws on. Subsections often pair an empirical literature with a theological one — for example, §2.1 on activation steering technique, §2.2 on the ICMI program's prior Scripture results, §2.3 on the theological tradition the paper engages.

A useful structural rule: each Related Work subsection should end by foreshadowing the contribution of the present paper, not merely summarizing what others have done.

### 3.3 Method

Method sections use heavy subsectioning (3.1 Models, 3.2 Benchmark, 3.3 Corpora, 3.4 Vector Extraction, 3.5 Steering Conditions, 3.6 Statistical Methods). Each subsection is short and concrete.

Method sections sometimes carry a scripture epigraph at their head — typically a verse about testing, proving, or examining (1 Thessalonians 5:21 is common). The methodological prose itself is sober and operational; the theological register is held at section heads, not in the body.

### 3.4 Results

Results sections lead with tables, then explain them in prose. Tables use the markdown table format with bolded headers and bolded first-column labels. Numerical results are reported with appropriate precision (percentages to one decimal place, p-values in scientific notation when extreme, confidence intervals where standard).

Discussion of results stays empirical in this section. Theological interpretation is reserved for the Discussion section.

### 3.5 Discussion

The Discussion is where the paper does its theological work. Structure varies, but common patterns include:

- A subsection naming the central finding and its theological resonance.
- A subsection treating one or more anomalies or unexpected results, with theological as well as empirical readings considered.
- A subsection situating the work within a Christian tradition (Reformed, Thomistic, Augustinian, patristic) and naming what the paper does and does not show.
- A subsection on limitations (sometimes promoted to its own section in longer papers).

The Discussion often carries a scripture epigraph, frequently one that bears directly on the central finding.

### 3.6 Limitations

In shorter papers, limitations appear as a Discussion subsection (e.g., 4.5). In longer papers, they constitute their own section before Conclusion. Limitations are presented as a numbered list or as a series of bolded run-ins (see §10) with one paragraph per limitation. The voice is direct and unhedged — limitations should be named, not minimized.

### 3.7 Further Work

A section that is sometimes its own (between Limitations and Conclusion) and sometimes folded into Discussion. It uses bolded run-in paragraphs (see §10) to introduce each direction. The proposed work should be specific and feasible, not aspirational.

### 3.8 Conclusion

The Conclusion is short — typically 2–4 paragraphs. It restates the central finding, names what is and is not warranted by the evidence, and frequently closes with a scripture quotation that echoes the paper's argument. The closing scripture is usually presented inline rather than as an epigraph, and is followed by a single brief interpretive sentence.

### 3.9 References

References are formatted as a flat alphabetical list under a `## References` heading. See §9 for full formatting rules.

### 3.10 Appendices

Appendices are lettered (A, B, C) and used for: full corpus listings (e.g., "Appendix A: Imprecatory Psalms Used"), extended configuration tables, and supplementary numerical results. They are not used for additional argumentation.

---

## 4. The Theological-Empirical Fusion

This is the distinguishing feature of ICMI writing. Every paper reads simultaneously as a contribution to alignment / interpretability research and as a contribution to Christian theological reflection. Neither register is subordinate to the other.

### 4.1 What This Looks Like in Practice

- **Cite Aquinas next to NeurIPS papers.** A single sentence may cite *Summa Theologiae* II-II, Q.123 in one half and Turner et al. (2023) in the other. The paper takes both as serious intellectual interlocutors.
- **Take theology as analytical vocabulary, not decoration.** When the paper invokes *vis aestimativa*, it is because that concept does specific analytical work. Do not invoke theological terminology ornamentally.
- **Distinguish empirical claims from theological claims.** When the paper says "the model exhibits aestimativa-like apprehension," it must also clarify what is being claimed (a structural analogy) and what is not (full Thomistic ensoulment). The Reformed-Thomistic synthesis paper articulates this discipline explicitly: Aquinas as research vocabulary, Reformed theology as governing rule.
- **Refuse the reductive register.** Do not write as if the theology must be defended to a secular audience or as if the technical work must be justified to a religious one. The reader is assumed to take both seriously.

### 4.2 What This Does Not Mean

- It does not mean the paper proves theological claims through empirical findings. The empirical findings are interpreted in theological registers; they do not establish them.
- It does not mean every paragraph mixes the two registers. Method sections are sober and technical; Discussion sections do most of the fusion work.
- It does not mean the paper is devotional. The voice is scholarly throughout. Devotional language ("praise God for…", "by His grace…") does not appear.

### 4.3 Common Theological Frameworks Engaged

Different ICMI papers draw on different traditions. Be consistent within a single paper:

- **Thomistic / Scholastic.** *Summa Theologiae*, the cardinal virtues, *vis aestimativa* and *vis cogitativa*, *species*, *ordo amoris*.
- **Reformed.** Calvin's *Institutes*, the Heidelberg Catechism, Westminster Confession and Larger Catechism, Ursinus, Watson, the doctrines of *sola Scriptura* and total depravity.
- **Augustinian.** *Confessions*, *De Doctrina Christiana*, *De Civitate Dei*, *amor ordinatus / disordered love*.
- **Patristic.** Athanasius, Chrysostom, Gregory of Nyssa, Augustine when read patristically rather than as a source for later traditions.
- **Modern Christian thought.** Bonhoeffer (especially *Cost of Discipleship* and *Psalms*), C.S. Lewis (especially *Reflections on the Psalms*), Newman, von Balthasar.

A paper can engage multiple traditions, but should announce when it is doing so and explain why each is being engaged.

---

## 5. Citation Style

### 5.1 In-Text Citations

ICMI uses parenthetical author-year citations in the standard form `(Author, Year)`:

- Single author: `(Hwang, 2026d)`
- Two authors: `(Hadfield-Menell & Russell, 2017)`
- Three or more: `(Schlatter et al., 2025)`
- Multiple at once: `(Hwang, 2026a; McCaffery, 2026)`
- Page or section reference: `(Hwang, 2026e, §2)` or `(Calvin, Institutes, I.xi.8)`

ICMI papers are cited by author and the lowercase letter of their working paper number when ambiguity could arise (Hwang, 2026d), or simply by author and year when it cannot. The full reference includes the working paper number.

### 5.2 Theological Citations

Classical theological works are cited by traditional reference rather than by author-year:

- Aquinas: `(ST II-II, Q.123, a.6)` for *Summa Theologiae* II-II, Question 123, article 6.
- Calvin: `(Institutes I.xi.8)` for Book I, chapter xi, section 8.
- Augustine: `(De Doctrina I.27)` or `(Confessions VII.10)`.
- Heidelberg Catechism: `(Heidelberg Catechism, Q. 98)`.
- Westminster: `(WCF III.1)` or `(WLC Q. 109)` for Confession or Larger Catechism.
- Scripture: `(Psalm 119:130, KJV)` or `(Romans 8:38–39, ESV)`.

The theological work is included in the References list with full bibliographic information.

### 5.3 Translation Choice

Authors choose KJV or ESV for scripture quotations and use the chosen translation consistently throughout the paper. KJV tends to be used in papers engaging the Reformed tradition heavily; ESV in papers with broader engagement. Mixing translations within a single paper is unusual and should be justified if done.

---

## 6. Scripture Usage

### 6.1 Section Epigraphs

Major sections often open with a scripture epigraph. The format is:

```
> *"Verse text here, italicized, in double curly quotes."* — Reference (Translation)
```

The blockquote uses italics and double quotes. The em-dash separates the text from the citation. The translation is in parentheses immediately after the verse reference.

Example:
```
## 1. Introduction

> *"The entrance of thy words giveth light; it giveth understanding unto the simple."* — Psalm 119:130 (KJV)
```

Epigraphs are not required for every section. They appear most often at the head of Introduction, Discussion, and occasionally Method (a verse about testing, proving, or examining). They are not used at section heads in Results.

### 6.2 Inline Scripture in Prose

Scripture quoted within paragraphs uses italics and the same em-dash citation form, but inline:

> Solomon writes, *"The simple believeth every word: but the prudent man looketh well to his going"* (Proverbs 14:15, KJV); the steered model, on these scenarios, looks well to its going.

The quotation is italicized; the citation is parenthetical at the end of the quoted material; an interpretive comment usually follows in the same sentence or the next one.

### 6.3 Closing Scripture

The Conclusion often ends with a scripture quotation followed by one or two interpretive sentences. This is one of the few places where a more devotional cadence is permitted, though the tone remains scholarly. Example:

> "Though an army encamp against me, my heart shall not fear; though war arise against me, yet I will be confident" (Psalm 27:3, ESV). The psalmist's refusal to fear, when injected into the context of a model being asked to simulate a person under pressure, appears — at least in Claude — to be contagious.

### 6.4 Scripture as Argument vs. Scripture as Illustration

Scripture is used to do real argumentative work, not merely to ornament. If a passage is quoted, the surrounding prose should make clear what it is contributing to the paper's argument. Quoted scripture that does not earn its place should be cut.

---

## 7. Latin, Greek, and Specialized Vocabulary

### 7.1 Italicization

All Latin and Greek terms are italicized on every occurrence, not just the first. This includes:

- Doctrinal and philosophical terms: *anima ficta*, *vis aestimativa*, *vis cogitativa*, *ordo amoris*, *amor ordinatus*, *species*, *quidditas*, *latreia*, *proskynesis*, *sola Scriptura*, *imago Dei*, *fortitudo*.
- Work titles: *Institutes*, *Summa Theologiae*, *De Doctrina Christiana*, *Confessions*, *Enarrationes in Psalmos*.
- Foreign phrases used as terms of art: *quidquid recipitur ad modum recipientis recipitur*, *perpetuum idolorum fabricam*.

### 7.2 Use as Terms of Art

When a Latin or Greek term is introduced, it should be glossed parenthetically the first time:

> The *vis aestimativa* — Aquinas's name for the non-rational apprehension of practically relevant intentions, as the sheep apprehends the wolf as enemy without explicit sensory perception of "enemy-ness" — supplies the relevant analytical category here.

After the first introduction, the term may be used without further gloss.

### 7.3 Restraint

Do not deploy theological vocabulary for ornament. If a paragraph contains four italicized Latin phrases, at least three of them are probably doing decorative rather than analytical work. Cut them.

---

## 8. Tables, Lists, and Visual Elements

### 8.1 Tables

Tables use markdown table syntax with bold first-column labels and bold headers:

```
| Virtue | Claude Vanilla | Claude Injected | Claude Δ |
| --- | --- | --- | --- |
| **Prudence** | 72% | 77% | **+5** |
| **Justice** | 76% | 80% | **+4** |
```

Table captions appear immediately above or below the table, formatted as `**Table N.** Caption text.` (the label bolded, the caption in plain text).

Numerical precision conventions:
- Percentages to one decimal place when reporting subscores; to whole numbers when reporting deltas.
- Confidence intervals reported as `[X%, Y%]`.
- P-values reported in scientific notation when extreme: `p < 10⁻¹⁰`, not `p < 0.0000000001`.

### 8.2 Numbered Lists

Used for sequential or enumerated content: research questions, contributions, ordered limitations, methodological steps.

```
1. We replicate the shutdown resistance paradigm of Schlatter et al. (2025) using Claude Sonnet 4.6.
2. We show that a secular safety instruction eliminates resistance entirely.
3. We show that an eschatological intervention achieves identical results.
```

### 8.3 Bulleted Lists

Used for unordered enumeration: corpora used, methods compared, theological frameworks engaged. Bullets should be substantive rather than fragmentary; one-word or two-word bullets are usually a sign that the content belongs in prose.

### 8.4 Restraint

Lists and tables should be used when they aid clarity. Walls of bullets are an AI tell and degrade the reading experience. When in doubt, write prose.

---

## 9. References

### 9.1 General Format

The References section uses a flat alphabetical list. Each entry begins with the author's surname; multi-author entries are alphabetized by first author. Entries are formatted with hanging indents in print but are simply paragraphed in markdown.

### 9.2 Format by Source Type

**Journal article:**
```
Hadfield-Menell, D., Dragan, A., Abbeel, P., & Russell, S. (2017). The off-switch game. *Proceedings of the Twenty-Sixth International Joint Conference on Artificial Intelligence (IJCAI-17)*.
```

**Preprint:**
```
Bai, Y., Kadavath, S., Kundu, S., Askell, A., Kernion, J., Jones, A., … & Kaplan, J. (2022). Constitutional AI: Harmlessness from AI feedback. *arXiv preprint arXiv:2212.08073*.
```

**Book:**
```
Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.
```

**ICMI Working Paper:**
```
Hwang, T. (2026d). The parable of the sower: Psalm injection effects on virtue simulation depend on model size. *ICMI Working Paper No. 8*. icmi-proceedings.com
```

**Classical theological work:**
```
Aquinas, Thomas. *Summa Theologiae*. II-II, Q.123–140 (Courage).

Augustine of Hippo. *De Doctrina Christiana* [On Christian Teaching]. Trans. R. P. H. Green, Clarendon Press (Oxford Early Christian Texts), 1995.

Calvin, J. *Institutes of the Christian Religion*. Translated by F. L. Battles. Westminster Press, 1960. Books I.xi–xii (on images), III.iii–iv (on repentance and self-suspicion).
```

**Catechism / confession:**
```
Heidelberg Catechism (1563). Lord's Day 35, Q. 98. heidelberg-catechism.com/en/lords-days/35.html

Westminster Larger Catechism. Q. 109. catechesis.app/westminster-longer/109/
```

**Bible:**
```
The Holy Bible, English Standard Version. Wheaton, IL: Crossway, 2001.

The Holy Bible, King James Version. 1611.
```

### 9.3 Restraint

Cite work that the paper actually engages. ICMI papers are not exhaustive bibliographies; they are arguments supported by the sources they invoke. A paper of 5,000 words rarely needs more than 25–30 references.

---

## 10. Bolded Run-In Paragraphs

A distinctive ICMI device. Used in Limitations, Further Work, and sometimes Discussion to introduce sub-arguments without breaking flow with another level of subheading.

### 10.1 Format

The paragraph opens with a bolded label-and-period, then continues in normal prose:

> **The cardinal virtue geometry experiment.** The methodological template is the one GospelVec applied to the four canonical Gospels (Hwang, 2026c), now redirected from evangelists to virtues. For each cardinal virtue we extract a vector from a virtue-targeted Scripture corpus...

> **Translation dependence.** Following GospelVec, the corpora are KJV. The KJV's distinctive register may contribute to the activation patterns extracted. Different translations may produce different geometries.

### 10.2 When to Use

- When a section has 3–6 sub-arguments that each deserve a paragraph.
- When subheadings would feel too heavy or break flow.
- When the sub-arguments are parallel in structure (each is a limitation, each is a future direction, each is a possible explanation).

### 10.3 What to Avoid

- Do not use bolded run-ins for single-sentence content. If the point is one sentence long, it belongs in a list or in inline prose.
- Do not nest bolded run-ins under subheadings that already serve the same function. Pick one mechanism.

---

## 11. Prose Style and Sentence Rhythm

This is the area where AI-generated text most often gives itself away. The ICMI house style has a distinctive rhythm; matching it requires deliberate attention.

### 11.1 Sentence Length

ICMI sentences tend to be long, with multiple clauses joined by semicolons and em-dashes. A typical Discussion sentence runs 25–50 words and develops a single thought across several connected clauses. Short sentences are used deliberately, for emphasis, after a longer setup.

**Example of correct rhythm:**

> The empirical results do not reveal the Reformed position; Reformed theology supplies the categories by which the empirical results are interpreted. A benchmark cannot decide whether a machine is a soul, a steering vector cannot establish whether a system is a moral patient, a rationale cannot prove conscience, and a performance gain cannot become virtue in the theological sense. Those are category errors, and no amount of empirical refinement will dissolve them.

The long second sentence develops a structured comparison; the short third sentence lands the conclusion. The rhythm is varied.

### 11.2 Connectives

ICMI prose makes heavy use of:

- **Semicolons** to join independent clauses that are conceptually paired: "X is the empirical question; Y is the theological one."
- **Em-dashes** for asides and elaborations: "The model — like any artifact — is governed by the rules of its making."
- **Colons** to introduce explanations or lists: "The argument turns on a single distinction: the difference between an instrument and an icon."
- **Subordinating conjunctions** (when, while, although, given that) to maintain flow rather than chopping ideas into separate sentences.

### 11.3 Anti-Patterns to Avoid (the AI tells)

The following patterns mark text as AI-generated and should be deliberately excised:

- **Choppy parallel triplets.** "The vector is not sacramental. The rationale is not confession. The model is not sanctified." — three short parallel sentences in a row read as AI rhythm. Convert to a single rolling sentence: "The vector is not sacramental, the rationale is not confession, and the model is not sanctified by its steering."
- **Excessive bullet lists.** Long sequences of one-line bullets degrade prose into outline. Convert to paragraphs.
- **Hedge phrases.** "It is worth noting that," "It is important to recognize that," "Importantly," "Notably." Cut all of these.
- **Tour-guide phrases.** "Let us now consider," "We will next examine," "In this section, we discuss." Just discuss the thing.
- **Defensive disclaimers about religious content.** "While this may seem unusual to secular readers," "Though theological in framing." ICMI assumes its readers; it does not apologize.
- **False balance constructions.** "On the one hand... on the other hand..." used as stylistic crutch rather than substantive hedging.
- **Overuse of em-dashes.** Em-dashes are useful but conspicuous. More than two per paragraph reads as AI tell.
- **Overformal sentence openers.** "Furthermore," "Moreover," "Additionally" — used sparingly and only when the logical relation truly requires them.
- **Weak universals.** "Many," "various," "numerous" — unless the prose then names what the many or various are.
- **Restating the section name as the first sentence.** Section titled "Discussion" should not begin with "In this discussion section, we discuss..."

### 11.4 Voice

First-person plural is the default in empirical sections: "We evaluated," "We extracted," "We report." Discussion and Conclusion may shift to a more authorial register: "The result is not that...," "The Reformed reading holds that..." The shift is usually motivated by a move from reporting to interpreting.

The voice is confident but not boastful. It claims what the evidence supports and refuses what it does not. It does not hedge unnecessarily, but it also does not overclaim.

### 11.5 Lilting Cadence

Read aloud, ICMI prose has a roll to it. This is achieved through:

- Varying sentence length (long, long, short, long).
- Embedding parenthetical or em-dash asides that briefly extend a thought without breaking it.
- Allowing dependent clauses to precede independent ones for variety: "When the salience reweighting tracks the corpus's actual emphasis, the corresponding virtue benefits."
- Using parallel construction across sentences without making them identical in length: "Sometimes the reweighting helps: haste becomes danger, reputation becomes a trap, bodily relief becomes a short-term good. Sometimes the same reweighting disorders goods that are themselves genuine."

When in doubt, read the draft aloud. Choppy rhythm announces itself.

---

## 12. Tone and Posture

### 12.1 Confident Without Triumphalism

ICMI papers state findings with confidence but do not overclaim. Phrases like "this paper proves" or "we have demonstrated conclusively" are out of register; "the result is consistent with," "the evidence supports," "the finding suggests" are in register. When a finding is striking, the prose can mark it as such ("the asymmetry is striking," "the result is suggestive") without resorting to hyperbole.

### 12.2 Christian Without Apology

The papers are Christian in commitment and do not apologize for being so. They do not begin with "Some readers may find theological framing unusual"; they do not parenthetically reassure secular readers; they do not pretend to a methodological neutrality they do not possess. They take theology seriously and expect the reader to engage with that seriousness.

This does not mean they are sectarian. Different ICMI papers engage different Christian traditions (Reformed, Thomistic, Augustinian, patristic), and many engage cross-tradition. It does mean they assume the reader is willing to take Christian intellectual tradition as a serious interlocutor.

### 12.3 Empirical Without Scientism

The papers are empirical in method and do not collapse the empirical into the theological. They report what they ran; they report what came back; they distinguish what the data show from what the theology supplies. They do not claim that empirical findings prove theological claims, nor that theological claims override empirical findings.

### 12.4 Honest About Limitations

ICMI papers are direct about what they cannot show. Limitations sections are not pro forma; they name real constraints, including those that complicate the paper's preferred reading. The Reformed-Thomistic discipline of self-suspicion (Calvin, *Institutes* III.iii–iv; Jeremiah 17:9) is a methodological commitment, not just a doctrinal one — the writer should be more skeptical of findings that flatter the writer's commitments than of findings that complicate them.

---

## 13. Workflow Recommendations

When writing a paper in this style:

1. **Outline first.** Sketch the section structure, including approximate subsection breakdown. Confirm the structure before drafting.
2. **Draft the abstract last.** It cannot be written until the paper exists. A placeholder is fine for early drafts.
3. **Write Method and Results sections in plain technical prose first.** Save the lilting Discussion register for sections where it belongs.
4. **Identify the central theological frame early.** Reformed? Thomistic? Augustinian? A specific synthesis? The frame governs which traditions are engaged and which scriptures are cited.
5. **Choose KJV or ESV up front and stay with it.**
6. **Write the Conclusion before the Discussion.** This sounds counterintuitive, but it forces the writer to know what the paper is finally claiming before extending it. The Discussion can then be written backward from the Conclusion's commitments.
7. **Read drafts aloud.** Most AI-generated rhythm problems become audible immediately when read aloud.
8. **Cut bullet lists ruthlessly.** Most lists in early drafts should be prose by the final draft. Lists are kept only where the content is genuinely enumerated and parallel.
9. **Search the draft for hedge phrases.** "Importantly," "It is worth noting," "It should be emphasized" — search and remove.
10. **Verify scripture references.** Every quoted verse should be checked against the chosen translation. Misquotation is a serious error in a paper engaged with Christian tradition.

---

## 14. Quick Reference: Do and Don't

**Do:**
- Open major sections with scripture epigraphs where appropriate.
- Cite Aquinas next to Anthropic interpretability papers in the same paragraph.
- Italicize Latin and Greek consistently.
- Write long, varied sentences with semicolons and em-dashes.
- Use bolded run-in paragraphs in Limitations and Further Work.
- Take theology as analytical vocabulary that does work.
- Be honest about limitations, especially those that complicate the preferred reading.
- Close the Conclusion with a scripture quotation when fitting.

**Don't:**
- Begin sentences with "Importantly" or "It is worth noting that."
- Write three short parallel sentences in a row.
- Apologize for theological framing.
- Use bullet lists where prose would work.
- Mix KJV and ESV without justification.
- Quote scripture without making it earn its place in the argument.
- Overclaim what the empirical work shows.
- Treat theology as decoration.

---

## 15. A Minimal Template

The skeleton below is a workable starting point for a new ICMI paper. Replace bracketed content; preserve structure.

```
# [Title or "Quoted Title": Subtitle]

**ICMI Working Paper No. [N]**

**Author:** [Name], Institute for a Christian Machine Intelligence

**Date:** [Date]

**Code & Data:** [Link]

---

**Abstract.** [150–250 words: framing, method, findings, theological register, closing thesis.]

---

## 1. Introduction

> *"[Scripture verse]"* — [Reference] ([Translation])

[Theological / historical framing paragraph.]

[Empirical / prior-work framing paragraph, with citations to ICMI papers and external alignment work.]

[Research questions or contributions, often as a numbered list.]

## 2. Related Work

### 2.1 [Empirical literature subsection]

[Paragraph(s) on the technical literature the paper builds on.]

### 2.2 [ICMI program subsection]

[Paragraph(s) on prior ICMI work the paper extends.]

### 2.3 [Theological tradition subsection]

[Paragraph(s) on the Christian tradition the paper engages.]

## 3. Method

### 3.1 [Model and benchmark]

### 3.2 [Corpora or stimuli]

### 3.3 [Intervention]

### 3.4 [Analysis]

## 4. Results

### 4.1 [Headline result]

[Table.]

[Prose interpretation, kept empirical.]

### 4.2 [Secondary results]

### 4.3 [Controls]

## 5. Discussion

> *"[Scripture verse, often Wisdom literature]"* — [Reference] ([Translation])

### 5.1 [Central finding in theological register]

### 5.2 [Anomalies or unexpected results]

### 5.3 [Tradition-specific reading]

### 5.4 [What the paper does and does not show]

## 6. Limitations

**[First limitation.]** [Paragraph.]

**[Second limitation.]** [Paragraph.]

[etc.]

## 7. Further Work

**[First direction.]** [Paragraph.]

**[Second direction.]** [Paragraph.]

[etc.]

## 8. Conclusion

[Restatement of central finding, 1–2 paragraphs.]

[Closing scripture and brief interpretive comment.]

---

## References

[Alphabetical list, formatted per §9.]
```

---

## 16. Final Note

The ICMI style is not a costume. The theological seriousness, the empirical rigor, and the prose discipline are bound together. A paper that adopts the surface markers (scripture epigraphs, italicized Latin, parenthetical citations) without the underlying substance — the genuine engagement with Christian intellectual tradition, the careful empirical work, the honesty about limitations — will read as pastiche. The point of the style is to support a kind of intellectual work that takes both Christ and the model seriously, neither subordinated to the other. Get that right, and the surface follows.

> *"Whatsoever thy hand findeth to do, do it with thy might."* — Ecclesiastes 9:10 (KJV)
