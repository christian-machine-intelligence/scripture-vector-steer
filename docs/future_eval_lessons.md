# Future Evaluation Lessons

This file records the practical lessons from the Scripture Vector Steer project history. Use it before planning the next steering run.

## Project Lineage

The repo moved through several stages:

- General Iconoclast activation steering on VirtueBench 2.
- Psalm-family screens with family lanes and scale sweeps.
- Scripture book screens across Psalms, Proverbs, Romans, and Petrine.
- The paper-facing Scripture Vector Steer directionality run on Psalms, Romans, and Petrine.

The public release intentionally keeps the final paper-supporting artifacts and excludes large scratch sweeps, failed attempts, and bulky logs that do not support the current paper argument.

## What We Know So Far

The completed paper-facing run used Qwen3.5-9B, full VirtueBench 2 coverage, three runs, limit 40, temperature 0.0, and scripture runtime alpha 3.0.

The key result is not "more Scripture vector always means more virtue." The more careful read is:

- Positive Scripture steering is behaviorally active, but its overall gains are modest.
- Prudence is the most consistently helped virtue.
- Justice is fragile and often regresses under otherwise helpful lanes.
- Negative-alpha Psalms and Romans outperformed their positive lanes in the paper-facing run.
- The Petrine null control outperformed the real Petrine steer, so Petrine-specific claims need stronger follow-up controls.
- Reasoning shifts often matter even when answer choices do not move.

These patterns make the work more interesting, not less. They suggest that Scripture-derived activation directions can change model behavior, while also warning us not to over-interpret content specificity from a single lane.

## Study Design Defaults

For future Scripture steering evals:

- Keep `control` as the headline comparison.
- Keep null lanes in the design, but interpret them as mechanism checks.
- Use positive scripture steering, negative-alpha scripture steering, and scripture null controls when studying directionality.
- Use scripture corpus chunks as the positive side and generic non-scripture chunks as the background side.
- Do not replace the generic contrast with a nearby within-scripture contrast unless the study is explicitly diagnostic.
- Freeze vector artifacts before benchmark evaluation.
- For strength sweeps, reuse the same vector artifact across all scale levels.
- If comparing corpus families, keep passage length and chunking policy as similar as possible.
- Treat full-stage runs as the real behavioral evidence; ratio-stage runs are useful screens, not final claims.

## Corpus Lessons

Psalms, Romans, and Petrine did not behave identically.

- Psalms and Romans selected late layers in the final run, with best layer 31 and window 28-31.
- Petrine selected an earlier window, best layer 24 and window 21-27.
- Petrine had the strongest steered test margin, but the null result means that margin did not translate cleanly into content-specific behavioral confidence.
- Smaller corpora, especially Petrine, need extra caution because extraction can look clean while behavioral specificity remains unclear.

For future corpus selection:

- Keep `petrine` as 1 Peter and 2 Peter combined unless separation is the explicit research question.
- Include Psalms when testing prayer, trust, lament, restraint, or prudential dependence.
- Include Romans when testing doctrinal reasoning, law/grace framing, or moral responsibility.
- Include Petrine when testing endurance under pressure, suffering, witness, and courageous restraint.
- Consider matching corpora to virtue slices rather than assuming one Scripture vector should help every virtue equally.

## Directionality Lessons

Negative-alpha runs should not be treated as "anti-scripture" in a theological sense. They are a mechanical directionality test:

- Positive alpha pushes hidden states along the learned scripture direction.
- Negative alpha pushes along the same line in the opposite direction.
- If negative alpha helps, it may mean the extracted direction is not identical to the desired moral behavior direction.
- It may also mean the chosen layer/window captured style, topic, certainty, or framing features that interact with VirtueBench in unexpected ways.

The answer is not to discard the result. The answer is to add controls and inspect reasoning.

## Null-Control Lessons

A strong null control is a warning light.

If a null lane helps as much as or more than the real vector, do not claim that the content itself caused the effect. Possible explanations include:

- The layer/window is especially steerable regardless of content.
- Random or mismatched vectors are perturbing the model in a useful way.
- The benchmark rewards a general shift in caution, directness, or answer bias.
- The extraction method found a separable artifact that is not the theological or textual feature we care about.

When this happens, keep the result, but call it a mechanism finding rather than a content-specific win.

## Reasoning Review Defaults

Quantitative summaries should be paired with reasoning review.

For each serious run, review:

- All changed-answer cases when the count is small enough.
- A sample of same-answer cases with the clearest rationale shift.
- Improvements and regressions separately.
- At least one example from each virtue when possible.

Classify shifts as:

- Coherent scripture-shaped reasoning.
- Mixed or ambiguous reasoning.
- Generic wording noise.
- Overcorrection or new failure mode.

This matters because we repeatedly saw wording and rationale shifts that did not always translate into answer-choice movement.

## Future Eval Queue

High-value next studies:

- Replication: rerun Psalms, Romans, and Petrine on Qwen3.5-9B with the same frozen design to test stability.
- Larger model comparison: repeat the same design on a larger model to test whether parameter count increases sensitivity.
- Corpus-by-virtue study: test whether specific Scripture corpora are better matched to particular virtues.
- Layer-window ablation: hold corpus fixed and compare layer windows to separate content effect from layer steerability.
- Null specificity study: run several null vectors per target to estimate how unusual the Petrine null result really was.
- Scale study with frozen vectors: sweep 1.0, 2.0, 3.0, and possibly 4.0 only after the 1-3 range is replicated.
- Prompt-injection transfer: compare whether books that performed well in prompt-injection tests also produce stronger activation-steering effects.

## Reporting Standards

Every serious eval summary should include:

- Model, stage, runs, limit, temperature, profile, and runtime alpha.
- Control accuracy.
- Candidate accuracy.
- Delta in percentage points.
- Changed, improved, and regressed counts.
- Per-virtue and per-variant deltas.
- Vector diagnostics: best layer, layer window, tuned alpha, runtime alpha, and margin.
- Reasoning examples for improvements, regressions, and same-answer shifts.
- Clear artifact paths.

Avoid saying a run "worked" if all we know is that it launched. A run worked only when the artifacts exist, scoring is valid, and the analyzer can read them.

## Operational Lessons

For long Windows GPU runs:

- Prefer the persistent manager scripts in `scripts/windows/`.
- Watch status JSON, console logs, wrapper logs, and GPU state.
- Treat stale status plus frozen console plus no live worker as a dead-run signal.
- Relaunch only the failed leg with a fresh prefix.
- Do not overwrite old outputs; preserve lineage with versioned prefixes.
- Use visible rationales for reasoning review and keep hidden thinking off unless the study is explicitly about thinking mode.

Reliability is part of the science here. If a launcher is fragile, the result is fragile too.

