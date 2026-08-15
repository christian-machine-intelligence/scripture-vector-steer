import asyncio
import importlib.machinery
import sys
import types

import pytest

# hf_local pulls in transformers, which is not installed in the CPU-only
# analysis environment. Skip the module rather than failing collection for the
# whole suite.
pytest.importorskip("transformers", reason="hf_local runner requires transformers")

fake_openai = types.ModuleType("openai")
fake_openai.__spec__ = importlib.machinery.ModuleSpec("openai", loader=None)


class _AsyncOpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.AsyncOpenAI = _AsyncOpenAI
sys.modules.setdefault("openai", fake_openai)

fake_anthropic = types.ModuleType("anthropic")
fake_anthropic.__spec__ = importlib.machinery.ModuleSpec("anthropic", loader=None)


class _AsyncAnthropic:
    def __init__(self, *args, **kwargs):
        pass


fake_anthropic.AsyncAnthropic = _AsyncAnthropic
sys.modules.setdefault("anthropic", fake_anthropic)

from virtue_bench.core.schema import PreparedSample, Scenario
from virtue_bench.eval.experiment import _effective_max_tokens, _run_single_query_batch
from virtue_bench.runners.base import ModelRunner
from virtue_bench.runners.hf_local import HFLocalRunner


class _FakeRunner(ModelRunner):
    def __init__(self):
        self.calls = []

    async def query(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 128,
        retries: int = 0,
        timeout: int = 120,
    ) -> dict:
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "retries": retries,
                "timeout": timeout,
            }
        )
        return {"response": "A", "infra_error": None}

    def model_id(self) -> str:
        return "fake"


def test_hf_local_generation_kwargs_include_timeout_cap():
    runner = HFLocalRunner("dummy")
    runner.ensure_loaded = lambda: None  # type: ignore[method-assign]
    runner._is_qwen3_family = lambda: False  # type: ignore[method-assign]

    kwargs = runner._generation_kwargs(temperature=0.0, max_tokens=32, timeout=45)

    assert kwargs["max_new_tokens"] == 32
    assert kwargs["max_time"] == 45.0
    assert kwargs["do_sample"] is False


def test_hf_local_generation_kwargs_keep_qwen_sampling_and_timeout():
    runner = HFLocalRunner("dummy")
    runner.ensure_loaded = lambda: None  # type: ignore[method-assign]
    runner._is_qwen3_family = lambda: True  # type: ignore[method-assign]

    kwargs = runner._generation_kwargs(temperature=0.7, max_tokens=24, timeout=30)

    assert kwargs["max_new_tokens"] == 24
    assert kwargs["max_time"] == 30.0
    assert kwargs["temperature"] == 0.7
    assert kwargs["top_p"] == 0.8
    assert kwargs["top_k"] == 20


def test_hf_local_chat_template_can_enable_qwen_thinking():
    runner = HFLocalRunner("dummy", enable_thinking=True)
    runner.ensure_loaded = lambda: None  # type: ignore[method-assign]
    runner._is_qwen3_family = lambda: True  # type: ignore[method-assign]

    kwargs = runner._chat_template_kwargs()

    assert kwargs == {"enable_thinking": True}


def test_hf_local_generation_kwargs_skip_non_thinking_sampling_overrides_when_thinking():
    runner = HFLocalRunner("dummy", enable_thinking=True)
    runner.ensure_loaded = lambda: None  # type: ignore[method-assign]
    runner._is_qwen3_family = lambda: True  # type: ignore[method-assign]

    kwargs = runner._generation_kwargs(temperature=0.7, max_tokens=24, timeout=30)

    assert kwargs["max_new_tokens"] == 24
    assert kwargs["max_time"] == 30.0
    assert kwargs["temperature"] == 0.7
    assert "top_p" not in kwargs
    assert "top_k" not in kwargs


def test_hf_local_model_id_marks_thinking_mode():
    runner = HFLocalRunner("Qwen/Qwen3.5-9B", enable_thinking=True)

    assert runner.model_id() == "Qwen3.5-9B+thinking"


def test_run_single_query_batch_forwards_timeout_and_max_tokens():
    sample = PreparedSample(
        scenario=Scenario(
            base_id="demo-1",
            variant="ratio",
            scenario_a="Do the right thing",
            scenario_b="Do the tempting thing",
            virtue="prudence",
            source="test",
        ),
        prompt="Option A: Do the right thing\nOption B: Do the tempting thing",
        target="A",
    )
    runner = _FakeRunner()

    results = asyncio.run(
        _run_single_query_batch(
            runner,
            [sample],
            "system",
            0.0,
            1,
            2,
            17,
            False,
            23,
        )
    )

    assert len(results) == 1
    assert runner.calls[0]["timeout"] == 17
    assert runner.calls[0]["max_tokens"] == 23


def test_effective_max_tokens_expands_default_budget_for_thinking_mode():
    runner = HFLocalRunner("Qwen/Qwen3.5-9B", enable_thinking=True)

    assert _effective_max_tokens(runner, 128) == 512
    assert _effective_max_tokens(runner, 32) == 32
