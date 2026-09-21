"""
Variability support for the ComfyUI nodes: finds an embedding model on this machine and hands
out one shared SemanticVariator per embedder, so models and vector caches load once per session.

Embedder choice ("auto" tries them in this order and takes the first that is available):
    graph_clip  the CLIP connected to the node's `clip` input (pooled output; CLIP-L/G style encoders)
    qwen3vl     Qwen3-VL-Embedding, through the loader in a sibling eric_semantic_search package.
                Model folder is found the same way that package finds it:
                env SEMANTIC_SEARCH_MODEL_PATH -> its user_settings.json "model_path" -> ComfyUI/models/Qwen
                (the 2B model is preferred over the 8B: phrases are short, 2B is plenty and much faster)
    openclip    a local open_clip model folder (one containing open_clip_config.json) under ComfyUI's
                text_encoders / clip folders
    sentence    a sentence-transformers model named in config.json
    lexical     no model: spelling similarity only. Always available, never chosen silently -
                the node's report says so.

Everything can be pinned in this package's config.json:
    "variability": {
        "embedder": "auto",
        "qwen3vl_model": "H:/semantic_search/models/Qwen3-VL-Embedding-2B",
        "qwen3vl_loader": "<...>/eric_semantic_search/core/qwen3_vl_embedding.py",
        "openclip_model": "A:/Models/text_encoders/CLIP-ViT-H-14-laion2B-s32B-b79K",
        "sentence_model": "sentence-transformers/all-MiniLM-L6-v2",
        "device": "cuda:1"
    }
"device" applies to qwen3vl. Left out, the model goes where eric_semantic_search's loader puts it:
torch's "cuda", which is cuda:0 of the ComfyUI process - the same card ComfyUI itself uses unless
you start it with --cuda-device. The 2B model takes about 4.5 GB in bfloat16.

Vector caches and the repulsion memory live in <package>/cache/ (git-ignored).

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from .core.variability import (
    NO_DIRECTION,
    ComfyClipEmbedder,
    DirectionAxis,
    Embedder,
    LexicalEmbedder,
    OpenClipEmbedder,
    Qwen3VLEmbedder,
    SemanticVariator,
    SentenceTransformerEmbedder,
    clip_label,
    load_directions,
)
from .wildcard_support import get_wildcard_engine

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_NODES_DIR = os.path.dirname(PACKAGE_DIR)
CACHE_DIR = os.path.join(PACKAGE_DIR, "cache")
CONFIG_PATH = os.path.join(PACKAGE_DIR, "config.json")

EMBEDDER_CHOICES = ["auto", "qwen3vl", "openclip", "graph_clip", "sentence", "lexical"]
DIRECTION_FILES = [
    os.path.join(PACKAGE_DIR, "variability", "directions.yaml"),
    os.path.join(PACKAGE_DIR, "variability", "directions_user.yaml"),    # yours; same name replaces a shipped axis
]


def direction_axes() -> Dict[str, DirectionAxis]:
    return load_directions(DIRECTION_FILES)


def direction_choices() -> List[str]:
    """Dropdown values: "none" first, then the shipped axes in file order, then the user's."""
    return [NO_DIRECTION] + list(direction_axes().keys())
QWEN_MODEL_FOLDERS = ["Qwen3-VL-Embedding-2B", "Qwen3-VL-Embedding-8B"]

_EMBEDDERS: Dict[str, Embedder] = {}
_VARIATORS: Dict[Tuple[str, Tuple[str, ...]], SemanticVariator] = {}


def _settings() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            section = json.load(handle).get("variability", {})
        return section if isinstance(section, dict) else {}
    except (OSError, ValueError):
        return {}


