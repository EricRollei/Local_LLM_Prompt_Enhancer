"""
Text embedders for the variability engine. One small interface, several backends.

    embedder.name            stable id, used as the cache key ("qwen3vl-2b", "openclip-ViT-H-14", ...)
    embedder.encode(texts)   -> float32 array [len(texts), dim], rows L2-normalised

Which space you embed in decides what "similar" means:
    qwen3vl     Qwen3-VL-Embedding. Text embedded in a space trained jointly with images, so
                neighbours are close in meaning AND in what they look like. Best default.
    openclip    CLIP text tower. Neighbours LOOK alike ("rusty" ~ "weathered copper").
    comfy_clip  The CLIP already loaded in your ComfyUI graph (pooled output). No extra model.
    sentence    Any sentence-transformers model. Neighbours MEAN alike.
    lexical     Character n-gram hashing. No model, no meaning - spelling similarity only.
                For tests and as a last resort so the node still runs with nothing installed.

Models load lazily on first encode() and stay loaded for the session.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from typing import Any, List, Optional

import numpy as np

BATCH_SIZE = 64


def _normalise(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class Embedder:
    name = "base"

    def encode(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError

    def describe(self) -> str:
        return self.name


class LexicalEmbedder(Embedder):
    """Hashed character trigrams. Deterministic, dependency-free, NOT semantic."""

    name = "lexical-256"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def encode(self, texts: List[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            padded = f"  {text.lower().strip()}  "
            for index in range(len(padded) - 2):
                digest = hashlib.md5(padded[index:index + 3].encode("utf-8")).digest()
                matrix[row, int.from_bytes(digest[:4], "little") % self.dim] += 1.0
        return _normalise(matrix)

    def describe(self) -> str:
        return "lexical (spelling similarity only - no model found)"


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name_or_path: str, device: Optional[str] = None):
        self.model_name_or_path = model_name_or_path
        self.device = device
        self.name = "sentence-" + os.path.basename(os.path.normpath(model_name_or_path)).lower()
        self._model = None

    def encode(self, texts: List[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name_or_path, device=self.device)
        vectors = self._model.encode(texts, batch_size=BATCH_SIZE, convert_to_numpy=True,
                                     normalize_embeddings=True, show_progress_bar=False)
        return _normalise(vectors)


class OpenClipEmbedder(Embedder):
    """
    CLIP text tower through open_clip.
    `source` is a local model folder that contains open_clip_config.json (loaded with open_clip's
    "local-dir:" scheme), or an "architecture|pretrained-tag" pair such as "ViT-H-14|laion2b_s32b_b79k".
    """

    def __init__(self, source: str, device: Optional[str] = None):
        self.source = source
        self.device = device
        label = os.path.basename(os.path.normpath(source)) if os.path.isdir(source) else source.replace("|", "-")
        self.name = "openclip-" + label.lower()
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        import open_clip
        import torch
        if os.path.isdir(self.source):
            model_name = "local-dir:" + self.source
            model, _, _ = open_clip.create_model_and_transforms(model_name)
            self._tokenizer = open_clip.get_tokenizer(model_name)
        else:
            architecture, _, pretrained = self.source.partition("|")
            model, _, _ = open_clip.create_model_and_transforms(architecture, pretrained=pretrained or None)
            self._tokenizer = open_clip.get_tokenizer(architecture)
        self.device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = model.to(self.device).eval()

    def encode(self, texts: List[str]) -> np.ndarray:
        import torch
        if self._model is None:
            self._load()
        chunks = []
        with torch.no_grad():
            for start in range(0, len(texts), BATCH_SIZE):
                tokens = self._tokenizer(texts[start:start + BATCH_SIZE]).to(self.device)
                chunks.append(self._model.encode_text(tokens).float().cpu().numpy())
        return _normalise(np.concatenate(chunks, axis=0))


class Qwen3VLEmbedder(Embedder):
    """
    Qwen3-VL-Embedding through the loader class in Eric's eric_semantic_search package
    (core/qwen3_vl_embedding.py, class Qwen3VLEmbedder). That file has no package-relative
    imports, so it is loaded by path; nothing in eric_semantic_search is modified or started.
    """

    INSTRUCTION = "Represent this phrase from an image generation prompt for finding visually and semantically similar phrases."

    def __init__(self, model_path: str, loader_file: str, device: Optional[str] = None):
        self.model_path = model_path
        self.loader_file = loader_file
        self.device = device            # e.g. "cuda:1" or "cpu"; None = wherever the loader puts it (cuda:0)
        self.name = "qwen3vl-" + os.path.basename(os.path.normpath(model_path)).lower()
        self._embedder: Any = None

    def _load(self) -> None:
        module_name = "vp_qwen3_vl_embedding"
        module = sys.modules.get(module_name)
        if module is None:
            spec = importlib.util.spec_from_file_location(module_name, self.loader_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        self._embedder = module.Qwen3VLEmbedder(self.model_path)
        if self.device:
            # The loader always picks "cuda" (= cuda:0). It keeps the device in .device and sends its
            # inputs there, so moving the model and updating that attribute is all a relocation takes.
            import torch
            target = torch.device(self.device)
            self._embedder.model.to(target)
            self._embedder.device = target

    def describe(self) -> str:
        where = self.device or "cuda:0 (loader default)"
        return f"{self.name} on {where}"

    def encode(self, texts: List[str]) -> np.ndarray:
        if self._embedder is None:
            self._load()
        chunks = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = [{"text": text, "instruction": self.INSTRUCTION} for text in texts[start:start + BATCH_SIZE]]
            vectors = self._embedder.process(batch, normalize=True)
            chunks.append(vectors.float().cpu().numpy())
        return _normalise(np.concatenate(chunks, axis=0))


class ComfyClipEmbedder(Embedder):
    """Pooled text output of a CLIP object from the ComfyUI graph. Needs an encoder that has a pooled output."""

    def __init__(self, clip: Any, label: str = "graph"):
        self.clip = clip
        self.name = "comfyclip-" + label

    def encode(self, texts: List[str]) -> np.ndarray:
        rows = []
        for text in texts:
            tokens = self.clip.tokenize(text)
            _conditioning, pooled = self.clip.encode_from_tokens(tokens, return_pooled=True)
            if pooled is None:
                raise RuntimeError("this text encoder has no pooled output; connect a CLIP-L/G encoder or pick another embedder")
            rows.append(pooled.float().reshape(-1).cpu().numpy())
        return _normalise(np.stack(rows, axis=0))


def clip_label(clip: Any) -> str:
    """A stable-enough id for a graph CLIP so its cache is not mixed with another encoder's."""
    try:
        inner = getattr(clip, "cond_stage_model", None)
        parts = [type(inner).__name__] + sorted(name for name in dir(inner) if name.startswith("clip_"))
        return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()[:8]
    except Exception:
        return "graph"
