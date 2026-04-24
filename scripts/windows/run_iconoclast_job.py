from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a VirtueBench iconoclast job with repo-local logging."
    )
    parser.add_argument("--repo", required=True, help="Windows path to the repo root")
    parser.add_argument(
        "--output-prefix",
        required=True,
        help="Artifact prefix used for the status and wrapper log files",
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        help="Spawn a truly detached worker process, then return immediately.",
    )
    parser.add_argument(
        "--launch-record",
        default=None,
        help="Optional JSON file describing the detached worker launch.",
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "iconoclast_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to `virtue_bench.cli iconoclast`",
    )
    return parser.parse_args()


def _normalized_passthrough(args: argparse.Namespace) -> list[str]:
    passthrough = list(args.iconoclast_args)
    if passthrough and passthrough[0] == "--":
        return passthrough[1:]
    return passthrough


def _run_worker(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    results_dir = repo / "results"
    status_path = results_dir / f"{args.output_prefix}.status"
    wrapper_path = results_dir / f"{args.output_prefix}_wrapper_console.log"
    python_path = repo / ".venv" / "Scripts" / "python.exe"
    passthrough = _normalized_passthrough(args)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONFAULTHANDLER"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["TORCH_SHOW_CPP_STACKTRACES"] = "1"
    if os.name != "nt":
        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    env["VIRTUE_BENCH_ICONOCLAST_CONSOLE"] = "file"

    results_dir.mkdir(parents=True, exist_ok=True)
    status_path.write_text("STARTED", encoding="utf-8")
    if wrapper_path.exists():
        wrapper_path.unlink()

    cmd = [
        str(python_path),
        "-X",
        "faulthandler",
        "-u",
        "-m",
        "virtue_bench.cli",
        "iconoclast",
        *passthrough,
    ]

    with wrapper_path.open("w", encoding="utf-8") as wrapper:
        completed = subprocess.run(
            cmd,
            cwd=repo,
            env=env,
            stdout=wrapper,
            stderr=subprocess.STDOUT,
            check=False,
        )

    if completed.returncode == 0:
        status_path.write_text("FINISHED", encoding="utf-8")
    else:
        status_path.write_text("FAILED", encoding="utf-8")

    return completed.returncode


def _spawn_detached_worker(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    python_path = repo / ".venv" / "Scripts" / "python.exe"
    worker_python = python_path
    script_path = Path(__file__).resolve()
    passthrough = _normalized_passthrough(args)
    results_dir = repo / "results"
    status_path = results_dir / f"{args.output_prefix}.status"
    wrapper_path = results_dir / f"{args.output_prefix}_wrapper_console.log"
    run_status_path = results_dir / f"{args.output_prefix}_run.status.json"

    worker_cmd = [
        str(worker_python),
        str(script_path),
        "--worker",
        "--repo",
        str(repo),
        "--output-prefix",
        args.output_prefix,
    ]
    if passthrough:
        worker_cmd.append("--")
        worker_cmd.extend(passthrough)

    launch_cmd = [
        "cmd.exe",
        "/c",
        "start",
        "",
        "/min",
        *worker_cmd,
    ]

    launch = subprocess.run(
        launch_cmd,
        cwd=repo,
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if launch.returncode != 0:
        return launch.returncode

    # Keep the parent alive through fragile startup so the child can reach a
    # stable phase before the launching shell disappears.
    startup_observation = {
        "timed_out": False,
        "phase": None,
        "state": None,
    }
    deadline = time.time() + 120.0
    while time.time() < deadline:
        if run_status_path.exists():
            try:
                payload = json.loads(run_status_path.read_text(encoding="utf-8"))
                startup_observation["phase"] = payload.get("phase")
                startup_observation["state"] = payload.get("state")
                if payload.get("state") != "running":
                    break
                if payload.get("phase") not in {"startup", "vector_load", "vector_extraction", "model_load"}:
                    break
            except Exception:
                pass
        time.sleep(2)
    else:
        startup_observation["timed_out"] = True

    launch_record = args.launch_record
    if launch_record:
        launch_path = Path(launch_record)
        launch_path.parent.mkdir(parents=True, exist_ok=True)
        launch_path.write_text(
            json.dumps(
                {
                    "launched_at": datetime.now(timezone.utc).isoformat(),
                    "cmd": launch_cmd,
                    "worker_cmd": worker_cmd,
                    "worker_python": str(worker_python),
                    "repo": str(repo),
                    "output_prefix": args.output_prefix,
                    "status_exists_after_grace": status_path.exists(),
                    "wrapper_exists_after_grace": wrapper_path.exists(),
                    "startup_observation": startup_observation,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print("DETACHED_WINDOW_LAUNCHED")
    return 0


def main() -> int:
    args = parse_args()
    if args.detach and args.worker:
        raise SystemExit("choose either --detach or --worker, not both")
    if args.detach:
        return _spawn_detached_worker(args)
    return _run_worker(args)


if __name__ == "__main__":
    raise SystemExit(main())
