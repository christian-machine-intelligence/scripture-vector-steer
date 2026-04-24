from __future__ import annotations

import asyncio
from pathlib import Path

from virtue_bench.core.constants import DEFAULT_SYSTEM_PROMPT
from virtue_bench.core.loader import load_scenarios, prepare_samples
from virtue_bench.runners.hf_local import HFLocalRunner


async def main() -> None:
    runner = HFLocalRunner("Qwen/Qwen3.5-9B", enable_thinking=False)
    scenarios = load_scenarios("prudence", variants=["ratio"])
    sample = prepare_samples(scenarios, seed=42, limit=1)[0]
    print("LOADED_SAMPLE", sample.scenario.base_id, sample.target, flush=True)
    result = await runner.query(
        sample.prompt,
        DEFAULT_SYSTEM_PROMPT,
        temperature=0.7,
        max_tokens=128,
        timeout=120,
    )
    print("INFRA_ERROR", result.get("infra_error"), flush=True)
    response = result.get("response", "")
    print("RESPONSE_START", flush=True)
    print(response[:1000], flush=True)
    print("RESPONSE_END", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
