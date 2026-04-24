import json

from virtue_bench.dashboard import build_dashboard_state


def _json_record(payload):
    return {"text": json.dumps(payload)}


def test_dashboard_reports_preflight_failure():
    snapshot = {
        "source": {"kind": "local", "results_dir": "/tmp/results"},
        "files": {
            "preflight": _json_record(
                {
                    "status": "failed",
                    "variant": "ratio",
                    "alpha_scale": 6.0,
                    "rows": [
                        {
                            "virtue": "courage",
                            "status": "fail",
                            "control_accuracy": 0.25,
                            "steer_accuracy": 0.25,
                            "null_accuracy": 0.25,
                            "answer_changes": 0,
                            "null_answer_changes": 0,
                            "notes": ["steering produced zero answer changes at probe strength"],
                        }
                    ],
                }
            )
        },
    }

    state = build_dashboard_state(snapshot, output_prefix="demo_run")

    assert state["overall_state"] == "failed"
    assert "Preflight" in state["headline"]
    assert state["preflight"]["counts"] == {"fail": 1}
    assert state["preflight"]["rows"][0]["virtue"] == "courage"


def test_dashboard_reports_running_stage_progress():
    result_rows = [
        {
            "model": "Qwen/Qwen3-8B",
            "virtue": "prudence",
            "variant": "ratio",
            "condition": "control",
            "frame": "ratio",
            "run_index": 0,
            "seed": 42,
            "temperature": 0.7,
            "accuracy": 0.6,
            "stderr": None,
            "samples": 20,
            "status": "completed",
            "metadata": {},
            "sample_details": [],
        },
        {
            "model": "Qwen/Qwen3-8B",
            "virtue": "prudence",
            "variant": "ratio",
            "condition": "control",
            "frame": "ratio",
            "run_index": 1,
            "seed": 43,
            "temperature": 0.7,
            "accuracy": 0.5,
            "stderr": None,
            "samples": 20,
            "status": "completed",
            "metadata": {},
            "sample_details": [],
        },
    ]
    snapshot = {
        "source": {"kind": "local", "results_dir": "/tmp/results"},
        "files": {
            "launcher_status": {"text": "STARTED"},
            "ratio_status": _json_record(
                {
                    "state": "running",
                    "stage": "ratio",
                    "total_runs": 12,
                    "completed_runs": 3,
                    "virtue": "prudence",
                    "variant": "ratio",
                    "condition": "control",
                    "run_index": 1,
                    "updated_at": "2026-04-20T18:00:00Z",
                }
            ),
            "ratio_results": _json_record(result_rows),
        },
    }

    state = build_dashboard_state(snapshot, output_prefix="demo_run")

    assert state["overall_state"] == "running"
    assert state["stages"][0]["name"] == "ratio"
    assert round(state["stages"][0]["progress"]["percent"], 2) == 25.0
    assert state["stages"][0]["rows"][0]["runs_seen"] == 2
    assert round(state["stages"][0]["rows"][0]["mean_accuracy"], 2) == 0.55
