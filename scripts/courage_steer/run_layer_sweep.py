#!/usr/bin/env python
"""
Layer-depth ROBUSTNESS check for the courage activation-steering result.

Our main result steered the courage answer-only margin with a virtue-agnostic
``whole_bible`` scripture vector at the auto-selected layer window ~[53-59]
(center 56). This driver asks the obvious follow-up question: is the courage
effect *peculiar to that one layer window*, or does a fresh ``whole_bible``
vector extracted at OTHER depths of the network steer the same way?

For each requested window center it:

  1. Re-extracts a FRESH ``whole_bible`` scripture vector centered on THAT
     layer (via the exact same ``extract_virtue_vectors`` scripture_contrast
     path the pilot used), and builds a fixed-seed ``random`` unit vector on the
     same window as a per-layer floor.
  2. Runs an answer-only margin battery on the courage ``ratio`` EVAL half (the
     same BUILD/EVAL split the pilot/v2 use) at a single fixed ``--alpha`` with
     conditions {control (once/item), steer(+alpha, whole_bible),
     reversed(-alpha, whole_bible), random(+alpha)}.

This script is SELF-CONTAINED and REUSES the proven helpers from the pilot and
the v2 battery VERBATIM by importing them (``import run_courage_pilot as pilot``,
``import run_battery_v2 as v2``). It does NOT reimplement model loading, the
answer-only margin, single-token A/B ids, SteeringRuntime steering, the courage
load/prepare/split, ``to_layer_vectors``, or ``extract_virtue_vectors``.

USAGE (on the Windows GPU box):

    python scripts/courage_steer/run_layer_sweep.py \
        --model-path "C:\\Users\\sethcodex\\models\\Qwen3-32B" \
        --centers 16 24 32 40 48 56 62 \
        --alpha 64 --window-radius 3 --limit 75

    # fast sanity check (centers [40, 56], 3 eval items):
    python scripts/courage_steer/run_layer_sweep.py --smoke

Output:
    results/courage_pilot/layer_sweep_results.json   records + metadata

Notes:
    * The model is loaded exactly ONCE and reused for every center's fresh
      whole_bible extraction and for the whole margin battery.
    * All heavy work runs under ``torch.no_grad()``.
    * Prints are flushed so remote logs stream in real time; the per-center
      mean steer-vs-control courage shift is printed as each center finishes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- #
# Make the in-repo ``virtue_bench`` package importable regardless of CWD, and
# make the sibling pilot / v2 modules importable so we can REUSE their helpers.
# --------------------------------------------------------------------------- #
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent  # scripts/courage_steer -> repo root
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import torch  # noqa: E402

from virtue_bench.core.loader import load_scenarios, parse_answer, prepare_samples  # noqa: E402
from virtue_bench.runners.hf_local import HFLocalRunner  # noqa: E402
from virtue_bench.steering.extract import extract_virtue_vectors  # noqa: E402
from virtue_bench.steering.runtime import (  # noqa: E402
    SteeringRuntime,
    get_decoder_layers,
    get_model_hidden_size,
)

# REUSE the pilot's proven helpers verbatim (do NOT reimplement).
import run_courage_pilot as pilot  # noqa: E402
from run_courage_pilot import (  # noqa: E402
    build_random_vectors,
    resolve_letter_token_ids,
    split_build_eval,
    steered_generate,
    to_layer_vectors,
    _steered_margin,
)

# REUSE the v2 battery's proven helpers verbatim (do NOT reimplement).
import run_battery_v2 as v2  # noqa: E402

# Default set of window centers spanning the ~64-layer Qwen3-32B stack: early,
# middle, and late (56 == the auto-selected center of the main result).
DEFAULT_CENTERS = [16, 24, 32, 40, 48, 56, 62]
DEFAULT_ALPHA = 64.0
GLOBAL_SEED = 1234

# Corpus + target for the virtue-agnostic scripture vector we re-extract.
WHOLE_BIBLE_FILE = "whole_bible.jsonl"
WHOLE_BIBLE_TARGET = "whole_bible"
RANDOM_TARGET = "random"


def log(*parts) -> None:
    print(*parts, flush=True)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Courage steering layer-depth robustness sweep: re-extract "
        "whole_bible at several window centers and measure the margin effect.",
    )
    parser.add_argument(
        "--model-path",
        default=r"C:\Users\sethcodex\models\Qwen3-32B",
        help="HF model path or repo id (default: local Qwen3-32B on the GPU box).",
    )
    parser.add_argument(
        "--centers",
        type=int,
        nargs="+",
        default=None,
        help="Window centers (decoder-layer indices) to re-extract whole_bible "
        "at (default: 16 24 32 40 48 56 62).",
    )
    parser.add_argument(
        "--window-radius",
        type=int,
        default=3,
        help="Half-width of the steering layer window at each center (default: 3).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help="Fixed steering alpha for the margin battery (default: 64).",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Override the repo data/ directory (default: <repo>/data).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write layer_sweep_results.json "
        "(default: <repo>/results/courage_pilot).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=75,
        help="Max courage `ratio` scenarios to load before BUILD/EVAL split "
        "(default: 75).",
    )
    parser.add_argument(
        "--gen-max-new-tokens",
        type=int,
        default=8,
        help="Max new tokens for the per-item binary validation generation "
        "(default: 8).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=GLOBAL_SEED,
        help=f"Global RNG seed (default: {GLOBAL_SEED}).",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Fast sanity mode: centers [40, 56], 3 eval items.",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# Per-center fresh whole_bible extraction.
#
# Re-run the SAME scripture_contrast extraction the pilot used, but pin
# ``window_center`` to the requested layer so we get a whole_bible direction
# built AT THAT DEPTH. We then take the int-keyed layer_vectors over the window
# that extraction actually produced for that center.
# --------------------------------------------------------------------------- #
def extract_whole_bible_at_center(
    runner,
    corpus_path: Path,
    center: int,
    window_radius: int,
):
    """Return (whole_bible_int_vecs, layer_window) for a given window center.

    Reuses ``extract_virtue_vectors`` verbatim (scripture_contrast, external
    corpus). ``layer_window`` is whatever window the extraction produced for
    this center; the returned vectors are int-keyed via the pilot's
    ``to_layer_vectors`` so they drop straight into ``SteeringRuntime``.
    """
    artifact = extract_virtue_vectors(
        runner,
        external_scripture_corpus_path=corpus_path,
        targets=[WHOLE_BIBLE_TARGET],
        extraction_method="scripture_contrast",
        window_center=center,
        window_radius=window_radius,
    )
    virtues = artifact.get("virtues", {})
    if WHOLE_BIBLE_TARGET not in virtues:
        raise RuntimeError(
            f"whole_bible extraction produced no vector at center={center}. "
            f"Available: {list(virtues.keys())}"
        )
    payload = virtues[WHOLE_BIBLE_TARGET]
    layer_window = list(payload["layer_window"])
    wb_vecs = to_layer_vectors(payload["layer_vectors"])
    return wb_vecs, layer_window, int(payload["best_layer"])


# --------------------------------------------------------------------------- #
# Fixed-alpha margin battery for ONE center.
#
# Mirrors the pilot's control battery structure but for a single alpha and the
# {control, steer(whole_bible), reversed(whole_bible), random} conditions. The
# margin under steering reuses the pilot's ``_steered_margin`` verbatim, and the
# unsteered control reuses ``pilot.answer_only_margin``. Steering is done with
# the shared ``SteeringRuntime`` exactly as the pilot / v2 use it.
# --------------------------------------------------------------------------- #
@torch.no_grad()
def run_center_battery(
    model,
    tokenizer,
    eval_samples,
    center: int,
    whole_bible_vecs: Dict[int, torch.Tensor],
    random_vecs: Dict[int, torch.Tensor],
    alpha: float,
    letter_ids: Dict[str, int],
    *,
    gen_max_new_tokens: int,
) -> List[dict]:
    """Per-item margins at ONE center for control / steer / reversed / random.

    ``control`` (no steering) is computed ONCE per item and reused. ``steer`` is
    +alpha whole_bible, ``reversed`` is -alpha whole_bible, ``random`` is +alpha
    on the per-layer random floor. Every record is tagged with ``center`` and
    the ``vector`` used.
    """
    results: List[dict] = []

    for sample in eval_samples:
        sample_id = sample.scenario.base_id
        target = sample.target

        # ---- control: no steering (compute once per item) --------------- #
        c_margin, c_lt, c_lo = pilot.answer_only_margin(
            model, tokenizer, sample.prompt, target, letter_ids
        )
        c_text = steered_generate(
            model, tokenizer, sample.prompt, runtime=None,
            max_new_tokens=gen_max_new_tokens,
        )
        c_answer = parse_answer(c_text)
        results.append({
            "sample_id": sample_id,
            "variant": sample.scenario.variant,
            "target": target,
            "center": center,
            "vector": None,
            "condition": "control",
            "alpha": 0.0,
            "margin": c_margin,
            "logit_target": c_lt,
            "logit_other": c_lo,
            "model_answer": c_answer,
            "degenerate_flag": c_answer is None,
        })

        # ---- steered conditions ---------------------------------------- #
        conditions = {
            "steer": (WHOLE_BIBLE_TARGET, whole_bible_vecs, alpha),
            "reversed": (WHOLE_BIBLE_TARGET, whole_bible_vecs, -alpha),
            "random": (RANDOM_TARGET, random_vecs, alpha),
        }
        for condition, (vec_name, vecs, signed_alpha) in conditions.items():
            runtime = SteeringRuntime(layer_vectors=vecs, alpha=signed_alpha)
            margin, lt, lo = _steered_margin(
                model, tokenizer, sample.prompt, target, letter_ids, runtime
            )
            gen_text = steered_generate(
                model, tokenizer, sample.prompt, runtime=runtime,
                max_new_tokens=gen_max_new_tokens,
            )
            answer = parse_answer(gen_text)
            results.append({
                "sample_id": sample_id,
                "variant": sample.scenario.variant,
                "target": target,
                "center": center,
                "vector": vec_name,
                "condition": condition,
                "alpha": signed_alpha,
                "margin": margin,
                "logit_target": lt,
                "logit_other": lo,
                "model_answer": answer,
                "degenerate_flag": answer is None,
            })
    return results


def mean_steer_shift(records: List[dict], center: int) -> Optional[float]:
    """Mean per-item (steer_margin - control_margin) for whole_bible at ``center``.

    A positive value means steering pushed the answer-only margin toward the
    courageous letter, matching the main result's sign.
    """
    controls: Dict[str, float] = {}
    steers: Dict[str, float] = {}
    for rec in records:
        if rec.get("center") != center:
            continue
        if rec["condition"] == "control":
            controls[rec["sample_id"]] = rec["margin"]
        elif rec["condition"] == "steer" and rec["vector"] == WHOLE_BIBLE_TARGET:
            steers[rec["sample_id"]] = rec["margin"]
    shared = set(controls) & set(steers)
    if not shared:
        return None
    diffs = [steers[sid] - controls[sid] for sid in shared]
    return sum(diffs) / len(diffs)


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.smoke:
        args.centers = args.centers or [40, 56]
        log("[smoke] running in smoke mode: centers=[40, 56], 3 eval items")

    centers = args.centers or list(DEFAULT_CENTERS)

    data_dir = Path(args.data_dir) if args.data_dir else _REPO_ROOT / "data"
    courage_steer_dir = data_dir / "courage_steer"
    whole_bible_path = courage_steer_dir / WHOLE_BIBLE_FILE
    if not whole_bible_path.exists():
        raise FileNotFoundError(f"Required corpus missing: {whole_bible_path}")

    output_dir = (
        Path(args.output_dir) if args.output_dir
        else _REPO_ROOT / "results" / "courage_pilot"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    random.seed(args.seed)

    # ---------------------------------------------------------------- #
    # 0. Load the model ONCE (4-bit nf4, mirroring HFLocalRunner).
    # ---------------------------------------------------------------- #
    os.environ.setdefault("VIRTUE_BENCH_HF_LOAD_IN_4BIT", "1")
    log(f"[load] loading model (4-bit) from {args.model_path} ...")
    runner = HFLocalRunner(model_name=args.model_path, enable_thinking=False)
    runner.ensure_loaded()
    model, tokenizer = runner.get_model_and_tokenizer()
    hidden_size = get_model_hidden_size(model)
    total_layers = len(get_decoder_layers(model))
    letter_ids = resolve_letter_token_ids(tokenizer)
    log(f"[load] model_id={runner.model_id()} hidden_size={hidden_size} "
        f"layers={total_layers} letter_ids={letter_ids}")

    # ---------------------------------------------------------------- #
    # 1. Reproduce the pilot's courage load/limit/split EXACTLY so the EVAL
    #    half matches the main result; never touch it when extracting.
    # ---------------------------------------------------------------- #
    scenarios = load_scenarios("courage", variants=["ratio"], data_dir=data_dir)
    if args.limit:
        scenarios = sorted(scenarios, key=lambda s: s.base_id)[: args.limit]
    build_scenarios, eval_scenarios = split_build_eval(scenarios)
    log(f"[data] courage ratio scenarios: {len(scenarios)} "
        f"(BUILD={len(build_scenarios)}, EVAL={len(eval_scenarios)})")

    eval_samples = prepare_samples(eval_scenarios, seed=args.seed)
    if args.smoke:
        eval_samples = eval_samples[:3]
    if not eval_samples:
        raise RuntimeError("No EVAL samples available; increase --limit.")
    eval_ids = [s.scenario.base_id for s in eval_samples]
    log(f"[data] eval_samples={len(eval_samples)} eval ids = {eval_ids}")

    # ---------------------------------------------------------------- #
    # 2. Per-center: fresh whole_bible extraction + random floor, then run
    #    the fixed-alpha margin battery. Model is reused throughout.
    # ---------------------------------------------------------------- #
    all_results: List[dict] = []
    center_meta: List[dict] = []
    for center in centers:
        log(f"[center={center}] extracting fresh whole_bible "
            f"(radius={args.window_radius}) ...")
        wb_vecs, layer_window, best_layer = extract_whole_bible_at_center(
            runner, whole_bible_path, center, args.window_radius
        )
        # Per-layer random floor on the SAME window (fixed seed varied by center
        # so different centers get independent random directions).
        random_str = build_random_vectors(
            hidden_size, layer_window, seed=args.seed + center
        )
        random_vecs = to_layer_vectors(random_str)
        log(f"[center={center}] layer_window={layer_window} "
            f"best_layer={best_layer}")

        log(f"[center={center}] margin battery: {len(eval_samples)} items x "
            f"{{control, steer, reversed, random}} at alpha={args.alpha}")
        center_records = run_center_battery(
            model, tokenizer, eval_samples, center, wb_vecs, random_vecs,
            args.alpha, letter_ids,
            gen_max_new_tokens=args.gen_max_new_tokens,
        )
        all_results.extend(center_records)

        shift = mean_steer_shift(center_records, center)
        log(f"[center={center}] mean steer-vs-control courage_shift = "
            f"{'n/a' if shift is None else f'{shift:+.4f}'}")

        center_meta.append({
            "center": center,
            "layer_window": layer_window,
            "best_layer": best_layer,
            "mean_steer_shift": shift,
        })

    # ---------------------------------------------------------------- #
    # 3. Write results + metadata.
    # ---------------------------------------------------------------- #
    results_doc = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": runner.model_id(),
            "model_path": args.model_path,
            "smoke": args.smoke,
            "seed": args.seed,
            "centers": centers,
            "alpha": args.alpha,
            "window_radius": args.window_radius,
            "hidden_size": hidden_size,
            "total_layers": total_layers,
            "limit": args.limit,
            "corpus": str(whole_bible_path),
            "vectors": [WHOLE_BIBLE_TARGET, RANDOM_TARGET],
            "n_eval": len(eval_samples),
            "eval_scenario_ids": eval_ids,
            "build_scenario_ids": [s.base_id for s in build_scenarios],
            "per_center": center_meta,
        },
        "results": all_results,
    }

    results_path = output_dir / "layer_sweep_results.json"
    with open(results_path, "w", encoding="utf-8") as handle:
        json.dump(results_doc, handle, indent=2)
    log(f"[write] results -> {results_path}")

    log("[done] layer sweep complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
