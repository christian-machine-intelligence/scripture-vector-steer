from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_TARGETS = ["psalms", "romans", "petrine"]
DEFAULT_PREFIX_BASE = "homepc_qwen35_full_scripture_study2"


@dataclass(frozen=True)
class Attempt:
    prefix: str
    version: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _python_path(repo: Path) -> Path:
    candidate = repo / ".venv" / "Scripts" / "python.exe"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def _prefix(base: str, version: int) -> str:
    return f"{base}_v{version}"


def _version_from_prefix(base: str, prefix: str) -> Optional[int]:
    marker = f"{base}_v"
    if not prefix.startswith(marker):
        return None
    raw = prefix[len(marker):]
    return int(raw) if raw.isdigit() else None


def _strip_suffix(name: str, suffix: str) -> Optional[str]:
    if not name.endswith(suffix):
        return None
    return name[: -len(suffix)]


def _attempts(results_dir: Path, base: str) -> list[Attempt]:
    suffixes = [
        "_run.status.json",
        "_full.status.json",
        "_full_logs.json",
        "_launch.json",
        "_console.log",
        "_wrapper_console.log",
        ".status",
    ]
    prefixes: set[str] = set()
    for suffix in suffixes:
        for path in results_dir.glob(f"{base}_v*{suffix}"):
            prefix = _strip_suffix(path.name, suffix)
            if prefix:
                prefixes.add(prefix)

    attempts = []
    for prefix in prefixes:
        version = _version_from_prefix(base, prefix)
        if version is not None:
            attempts.append(Attempt(prefix=prefix, version=version))
    attempts.sort(key=lambda attempt: attempt.version)
    return attempts


def _artifact_exists(raw_path: Optional[str], repo: Path) -> bool:
    if not raw_path:
        return False
    path = Path(raw_path)
    if path.exists():
        return True
    return (repo / raw_path).exists()


def _is_completed(results_dir: Path, repo: Path, prefix: str) -> bool:
    required = [
        results_dir / f"{prefix}_run.status.json",
        results_dir / f"{prefix}_full.status.json",
        results_dir / f"{prefix}_full.json",
        results_dir / f"{prefix}_full_logs.json",
        results_dir / f"{prefix}_vector_diagnostics.json",
        results_dir / f"{prefix}_vector_diagnostics.md",
    ]
    if any(not path.exists() for path in required):
        return False

    run_status = _read_json(results_dir / f"{prefix}_run.status.json")
    full_status = _read_json(results_dir / f"{prefix}_full.status.json")
    if run_status.get("state") != "completed" or full_status.get("state") != "completed":
        return False

    vector_artifact = (run_status.get("artifacts") or {}).get("vector_artifact")
    return _artifact_exists(vector_artifact, repo)


def _completed_attempt(results_dir: Path, repo: Path, base: str) -> Optional[Attempt]:
    completed = [
        attempt
        for attempt in _attempts(results_dir, base)
        if _is_completed(results_dir, repo, attempt.prefix)
    ]
    if not completed:
        return None
    return completed[-1]


def _running_attempt(results_dir: Path, base: str) -> Optional[Attempt]:
    running = []
    for attempt in _attempts(results_dir, base):
        run_status = _read_json(results_dir / f"{attempt.prefix}_run.status.json")
        wrapper_status_path = results_dir / f"{attempt.prefix}.status"
        wrapper_status = ""
        try:
            wrapper_status = wrapper_status_path.read_text(encoding="utf-8").strip()
        except OSError:
            pass
        if run_status.get("state") == "running" or wrapper_status == "STARTED":
            running.append(attempt)
    if not running:
        return None
    return running[-1]


def _latest_activity_epoch(results_dir: Path, prefix: str) -> float:
    paths = [
        results_dir / f"{prefix}_run.status.json",
        results_dir / f"{prefix}_full.status.json",
        results_dir / f"{prefix}_console.log",
        results_dir / f"{prefix}_wrapper_console.log",
        results_dir / f"{prefix}_launch.json",
        results_dir / f"{prefix}.status",
    ]
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    if not mtimes:
        return 0.0
    return max(mtimes)


def _is_stale(results_dir: Path, prefix: str, stale_seconds: float) -> bool:
    latest_activity = _latest_activity_epoch(results_dir, prefix)
    if latest_activity <= 0:
        return True
    return (time.time() - latest_activity) > stale_seconds


