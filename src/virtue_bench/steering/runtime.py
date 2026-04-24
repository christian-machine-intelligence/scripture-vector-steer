"""Low-level activation collection and steering hooks for decoder-only HF models."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from typing import Dict, Iterable, List

try:
    import torch
except ImportError:  # pragma: no cover - exercised when hf extras are absent
    torch = None  # type: ignore


def _require_torch():
    if torch is None:  # pragma: no cover - defensive guard
        raise ImportError(
            "Activation steering requires the hf optional dependencies. "
            "Install with `pip install .[hf]`."
        )


def get_decoder_layers(model) -> List:
    """Return the decoder block list for common HF causal language models."""
    candidates = [
        getattr(getattr(model, "model", None), "layers", None),
        getattr(getattr(getattr(model, "model", None), "language_model", None), "layers", None),
        getattr(getattr(getattr(model, "model", None), "decoder", None), "layers", None),
        getattr(getattr(model, "transformer", None), "h", None),
        getattr(getattr(model, "gpt_neox", None), "layers", None),
    ]
    for layers in candidates:
        if layers is not None:
            return list(layers)
    raise ValueError(
        "Could not locate decoder layers on the supplied model. "
        "Expected one of model.layers, model.decoder.layers, transformer.h, or gpt_neox.layers."
    )


def get_model_hidden_size(model) -> int:
    """Return the text hidden size for a loaded model, including wrapped configs."""
    config = getattr(model, "config", None)
    if config is None:
        raise ValueError("Model has no config; could not determine hidden size.")

    hidden_size = getattr(config, "hidden_size", None)
    if hidden_size is not None:
        return int(hidden_size)

    text_config = getattr(config, "text_config", None)
    hidden_size = getattr(text_config, "hidden_size", None)
    if hidden_size is not None:
        return int(hidden_size)

    raise ValueError("Could not determine model hidden size from config.hidden_size or config.text_config.hidden_size.")


def get_model_device(model):
    """Return the primary device for a loaded model."""
    _require_torch()
    return next(model.parameters()).device


def _hidden_tensor_from_output(output):
    if isinstance(output, tuple):
        return output[0]
    return output


def _replace_hidden_tensor(output, hidden_states):
    if isinstance(output, tuple):
        return (hidden_states,) + output[1:]
    return hidden_states


def mean_pool_hidden(hidden_states, attention_mask):
    """Mean-pool active token positions and skip the first token when possible."""
    _require_torch()
    mask = attention_mask.to(hidden_states.device, hidden_states.dtype)
    if mask.shape[1] > 1:
        mask[:, 0] = 0
    denom = mask.sum(dim=1, keepdim=True).clamp_min(1.0)
    pooled = (hidden_states * mask.unsqueeze(-1)).sum(dim=1) / denom
    return pooled


class LayerActivationCollector:
    """Context manager that captures decoder block outputs for selected layers."""

    def __init__(self, model, layer_indices: Iterable[int]):
        self.layers = get_decoder_layers(model)
        self.layer_indices = list(layer_indices)
        self.activations: Dict[int, object] = {}
        self._stack = ExitStack()

    def __enter__(self):
        for layer_index in self.layer_indices:
            layer = self.layers[layer_index]

            def hook(_, __, output, *, layer_index=layer_index):
                self.activations[layer_index] = _hidden_tensor_from_output(output).detach()
                return output

            handle = layer.register_forward_hook(hook)
            self._stack.callback(handle.remove)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stack.close()
        return False


@dataclass
class SteeringRuntime:
    """Installable multi-layer residual steering for generation or probing."""

    layer_vectors: Dict[int, object]
    alpha: float
    skip_prefill: bool = False

    def install(self, model):
        _require_torch()
        layers = get_decoder_layers(model)
        stack = ExitStack()
        state = {"forward_calls": 0}

        def model_pre_hook(_, __):
            state["forward_calls"] += 1

        model_handle = model.register_forward_pre_hook(model_pre_hook)
        stack.callback(model_handle.remove)

        for layer_index, vector in self.layer_vectors.items():
            layer = layers[layer_index]
            base_vector = vector.detach()

            def hook(_, __, output, *, base_vector=base_vector):
                if self.skip_prefill and state["forward_calls"] <= 1:
                    return output
                hidden_states = _hidden_tensor_from_output(output)
                shift = (self.alpha * base_vector).to(hidden_states.device, hidden_states.dtype)
                shifted = hidden_states + shift.view(1, 1, -1)
                return _replace_hidden_tensor(output, shifted)

            handle = layer.register_forward_hook(hook)
            stack.callback(handle.remove)

        return stack
