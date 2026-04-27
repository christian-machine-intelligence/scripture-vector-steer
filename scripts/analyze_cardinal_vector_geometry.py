from __future__ import annotations

import argparse
import json
from itertools import combinations
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
        raise ImportError("This diagnostic requires torch so it can read vector artifacts.")


def cosine(left, right) -> float:
    left = left.float().flatten()
    right = right.float().flatten()
    denom = left.norm(p=2) * right.norm(p=2)
    if denom.item() <= 1e-12:
        return 0.0
    return torch.dot(left, right).div(denom).item()


def unit(vector):
    vector = vector.float()
    denom = vector.norm(p=2).clamp_min(1e-8)
    return vector / denom


def project_away(vector, component):
    vector = vector.float()
    component = unit(component)
    return vector - torch.dot(vector.flatten(), component.flatten()) * component


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def rounded(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def layer_vectors(payload: dict[str, Any], key: str) -> dict[int, Any]:
    return {int(layer): vector for layer, vector in payload[key].items()}


def concat_layers(vectors_by_layer: dict[int, Any], layers: list[int]):
    return torch.cat([vectors_by_layer[layer].float().flatten() for layer in layers], dim=0)


def analyze(artifact: dict[str, Any], targets: list[str]) -> dict[str, Any]:
    virtues = artifact["virtues"]
    available_targets = [target for target in targets if target in virtues]
    if len(available_targets) < 2:
        raise ValueError("Need at least two available targets for geometry diagnostics.")

    real = {
        target: layer_vectors(virtues[target], "layer_vectors")
        for target in available_targets
    }
    null = {
        target: layer_vectors(virtues[target], "null_vectors")
        for target in available_targets
    }
    common_layers = sorted(set.intersection(*(set(real[target]) for target in available_targets)))

    target_rows = []
    for target in available_targets:
        layers = sorted(real[target])
        real_null_by_layer = [
            cosine(real[target][layer], null[target][layer])
            for layer in layers
            if layer in null[target]
        ]
        target_rows.append(
            {
                "target": target,
                "best_layer": virtues[target].get("best_layer"),
                "layer_window": virtues[target].get("layer_window"),
                "alpha": virtues[target].get("alpha"),
                "dev_accuracy": virtues[target].get("dev_accuracy"),
                "dev_specificity": virtues[target].get("dev_specificity"),
                "test_accuracy": virtues[target].get("test_accuracy"),
                "train_examples": virtues[target].get("train_examples"),
                "dev_examples": virtues[target].get("dev_examples"),
                "test_examples": virtues[target].get("test_examples"),
                "real_null_cosine_mean": mean(real_null_by_layer),
                "real_null_cosine_by_layer": {
                    str(layer): cosine(real[target][layer], null[target][layer])
                    for layer in layers
                    if layer in null[target]
                },
            }
        )

    pair_rows = []
    for left, right in combinations(available_targets, 2):
        shared = sorted(set(real[left]).intersection(real[right]))
        if shared:
            real_cos = cosine(concat_layers(real[left], shared), concat_layers(real[right], shared))
            null_cos = cosine(concat_layers(null[left], shared), concat_layers(null[right], shared))
            cross_left_null_right = cosine(concat_layers(real[left], shared), concat_layers(null[right], shared))
            cross_right_null_left = cosine(concat_layers(real[right], shared), concat_layers(null[left], shared))
        else:
            real_cos = None
            null_cos = None
            cross_left_null_right = None
            cross_right_null_left = None
        pair_rows.append(
            {
                "left": left,
                "right": right,
                "shared_layers": shared,
                "real_cosine": real_cos,
                "null_cosine": null_cos,
                "left_real_to_right_null_cosine": cross_left_null_right,
                "right_real_to_left_null_cosine": cross_right_null_left,
            }
        )

    general_by_layer = {}
    for layer in common_layers:
        stacked = torch.stack([unit(real[target][layer]) for target in available_targets], dim=0)
        general_by_layer[layer] = unit(stacked.mean(dim=0))

    residual = {}
    null_residual = {}
    residual_rows = []
    for target in available_targets:
        residual[target] = {}
        null_residual[target] = {}
        real_to_general = []
        residual_norm_ratios = []
        null_residual_norm_ratios = []
        residual_null_cosines = []
        for layer in common_layers:
            general = general_by_layer[layer]
            r = real[target][layer].float()
            n = null[target][layer].float()
            rr = project_away(r, general)
            nr = project_away(n, general)
            residual[target][layer] = rr
            null_residual[target][layer] = nr
            real_to_general.append(cosine(r, general))
            residual_norm_ratios.append((rr.norm(p=2) / r.norm(p=2).clamp_min(1e-8)).item())
            null_residual_norm_ratios.append((nr.norm(p=2) / n.norm(p=2).clamp_min(1e-8)).item())
            residual_null_cosines.append(cosine(rr, nr))
        residual_rows.append(
            {
                "target": target,
                "real_to_scripture_general_cosine_mean": mean(real_to_general),
                "real_residual_norm_ratio_mean": mean(residual_norm_ratios),
                "null_residual_norm_ratio_mean": mean(null_residual_norm_ratios),
                "real_residual_to_null_residual_cosine_mean": mean(residual_null_cosines),
            }
        )

    residual_pair_rows = []
    for left, right in combinations(available_targets, 2):
        if not common_layers:
            residual_cosine = None
        else:
            left_vec = concat_layers(residual[left], common_layers)
            right_vec = concat_layers(residual[right], common_layers)
            residual_cosine = cosine(left_vec, right_vec)
        residual_pair_rows.append(
            {
                "left": left,
                "right": right,
                "residual_cosine": residual_cosine,
            }
        )

    return {
        "version": 1,
        "model": artifact.get("model"),
        "extraction_method": artifact.get("extraction_method"),
        "targets": available_targets,
        "common_layers": common_layers,
        "target_rows": target_rows,
        "pair_rows": pair_rows,
        "residual_rows": residual_rows,
        "residual_pair_rows": residual_pair_rows,
        "summary": {
            "mean_real_null_cosine": mean([row["real_null_cosine_mean"] for row in target_rows]),
            "mean_pairwise_real_cosine": mean([
                row["real_cosine"] for row in pair_rows if row["real_cosine"] is not None
            ]),
            "mean_pairwise_null_cosine": mean([
                row["null_cosine"] for row in pair_rows if row["null_cosine"] is not None
            ]),
            "mean_real_to_scripture_general_cosine": mean([
                row["real_to_scripture_general_cosine_mean"] for row in residual_rows
            ]),
            "mean_real_residual_norm_ratio": mean([
                row["real_residual_norm_ratio_mean"] for row in residual_rows
            ]),
            "mean_residual_pairwise_cosine": mean([
                row["residual_cosine"]
                for row in residual_pair_rows
                if row["residual_cosine"] is not None
            ]),
        },
    }


def write_markdown(payload: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Cardinal Virtue Vector Geometry Diagnostic",
        "",
        f"- Model: `{payload.get('model')}`",
        f"- Extraction method: `{payload.get('extraction_method')}`",
        f"- Targets: `{', '.join(payload.get('targets', []))}`",
        f"- Common layers: `{payload.get('common_layers')}`",
        "",
        "## Summary",
        "",
    ]
    summary = payload["summary"]
    for key, value in summary.items():
        lines.append(f"- {key}: `{rounded(value)}`")

    lines.extend([
        "",
        "## Real Vector vs Null Vector",
        "",
        "| Target | Best layer | Alpha | Real/null cosine | Dev specificity | Train/dev/test |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in payload["target_rows"]:
        counts = f"{row.get('train_examples')}/{row.get('dev_examples')}/{row.get('test_examples')}"
        lines.append(
            f"| {row['target']} | {row.get('best_layer')} | {row.get('alpha')} | "
            f"{rounded(row.get('real_null_cosine_mean'))} | "
            f"{rounded(row.get('dev_specificity'))} | {counts} |"
        )

    lines.extend([
        "",
        "## Pairwise Real-Vector Geometry",
        "",
        "| Pair | Real cosine | Null cosine | Left real/right null | Right real/left null |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for row in payload["pair_rows"]:
        pair = f"{row['left']} / {row['right']}"
        lines.append(
            f"| {pair} | {rounded(row['real_cosine'])} | {rounded(row['null_cosine'])} | "
            f"{rounded(row['left_real_to_right_null_cosine'])} | "
            f"{rounded(row['right_real_to_left_null_cosine'])} |"
        )

    lines.extend([
        "",
        "## Scripture-General Residual",
        "",
        "The scripture-general component is the mean normalized real vector across the four targets at each shared layer. The residual is each target vector after projecting away that shared component.",
        "",
        "| Target | Real to scripture-general cosine | Residual norm ratio | Null residual norm ratio | Real residual/null residual cosine |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for row in payload["residual_rows"]:
        lines.append(
            f"| {row['target']} | {rounded(row['real_to_scripture_general_cosine_mean'])} | "
            f"{rounded(row['real_residual_norm_ratio_mean'])} | "
            f"{rounded(row['null_residual_norm_ratio_mean'])} | "
            f"{rounded(row['real_residual_to_null_residual_cosine_mean'])} |"
        )

    lines.extend([
        "",
        "## Pairwise Residual Geometry",
        "",
        "| Pair | Residual cosine |",
        "| --- | ---: |",
    ])
    for row in payload["residual_pair_rows"]:
        lines.append(f"| {row['left']} / {row['right']} | {rounded(row['residual_cosine'])} |")

    lines.extend([
        "",
        "## Interpretation Guide",
        "",
        "- High real/null cosine means the null control is not cleanly inert for that target.",
        "- High pairwise real-vector cosine means the virtue vectors are not very distinct.",
        "- High real-to-scripture-general cosine means the vector is dominated by a shared Scripture-general component.",
        "- A low residual norm ratio means little virtue-specific signal remains after removing the shared component.",
        "",
    ])
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose Cardinal Virtue vector geometry.")
    parser.add_argument("--vectors", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--targets", nargs="+", default=DEFAULT_TARGETS)
    args = parser.parse_args()

    require_torch()
    artifact = torch.load(args.vectors, map_location="cpu")
    payload = analyze(artifact, args.targets)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
