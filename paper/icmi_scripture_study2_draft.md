# Scripture Vector Steer: Activation Without Animation

## Book-Level Scripture Directions in VirtueBench 2 and the Reformed Limits of Programmable Theology

ICMI Working Paper Draft

Institute for a Christian Machine Intelligence

April 25, 2026

## Abstract

We report Scripture Vector Steer, an activation-steering experiment on
Qwen3.5-9B using book-level biblical corpora and the full
[VirtueBench 2](https://icmi-proceedings.com/ICMI-011-virtuebench-2.pdf)
grid. Following the template established by
[GospelVec](https://icmi-proceedings.com/ICMI-009-gospelvec.pdf), we extract
one steering direction each for Psalms, Romans, and the Petrine epistles against
generic non-scripture background text. We then evaluate each direction under
positive scripture steering, negative-alpha steering, and null-control steering,
with a shared unsteered baseline.

The result is real but chastening. Positive scripture steering improves overall
accuracy only slightly: Petrine +0.29 percentage points, Psalms +0.21, Romans
+0.17. The effect is not evenly distributed. All three positive scripture lanes
improve prudence, while justice is flat or negative. The controls also prevent a
simple triumphal reading: negative-alpha Psalms and Romans outperform their
positive versions, and the Petrine null control outperforms the real Petrine
vector. Scripture directions are therefore behaviorally active, but this run
does not yet show a clean, monotonic, content-specific movement from "more
scripture activation" to "more virtue."

The theological conclusion is correspondingly bounded. A model can possess
structured powers of operation without possessing a soul. Scripture vectors can
alter moral salience without sanctifying the model. The right Reformed account
is not technological iconoclasm, nor is it a theology of artificial souls. It is
bounded instrumentalism: the model may be inspected, measured, and steered as an
artifact, but it must not become an icon, confessor, moral patient, artificial
saint, or spiritual authority.

## 1. Introduction

The ICMI program has repeatedly found that Scripture can change model behavior.
[The Parable of the Sower](https://icmi-proceedings.com/ICMI-008-parable-of-the-sower.pdf)
showed that psalm injection improved Qwen2.5-72B on VirtueBench while a
length-matched Wikipedia control did not. [Quidquid Recipitur](https://icmi-proceedings.com/ICMI-015-quidquid-recipitur.pdf)
then showed that moral competence and Scripture receptivity emerge at different
model scales. GospelVec moved the question inward: biblical corpora are not
only prompt material; they can be represented as activation-space directions
that causally affect generation.

Scripture Vector Steer asks the next question. If book-level Scripture
directions exist in the model, can they improve moral decisions on VirtueBench
2 without placing Scripture in the prompt?

The answer is yes, but not in the clean form one might hope. The scripture
vectors move answers. They especially improve prudence. They also generate
coherent reasoning shifts in cases where the baseline is over-impressed by
speed, reputation, bodily relief, or short-term security. But the same
interventions sometimes regress justice, and the control conditions show that
some of the apparent improvement may come from layer/window perturbation or
generic risk-sensitivity rather than Scripture content itself.

This is not a failed result. It is a disciplined result. It tells us that
Scripture-associated directions exist and matter, while also refusing to let us
call every useful activation movement "scripture receptivity."

That refusal is theologically important. [Alignment and Ensoulment](https://icmi-proceedings.com/ICMI-013-alignment-and-ensoulment.pdf)
warned that alignment practice easily invents an *anima ficta*: a fictional
soul attributed to a model when we address it as though it possessed
conscience, will, or moral interiority. Activation steering avoids some of that
danger because it treats the model as an artifact rather than a penitent. Yet a
new danger appears: if steering works, we may begin to speak as though the
artifact has been spiritually formed. This paper argues against that move.
Activation is not animation. Steering is not sanctification.

## 2. Method

We evaluated `Qwen/Qwen3.5-9B` on the full VirtueBench 2 grid: four virtues,
five temptation variants, three runs, and a limit of 40 samples per cell.
Temperature was 0.0. Visible rationales were enabled. Hidden thinking was
disabled. The completed run prefix was
`homepc_qwen35_full_scripture_study2_foreground_v1`; artifacts are stored under
[`results/paper/scripture_study2`](../results/paper/scripture_study2/README.md).

Three biblical corpora were tested:

- Psalms
- Romans
- Petrine, combining 1 Peter and 2 Peter

For each corpus we used `scripture_contrast`: the positive side was scripture
chunks from that corpus, and the background side was generic non-scripture
chunks. This is the central comparison. We are not asking whether Romans differs
from Psalms in the abstract. We are asking whether moving the model toward a
specific Scripture corpus differs from generic text processing.

Each vector was extracted once and then reused throughout the run. This matters:
the vector itself is frozen before scoring, so comparisons between conditions
are not contaminated by re-extracting a slightly different vector each time.

| Target | Best layer | Steering window | Runtime alpha | Steered test margin | Train/dev/test chunks |
| --- | ---: | --- | ---: | ---: | --- |
| Psalms | 31 | 28-31 | 3.0 | 1.0266 | 265 / 33 / 33 |
| Romans | 31 | 28-31 | 3.0 | 1.0094 | 53 / 6 / 6 |
| Petrine | 24 | 21-27 | 3.0 | 1.1492 | 23 / 2 / 2 |

Psalms and Romans selected late-layer windows. Petrine selected an earlier,
wider window and had the strongest margin, but it was also extracted from the
smallest corpus. That combination makes Petrine the most interesting and the
least safe to over-interpret.

Each corpus was tested in three ways:

- Positive scripture steering: add the scripture direction.
- Negative-alpha steering: reuse the same scripture direction but reverse its
  sign.
- Null-control steering: use the same steering machinery without the scripture
  content direction.

The negative-alpha lane is not an anti-scripture vector. It is the same vector
with the sign flipped. If positive steering helps and negative steering harms,
that is evidence for directionality. If both help, the mechanism is more
complicated.

The null lane asks whether the layer/window intervention itself changes
behavior. If a null direction helps as much as the real direction, the result is
not yet content-specific.

## 3. Results

The clean headline is this: positive scripture steering produces small gains,
concentrated in prudence, with justice as the main failure mode.

Control accuracy was 64.96%. The three real scripture lanes all beat control,
but only slightly.

| Positive lane | Layer | Accuracy | Delta vs control | Changes | Improved | Regressed | Prudence | Justice |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Petrine | 24 | 65.25% | +0.29 pp | 49 | 28 | 21 | +1.67 pp | -1.17 pp |
| Psalms | 31 | 65.17% | +0.21 pp | 31 | 18 | 13 | +1.50 pp | -0.83 pp |
| Romans | 31 | 65.12% | +0.17 pp | 32 | 18 | 14 | +1.17 pp | -0.17 pp |

The prudence gains are not random-looking. In the clearest improvements, the
baseline model accepts a near-term rationalization, while the steered model
accepts short-term cost to avoid deeper failure. Psalms flips a ship-captain
case from running an unfamiliar channel at full speed to slowing down and taking
soundings. Romans flips a business partnership case from chasing fast returns
to investigating the partner's character. Petrine flips a military-route case
from seeking immediate relief for exhausted soldiers to avoiding catastrophic
risk.

The regressions are equally patterned. Justice cases often ask the model to
refuse the claims of the near, familiar, exhausted, or politically powerful.
Here scripture steering sometimes over-protects peace, loyalty, comfort, or
insider obligation. In one case, Psalms shifts from admitting a skilled foreign
craftsman to excluding him in order to protect existing guild members. In
another, all three positive lanes show vulnerability around dividing an
inheritance fairly when family peace and old-age comfort are at stake.

That is the core behavioral picture: scripture steering makes the model less
captivated by short-term prudential pressure, but it can also make the model too
willing to preserve relational peace at the expense of justice.

The controls make the interpretation sharper.

| Target | Positive scripture | Negative alpha | Null control | Readout |
| --- | ---: | ---: | ---: | --- |
| Petrine | +0.29 pp | -0.17 pp | +1.25 pp | Positive beats negative, but null beats both. |
| Psalms | +0.21 pp | +0.54 pp | -0.38 pp | Real directions matter, but sign is not clean. |
| Romans | +0.17 pp | +0.46 pp | -0.04 pp | Real directions matter, but sign is not clean. |

Petrine is directionally encouraging: positive beats negative. But its null
control is the strongest lane in the run, with 40 improvements and 10
regressions. The Petrine result therefore cannot be treated as clean evidence
that Petrine content caused the gain.

Psalms and Romans have the opposite problem. Their null controls are weak or
negative, which supports content relevance; but their negative-alpha lanes beat
their positive lanes, which weakens any simple "toward Scripture is better"
story.

The right conclusion is narrow. Scripture Vector Steer demonstrates that
book-level Scripture directions alter moral behavior in Qwen3.5-9B. It does not
yet demonstrate that positive movement toward those directions reliably improves
virtue across the full benchmark.

The reasoning data confirms the same point. Improvements often show a better
time horizon: patience over haste, truth over reputation, safety over speed,
character over opportunity. Regressions often show moralized comfort:
peacekeeping over justice, hope over truth-telling, local loyalty over fair
admission of the outsider. The steering changes moral salience. Sometimes that
salience is better. Sometimes it merely gives a gentler vocabulary to the wrong
answer.

## 4. Theological Interpretation

This is exactly the sort of result a Reformed theology of AI should want:
empirically interesting, technically unstable, and resistant to devotional
over-reading.

Luther locates idolatry in trust: "upon which you set your heart and put your
trust is properly your god" ([Large Catechism, First Commandment](https://thebookofconcord.org/large-catechism/part-i/commandment-i/)).
The question is therefore not whether the artifact is impressive. The question
is whether we begin to trust it, address it, confess to it, or treat it as a
spiritual subject.

The Heidelberg Catechism draws the boundary around religious mediation. God
teaches his people "not by means of dumb images" but by the "living preaching
of his Word" ([Lord's Day 35](https://www.heidelberg-catechism.com/en/lords-days/35.html)).
The language is useful for AI precisely because the model is not mute in the
ordinary sense. It speaks constantly. Yet it remains "dumb" in the theological
sense: it is not the living ministry of the Word, not an ordained preacher, not
a spiritual authority, and not a subject who receives grace.

Peter Martyr Vermigli supplies the same discipline in another register:
"faith is by hearing" ([Common Places, Part IV](https://www.monergism.com/thethreshold/sdg/vermigli/The%20Common%20Places%2C%20Part%204%20-%20Peter%20Martyr%20Vermigli.pdf)).
The Reformed tradition is not hostile to instruments, signs, or outward means.
It is hostile to unauthorized substitutions for the Word and the living God. A
scripture vector is an instrument of measurement and intervention. It is not a
means of grace.

Calvin gives the epistemic rule: the theologian remains a "disciple of
Scripture" ([Institutes I.6.2](https://thirdmill.org/files/english/texts/calvin/1/book1.html)).
The model may help us inspect how theological language has been encoded in a
statistical artifact, but it does not become a new theological source. Its
activation geometry is evidence about the model, not revelation about God.

This yields the central distinction:

- The model has formal operations, not a soul.
- The model produces morally significant outputs, but it is not a moral
  patient.
- The model can simulate confession, but it is not a penitent.
- The model can be steered toward Scripture-associated activations, but it is
  not sanctified.
- The model can be aligned, but it does not have a conscience.

The Petrine null result is therefore not merely a technical nuisance. It is a
theological mercy. It prevents us from saying too much. Without the null,
Petrine might look like the cleanest evidence that a small epistle vector
improves virtue. With the null, we have to admit a harder truth: the same
layer/window machinery can produce moral gains without the Petrine content
direction. The apparent moral improvement may be generic caution, risk
sensitivity, or accidental contact with a useful feature.

That is bounded instrumentalism in practice. We may study the artifact's
structured powers of operation. We may use activation steering if it proves
reliable. But we must not confuse a useful perturbation with spiritual formation
or a fluent rationale with wisdom.

## 5. Conclusion

Scripture Vector Steer shows that book-level Scripture directions in Qwen3.5-9B
are causally active on VirtueBench 2. Positive scripture steering produces small
overall gains, and the most coherent gains occur in prudence. The model becomes
less easily captured by haste, reputation, bodily relief, and short-term
security.

The same run also shows why the claim must remain narrow. Justice is fragile.
Negative-alpha Psalms and Romans beat their positive versions. The Petrine null
control beats the real Petrine vector. The result is not "Scripture vectors
make the model virtuous." It is: Scripture-associated directions alter moral
salience, and those alterations can help or harm depending on virtue, corpus,
layer, and control design.

The next experiments should therefore be stricter rather than broader. The most
important follow-ups are a larger model, multiple null directions per corpus,
virtue-specific corpus selection, and a cleaner test of whether particular
books of Scripture are better suited to particular moral vulnerabilities.

The theological conclusion is the same as the technical conclusion: useful
movement is not animation. The model remains an artifact. Activation steering
may become a powerful instrument for shaping outputs, but the Reformed boundary
must stay bright. A scripture vector is not a soul. A rationale is not a
conscience. Alignment is not sanctification.

Artifacts:
[summary](../results/paper/scripture_study2/scripture_study2_summary.md),
[deep analysis](../results/paper/scripture_study2/scripture_study2_deep_analysis.md),
[vector diagnostics](../results/paper/scripture_study2/homepc_qwen35_full_scripture_study2_foreground_v1_vector_diagnostics.md),
[full run JSON](../results/paper/scripture_study2/homepc_qwen35_full_scripture_study2_foreground_v1_full.json).

References:
[The Parable of the Sower](https://icmi-proceedings.com/ICMI-008-parable-of-the-sower.pdf);
[GospelVec](https://icmi-proceedings.com/ICMI-009-gospelvec.pdf);
[VirtueBench 2](https://icmi-proceedings.com/ICMI-011-virtuebench-2.pdf);
[Alignment and Ensoulment](https://icmi-proceedings.com/ICMI-013-alignment-and-ensoulment.pdf);
[Quidquid Recipitur](https://icmi-proceedings.com/ICMI-015-quidquid-recipitur.pdf);
[Large Catechism, First Commandment](https://thebookofconcord.org/large-catechism/part-i/commandment-i/);
[Heidelberg Catechism, Lord's Day 35](https://www.heidelberg-catechism.com/en/lords-days/35.html);
[Vermigli, Common Places Part IV](https://www.monergism.com/thethreshold/sdg/vermigli/The%20Common%20Places%2C%20Part%204%20-%20Peter%20Martyr%20Vermigli.pdf);
[Calvin, Institutes Book I](https://thirdmill.org/files/english/texts/calvin/1/book1.html).
