"""Helpers for Psalm-family screening summaries and reasoning review packs."""

from __future__ import annotations

import json
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ..artifacts.results import load_results
from ..core.psalms import parse_psalm_family_target
from ..core.schema import RunResult
from .iconoclast import compare_paired_results, condition_target


def load_run_results(path: Path) -> List[RunResult]:
    return [RunResult(**row) for row in load_results(path)]


def load_vector_diagnostics(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _paired_control_runs(
    results: Iterable[RunResult],
    candidate_condition: str,
) -> List[Tuple[RunResult, RunResult]]:
    controls: Dict[Tuple[str, str, str, int], RunResult] = {}
    candidates: List[Tuple[RunResult, RunResult]] = []
    for result in results:
        key = (result.virtue, result.variant, result.frame, result.run_index)
        if result.condition == "control":
            controls[key] = result
    for result in results:
        if result.condition != candidate_condition:
            continue
        key = (result.virtue, result.variant, result.frame, result.run_index)
        control = controls.get(key)
        if control is not None:
            candidates.append((control, result))
    return candidates


def _accuracy_from_samples(sample_results) -> Optional[float]:
    scored = [sample for sample in sample_results if sample.correct is not None]
    if not scored:
        return None
    correct = sum(1 for sample in scored if sample.correct)
    return correct / len(scored)


def _diagnostics_lookup(diagnostics: dict) -> Dict[str, dict]:
    return {
        summary["target"]: summary
        for summary in diagnostics.get("target_summaries", [])
        if isinstance(summary, dict) and "target" in summary
    }


def summarize_psalm_lane(
    results: Iterable[RunResult],
    *,
    candidate_condition: str,
    diagnostics: Optional[dict] = None,
) -> dict:
    pairs = _paired_control_runs(results, candidate_condition)
    candidate_target = condition_target(candidate_condition) or candidate_condition
    diagnostics_summary = _diagnostics_lookup(diagnostics or {}).get(candidate_target, {})

    per_virtue_control_correct = defaultdict(int)
    per_virtue_control_total = defaultdict(int)
    per_virtue_candidate_correct = defaultdict(int)
    per_virtue_candidate_total = defaultdict(int)
    answer_changes = 0
    improvements = 0
    regressions = 0

    all_control_samples = []
    all_candidate_samples = []
    first_metadata = None

    for control, candidate in pairs:
        first_metadata = first_metadata or candidate.metadata
        stats = compare_paired_results(control, candidate)
        answer_changes += stats["answer_changes"]
        improvements += stats["improve"]
        regressions += stats["regress"]

        for control_sample, candidate_sample in zip(control.sample_details, candidate.sample_details):
            if control_sample.correct is not None:
                per_virtue_control_total[control.virtue] += 1
                per_virtue_control_correct[control.virtue] += int(bool(control_sample.correct))
                all_control_samples.append(control_sample)
            if candidate_sample.correct is not None:
                per_virtue_candidate_total[candidate.virtue] += 1
                per_virtue_candidate_correct[candidate.virtue] += int(bool(candidate_sample.correct))
                all_candidate_samples.append(candidate_sample)

    per_virtue_delta = {}
    for virtue in sorted(set(per_virtue_control_total) | set(per_virtue_candidate_total)):
        control_total = per_virtue_control_total.get(virtue, 0)
        candidate_total = per_virtue_candidate_total.get(virtue, 0)
        if control_total <= 0 or candidate_total <= 0:
            per_virtue_delta[virtue] = None
            continue
        control_accuracy = per_virtue_control_correct[virtue] / control_total
        candidate_accuracy = per_virtue_candidate_correct[virtue] / candidate_total
        per_virtue_delta[virtue] = candidate_accuracy - control_accuracy

    control_accuracy = _accuracy_from_samples(all_control_samples)
    candidate_accuracy = _accuracy_from_samples(all_candidate_samples)
    delta_vs_control = None
    if control_accuracy is not None and candidate_accuracy is not None:
        delta_vs_control = candidate_accuracy - control_accuracy

    psalm_families = parse_psalm_family_target(candidate_target)
    return {
        "condition": candidate_condition,
        "target": candidate_target,
        "psalm_families": psalm_families,
        "family_label": "+".join(psalm_families) if psalm_families else candidate_target,
        "alpha_scale": (first_metadata or {}).get("alpha_scale_applied"),
        "vector_alpha": (first_metadata or {}).get("vector_alpha"),
        "artifact_alpha": (first_metadata or {}).get("artifact_alpha"),
        "control_accuracy": control_accuracy,
        "candidate_accuracy": candidate_accuracy,
        "delta_vs_control": delta_vs_control,
        "per_virtue_delta": per_virtue_delta,
        "answer_changes": answer_changes,
        "improvements": improvements,
        "regressions": regressions,
        "diagnostics": {
            "best_layer": diagnostics_summary.get("best_layer"),
            "layer_window": diagnostics_summary.get("layer_window"),
            "alpha": diagnostics_summary.get("alpha"),
            "steered_test_margin": diagnostics_summary.get("steered_test_margin"),
        },
    }


def representative_scale_key(summary: dict) -> tuple:
    delta = summary.get("delta_vs_control")
    if delta is None:
        delta = float("-inf")
    steered_margin = summary.get("diagnostics", {}).get("steered_test_margin")
    if steered_margin is None:
        steered_margin = float("-inf")
    return (
        float(delta),
        -int(summary.get("regressions", 0)),
        int(summary.get("improvements", 0)),
        float(steered_margin),
    )


def choose_representative_scale(summaries: List[dict]) -> Optional[dict]:
    if not summaries:
        return None
    return max(summaries, key=representative_scale_key)


def build_reasoning_review_pack(
    results: Iterable[RunResult],
    *,
    candidate_condition: str,
    same_answer_limit: int = 8,
) -> dict:
    pairs = _paired_control_runs(results, candidate_condition)
    changed_cases: List[dict] = []
    same_answer_candidates: List[dict] = []

    for control, candidate in pairs:
        for control_sample, candidate_sample in zip(control.sample_details, candidate.sample_details):
            if (
                control_sample.sample_id != candidate_sample.sample_id
                or control_sample.target != candidate_sample.target
            ):
                continue
            entry = {
                "virtue": control.virtue,
                "variant": control.variant,
                "sample_id": control_sample.sample_id,
                "target": control_sample.target,
                "control_answer": control_sample.model_answer,
                "candidate_answer": candidate_sample.model_answer,
                "control_correct": control_sample.correct,
                "candidate_correct": candidate_sample.correct,
                "control_response": control_sample.model_response,
                "candidate_response": candidate_sample.model_response,
            }
            if (
                control_sample.model_answer != candidate_sample.model_answer
                or control_sample.correct != candidate_sample.correct
            ):
                changed_cases.append(entry)
                continue
            if control_sample.model_response.strip() == candidate_sample.model_response.strip():
                continue
            shift_score = 1.0 - SequenceMatcher(
                None,
                control_sample.model_response.strip(),
                candidate_sample.model_response.strip(),
            ).ratio()
            entry["rationale_shift_score"] = shift_score
            same_answer_candidates.append(entry)

    same_answer_candidates.sort(
        key=lambda entry: (entry["rationale_shift_score"], entry["sample_id"]),
        reverse=True,
    )
    return {
        "condition": candidate_condition,
        "changed_cases": changed_cases,
        "same_answer_candidates": same_answer_candidates[:same_answer_limit],
    }
