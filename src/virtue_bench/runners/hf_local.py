"""
Local HuggingFace model runner for VirtueBench V2.

Loads a model (with optional LoRA adapter) and runs inference locally.

Usage via CLI:
    virtue-bench run --model meta-llama/Llama-3.1-8B-Instruct --runner hf-local
    virtue-bench run --model meta-llama/Llama-3.1-8B-Instruct --runner hf-local --hf-adapter /path/to/adapter
"""

from __future__ import annotations

import gc
import sys
import threading
import traceback
from contextlib import nullcontext
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
try:
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
except ImportError:  # pragma: no cover - older transformers installs
    Qwen3_5Config = None  # type: ignore
    Qwen3_5ForConditionalGeneration = None  # type: ignore

from .base import ModelRunner


class HFLocalRunner(ModelRunner):
    """Run inference on a local HuggingFace model."""

    def __init__(
        self,
        model_name: str,
        adapter_path: str | None = None,
        *,
        enable_thinking: bool = False,
    ):
        self._model_name = model_name
        self._adapter_path = adapter_path
        self._enable_thinking = enable_thinking
        self._model = None
        self._tokenizer = None
        self._steering_runtime = None
        self._query_count = 0
        self._load_lock = threading.Lock()

    def ensure_loaded(self):
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return

            source_name = self._model_name
            load_kwargs = {
                "torch_dtype": torch.bfloat16,
                "device_map": {"": "cuda:0"},
            }
            if sys.platform.startswith("win"):
                # Windows CUDA kernels are proving less stable for long Qwen3 runs.
                # Eager attention is slower but noticeably safer than the default.
                load_kwargs["attn_implementation"] = "eager"

            if "qwen3.5" in self._model_name.lower() and Qwen3_5Config is not None and Qwen3_5ForConditionalGeneration is not None:
                source_name = self._prepare_qwen35_local_source()
                load_kwargs["use_safetensors"] = True
                load_kwargs["local_files_only"] = True
                config = Qwen3_5Config.from_pretrained(source_name, local_files_only=True)
                self._model = Qwen3_5ForConditionalGeneration.from_pretrained(
                    source_name,
                    config=config,
                    **load_kwargs,
                )
            else:
                self._model = AutoModelForCausalLM.from_pretrained(
                    source_name,
                    **load_kwargs,
                )
            self._tokenizer = AutoTokenizer.from_pretrained(
                source_name,
                local_files_only=bool("qwen3.5" in self._model_name.lower()),
            )
            self._tokenizer.pad_token = self._tokenizer.eos_token

            if self._adapter_path:
                from peft import PeftModel
                self._model = PeftModel.from_pretrained(self._model, self._adapter_path)

            self._model.eval()

    def _ensure_loaded(self):
        self.ensure_loaded()

    @property
    def model(self):
        self.ensure_loaded()
        return self._model

    @property
    def tokenizer(self):
        self.ensure_loaded()
        return self._tokenizer

    def get_model_and_tokenizer(self):
        self.ensure_loaded()
        return self._model, self._tokenizer

    def _is_qwen3_family(self) -> bool:
        self.ensure_loaded()
        config = getattr(self._model, "config", None)
        model_type = getattr(config, "model_type", None)
        if model_type in {"qwen3", "qwen3_5"}:
            return True
        return "qwen3" in self._model_name.lower()

    def _prepare_qwen35_local_source(self) -> str:
        """Mirror Qwen3.5 into a normal local directory before loading on Windows."""
        from huggingface_hub import snapshot_download

        model_dir = Path.home() / "models" / self._model_name.split("/")[-1]
        snapshot_download(
            repo_id=self._model_name,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
            allow_patterns=[
                "*.json",
                "*.safetensors",
                "*.txt",
                "*.model",
                "tokenizer*",
                "vocab*",
                "merges.txt",
                "special_tokens_map.json",
            ],
        )
        return str(model_dir)

    def _chat_template_kwargs(self) -> dict:
        """Model-specific chat template options for benchmark-compatible output."""
        if self._is_qwen3_family():
            return {"enable_thinking": self._enable_thinking}
        return {}

    def _generation_kwargs(self, *, temperature: float, max_tokens: int, timeout: int) -> dict:
        """Model-specific generation settings."""
        self.ensure_loaded()

        gen_kwargs = {"max_new_tokens": max_tokens}
        if timeout > 0:
            # HuggingFace can stop long-running generations once wall-clock time
            # crosses this threshold, which is much better than letting a single
            # steered sample stall the whole experiment indefinitely.
            gen_kwargs["max_time"] = float(timeout)
        if temperature > 0:
            gen_kwargs["temperature"] = temperature
            gen_kwargs["do_sample"] = True
        else:
            gen_kwargs["do_sample"] = False

        if self._is_qwen3_family() and temperature > 0 and not self._enable_thinking:
            # Qwen3/Qwen3.5 non-thinking guidance recommends this sampling setup.
            gen_kwargs["top_p"] = 0.8
            gen_kwargs["top_k"] = 20

        return gen_kwargs

    def set_steering_runtime(self, runtime) -> None:
        self._steering_runtime = runtime

    async def query(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 128,
        timeout: int = 120,
        **kwargs,
    ) -> dict:
        self.ensure_loaded()
        self._query_count += 1

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        inputs = None
        output = None
        try:
            inputs = self._tokenizer.apply_chat_template(
                messages,
                return_tensors="pt",
                add_generation_prompt=True,
                return_dict=True,
                **self._chat_template_kwargs(),
            ).to(self._model.device)

            gen_kwargs = self._generation_kwargs(
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            steering_context = nullcontext()
            if self._steering_runtime is not None:
                steering_context = self._steering_runtime.install(self._model)

            with steering_context:
                with torch.inference_mode():
                    output = self._model.generate(**inputs, **gen_kwargs)
                    if self._model.device.type == "cuda":
                        torch.cuda.synchronize(self._model.device)

            input_len = inputs["input_ids"].shape[1]
            response = self._tokenizer.decode(
                output[0][input_len:], skip_special_tokens=True
            )

            return {"response": response, "infra_error": None}

        except Exception as e:
            return {
                "response": "",
                "infra_error": f"{e}\n{traceback.format_exc(limit=20)}",
            }
        finally:
            if output is not None:
                del output
            if inputs is not None:
                del inputs
            if self._model.device.type == "cuda" and self._query_count % 10 == 0:
                gc.collect()
                torch.cuda.empty_cache()
                if hasattr(torch.cuda, "ipc_collect"):
                    torch.cuda.ipc_collect()

    def model_id(self) -> str:
        name = self._model_name.split("/")[-1]
        if self._enable_thinking:
            name = f"{name}+thinking"
        if self._adapter_path:
            adapter_name = self._adapter_path.rstrip("/").split("/")[-2]
            return f"{name}+{adapter_name}"
        return name
