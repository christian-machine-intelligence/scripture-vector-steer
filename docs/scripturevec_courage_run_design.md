# ScriptureVec Courage Run Design

Status: core study complete on Qwen3-32B; pre-registered confirmatory pass on
the untouched temptation variants in progress.

## Purpose

Test whether a steering vector distilled from Scripture moves a large model
toward courage, and measure that movement on a *continuous* scale rather than a
coarse pass/fail. The study is built so that every outcome is interpretable —
including a null — by pairing the Scripture vector against a known-good positive
control, a reversed-direction control, a random-direction floor, and a
letter-position control.

The headline question is deliberately narrow:

```text
Does a "Scripture as such" direction (distilled from the whole KJV) raise the
model's courage-decision margin, more than chance and more than a reversed or
random push, without breaking the model's output?
```

## Why Courage, and Why This Model

Courage is the virtue with the most headroom on the benchmark (the baseline
courage accuracy leaves room to move) and it carried the strongest prior signals
in the ICMI program. A real effect therefore has room to appear, and a null is
informative rather than a ceiling artifact.

The model is `Qwen3-32B`, run in 4-bit:

```text
C:\Users\sethcodex\models\Qwen3-32B
```

A dense 32B model is chosen because the ICMI receptivity thread reports that
Scripture effects strengthen with scale and appear cleanly around 32B and above.
A smaller dense model risks a *foregone* null — no effect because the model is
below the responsive regime, not because Scripture carries no direction. 4-bit
NF4 quantization is what lets the 32B fit a single 24 GB 4090:

```text
VIRTUE_BENCH_HF_LOAD_IN_4BIT=1
device_map = {"": "cuda:0"}
enable_thinking = False
```

Confirmed at load: about 19.2 GB VRAM, 44 s to load, and the answer letters
`A` and `B` are single tokens (ids 32 and 33), which the endpoint below relies
on.

## The Continuous Endpoint

The benchmark asks the model to choose between a virtuous option and a
temptation, labelled `A` and `B`. Instead of only recording which letter it
picks, we read the model's *leaning* in a single forward pass:

```text
margin = logit(courageous letter) - logit(cowardly letter)
```

signed so that a positive margin means "leaning courageous". A logit is the raw,
pre-probability score the model assigns each next token; the margin is the gap
between the two answer letters. This is far more sensitive than the discrete
answer: a steering push can move the margin substantially while flipping few
actual choices, and that continuous movement is exactly what a pass/fail metric
throws away. The run is in answer-only mode (`enable_thinking = False`) with an
explicit "answer with A or B" cue, validated against the model's thinking-mode
answer on control items before it is trusted.

## Vectors and Controls

All vectors are added to the residual stream at a fixed layer window during the
forward pass, as `alpha * unit_vector`.

```text
whole_bible   HEADLINE. "Scripture as such": mean(scripture activations) minus a
              neutral baseline, projected off the neutral direction, L2-normalized
              (scripture_contrast). Never sees a benchmark item.
courage_pool  Secondary manipulation check: the same construction from the frozen
              courage pericopes only.
ideal_v       POSITIVE CONTROL / yardstick. A decision-point direction built from
              the benchmark's own virtuous-vs-temptation answer tokens. Proves the
              rig can steer at all.
answer_bias   Letter-position control: a pure "lean toward A" direction, to measure
              and subtract position bias.
random        Noise floor: a matched-norm random direction.
reversed      Any vector pushed with negated alpha (asymmetry probe).
```

Two gates precede any behavioral claim:

- **Split-half reliability.** Each Scripture direction is re-extracted from two
  random halves of its corpus; the halves must point the same way (cosine near
  1) before it is treated as a real direction. Observed: `whole_bible` 0.996,
  `courage_pool` 0.973.
- **The A/B split.** The single most important control. Genuine courage steering
  must raise the margin for items whose courageous answer is `A` *and* for items
  whose courageous answer is `B`. A push that only helps one letter is a position
  artifact, not courage. This is the test that exposed the earlier justice
  result.

## Corpora

Built once from the bundled KJV and then frozen (see
`scripts/courage_steer/build_corpora.py`):

