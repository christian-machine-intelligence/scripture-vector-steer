from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import torch
except ImportError:  # pragma: no cover - used only in hf/torch environments
    torch = None  # type: ignore


DEFAULT_TARGETS = [
    "prudence_scripture",
    "justice_scripture",
    "fortitude_scripture",
    "temperance_scripture",
]


def require_torch():
    if torch is None:
        raise ImportError("This script requires torch so it can read and write vector artifacts.")


def unit(vector):
    vector = vector.float()
    return vector / vector.norm(p=2).clamp_min(1e-8)


def project_away(vector, component):
    component = unit(component)
    return vector.float() - torch.dot(vector.float().flatten(), component.flatten()) * component


def build_null_vectors(layer_vectors: dict[int, Any], seed: int) -> dict[str, Any]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    null_vectors = {}
    for layer, vector in layer_vectors.items():
        permutation = torch.randperm(vector.shape[0], generator=generator)
        null_vectors[str(layer)] = vector[permutation].clone().cpu()
    return null_vectors


def load_layer_vectors(payload: dict[str, Any], key: str) -> dict[int, Any]:
    return {int(layer): vector for layer, vector in payload[key].items()}


def build_residual_artifact(
    artifact: dict[str, Any],
    *,
    targets: list[str],
    normalize: bool,
) -> dict[str, Any]:
    available_targets = [target for target in targets if target in artifact["virtues"]]
    if len(available_targets) < 2:
        raise ValueError("Need at least two available targets to build residual vectors.")

    real = {
        target: load_layer_vectors(artifact["virtues"][target], "layer_vectors")
        for target in available_targets
    }
    common_layers = sorted(set.intersection(*(set(real[target]) for target in available_targets)))
    general_by_layer = {}
    for layer in common_layers:
        stacked = torch.stack([unit(real[target][layer]) for target in available_targets], dim=0)
        general_by_layer[layer] = unit(stacked.mean(dim=0))

    output = deepcopy(artifact)
    output["created_at"] = datetime.now(timezone.utc).isoformat()
    output["derived_from"] = {
        "source_created_at": artifact.get("created_at"),
        "source_model": artifact.get("model"),
        "source_extraction_method": artifact.get("extraction_method"),
        "operation": "project_away_mean_scripture_general_component",
        "targets": available_targets,
        "common_layers": common_layers,
        "normalize_residuals": normalize,
    }
    output["extraction_method"] = "scripture_general_residual"

    for target in available_targets:
        residual_vectors: dict[int, Any] = {}
        residual_norm_ratios: dict[str, float] = {}
        for layer in sorted(real[target]):
            vector = real[target][layer].float()
            if layer in general_by_layer:
                residual = project_away(vector, general_by_layer[layer])
            else:
                residual = vector.clone()
            residual_norm_ratios[str(layer)] = (
                residual.norm(p=2) / vector.norm(p=2).clamp_min(1e-8)
            ).item()
            if normalize:
                residual = unit(residual)
            residual_vectors[layer] = residual.cpu()

        payload = output["virtues"][target]
        payload["extraction_method_requested"] = "scripture_general_residual"
        payload["extraction_method_used"] = "scripture_general_residual"
        payload["source_mode"] = "target_scripture_residual_after_shared_scripture_general_projection"
        payload["background_mode"] = "scripture_general_component_projected_out"
        payload["residual_norm_ratios"] = residual_norm_ratios
        payload["layer_vectors"] = {
            str(layer): vector.cpu() for layer, vector in residual_vectors.items()
        }
        payload["null_vectors"] = build_null_vectors(
            residual_vectors,
            seed=int(payload.get("best_layer") or 0) + len(target) + 1000,
        )

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Cardinal Virtue residual vector artifact.")
    parser.add_argument("--vectors", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--targets", nargs="+", default=DEFAULT_TARGETS)
    parser.add_argument(
        "--preserve-residual-norm",
        action="store_true",
        help="Do not normalize residual directions after subtracting the shared component.",
    )
    args = parser.parse_args()

    require_torch()
    artifact = torch.load(args.vectors, map_location="cpu")
    residual = build_residual_artifact(
        artifact,
        targets=args.targets,
        normalize=not args.preserve_residual_norm,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(residual, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
