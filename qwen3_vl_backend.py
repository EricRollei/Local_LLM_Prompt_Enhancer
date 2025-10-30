"""Utilities for working with Qwen3-VL vision-language models locally.

This module mirrors the essential loader/runner behavior provided by
Granddyser's dedicated Qwen3-VL ComfyUI nodes, but keeps everything
encapsulated so the Video Prompter nodes can optionally call Qwen3-VL
without additional graph plumbing.

Key capabilities:
- Resolve/download a Qwen3-VL model (default: 4B Instruct) into ComfyUI's
  models directory under ``VLM``.
- Optional quantization hints via ``@4bit``/``@8bit`` suffix on the model id.
- Simple key/value override string (e.g. ``quant=8bit;attn=sdpa``) that can be
  provided via the ComfyUI input currently used for endpoints.
- Cached model + processor instances so repeated invocations reuse memory.
- Image caption helper returning a plain string suitable for downstream use.

Dependencies are imported lazily and validated at call-time so that users who
stick with HTTP backends (LM Studio / Ollama) are not required to install the
transformers stack.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import folder_paths
from PIL import Image


try:  # Optional heavy dependencies – only required when Qwen is used.
    from transformers import (  # type: ignore
        AutoProcessor,
        Qwen3VLForConditionalGeneration,
    )
    try:
        from transformers import BitsAndBytesConfig  # type: ignore
    except ImportError:  # bitsandbytes is optional
        BitsAndBytesConfig = None  # type: ignore[assignment]
except ImportError:  # pragma: no cover - handled gracefully at runtime
    AutoProcessor = None  # type: ignore[assignment]
    Qwen3VLForConditionalGeneration = None  # type: ignore[assignment]
    BitsAndBytesConfig = None  # type: ignore[assignment]

try:
    from huggingface_hub import snapshot_download  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    snapshot_download = None  # type: ignore[assignment]

try:
    import torch  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    torch = None  # type: ignore[assignment]


DEFAULT_MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"


class Qwen3VLError(RuntimeError):
    """Raised when required Qwen3-VL dependencies are unavailable."""


@dataclass(frozen=True)
class Qwen3VLConfig:
    """Resolved configuration for loading and running a Qwen3-VL model."""

    model_id: str = DEFAULT_MODEL_ID
    quantization: str = "auto"
    attention: Optional[str] = None
    device_map: str = "auto"


_MODEL_CACHE: Dict[Qwen3VLConfig, Dict[str, Any]] = {}
_CACHE_LOCK = threading.Lock()


def caption_with_qwen3_vl(
    image: Image.Image,
    prompt: str,
    system_prompt: Optional[str] = None,
    model_spec: Optional[str] = None,
    backend_hint: Optional[str] = None,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Generate a detailed caption for ``image`` using a local Qwen3-VL model.

    Parameters
    ----------
    image:
        PIL image instance (will be converted to RGB internally).
    prompt:
        Text provided to the model alongside the image (user role).
    system_prompt:
        Optional system instruction. When omitted a default descriptive prompt
        is used.
    model_spec:
        HuggingFace repo id or local path. Accepts ``@4bit`` / ``@8bit`` to
        request quantized variants.
    backend_hint:
        Optional semi-colon separated key/value overrides, e.g.
        ``quant=8bit;attn=sdpa``. For backwards compatibility this parameter
        is ignored when it looks like a URL (contains ``://``).
    max_new_tokens:
        Generation length cap for the response.
    temperature:
        Sampling temperature. Values <=0.0 force greedy decoding.

    Returns
    -------
    Dict[str, Any]
        ``{"success": bool, "caption": str, "error": Optional[str]}``
    """

    config = _parse_config(model_spec, backend_hint)

    try:
        model_state = _get_or_load_model(config)
    except Qwen3VLError as exc:
        return {"success": False, "caption": "", "error": str(exc)}
    except Exception as exc:  # pragma: no cover - safety net
        return {
            "success": False,
            "caption": "",
            "error": f"Failed to load Qwen3-VL model: {exc}",
        }

    model = model_state["model"]
    processor = model_state["processor"]

    if system_prompt is None or not system_prompt.strip():
        system_prompt = (
            "You are an expert visual analyst. Describe every element in the image "
            "clearly and precisely."
        )

    image_rgb = image.convert("RGB")

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image", "image": image_rgb},
            ],
        },
    ]

    chat_text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    try:
        inputs = processor(
            text=[chat_text],
            images=[image_rgb],
            return_tensors="pt",
        )
    except Exception as exc:  # pragma: no cover - processor should handle
        return {"success": False, "caption": "", "error": str(exc)}

    target_device = _resolve_model_device(model)

    try:
        inputs = inputs.to(target_device)
    except Exception as exc:  # pragma: no cover - safety
        return {
            "success": False,
            "caption": "",
            "error": f"Unable to move inputs to device {target_device}: {exc}",
        }

    generation_kwargs: Dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0.0 and temperature != 1.0,
    }

    if generation_kwargs["do_sample"]:
        generation_kwargs["temperature"] = max(0.01, float(temperature))

    try:
        if torch is None:
            raise Qwen3VLError("PyTorch is required for Qwen3-VL captioning.")
        with torch.inference_mode():
            generated_ids = model.generate(**inputs, **generation_kwargs)
    except Exception as exc:
        return {"success": False, "caption": "", "error": str(exc)}

    input_length = inputs["input_ids"].shape[-1]
    generated_trimmed = generated_ids[:, input_length:]

    decoded = processor.batch_decode(
        generated_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )

    caption = (decoded[0] if decoded else "").strip()
    if "</think>" in caption:
        caption = caption.split("</think>")[-1].strip()

    return {"success": True, "caption": caption, "error": None}