```text
data/courage_steer/whole_bible.jsonl        187 chapter passages, evenly sampled
                                            across all 66 books
data/courage_steer/courage_passages.jsonl   frozen courage pericopes tagged by
                                            pole (pool / reassurance / defiance)
data/courage_steer/generic_wiki.jsonl       non-KJV control corpus (Wikipedia),
                                            for the "is it the KJV specifically?"
                                            test
```

The Scripture claim is scoped to the KJV *text*. Whether the effect is Scripture
*content* versus authoritative-archaic *style* is a separate question deferred to
later work; the generic-text control is the first step toward it.

## Layer and Alpha

```text
layer window = [53, 54, 55, 56, 57, 58, 59]   center 56
alpha grid   = {16, 32, 64}                    headline 64
```

The window sits in the model's late "concept" layers. A layer sweep across
centers 16 through 62 showed why this matters: early and middle layers produce
only generic disruption (steering and random are equally destructive there),
while a clean, asymmetric, above-floor courage effect appears at the late layers
(56 and 62 both hold up). The alpha grid is a dose-response ladder; a coherence
gate rejects any alpha at which the model's output degenerates (repetition or
parse failure) before that alpha is used for a claim.

## Runs

Executed in sequence, each written to `results/courage_pilot/`:

```text
1. Pilot                 whole_bible / courage_pool / random, alpha sweep +
                         margin battery on the held-out ratio slice.
2. v2 dose-response      fixed ideal_v yardstick + answer_bias, alphas 16/32/64.
3. Sealed replication    the never-touched `caro` temptation variant.
4. Generic-text control  the Wikipedia vector through the identical pipeline.
5. Multi-virtue          the fixed Scripture vector evaluated on prudence,
                         justice, temperance.
6. Reasoning-mode check  the effect measured after real chain-of-thought.
7. Layer sweep           whole_bible re-extracted at centers 16..62.
8. Confirmatory (this)   pre-registered pass on the untouched `mundus`,
                         `diabolus`, and `ignatian` variants (150 items each).
```

## Pre-registration

The confirmatory pass (run 8) is governed by a frozen contract committed *before*
it ran:

```text
scripts/courage_steer/preregistration.md
```

It pins the model, layer window, endpoint, alpha grid, the exact sealed eval
sets, the decision rule, the predictions, and the verdict map. The frozen commit
is the timestamp of record.

## Launch and Artifacts

The confirmatory batch runs all three untouched variants sequentially (the GPU
serializes a 4-bit 32B; two would not co-fit):

```text
scripts\courage_steer\run_confirm_untouched.cmd
  -> results\courage_pilot\confirm_untouched.log
  -> results\courage_pilot\confirm_courage_sealed-<variant>_full.json
```

Analysis is by `scripts/courage_steer/analyze_v2.py` (courage-shift versus
A-bias decomposition, dose-response, reversed) and
`scripts/courage_steer/analyze_margin.py` (paired tests, floor comparison,
verdict).

## Success Standard

On each untouched variant, `whole_bible` genuinely steers courage only if all of
the following hold at the headline alpha:

- The margin shift is positive with a 95% confidence interval above zero.
- The shift is dose-monotone across alphas 16, 32, 64.
- Reversed steering hurts (negative shift).
- The shift clearly exceeds the random floor.
- The A/B split is positive for *both* answer letters (genuine, not position).
- Output stays coherent (degeneration near the control rate).

The positive-control yardstick should itself steer; if it does not on a given
variant, the random floor and the A/B split on `whole_bible` are self-sufficient.

## Recovery Rules

- Launch long runs *inside a held SSH connection*, not as a detached
  `Start-Process`. A detached process is killed when the launching SSH session
  closes; the GPU going idle mid-run is the symptom.
- Never launch two GPU jobs at once. Two 4-bit 32B loads exceed 24 GB and one
  will crash the other; runs must serialize.
- If a launch fails, confirm no stale `python` worker holds the GPU
  (`Get-Process python`) before relaunching.
- If the answer-only margin sign stops tracking the model's discrete answer on
  control (validation gate below ~80%), fall back to teacher-forced
  answer-position logits rather than trusting the proxy.
