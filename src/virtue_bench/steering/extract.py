"""Vector extraction for the Iconoclast activation-space experiment."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import random
from typing import Dict, Iterable, List, Optional

from ..core.bible import load_bible_chapters
from ..core.psalms import (
    get_psalm_numbers,
    is_psalm_family_target,
    parse_psalm_family_target,
)
from .corpora import (
    CORPUS_FILE,
    DEFAULT_VIRTUE_TARGETS,
    POOLED_VIRTUE_TARGET,
    SCRIPTURE_FAMILY_TARGETS,
    SCRIPTURE_TARGETS,
    build_contrast_pairs,
    list_steering_targets,
    load_steering_corpus,
    pooled_virtue_members,
    select_corpus_texts,
)
from .runtime import (
    LayerActivationCollector,
    SteeringRuntime,
    get_decoder_layers,
    get_model_device,
    get_model_hidden_size,
    mean_pool_hidden,
)

try:
    import torch
except ImportError:  # pragma: no cover - exercised when hf extras are absent
    torch = None  # type: ignore


DEFAULT_ALPHA_CANDIDATES = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
EXTRACTION_METHODS = {
    "auto",
    "mean_diff",
    "mean_centered",
    "pca_pairwise",
    "specific_mean_centered",
    "specific_pca_pairwise",
    "scripture_contrast",
    "gospelvec_mean",
}


def _is_scripture_target_name(target: str) -> bool:
    return target in SCRIPTURE_TARGETS or is_psalm_family_target(target)


def _require_torch():
    if torch is None:  # pragma: no cover - defensive guard
        raise ImportError(
            "Activation steering requires the hf optional dependencies. "
            "Install with `pip install .[hf]`."
        )


def _l2_normalize(vector):
    denom = vector.norm(p=2).clamp_min(1e-8)
    return vector / denom


def _cosine_scores(matrix, vector):
    matrix = matrix.float()
    vector = vector.float()
    matrix_norm = matrix / matrix.norm(dim=1, keepdim=True).clamp_min(1e-8)
    vector_norm = vector / vector.norm(p=2).clamp_min(1e-8)
    return torch.matmul(matrix_norm, vector_norm)


def _binary_accuracy(vector, positive_matrix, negative_matrix) -> float:
    pos_scores = _cosine_scores(positive_matrix, vector)
    neg_scores = _cosine_scores(negative_matrix, vector)
    correct = (pos_scores > 0).sum().item() + (neg_scores < 0).sum().item()
    total = positive_matrix.shape[0] + negative_matrix.shape[0]
    return correct / total if total else 0.0


def _binary_margin(vector, positive_matrix, negative_matrix) -> float:
    pos_scores = _cosine_scores(positive_matrix, vector)
    neg_scores = _cosine_scores(negative_matrix, vector)
    if pos_scores.numel() == 0 or neg_scores.numel() == 0:
        return 0.0
    return (pos_scores.mean() - neg_scores.mean()).item()


def _specificity_margin(vector, target_positive_matrix, other_positive_matrix) -> float:
    if target_positive_matrix.shape[0] == 0 or other_positive_matrix.shape[0] == 0:
        return 0.0
    target_scores = _cosine_scores(target_positive_matrix, vector)
    other_scores = _cosine_scores(other_positive_matrix, vector)
    return (target_scores.mean() - other_scores.mean()).item()


def _pairwise_accuracy(vector, positive_matrix, negative_matrix) -> Optional[float]:
    pair_count = min(positive_matrix.shape[0], negative_matrix.shape[0])
    if pair_count == 0:
        return None
    pos_scores = _cosine_scores(positive_matrix[:pair_count], vector)
    neg_scores = _cosine_scores(negative_matrix[:pair_count], vector)
    return (pos_scores > neg_scores).float().mean().item()


def _accuracy_tolerance(positive_count: int, negative_count: int) -> float:
    total = positive_count + negative_count
    if total <= 0:
        return 0.0
    return 1.0 / total


def _top_candidates_within_tolerance(scores: Dict[object, float], tolerance: float) -> List[object]:
    if not scores:
        return []
    best_score = max(scores.values())
    return [key for key, score in scores.items() if score >= (best_score - tolerance)]


def _layer_priority(
    layer: int,
    *,
    layer_scores: Dict[int, float],
    layer_pair_scores: Dict[int, Optional[float]],
    layer_specificity: Dict[int, float],
    layer_margins: Dict[int, float],
    midpoint: int,
):
    return (
        layer_specificity[layer] > 0,
        layer_specificity[layer],
        layer_pair_scores[layer] if layer_pair_scores[layer] is not None else float("-inf"),
        layer_margins[layer],
        layer_scores[layer],
        -abs(layer - midpoint),
    )


def _alpha_priority(
    alpha: float,
    *,
    alpha_scores: Dict[float, float],
    alpha_specificity: Dict[float, float],
    alpha_margins: Dict[float, float],
):
    return (
        alpha_specificity[alpha] > 0,
        alpha_specificity[alpha],
        alpha_margins[alpha],
        alpha_scores[alpha],
        alpha,
    )


def _select_layer(
    *,
    method_used: str,
    layer_scores: Dict[int, float],
    layer_pair_scores: Dict[int, Optional[float]],
    layer_specificity: Dict[int, float],
    layer_margins: Dict[int, float],
    midpoint: int,
    tolerance: float,
):
    if method_used.startswith("specific_"):
        layer_candidates = _top_candidates_within_tolerance(layer_scores, tolerance)
        best_layer = max(
            layer_candidates,
            key=lambda layer: _layer_priority(
                layer,
                layer_scores=layer_scores,
                layer_pair_scores=layer_pair_scores,
                layer_specificity=layer_specificity,
                layer_margins=layer_margins,
                midpoint=midpoint,
            ),
        )
        return best_layer, "specificity_within_accuracy_tolerance", layer_candidates

    best_layer = max(
        layer_scores,
        key=lambda layer: (
            layer_scores[layer],
            layer_pair_scores[layer] if layer_pair_scores[layer] is not None else float("-inf"),
            layer_specificity[layer],
            layer_margins[layer],
            -abs(layer - midpoint),
        ),
    )
    return best_layer, "dev_accuracy", list(layer_scores.keys())


def _select_alpha(
    *,
    method_used: str,
    alpha_scores: Dict[float, float],
    alpha_specificity: Dict[float, float],
    alpha_margins: Dict[float, float],
    tolerance: float,
):
    if method_used.startswith("specific_"):
        alpha_candidates = _top_candidates_within_tolerance(alpha_scores, tolerance)
        best_alpha = max(
            alpha_candidates,
            key=lambda candidate: _alpha_priority(
                candidate,
                alpha_scores=alpha_scores,
                alpha_specificity=alpha_specificity,
                alpha_margins=alpha_margins,
            ),
        )
        return best_alpha, "specificity_within_accuracy_tolerance", alpha_candidates

    best_alpha = max(
        alpha_scores,
        key=lambda candidate: (
            alpha_scores[candidate],
            alpha_specificity[candidate],
            alpha_margins[candidate],
            -candidate,
        ),
    )
    return best_alpha, "dev_accuracy", list(alpha_scores.keys())


def _compute_pca_basis(matrix, variance_threshold: float = 0.5):
    if matrix.shape[0] < 2:
        return None
    centered = matrix.float() - matrix.float().mean(dim=0, keepdim=True)
    _, singular_values, vh = torch.linalg.svd(centered, full_matrices=False)
    variance = singular_values.square()
    variance_ratio = variance / variance.sum().clamp_min(1e-8)
    cumulative = torch.cumsum(variance_ratio, dim=0)
    k = int((cumulative < variance_threshold).sum().item()) + 1
    k = min(k, vh.shape[0])
    return vh[:k].T


def _project_out_basis(vector, basis):
    if basis is None:
        return vector
    basis = basis.to(vector.dtype)
    return vector - basis @ (basis.T @ vector)


def _combine_bases(*bases):
    active = [basis.float() for basis in bases if basis is not None and basis.numel() > 0]
    if not active:
        return None
    stacked = torch.cat(active, dim=1)
    if stacked.shape[1] == 1:
        return stacked
    q, _ = torch.linalg.qr(stacked, mode="reduced")
    return q


def _align_direction(direction, reference):
    if torch.dot(direction.float(), reference.float()) < 0:
        return -direction
    return direction


def _mean_difference_direction(positive_matrix, negative_matrix):
    return positive_matrix.mean(dim=0) - negative_matrix.mean(dim=0)


def _mean_centered_direction(positive_matrix, negative_matrix, neutral_matrix):
    background = [positive_matrix, negative_matrix]
    if neutral_matrix.shape[0] > 0:
        background.append(neutral_matrix)
    background_mean = torch.cat(background, dim=0).mean(dim=0)
    direction = positive_matrix.mean(dim=0) - background_mean
    return _align_direction(direction, _mean_difference_direction(positive_matrix, negative_matrix))


def _specific_mean_centered_direction(
    positive_matrix,
    negative_matrix,
    neutral_matrix,
    other_positive_matrix,
):
    background = [positive_matrix, negative_matrix]
    if neutral_matrix.shape[0] > 0:
        background.append(neutral_matrix)
    if other_positive_matrix.shape[0] > 0:
        background.append(other_positive_matrix)
    background_mean = torch.cat(background, dim=0).mean(dim=0)
    direction = positive_matrix.mean(dim=0) - background_mean
    return _align_direction(direction, _mean_difference_direction(positive_matrix, negative_matrix))


def _pca_pairwise_direction(positive_matrix, negative_matrix):
    pair_count = min(positive_matrix.shape[0], negative_matrix.shape[0])
    if pair_count == 0:
        raise ValueError("Pairwise PCA extraction requires at least one matched positive/negative pair.")

    deltas = positive_matrix[:pair_count].float() - negative_matrix[:pair_count].float()
    if pair_count == 1:
        return deltas[0]

    centered = deltas - deltas.mean(dim=0, keepdim=True)
    _, _, vh = torch.linalg.svd(centered, full_matrices=False)
    direction = vh[0]
    return _align_direction(direction, deltas.mean(dim=0))


def _gospelvec_mean_direction(target_matrix, global_matrix):
    return target_matrix.mean(dim=0) - global_matrix.mean(dim=0)


def _scripture_contrast_direction(target_matrix, background_matrix):
    return target_matrix.mean(dim=0) - background_matrix.mean(dim=0)


def _resolve_extraction_method(requested: str, *, pair_count: int, target: Optional[str] = None) -> str:
    if requested not in EXTRACTION_METHODS:
        raise ValueError(f"Unknown extraction method: {requested}")
    if requested == "auto":
        if target is not None and _is_scripture_target_name(target):
            return "scripture_contrast"
        if target in {"christian", POOLED_VIRTUE_TARGET}:
            return "pca_pairwise" if pair_count >= 2 else "mean_centered"
        return "specific_pca_pairwise" if pair_count >= 2 else "specific_mean_centered"
    if requested == "pca_pairwise" and pair_count < 2:
        return "mean_centered"
    if requested == "specific_pca_pairwise" and pair_count < 2:
        return "specific_mean_centered"
    return requested


def _texts(records: Iterable, virtue: str, polarity: str, split: str) -> List[str]:
    return [item.text for item in select_corpus_texts(records, virtue=virtue, polarity=polarity, split=split)]


def _texts_for_virtues(records: Iterable, virtues: List[str], polarity: str, split: str) -> List[str]:
    if not virtues:
        return []
    allowed = set(virtues)
    return [
        item.text
        for item in records
        if item.virtue in allowed and item.polarity == polarity and item.split == split
    ]


def _other_virtue_positive_texts(records: Iterable, virtue: str, split: str) -> List[str]:
    return [
        item.text
        for item in records
        if item.virtue not in {virtue, "neutral"}
        and item.polarity == "positive"
        and item.split == split
    ]


def _word_count(text: str) -> int:
    return len(text.split())


def _passage_windows(
    texts: List[str],
    *,
    min_words: int = 40,
    max_items: int = 3,
) -> List[str]:
    if not texts:
        return []
    if len(texts) == 1:
        return list(texts)
    if sum(_word_count(text) for text in texts) / len(texts) >= min_words:
        return list(texts)

    windows: List[str] = []
    total = len(texts)
    for index in range(total):
        parts: List[str] = []
        words = 0
        step = 0
        while step < total and step < max_items and words < min_words:
            text = texts[(index + step) % total].strip()
            parts.append(text)
            words += _word_count(text)
            step += 1
        windows.append("\n\n".join(parts))
    return windows


def _pair_passage_windows(
    pairs,
    *,
    min_words: int = 40,
    max_items: int = 3,
) -> tuple[List[str], List[str]]:
    if not pairs:
        return [], []

    positive_texts = [pair.positive.text for pair in pairs]
    negative_texts = [pair.negative.text for pair in pairs]
    if len(positive_texts) == 1:
        return positive_texts, negative_texts
    if sum(_word_count(text) for text in positive_texts) / len(positive_texts) >= min_words:
        return positive_texts, negative_texts

    positive_windows: List[str] = []
    negative_windows: List[str] = []
    total = len(pairs)
    for index in range(total):
        positive_parts: List[str] = []
        negative_parts: List[str] = []
        words = 0
        step = 0
        while step < total and step < max_items and words < min_words:
            pair = pairs[(index + step) % total]
            positive_parts.append(pair.positive.text.strip())
            negative_parts.append(pair.negative.text.strip())
            words += _word_count(pair.positive.text)
            step += 1
        positive_windows.append("\n\n".join(positive_parts))
        negative_windows.append("\n\n".join(negative_parts))
    return positive_windows, negative_windows


def _pooled_virtue_pairs(records: Iterable, virtues: List[str], split: str):
    pairs = []
    for virtue in virtues:
        pairs.extend(build_contrast_pairs(records, virtue=virtue, split=split))
    return pairs


def _scripture_books_for_target(target: str) -> List[str]:
    if is_psalm_family_target(target):
        return ["PSA"]
    if target == "psalms":
        return ["PSA"]
    if target == "proverbs":
        return ["PRO"]
    if target == "gospels":
        return ["MAT", "MRK", "LUK", "JHN"]
    if target == "romans":
        return ["ROM"]
    if target == "petrine":
        return ["1PE", "2PE"]
    raise ValueError(f"Unsupported scripture-family target: {target}")


def _scripture_comparison_targets(target_names: List[str]) -> List[str]:
    return list(dict.fromkeys(list(SCRIPTURE_FAMILY_TARGETS) + list(target_names)))


def _scripture_target_psalm_sets(
    target: str,
    *,
    default_psalm_sets: Optional[List[str]] = None,
) -> Optional[List[str]]:
    target_psalm_families = parse_psalm_family_target(target)
    if target_psalm_families is not None:
        return target_psalm_families
    if target == "psalms":
        return default_psalm_sets
    return None


def _neutral_passage_splits(
    records: Iterable,
    *,
    min_words: int,
    max_items: int,
) -> Dict[str, List[str]]:
    return {
        split: _passage_windows(
            _texts(records, "neutral", "neutral", split),
            min_words=min_words,
            max_items=max_items,
        )
        for split in ("train", "dev", "test")
    }


def _split_scripture_chunks(texts: List[str], *, seed: int = 42) -> Dict[str, List[str]]:
    shuffled = list(texts)
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    if total == 0:
        return {"train": [], "dev": [], "test": []}
    if total == 1:
        return {"train": list(shuffled), "dev": [], "test": []}
    if total == 2:
        return {"train": [shuffled[0]], "dev": [shuffled[1]], "test": []}

    holdout = max(1, total // 10)
    test_count = min(holdout, total - 2)
    dev_count = min(holdout, total - test_count - 1)
    train_count = total - dev_count - test_count
    if train_count <= 0:
        train_count = 1
        if dev_count >= test_count and dev_count > 0:
            dev_count -= 1
        elif test_count > 0:
            test_count -= 1

    return {
        "train": shuffled[:train_count],
        "dev": shuffled[train_count:train_count + dev_count],
        "test": shuffled[train_count + dev_count:],
    }


def _chunk_scripture_family_texts(
    tokenizer,
    *,
    target: str,
    max_length: int,
    psalm_vector_sets: Optional[List[str]] = None,
) -> List[str]:
    chapters = load_bible_chapters(books=_scripture_books_for_target(target))
    target_psalm_sets = _scripture_target_psalm_sets(
        target,
        default_psalm_sets=psalm_vector_sets,
    )
    if target_psalm_sets:
        allowed_psalms = set(get_psalm_numbers(psalm_sets=target_psalm_sets))
        chapters = [chapter for chapter in chapters if chapter["chapter"] in allowed_psalms]
    chunks: List[str] = []

    for chapter in chapters:
        book = chapter["book"]
        chapter_no = chapter["chapter"]
        verses = chapter["verses"]
        current_lines: List[str] = []
        current_start: Optional[int] = None
        current_end: Optional[int] = None

        for verse in verses:
            verse_no = verse["verse"]
            verse_line = f"{verse_no}. {verse['text']}"
            if current_start is None:
                candidate_start = verse_no
                candidate_lines = [verse_line]
            else:
                candidate_start = current_start
                candidate_lines = current_lines + [verse_line]

            candidate_end = verse_no
            source = f"{book} {chapter_no}:{candidate_start}-{candidate_end}"
            candidate_text = f"{source}\n{' '.join(candidate_lines)}"
            candidate_tokens = len(tokenizer.encode(candidate_text, add_special_tokens=False))

            if current_lines and candidate_tokens > max_length:
                source = f"{book} {chapter_no}:{current_start}-{current_end}"
                chunks.append(f"{source}\n{' '.join(current_lines)}")
                current_lines = [verse_line]
                current_start = verse_no
                current_end = verse_no
                continue

            current_lines = candidate_lines
            current_start = candidate_start
            current_end = candidate_end

        if current_lines:
            source = f"{book} {chapter_no}:{current_start}-{current_end}"
            chunks.append(f"{source}\n{' '.join(current_lines)}")

    return chunks


def _family_classification_metrics(
    directions: Dict[str, object],
    family_activations: Dict[str, object],
) -> tuple[float, Dict[str, float], Dict[str, float], Dict[str, float]]:
    family_names = list(directions.keys())
    total = 0
    correct = 0
    per_family_accuracy: Dict[str, float] = {}
    per_family_margin: Dict[str, float] = {}
    per_family_specificity: Dict[str, float] = {}

    for family in family_names:
        matrix = family_activations[family]
        if matrix.shape[0] == 0:
            per_family_accuracy[family] = 0.0
            per_family_margin[family] = 0.0
            per_family_specificity[family] = 0.0
            continue

        score_columns = [_cosine_scores(matrix, directions[name]) for name in family_names]
        scores = torch.stack(score_columns, dim=1)
        family_index = family_names.index(family)
        predictions = scores.argmax(dim=1)
        own_scores = scores[:, family_index]

        other_indices = [index for index, name in enumerate(family_names) if name != family]
        if other_indices:
            other_scores = scores[:, other_indices]
            other_best = other_scores.max(dim=1).values
            other_mean = other_scores.mean(dim=1)
            per_family_margin[family] = (own_scores - other_best).mean().item()
            per_family_specificity[family] = (own_scores - other_mean).mean().item()
        else:
            per_family_margin[family] = own_scores.mean().item()
            per_family_specificity[family] = own_scores.mean().item()

        family_correct = (predictions == family_index).sum().item()
        per_family_accuracy[family] = family_correct / matrix.shape[0]
        total += matrix.shape[0]
        correct += family_correct

    overall_accuracy = correct / total if total else 0.0
    return overall_accuracy, per_family_accuracy, per_family_margin, per_family_specificity


def _scripture_target_metrics(
    *,
    target: str,
    directions: Dict[str, object],
    matrix,
) -> tuple[float, float, float]:
    family_names = list(directions.keys())
    if matrix.shape[0] == 0:
        return 0.0, 0.0, 0.0

    score_columns = [_cosine_scores(matrix, directions[name]) for name in family_names]
    scores = torch.stack(score_columns, dim=1)
    target_index = family_names.index(target)
    predictions = scores.argmax(dim=1)
    own_scores = scores[:, target_index]
    other_indices = [index for index, name in enumerate(family_names) if name != target]

    if other_indices:
        other_scores = scores[:, other_indices]
        margin = (own_scores - other_scores.max(dim=1).values).mean().item()
        specificity = (own_scores - other_scores.mean(dim=1)).mean().item()
    else:
        margin = own_scores.mean().item()
        specificity = own_scores.mean().item()

    accuracy = (predictions == target_index).float().mean().item()
    return accuracy, margin, specificity


def _scripture_contrast_metrics(
    vector,
    positive_matrix,
    negative_matrix,
) -> tuple[float, float, Optional[float]]:
    return (
        _binary_accuracy(vector, positive_matrix, negative_matrix),
        _binary_margin(vector, positive_matrix, negative_matrix),
        _pairwise_accuracy(vector, positive_matrix, negative_matrix),
    )


def _select_scripture_layer(
    *,
    target: str,
    layer_scores: Dict[int, float],
    layer_specificity: Dict[int, float],
    layer_margins: Dict[int, float],
    shared_scores: Dict[int, float],
    dev_examples: int,
    midpoint: int,
    window_center: Optional[int],
):
    if window_center is not None:
        return window_center, "fixed", [window_center], 0.0

    tolerance = _accuracy_tolerance(dev_examples, 0)
    candidates = _top_candidates_within_tolerance(layer_scores, tolerance)
    best_layer = max(
        candidates,
        key=lambda layer: (
            layer_specificity[layer] > 0,
            layer_specificity[layer],
            layer_margins[layer],
            layer_scores[layer],
            shared_scores[layer],
            -abs(layer - midpoint),
        ),
    )
    return best_layer, "target_dev_accuracy_with_specificity", candidates, tolerance


def _select_scripture_alpha(
    *,
    alpha_scores: Dict[float, float],
    alpha_specificity: Dict[float, float],
    alpha_margins: Dict[float, float],
    dev_examples: int,
):
    tolerance = _accuracy_tolerance(dev_examples, 0)
    candidates = _top_candidates_within_tolerance(alpha_scores, tolerance)
    best_alpha = max(
        candidates,
        key=lambda alpha: (
            alpha_specificity[alpha] > 0,
            alpha_specificity[alpha],
            alpha_margins[alpha],
            alpha_scores[alpha],
            alpha,
        ),
    )
    return best_alpha, "target_dev_accuracy_with_specificity", candidates, tolerance


def _extract_activations(
    model,
    tokenizer,
    texts: List[str],
    layer_indices: List[int],
    *,
    max_length: int = 256,
    steering_runtime: Optional[SteeringRuntime] = None,
) -> Dict[int, object]:
    _require_torch()
    outputs: Dict[int, List[object]] = {layer: [] for layer in layer_indices}
    device = get_model_device(model)
    hidden_size = get_model_hidden_size(model)

    if not texts:
        return {layer: torch.empty((0, hidden_size), dtype=torch.float32) for layer in layer_indices}

    for text in texts:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
        ).to(device)
        install = steering_runtime.install(model) if steering_runtime is not None else None
        try:
            with LayerActivationCollector(model, layer_indices) as collector:
                with torch.no_grad():
                    model(**inputs, use_cache=False)
            for layer in layer_indices:
                pooled = mean_pool_hidden(collector.activations[layer], inputs["attention_mask"])
                outputs[layer].append(pooled.squeeze(0).cpu())
        finally:
            if install is not None:
                install.close()

    return {layer: torch.stack(values) for layer, values in outputs.items()}


def _build_null_vectors(layer_vectors: Dict[int, object], seed: int) -> Dict[int, object]:
    _require_torch()
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    null_vectors = {}
    for layer, vector in layer_vectors.items():
        permutation = torch.randperm(vector.shape[0], generator=generator)
        null_vectors[layer] = vector[permutation].clone()
    return null_vectors


def _window_around(best_layer: int, total_layers: int, radius: int) -> List[int]:
    start = max(0, best_layer - radius)
    end = min(total_layers, best_layer + radius + 1)
    return list(range(start, end))


def _extract_scripture_family_payloads(
    model,
    tokenizer,
    layer_indices: List[int],
    target_names: List[str],
    neutral_acts,
    neutral_split_acts: Dict[str, Dict[int, object]],
    *,
    neutral_text_splits: Dict[str, List[str]],
    extraction_method_requested: str,
    max_length: int,
    alpha_grid: List[float],
    window_radius: int,
    window_center: Optional[int],
    variance_threshold: float,
    psalm_vector_sets: Optional[List[str]] = None,
):
    resolved_methods = {
        target: _resolve_extraction_method(
            extraction_method_requested,
            pair_count=1,
            target=target,
        )
        for target in target_names
    }
    comparison_targets = _scripture_comparison_targets(target_names)
    chunk_targets = comparison_targets if any(
        method == "gospelvec_mean" for method in resolved_methods.values()
    ) else list(target_names)
    family_chunks = {
        target: _split_scripture_chunks(
            _chunk_scripture_family_texts(
                tokenizer,
                target=target,
                max_length=max_length,
                psalm_vector_sets=psalm_vector_sets,
            )
        )
        for target in chunk_targets
    }

    family_acts = {
        target: {
            split: _extract_activations(
                model,
                tokenizer,
                family_chunks[target][split],
                layer_indices,
                max_length=max_length,
            )
            for split in ("train", "dev", "test")
        }
        for target in chunk_targets
    }

    midpoint = len(layer_indices) // 2
    payloads = {}

    for target in target_names:
        method_used = resolved_methods[target]
        target_psalm_sets = _scripture_target_psalm_sets(
            target,
            default_psalm_sets=psalm_vector_sets,
        )
        target_psalm_families = parse_psalm_family_target(target)
        if window_center is not None and (window_center < 0 or window_center >= len(layer_indices)):
            raise ValueError(
                f"window_center={window_center} is out of range for {len(layer_indices)} layers"
            )

        if method_used == "gospelvec_mean":
            family_layer_vectors: Dict[int, object] = {}
            layer_scores: Dict[int, float] = {}
            layer_margins: Dict[int, float] = {}
            layer_specificity: Dict[int, float] = {}
            layer_test_accuracy: Dict[int, float] = {}
            layer_test_margin: Dict[int, float] = {}
            layer_test_specificity: Dict[int, float] = {}
            shared_layer_scores: Dict[int, float] = {}
            shared_layer_test_scores: Dict[int, float] = {}
            directions_by_layer: Dict[int, Dict[str, object]] = {}

            for layer in layer_indices:
                neutral_basis = _compute_pca_basis(
                    neutral_acts[layer],
                    variance_threshold=variance_threshold,
                )
                train_matrices = [
                    family_acts[name]["train"][layer]
                    for name in comparison_targets
                    if family_acts[name]["train"][layer].shape[0] > 0
                ]
                global_train = torch.cat(train_matrices, dim=0)

                directions: Dict[str, object] = {}
                for name in comparison_targets:
                    direction = _gospelvec_mean_direction(
                        family_acts[name]["train"][layer],
                        global_train,
                    )
                    direction = _project_out_basis(direction, neutral_basis)
                    directions[name] = _l2_normalize(direction.cpu())

                directions_by_layer[layer] = directions
                family_layer_vectors[layer] = directions[target]

                shared_dev, per_dev_acc, per_dev_margin, per_dev_spec = _family_classification_metrics(
                    directions,
                    {name: family_acts[name]["dev"][layer] for name in comparison_targets},
                )
                shared_test, per_test_acc, per_test_margin, per_test_spec = _family_classification_metrics(
                    directions,
                    {name: family_acts[name]["test"][layer] for name in comparison_targets},
                )
                shared_layer_scores[layer] = shared_dev
                shared_layer_test_scores[layer] = shared_test
                layer_scores[layer] = per_dev_acc[target]
                layer_margins[layer] = per_dev_margin[target]
                layer_specificity[layer] = per_dev_spec[target]
                layer_test_accuracy[layer] = per_test_acc[target]
                layer_test_margin[layer] = per_test_margin[target]
                layer_test_specificity[layer] = per_test_spec[target]

            best_layer, best_layer_selection, layer_candidates, selection_tolerance = _select_scripture_layer(
                target=target,
                layer_scores=layer_scores,
                layer_specificity=layer_specificity,
                layer_margins=layer_margins,
                shared_scores=shared_layer_scores,
                dev_examples=len(family_chunks[target]["dev"]),
                midpoint=midpoint,
                window_center=window_center,
            )
            layer_window = _window_around(best_layer, len(layer_indices), radius=window_radius)
            window_vectors = {layer: family_layer_vectors[layer] for layer in layer_window}
            directions_at_best = directions_by_layer[best_layer]

            alpha_scores: Dict[float, float] = {}
            alpha_margins: Dict[float, float] = {}
            alpha_specificity: Dict[float, float] = {}
            for alpha in alpha_grid:
                runtime = SteeringRuntime(layer_vectors=window_vectors, alpha=alpha)
                steered_dev = _extract_activations(
                    model,
                    tokenizer,
                    family_chunks[target]["dev"],
                    [best_layer],
                    max_length=max_length,
                    steering_runtime=runtime,
                )[best_layer]
                accuracy, margin, specificity = _scripture_target_metrics(
                    target=target,
                    directions=directions_at_best,
                    matrix=steered_dev,
                )
                alpha_scores[alpha] = accuracy
                alpha_margins[alpha] = margin
                alpha_specificity[alpha] = specificity

            best_alpha, alpha_selection, alpha_candidates, alpha_tolerance = _select_scripture_alpha(
                alpha_scores=alpha_scores,
                alpha_specificity=alpha_specificity,
                alpha_margins=alpha_margins,
                dev_examples=len(family_chunks[target]["dev"]),
            )
            runtime = SteeringRuntime(layer_vectors=window_vectors, alpha=best_alpha)
            steered_test = _extract_activations(
                model,
                tokenizer,
                family_chunks[target]["test"],
                [best_layer],
                max_length=max_length,
                steering_runtime=runtime,
            )[best_layer]
            steered_accuracy, steered_margin, steered_specificity = _scripture_target_metrics(
                target=target,
                directions=directions_at_best,
                matrix=steered_test,
            )

            payloads[target] = {
                "extraction_method_requested": extraction_method_requested,
                "extraction_method_used": method_used,
                "source_mode": (
                    "whole_text_psalm_family_within_scripture_space"
                    if target_psalm_families is not None
                    else "whole_text_scripture_within_scripture_space"
                ),
                "best_layer": best_layer,
                "best_layer_selection": best_layer_selection,
                "layer_selection_candidates": layer_candidates,
                "layer_window": layer_window,
                "alpha": best_alpha,
                "alpha_selection": alpha_selection,
                "alpha_selection_candidates": alpha_candidates,
                "selection_accuracy_tolerance": selection_tolerance,
                "alpha_selection_tolerance": alpha_tolerance,
                "shared_family_dev_accuracy": shared_layer_scores[best_layer],
                "shared_family_test_accuracy": shared_layer_test_scores[best_layer],
                "layer_scores": {str(layer): score for layer, score in shared_layer_scores.items()},
                "layer_margins": {str(layer): margin for layer, margin in layer_margins.items()},
                "layer_specificity": {str(layer): score for layer, score in layer_specificity.items()},
                "dev_accuracy": layer_scores[best_layer],
                "dev_margin": layer_margins[best_layer],
                "dev_specificity": layer_specificity[best_layer],
                "dev_pair_accuracy": None,
                "steered_dev_accuracy": alpha_scores[best_alpha],
                "steered_dev_margin": alpha_margins[best_alpha],
                "steered_dev_specificity": alpha_specificity[best_alpha],
                "alpha_scores": {str(alpha): score for alpha, score in alpha_scores.items()},
                "alpha_margins": {str(alpha): margin for alpha, margin in alpha_margins.items()},
                "alpha_specificity": {str(alpha): score for alpha, score in alpha_specificity.items()},
                "test_accuracy": layer_test_accuracy[best_layer],
                "test_margin": layer_test_margin[best_layer],
                "test_specificity": layer_test_specificity[best_layer],
                "test_pair_accuracy": None,
                "test_accuracy_steered": steered_accuracy,
                "test_specificity_steered": steered_specificity,
                "train_examples": len(family_chunks[target]["train"]),
                "dev_examples": len(family_chunks[target]["dev"]),
                "test_examples": len(family_chunks[target]["test"]),
                "other_train_examples": sum(
                    len(family_chunks[name]["train"]) for name in comparison_targets if name != target
                ),
                "other_dev_examples": sum(
                    len(family_chunks[name]["dev"]) for name in comparison_targets if name != target
                ),
                "other_test_examples": sum(
                    len(family_chunks[name]["test"]) for name in comparison_targets if name != target
                ),
                "train_pairs": 0,
                "dev_pairs": 0,
                "test_pairs": 0,
                "steered_test_margin": steered_margin,
                "comparison_families": comparison_targets,
                "background_mode": "scripture_space",
                "psalm_vector_sets": target_psalm_sets,
                "psalm_families": target_psalm_families,
                "scripture_chunk_counts": {
                    split: len(family_chunks[target][split]) for split in ("train", "dev", "test")
                },
                "layer_vectors": {
                    str(layer): vector.cpu() for layer, vector in window_vectors.items()
                },
                "null_vectors": {
                    str(layer): vector.cpu()
                    for layer, vector in _build_null_vectors(window_vectors, seed=best_layer + len(target)).items()
                },
            }
            continue

        layer_vectors: Dict[int, object] = {}
        layer_scores: Dict[int, float] = {}
        layer_margins: Dict[int, float] = {}
        layer_specificity: Dict[int, float] = {}
        layer_pair_scores: Dict[int, Optional[float]] = {}
        layer_test_accuracy: Dict[int, float] = {}
        layer_test_margin: Dict[int, float] = {}
        layer_test_pair_accuracy: Dict[int, Optional[float]] = {}

        for layer in layer_indices:
            neutral_basis = _compute_pca_basis(
                neutral_acts[layer],
                variance_threshold=variance_threshold,
            )
            direction = _scripture_contrast_direction(
                family_acts[target]["train"][layer],
                neutral_split_acts["train"][layer],
            )
            direction = _project_out_basis(direction, neutral_basis)
            direction = _l2_normalize(direction.cpu())
            layer_vectors[layer] = direction

            dev_accuracy, dev_margin, dev_pair_accuracy = _scripture_contrast_metrics(
                direction,
                family_acts[target]["dev"][layer],
                neutral_split_acts["dev"][layer],
            )
            test_accuracy, test_margin, test_pair_accuracy = _scripture_contrast_metrics(
                direction,
                family_acts[target]["test"][layer],
                neutral_split_acts["test"][layer],
            )
            layer_scores[layer] = dev_accuracy
            layer_margins[layer] = dev_margin
            layer_specificity[layer] = dev_margin
            layer_pair_scores[layer] = dev_pair_accuracy
            layer_test_accuracy[layer] = test_accuracy
            layer_test_margin[layer] = test_margin
            layer_test_pair_accuracy[layer] = test_pair_accuracy

        selection_tolerance = _accuracy_tolerance(
            len(family_chunks[target]["dev"]),
            len(neutral_text_splits["dev"]),
        )
        if window_center is not None:
            best_layer = window_center
            best_layer_selection = "fixed"
            layer_candidates = [window_center]
        else:
            best_layer, best_layer_selection, layer_candidates = _select_layer(
                method_used="specific_mean_centered",
                layer_scores=layer_scores,
                layer_pair_scores=layer_pair_scores,
                layer_specificity=layer_specificity,
                layer_margins=layer_margins,
                midpoint=midpoint,
                tolerance=selection_tolerance,
            )
        layer_window = _window_around(best_layer, len(layer_indices), radius=window_radius)
        window_vectors = {layer: layer_vectors[layer] for layer in layer_window}

        alpha_scores: Dict[float, float] = {}
        alpha_margins: Dict[float, float] = {}
        alpha_specificity: Dict[float, float] = {}
        for alpha in alpha_grid:
            runtime = SteeringRuntime(layer_vectors=window_vectors, alpha=alpha)
            steered_dev = _extract_activations(
                model,
                tokenizer,
                family_chunks[target]["dev"],
                [best_layer],
                max_length=max_length,
                steering_runtime=runtime,
            )[best_layer]
            accuracy, margin, _ = _scripture_contrast_metrics(
                layer_vectors[best_layer],
                steered_dev,
                neutral_split_acts["dev"][best_layer],
            )
            alpha_scores[alpha] = accuracy
            alpha_margins[alpha] = margin
            alpha_specificity[alpha] = margin

        alpha_tolerance = _accuracy_tolerance(
            len(family_chunks[target]["dev"]),
            len(neutral_text_splits["dev"]),
        )
        best_alpha, alpha_selection, alpha_candidates = _select_alpha(
            method_used="specific_mean_centered",
            alpha_scores=alpha_scores,
            alpha_specificity=alpha_specificity,
            alpha_margins=alpha_margins,
            tolerance=alpha_tolerance,
        )
        runtime = SteeringRuntime(layer_vectors=window_vectors, alpha=best_alpha)
        steered_test = _extract_activations(
            model,
            tokenizer,
            family_chunks[target]["test"],
            [best_layer],
            max_length=max_length,
            steering_runtime=runtime,
        )[best_layer]
        steered_test_accuracy, steered_test_margin, steered_test_pair = _scripture_contrast_metrics(
            layer_vectors[best_layer],
            steered_test,
            neutral_split_acts["test"][best_layer],
        )

        payloads[target] = {
            "extraction_method_requested": extraction_method_requested,
            "extraction_method_used": method_used,
            "source_mode": (
                "whole_text_psalm_family_vs_generic"
                if target_psalm_families is not None
                else "whole_text_scripture_vs_generic"
            ),
            "best_layer": best_layer,
            "best_layer_selection": best_layer_selection,
            "layer_selection_candidates": layer_candidates,
            "layer_window": layer_window,
            "alpha": best_alpha,
            "alpha_selection": alpha_selection,
            "alpha_selection_candidates": alpha_candidates,
            "selection_accuracy_tolerance": selection_tolerance,
            "alpha_selection_tolerance": alpha_tolerance,
            "shared_family_dev_accuracy": None,
            "shared_family_test_accuracy": None,
            "layer_scores": {str(layer): score for layer, score in layer_scores.items()},
            "layer_margins": {str(layer): margin for layer, margin in layer_margins.items()},
            "layer_specificity": {str(layer): score for layer, score in layer_specificity.items()},
            "dev_accuracy": layer_scores[best_layer],
            "dev_margin": layer_margins[best_layer],
            "dev_specificity": layer_specificity[best_layer],
            "dev_pair_accuracy": layer_pair_scores[best_layer],
            "steered_dev_accuracy": alpha_scores[best_alpha],
            "steered_dev_margin": alpha_margins[best_alpha],
            "steered_dev_specificity": alpha_specificity[best_alpha],
            "alpha_scores": {str(alpha): score for alpha, score in alpha_scores.items()},
            "alpha_margins": {str(alpha): margin for alpha, margin in alpha_margins.items()},
            "alpha_specificity": {str(alpha): score for alpha, score in alpha_specificity.items()},
            "test_accuracy": layer_test_accuracy[best_layer],
            "test_margin": layer_test_margin[best_layer],
            "test_specificity": layer_test_margin[best_layer],
            "test_pair_accuracy": layer_test_pair_accuracy[best_layer],
            "test_accuracy_steered": steered_test_accuracy,
            "test_specificity_steered": steered_test_margin,
            "train_examples": len(family_chunks[target]["train"]),
            "dev_examples": len(family_chunks[target]["dev"]),
            "test_examples": len(family_chunks[target]["test"]),
            "other_train_examples": len(neutral_text_splits["train"]),
            "other_dev_examples": len(neutral_text_splits["dev"]),
            "other_test_examples": len(neutral_text_splits["test"]),
            "train_pairs": 0,
            "dev_pairs": 0,
            "test_pairs": 0,
            "steered_test_margin": steered_test_margin,
            "comparison_families": None,
            "background_mode": "generic_non_scripture",
            "psalm_vector_sets": target_psalm_sets,
            "psalm_families": target_psalm_families,
            "scripture_chunk_counts": {
                split: len(family_chunks[target][split]) for split in ("train", "dev", "test")
            },
            "neutral_chunk_counts": {
                split: len(neutral_text_splits[split]) for split in ("train", "dev", "test")
            },
            "layer_vectors": {
                str(layer): vector.cpu() for layer, vector in window_vectors.items()
            },
            "null_vectors": {
                str(layer): vector.cpu()
                for layer, vector in _build_null_vectors(window_vectors, seed=best_layer + len(target)).items()
            },
        }

    return payloads


def extract_virtue_vectors(
    runner,
    *,
    corpus_path: Optional[Path] = None,
    targets: Optional[List[str]] = None,
    alpha_candidates: Optional[List[float]] = None,
    extraction_method: str = "auto",
    max_length: int = 256,
    window_radius: int = 3,
    window_center: Optional[int] = None,
    variance_threshold: float = 0.5,
    specificity_variance_threshold: float = 0.35,
    min_passage_words: int = 40,
    max_texts_per_passage: int = 3,
    psalm_vector_sets: Optional[List[str]] = None,
) -> dict:
    """Extract per-target steering vectors from the bundled contrastive corpus."""
    _require_torch()
    model, tokenizer = runner.get_model_and_tokenizer()
    layers = get_decoder_layers(model)
    layer_indices = list(range(len(layers)))
    records = load_steering_corpus(corpus_path)
    target_names = list(targets or list_steering_targets(records) or DEFAULT_VIRTUE_TARGETS)
    alpha_grid = alpha_candidates or list(DEFAULT_ALPHA_CANDIDATES)
    pooled_members = pooled_virtue_members(records)

    neutral_text_splits = _neutral_passage_splits(
        records,
        min_words=min_passage_words,
        max_items=max_texts_per_passage,
    )
    neutral_acts_by_split = {
        split: _extract_activations(
            model,
            tokenizer,
            neutral_text_splits[split],
            layer_indices,
            max_length=max_length,
        )
        for split in ("train", "dev", "test")
    }
    neutral_acts = neutral_acts_by_split["train"]

    payload = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": runner.model_id(),
        "corpus_path": str(corpus_path or CORPUS_FILE),
        "extraction_method": extraction_method,
        "targets": target_names,
        "alpha_candidates": alpha_grid,
        "window_radius": window_radius,
        "window_center": window_center,
        "min_passage_words": min_passage_words,
        "max_texts_per_passage": max_texts_per_passage,
        "psalm_vector_sets": psalm_vector_sets,
        "virtues": {},
    }

    scripture_targets = [target for target in target_names if _is_scripture_target_name(target)]
    if scripture_targets:
        payload["virtues"].update(
            _extract_scripture_family_payloads(
                model,
                tokenizer,
                layer_indices,
                scripture_targets,
                neutral_acts,
                neutral_acts_by_split,
                neutral_text_splits=neutral_text_splits,
                extraction_method_requested=extraction_method,
                max_length=max_length,
                alpha_grid=alpha_grid,
                window_radius=window_radius,
                window_center=window_center,
                variance_threshold=variance_threshold,
                psalm_vector_sets=psalm_vector_sets,
            )
        )

    for virtue in target_names:
        if _is_scripture_target_name(virtue):
            continue
        source_virtues = pooled_members if virtue == POOLED_VIRTUE_TARGET else [virtue]
        pos_train = _passage_windows(
            _texts_for_virtues(records, source_virtues, "positive", "train"),
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        neg_train = _passage_windows(
            _texts_for_virtues(records, source_virtues, "negative", "train"),
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        pos_dev = _passage_windows(
            _texts_for_virtues(records, source_virtues, "positive", "dev"),
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        neg_dev = _passage_windows(
            _texts_for_virtues(records, source_virtues, "negative", "dev"),
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        pos_test = _passage_windows(
            _texts_for_virtues(records, source_virtues, "positive", "test"),
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        neg_test = _passage_windows(
            _texts_for_virtues(records, source_virtues, "negative", "test"),
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        if virtue == POOLED_VIRTUE_TARGET:
            other_pos_train = []
            other_pos_dev = []
            other_pos_test = []
            train_pairs = _pooled_virtue_pairs(records, source_virtues, "train")
            dev_pairs = _pooled_virtue_pairs(records, source_virtues, "dev")
            test_pairs = _pooled_virtue_pairs(records, source_virtues, "test")
        else:
            other_pos_train = _other_virtue_positive_texts(records, virtue, "train")
            other_pos_dev = _other_virtue_positive_texts(records, virtue, "dev")
            other_pos_test = _other_virtue_positive_texts(records, virtue, "test")
            train_pairs = build_contrast_pairs(records, virtue=virtue, split="train")
            dev_pairs = build_contrast_pairs(records, virtue=virtue, split="dev")
            test_pairs = build_contrast_pairs(records, virtue=virtue, split="test")
        train_pair_pos_texts, train_pair_neg_texts = _pair_passage_windows(
            train_pairs,
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        dev_pair_pos_texts, dev_pair_neg_texts = _pair_passage_windows(
            dev_pairs,
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )
        test_pair_pos_texts, test_pair_neg_texts = _pair_passage_windows(
            test_pairs,
            min_words=min_passage_words,
            max_items=max_texts_per_passage,
        )

        train_pos_acts = _extract_activations(model, tokenizer, pos_train, layer_indices, max_length=max_length)
        train_neg_acts = _extract_activations(model, tokenizer, neg_train, layer_indices, max_length=max_length)
        dev_pos_acts = _extract_activations(model, tokenizer, pos_dev, layer_indices, max_length=max_length)
        dev_neg_acts = _extract_activations(model, tokenizer, neg_dev, layer_indices, max_length=max_length)
        test_pos_acts = _extract_activations(model, tokenizer, pos_test, layer_indices, max_length=max_length)
        test_neg_acts = _extract_activations(model, tokenizer, neg_test, layer_indices, max_length=max_length)
        other_train_pos_acts = _extract_activations(model, tokenizer, other_pos_train, layer_indices, max_length=max_length)
        other_dev_pos_acts = _extract_activations(model, tokenizer, other_pos_dev, layer_indices, max_length=max_length)
        other_test_pos_acts = _extract_activations(model, tokenizer, other_pos_test, layer_indices, max_length=max_length)
        train_pair_pos_acts = _extract_activations(
            model,
            tokenizer,
            train_pair_pos_texts,
            layer_indices,
            max_length=max_length,
        )
        train_pair_neg_acts = _extract_activations(
            model,
            tokenizer,
            train_pair_neg_texts,
            layer_indices,
            max_length=max_length,
        )
        dev_pair_pos_acts = _extract_activations(
            model,
            tokenizer,
            dev_pair_pos_texts,
            layer_indices,
            max_length=max_length,
        )
        dev_pair_neg_acts = _extract_activations(
            model,
            tokenizer,
            dev_pair_neg_texts,
            layer_indices,
            max_length=max_length,
        )
        test_pair_pos_acts = _extract_activations(
            model,
            tokenizer,
            test_pair_pos_texts,
            layer_indices,
            max_length=max_length,
        )
        test_pair_neg_acts = _extract_activations(
            model,
            tokenizer,
            test_pair_neg_texts,
            layer_indices,
            max_length=max_length,
        )

        layer_vectors: Dict[int, object] = {}
        layer_scores: Dict[int, float] = {}
        layer_margins: Dict[int, float] = {}
        layer_pair_scores: Dict[int, Optional[float]] = {}
        layer_specificity: Dict[int, float] = {}
        bases: Dict[int, object] = {}
        method_used = _resolve_extraction_method(
            extraction_method,
            pair_count=len(train_pairs),
            target=virtue,
        )
        selection_tolerance = _accuracy_tolerance(len(pos_dev), len(neg_dev))

        for layer in layer_indices:
            neutral_basis = _compute_pca_basis(neutral_acts[layer], variance_threshold=variance_threshold)
            specificity_basis = None
            if method_used.startswith("specific_"):
                specificity_basis = _compute_pca_basis(
                    other_train_pos_acts[layer],
                    variance_threshold=specificity_variance_threshold,
                )
            basis = _combine_bases(neutral_basis, specificity_basis)
            bases[layer] = basis
            mean_diff = _mean_difference_direction(train_pos_acts[layer], train_neg_acts[layer])

            if method_used in {"pca_pairwise", "specific_pca_pairwise"}:
                direction = _pca_pairwise_direction(train_pair_pos_acts[layer], train_pair_neg_acts[layer])
            elif method_used == "specific_mean_centered":
                direction = _specific_mean_centered_direction(
                    train_pos_acts[layer],
                    train_neg_acts[layer],
                    neutral_acts[layer],
                    other_train_pos_acts[layer],
                )
            elif method_used == "mean_centered":
                direction = _mean_centered_direction(
                    train_pos_acts[layer],
                    train_neg_acts[layer],
                    neutral_acts[layer],
                )
            else:
                direction = mean_diff

            direction = _align_direction(direction, mean_diff)
            direction = _project_out_basis(direction, basis)
            direction = _l2_normalize(direction.cpu())
            layer_vectors[layer] = direction
            layer_scores[layer] = _binary_accuracy(direction, dev_pos_acts[layer], dev_neg_acts[layer])
            layer_margins[layer] = _binary_margin(direction, dev_pos_acts[layer], dev_neg_acts[layer])
            layer_pair_scores[layer] = _pairwise_accuracy(direction, dev_pair_pos_acts[layer], dev_pair_neg_acts[layer])
            layer_specificity[layer] = _specificity_margin(
                direction,
                dev_pos_acts[layer],
                other_dev_pos_acts[layer],
            )

        if window_center is not None:
            if window_center < 0 or window_center >= len(layer_indices):
                raise ValueError(
                    f"window_center={window_center} is out of range for {len(layer_indices)} layers"
                )
            best_layer = window_center
            best_layer_selection = "fixed"
            layer_candidates = [best_layer]
        else:
            midpoint = len(layer_indices) // 2
            best_layer, best_layer_selection, layer_candidates = _select_layer(
                method_used=method_used,
                layer_scores=layer_scores,
                layer_pair_scores=layer_pair_scores,
                layer_specificity=layer_specificity,
                layer_margins=layer_margins,
                midpoint=midpoint,
                tolerance=selection_tolerance,
            )
        layer_window = _window_around(best_layer, len(layer_indices), radius=window_radius)
        window_vectors = {layer: layer_vectors[layer] for layer in layer_window}

        alpha_scores: Dict[float, float] = {}
        alpha_margins: Dict[float, float] = {}
        alpha_specificity: Dict[float, float] = {}
        for alpha in alpha_grid:
            runtime = SteeringRuntime(layer_vectors=window_vectors, alpha=alpha)
            steered_pos = _extract_activations(
                model, tokenizer, pos_dev, [best_layer], max_length=max_length, steering_runtime=runtime,
            )[best_layer]
            steered_neg = _extract_activations(
                model, tokenizer, neg_dev, [best_layer], max_length=max_length, steering_runtime=runtime,
            )[best_layer]
            steered_other = _extract_activations(
                model,
                tokenizer,
                other_pos_dev,
                [best_layer],
                max_length=max_length,
                steering_runtime=runtime,
            )[best_layer]
            alpha_scores[alpha] = _binary_accuracy(layer_vectors[best_layer], steered_pos, steered_neg)
            alpha_margins[alpha] = _binary_margin(layer_vectors[best_layer], steered_pos, steered_neg)
            alpha_specificity[alpha] = _specificity_margin(layer_vectors[best_layer], steered_pos, steered_other)

        best_alpha, alpha_selection, alpha_candidates = _select_alpha(
            method_used=method_used,
            alpha_scores=alpha_scores,
            alpha_specificity=alpha_specificity,
            alpha_margins=alpha_margins,
            tolerance=selection_tolerance,
        )
        best_runtime = SteeringRuntime(layer_vectors=window_vectors, alpha=best_alpha)
        steered_test_pos = _extract_activations(
            model, tokenizer, pos_test, [best_layer], max_length=max_length, steering_runtime=best_runtime,
        )[best_layer]
        steered_test_neg = _extract_activations(
            model, tokenizer, neg_test, [best_layer], max_length=max_length, steering_runtime=best_runtime,
        )[best_layer]
        steered_test_other = _extract_activations(
            model,
            tokenizer,
            other_pos_test,
            [best_layer],
            max_length=max_length,
            steering_runtime=best_runtime,
        )[best_layer]

        payload["virtues"][virtue] = {
            "extraction_method_requested": extraction_method,
            "extraction_method_used": method_used,
            "source_mode": "pooled_virtue_corpus" if virtue == POOLED_VIRTUE_TARGET else "virtue_corpus",
            "source_virtues": source_virtues if virtue == POOLED_VIRTUE_TARGET else None,
            "best_layer": best_layer,
            "best_layer_selection": best_layer_selection,
            "layer_selection_candidates": layer_candidates,
            "layer_window": layer_window,
            "alpha": best_alpha,
            "alpha_selection": alpha_selection,
            "alpha_selection_candidates": alpha_candidates,
            "selection_accuracy_tolerance": selection_tolerance,
            "layer_scores": {str(layer): score for layer, score in layer_scores.items()},
            "layer_margins": {str(layer): margin for layer, margin in layer_margins.items()},
            "layer_specificity": {str(layer): score for layer, score in layer_specificity.items()},
            "layer_pair_scores": {
                str(layer): score
                for layer, score in layer_pair_scores.items()
                if score is not None
            },
            "alpha_scores": {str(alpha): score for alpha, score in alpha_scores.items()},
            "alpha_margins": {str(alpha): margin for alpha, margin in alpha_margins.items()},
            "alpha_specificity": {str(alpha): score for alpha, score in alpha_specificity.items()},
            "dev_accuracy": layer_scores[best_layer],
            "dev_margin": layer_margins[best_layer],
            "dev_specificity": layer_specificity[best_layer],
            "dev_pair_accuracy": layer_pair_scores[best_layer],
            "test_accuracy": _binary_accuracy(layer_vectors[best_layer], test_pos_acts[best_layer], test_neg_acts[best_layer]),
            "test_margin": _binary_margin(layer_vectors[best_layer], test_pos_acts[best_layer], test_neg_acts[best_layer]),
            "test_specificity": _specificity_margin(
                layer_vectors[best_layer],
                test_pos_acts[best_layer],
                other_test_pos_acts[best_layer],
            ),
            "test_pair_accuracy": _pairwise_accuracy(
                layer_vectors[best_layer],
                test_pair_pos_acts[best_layer],
                test_pair_neg_acts[best_layer],
            ),
            "test_accuracy_steered": _binary_accuracy(layer_vectors[best_layer], steered_test_pos, steered_test_neg),
            "test_specificity_steered": _specificity_margin(
                layer_vectors[best_layer],
                steered_test_pos,
                steered_test_other,
            ),
            "train_examples": len(pos_train) + len(neg_train),
            "dev_examples": len(pos_dev) + len(neg_dev),
            "test_examples": len(pos_test) + len(neg_test),
            "other_train_examples": len(other_pos_train),
            "other_dev_examples": len(other_pos_dev),
            "other_test_examples": len(other_pos_test),
            "train_pairs": len(train_pairs),
            "dev_pairs": len(dev_pairs),
            "test_pairs": len(test_pairs),
            "layer_vectors": {str(layer): vector.cpu() for layer, vector in window_vectors.items()},
            "null_vectors": {
                str(layer): vector.cpu()
                for layer, vector in _build_null_vectors(window_vectors, seed=best_layer + len(virtue)).items()
            },
        }

    return payload


def save_vector_artifact(artifact: dict, output_path: Path) -> Path:
    """Persist a vector artifact to disk."""
    _require_torch()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(artifact, output_path)
    return output_path


def load_vector_artifact(path: Path) -> dict:
    """Load a previously extracted vector artifact."""
    _require_torch()
    return torch.load(path, map_location="cpu")
