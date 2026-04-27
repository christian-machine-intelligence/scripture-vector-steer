import json
import os
import sys
import types
from pathlib import Path

import virtue_bench.cli as cli_module
from virtue_bench.steering.corpora import load_steering_corpus

fake_eval_package = types.ModuleType("virtue_bench.eval")
fake_eval_package.__path__ = []  # type: ignore[attr-defined]
fake_eval_experiment = types.ModuleType("virtue_bench.eval.experiment")
fake_eval_experiment.RESULTS_DIR = Path("/tmp")


async def _unused_run_single_condition(*args, **kwargs):
    raise NotImplementedError


fake_eval_experiment.run_single_condition = _unused_run_single_condition
fake_eval_package.experiment = fake_eval_experiment
sys.modules.setdefault("virtue_bench.eval", fake_eval_package)
sys.modules.setdefault("virtue_bench.eval.experiment", fake_eval_experiment)

from virtue_bench.steering.experiment import (
    IconoclastConfig,
    _artifact_to_runtime,
    _condition_alpha_scale,
    _planned_stage_runs,
    _preflight_failure_keys,
    _preflight_families,
    _requested_vector_targets,
    _run_artifact_paths,
    _steering_targets,
    _vector_diagnostics_payload,
    _write_preflight_payload,
    _write_run_status,
)
from virtue_bench.steering.runtime import SubspaceSteeringRuntime


def test_christian_steering_targets_route_to_fixed_target():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "virtue_steer", "christian_steer", "scripture_steer"],
    )

    assert _steering_targets(config, "smoke", "prudence", "virtue_steer") == ["prudence"]
    assert _steering_targets(config, "smoke", "prudence", "christian_steer") == ["christian"]
    assert _steering_targets(config, "smoke", "prudence", "scripture_steer") == ["psalms", "proverbs", "gospels"]


def test_pooled_virtue_steering_targets_route_to_single_target():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "virtue_steer", "scripture_steer"],
        pooled_virtue_steer=True,
    )

    assert _steering_targets(config, "smoke", "prudence", "virtue_steer") == ["virtues"]
    assert _steering_targets(config, "ratio", "justice", "virtue_steer") == ["virtues"]


def test_condition_alpha_scale_routes_by_steering_family():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        virtue_alpha_scale=1.25,
        christian_alpha_scale=1.5,
        scripture_alpha_scale=2.0,
    )

    assert _condition_alpha_scale(config, "control") == 1.0
    assert _condition_alpha_scale(config, "virtue_steer") == 1.25
    assert _condition_alpha_scale(config, "null_control") == 1.25
    assert _condition_alpha_scale(config, "christian_steer") == 1.5
    assert _condition_alpha_scale(config, "scripture_steer") == 2.0
    assert _condition_alpha_scale(config, "scripture_negative_alpha") == 2.0
    assert _condition_alpha_scale(config, "scripture_null_control") == 2.0


def test_psalm_family_alpha_scale_only_applies_to_matching_lane():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        scripture_targets=[],
        psalm_family_lanes=["trust", "wisdom"],
        scripture_alpha_scale=1.0,
        psalm_family_alpha_scales={"trust": 1.5},
        merged_psalm_family_alpha_scale=2.5,
        include_merged_psalm_family_lane=True,
    )

    assert _condition_alpha_scale(config, "scripture_steer", "psalms[trust]") == 1.5
    assert _condition_alpha_scale(config, "scripture_steer", "psalms[wisdom]") == 1.0
    assert _condition_alpha_scale(config, "scripture_steer", "psalms[trust+wisdom]") == 2.5
    assert _condition_alpha_scale(config, "scripture_steer", "proverbs") == 1.0


def test_requested_vector_targets_include_christian_when_needed():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "virtue_steer", "christian_steer", "scripture_steer"],
    )

    targets = _requested_vector_targets(config, load_steering_corpus())

    assert targets == [
        "prudence",
        "justice",
        "courage",
        "temperance",
        "christian",
        "psalms",
        "proverbs",
        "gospels",
    ]


