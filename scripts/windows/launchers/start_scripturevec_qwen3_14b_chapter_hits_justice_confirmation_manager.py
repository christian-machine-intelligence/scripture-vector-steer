"""Start the chapter-hit confirmation manager as a detached Windows process."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-batch", default="01")
    parser.add_argument("--version", default="1")
    args = parser.parse_args()

    launcher_dir = Path(__file__).resolve().parent
    repo = launcher_dir.parents[2]
    results = repo / "results" / "experiments" / "scripturevec14"
    results.mkdir(parents=True, exist_ok=True)

    manager = launcher_dir / "run_scripturevec_qwen3_14b_chapter_hits_justice_confirmation_manager.cmd"
    prefix = f"scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40_manager_v{args.version}"
    stdout_path = results / f"{prefix}_detached_stdout.log"
    stderr_path = results / f"{prefix}_detached_stderr.log"

    command = f'"{manager}" {args.start_batch} {args.version}'

    creationflags = 0

    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
            shell=True,
        )

    print(f"Started manager pid={process.pid} start_batch={args.start_batch} version={args.version}")


if __name__ == "__main__":
    main()
