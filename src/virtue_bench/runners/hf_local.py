"""
Local HuggingFace model runner for VirtueBench V2.

Loads a model (with optional LoRA adapter) and runs inference locally.

Usage via CLI:
    virtue-bench run --model meta-llama/Llama-3.1-8B-Instruct --runner hf-local
    virtue-bench run --model meta-llama/Llama-3.1-8B-Instruct --runner hf-local --hf-adapter /path/to/adapter
"""

from __future__ import annotations

import gc
import os
import sys
import threading
import traceback
from contextlib import nullcontext
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
try:
    from transformers import BitsAndBytesConfig
except ImportError:  # pragma: no cover - older transformers installs
    BitsAndBytesConfig = None  # type: ignore
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
            model_name_lower = self._model_name.lower()
            use_4bit = self._should_load_in_4bit(model_name_lower)
            if torch.cuda.is_available():
                load_kwargs = {
                    "device_map": self._resolve_device_map(
                        model_name_lower,
                        use_4bit=use_4bit,
                    ),
                }
                max_memory = self._resolve_max_memory()
                if max_memory is not None:
                    load_kwargs["max_memory"] = max_memory
                if use_4bit:
                    load_kwargs["torch_dtype"] = torch.bfloat16
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    )
                    print(
                        f"Loading {self._model_name} with 4-bit quantization",
                        flush=True,
                    )
                else:
                    load_kwargs["torch_dtype"] = torch.bfloat16
            else:
                # CPU is slow for real runs, but it keeps tiny local smoke tests
                # usable on development machines without CUDA.
                load_kwargs = {"torch_dtype": torch.float32}
            if sys.platform.startswith("win"):
                # Windows CUDA kernels are proving less stable for long Qwen3 runs.
                # Eager attention is slower but noticeably safer than the default.
                load_kwargs["attn_implementation"] = "eager"

            if "qwen3.5" in model_name_lower:
                source_name = self._prepare_qwen35_local_source()
                load_kwargs["use_safetensors"] = True
                load_kwargs["local_files_only"] = True
                config = AutoConfig.from_pretrained(source_name, local_files_only=True)
                if (
                    getattr(config, "model_type", None) == "qwen3_5_moe"
                    or Qwen3_5Config is None
                    or Qwen3_5ForConditionalGeneration is None
                ):
                    self._model = AutoModelForCausalLM.from_pretrained(
                        source_name,
                        config=config,
                        **load_kwargs,
                    )
                else:
                    dense_config = Qwen3_5Config.from_pretrained(source_name, local_files_only=True)
                    self._model = Qwen3_5ForConditionalGeneration.from_pretrained(
                        source_name,
                        config=dense_config,
                        **load_kwargs,
                    )
            else:
                self._model = AutoModelForCausalLM.from_pretrained(
                    source_name,
                    **load_kwargs,
                )
            self._tokenizer = AutoTokenizer.from_pretrained(
                source_name,
                local_files_only=bool("qwen3.5" in model_name_lower),
            )
            self._tokenizer.pad_token = self._tokenizer.eos_token

            if self._adapter_path:
                from peft import PeftModel
                self._model = PeftModel.from_pretrained(self._model, self._adapter_path)

            self._model.eval()

    def _ensure_loaded(self):
        self.ensure_loaded()

    def _should_load_in_4bit(self, model_name_lower: str) -> bool:
        default = "1" if "qwen3.5-35b" in model_name_lower and torch.cuda.is_available() else "0"
        raw_value = os.environ.get("VIRTUE_BENCH_HF_LOAD_IN_4BIT", default)
        requested = raw_value.strip().lower() in {"1", "true", "yes", "on"}
        if requested and BitsAndBytesConfig is None:
            raise RuntimeError(
                "VIRTUE_BENCH_HF_LOAD_IN_4BIT is enabled, but this environment "
                "does not have a transformers BitsAndBytesConfig available."
            )
        return requested

    def _resolve_device_map(self, model_name_lower: str, *, use_4bit: bool):
        default = "auto" if use_4bit and "qwen3.5-35b" in model_name_lower else ""
        raw_value = os.environ.get("VIRTUE_BENCH_HF_DEVICE_MAP", default).strip()
        if raw_value:
            return raw_value
        cuda_device = os.environ.get("VIRTUE_BENCH_CUDA_DEVICE", "cuda:0")
        return {"": cuda_device}

    def _resolve_max_memory(self):
        raw_value = os.environ.get("VIRTUE_BENCH_HF_MAX_MEMORY", "").strip()
        if not raw_value:
            return None
        max_memory = {}
        for item in raw_value.split(","):
            key, value = item.split(":", 1)
            key = key.strip()
            parsed_key = int(key) if key.isdigit() else key
            max_memory[parsed_key] = value.strip()
        return max_memory

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
        max_workers = max(
            1,
            int(os.environ.get("VIRTUE_BENCH_HF_DOWNLOAD_WORKERS", "1")),
        )
        allow_patterns = [
            "*.json",
            "*.safetensors",
            "*.txt",
            "*.model",
            "tokenizer*",
            "vocab*",
            "merges.txt",
            "special_tokens_map.json",
        ]
        print(
            f"Preparing local Qwen3.5 mirror at {model_dir} "
            f"(download_workers={max_workers})",
            flush=True,
        )
        try:
            snapshot_download(
                repo_id=self._model_name,
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
                allow_patterns=allow_patterns,
                max_workers=max_workers,
            )
        except TypeError as exc:
            if "local_dir_use_symlinks" not in str(exc):
                raise
            snapshot_download(
                repo_id=self._model_name,
                local_dir=str(model_dir),
                allow_patterns=allow_patterns,
                max_workers=max_workers,
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
            if getattr(self._tokenizer, "chat_template", None):
                inputs = self._tokenizer.apply_chat_template(
                    messages,
                    return_tensors="pt",
                    add_generation_prompt=True,
                    return_dict=True,
                    **self._chat_template_kwargs(),
                ).to(self._model.device)
            else:
                prompt_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                inputs = self._tokenizer(
                    prompt_text,
                    return_tensors="pt",
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
            if (
                self._model.device.type == "cuda"
                and not sys.platform.startswith("win")
                and self._query_count % 10 == 0
            ):
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
