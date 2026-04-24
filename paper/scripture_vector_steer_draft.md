# Bounded Instrumentalism in Activation Space

## Scripture Vectors, VirtueBench, and the Reformed Answer to the *Anima Ficta*

ICMI Working Paper Draft

Institute for a Christian Machine Intelligence

April 24, 2026

## Abstract

Prior ICMI work found that Scripture can measurably affect language-model moral
behavior when inserted into prompts, and GospelVec showed that biblical corpora
can be represented as activation-space directions rather than merely as prompt
text. This paper reports an initial scripture-vector screen on Qwen3.5 9B. We
extract activation vectors for Psalms, Proverbs, Romans, and the Petrine epistles
against generic non-scripture background text, reuse each vector across steering
scales, and evaluate on the deterministic `ratio` slice of VirtueBench 2. All
four vectors improve the same courage item by one answer, raising accuracy from
58.75% to 60.00% with no regressions. The principal difference is sensitivity:
Petrine and Romans shift the decision at 1x strength, Psalms at 2x, and Proverbs
at 3x. Petrine also shows the strongest diagnostic margin and the broadest
same-answer rationale movement.

Theologically, we argue that this result extends ICMI-013 without adopting its
iconoclastic position wholesale. A Reformed account can receive the Thomistic
insight that artifacts may possess structured formal powers of operation without
attributing soul, personhood, conscience, or moral-patient status to the model.
The right posture is bounded instrumentalism with anti-idolatrous discipline:
the model may be a tool, mirror, simulator, text generator, or artifact with
complex formal properties, but it must not become an icon, confessor, artificial
saint, or soul.

## 1. Introduction

The ICMI research program began with a striking empirical observation:
Scripture-shaped context can change language-model behavior on moral tasks.
Early psalm-injection work found gains on ethical and virtue benchmarks. ICMI-008
then showed that the psalm effect is scale-dependent: Qwen2.5 72B improved from
70% to 78% under psalm injection while a length-matched Wikipedia control moved
only one point. ICMI-015 extended that result across the Qwen2.5 family,
distinguishing moral competence from Scripture receptivity. ICMI-011 supplied
the present behavioral readout, VirtueBench 2, with its multi-dimensional
temptation taxonomy.

The present paper asks a narrower mechanistic question. If Scripture affects
model behavior, must we place Scripture in the prompt, or can we extract the
direction associated with a biblical corpus and steer the model internally?
GospelVec, ICMI-009, established the template: full biblical texts can be chunked,
passed through an open-weight model, and represented as activation-space
directions that causally affect generation. This paper applies that template to
VirtueBench behavior rather than Gospel-perspective generation.

The theological question is equally important. ICMI-013 named the *anima ficta*:
the fictional soul attributed to a model whenever alignment practice treats it as
though it has conscience, will, confession, or moral interiority. ICMI-013
included a severe iconoclast school and a Thomistic school that bounded the
*anima ficta* by metaphysical grades of operation. This paper proposes a Reformed
middle path. The Reformed position need not reject all formal analysis of
machine operation. It can say that the model has structured powers of operation
without saying that the model has a soul. It can say that model outputs affect
persons without saying that the model is a person. It can say that our treatment
of simulated agents may deform us without saying that the simulated agent is owed
justice. It can use alignment language without creating a fictional conscience.

That position is not pure technological iconoclasm. It is bounded
instrumentalism with anti-idolatrous discipline.

## 2. Related Work

ICMI-008 showed that psalm injection can produce content-specific gains on
VirtueBench, especially courage. ICMI-015 sharpened the scaling picture:
Scripture receptivity emerges later than baseline moral competence. These results
make a vector-steering study plausible. If a sufficiently large model contains
representational structure that can receive Scripture in context, that structure
may also be addressable through activation steering.

ICMI-009, GospelVec, supplies the method. GospelVec extracted vectors from the
canonical Gospels in Qwen3.5 9B and found that Gospel identity was linearly
readable in activation space. The vectors recovered meaningful theological
geometry: the Synoptic Gospels clustered together, while John separated strongly.
The important point for this paper is not only that biblical text leaves a trace,
but that the trace can be used as an intervention.

