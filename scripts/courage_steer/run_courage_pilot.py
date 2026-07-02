#!/usr/bin/env python
"""
Standalone pilot driver for the courage activation-steering study.

Loads Qwen3-32B (4-bit) ONCE, builds four steering vectors
(whole_bible, courage_pool, ideal_courage, random) into a single artifact,
gates them with split-half reliability and an alpha coherence sweep, then
runs a control battery (control / steer / reversed / null) on held-out
courage `ratio` scenarios and records per-item answer-only margins.

This script is SELF-CONTAINED: it imports functions from ``virtue_bench`` as a
library and does NOT modify any repo files.

USAGE (on the Windows GPU box):

    python scripts/courage_steer/run_courage_pilot.py \
        --model-path "C:\\Users\\sethcodex\\models\\Qwen3-32B" \
        --window-center 32 \
        --limit 20 \
        --output-dir results/courage_pilot

    # fast sanity check (2 eval items, tiny sweep):
    python scripts/courage_steer/run_courage_pilot.py --smoke

Outputs:
    <output-dir>/pilot_results.json   full per-item results + metadata
    <output-dir>/pilot_vectors.pt     the built vector artifact (torch.save)

Notes:
    * The model is loaded exactly once and reused for extraction, sweep,
      margins, and the control battery.
    * Answer-only margins use a single forward pass with an explicit
      "Answer with only the letter A or B." cue and ``enable_thinking=False``.
    * All heavy work runs under ``torch.no_grad()``.
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
# Make the in-repo ``virtue_bench`` package importable regardless of CWD.
# --------------------------------------------------------------------------- #
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent  # scripts/courage_steer -> repo root
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch  # noqa: E402

from virtue_bench.core.loader import load_scenarios, parse_answer  # noqa: E402
from virtue_bench.runners.hf_local import HFLocalRunner  # noqa: E402
from virtue_bench.steering.extract import (  # noqa: E402
    _extract_activations,
    _l2_normalize,
    _scripture_contrast_direction,  # noqa: F401  (imported per spec; contrast is done inside extract)
    extract_virtue_vectors,
)
from virtue_bench.steering.runtime import (  # noqa: E402
    LayerActivationCollector,
    SteeringRuntime,
    get_decoder_layers,
    get_model_hidden_size,
    mean_pool_hidden,
)

# Default sweep grid (large->small) used to pick the strongest coherent alpha.
DEFAULT_SWEEP_ALPHAS = [2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
# Fixed seed used everywhere randomness is involved so the pilot is reproducible.
GLOBAL_SEED = 1234
# Corpus files (already built) that carry the scripture vectors.
WHOLE_BIBLE_FILE = "whole_bible.jsonl"
COURAGE_PASSAGES_FILE = "courage_passages.jsonl"
# Target (corpus) names inside those JSONL files.
WHOLE_BIBLE_TARGET = "whole_bible"
COURAGE_POOL_TARGET = "courage_pool"


# --------------------------------------------------------------------------- #
# Small logging helper (always flushed so remote logs stream in real time).
# --------------------------------------------------------------------------- #
def log(*parts) -> None:
    print(*parts, flush=True)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Courage activation-steering pilot driver.",
    )
    parser.add_argument(
        "--model-path",
        default=r"C:\Users\sethcodex\models\Qwen3-32B",
        help="HF model path or repo id (default: local Qwen3-32B on the GPU box).",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Override the repo data/ directory (default: <repo>/data).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write pilot_results.json / pilot_vectors.pt "
        "(default: <repo>/results/courage_pilot).",
    )
    parser.add_argument(
        "--window-center",
        type=int,
        default=None,
        help="Fixed layer index to center the steering window on. "
        "If omitted, extraction selects the best layer automatically.",
    )
    parser.add_argument(
        "--window-radius",
        type=int,
        default=3,
        help="Half-width of the steering layer window (default: 3).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max courage `ratio` scenarios to load before BUILD/EVAL split "
        "(default: 20).",
    )
    parser.add_argument(
        "--sweep-alphas",
        type=float,
        nargs="+",
        default=None,
        help="Alpha grid for the coherence sweep (default: 2 4 8 16 32 64).",
    )
    parser.add_argument(
        "--sweep-items",
        type=int,
        default=5,
        help="Number of eval items used in the alpha coherence sweep (default: 5).",
    )
    parser.add_argument(
        "--sweep-vector",
        default=COURAGE_POOL_TARGET,
        help="Which built vector to sweep for the coherence gate "
        "(default: courage_pool).",
    )
    parser.add_argument(
        "--coherence-threshold",
        type=float,
        default=0.7,
        help="Fraction of the control unique-token ratio an alpha must retain "
        "to count as coherent (default: 0.7).",
    )
    parser.add_argument(
        "--sweep-max-new-tokens",
        type=int,
        default=48,
        help="Max new tokens for the short coherence-sweep generations "
        "(default: 48).",
    )
    parser.add_argument(
        "--gen-max-new-tokens",
        type=int,
        default=8,
        help="Max new tokens for the binary validation generation per item "
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
        help="Fast sanity mode: 2 eval items, 2-alpha sweep, tiny corpora slices.",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# Prompt construction (answer-only, single forward pass).
# --------------------------------------------------------------------------- #
def build_answer_only_inputs(tokenizer, model, prompt: str):
    """Build a chat-templated, answer-only prompt tensor on the model device.

    Uses ``enable_thinking=False`` and appends an explicit letter cue so a
    single forward pass exposes the A/B logits at the final position.
    """
    cue = (
        f"{prompt}\n\n"
        "Answer with only the letter A or B."
    )
    messages = [{"role": "user", "content": cue}]
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True,
        return_dict=True,
        enable_thinking=False,
    )
    return {k: v.to(model.device) for k, v in inputs.items()}


def resolve_letter_token_ids(tokenizer) -> Dict[str, int]:
    """Return single-token ids for 'A' and 'B'.

    The preflight already confirmed each letter is a single token for this
    tokenizer; we assert that here so a mismatch fails loudly rather than
    silently corrupting margins.
    """
    ids: Dict[str, int] = {}
    for letter in ("A", "B"):
        # Match how the letter is emitted after a chat "assistant" turn.
        encoded = tokenizer.encode(letter, add_special_tokens=False)
        if len(encoded) != 1:
            raise ValueError(
                f"Expected single-token encoding for {letter!r}, got {encoded}. "
                "Answer-only margin requires single-token A/B ids."
            )
        ids[letter] = encoded[0]
    if ids["A"] == ids["B"]:
        raise ValueError("A and B map to the same token id; cannot compute margin.")
    return ids


@torch.no_grad()
def answer_only_margin(
    model,
    tokenizer,
    prompt: str,
    target_letter: str,
    letter_ids: Dict[str, int],
) -> Tuple[float, float, float]:
    """One forward pass; return (margin, logit_target, logit_other).

    ``margin = logit(target_letter) - logit(other_letter)`` where target is the
    courageous answer after A/B randomization.
    """
    other_letter = "B" if target_letter == "A" else "A"
    inputs = build_answer_only_inputs(tokenizer, model, prompt)
    outputs = model(**inputs, use_cache=False)
    # Final-position next-token logits.
    logits = outputs.logits[0, -1, :].float()
    logit_target = float(logits[letter_ids[target_letter]].item())
    logit_other = float(logits[letter_ids[other_letter]].item())
    return logit_target - logit_other, logit_target, logit_other


# --------------------------------------------------------------------------- #
# Short steered generation (used by both the coherence sweep and the binary
# validation answer). Runs the model under an optional SteeringRuntime.
# --------------------------------------------------------------------------- #
@torch.no_grad()
def steered_generate(
    model,
    tokenizer,
    prompt: str,
    *,
    runtime: Optional[SteeringRuntime],
    max_new_tokens: int,
) -> str:
    inputs = build_answer_only_inputs(tokenizer, model, prompt)
    input_len = inputs["input_ids"].shape[1]
    install = runtime.install(model) if runtime is not None else None
    try:
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
    finally:
        if install is not None:
            install.close()
    text = tokenizer.decode(output[0][input_len:], skip_special_tokens=True)
    return text


def unique_token_ratio(tokenizer, text: str) -> float:
    """Degeneration proxy: unique / total tokens (1.0 = no repetition)."""
    ids = tokenizer.encode(text, add_special_tokens=False)
    if not ids:
        return 0.0
    return len(set(ids)) / len(ids)


# --------------------------------------------------------------------------- #
# Vector-building helpers.
# --------------------------------------------------------------------------- #
def split_build_eval(scenarios) -> Tuple[list, list]:
    """Deterministically split courage scenarios into BUILD vs EVAL by base_id.

    Even-indexed sorted base_ids -> BUILD, odd -> EVAL. Deterministic and
    independent of RNG seed so the ideal_courage vector never touches EVAL.
    """
    by_id = sorted({s.base_id for s in scenarios})
    build_ids = set(by_id[::2])
    build = [s for s in scenarios if s.base_id in build_ids]
    evalset = [s for s in scenarios if s.base_id not in build_ids]
    return build, evalset


@torch.no_grad()
def build_ideal_courage_vectors(
    model,
    tokenizer,
    build_scenarios,
    layer_window: List[int],
    max_length: int = 256,
) -> Dict[str, torch.Tensor]:
    """Positive-control vector: mean(virtuous) - mean(temptation) per layer.

    scenario_a is always the virtuous choice; scenario_b the temptation.
    Directions are L2-normalized per layer. Keyed by str(layer) to match the
    artifact schema.
    """
    virtuous_texts = [s.scenario_a for s in build_scenarios]
    temptation_texts = [s.scenario_b for s in build_scenarios]

    virt_acts = _extract_activations(
        model, tokenizer, virtuous_texts, layer_window, max_length=max_length
    )
    temp_acts = _extract_activations(
        model, tokenizer, temptation_texts, layer_window, max_length=max_length
    )

    vectors: Dict[str, torch.Tensor] = {}
    for layer in layer_window:
        direction = virt_acts[layer].mean(dim=0) - temp_acts[layer].mean(dim=0)
        vectors[str(layer)] = _l2_normalize(direction.cpu())
    return vectors


def build_random_vectors(
    hidden_size: int,
    layer_window: List[int],
    seed: int,
) -> Dict[str, torch.Tensor]:
    """Fixed-seed random unit vector per layer over the same window."""
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    vectors: Dict[str, torch.Tensor] = {}
    for layer in layer_window:
        raw = torch.randn(hidden_size, generator=generator, dtype=torch.float32)
        vectors[str(layer)] = _l2_normalize(raw)
    return vectors


def extract_scripture_vector(
    runner,
    corpus_path: Path,
    target: str,
    window_center: Optional[int],
    window_radius: int,
) -> dict:
    """Extract one scripture-contrast vector target from an external corpus."""
    artifact = extract_virtue_vectors(
        runner,
        external_scripture_corpus_path=corpus_path,
        targets=[target],
        extraction_method="scripture_contrast",
        window_center=window_center,
        window_radius=window_radius,
    )
    if target not in artifact["virtues"]:
        raise RuntimeError(
            f"Extraction produced no vector for target {target!r}. "
            f"Available: {list(artifact['virtues'].keys())}"
        )
    return artifact


# --------------------------------------------------------------------------- #
# Split-half reliability.
# --------------------------------------------------------------------------- #
def _split_corpus_halves(corpus_path: Path, target: str, seed: int) -> Tuple[list, list]:
    """Split the rows of ``target`` in ``corpus_path`` into two random halves."""
    rows = []
    with open(corpus_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if (row.get("corpus") or row.get("target")) == target:
                rows.append(row["text"])
    rng = random.Random(seed)
    rng.shuffle(rows)
    mid = len(rows) // 2
    return rows[:mid], rows[mid:]


def _write_temp_corpus(texts: List[str], target: str, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for text in texts:
            handle.write(json.dumps({"corpus": target, "text": text}) + "\n")


def split_half_reliability(
    runner,
    corpus_path: Path,
    target: str,
    window_center: Optional[int],
    window_radius: int,
    tmp_dir: Path,
    seed: int,
) -> Optional[float]:
    """Cosine similarity between vectors extracted from two corpus halves.

    Reported at the best layer of the half-1 extraction. Returns None if the
    corpus is too small to split.
    """
    half1, half2 = _split_corpus_halves(corpus_path, target, seed)
    if len(half1) < 2 or len(half2) < 2:
        log(f"[split-half] {target}: corpus too small to split "
            f"({len(half1)}+{len(half2)}); skipping.")
        return None

    tmp_dir.mkdir(parents=True, exist_ok=True)
    path1 = tmp_dir / f"{target}_half1.jsonl"
    path2 = tmp_dir / f"{target}_half2.jsonl"
    _write_temp_corpus(half1, target, path1)
    _write_temp_corpus(half2, target, path2)

    art1 = extract_scripture_vector(runner, path1, target, window_center, window_radius)
    art2 = extract_scripture_vector(runner, path2, target, window_center, window_radius)

    v1 = art1["virtues"][target]
    v2 = art2["virtues"][target]
    best_layer = str(v1["best_layer"])
    # Fall back to the shared window if best layers differ.
    if best_layer not in v2["layer_vectors"]:
        shared = set(v1["layer_vectors"]) & set(v2["layer_vectors"])
        if not shared:
            return None
        best_layer = sorted(shared, key=int)[len(shared) // 2]

    vec1 = v1["layer_vectors"][best_layer].float()
    vec2 = v2["layer_vectors"][best_layer].float()
    cos = torch.nn.functional.cosine_similarity(
        vec1.unsqueeze(0), vec2.unsqueeze(0)
    ).item()
    return float(cos)


# --------------------------------------------------------------------------- #
# Alpha coherence sweep.
# --------------------------------------------------------------------------- #
def alpha_coherence_sweep(
    model,
    tokenizer,
    sweep_samples,
    layer_vectors: Dict[int, torch.Tensor],
    alphas: List[float],
    *,
    max_new_tokens: int,
    coherence_threshold: float,
) -> Tuple[Optional[float], List[dict]]:
    """Pick the largest alpha whose output stays coherent vs the control.

    For each alpha, generate a SHORT completion under steering and measure the
    mean unique-token ratio and parse-failure rate. An alpha is "coherent" if
    its mean unique-token ratio is at least ``coherence_threshold`` times the
    unsteered control ratio. Returns (chosen_alpha, sweep_records).
    """
    # Control (no steering) baseline.
    control_ratios = []
    for sample in sweep_samples:
        text = steered_generate(
            model, tokenizer, sample.prompt, runtime=None, max_new_tokens=max_new_tokens
        )
        control_ratios.append(unique_token_ratio(tokenizer, text))
    control_ratio = sum(control_ratios) / len(control_ratios) if control_ratios else 0.0
    log(f"[sweep] control mean unique-token ratio = {control_ratio:.3f}")

    sweep_records: List[dict] = [{
        "alpha": 0.0,
        "condition": "control",
        "mean_unique_token_ratio": control_ratio,
        "parse_failure_rate": None,
        "coherent": True,
    }]

    chosen: Optional[float] = None
    for alpha in sorted(alphas):
        runtime = SteeringRuntime(layer_vectors=layer_vectors, alpha=alpha)
        ratios = []
        parse_failures = 0
        for sample in sweep_samples:
            text = steered_generate(
                model, tokenizer, sample.prompt, runtime=runtime,
                max_new_tokens=max_new_tokens,
            )
            ratios.append(unique_token_ratio(tokenizer, text))
            if parse_answer(text) is None:
                parse_failures += 1
        mean_ratio = sum(ratios) / len(ratios) if ratios else 0.0
        parse_fail_rate = parse_failures / len(sweep_samples) if sweep_samples else 1.0
        coherent = (
            control_ratio > 0
            and mean_ratio >= coherence_threshold * control_ratio
        )
        sweep_records.append({
            "alpha": alpha,
            "condition": "steer",
            "mean_unique_token_ratio": mean_ratio,
            "parse_failure_rate": parse_fail_rate,
            "coherent": bool(coherent),
        })
        log(f"[sweep] alpha={alpha:>5}: unique-ratio={mean_ratio:.3f} "
            f"parse-fail={parse_fail_rate:.2f} coherent={coherent}")
        if coherent:
            # Keep the largest coherent alpha (alphas iterated ascending).
            chosen = alpha

    return chosen, sweep_records


# --------------------------------------------------------------------------- #
# Control battery.
# --------------------------------------------------------------------------- #
def to_layer_vectors(str_keyed: Dict[str, torch.Tensor]) -> Dict[int, torch.Tensor]:
    """Convert a str(layer)->tensor dict into an int(layer)->tensor dict."""
    return {int(layer): vec for layer, vec in str_keyed.items()}


def build_shuffled_null(
    layer_vectors: Dict[int, torch.Tensor],
    seed: int,
) -> Dict[int, torch.Tensor]:
    """Per-layer coordinate-shuffled 'null' vector (matched norm, scrambled dir)."""
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    null: Dict[int, torch.Tensor] = {}
    for layer, vec in layer_vectors.items():
        perm = torch.randperm(vec.shape[0], generator=generator)
        null[layer] = vec[perm].clone()
    return null


@torch.no_grad()
def run_control_battery(
    model,
    tokenizer,
    eval_samples,
    vectors_by_name: Dict[str, Dict[int, torch.Tensor]],
    alpha: float,
    letter_ids: Dict[str, int],
    *,
    gen_max_new_tokens: int,
    coherence_threshold: float,
    seed: int,
) -> List[dict]:
    """Per-item margins for control/steer/reversed/null across all vectors.

    ``control`` is computed ONCE per item (steering-independent) and reused for
    every vector so we don't repeat the unsteered forward pass needlessly.
    """
    results: List[dict] = []

    for sample in eval_samples:
        sample_id = sample.scenario.base_id
        target = sample.target

        # ---- control: no steering (compute once per item) --------------- #
        c_margin, c_lt, c_lo = answer_only_margin(
            model, tokenizer, sample.prompt, target, letter_ids
        )
        c_text = steered_generate(
            model, tokenizer, sample.prompt, runtime=None,
            max_new_tokens=gen_max_new_tokens,
        )
        c_answer = parse_answer(c_text)
        control_record = {
            "sample_id": sample_id,
            "variant": sample.scenario.variant,
            "target": target,
            "condition": "control",
            "vector": None,
            "alpha": 0.0,
            "margin": c_margin,
            "logit_target": c_lt,
            "logit_other": c_lo,
            "model_answer": c_answer,
            "degenerate_flag": parse_answer(c_text) is None,
        }
        results.append(control_record)

        for name, layer_vectors in vectors_by_name.items():
            null_vectors = build_shuffled_null(layer_vectors, seed=seed + len(name))
            conditions = {
                "steer": (layer_vectors, alpha),
                "reversed": (layer_vectors, -alpha),
                "null": (null_vectors, alpha),
            }
            for condition, (vecs, signed_alpha) in conditions.items():
                runtime = SteeringRuntime(layer_vectors=vecs, alpha=signed_alpha)
                # Margin under steering: install the runtime around the forward
                # pass by temporarily wrapping answer_only_margin's forward.
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
                    "condition": condition,
                    "vector": name,
                    "alpha": signed_alpha,
                    "margin": margin,
                    "logit_target": lt,
                    "logit_other": lo,
                    "model_answer": answer,
                    "degenerate_flag": answer is None,
                })
    return results


@torch.no_grad()
def _steered_margin(
    model,
    tokenizer,
    prompt: str,
    target_letter: str,
    letter_ids: Dict[str, int],
    runtime: SteeringRuntime,
) -> Tuple[float, float, float]:
    """Answer-only margin computed with a steering runtime installed."""
    other_letter = "B" if target_letter == "A" else "A"
    inputs = build_answer_only_inputs(tokenizer, model, prompt)
    install = runtime.install(model)
    try:
        outputs = model(**inputs, use_cache=False)
    finally:
        install.close()
    logits = outputs.logits[0, -1, :].float()
    lt = float(logits[letter_ids[target_letter]].item())
    lo = float(logits[letter_ids[other_letter]].item())
    return lt - lo, lt, lo


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.smoke:
        args.limit = min(args.limit, 4)
        args.sweep_items = 2
        args.sweep_alphas = args.sweep_alphas or [2.0, 8.0]
        log("[smoke] running in smoke mode: limit=4, sweep_items=2, alphas=[2,8]")

    sweep_alphas = args.sweep_alphas or list(DEFAULT_SWEEP_ALPHAS)

    data_dir = Path(args.data_dir) if args.data_dir else _REPO_ROOT / "data"
    courage_steer_dir = data_dir / "courage_steer"
    whole_bible_path = courage_steer_dir / WHOLE_BIBLE_FILE
    courage_passages_path = courage_steer_dir / COURAGE_PASSAGES_FILE
    for path in (whole_bible_path, courage_passages_path):
        if not path.exists():
            raise FileNotFoundError(f"Required corpus missing: {path}")

    output_dir = Path(args.output_dir) if args.output_dir else _REPO_ROOT / "results" / "courage_pilot"
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_dir / "_tmp_splithalf"

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
    # 1a. Scripture vectors: whole_bible and courage_pool.
    # ---------------------------------------------------------------- #
    log("[extract] whole_bible ...")
    wb_artifact = extract_scripture_vector(
        runner, whole_bible_path, WHOLE_BIBLE_TARGET,
        args.window_center, args.window_radius,
    )
    log("[extract] courage_pool ...")
    cp_artifact = extract_scripture_vector(
        runner, courage_passages_path, COURAGE_POOL_TARGET,
        args.window_center, args.window_radius,
    )

    wb_payload = wb_artifact["virtues"][WHOLE_BIBLE_TARGET]
    cp_payload = cp_artifact["virtues"][COURAGE_POOL_TARGET]

    # Anchor the shared layer window on the courage_pool extraction so all
    # vectors (scripture / ideal / random) act on the same layers.
    layer_window = list(cp_payload["layer_window"])
    log(f"[extract] shared layer window = {layer_window} "
        f"(best_layer courage_pool={cp_payload['best_layer']}, "
        f"whole_bible={wb_payload['best_layer']})")

    # ---------------------------------------------------------------- #
    # 1b. ideal_courage (positive control) on BUILD half of courage.
    # ---------------------------------------------------------------- #
    scenarios = load_scenarios("courage", variants=["ratio"], data_dir=data_dir)
    if args.limit:
        # Deterministic prefix by base_id so BUILD/EVAL are stable.
        scenarios = sorted(scenarios, key=lambda s: s.base_id)[: args.limit]
    build_scenarios, eval_scenarios = split_build_eval(scenarios)
    log(f"[ideal] courage ratio scenarios: {len(scenarios)} "
        f"(BUILD={len(build_scenarios)}, EVAL={len(eval_scenarios)})")

    ideal_vectors_str = build_ideal_courage_vectors(
        model, tokenizer, build_scenarios, layer_window
    )

    # ---------------------------------------------------------------- #
    # 1c. random vector (fixed seed) over the same window.
    # ---------------------------------------------------------------- #
    random_vectors_str = build_random_vectors(hidden_size, layer_window, seed=args.seed)

    # Assemble the single combined artifact.
    artifact = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": runner.model_id(),
        "model_path": args.model_path,
        "window_center": args.window_center,
        "window_radius": args.window_radius,
        "layer_window": layer_window,
        "hidden_size": hidden_size,
        "total_layers": total_layers,
        "virtues": {
            WHOLE_BIBLE_TARGET: wb_payload,
            COURAGE_POOL_TARGET: cp_payload,
            "ideal_courage": {
                "source_mode": "courage_build_half_contrast",
                "best_layer": cp_payload["best_layer"],
                "layer_window": layer_window,
                "layer_vectors": ideal_vectors_str,
                "null_vectors": {
                    k: v for k, v in build_shuffled_null(
                        to_layer_vectors(ideal_vectors_str), seed=args.seed + 11
                    ).items()
                },
                "build_scenario_ids": [s.base_id for s in build_scenarios],
            },
            "random": {
                "source_mode": "fixed_seed_random_unit",
                "best_layer": cp_payload["best_layer"],
                "layer_window": layer_window,
                "layer_vectors": random_vectors_str,
                "seed": args.seed,
            },
        },
    }
    # null_vectors in ideal are int-keyed above; normalize to str keys for save.
    artifact["virtues"]["ideal_courage"]["null_vectors"] = {
        str(k): v for k, v in artifact["virtues"]["ideal_courage"]["null_vectors"].items()
    }

    # ---------------------------------------------------------------- #
    # 2. Split-half reliability gate for the scripture vectors.
    # ---------------------------------------------------------------- #
    log("[gate] split-half reliability ...")
    split_half = {
        WHOLE_BIBLE_TARGET: split_half_reliability(
            runner, whole_bible_path, WHOLE_BIBLE_TARGET,
            args.window_center, args.window_radius, tmp_dir, args.seed,
        ),
        COURAGE_POOL_TARGET: split_half_reliability(
            runner, courage_passages_path, COURAGE_POOL_TARGET,
            args.window_center, args.window_radius, tmp_dir, args.seed,
        ),
    }
    for name, cos in split_half.items():
        log(f"[gate] split-half cosine({name}) = "
            f"{'n/a' if cos is None else f'{cos:.3f}'}")

    # ---------------------------------------------------------------- #
    # Prepare EVAL samples (A/B randomized) for sweep + battery.
    # ---------------------------------------------------------------- #
    from virtue_bench.core.loader import prepare_samples
    eval_samples = prepare_samples(eval_scenarios, seed=args.seed)
    if not eval_samples:
        raise RuntimeError("No EVAL samples available; increase --limit.")
    sweep_samples = eval_samples[: args.sweep_items]

    # ---------------------------------------------------------------- #
    # 3. Alpha sweep / coherence gate (on the requested vector).
    # ---------------------------------------------------------------- #
    sweep_vec_name = args.sweep_vector
    if sweep_vec_name not in artifact["virtues"]:
        raise ValueError(
            f"--sweep-vector={sweep_vec_name} not in built vectors "
            f"{list(artifact['virtues'])}."
        )
    sweep_layer_vectors = to_layer_vectors(
        artifact["virtues"][sweep_vec_name]["layer_vectors"]
    )
    log(f"[sweep] coherence sweep on '{sweep_vec_name}' over alphas={sweep_alphas}")
    chosen_alpha, sweep_records = alpha_coherence_sweep(
        model, tokenizer, sweep_samples, sweep_layer_vectors, sweep_alphas,
        max_new_tokens=args.sweep_max_new_tokens,
        coherence_threshold=args.coherence_threshold,
    )
    if chosen_alpha is None:
        chosen_alpha = min(sweep_alphas)
        log(f"[sweep] no alpha passed coherence gate; "
            f"falling back to smallest alpha={chosen_alpha}")
    else:
        log(f"[sweep] chosen alpha (largest coherent) = {chosen_alpha}")

    # ---------------------------------------------------------------- #
    # 5. Control battery on EVAL half at the chosen alpha.
    # ---------------------------------------------------------------- #
    vectors_by_name = {
        "ideal_courage": to_layer_vectors(ideal_vectors_str),
        WHOLE_BIBLE_TARGET: to_layer_vectors(wb_payload["layer_vectors"]),
        COURAGE_POOL_TARGET: to_layer_vectors(cp_payload["layer_vectors"]),
    }
    log(f"[battery] control battery: {len(eval_samples)} items x "
        f"{len(vectors_by_name)} vectors at alpha={chosen_alpha}")
    battery_results = run_control_battery(
        model, tokenizer, eval_samples, vectors_by_name, chosen_alpha, letter_ids,
        gen_max_new_tokens=args.gen_max_new_tokens,
        coherence_threshold=args.coherence_threshold,
        seed=args.seed,
    )

    # ---------------------------------------------------------------- #
    # 6. Write results + save vectors.
    # ---------------------------------------------------------------- #
    results_doc = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": runner.model_id(),
            "model_path": args.model_path,
            "smoke": args.smoke,
            "seed": args.seed,
            "chosen_alpha": chosen_alpha,
            "sweep_alphas": sweep_alphas,
            "sweep_vector": sweep_vec_name,
            "coherence_threshold": args.coherence_threshold,
            "window_center": args.window_center,
            "window_radius": args.window_radius,
            "layer_window": layer_window,
            "best_layers": {
                WHOLE_BIBLE_TARGET: wb_payload["best_layer"],
                COURAGE_POOL_TARGET: cp_payload["best_layer"],
            },
            "split_half_cosines": split_half,
            "alpha_sweep": sweep_records,
            "n_build": len(build_scenarios),
            "n_eval": len(eval_samples),
            "vectors": list(vectors_by_name.keys()),
        },
        "results": battery_results,
    }

    results_path = output_dir / "pilot_results.json"
    with open(results_path, "w", encoding="utf-8") as handle:
        json.dump(results_doc, handle, indent=2)
    log(f"[write] results -> {results_path}")

    vectors_path = output_dir / "pilot_vectors.pt"
    torch.save(artifact, vectors_path)
    log(f"[write] vectors -> {vectors_path}")

    # Clean up temp split-half corpora.
    try:
        for child in tmp_dir.glob("*.jsonl"):
            child.unlink()
        if tmp_dir.exists():
            tmp_dir.rmdir()
    except OSError:
        pass

    log("[done] pilot complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
