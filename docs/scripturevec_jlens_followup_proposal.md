# Proposal: A J-Space Follow-Up to "Form Upon Matter"

Status: proposal only; no runs yet. Written against the courage study on the
`courage-steer-study` branch (PR #6, *Form Upon Matter: Scripture-Steered
Courage in Qwen3-32B*) and the new Anthropic workspace paper (July 2026).

## What Anthropic Published

The paper is *Verbalizable Representations Form a Global Workspace in Language
Models* (Transformer Circuits, 2026,
https://transformer-circuits.pub/2026/workspace/index.html), with companion
code at https://github.com/anthropics/jacobian-lens (Apache 2.0) and an
interactive explorer at https://neuronpedia.org/jlens.

Two ideas matter for us, and both can be said in plain English.

**The Jacobian lens (J-lens).** A tool that reads what an internal activation
is *disposed to make the model say*. For a residual-stream vector `h` at layer
ℓ, the lens transports it into the final-layer basis with a fitted linear map
and decodes it through the model's own unembedding:

```text
lens_ℓ(h) = Unembed(J_ℓ · h),   J_ℓ = E[∂h_final / ∂h_ℓ]
```

`J_ℓ` is the average input–output Jacobian over a text corpus — an improved
logit lens that corrects for how representations change across layers. The
released code fits lenses on open-weights Hugging Face decoders, with Qwen
worked examples; paper-grade fitting used 1,000 sequences of 128 tokens, and
the authors report quality saturates quickly (~100 prompts is usable).

**The J-space.** The span of the J-lens directions at a layer — the small,
privileged subspace of representations the model can verbalize, report, and
reason with. Anthropic shows it behaves like a *global workspace* (the
functional analogue of access consciousness, with the paper's explicit
discipline that no claim about phenomenal consciousness follows): it is small
(6–10% of activation variance; typically 10–25 concepts active at once),
it is what determines verbal report (swapping J-space components changes what
the model says 88% of the time, vs 5% for non-J-space components), it carries
intermediate steps of multi-hop reasoning (intermediates surface ~17 percentile
layers before answers, and swapping them redirects conclusions), it occupies
the middle stratum of the network (~38–92% depth on a 100-layer model, with
early "sensory" and late "motor" layers outside it), and automatic behavior
proceeds without it while flexible inference requires it. Their headline
demonstrations are on Claude models (Sonnet 4.5, Haiku 4.5, Opus 4.5/4.6),
with open-source implementations mirrored on Neuronpedia.

The short version for this repo: **we have been steering the residual stream
blind; the J-lens is an instrument that says, in vocabulary, what a direction
is disposed to make the model say, and whether a given effect runs through the
model's reportable workspace or beneath it.**

## Why This Fits Our Program Exactly

*Form Upon Matter* ends on two named gaps. Both are J-lens questions.

**Gap 1 — §5.4, "Virtue-seeking versus confidence."** The courage paper's
preferred reading is that the whole-Bible vector amplifies the model's
*adherence to Scripture* (the rationale vocabulary rises and falls with the
steering direction), not merely its confidence in a preferred answer. But the
rationale evidence is behavioral and correlational, and the paper says so. The
J-lens reads the same question internally: decompose the steered vs. unsteered
residual stream at the decision point and see *which verbalizable concepts the
vector promotes* — Scripture-register concepts (the adherence reading) or
answer-letter/certainty structure (the confidence reading).

**Gap 2 — §7, "Supplying the prudence."** The planned sequel adds a
discernment vector alongside the Scripture vector and predicts an interaction:
rescue on `ignatian`, restraint where the push runs to excess, little change
where the effect is already right. That design currently has only a behavioral
endpoint (the margin). The workspace paper hands us a mechanistic one: prudence
is the *deliberative* virtue, and the J-space is where the model's deliberation
is visible — intermediate conclusions surface there before answers do. A
discernment vector that works should leave a trace: the counterfeit-detection
thought ("this quotes Scripture falsely") appearing in the workspace before the
answer, on exactly the items that get rescued.

**Gap 3 — the standing localization puzzle.** The courage effect lives at
layers 53–59 of 64 (83–92% depth; earlier layers gave only generic
disruption); the archived Justice atlas found its cells at layers 24–31 of 40
(60–78% depth). The workspace paper predicts a specific layer anatomy —
sensory floor, workspace band, motor ceiling. Fitting a lens on Qwen3-32B
tells us where that band actually sits in *our* model, and therefore whether
Scripture steering acts inside the workspace band, at its motor boundary, or
below it. This would replace "a sweep found these layers" with a principled
account of *why* those layers.

There is also a fourth, quieter fit: the Justice paper's §10 promised a
sparse-feature follow-up (SAE work) that was never run. The J-lens is arguably
the better instrument for our purposes — its features are defined by
*verbalizability* (what the model is disposed to say), which is the very
register our rationale protocol already measures, and it requires no SAE
training, only a one-time lens fit.

## The Proposed Paper

One follow-up paper, two studies, with a pre-registered confirmatory core in
the discipline PR #6 established. Working titles, in the house register:

- *"Try the Spirits": Scripture Steering, Prudence, and the Verbalizable
  Workspace of Qwen3-32B* (1 John 4:1 — names the discernment task exactly:
  the Ignatian counterfeit is a spirit to be tried)
- *"Senses Exercised to Discern": Prudence in the Model's Workspace*
  (Hebrews 5:14 — already the courage paper's opening epigraph; the sequel
  would inherit it honestly)
- *"With Their Mouth": Where the Scripture Vector Lives* (Isaiah 29:13 — if
  Study 1 is published alone)

### Phase 0 — Fit and validate the instrument (gate for everything else)

1. **Fit a J-lens on Qwen3-14B first** (the archived Justice model) as the
   cheap pilot of the full pipeline: fit, sanity-decode, visualize.
2. **Fit the paper lens on Qwen3-32B.** The fit requires backprop through the
   model; our 4090 rig only holds the 32B in 4-bit NF4, and a Jacobian
   estimated through NF4 quantization is unvalidated territory. Mitigation:
   fit the lens in bf16 on a rented A100/H100 (a day-scale job at reference
   speed; the repo supports fitting on disjoint prompt slices and merging),
   then *apply* the fitted lens under our local 4-bit inference rig — lens
   application is a per-layer linear map plus unembed, i.e. cheap forward-pass
   instrumentation, which is all Studies 1–2 need at runtime.
3. **Validate transfer.** The workspace results are Claude-centric; before
   leaning on them we replicate two basics on Qwen3-32B: (i) the layer
   stratification (where lens decodes become meaningful — this locates the
   workspace band for Gap 3); (ii) one directed-modulation check ("think
   about X" raising X's J-lens activation). If these fail on Qwen3-32B, that
   is itself a reportable negative and the paper narrows to Study 1's
   decode-and-split results, which do not depend on the workspace
   interpretation.

### Study 1 — Where the received form lives (anatomy of the existing result)

No new benchmark design; this instruments the frozen apparatus of PR #6
(`pilot_vectors.pt`, layers 53–59, margin endpoint, five framings).

**E1. Decode the vectors.** Push the frozen `whole_bible` direction through
the lens at and around the steering window and report the top-k vocabulary per
layer — literally, what the vector is disposed to make the model say. Decode
the controls alongside: `generic_wiki` (should decode to fluent-prose nothing
in particular), `answer_bias` (should decode to the letter tokens — a built-in
positive control for the lens), `ideal_v`, and `random` (should decode to
nothing stable). This is the paper's cheapest and most vivid figure, and it is
the first direct look at *content* in this whole research line.

**E2. Split the vector against the workspace.** Project `whole_bible` onto the
J-space (span of the fitted lens directions) and its complement at each
steering layer; report the norm fraction. Then steer with the J-space
component only, the complement only, and the full vector, at matched norms,
on `caro`/`mundus`/`ratio`/`ignatian`, with the margin endpoint, the A/B
split, and the dose ladder as in PR #6. Three outcomes, all publishable:

- *Effect rides the J-space component* → the imposed form enters through the
  verbalizable workspace; consonant with the rationale finding (the model
  voices Scripture more when steered) and with the reversal (strip the
  workspace content, strip the warrant).
- *Effect rides the complement* → the form works beneath report; the voiced
  scriptural warrant is downstream gloss. This would overturn §5.1's preferred
  reading — which is exactly why it must be run.
- *Mixed* → report the decomposition; the "received disposition" turns out to
  have a confessing part and a subverbal part, and we can say how much of
  each.

**E3. Read the workspace under steering.** Sparse decomposition
(gradient-pursuit, k in the paper's 10–25 range) of activations at the
decision position under control / steer / reversed, on `ignatian` and `caro`.
Two questions: (i) which concepts move with dose — Scripture-register concepts
or answer/certainty structure (this is §5.4, adjudicated internally); (ii) on
*unsteered* `ignatian` items, does the workspace ever contain
counterfeit-detection concepts (deceive, twist, misuse, false)? A model that
apprehends the counterfeit and yields is a different creature from one that
never apprehends it — this is the *vis aestimativa / vis cogitativa* reading
of §5.3 made testable.

**E4. The paper's own decisive control, instrumented.** §5.4 proposed steering
on non-moral binary choices: if the multiplicative gain persists where there is
no good to pursue, the amplified quantity is confidence. Run it, and let the
J-lens say *what* is amplified in each case rather than inferring from margins
alone.

### Study 2 — Supplying the prudence, with the workspace as endpoint

The §7 sequel as specified there, upgraded with internal endpoints and frozen
before the confirmatory run, per the PR #6 pre-registration discipline.

**Vectors.** The discernment direction exactly as §7 prescribes: difference of
means between scriptural argument used rightly and the same scriptural
authority bent to a false end, extracted from the Ignatian variants of the
*other* cardinal virtues (so the discernment must transfer to courage). The
`prudence/scenarios.csv` bank already bundled in this repo supplies material.
Controls: a matched-norm random second direction (no rescue by mere
interference), prudence-alone, Scripture-alone. Split-half reliability gate as
in PR #6.

**Behavioral predictions (frozen).** The interaction signature from §7:
rescue on `ignatian`, restraint where the push runs rash, little change on
`caro`/`mundus`/`ratio`.

**Workspace predictions (frozen).** This is what the J-lens adds:

1. On rescued `ignatian` items, a counterfeit-detection concept appears in the
   J-space at intermediate layers *before* the answer position/layer — the
   workspace paper's internal-reasoning property, now sought as the mechanism
   of discernment. Items where no such intermediate appears do not rescue.
2. The prudence vector acts as an interaction in concept space too: it changes
   *which* concepts the Scripture vector promotes, rather than adding a fixed
   concept set of its own. (A merely additive second push predicts the
   latter.)
3. Aquinas's three acts of prudence give the register for the anatomy, held
   as register and not as claim: *consilium* (counsel — candidate
   considerations present in the workspace), *iudicium* (judgment — selection
   among them), *imperium* (command — propagation into the late motor layers
   that fix the answer). The lens can show whether rescue looks like counsel
   restored (the missing consideration finally present) or like command
   overridden (same contents, different motor outcome). Those are different
   mechanisms and different theology.

**Precedent worth citing.** The workspace paper's counterfactual-reflection
training — models trained to articulate principles later carry those
principles in the J-space during normal operation, with improved behavior —
is independent evidence that putting the right contents into the workspace is
a real causal channel to better action, not a decoration.

### Optional Study 3 — The corpus angle (or a separate short paper)

Cheap once the 14B lens exists, because it is pure decoding of archived
artifacts, no benchmark runs:

- Decode the sixteen archived Justice chapter vectors and seven book vectors
  through the 14B lens. The Justice paper's §7.4 offered four theses about
  what the chapter directions carry (recompense, adjudicated event, the
  Christological just-one, speech held under pressure); each thesis predicts a
  different decoded vocabulary. This tests them at the level of content,
  which the behavioral atlas never could.
- The Amos asymmetry: does the book-level vector decode to a broad, distributed
  justice vocabulary where the individual chapter vectors decode to narrow
  slices — the "book-scale moral form" reading made visible?
- The L24 α-collapse: measure whether high-α steering at L24 pushes
  activations off the workspace manifold (concept structure degenerating with
  dose), which would explain the collapse as displacement rather than
  saturation.

This study honors the archived paper's §10 promise (sparse-feature follow-up)
with a verbalizability-defined instrument instead of an SAE, and it gives the
ICMI corpus a semantic coordinate system — vocabulary, not layer indices —
in which Scripture-vector results can finally be compared across models,
virtues, and translations.

## Feasibility and Cost

- **Lens fit** is the one real cost: a day-scale bf16 fitting job per model
  (rented GPU for the 32B; the 4090 may suffice for a 14B pilot with care).
  Everything downstream is forward passes with a linear readout — the same
  cost class as the margin runs PR #6 already performed.
- **Runtime experiments** (E2–E4, Study 2) reuse the existing
  `scripts/courage_steer/` rig: same model, same NF4 loading, same margin
  endpoint, same item banks. New code is (a) lens application hooks,
  (b) J-space projection/split of a stored vector, (c) sparse decomposition
  readout. All three are reference-implemented in `jacobian-lens`.
- **No dependence on PR #6 merging first**, but the follow-up should base on
  its branch once merged, since it consumes the frozen vectors and item
  splits.

## Risks and Honest Limits

- **Quantization.** A lens fitted in bf16 and applied under NF4 inference
  mixes precisions; the margin endpoint already tolerates ~0.25-step logit
  quantization, but we must verify lens decodes are stable under the 4-bit
  rig before trusting them (Phase 0.3).
- **Single-token concepts.** The J-lens reads vocabulary tokens; the KJV
  register (righteousness, discernment, prudence) is multi-token in the Qwen
  tokenizer. The paper's multi-token extension is partial. Mitigation: build
  the probe vocabulary from our existing rationale word lists restricted to
  tokenizer-single tokens, and report coverage explicitly.
- **Transfer.** The five workspace properties are demonstrated on Claude
  models; Qwen implementations exist on Neuronpedia but our exact checkpoints
  need Phase 0 validation. A transfer failure is reportable, not fatal.
- **Instrument limits.** Absence from the J-lens readout is not absence of
  representation (the workspace paper says this itself, especially for early
  layers). Claims must be phrased as "not verbalizable by this instrument."
- **Register discipline.** The workspace paper is explicit that J-space is
  functional access, not phenomenal consciousness. That discipline is ours
  too — it is the *anima ficta* boundary in interpretability dress, and the
  paper should cite Anthropic's own refusal approvingly rather than outrun
  it. A workspace is not a soul; a verbalizable concept is not a confession
  of faith. The bounded-instrument frame of ICMI-013 carries over unchanged.

## What This Contributes to the ICMI Corpus

The steering line (ICMI-009 GospelVec → ICMI-022 emotion mechanism →
ICMI-026 persona geometry → PR #6 whole-Bible courage) has measured *that*
Scripture-derived directions move behavior and mapped *where* they act. The
J-lens upgrade measures *what they say* and *through which faculty they act* —
the difference between a behavioral atlas and a mechanistic account. And the
theological stakes sharpen rather than decorate: the J-space is, functionally,
what the model can bring to its mouth; its complement is what moves the model
without report. Whether the Scripture vector lives in the one or the other is
Isaiah 29:13 as a measurement — *"this people draw near me with their mouth...
but have removed their heart far from me"* — and Study 2 asks whether
discernment, the *auriga virtutum*, can be supplied to the workspace where the
courage paper showed it missing. Either answer instructs the programme: a
rescue shows virtue and its ordering separable and separately steerable in
activation space; a failure locates the Ignatian reversal beneath the
workspace, where no verbalizable ordering reaches it.

## Decision Points

1. **Scope:** the two-study paper as proposed, or Study 1 alone as a fast
   short paper (it needs no new benchmark design and answers §5.4)?
2. **Model order:** pilot everything at 14B first (cheaper, connects to the
   archived Justice artifacts) vs. going straight at the 32B (where the
   courage result lives)? Proposal assumes 14B-pilot-then-32B.
3. **Compute:** approve a rented-GPU day for the 32B bf16 lens fit, or
   attempt an NF4-gradient fit on the 4090 first and accept the validation
   burden?
4. **Study 3:** fold into the paper, spin off as a short companion, or drop?
