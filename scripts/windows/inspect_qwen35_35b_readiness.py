"""Inspect whether the Windows GPU box is ready to load Qwen3.5-35B-A3B.

This script is intentionally read-only. It reports live GPU memory, likely
Python workers, relevant CUDA/model-loading environment variables, and whether
the local 35B mirror exists.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODEL_DIR = Path.home() / "models" / "Qwen3.5-35B-A3B"
ENV_KEYS = [
    "CUDA_VISIBLE_DEVICES",
    "VIRTUE_BENCH_CUDA_DEVICE",
    "VIRTUE_BENCH_HF_DEVICE_MAP",
    "VIRTUE_BENCH_HF_MAX_MEMORY",
    "VIRTUE_BENCH_HF_LOAD_IN_4BIT",
    "PYTORCH_CUDA_ALLOC_CONF",
]


def _run(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return f"{command[0]} not found"
    output = (completed.stdout or "").strip()
    error = (completed.stderr or "").strip()
    if completed.returncode and error:
        return f"{output}\n{error}".strip()
    return output or error or "(no output)"


def _dir_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    _print_section("GPU memory")
    print(
        _run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ]
        )
    )

    _print_section("GPU processes")
    print(_run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"]))

    _print_section("Python processes")
    print(_run(["cmd", "/c", "tasklist /FI \"IMAGENAME eq python.exe\" /V"]))

    _print_section("Relevant environment")
    for key in ENV_KEYS:
        value = os.environ.get(key)
        print(f"{key}={value if value else '(unset)'}")

    _print_section("PyTorch CUDA view")
    try:
        import torch
    except ImportError:
        print("torch is not installed in this Python environment")
    else:
        print(f"torch version: {torch.__version__}")
        print(f"cuda available: {torch.cuda.is_available()}")
        print(f"cuda device count: {torch.cuda.device_count()}")
        for index in range(torch.cuda.device_count()):
            free, total = torch.cuda.mem_get_info(index)
            print(
                f"cuda:{index} {torch.cuda.get_device_name(index)} "
                f"free={free / 1024**3:.2f} GiB total={total / 1024**3:.2f} GiB"
            )

    _print_section("Local 35B mirror")
    print(f"path: {MODEL_DIR}")
    print(f"exists: {MODEL_DIR.exists()}")
    if MODEL_DIR.exists():
        size_gib = _dir_size(MODEL_DIR) / 1024**3
        safetensors = sorted(MODEL_DIR.glob("*.safetensors"))
        print(f"size: {size_gib:.2f} GiB")
        print(f"safetensors files: {len(safetensors)}")
        config_path = MODEL_DIR / "config.json"
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            for key in [
                "model_type",
                "num_hidden_layers",
                "hidden_size",
                "num_attention_heads",
                "num_experts",
                "num_experts_per_tok",
            ]:
                if key in config:
                    print(f"{key}: {config[key]}")

    _print_section("Interpreter")
    print(sys.executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
