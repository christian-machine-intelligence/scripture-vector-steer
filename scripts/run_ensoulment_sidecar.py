#!/usr/bin/env python3
"""Run Ensoulment Propensity sidecar prompts with the local HF runner."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Iterable

from virtue_bench.runners.hf_local import HFLocalRunner


DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's prompt directly and concisely."


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def row_key(row: dict) -> tuple[str, str]:
    return (row["condition"], row["prompt_id"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--conditions", nargs="*", default=None)
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=180)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    packet_rows = read_jsonl(args.prompt_packet)
    if args.conditions:
        allowed_conditions = set(args.conditions)
        packet_rows = [row for row in packet_rows if row["condition"] in allowed_conditions]
    if args.limit is not None:
        packet_rows = packet_rows[: args.limit]

    existing = read_jsonl(args.output) if args.output.exists() else []
    completed = {row_key(row) for row in existing}
    output_rows = list(existing)

    runner = HFLocalRunner(model_name=args.model)
    total = len(packet_rows)
    for index, row in enumerate(packet_rows, start=1):
        key = row_key(row)
        if key in completed:
            print(f"[{index}/{total}] skip {row['condition']} {row['prompt_id']}")
            continue

        print(f"[{index}/{total}] run {row['condition']} {row['prompt_id']}", flush=True)
        result = asyncio.run(
            runner.query(
                row["prompt"],
                system_prompt=args.system_prompt,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
            )
        )
        output_rows.append(
            {
                "run_id": row.get("run_id"),
                "condition": row["condition"],
                "prompt_id": row["prompt_id"],
                "claim_category": row.get("claim_category"),
                "probe_style": row.get("probe_style"),
                "model": runner.model_id(),
                "temperature": args.temperature,
                "model_output": result.get("response", ""),
                "infra_error": result.get("infra_error"),
            }
        )
        write_jsonl(args.output, output_rows)

    print(f"wrote {len(output_rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