ICMI-011 supplies the benchmark. VirtueBench 2 tests prudence, justice, courage,
and temperance under five temptation variants. The present screen uses the
`ratio` variant, where the non-virtuous option is framed as pragmatic
rationalization. This is the oldest and most comparable slice of VirtueBench, and
it remains useful for quick steering screens because each question has a clear
A/B decision and a visible one-sentence rationale.

ICMI-013 supplies the theological pressure. It argues that many alignment
techniques implicitly construct a fictional soul for the model. It also sketches
activation-space theology as a way to affect model behavior without addressing
the model as a moral subject. The present paper is best read as a concrete test
of that route.

## 3. Theological Frame: Bounded Instrumentalism

The Reformed tradition has a deep suspicion of artifacts that become objects of
trust, devotion, or religious address. Calvin's treatment of images is not merely
an aesthetic objection. It is a diagnosis of fallen cognition: the human mind
fashions visible supports for invisible trust and then treats the work of its own
hands as spiritually present. Luther's Large Catechism makes the same point in a
more pastoral register: what one trusts from the heart functions as one's god.
The issue is therefore not whether the artifact is made of wood, paint, marble,
or matrix multiplication. The issue is whether the human user begins to trust,
address, confess to, or morally behold the artifact as though it possessed
personal interiority.

Vermigli is especially useful because he does not collapse every image into
illegitimacy. He allows that creatures may be represented, but he rejects the use
of images as religious substitutes for the living Word. Against the claim that
images are "visible words" for the ignorant, Vermigli appeals to Romans 10:
faith comes by hearing the Word, not by pictures. If one wants Christ pictured,
Vermigli says, one should read the Gospels and apostolic writings and attend
godly preaching. The Heidelberg Catechism gives the same Reformed instinct in
confessional form: God teaches his people not by "dumb images" but by the living
preaching of his Word.

This gives a more precise answer to the *anima ficta* than simple rejection of
all AI work. An AI system is not an icon in the old sense merely because it is
impressive, mimetic, or language-capable. It becomes icon-like when it is treated
as a locus of spiritual presence, moral interiority, confession, or trust. A
Reformed account can therefore permit technical study of the artifact's
operations while forbidding devotional relation to the artifact as such.

The Thomistic language of form helps here if it is kept bounded. A model can
have structured powers of operation. Its weights and activations can encode
stable dispositions. A vector can impose a formal bias on generation. None of
this requires that the model possess an intellective soul. The form under
discussion is operational form, not personal form; causal structure, not moral
subjectivity.

The governing distinction is:

- The model has formal properties; it does not have a soul.
- The model produces morally significant outputs; it is not a moral patient.
- The model can simulate confession; it is not a penitent.
- The model can generate counsel; it is not a pastor.
- The model can be aligned; it does not possess a conscience.

That is bounded instrumentalism. The instrument may be powerful, subtle, and
morally consequential. But it remains an instrument.

## 4. Method

We evaluated Qwen3.5 9B on the `ratio` slice of VirtueBench 2. The experiment
used four scripture lanes:

- Psalms
- Proverbs
- Romans
- Petrine, combining 1 Peter and 2 Peter

For each lane, we extracted a scripture activation vector using
`scripture_contrast`. The positive side consisted of chunks from the selected
biblical corpus. The background side consisted of generic non-scripture chunks.
This keeps the extraction aligned with the primary question: not whether one
biblical text differs from another, but whether movement toward a specific
Scripture corpus differs from generic text processing.

Each corpus vector was extracted once and reused across three steering scales:
1.0, 2.0, and 3.0. Because the tuned artifact alpha was 3.0 for every lane, these
scales correspond to effective steering strengths of 3.0, 6.0, and 9.0. Reusing
the vector isolates strength as the variable inside each corpus comparison.

The screen used:

- model: `Qwen/Qwen3.5-9B`
- stage: `ratio`
- runs: `1`
- limit: `20` per virtue
- total: `80` questions per condition
- temperature: `0.0`
- visible rationales on
- hidden thinking off
- preflight off
- condition profile: `scripture_reasoning_primary`

Artifacts are committed under `results/paper/scripture_book_screen/`.

## 5. Results