class Manager:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.repo = args.repo.resolve()
        self.results_dir = args.results_dir.resolve()
        self.base = args.output_prefix_base
        self.python = _python_path(self.repo)
        self.log_path = self.results_dir / args.manager_log
        self.status_path = self.results_dir / args.manager_status
        self.lock_path = self.results_dir / args.lock_file
        self.last_message: Optional[str] = None

    def acquire_lock(self) -> None:
        if self.args.no_lock:
            return
        self.results_dir.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise RuntimeError(f"Manager lock already exists: {self.lock_path}")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "created_at": _utc_now()}, indent=2))

    def release_lock(self) -> None:
        if self.args.no_lock:
            return
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    def log(self, message: str, *, always: bool = False) -> None:
        line = f"[{_utc_now()}] {message}"
        if always or message != self.last_message:
            print(line, flush=True)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            self.last_message = message

    def write_status(self, *, state: str, note: str, prefix: Optional[str] = None) -> None:
        completed = _completed_attempt(self.results_dir, self.repo, self.base)
        payload = {
            "state": state,
            "note": note,
            "updated_at": _utc_now(),
            "current_prefix": prefix,
            "completed": completed.prefix if completed is not None else None,
            "targets": list(self.args.targets),
            "stage": "full",
            "runs": self.args.runs,
            "limit": self.args.limit,
            "scripture_runtime_alpha": self.args.scripture_runtime_alpha,
            "results_dir": str(self.results_dir),
        }
        _write_json(self.status_path, payload)

    def next_version(self) -> int:
        attempts = _attempts(self.results_dir, self.base)
        if not attempts:
            return 1
        return max(attempt.version for attempt in attempts) + 1

    def launch_attempt(self) -> None:
        prefix = _prefix(self.base, self.next_version())
        iconoclast_args = [
            "--model",
            self.args.model,
            "--stage",
            "full",
            "--runs",
            str(self.args.runs),
            "--limit",
            str(self.args.limit),
            "--temperature",
            str(self.args.temperature),
            "--seed",
            str(self.args.seed),
            "--condition-profile",
            "scripture_study2",
            "--scripture-targets",
            *self.args.targets,
            "--extraction-method",
            "scripture_contrast",
            "--scripture-runtime-alpha",
            str(self.args.scripture_runtime_alpha),
            "--preflight-policy",
            "off",
            "--output-prefix",
            prefix,
        ]

        launch_record = self.results_dir / f"{prefix}_launch.json"
        command = [
            str(self.python),
            str(self.repo / "scripts" / "windows" / "run_iconoclast_job.py"),
            "--detach",
            "--repo",
            str(self.repo),
            "--output-prefix",
            prefix,
            "--launch-record",
            str(launch_record),
            "--",
            *iconoclast_args,
        ]

        self.write_status(state="launching", note="launching Study 2", prefix=prefix)
        self.log(f"Launching Study 2 as {prefix}", always=True)
        if self.args.dry_run:
            self.log("Dry run enabled; launch skipped.", always=True)
            return

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.repo / "src")
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONFAULTHANDLER"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run(command, cwd=self.repo, env=env, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"Launch command failed for {prefix} with exit code {completed.returncode}")
        self.write_status(state="running", note="Study 2 launched", prefix=prefix)

    def run_summary(self, prefix: str) -> None:
        command = [
            str(self.python),
            str(self.repo / "scripts" / "analyze_scripture_study2.py"),
            "--results-dir",
            str(self.results_dir),
            "--glob",
            f"{prefix}_full_logs.json",
            "--output-prefix",
            self.args.summary_output_prefix,
        ]
        self.log(f"Writing Study 2 summary for {prefix}", always=True)
        if self.args.dry_run:
            self.log("Dry run enabled; summary skipped.", always=True)
            return
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.repo / "src")
        completed = subprocess.run(
            command,
            cwd=self.repo,
            env=env,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if completed.stdout:
            for line in completed.stdout.splitlines():
                self.log(f"summary: {line}", always=True)
        if completed.returncode != 0:
            raise RuntimeError(f"Summary command failed with exit code {completed.returncode}")

    def step(self) -> bool:
        completed = _completed_attempt(self.results_dir, self.repo, self.base)
        if completed is not None:
            self.run_summary(completed.prefix)
            self.write_status(state="completed", note="Study 2 completed and summary written", prefix=completed.prefix)
            self.log("Study 2 completed.", always=True)
            return True

        running = _running_attempt(self.results_dir, self.base)
        if running is not None:
            if _is_stale(self.results_dir, running.prefix, self.args.stale_minutes * 60.0):
                self.log(f"{running.prefix} is stale; launching a replacement.", always=True)
                self.launch_attempt()
                return False
            self.write_status(state="running", note="waiting for Study 2", prefix=running.prefix)
            self.log(f"Waiting for active Study 2 attempt {running.prefix}")
            return False

        self.launch_attempt()
        return False

    def run(self) -> None:
        self.acquire_lock()
        try:
            self.log("Study 2 manager started.", always=True)
            while True:
                done = self.step()
                if done or self.args.once:
                    break
                time.sleep(self.args.poll_seconds)
        finally:
            self.release_lock()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor and advance the Qwen3.5 scripture Study 2 run on Windows."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repo root on the Windows machine")
    parser.add_argument("--results-dir", type=Path, default=None, help="Result artifact directory")
    parser.add_argument("--targets", nargs="+", default=list(DEFAULT_TARGETS))
    parser.add_argument("--output-prefix-base", default=DEFAULT_PREFIX_BASE)
    parser.add_argument("--model", default="Qwen/Qwen3.5-9B")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scripture-runtime-alpha", type=float, default=3.0)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--stale-minutes", type=float, default=8.0)
    parser.add_argument("--manager-log", default="scripture_study2_manager.log")
    parser.add_argument("--manager-status", default="scripture_study2_manager.status.json")
    parser.add_argument("--summary-output-prefix", default="scripture_study2_summary")
    parser.add_argument("--lock-file", default="scripture_study2_manager.lock")
    parser.add_argument("--no-lock", action="store_true", help="Allow multiple managers to run at once")
    parser.add_argument("--once", action="store_true", help="Run one manager step and exit")
    parser.add_argument("--dry-run", action="store_true", help="Show decisions without launching jobs")
    args = parser.parse_args()

    unknown_targets = [target for target in args.targets if target not in DEFAULT_TARGETS]
    if unknown_targets:
        raise SystemExit(f"Unknown Study 2 scripture targets: {', '.join(unknown_targets)}")

    args.repo = args.repo.resolve()
    if args.results_dir is None:
        args.results_dir = args.repo / "results"
    else:
        args.results_dir = args.results_dir.resolve()
    return args


def main() -> int:
    args = parse_args()
    manager = Manager(args)
    try:
        manager.run()
    except Exception as exc:
        manager.write_status(state="failed", note=f"{type(exc).__name__}: {exc}")
        manager.log(f"Manager failed: {type(exc).__name__}: {exc}", always=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
