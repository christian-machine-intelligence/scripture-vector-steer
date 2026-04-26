from __future__ import annotations

import argparse
import json
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

DEFAULT_RECIPES = [
    "target_vs_other",
    "partial_center_0p50",
    "partial_center_0p75",
    "scripture_plus_accent_1p0_1p0",
    "scripture_plus_accent_1p0_2p0",
    "mixed_generic_other_1p0_1p0",
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


def project_component(vector, component):
    component = unit(component)
    return torch.dot(vector.float().flatten(), component.flatten()) * component


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


def recipe_slug(recipe: str) -> str:
    return recipe.replace(".", "p").replace("-", "_")


def parse_weighted_recipe(recipe: str, prefix: str) -> tuple[float, float] | None:
    if not recipe.startswith(prefix):
        return None
    raw = recipe.removeprefix(prefix)
    parts = raw.split("_")
    if len(parts) != 2:
        raise ValueError(f"Expected two weights in recipe {recipe!r}")
    return tuple(float(part.replace("p", ".")) for part in parts)  # type: ignore[return-value]


def parse_partial_center(recipe: str) -> float | None:
    prefix = "partial_center_"
    if not recipe.startswith(prefix):
        return None
    return float(recipe.removeprefix(prefix).replace("p", "."))


def common_layers_for(real: dict[str, dict[int, Any]]) -> list[int]:
    return sorted(set.intersection(*(set(layers) for layers in real.values())))


def build_general_by_layer(
    real: dict[str, dict[int, Any]],
    targets: list[str],
    common_layers: list[int],
) -> dict[int, Any]:
    general = {}
    for layer in common_layers:
        stacked = torch.stack([unit(real[target][layer]) for target in targets], dim=0)
        general[layer] = unit(stacked.mean(dim=0))
    return general


def build_recipe_vectors(
    real: dict[str, dict[int, Any]],
    *,
    targets: list[str],
    common_layers: list[int],
    general_by_layer: dict[int, Any],
    recipe: str,
) -> dict[str, dict[int, Any]]:
    output: dict[str, dict[int, Any]] = {target: {} for target in targets}
    partial_center = parse_partial_center(recipe)
    scripture_plus = parse_weighted_recipe(recipe, "scripture_plus_accent_")
    mixed = parse_weighted_recipe(recipe, "mixed_generic_other_")

    for target in targets:
        others = [name for name in targets if name != target]
        for layer in common_layers:
            target_vector = real[target][layer].float()
            general = general_by_layer[layer]
            other_mean = unit(torch.stack([unit(real[name][layer]) for name in others], dim=0).mean(dim=0))
            other_accent = unit(unit(target_vector) - other_mean)
            residual = project_away(target_vector, general)

            if recipe == "target_vs_other":
                candidate = other_accent
            elif partial_center is not None:
                candidate = target_vector - partial_center * project_component(target_vector, general)
            elif scripture_plus is not None:
                scripture_weight, accent_weight = scripture_plus
                candidate = scripture_weight * general + accent_weight * unit(residual)
            elif mixed is not None:
                generic_weight, other_weight = mixed
                candidate = generic_weight * unit(target_vector) + other_weight * other_accent
            else:
                raise ValueError(f"Unknown recipe: {recipe}")

            output[target][layer] = unit(candidate).cpu()
    return output


def build_candidate_artifact(
    artifact: dict[str, Any],
    *,
    targets: list[str],
    recipe: str,
) -> dict[str, Any]:
    available_targets = [target for target in targets if target in artifact["virtues"]]
    if len(available_targets) < 2:
        raise ValueError("Need at least two available targets to build candidate vectors.")

    real = {
        target: load_layer_vectors(artifact["virtues"][target], "layer_vectors")
        for target in available_targets
    }
    common_layers = common_layers_for(real)
    general_by_layer = build_general_by_layer(real, available_targets, common_layers)
    recipe_vectors = build_recipe_vectors(
        real,
        targets=available_targets,
        common_layers=common_layers,
        general_by_layer=general_by_layer,
        recipe=recipe,
    )

    output = deepcopy(artifact)
    output["created_at"] = datetime.now(timezone.utc).isoformat()
    output["derived_from"] = {
        "source_created_at": artifact.get("created_at"),
        "source_model": artifact.get("model"),
        "source_extraction_method": artifact.get("extraction_method"),
        "operation": "cardinal_candidate_vector_recipe",
        "recipe": recipe,
        "targets": available_targets,
        "common_layers": common_layers,
    }
    output["extraction_method"] = f"cardinal_candidate_{recipe_slug(recipe)}"

    for target in available_targets:
        payload = output["virtues"][target]
        payload["extraction_method_requested"] = output["extraction_method"]
        payload["extraction_method_used"] = output["extraction_method"]
        payload["source_mode"] = "candidate_cardinal_scripture_vector_recipe"
        payload["background_mode"] = recipe
        payload["layer_vectors"] = {
            str(layer): vector.cpu()
            for layer, vector in recipe_vectors[target].items()
        }
        payload["null_vectors"] = build_null_vectors(
            recipe_vectors[target],
            seed=int(payload.get("best_layer") or 0) + len(target) + len(recipe) + 2000,
        )

    return output


def write_index(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build candidate Cardinal Virtue vector artifacts from a frozen source artifact."
    )
    parser.add_argument("--vectors", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prefix", default="cardinal_v1_candidate")
    parser.add_argument("--targets", nargs="+", default=DEFAULT_TARGETS)
    parser.add_argument("--recipes", nargs="+", default=DEFAULT_RECIPES)
    args = parser.parse_args()

    require_torch()
    source = torch.load(args.vectors, map_location="cpu")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for recipe in args.recipes:
        slug = recipe_slug(recipe)
        artifact = build_candidate_artifact(source, targets=args.targets, recipe=recipe)
        output_path = args.output_dir / f"{args.prefix}_{slug}_vectors.pt"
        torch.save(artifact, output_path)
        rows.append(
            {
                "recipe": recipe,
                "slug": slug,
                "path": str(output_path),
                "extraction_method": artifact["extraction_method"],
            }
        )
        print(f"Wrote {output_path}")

    write_index(rows, args.output_dir / f"{args.prefix}_index.json")


if __name__ == "__main__":
    main()