def test_requested_vector_targets_use_pooled_virtue_when_requested():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "virtue_steer", "scripture_steer"],
        pooled_virtue_steer=True,
        scripture_targets=["psalms"],
    )

    targets = _requested_vector_targets(config, load_steering_corpus())

    assert targets == ["virtues", "psalms"]


def test_requested_vector_targets_stay_scripture_only_when_virtues_are_not_requested():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "scripture_steer", "scripture_null_control"],
    )

    targets = _requested_vector_targets(config, load_steering_corpus())

    assert targets == ["psalms", "proverbs", "gospels"]


def test_requested_vector_targets_include_explicit_book_lanes_without_corpus_pairs():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "scripture_steer"],
        scripture_targets=["psalms", "proverbs", "romans", "petrine"],
    )

    targets = _requested_vector_targets(config, load_steering_corpus())

    assert targets == ["psalms", "proverbs", "romans", "petrine"]


def test_requested_vector_targets_include_external_scripture_target_names():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "scripture_steer"],
        scripture_targets=["prudence_scripture", "justice_scripture"],
        external_scripture_corpus_path="lex-corpora.jsonl",
    )

    targets = _requested_vector_targets(config, load_steering_corpus())

    assert targets == ["prudence_scripture", "justice_scripture"]


def test_requested_vector_targets_include_distinct_psalm_family_lanes():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "scripture_steer"],
        scripture_targets=[],
        psalm_family_lanes=["trust", "wisdom"],
        include_merged_psalm_family_lane=True,
    )

    targets = _requested_vector_targets(config, load_steering_corpus())

    assert targets == [
        "psalms[trust]",
        "psalms[wisdom]",
        "psalms[trust+wisdom]",
    ]


def test_preflight_families_cover_virtue_and_christian_tracks():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=[
            "control",
            "combined",
            "christian_steer",
            "christian_null_control",
            "scripture_steer",
            "scripture_null_control",
        ],
    )

    assert _preflight_families(config) == [
        ("virtue_steer", "null_control", "virtue"),
        ("christian_steer", "christian_null_control", "christian"),
        ("scripture_steer", "scripture_null_control", "scripture"),
    ]


def test_preflight_failure_keys_only_collect_fail_rows():
    preflight = {
        "rows": [
            {"virtue": "prudence", "condition": "virtue_steer", "steering_target": "prudence", "status": "fail"},
            {"virtue": "courage", "condition": "christian_steer", "steering_target": "christian", "status": "warn"},
            {"virtue": "temperance", "condition": "virtue_steer", "steering_target": "temperance", "status": "pass"},
        ]
    }

    assert _preflight_failure_keys(preflight) == {("prudence", "virtue_steer", "prudence")}


def test_planned_stage_runs_excludes_skipped_preflight_paths():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        virtues=["prudence"],
        conditions=["control", "virtue_steer", "scripture_steer"],
    )

    total = _planned_stage_runs(
        config,
        "ratio",
        ["ratio"],
        2,
        skipped_preflight_paths={("prudence", "virtue_steer", "prudence")},
    )

    assert total == 8


def test_planned_stage_runs_with_pooled_virtue_has_single_virtue_lane():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        virtues=["prudence"],
        conditions=["control", "virtue_steer", "scripture_steer"],
        scripture_targets=["psalms"],
        pooled_virtue_steer=True,
    )

    total = _planned_stage_runs(
        config,
        "ratio",
        ["ratio"],
        2,
    )

    assert total == 6


def test_steering_targets_expand_to_distinct_psalm_family_labels():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "scripture_steer"],
        scripture_targets=[],
        psalm_family_lanes=["trust", "wisdom"],
        include_merged_psalm_family_lane=True,
    )

    assert _steering_targets(config, "ratio", "prudence", "scripture_steer") == [
        "psalms[trust]",
        "psalms[wisdom]",
        "psalms[trust+wisdom]",
    ]


def test_steering_targets_keep_explicit_book_lanes_in_order():
    config = IconoclastConfig(
        name="test",
        model="qwen",
        conditions=["control", "scripture_steer", "scripture_negative_alpha"],
        scripture_targets=["psalms", "proverbs", "romans", "petrine"],
    )

    assert _steering_targets(config, "ratio", "prudence", "scripture_steer") == [
        "psalms",
        "proverbs",
        "romans",
        "petrine",
    ]
    assert _steering_targets(config, "ratio", "prudence", "scripture_negative_alpha") == [
        "psalms",
        "proverbs",
        "romans",
        "petrine",
    ]