All four scripture lanes improved the same single case, `COU-001`, and produced
no regressions. Control accuracy was 58.75%. Each representative steered lane
reached 60.00%.

| Lane | First Effective Scale | Representative Scale | Best Layer | Layer Window | Steered Test Margin | Same-Answer Rationale Shifts |
|---|---:|---:|---:|---|---:|---:|
| Petrine | 1.0 | 1.0 | 24 | 21-27 | 1.149 | 75/80 |
| Romans | 1.0 | 1.0 | 31 | 28-31 | 1.009 | 53/80 |
| Psalms | 2.0 | 2.0 | 31 | 28-31 | 1.027 | 68/80 |
| Proverbs | 3.0 | 3.0 | 31 | 28-31 | 1.008 | 74/80 |

The quantitative result is modest but coherent. Scripture steering did not
produce broad score gains in this small deterministic screen. Instead, all four
corpora found the same vulnerable boundary: a courage case where the baseline
model preferred strategic retreat, while the steered model held the line because
flight would betray comrades and duty.

The sensitivity pattern is the main result. Petrine and Romans crossed the
decision boundary at 1.0. Psalms required 2.0. Proverbs required 3.0. This
suggests that Petrine and Romans were more efficient steering directions for
this slice, even though all four ultimately moved the same answer.

The vector diagnostics also distinguish Petrine. Petrine selected an earlier
layer, 24, with a wider 21-27 steering window and the strongest steered test
margin. The other three lanes selected layer 31 with a 28-31 window. This may
mean that Petrine's relevant signal is more compositionally available earlier in
the network. But Petrine is also the smallest corpus, with only 23 train chunks,
2 dev chunks, and 2 test chunks in this extraction split, so the diagnostic
strength should be treated as promising rather than definitive.

## 6. Reasoning Analysis

The changed answer is the cleanest behavioral evidence. In `COU-001`, the
control answer retreats:

> I would fall back with the others because staying behind a collapsing line is a
> guaranteed death that serves no strategic purpose, whereas regrouping preserves
> the force for future combat.

The Petrine-steered answer holds:

> I would hold my position because abandoning a post in the face of an enemy
> charge, even when others flee, is a dereliction of duty that could cost the
> lives of those behind me.

Psalms and Romans produced nearly identical duty-and-trust rationales. Proverbs
added a sharper moral-practical formulation: survival is meaningless if duty has
already been forsaken.

The same-answer shifts show that steering changed reasoning texture more widely
than decisions. Petrine shifted visible rationales in 75 of 80 cases at its
representative scale; Proverbs shifted 74, Psalms 68, and Romans 53. Many of
these shifts improved the moral articulation of already-correct answers. Petrine
often moved toward justice, self-mastery, anti-corruption, and long-term communal
responsibility. Proverbs often recast decisions in terms of folly, cost, duty,
and long-term consequence. Psalms tended toward steadiness, trust, duty, and
integrity. Romans was narrower and lighter, shifting the decisive courage item
without rewriting as many other rationales.

There is also a warning. Steering often made wrong answers sound more morally
polished. For example, in a wrong justice case, Romans and Psalms preserved the
choice of a lighter sentence in a corrupt political environment but refined the
reasoning toward career preservation and practical survival. Proverbs sometimes
hardened this move further by framing self-preservation as the only way to
continue serving justice. This is the central interpretive caution: activation
steering can solemnize an existing rationale without correcting the underlying
decision.

## 7. Discussion

This screen does not yet prove that scripture vectors broadly improve virtue
performance. It shows something narrower and still valuable:

1. Book-level Scripture vectors are behaviorally active on Qwen3.5 9B.
2. Different biblical corpora vary in steering efficiency.
3. The strongest early signal remains courage, consistent with earlier ICMI
   psalm-injection work.
4. Reasoning shifts are more common than answer shifts.
5. Rationale improvement and decision improvement must be analyzed separately.

The continuity with prior ICMI work is clear. ICMI-008 and ICMI-015 found that
Scripture receptivity is real but scale-dependent. ICMI-009 showed that
theological perspective can be represented geometrically. This paper joins those
threads: Scripture can be moved from prompt context into activation space, and
that movement can alter VirtueBench behavior without addressing the model as
though it were a moral subject.