def _parse_config(
    model_spec: Optional[str],
    backend_hint: Optional[str],
) -> Qwen3VLConfig:
    spec = (model_spec or DEFAULT_MODEL_ID).strip()
    quantization = "auto"
    attention: Optional[str] = None
    device_map = "auto"

    if "@" in spec:
        base, suffix = spec.split("@", 1)
        spec = base.strip() or DEFAULT_MODEL_ID
        quantization = suffix.strip().lower() or "auto"

    # Basic key/value override parser (e.g. quant=4bit;attn=sdpa)
    hint = (backend_hint or "").strip()
    if hint and "://" not in hint:
        for token in re.split(r"[;,]", hint):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if not value:
                continue
            if key in {"quant", "quantization"}:
                quantization = value.lower()
            elif key in {"attn", "attention"}:
                attention = value
            elif key in {"device", "device_map"}:
                device_map = value

    if spec.lower().startswith("local:"):
        spec = os.path.expanduser(spec.split(":", 1)[1].strip())

    return Qwen3VLConfig(
        model_id=spec or DEFAULT_MODEL_ID,
        quantization=quantization or "auto",
        attention=attention,
        device_map=device_map or "auto",
    )


def _get_or_load_model(config: Qwen3VLConfig) -> Dict[str, Any]:
    if AutoProcessor is None or Qwen3VLForConditionalGeneration is None:
        raise Qwen3VLError(
            "transformers>=4.41 with Qwen3-VL support is required for the local backend."
        )

    if torch is None:
        raise Qwen3VLError("PyTorch is required for the local Qwen3-VL backend.")

    with _CACHE_LOCK:
        cached = _MODEL_CACHE.get(config)
        if cached:
            return cached

    model_path = _resolve_model_path(config.model_id)

    quantization_config = None
    if config.quantization in {"4bit", "8bit"}:
        if BitsAndBytesConfig is None:
            raise Qwen3VLError(
                "bitsandbytes is required for {} quantization.".format(config.quantization)
            )
        load_in_4bit = config.quantization == "4bit"
        load_in_8bit = config.quantization == "8bit"
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=load_in_4bit,
            load_in_8bit=load_in_8bit,
        )

    load_kwargs: Dict[str, Any] = {
        "torch_dtype": "auto",
        "device_map": config.device_map or "auto",
        "trust_remote_code": True,
    }

    if quantization_config is not None:
        load_kwargs["quantization_config"] = quantization_config

    if config.attention:
        load_kwargs["attn_implementation"] = config.attention

    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path,
        **load_kwargs,
    )
    model.eval()

    processor = AutoProcessor.from_pretrained(
        model_path,
        trust_remote_code=True,
    )

    state = {"model": model, "processor": processor}

    with _CACHE_LOCK:
        _MODEL_CACHE[config] = state

    return state


def _resolve_model_path(model_id: str) -> str:
    potential_path = Path(model_id)
    if potential_path.exists():
        return str(potential_path)

    models_dir = Path(folder_paths.models_dir) / "VLM"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Match Granddyser node behavior: extract just the model name (after last slash)
    # This allows reusing models downloaded by the Granddyser nodes
    model_name = model_id.rsplit("/", 1)[-1]
    local_dir = models_dir / model_name

    if local_dir.exists() and any(local_dir.iterdir()):
        return str(local_dir)

    if snapshot_download is None:
        raise Qwen3VLError(
            "huggingface_hub is required to download '{}'".format(model_id)
        )

    snapshot_download(
        repo_id=model_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
    )

    return str(local_dir)


def _resolve_model_device(model: Any) -> Any:
    if hasattr(model, "device"):
        return model.device
    if hasattr(model, "hf_device_map"):
        device_map = model.hf_device_map
        if isinstance(device_map, dict) and device_map:
            first = next(iter(device_map.values()))
            if isinstance(first, (int, str)):
                return first
            if isinstance(first, (list, tuple)) and first:
                return first[0]
    return "cpu"


def generate_text_with_qwen3_vl(
    prompt: str,
    model_spec: Optional[str] = None,
    backend_hint: Optional[str] = None,
    max_new_tokens: int = 2000,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Generate text using Qwen3-VL model (no image input - pure text generation).
    
    Parameters
    ----------
    prompt:
        Text prompt for generation (can include system instructions).
    model_spec:
        Optional model specification (e.g., "local:/path/to/model" or None for default).
    backend_hint:
        Optional configuration hint string (e.g., "quant=8bit;attn=sdpa").
    max_new_tokens:
        Maximum tokens to generate.
    temperature:
        Sampling temperature (0.1-2.0).
        
    Returns
    -------
    Dictionary with 'success' bool, 'response' text, and optional 'error'.
    """
    try:
        config = _parse_model_spec(model_spec, backend_hint)
        state = _get_or_load_model(config)
        
        model = state["model"]
        processor = state["processor"]
        device = _resolve_model_device(model)
        
        # Format as text-only conversation
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        inputs = processor(
            text=[text],
            return_tensors="pt",
        )
        inputs = inputs.to(device)
        
        # Generate with temperature sampling
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=(temperature > 0.0),  # Only sample if temperature > 0
            )
        
        # Decode only the new tokens (skip input)
        input_len = inputs["input_ids"].shape[1]
        generated_ids = output_ids[:, input_len:]
        response_text = processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        
        return {
            "success": True,
            "response": response_text.strip(),
            "error": None
        }
        
    except Qwen3VLError as exc:
        return {
            "success": False,
            "response": "",
            "error": f"Qwen3-VL configuration error: {exc}"
        }
    except Exception as exc:
        return {
            "success": False,
            "response": "",
            "error": f"Qwen3-VL text generation failed: {exc}"
        }
