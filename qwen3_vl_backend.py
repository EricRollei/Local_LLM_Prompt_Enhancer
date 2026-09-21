"""Utilities for working with Qwen3-VL vision-language models locally.

This module mirrors the essential loader/runner behavior provided by
Granddyser's dedicated Qwen3-VL ComfyUI nodes, but keeps everything
encapsulated so the Video Prompter nodes can optionally call Qwen3-VL
without additional graph plumbing.

Key capabilities:
- Resolve a Qwen3-VL model from ComfyUI's ``models/VLM`` folder. Nothing is ever
  downloaded silently: a download happens only when the user typed an explicit
  ``org/name`` repository id that is not on disk. See ``resolve_model_spec``.
- Optional quantization hints via ``@4bit``/``@8bit`` suffix on the model id.
- Simple key/value override string (e.g. ``quant=8bit;attn=sdpa``) that can be
  provided via the ComfyUI input currently used for endpoints.
- Cached model + processor instances, keyed by the RESOLVED folder, so the image
  pass and the text pass of one node share a single copy in VRAM.
- Image caption helper returning a plain string suitable for downstream use.

Dependencies are imported lazily and validated at call-time so that users who
stick with HTTP backends (LM Studio / Ollama) are not required to install the
transformers stack.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

    model_id: str = ""           # "" = auto-detect a local model (see resolve_model_spec)
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
    # "" = no model was named: resolve_model_spec auto-detects a local one. The default repo id is NOT filled in
    # here, so that a missing default can never turn into a download nobody asked for.
    spec = (model_spec or "").strip()
    quantization = "auto"
    attention: Optional[str] = None
    device_map = "auto"

    if "@" in spec:
        base, suffix = spec.split("@", 1)
        spec = base.strip()
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
        model_id=spec,
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

    # Resolve first, then look in the cache: the image pass names no model and the text pass used to name a full
    # path, which made two cache keys for one folder and loaded the same model into VRAM twice.
    model_path = _resolve_model_path(config.model_id)
    config = _cache_key(config, model_path)

    with _CACHE_LOCK:
        cached = _MODEL_CACHE.get(config)
        if cached:
            return cached
    print(f"[Qwen3-VL Backend] loading {model_path}")

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


REPO_ID = re.compile(r"^[A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*$")
DEFAULT_SPECS = {"", "default", "auto", "none"}


def vlm_dir() -> Path:
    return Path(folder_paths.models_dir) / "VLM"


def _is_model_folder(path: Path) -> bool:
    return path.is_dir() and (path / "config.json").is_file()


def list_local_models() -> List[Path]:
    """Qwen VL model folders in models/VLM (a folder counts when it holds a config.json), in a stable order."""
    base = vlm_dir()
    if not base.is_dir():
        return []
    found = [child for child in base.iterdir() if _is_model_folder(child) and re.search(r"qwen.*vl", child.name, re.I)]
    return sorted(found, key=lambda path: path.name.lower())


def _auto_detect() -> Optional[Path]:
    """The default when no model was named: Qwen3-VL-4B-Instruct if present, else an Instruct model, else the first."""
    models = list_local_models()
    if not models:
        return None
    default_name = DEFAULT_MODEL_ID.rsplit("/", 1)[-1].lower()
    for wanted in (lambda p: p.name.lower() == default_name,
                   lambda p: "instruct" in p.name.lower() and "thinking" not in p.name.lower(),
                   lambda p: True):
        for path in models:
            if wanted(path):
                return path
    return None


def _find_local(name: str) -> Optional[Path]:
    """A folder under models/VLM by name: exact, 'org_name' (how some nodes save 'org/name'), or case-insensitive."""
    base = vlm_dir()
    short = name.rsplit("/", 1)[-1]
    candidates = [name.replace("/", os.sep), short, name.replace("/", "_")]
    # By folder listing first, so the path comes back in the folder's real spelling (Windows would accept any case)
    lowered = {candidate.lower() for candidate in candidates}
    if base.is_dir():
        for child in sorted(base.iterdir(), key=lambda path: path.name.lower()):
            if child.name.lower() in lowered and _is_model_folder(child):
                return child
    for candidate in candidates:            # a nested folder such as Qwen/Qwen3-VL-8B-Instruct
        path = base / candidate
        if _is_model_folder(path):
            return path
    return None


def resolve_model_spec(spec: Optional[str]) -> Tuple[str, List[str], bool]:
    """
    Turn whatever arrived in a node's model / endpoint field into a model folder.

    Returns (folder or repo id, notes for the log, needs_download). Accepted, in this order:
      - nothing, "default", the default repo id, or a URL (the field doubles as the LM Studio endpoint)
        -> auto-detect in models/VLM
      - an existing folder (with or without the old "local:" prefix)
      - a folder NAME under models/VLM, e.g. Qwen3-VL-8B-Instruct
      - an explicit org/name repository id: the local copy if there is one, otherwise - and only then - a download
      - anything else (a stray value from an old workflow, such as "1") is ignored with a note -> auto-detect
    Raises Qwen3VLError when no local model can be found; it never falls back to downloading the default.
    """
    notes: List[str] = []
    text = (spec or "").strip()
    if text.lower().startswith("local:"):
        text = text.split(":", 1)[1].strip()
    text = os.path.expanduser(text.strip().strip('"'))

    if text and "://" not in text and text.lower() not in DEFAULT_SPECS:
        folder = Path(text)
        if _is_model_folder(folder):
            return str(folder), notes, False
        if folder.is_dir():
            raise Qwen3VLError(f"'{folder}' is a folder but holds no config.json, so it is not a model folder.")
        local = _find_local(text)
        if local is not None:
            return str(local), notes, False
        if REPO_ID.match(text):
            notes.append(f"'{text}' is not in {vlm_dir()}; downloading it because it was named explicitly")
            return text, notes, True
        notes.append(f"ignored the model field value '{text}': not a folder, not a model in {vlm_dir()}, not an org/name id")

    detected = _auto_detect()
    if detected is not None:
        notes.append(f"using local model {detected.name}")
        return str(detected), notes, False

    present = ", ".join(path.name for path in list_local_models()) or "none"
    raise Qwen3VLError(
        f"No local Qwen VL model found in {vlm_dir()} (found: {present}). Nothing is downloaded automatically. "
        f"Put a model folder there, give a full folder path in the node's endpoint / model field, or type an explicit "
        f"repository id such as {DEFAULT_MODEL_ID} in that field to download it."
    )


def _resolve_model_path(model_id: str) -> str:
    target, notes, needs_download = resolve_model_spec(model_id)
    for note in notes:
        print(f"[Qwen3-VL Backend] {note}")
    if not needs_download:
        return target

    if snapshot_download is None:
        raise Qwen3VLError("huggingface_hub is required to download '{}'".format(target))
    base = vlm_dir()
    base.mkdir(parents=True, exist_ok=True)
    # Match Granddyser node behavior: the folder is the model name (after the last slash)
    local_dir = base / target.rsplit("/", 1)[-1]
    snapshot_download(repo_id=target, local_dir=str(local_dir), local_dir_use_symlinks=False)
    return str(local_dir)


def _cache_key(config: "Qwen3VLConfig", model_path: str) -> "Qwen3VLConfig":
    """One cache entry per model FOLDER, however it was named ('Qwen/...', a bare name, a full path)."""
    return replace(config, model_id=os.path.normcase(os.path.abspath(model_path)))


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
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate text using Qwen3-VL model (no image input - pure text generation).
    
    Parameters
    ----------
    prompt:
        The user turn.
    system_prompt:
        Optional system turn. Long instructions belong here, not glued in front of the user's text.
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
        config = _parse_config(model_spec, backend_hint)
        state = _get_or_load_model(config)
        
        model = state["model"]
        processor = state["processor"]
        device = _resolve_model_device(model)
        
        # Format as text-only conversation
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})
        messages += [
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
        
        response_text = response_text.strip()
        if "</think>" in response_text:          # Thinking variants: keep the answer, drop the reasoning
            response_text = response_text.split("</think>")[-1].strip()

        return {
            "success": True,
            "response": response_text,
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
