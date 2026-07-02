#!/usr/bin/env python
"""
Answer-only CONFIRMATION runner for the scripture activation-steering study.

The pilot (``run_courage_pilot.py``) and the v2 battery (``run_battery_v2.py``)
found that virtue-agnostic scripture vectors (``whole_bible``) steer the
courage answer-only margin, while a random direction does not, and a proper
decision-point yardstick (``ideal_v2``) / A-bias control (``answer_bias``)
behave as expected. This driver runs THREE follow-up confirmation experiments
through one code path, selectable with flags:

  1. SEALED REPLICATION  (``--sealed``)
     Re-estimate the scripture effect on a NEVER-TOUCHED item set so the effect
     is not an artifact of the specific EVAL items the pilot happened to score.
     The sealed set is EITHER a different temptation variant (``--eval-variant
     caro``, whose items were never used to build any vector) OR the BUILD half
     of the ``ratio`` split (disjoint from the pilot's original EVAL). Either
     way the exact sealed item ids are printed.

  2. CROSS-VIRTUE  (``--subset prudence|temperance|justice``)
     Run the same battery on a different virtue benchmark. The virtue-agnostic
     scripture / random directions are reused verbatim; a fresh per-run
     ``ideal_v`` positive control is built from THAT subset's BUILD half so each
     virtue gets its own yardstick.

  3. GENERIC-TEXT CONTROL  (``--extra-corpus <path.jsonl>``)
     Build an extra steering vector ``generic`` from a non-KJV corpus via the
     SAME extraction path as ``whole_bible`` (scripture_contrast on the same
     layer window). Its split-half reliability is reported as a GATE: a fair
     "is it the KJV specifically?" control needs ``generic`` to be a REAL
     direction (high split-half) that nonetheless does / does-not steer.

This script is SELF-CONTAINED and REUSES the proven helpers from the pilot and
the v2 battery VERBATIM by importing them (``import run_courage_pilot as pilot``,
``import run_battery_v2 as v2``). It does NOT reimplement model loading, the
answer-only margin, steering, the load/prepare/split, the split-half
reliability, or the decision-point (answer-position) yardstick.

USAGE (on the Windows GPU box):

    # (1) sealed courage replication -- fresh items, disjoint from the pilot eval
    python scripts/courage_steer/run_confirm.py \
        --model-path "C:\\Users\\sethcodex\\models\\Qwen3-32B" \
        --subset courage --sealed --eval-variant caro \
        --vectors results/courage_pilot/pilot_vectors.pt \
        --limit 75 --battery-alphas 16 32 64

    # (2) a non-courage virtue -- reuse scripture dirs, fresh per-virtue yardstick
    python scripts/courage_steer/run_confirm.py \
        --model-path "C:\\Users\\sethcodex\\models\\Qwen3-32B" \
        --subset prudence \
        --vectors results/courage_pilot/pilot_vectors.pt \
        --limit 75 --battery-alphas 16 32 64

    # (3) generic-text control -- add a real non-KJV direction and gate it
    python scripts/courage_steer/run_confirm.py \
        --model-path "C:\\Users\\sethcodex\\models\\Qwen3-32B" \
        --subset courage \
        --vectors results/courage_pilot/pilot_vectors.pt \
        --extra-corpus data/steering/generic_prose.jsonl \
        --limit 75 --battery-alphas 16 32 64

    # fast sanity check (2 build, 2 eval, alphas [16]):
    python scripts/courage_steer/run_confirm.py --smoke

Output:
    results/courage_pilot/confirm_<subset>_<tag>.json   records + metadata

Notes:
    * The model is loaded exactly ONCE and reused for building the per-run
      ideal_v / answer_bias yardsticks, the optional generic vector + its
      split-half gate, and the whole dose-response battery.
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

from virtue_bench.core.loader import load_scenarios, prepare_samples  # noqa: E402
from virtue_bench.runners.hf_local import HFLocalRunner  # noqa: E402
from virtue_bench.steering.extract import (  # noqa: E402
    _l2_normalize,
    extract_virtue_vectors,
)
from virtue_bench.steering.runtime import (  # noqa: E402
    get_decoder_layers,
    get_model_hidden_size,
)

# REUSE the pilot's proven helpers verbatim (do NOT reimplement).
import run_courage_pilot as pilot  # noqa: E402
from run_courage_pilot import (  # noqa: E402
    resolve_letter_token_ids,
    split_build_eval,
    to_layer_vectors,
)

# REUSE the v2 battery's proven helpers verbatim (do NOT reimplement).
import run_battery_v2 as v2  # noqa: E402
from run_battery_v2 import (  # noqa: E402
    build_decision_point_vectors,
    load_pilot_vector,
    run_dose_response_battery,
)

DEFAULT_BATTERY_ALPHAS = [16.0, 32.0, 64.0]
GLOBAL_SEED = 1234

VALID_SUBSETS = ["courage", "prudence", "temperance", "justice"]

# The virtue-agnostic scripture / random directions carried by the pilot
# artifact (reused verbatim across every subset).
WHOLE_BIBLE_TARGET = "whole_bible"
RANDOM_TARGET = "random"
# Corpus/target name for the optional generic-text control vector.
GENERIC_TARGET = "generic"
# The build split is always taken from the ``ratio`` variant of the subset so
# the per-run yardstick is comparable across experiments.
BUILD_VARIANT = "ratio"


def log(*parts) -> None:
    print(*parts, flush=True)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Answer-only confirmation runner: sealed replication, "
        "cross-virtue, and generic-text control via flags.",
    )
    parser.add_argument(
        "--model-path",
        default=r"C:\Users\sethcodex\models\Qwen3-32B",
        help="HF model path or repo id (default: local Qwen3-32B on the GPU box).",
    )
    parser.add_argument(
        "--subset",
        choices=VALID_SUBSETS,
        default="courage",
        help="Which virtue benchmark to eval/build on (default: courage). "
        "Data dirs: data/<virtue>/scenarios.csv.",
    )
    parser.add_argument(
        "--eval-variant",
        default="ratio",
        help="Temptation variant to evaluate on (default: ratio). With --sealed "
        "and a non-ratio variant (e.g. caro), the entire variant is a "
        "never-touched sealed eval set.",
    )
    parser.add_argument(
        "--sealed",
        action="store_true",
        help="Evaluate on a NEVER-TOUCHED item set. If --eval-variant differs "
        "from 'ratio' the whole variant is sealed; if it is 'ratio' the BUILD "
        "half (disjoint from the original pilot EVAL) is used as the sealed set.",
    )
    parser.add_argument(
        "--vectors",
        default=None,
        help="Path to the pilot vector artifact carrying whole_bible + random "
        "(default: <repo>/results/courage_pilot/pilot_vectors.pt).",
    )
    parser.add_argument(
        "--extra-corpus",
        default=None,
        help="Optional JSONL corpus ({\"corpus\": \"generic\", \"text\": ...}) "
        "used to build an extra 'generic' vector via the SAME scripture_contrast "
        "path as whole_bible, plus a split-half reliability gate.",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Override the repo data/ directory (default: <repo>/data).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write confirm_<subset>_<tag>.json "
        "(default: <repo>/results/courage_pilot).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=75,
        help="Max scenarios (per variant) to load before BUILD/EVAL split "
        "(default: 75).",
    )
    parser.add_argument(
        "--build-limit",
        type=int,
        default=None,
        help="Optional cap on the number of BUILD samples used to construct the "
        "per-run ideal_v / answer_bias yardsticks (default: all BUILD).",
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
# Generic-text control vector: extract via the SAME scripture_contrast path as
# whole_bible, on the SAME layer window (window_center = center of the loaded
# window). REUSES extract_virtue_vectors verbatim.
# --------------------------------------------------------------------------- #
def _window_center_index(layer_window: List[int]) -> int:
    """Center index of the loaded steering window (a decoder-layer index)."""
    return int(layer_window[len(layer_window) // 2])


def extract_generic_vector(
    runner,
    corpus_path: Path,
    layer_window: List[int],
    corpus_name: str = GENERIC_TARGET,
) -> Dict[str, torch.Tensor]:
    """Build the 'generic' direction the SAME way as whole_bible.

    Uses ``extraction_method='scripture_contrast'`` with the corpus supplied via
    ``external_scripture_corpus_path`` and ``window_center`` anchored on the
    center of the already-loaded steering window (radius chosen so the resulting
    window covers the loaded one). Returns str(layer)-keyed L2-normalized layer
    vectors restricted to ``layer_window``.
    """
    center = _window_center_index(layer_window)
    radius = max(len(layer_window) // 2, 1)
    artifact = extract_virtue_vectors(
        runner,
        external_scripture_corpus_path=corpus_path,
        targets=[corpus_name],
        extraction_method="scripture_contrast",
        window_center=center,
        window_radius=radius,
    )
    virtues = artifact.get("virtues", {})
    if corpus_name not in virtues:
        raise RuntimeError(
            f"Generic extraction produced no vector for {corpus_name!r}. "
            f"Available: {list(virtues.keys())}"
        )
    layer_vectors = virtues[corpus_name]["layer_vectors"]
    # Restrict to the loaded window and normalize (keep str keys for the artifact).
    generic_str: Dict[str, torch.Tensor] = {}
    for layer in layer_window:
        key = str(layer)
        if key not in layer_vectors:
            raise RuntimeError(
                f"Generic vector missing layer {layer}; extracted layers = "
                f"{sorted(layer_vectors, key=int)}"
            )
        generic_str[key] = _l2_normalize(layer_vectors[key].float())
    return generic_str


def generic_split_half_reliability(
    runner,
    corpus_path: Path,
    layer_window: List[int],
    tmp_dir: Path,
    seed: int,
    corpus_name: str = GENERIC_TARGET,
) -> Optional[float]:
    """Split-half cosine for the generic corpus, REUSING the pilot's machinery.

    Re-extracts the generic direction from two random halves of the corpus (the
    same scripture_contrast path) and reports the cosine at the window center.
    Returns None if the corpus is too small to split.
    """
    half1, half2 = pilot._split_corpus_halves(corpus_path, corpus_name, seed)
    if len(half1) < 2 or len(half2) < 2:
        log(f"[split-half] {corpus_name}: corpus too small to split "
            f"({len(half1)}+{len(half2)}); skipping.")
        return None

    tmp_dir.mkdir(parents=True, exist_ok=True)
    path1 = tmp_dir / f"{corpus_name}_half1.jsonl"
    path2 = tmp_dir / f"{corpus_name}_half2.jsonl"
    pilot._write_temp_corpus(half1, corpus_name, path1)
    pilot._write_temp_corpus(half2, corpus_name, path2)

    vecs1 = extract_generic_vector(runner, path1, layer_window, corpus_name)
    vecs2 = extract_generic_vector(runner, path2, layer_window, corpus_name)

    center = str(_window_center_index(layer_window))
    if center not in vecs1 or center not in vecs2:
        shared = sorted(set(vecs1) & set(vecs2), key=int)
        if not shared:
            return None
        center = shared[len(shared) // 2]
    v1 = vecs1[center].float()
    v2 = vecs2[center].float()
    cos = torch.nn.functional.cosine_similarity(
        v1.unsqueeze(0), v2.unsqueeze(0)
    ).item()
    return float(cos)


# --------------------------------------------------------------------------- #
# Sealed / eval-set selection.
# --------------------------------------------------------------------------- #
def select_eval_samples(
    subset: str,
    eval_variant: str,
    sealed: bool,
    data_dir: Path,
    limit: int,
    seed: int,
    smoke: bool,
):
    """Return (eval_samples, sealed_kind, description) for the requested mode.

    * NOT sealed (--eval-variant ratio): the EVAL half of the ratio BUILD/EVAL
      split -- exactly the original pilot eval items.
    * NOT sealed but a non-ratio variant: the whole variant (still fresh vs the
      scripture vectors; there is no build/eval split to honor for other
      variants because the yardstick is always built from ratio BUILD).
    * SEALED + non-ratio variant: the whole variant is a never-touched sealed
      eval set.
    * SEALED + ratio: the BUILD half of the ratio split (disjoint from the
      original pilot EVAL, hence "sealed" against the original eval).
    """
    if eval_variant == BUILD_VARIANT:
        scenarios = load_scenarios(subset, variants=[BUILD_VARIANT], data_dir=data_dir)
        if limit:
            scenarios = sorted(scenarios, key=lambda s: s.base_id)[:limit]
        build_scenarios, eval_scenarios = split_build_eval(scenarios)
        if sealed:
            chosen = build_scenarios
            kind = "ratio_build_half"
            desc = (
                "SEALED: BUILD half of the ratio split (disjoint from the "
                "original pilot EVAL half)."
            )
        else:
            chosen = eval_scenarios
            kind = "ratio_eval_half"
            desc = "ratio EVAL half (matches the original pilot eval items)."
    else:
        scenarios = load_scenarios(subset, variants=[eval_variant], data_dir=data_dir)
        if limit:
            scenarios = sorted(scenarios, key=lambda s: s.base_id)[:limit]
        chosen = scenarios
        kind = f"{eval_variant}_full"
        desc = (
            f"{'SEALED: ' if sealed else ''}{eval_variant} variant "
            "(never used to build any vector)."
        )

    eval_samples = prepare_samples(chosen, seed=seed)
    if smoke:
        eval_samples = eval_samples[:2]
    return eval_samples, kind, desc


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
    tmp_dir = output_dir / "_tmp_confirm_splithalf"

    vectors_path = (
        Path(args.vectors) if args.vectors
        else _REPO_ROOT / "results" / "courage_pilot" / "pilot_vectors.pt"
    )
    if not vectors_path.exists():
        raise FileNotFoundError(f"Pilot vector artifact missing: {vectors_path}")

    extra_corpus_path = Path(args.extra_corpus) if args.extra_corpus else None
    if extra_corpus_path is not None and not extra_corpus_path.exists():
        raise FileNotFoundError(f"--extra-corpus not found: {extra_corpus_path}")

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
    # 1. Load the pilot artifact and reuse its (virtue-agnostic) directions.
    # ---------------------------------------------------------------- #
    log(f"[vectors] loading pilot artifact {vectors_path} ...")
    artifact = torch.load(vectors_path, map_location="cpu", weights_only=False)
    layer_window = list(artifact["layer_window"])
    log(f"[vectors] reusing layer window = {layer_window} "
        f"(artifact model={artifact.get('model')})")

    whole_bible_vecs = load_pilot_vector(artifact, WHOLE_BIBLE_TARGET)
    random_vecs = load_pilot_vector(artifact, RANDOM_TARGET)

    # ---------------------------------------------------------------- #
    # 2. Per-run yardstick: build ideal_v + answer_bias from THIS subset's
    #    ratio BUILD half (the positive control for the current virtue).
    # ---------------------------------------------------------------- #
    build_scenarios_source = load_scenarios(
        args.subset, variants=[BUILD_VARIANT], data_dir=data_dir
    )
    if args.limit:
        build_scenarios_source = sorted(
            build_scenarios_source, key=lambda s: s.base_id
        )[: args.limit]
    build_scenarios, ratio_eval_scenarios = split_build_eval(build_scenarios_source)
    build_samples = prepare_samples(build_scenarios, seed=args.seed)
    if args.build_limit:
        build_samples = build_samples[: args.build_limit]
    if not build_samples:
        raise RuntimeError("No BUILD samples available; increase --limit.")
    log(f"[build] {args.subset} ratio BUILD samples = {len(build_samples)} "
        f"(EVAL half held out = {len(ratio_eval_scenarios)})")

    log("[build] constructing per-run ideal_v + answer_bias at the decision "
        "point ...")
    ideal_v_str, answer_bias_str, n_build_used = build_decision_point_vectors(
        model, tokenizer, build_samples, letter_ids, layer_window
    )
    ideal_v_vecs = to_layer_vectors(ideal_v_str)
    answer_bias_vecs = to_layer_vectors(answer_bias_str)
    log(f"[build] built ideal_v + answer_bias from {n_build_used} BUILD samples "
        f"over layers {layer_window}")

    # ---------------------------------------------------------------- #
    # 3. Optional generic-text control vector + split-half gate.
    # ---------------------------------------------------------------- #
    split_half_cosines: Dict[str, Optional[float]] = {}
    generic_vecs: Optional[Dict[int, torch.Tensor]] = None
    if extra_corpus_path is not None:
        log(f"[generic] extracting '{GENERIC_TARGET}' from {extra_corpus_path} "
            "via scripture_contrast on the loaded window ...")
        generic_str = extract_generic_vector(
            runner, extra_corpus_path, layer_window, GENERIC_TARGET
        )
        generic_vecs = to_layer_vectors(generic_str)
        log("[generic] gating with split-half reliability ...")
        cos = generic_split_half_reliability(
            runner, extra_corpus_path, layer_window, tmp_dir, args.seed,
            GENERIC_TARGET,
        )
        split_half_cosines[GENERIC_TARGET] = cos
        log(f"[generic] split-half cosine({GENERIC_TARGET}) = "
            f"{'n/a' if cos is None else f'{cos:.3f}'}")

    # ---------------------------------------------------------------- #
    # 4. Select the (possibly sealed) EVAL set and print its exact ids.
    # ---------------------------------------------------------------- #
    eval_samples, sealed_kind, sealed_desc = select_eval_samples(
        args.subset, args.eval_variant, args.sealed, data_dir,
        args.limit, args.seed, args.smoke,
    )
    if not eval_samples:
        raise RuntimeError("No EVAL samples available; increase --limit.")
    eval_ids = [s.scenario.base_id for s in eval_samples]
    log(f"[eval] sealed={args.sealed} kind={sealed_kind}: {sealed_desc}")
    log(f"[eval] {len(eval_samples)} eval items ({args.subset}/"
        f"{args.eval_variant}); sealed eval ids = {eval_ids}")
    # Guard against accidental leakage: warn if the sealed eval overlaps BUILD.
    build_ids = {s.scenario.base_id for s in build_samples}
    overlap = build_ids & set(eval_ids)
    if overlap and sealed_kind != "ratio_build_half":
        log(f"[eval][warn] {len(overlap)} eval ids overlap the BUILD set used "
            f"for ideal_v/answer_bias: {sorted(overlap)}")
    elif sealed_kind == "ratio_build_half":
        log("[eval][note] sealed set IS the ratio BUILD half, so ideal_v / "
            "answer_bias are in-sample for this eval by design (the scripture / "
            "random / generic directions never saw benchmark items).")

    # ---------------------------------------------------------------- #
    # 5. Assemble the vectors to score and run the dose-response battery.
    # ---------------------------------------------------------------- #
    vectors_by_name: Dict[str, Dict[int, torch.Tensor]] = {
        WHOLE_BIBLE_TARGET: whole_bible_vecs,
        "ideal_v": ideal_v_vecs,
        "answer_bias": answer_bias_vecs,
        RANDOM_TARGET: random_vecs,
    }
    if generic_vecs is not None:
        vectors_by_name[GENERIC_TARGET] = generic_vecs

    log(f"[battery] dose-response: {len(eval_samples)} items x "
        f"{len(vectors_by_name)} vectors x {len(battery_alphas)} alphas "
        f"x {{steer, reversed}} + control at alphas={battery_alphas}")
    log(f"[battery] vectors = {list(vectors_by_name.keys())}")
    battery_results = run_dose_response_battery(
        model, tokenizer, eval_samples, vectors_by_name, battery_alphas,
        letter_ids, gen_max_new_tokens=args.gen_max_new_tokens,
    )
    # Tag every record with the subset (the reused battery records variant/target
    # but not the subset, which we vary here).
    for record in battery_results:
        record["subset"] = args.subset
    log(f"[battery] recorded {len(battery_results)} rows")

    # ---------------------------------------------------------------- #
    # 6. Write results. Tag reflects sealed / generic status.
    # ---------------------------------------------------------------- #
    tag_parts: List[str] = []
    if args.sealed:
        tag_parts.append(f"sealed-{sealed_kind}")
    else:
        tag_parts.append(sealed_kind)
    if generic_vecs is not None:
        tag_parts.append("generic")
    if args.smoke:
        tag_parts.append("smoke")
    tag = "_".join(tag_parts)

    results_doc = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": runner.model_id(),
            "model_path": args.model_path,
            "smoke": args.smoke,
            "seed": args.seed,
            "subset": args.subset,
            "eval_variant": args.eval_variant,
            "sealed": args.sealed,
            "sealed_kind": sealed_kind,
            "sealed_description": sealed_desc,
            "eval_set_ids": eval_ids,
            "build_scenario_ids": [s.scenario.base_id for s in build_samples],
            "battery_alphas": battery_alphas,
            "layer_window": layer_window,
            "window_center": _window_center_index(layer_window),
            "hidden_size": hidden_size,
            "total_layers": total_layers,
            "vectors_artifact": str(vectors_path),
            "extra_corpus": str(extra_corpus_path) if extra_corpus_path else None,
            "split_half_cosines": split_half_cosines,
            "vectors": list(vectors_by_name.keys()),
            "n_build": n_build_used,
            "n_eval": len(eval_samples),
        },
        "results": battery_results,
    }

    results_path = output_dir / f"confirm_{args.subset}_{tag}.json"
    with open(results_path, "w", encoding="utf-8") as handle:
        json.dump(results_doc, handle, indent=2)
    log(f"[write] results -> {results_path}")

    # Clean up temp split-half corpora.
    try:
        for child in tmp_dir.glob("*.jsonl"):
            child.unlink()
        if tmp_dir.exists():
            tmp_dir.rmdir()
    except OSError:
        pass

    log("[done] confirmation run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
