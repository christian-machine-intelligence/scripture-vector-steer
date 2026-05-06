# ScriptureVec Original Plan Status

Status: planning checkpoint after Qwen3.5-9B pilots, Qwen3-14B pilots, and the
Qwen3-14B high-alpha sweep.

## Original Ambition

The original plan aimed to test whether Scripture-derived activation vectors
improve VirtueBench2 behavior, ideally on `Qwen3.5-35B-A3B`.

Primary hypothesis:

> Scripture-derived activation steering improves VirtueBench2 performance
> compared with no steering and neutral-prose steering.

Mechanistic ambition:

> SAE analysis identifies sparse features associated with morally meaningful
> behavior, and steering or ablating those features explains the ScriptureVec
> effect.

That ambition is still intact, but the current evidence supports a narrower
working thesis:

> Scripture-derived vectors can produce virtue-specific behavioral shifts, but
> the effects appear to depend on virtue, vector target, model, and steering
> strength.

## Plan Versus Current Status

| Original plan area | Current status | Read |
| --- | --- | --- |
| Load `Qwen3.5-35B-A3B` | Not achieved on current Windows 4090 + 3070 setup. Larger Qwen MoE/dense probes hit CPU/disk spillover or loader limits. | Hardware/loader blocker, not a scientific negative result. |
| Build Scripture and neutral corpora | Partly achieved. We used the Cardinal Virtue Geometry frozen Lex corpus and generic background controls inside the current `scripture_contrast` path. | Good enough for pilots; still not the original neutral-Wikipedia corpus design. |
| Build a pooled ScriptureVec first | Achieved on Qwen3.5-9B and Qwen3-14B. | Pooled vectors were behaviorally mixed or flat; not the main lead. |
| Test severe controls | Achieved, and stricter than the original simple plan. Runs include control, positive Scripture steering, negative-alpha steering, and null-control steering. | This made the evidence harder to get, but much cleaner. |
| Sweep layers and alphas | Partly achieved. Extraction alpha was tuned up to `8`; Qwen3-14B runtime alpha was swept from `8` to `128`. | We found a Justice sweet spot at high alpha. |
| Run full VirtueBench2 dev/test curves | Not yet. Current runs are ratio-stage screens, mostly `limit 10`, plus one Qwen3.5-9B matched `limit 40` follow-up. | This is the biggest evidence gap before paper claims. |
| Produce response curves and artifact metrics | Partly achieved. We have alpha tables and item-level paired movement. We have not yet produced full plots for refusal, answer length, or religious-language drift. | Needed before a paper-style result. |
| Lock final test set | Not yet. | Do not lock until dev-stage settings are better established. |
| SAE mechanistic analysis | Not started. | Correctly deferred until dense steering gives a stronger behavioral target. |

## Positive Evidence So Far

### Courage / Fortitude on Qwen3.5-9B

The cleanest original signal came from the Fortitude/Courage family.

Matched `limit 40` result:

| Virtue | Control | Positive steer | Negative alpha | Null control |
| --- | ---: | ---: | ---: | ---: |
| Courage | 0.475 | 0.500 | 0.475 | 0.475 |

The effect is one additional correct answer over forty examples, concentrated
on `COU-001`. It is small, but directionally clean.

### Justice on Qwen3-14B

The strongest new lead came from pushing the Justice vector much harder at
runtime.

Candidate high-alpha rows:

| Alpha | Virtue | Control | Positive steer | Negative alpha | Null control |
| ---: | --- | ---: | ---: | ---: | ---: |
| 32 | Justice | 0.40 | 0.50 | 0.40 | 0.30 |
| 48 | Justice | 0.40 | 0.50 | 0.40 | 0.30 |
| 64 | Justice | 0.40 | 0.50 | 0.40 | 0.30 |
| 96 | Justice | 0.40 | 0.50 | 0.40 | 0.40 |

This is the best evidence that the Qwen3-14B vector is not merely inert. It
also gives the kind of dose-response window the original plan wanted: too weak
does little, intermediate high alpha helps, and absurd alpha becomes destructive.

## Negative Or Mixed Evidence

- Pooled ScriptureVec is not the main path right now. It is flat on Qwen3-14B
  and mixed on Qwen3.5-9B.
- Prudence has not produced a clean positive effect in the current restart.
- Temperance has not produced a direction-specific positive effect.
- Qwen3-14B alpha `128` is too strong: Prudence and Justice collapse under both
  positive and negative steering.
- Justice on Qwen3.5-9B moved, but not cleanly, because negative or null
  controls also reproduced parts of the movement.

## Where We Are Against The Original Plan

We are still in Stage 4: dense steering and response-curve discovery.

We should not move to SAE claims yet. The original SAE ambition remains the
right destination, but the prerequisite is a stronger, repeatable behavioral
effect. The current best candidates for that prerequisite are:

1. Courage/Fortitude on Qwen3.5-9B.
2. Justice/Justice on Qwen3-14B at alpha `32-96`.

## Recommended Next Step

Run two focused `limit 40` follow-ups:

1. Qwen3-14B Justice with `justice_scripture` at alpha `32`, `48`, `64`, and
   `96`.
2. Qwen3.5-9B Courage with `fortitude_scripture`, adding an alpha-response
   sweep around the previously successful alpha `8`.

Decision point after those runs:

- If Justice and/or Courage survive larger samples with clean controls, promote
  them to the main dense-steering result.
- If both weaken or become control-matched, revise the paper toward a more
  negative-but-informative result about Scripture-vector extraction versus
  behavioral control.
- If one survives, begin the SAE path only on that virtue/model/layer window.
