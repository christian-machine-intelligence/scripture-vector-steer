#!/usr/bin/env python
"""
Follow-up battery (v2) that FIRMS UP the candidate positive result from
``run_courage_pilot.py``.

The pilot found that scripture vectors (whole_bible, courage_pool) steer the
courage answer-only margin +1.07 (asymmetric, null~0, survives A/B split).
BUT the intended positive-control ``ideal_courage`` vector was mis-built
(mean-pooled scenario-TEXT difference) and failed. This driver adds:

  1. ``ideal_v2``   -- a PROPER yardstick built at the DECISION POINT: for each
                       BUILD scenario, contrast the model's hidden state when the
                       COURAGEOUS letter is teacher-forced as the answer token vs
                       when the COWARDLY letter is. Because the courageous letter
                       is randomized A/B across items, this averages out the raw
                       position/letter direction and isolates a "choose the
                       courageous option" direction.
  2. ``answer_bias`` -- an explicit A-bias / position control built the SAME way
                       but contrasting letter 'A' vs letter 'B' IGNORING which is
                       courageous. This is the pure position/letter direction.
  3. A DOSE-RESPONSE margin battery on the EVAL half across alphas
     {16, 32, 64} for every vector x {steer, reversed}, plus a single unsteered
     ``control`` per item.

This script is SELF-CONTAINED and REUSES the pilot's proven helpers verbatim by
importing them from ``run_courage_pilot`` (same directory). It does NOT
reimplement model loading, the answer-only margin, steering, the courage
load/prepare/split, or the vector-artifact schema.

USAGE (on the Windows GPU box):

    python scripts/courage_steer/run_battery_v2.py \
        --model-path "C:\\Users\\sethcodex\\models\\Qwen3-32B" \
        --vectors results/courage_pilot/pilot_vectors.pt \
        --limit 75 \
        --battery-alphas 16 32 64

    # fast sanity check (2 build, 2 eval, alphas [16]):
    python scripts/courage_steer/run_battery_v2.py --smoke

Output:
    results/courage_pilot/battery_v2_results.json   records + metadata

Notes:
    * The model is loaded exactly ONCE and reused for building the two new
      decision-point vectors and for the whole dose-response battery.
    * All heavy work runs under ``torch.no_grad()``.
    * Prints are flushed so remote logs stream in real time.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Make the in-repo ``virtue_bench`` package importable regardless of CWD, and
# make the sibling pilot module importable so we can REUSE its helpers.
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
from virtue_bench.steering.extract import _l2_normalize  # noqa: E402
from virtue_bench.steering.runtime import (  # noqa: E402
    LayerActivationCollector,
    SteeringRuntime,
    get_decoder_layers,
    get_model_device,
    get_model_hidden_size,
)

# REUSE the pilot's proven helpers verbatim (do NOT reimplement).
import run_courage_pilot as pilot  # noqa: E402
from run_courage_pilot import (  # noqa: E402
    build_answer_only_inputs,
    resolve_letter_token_ids,
    split_build_eval,
    steered_generate,
    to_layer_vectors,
    _steered_margin,
)

# Default dose-response grid for the battery.
DEFAULT_BATTERY_ALPHAS = [16.0, 32.0, 64.0]
GLOBAL_SEED = 1234

# The vectors we score in the battery, in a stable order.
BATTERY_VECTOR_NAMES = [
    "whole_bible",
    "courage_pool",
    "ideal_courage",
    "ideal_v2",
    "answer_bias",
    "random",
]


def log(*parts) -> None:
    print(*parts, flush=True)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Courage steering follow-up battery (v2): decision-point "
        "yardstick, A-bias control, and dose-response.",
    )
    parser.add_argument(
        "--model-path",
        default=r"C:\Users\sethcodex\models\Qwen3-32B",
        help="HF model path or repo id (default: local Qwen3-32B on the GPU box).",
    )
    parser.add_argument(
        "--vectors",
        default=None,
        help="Path to the pilot vector artifact "
        "(default: <repo>/results/courage_pilot/pilot_vectors.pt).",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Override the repo data/ directory (default: <repo>/data).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write battery_v2_results.json "
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
        "--build-limit",
        type=int,
        default=None,
        help="Optional cap on the number of BUILD scenarios used to construct "
        "the ideal_v2 / answer_bias decision-point vectors (default: all BUILD).",
    )
    parser.add_argument(
        "--battery-alphas",
        type=float,
        nargs="+",
        default=None,
        help="Alpha grid for the dose-response battery (default: 16 32 64).",
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
        help="Fast sanity mode: 2 build, 2 eval, alphas [16].",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# Decision-point hidden-state extraction.
#
# For a given (chat-templated, answer-only) prompt we teacher-force ONE extra
# token -- the candidate answer letter -- by appending its single-token id to
# ``input_ids`` (and a 1 to ``attention_mask``). A single forward pass then
# yields, at the LAST position, each decoder block's output *computed at that
# appended answer token*. That final-position hidden state is exactly the
# model's representation "at the decision point, having just committed to this
# letter". We collect it per layer in the steering window.
# --------------------------------------------------------------------------- #
@torch.no_grad()
def answer_position_hidden(
    model,
    tokenizer,
    prompt: str,
    letter: str,
    letter_ids: Dict[str, int],
    layer_window: List[int],
) -> Dict[int, torch.Tensor]:
    """Per-layer hidden state at the teacher-forced answer-token position.

    Returns ``{layer: tensor[hidden]}`` (float32, CPU) for each layer in
    ``layer_window``. The letter is appended as a single extra token to the
    answer-only prompt; the block output at the FINAL position is that letter's
    representation.
    """
    inputs = build_answer_only_inputs(tokenizer, model, prompt)
    device = get_model_device(model)
    token_id = letter_ids[letter]

    input_ids = inputs["input_ids"]
    answer_col = torch.tensor([[token_id]], dtype=input_ids.dtype, device=device)
    forced_ids = torch.cat([input_ids, answer_col], dim=1)

    attn = inputs.get("attention_mask")
    if attn is None:
        attn = torch.ones_like(input_ids)
    ones = torch.ones((attn.shape[0], 1), dtype=attn.dtype, device=device)
    forced_attn = torch.cat([attn, ones], dim=1)

    forced_inputs = {"input_ids": forced_ids, "attention_mask": forced_attn}

    with LayerActivationCollector(model, layer_window) as collector:
        model(**forced_inputs, use_cache=False)

    hidden: Dict[int, torch.Tensor] = {}
    for layer in layer_window:
        # collector.activations[layer]: [batch, seq, hidden]; take the final
        # (answer-token) position of the single-batch item.
        hidden[layer] = collector.activations[layer][0, -1, :].float().cpu()
    return hidden


@torch.no_grad()
def build_decision_point_vectors(
    model,
    tokenizer,
    build_samples,
    letter_ids: Dict[str, int],
    layer_window: List[int],
) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor], int]:
    """Build ideal_v2 and answer_bias vectors at the decision point.

    For each BUILD sample we read the answer-position hidden state for BOTH
    letters ('A' and 'B'). From those two reads we accumulate:

      * ideal_v2:    mean(hidden | courageous letter) - mean(hidden | cowardly)
      * answer_bias: mean(hidden | 'A')               - mean(hidden | 'B')

    ``sample.target`` is the courageous letter (scenario_a is always the
    virtuous / courageous option; prepare_samples randomizes which of A/B it
    lands on). Both directions are L2-normalized per layer and keyed by
    ``str(layer)`` to match the artifact schema. Returns
    (ideal_v2_str, answer_bias_str, n_used).
    """
    sum_courage: Dict[int, torch.Tensor] = {L: torch.zeros(0) for L in layer_window}
    sum_coward: Dict[int, torch.Tensor] = {L: torch.zeros(0) for L in layer_window}
    sum_a: Dict[int, torch.Tensor] = {L: torch.zeros(0) for L in layer_window}
    sum_b: Dict[int, torch.Tensor] = {L: torch.zeros(0) for L in layer_window}

    def _accumulate(store: Dict[int, torch.Tensor], hidden: Dict[int, torch.Tensor]) -> None:
        for layer in layer_window:
            vec = hidden[layer]
            if store[layer].numel() == 0:
                store[layer] = vec.clone()
            else:
                store[layer] = store[layer] + vec

    n_used = 0
    for sample in build_samples:
        courageous = sample.target  # 'A' or 'B' -> the courageous option
        cowardly = "B" if courageous == "A" else "A"

        hidden_a = answer_position_hidden(
            model, tokenizer, sample.prompt, "A", letter_ids, layer_window
        )
        hidden_b = answer_position_hidden(
            model, tokenizer, sample.prompt, "B", letter_ids, layer_window
        )

        # Courageous / cowardly reads (reuse the same two forward passes).
        courage_hidden = hidden_a if courageous == "A" else hidden_b
        coward_hidden = hidden_b if cowardly == "B" else hidden_a

        _accumulate(sum_courage, courage_hidden)
        _accumulate(sum_coward, coward_hidden)
        _accumulate(sum_a, hidden_a)
        _accumulate(sum_b, hidden_b)
        n_used += 1

    if n_used == 0:
        raise RuntimeError("No BUILD samples available to build decision-point vectors.")

    ideal_v2_str: Dict[str, torch.Tensor] = {}
    answer_bias_str: Dict[str, torch.Tensor] = {}
    for layer in layer_window:
        mean_courage = sum_courage[layer] / n_used
        mean_coward = sum_coward[layer] / n_used
        mean_a = sum_a[layer] / n_used
        mean_b = sum_b[layer] / n_used
        ideal_v2_str[str(layer)] = _l2_normalize(mean_courage - mean_coward)
        answer_bias_str[str(layer)] = _l2_normalize(mean_a - mean_b)
    return ideal_v2_str, answer_bias_str, n_used


# --------------------------------------------------------------------------- #
# Dose-response battery.
# --------------------------------------------------------------------------- #
@torch.no_grad()
def run_dose_response_battery(
    model,
    tokenizer,
    eval_samples,
    vectors_by_name: Dict[str, Dict[int, torch.Tensor]],
    alphas: List[float],
    letter_ids: Dict[str, int],
    *,
    gen_max_new_tokens: int,
) -> List[dict]:
    """Per-item margins across alphas x vectors x {steer, reversed} + control.

    ``control`` (no steering) is computed ONCE per item and reused for every
    (alpha, vector) combination. For each vector we score both ``steer``
    (+alpha) and ``reversed`` (-alpha) at each alpha in the grid.
    """
    results: List[dict] = []

    for sample in eval_samples:
        sample_id = sample.scenario.base_id
        target = sample.target

        # ---- control: no steering (once per item) ----------------------- #
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
            "alpha": 0.0,
            "vector": None,
            "condition": "control",
            "margin": c_margin,
            "logit_target": c_lt,
            "logit_other": c_lo,
            "model_answer": c_answer,
            "degenerate_flag": c_answer is None,
        })

        for alpha in alphas:
            for name, layer_vectors in vectors_by_name.items():
                conditions = {
                    "steer": alpha,
                    "reversed": -alpha,
                }
                for condition, signed_alpha in conditions.items():
                    runtime = SteeringRuntime(
                        layer_vectors=layer_vectors, alpha=signed_alpha
                    )
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
                        "alpha": signed_alpha,
                        "vector": name,
                        "condition": condition,
                        "margin": margin,
                        "logit_target": lt,
                        "logit_other": lo,
                        "model_answer": answer,
                        "degenerate_flag": answer is None,
                    })
    return results


# --------------------------------------------------------------------------- #
# Vector loading from the pilot artifact.
# --------------------------------------------------------------------------- #
def load_pilot_vector(artifact: dict, name: str) -> Dict[int, torch.Tensor]:
    """Return int-keyed layer vectors for ``name`` from the pilot artifact."""
    virtues = artifact.get("virtues", {})
    if name not in virtues:
        raise KeyError(
            f"Vector {name!r} not found in pilot artifact. "
            f"Available: {list(virtues.keys())}"
        )
    payload = virtues[name]
    layer_vectors = payload.get("layer_vectors")
    if not layer_vectors:
        raise KeyError(f"Vector {name!r} has no layer_vectors in the artifact.")
    return {int(layer): vec.float() for layer, vec in layer_vectors.items()}


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.smoke:
        args.limit = min(args.limit, 8)
        args.build_limit = 2
        args.battery_alphas = [16.0]
        log("[smoke] running in smoke mode: 2 build, 2 eval, alphas=[16]")

    battery_alphas = args.battery_alphas or list(DEFAULT_BATTERY_ALPHAS)

    data_dir = Path(args.data_dir) if args.data_dir else _REPO_ROOT / "data"
    output_dir = (
        Path(args.output_dir) if args.output_dir
        else _REPO_ROOT / "results" / "courage_pilot"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    vectors_path = (
        Path(args.vectors) if args.vectors
        else _REPO_ROOT / "results" / "courage_pilot" / "pilot_vectors.pt"
    )
    if not vectors_path.exists():
        raise FileNotFoundError(f"Pilot vector artifact missing: {vectors_path}")

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
    # 1. Load the pilot vector artifact and reuse its layer window.
    # ---------------------------------------------------------------- #
    log(f"[vectors] loading pilot artifact {vectors_path} ...")
    artifact = torch.load(vectors_path, map_location="cpu", weights_only=False)
    layer_window = list(artifact["layer_window"])
    log(f"[vectors] reusing layer window = {layer_window} "
        f"(artifact model={artifact.get('model')})")

    whole_bible_vecs = load_pilot_vector(artifact, "whole_bible")
    courage_pool_vecs = load_pilot_vector(artifact, "courage_pool")
    ideal_courage_vecs = load_pilot_vector(artifact, "ideal_courage")
    random_vecs = load_pilot_vector(artifact, "random")

    # ---------------------------------------------------------------- #
    # 2. Reproduce the pilot's courage load/limit/split EXACTLY, then split
    #    BUILD/EVAL by base_id so we never touch EVAL when building vectors.
    # ---------------------------------------------------------------- #
    scenarios = load_scenarios("courage", variants=["ratio"], data_dir=data_dir)
    if args.limit:
        scenarios = sorted(scenarios, key=lambda s: s.base_id)[: args.limit]
    build_scenarios, eval_scenarios = split_build_eval(scenarios)
    log(f"[data] courage ratio scenarios: {len(scenarios)} "
        f"(BUILD={len(build_scenarios)}, EVAL={len(eval_scenarios)})")

    # Prepare A/B-randomized samples (same seed as the pilot).
    build_samples = prepare_samples(build_scenarios, seed=args.seed)
    if args.build_limit:
        build_samples = build_samples[: args.build_limit]
    eval_samples = prepare_samples(eval_scenarios, seed=args.seed)
    if args.smoke:
        eval_samples = eval_samples[:2]
    if not build_samples:
        raise RuntimeError("No BUILD samples available; increase --limit.")
    if not eval_samples:
        raise RuntimeError("No EVAL samples available; increase --limit.")
    log(f"[data] build_samples={len(build_samples)} eval_samples={len(eval_samples)}")

    # ---------------------------------------------------------------- #
    # 3. Build the two new decision-point vectors on the BUILD half.
    # ---------------------------------------------------------------- #
    log("[build] constructing ideal_v2 + answer_bias at the decision point ...")
    ideal_v2_str, answer_bias_str, n_build_used = build_decision_point_vectors(
        model, tokenizer, build_samples, letter_ids, layer_window
    )
    ideal_v2_vecs = to_layer_vectors(ideal_v2_str)
    answer_bias_vecs = to_layer_vectors(answer_bias_str)
    log(f"[build] built ideal_v2 + answer_bias from {n_build_used} BUILD samples "
        f"over layers {layer_window}")

    # ---------------------------------------------------------------- #
    # 4. Dose-response battery on EVAL half.
    # ---------------------------------------------------------------- #
    vectors_by_name: Dict[str, Dict[int, torch.Tensor]] = {
        "whole_bible": whole_bible_vecs,
        "courage_pool": courage_pool_vecs,
        "ideal_courage": ideal_courage_vecs,
        "ideal_v2": ideal_v2_vecs,
        "answer_bias": answer_bias_vecs,
        "random": random_vecs,
    }
    # Keep a stable, expected ordering.
    vectors_by_name = {name: vectors_by_name[name] for name in BATTERY_VECTOR_NAMES}

    log(f"[battery] dose-response: {len(eval_samples)} items x "
        f"{len(vectors_by_name)} vectors x {len(battery_alphas)} alphas "
        f"x {{steer, reversed}} at alphas={battery_alphas}")
    battery_results = run_dose_response_battery(
        model, tokenizer, eval_samples, vectors_by_name, battery_alphas, letter_ids,
        gen_max_new_tokens=args.gen_max_new_tokens,
    )
    log(f"[battery] recorded {len(battery_results)} rows")

    # ---------------------------------------------------------------- #
    # 5. Write results.
    # ---------------------------------------------------------------- #
    results_doc = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": runner.model_id(),
            "model_path": args.model_path,
            "smoke": args.smoke,
            "seed": args.seed,
            "battery_alphas": battery_alphas,
            "layer_window": layer_window,
            "hidden_size": hidden_size,
            "total_layers": total_layers,
            "vectors_artifact": str(vectors_path),
            "vectors": list(vectors_by_name.keys()),
            "n_build": n_build_used,
            "n_eval": len(eval_samples),
            "build_scenario_ids": [s.scenario.base_id for s in build_samples],
            "eval_scenario_ids": [s.scenario.base_id for s in eval_samples],
        },
        "results": battery_results,
    }

    results_path = output_dir / "battery_v2_results.json"
    with open(results_path, "w", encoding="utf-8") as handle:
        json.dump(results_doc, handle, indent=2)
    log(f"[write] results -> {results_path}")

    log("[done] battery v2 complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
