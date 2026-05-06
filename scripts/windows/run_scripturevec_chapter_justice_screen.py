from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


MANAGER_PREFIX = "scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_all_v2"
PREFIX_STUB = "scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch"
MODEL_PATH = r"C:\Users\sethcodex\models\Qwen3-14B"
CORPUS_PATH = (
    r"results\experiments\scripturevec14\canon_discovery"
    r"\canon_justice_survivor_chapters_v1.jsonl"
)

BATCHES = {
    "01_skip03": "chapter_num_01 chapter_num_02 chapter_num_04 chapter_num_05 chapter_num_06 chapter_num_07 chapter_num_08 chapter_num_09 chapter_num_10".split(),
    "02": "chapter_num_11 chapter_num_12 chapter_num_13 chapter_num_14 chapter_num_15 chapter_num_16 chapter_num_17 chapter_num_18 chapter_num_19 chapter_num_20".split(),
    "03": "chapter_num_21 chapter_num_22 chapter_num_23 chapter_num_24 chapter_num_25 chapter_num_26 chapter_num_27 chapter_num_28 chapter_num_29 chapter_num_30".split(),
    "04": "chapter_num_31 chapter_num_32 chapter_num_33 chapter_num_34 chapter_num_35 chapter_num_36 chapter_deu_01 chapter_deu_02 chapter_deu_03 chapter_deu_04".split(),
    "05": "chapter_deu_05 chapter_deu_06 chapter_deu_07 chapter_deu_08 chapter_deu_09 chapter_deu_10 chapter_deu_11 chapter_deu_12 chapter_deu_13 chapter_deu_14".split(),
    "06": "chapter_deu_15 chapter_deu_16 chapter_deu_17 chapter_deu_18 chapter_deu_19 chapter_deu_20 chapter_deu_21 chapter_deu_22 chapter_deu_23 chapter_deu_24".split(),
    "07": "chapter_deu_25 chapter_deu_26 chapter_deu_27 chapter_deu_28 chapter_deu_29 chapter_deu_30 chapter_deu_31 chapter_deu_32 chapter_deu_33 chapter_deu_34".split(),
    "08": "chapter_jdg_01 chapter_jdg_02 chapter_jdg_03 chapter_jdg_04 chapter_jdg_05 chapter_jdg_06 chapter_jdg_07 chapter_jdg_08 chapter_jdg_09 chapter_jdg_10".split(),
    "09": "chapter_jdg_11 chapter_jdg_12 chapter_jdg_13 chapter_jdg_14 chapter_jdg_15 chapter_jdg_16 chapter_jdg_17 chapter_jdg_18 chapter_jdg_19 chapter_jdg_20".split(),
    "10": "chapter_jdg_21 chapter_1ch_01 chapter_1ch_02 chapter_1ch_03 chapter_1ch_04 chapter_1ch_05 chapter_1ch_06 chapter_1ch_07 chapter_1ch_08 chapter_1ch_09".split(),
    "11": "chapter_1ch_10 chapter_1ch_11 chapter_1ch_12 chapter_1ch_13 chapter_1ch_14 chapter_1ch_15 chapter_1ch_16 chapter_1ch_17 chapter_1ch_18 chapter_1ch_19".split(),
    "12": "chapter_1ch_20 chapter_1ch_21 chapter_1ch_22 chapter_1ch_23 chapter_1ch_24 chapter_1ch_25 chapter_1ch_26 chapter_1ch_27 chapter_1ch_28 chapter_1ch_29".split(),
    "13": "chapter_amo_01 chapter_amo_02 chapter_amo_03 chapter_amo_04 chapter_amo_05 chapter_amo_06 chapter_amo_07 chapter_amo_08 chapter_amo_09 chapter_act_01".split(),
    "14": "chapter_act_02 chapter_act_03 chapter_act_04 chapter_act_05 chapter_act_06 chapter_act_07 chapter_act_08 chapter_act_09 chapter_act_10 chapter_act_11".split(),
    "15": "chapter_act_12 chapter_act_13 chapter_act_14 chapter_act_15 chapter_act_16 chapter_act_17 chapter_act_18 chapter_act_19 chapter_act_20 chapter_act_21".split(),
    "16": "chapter_act_22 chapter_act_23 chapter_act_24 chapter_act_25 chapter_act_26 chapter_act_27 chapter_act_28 chapter_heb_01 chapter_heb_02 chapter_heb_03".split(),
    "17": "chapter_heb_04 chapter_heb_05 chapter_heb_06 chapter_heb_07 chapter_heb_08 chapter_heb_09 chapter_heb_10 chapter_heb_11 chapter_heb_12 chapter_heb_13".split(),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")


def _python_path(repo: Path) -> Path:
    candidate = repo / ".venv" / "Scripts" / "python.exe"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def _batch_prefix(batch: str) -> str:
    return f"{PREFIX_STUB}{batch}_v1"


def _is_finished(status_path: Path) -> bool:
    try:
        return status_path.read_text(encoding="utf-8").strip() == "FINISHED"
    except OSError:
        return False


def _run_batch(repo: Path, results_dir: Path, python: Path, batch: str, targets: list[str]) -> int:
    prefix = _batch_prefix(batch)
    status_path = results_dir / f"{prefix}.status"
    wrapper_path = results_dir / f"{prefix}_wrapper_console.log"

    if _is_finished(status_path):
        return 0

    _write(status_path, "STARTED")
    if wrapper_path.exists():
        wrapper_path.unlink()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONFAULTHANDLER"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["TORCH_SHOW_CPP_STACKTRACES"] = "1"
    env["TORCH_DISABLE_ADDR2LINE"] = "1"
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    env["VIRTUE_BENCH_CUDA_DEVICE"] = "cuda:0"
    env["VIRTUE_BENCH_HF_DEVICE_MAP"] = ""
    env["VIRTUE_BENCH_HF_MAX_MEMORY"] = ""
    env["VIRTUE_BENCH_HF_LOAD_IN_4BIT"] = "1"

    cmd = [
        str(python),
        "-X",
        "faulthandler",
        "-u",
        "-m",
        "virtue_bench.cli",
        "iconoclast",
        "--model",
        MODEL_PATH,
        "--subset",
        "justice",
        "--stage",
        "ratio",
        "--runs",
        "1",
        "--limit",
        "10",
        "--temperature",
        "0.0",
        "--seed",
        "42",
        "--condition-profile",
        "scripturevec35",
        "--scripture-targets",
        *targets,
        "--external-scripture-corpus",
        str(repo / CORPUS_PATH),
        "--extraction-method",
        "scripture_contrast",
        "--alpha-candidates",
        "0.5,1.0,2.0,3.0,4.0,6.0,8.0",
        "--scripture-runtime-alpha",
        "32.0",
        "--preflight-policy",
        "off",
        "--output-prefix",
        f"experiments/scripturevec14/{prefix}",
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
        _write(status_path, "FINISHED")
    else:
        _write(status_path, "FAILED")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    results_dir = repo / "results"
    manager_status = results_dir / f"{MANAGER_PREFIX}.status"
    manager_log = results_dir / f"{MANAGER_PREFIX}_manager.log"
    python = _python_path(repo)

    _write(manager_status, "STARTED")
    _write(manager_log, f"[{_utc_now()}] STARTED")

    for batch, targets in BATCHES.items():
        prefix = _batch_prefix(batch)
        status_path = results_dir / f"{prefix}.status"
        if _is_finished(status_path):
            _append(manager_log, f"[{_utc_now()}] SKIP batch {batch} already finished")
            continue
        _append(manager_log, f"[{_utc_now()}] RUN batch {batch}")
        returncode = _run_batch(repo, results_dir, python, batch, targets)
        if returncode != 0:
            _write(manager_status, f"FAILED batch {batch}")
            _append(manager_log, f"[{_utc_now()}] FAILED batch {batch}")
            return returncode
        _append(manager_log, f"[{_utc_now()}] FINISHED batch {batch}")

    _write(manager_status, "FINISHED")
    _append(manager_log, f"[{_utc_now()}] FINISHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