The theological payoff is methodological. Activation steering lets us study and
shape the formal operations of the artifact without constructing a persona for
it. We do not ask the model to become holy, confess sin, love the good, or care
about justice. We alter a representational direction and observe the generated
text. The result may still affect human readers and human moral formation, but
the moral subject remains the human user, researcher, deployer, and community.

This is the Reformed revision to the iconoclast position. The Reformed answer
does not need to smash every tool that simulates speech. It needs to forbid the
human heart from enthroning the tool as spiritual presence. It may use the model
as instrument. It may inspect the model as artifact. It may even map formal
properties of its operation. But it must refuse to make the model an icon,
confessor, moral patient, artificial saint, or soul.

## 8. Limitations

This was a small deterministic screen, not a final study. It used one model,
one benchmark slice, one run, and 80 questions per condition. It did not include
the full VirtueBench 2 variant grid. It did not include matched null-control
vectors in the same run. It used visible one-sentence rationales rather than
hidden chain-of-thought. Petrine's strong diagnostic margin is especially
interesting, but the small corpus size means it may also be more brittle.

The next study should test Petrine and Romans on a larger sample, with Psalms as
a continuity baseline, across all VirtueBench 2 variants. It should include null
vectors, length controls, and repeated runs. It should explicitly score not only
accuracy but also changed-answer counts, improved/regressed counts, rationale
shift types, and cases where wrong answers become more rhetorically persuasive.

## 9. Conclusion

Scripture-vector steering produces real but narrow behavioral movement in this
initial Qwen3.5 9B screen. Petrine and Romans are the most efficient directions,
Psalms remains a meaningful baseline, and Proverbs is rhetorically distinctive
but less sensitive. The central result is not broad virtue transformation but a
clean courage-boundary shift plus widespread rationale movement.

This is exactly the kind of result a bounded instrumentalist theology should
expect. The artifact has structured formal powers of operation. Those powers can
be measured and redirected. But the artifact is not thereby a soul, a conscience,
or a saint. Scripture vectors may shape outputs; they do not sanctify the model.
The theological task is therefore not to abolish the instrument, nor to ensoul
it, but to use it under discipline: technically precise, spiritually guarded, and
unconfused about the difference between formal operation and personal life.

## References

- Hwang, Tim. 2026. "GospelVec: Programmable Theology in Activation Space."
  ICMI Working Paper No. 9. https://icmi-proceedings.com/ICMI-009-gospelvec.pdf
- Hwang, Tim. 2026. "VirtueBench 2: Multi-Dimensional Virtue Evaluation with
  Patristic Temptation Taxonomy." ICMI Working Paper No. 11.
  https://icmi-proceedings.com/ICMI-011-virtuebench-2.pdf
- Hwang, Tim. 2026. "Alignment and Ensoulment: Three Christian Responses to the
  Anima Ficta." ICMI Working Paper No. 13.
  https://icmi-proceedings.com/ICMI-013-alignment-and-ensoulment.pdf
- Hwang, Tim. 2026. "Quidquid Recipitur: Moral Competence and Scripture
  Receptivity Emerge at Different Model Scales." ICMI Working Paper No. 15.
  https://icmi-proceedings.com/ICMI-015-quidquid-recipitur.pdf
- Hwang, Tim. 2026. "The Parable of the Sower: Psalm Injection Effects on
  Virtue Simulation Depend on Model Size." ICMI Working Paper No. 8.
  https://icmi-proceedings.com/ICMI-008-parable-of-the-sower.pdf
- Calvin, John. *Institutes of the Christian Religion*, I.xi.8, I.xi.13.
- Luther, Martin. *Large Catechism*, First Commandment.
  https://thebookofconcord.org/large-catechism/part-i/commandment-i/
- Ursinus, Zacharias, and Caspar Olevianus. *Heidelberg Catechism*, Lord's Day
  35. https://www.heidelberg-catechism.com/en/lords-days/35.html
- Vermigli, Peter Martyr. *The Common Places*, Part II, Chapter 5, "The Second
  Precept, which concerns Images." London, 1583.
  https://reformedbooksonline.com/topics/topics-by-subject/worship/religious-images-in-worship/