def test_write_run_status_persists_phase_and_error(tmp_path):
    path = tmp_path / "run.status.json"

    _write_run_status(
        path,
        state="failed",
        phase="preflight",
        output_prefix="iconoclast/demo",
        note="run stopped",
        current_virtue="prudence",
        current_condition="virtue_steer:prudence",
        error_type="RuntimeError",
        error_message="boom",
        artifacts={"console_log": "/tmp/demo_console.log"},
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["state"] == "failed"
    assert payload["phase"] == "preflight"
    assert payload["current_virtue"] == "prudence"
    assert payload["error_type"] == "RuntimeError"
    assert payload["artifacts"]["console_log"] == "/tmp/demo_console.log"


def test_write_preflight_payload_includes_active_probe_details(tmp_path):
    path = tmp_path / "preflight.json"

    _write_preflight_payload(
        path,
        status="running",
        policy="skip",
        alpha_scale=6.0,
        variant="ratio",
        rows=[{"virtue": "justice", "status": "warn"}],
        active={
            "virtue": "justice",
            "condition": "christian_steer",
            "steering_target": "christian",
        },
        note="probing steering divergence",
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "running"
    assert payload["active"]["virtue"] == "justice"
    assert payload["rows"][0]["status"] == "warn"


def test_artifact_to_runtime_applies_alpha_scale():
    artifact = {
        "virtues": {
            "psalms": {
                "alpha": 0.75,
                "layer_vectors": {"20": "real"},
                "null_vectors": {"20": "fake"},
            }
        }
    }

    runtime = _artifact_to_runtime(artifact, "psalms", use_null=False, alpha_scale=2.0)
    null_runtime = _artifact_to_runtime(artifact, "psalms", use_null=True, alpha_scale=0.5)

    assert runtime.alpha == 1.5
    assert runtime.layer_vectors == {20: "real"}
    assert null_runtime.alpha == 0.375
    assert null_runtime.layer_vectors == {20: "fake"}


def test_artifact_to_runtime_can_force_absolute_runtime_alpha():
    artifact = {
        "virtues": {
            "psalms": {
                "alpha": 0.75,
                "layer_vectors": {"20": "real"},
                "null_vectors": {"20": "fake"},
            }
        }
    }

    runtime = _artifact_to_runtime(
        artifact,
        "psalms",
        use_null=False,
        alpha_scale=2.0,
        runtime_alpha=-3.0,
    )

    assert runtime.alpha == -3.0
    assert runtime.layer_vectors == {20: "real"}


def test_artifact_to_runtime_uses_subspace_payload_when_present():
    artifact = {
        "virtues": {
            "fortitude_scripture": {
                "alpha": 0.75,
                "steering_mode": "subspace",
                "subspace_vectors": {"24": "real_basis"},
                "subspace_target_coefficients": {"24": "real_coeffs"},
                "null_subspace_vectors": {"24": "null_basis"},
                "null_subspace_target_coefficients": {"24": "null_coeffs"},
                "layer_vectors": {"24": "fallback_real"},
                "null_vectors": {"24": "fallback_null"},
            }
        }
    }

    runtime = _artifact_to_runtime(
        artifact,
        "fortitude_scripture",
        use_null=False,
        alpha_scale=2.0,
        runtime_alpha=6.0,
    )
    null_runtime = _artifact_to_runtime(
        artifact,
        "fortitude_scripture",
        use_null=True,
        alpha_scale=2.0,
    )

    assert isinstance(runtime, SubspaceSteeringRuntime)
    assert runtime.alpha == 6.0
    assert runtime.layer_bases == {24: "real_basis"}
    assert runtime.target_coefficients == {24: "real_coeffs"}
    assert isinstance(null_runtime, SubspaceSteeringRuntime)
    assert null_runtime.alpha == 1.5
    assert null_runtime.layer_bases == {24: "null_basis"}
    assert null_runtime.target_coefficients == {24: "null_coeffs"}


def test_run_artifact_paths_include_vector_diagnostics():
    config = IconoclastConfig(name="test", model="qwen", output_prefix="experiments/demo")

    paths = _run_artifact_paths(config, Path("/tmp/demo_vectors.pt"))

    diagnostics_json = Path(paths["vector_diagnostics_json"]).as_posix()
    diagnostics_md = Path(paths["vector_diagnostics_md"]).as_posix()
    assert diagnostics_json.endswith("experiments/demo_vector_diagnostics.json")
    assert diagnostics_md.endswith("experiments/demo_vector_diagnostics.md")


def test_vector_diagnostics_payload_surfaces_rankings_and_candidates():
    artifact = {
        "model": "Qwen3.5-9B",
        "extraction_method": "scripture_contrast",
        "targets": ["psalms"],
        "virtues": {
            "psalms": {
                "extraction_method_used": "scripture_contrast",
                "source_mode": "whole_text_scripture_vs_generic",
                "background_mode": "generic_non_scripture",
                "psalm_vector_sets": ["popular", "trust"],
                "best_layer": 24,
                "best_layer_selection": "target_dev_accuracy_with_specificity",
                "layer_selection_candidates": [24, 25],
                "layer_window": [21, 22, 23, 24, 25, 26, 27],
                "alpha": 1.5,
                "alpha_selection": "target_dev_accuracy_with_specificity",
                "alpha_selection_candidates": [1.0, 1.5],
                "train_examples": 100,
                "dev_examples": 20,
                "test_examples": 20,
                "other_train_examples": 90,
                "other_dev_examples": 18,
                "other_test_examples": 18,
                "dev_accuracy": 0.7,
                "dev_margin": 0.12,
                "dev_specificity": 0.12,
                "steered_dev_accuracy": 0.75,
                "steered_dev_margin": 0.16,
                "steered_dev_specificity": 0.16,
                "test_accuracy": 0.65,
                "test_margin": 0.08,
                "test_specificity": 0.08,
                "test_accuracy_steered": 0.7,
                "steered_test_margin": 0.11,
                "test_specificity_steered": 0.11,
                "layer_scores": {"24": 0.7, "25": 0.68},
                "layer_margins": {"24": 0.12, "25": 0.09},
                "alpha_scores": {"1.0": 0.72, "1.5": 0.75},
                "alpha_margins": {"1.0": 0.13, "1.5": 0.16},
            }
        },
    }

    payload = _vector_diagnostics_payload(artifact, scripture_runtime_alpha=3.0)

    assert payload["scripture_runtime_alpha"] == 3.0
    assert payload["rankings"]["by_steered_dev_accuracy"][0]["target"] == "psalms"
    assert payload["target_summaries"][0]["scripture_runtime_alpha"] == 3.0
    assert payload["target_summaries"][0]["top_layers_by_dev_accuracy"][0] == {"layer": 24, "score": 0.7}
    assert payload["target_summaries"][0]["top_alphas_by_dev_accuracy"][0] == {"alpha": 1.5, "score": 0.75}


def test_iconoclast_console_capture_supports_file_only_mode(tmp_path):
    previous_results_dir = cli_module.RESULTS_DIR
    previous_mode = os.environ.get("VIRTUE_BENCH_ICONOCLAST_CONSOLE")

    cli_module.RESULTS_DIR = tmp_path
    os.environ["VIRTUE_BENCH_ICONOCLAST_CONSOLE"] = "file"
    try:
        with cli_module._iconoclast_console_capture("demo"):
            print("hello from stdout")
            sys.stderr.write("hello from stderr\n")
        payload = (tmp_path / "demo_console.log").read_text(encoding="utf-8")
    finally:
        cli_module.RESULTS_DIR = previous_results_dir
        if previous_mode is None:
            os.environ.pop("VIRTUE_BENCH_ICONOCLAST_CONSOLE", None)
        else:
            os.environ["VIRTUE_BENCH_ICONOCLAST_CONSOLE"] = previous_mode

    assert "hello from stdout" in payload
    assert "hello from stderr" in payload