def _find_qwen3vl(settings: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """(model folder, loader file) for Qwen3-VL-Embedding, or None."""
    semantic_search_dir = os.path.join(CUSTOM_NODES_DIR, "eric_semantic_search")
    loader = settings.get("qwen3vl_loader") or os.path.join(semantic_search_dir, "core", "qwen3_vl_embedding.py")
    if not os.path.isfile(loader):
        return None

    pinned = settings.get("qwen3vl_model")
    if pinned:
        return (pinned, loader) if os.path.isdir(pinned) else None

    roots: List[str] = []
    if os.environ.get("SEMANTIC_SEARCH_MODEL_PATH"):
        roots.append(os.environ["SEMANTIC_SEARCH_MODEL_PATH"])
    try:
        with open(os.path.join(semantic_search_dir, "user_settings.json"), "r", encoding="utf-8") as handle:
            model_path = json.load(handle).get("model_path")
        if model_path:
            roots.append(model_path)
    except (OSError, ValueError):
        pass
    try:
        import folder_paths
        roots.append(os.path.join(folder_paths.models_dir, "Qwen"))
    except ImportError:
        pass

    for root in roots:
        for folder in QWEN_MODEL_FOLDERS:
            candidate = os.path.join(root, folder)
            if os.path.isfile(os.path.join(candidate, "config.json")):
                return candidate, loader
    return None


def _find_openclip(settings: Dict[str, Any]) -> Optional[str]:
    pinned = settings.get("openclip_model")
    if pinned:
        return pinned if (os.path.isdir(pinned) or "|" in pinned) else None
    try:
        import folder_paths
    except ImportError:
        return None
    roots: List[str] = []
    for folder_name in ("text_encoders", "clip"):
        try:
            roots.extend(folder_paths.get_folder_paths(folder_name))
        except Exception:
            pass
    for root in dict.fromkeys(roots):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            candidate = os.path.join(root, name)
            if os.path.isfile(os.path.join(candidate, "open_clip_config.json")):
                return candidate
    return None


def available_embedders(clip: Any = None) -> Dict[str, str]:
    """{choice: where it would load from} for every embedder usable right now. For reports and diagnostics."""
    settings = _settings()
    found: Dict[str, str] = {}
    if clip is not None:
        found["graph_clip"] = "the CLIP connected to this node"
    qwen = _find_qwen3vl(settings)
    if qwen:
        found["qwen3vl"] = qwen[0]
    openclip = _find_openclip(settings)
    if openclip:
        found["openclip"] = openclip
    if settings.get("sentence_model"):
        found["sentence"] = str(settings["sentence_model"])
    found["lexical"] = "built in (spelling similarity only)"
    return found


def get_embedder(choice: str = "auto", clip: Any = None) -> Tuple[Embedder, List[str]]:
    """Returns (embedder, notes). Falls back down the list rather than failing; notes say what happened."""
    settings = _settings()
    notes: List[str] = []
    choice = (choice or "auto").strip().lower()
    if choice == "auto":
        choice = str(settings.get("embedder", "auto")).strip().lower()
    order = ["graph_clip", "qwen3vl", "openclip", "sentence", "lexical"] if choice == "auto" else [choice, "lexical"]

    for name in order:
        if name == "graph_clip" and clip is not None:
            return ComfyClipEmbedder(clip, clip_label(clip)), notes   # holds a graph object: never cached
        if name == "graph_clip" and choice == "graph_clip":
            notes.append("graph_clip was chosen but nothing is connected to `clip`")
        if name == "qwen3vl":
            location = _find_qwen3vl(settings)
            if location:
                key = "qwen3vl|" + location[0]
                if key not in _EMBEDDERS:
                    _EMBEDDERS[key] = Qwen3VLEmbedder(location[0], location[1], device=settings.get("device") or None)
                return _EMBEDDERS[key], notes
            if choice == "qwen3vl":
                notes.append("qwen3vl was chosen but no Qwen3-VL-Embedding model or eric_semantic_search loader was found")
        if name == "openclip":
            source = _find_openclip(settings)
            if source:
                key = "openclip|" + source
                if key not in _EMBEDDERS:
                    _EMBEDDERS[key] = OpenClipEmbedder(source)
                return _EMBEDDERS[key], notes
            if choice == "openclip":
                notes.append("openclip was chosen but no folder with open_clip_config.json was found")
        if name == "sentence":
            model = settings.get("sentence_model")
            if model:
                key = "sentence|" + str(model)
                if key not in _EMBEDDERS:
                    _EMBEDDERS[key] = SentenceTransformerEmbedder(str(model))
                return _EMBEDDERS[key], notes
            if choice == "sentence":
                notes.append('sentence was chosen but config.json has no "variability": {"sentence_model": ...}')
        if name == "lexical":
            if choice != "lexical":
                notes.append("NO EMBEDDING MODEL AVAILABLE - using spelling similarity, which is not semantic")
            if "lexical" not in _EMBEDDERS:
                _EMBEDDERS["lexical"] = LexicalEmbedder()
            return _EMBEDDERS["lexical"], notes

    return LexicalEmbedder(), notes


def get_variator(embedder: Embedder, extra_paths: Optional[List[str]] = None) -> SemanticVariator:
    engine = get_wildcard_engine(extra_paths)
    if isinstance(embedder, ComfyClipEmbedder):
        return SemanticVariator(engine, embedder, CACHE_DIR, direction_axes())   # vectors still cached on disk by encoder id
    key = (embedder.name, tuple(engine.library.search_paths))
    variator = _VARIATORS.get(key)
    if variator is None or variator.embedder is not embedder:
        variator = SemanticVariator(engine, embedder, CACHE_DIR, direction_axes())
        _VARIATORS[key] = variator
    else:
        axes = direction_axes()                       # pick up edits to the YAML without a restart
        if {name: (axis.start, axis.end) for name, axis in axes.items()} != \
           {name: (axis.start, axis.end) for name, axis in variator.directions.items()}:
            variator.directions = axes
            variator._direction_vectors.clear()
    return variator
