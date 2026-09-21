"""
Ideogram 4 Magic Prompt - core engine.

Expands a plain-language idea into an Ideogram 4 structured caption (JSON string)
using a local LLM via the existing LLMBackend, driven by Ideogram's *official*
open-source magic-prompt system prompt (v1.txt).

Provenance:
  The system prompt file (v1.txt) is Ideogram's open-source magic-prompt prompt,
  Apache-2.0, from https://github.com/ideogram-oss/ideogram4
  (src/ideogram4/magic_prompt_system_prompts/v1.txt). It is downloaded and cached
  on first use (or place it manually - see ensure_official_prompt). Integration
  code (c) Eric Hiss. See IDEOGRAM_NOTES.md for schema + tailoring rationale.

Mechanics mirror Ideogram's magic_prompt.py: parse [SYSTEM]/[USER] sections, fill
the user template, call the model, strip code fences, reorder keys to the canonical
schema order, drop the top-level aspect_ratio (dims are passed separately), and
optionally strip bboxes.
"""

from __future__ import annotations
import json
import os
import math
import urllib.request
from functools import lru_cache

from .llm_backend import LLMBackend

THIS_DIR = os.path.dirname(__file__)
PROMPT_DIR = os.path.join(THIS_DIR, "ideogram_prompts")
OFFICIAL_PATH = os.path.join(PROMPT_DIR, "v1_official.txt")
TAILORING_PATH = os.path.join(PROMPT_DIR, "v1_tailoring.txt")
OFFICIAL_URL = (
    "https://raw.githubusercontent.com/ideogram-oss/ideogram4/main/"
    "src/ideogram4/magic_prompt_system_prompts/v1.txt"
)

# Canonical key orders (from the Ideogram caption schema / prompting.md).
TOP_ORDER = ["aspect_ratio", "high_level_description", "style_description",
             "compositional_deconstruction"]
CD_ORDER = ["background", "elements"]
STYLE_PHOTO = ["aesthetics", "lighting", "photo", "medium", "color_palette"]
STYLE_ART = ["aesthetics", "lighting", "medium", "art_style", "color_palette"]
OBJ_ORDER = ["type", "bbox", "desc", "color_palette"]
TEXT_ORDER = ["type", "bbox", "text", "desc", "color_palette"]


def ensure_official_prompt() -> str:
    """Return the path to the cached official v1.txt, downloading it on first use."""
    os.makedirs(PROMPT_DIR, exist_ok=True)
    if os.path.isfile(OFFICIAL_PATH) and os.path.getsize(OFFICIAL_PATH) > 1000:
        return OFFICIAL_PATH
    try:
        req = urllib.request.Request(OFFICIAL_URL, headers={"User-Agent": "comfyui-ideogram-magic"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode("utf-8")
        if "[SYSTEM]" not in data:
            raise ValueError("downloaded file is missing the [SYSTEM] section")
        with open(OFFICIAL_PATH, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"[Ideogram Magic] Cached official system prompt -> {OFFICIAL_PATH}")
        return OFFICIAL_PATH
    except Exception as e:
        raise RuntimeError(
            f"Could not download Ideogram's official magic-prompt v1.txt ({e}). "
            f"Place it manually at:\n  {OFFICIAL_PATH}\nSource: {OFFICIAL_URL}"
        )


@lru_cache(maxsize=8)
def _load_sections_cached(path: str, mtime: float) -> dict:
    raw = open(path, encoding="utf-8").read()
    sections, current, lines = {}, None, []
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]") and " " not in s:
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current = s[1:-1].lower()
            lines = []
        else:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def load_sections(path: str) -> dict:
    return _load_sections_cached(path, os.path.getmtime(path))


def _strip_fences(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json(text: str) -> dict:
    text = _strip_fences(text)
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object found in model output")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON in model output")


def _ordered(d: dict, order: list) -> dict:
    known = [k for k in order if k in d]
    extra = [k for k in d if k not in order]
    return {k: d[k] for k in (*known, *extra)}


def reorder(caption: dict) -> dict:
    """Reorder caption keys to canonical schema order (CaptionVerifier-friendly)."""
    if not isinstance(caption, dict):
        return caption
    sd = caption.get("style_description")
    if isinstance(sd, dict):
        order = STYLE_PHOTO if "photo" in sd else (STYLE_ART if "art_style" in sd else STYLE_PHOTO)
        caption["style_description"] = _ordered(sd, order)
    cd = caption.get("compositional_deconstruction")
    if isinstance(cd, dict):
        cd = _ordered(cd, CD_ORDER)
        els = cd.get("elements")
        if isinstance(els, list):
            cd["elements"] = [
                _ordered(e, TEXT_ORDER if e.get("type") == "text" else OBJ_ORDER)
                if isinstance(e, dict) else e
                for e in els
            ]
        caption["compositional_deconstruction"] = cd
    return _ordered(caption, TOP_ORDER)


def aspect_to_dims(aspect: str, megapixels: float):
    try:
        a, b = aspect.split(":")
        w, h = float(a), float(b)
        if w <= 0 or h <= 0:
            raise ValueError
    except Exception:
        w = h = 1.0
    k = math.sqrt((megapixels * 1e6) / (w * h))
    r16 = lambda x: max(256, min(2048, int(round(x / 16) * 16)))
    return r16(w * k), r16(h * k)


def _quick_verify(cap: dict) -> list:
    """Light guideline check echoing the official prompt's hard caps."""
    warns = []
    hl = cap.get("high_level_description") or ""
    if len(hl.split()) > 50:
        warns.append(f"high_level_description is {len(hl.split())} words (>50 cap)")
    cd = cap.get("compositional_deconstruction", {})
    if "background" not in cd:
        warns.append("missing compositional_deconstruction.background")
    if "elements" not in cd:
        warns.append("missing compositional_deconstruction.elements")
    for i, e in enumerate(cd.get("elements", []) or []):
        if isinstance(e, dict) and len((e.get("desc") or "").split()) > 60:
            warns.append(f"element {i} desc is {len(e['desc'].split())} words (>60 cap)")
    return warns


def expand(idea: str, *, backend: str = "lm_studio",
           endpoint: str = "http://localhost:1234/v1", model: str = "",
           temperature: float = 1.0, aspect_ratio: str = "1:1",
           megapixels: float = 1.0, keep_bboxes: bool = True,
           use_tailoring: bool = True, max_tokens: int = 16384,
           reference_caption: str = "", application: str = "",
           extra_system: str = "") -> dict:
    """Expand a plain idea into an Ideogram 4 caption. Returns a result dict.

    extra_system: optional text appended to the system prompt after the tailoring file. Used for
    the wildcard selected-elements block; it goes in SYSTEM, not in the idea, so Ideogram's
    rewriter never mistakes the instruction for text to render in the image.
    """
    path = ensure_official_prompt()
    sections = load_sections(path)
    system = sections.get("system", "")
    if not system:
        return {"ok": False, "error": "official v1.txt has no [SYSTEM] section",
                "prompt_json": "", "high_level": "", "width": 0, "height": 0}

    if use_tailoring and os.path.isfile(TAILORING_PATH):
        tail = open(TAILORING_PATH, encoding="utf-8").read().strip()
        if tail:
            system = f"{system}\n\n{tail}"

    if extra_system and extra_system.strip():
        system = f"{system}\n\n{extra_system.strip()}"

    user_t = sections.get(
        "user",
        "TARGET IMAGE ASPECT RATIO: {{aspect_ratio}} (width:height).\nUser idea: {{original_prompt}}",
    )
    idea_full = idea.strip()
    if reference_caption.strip():
        idea_full = f"{idea_full}\n\nReference image (use as visual guidance): {reference_caption.strip()}"
    user = user_t.replace("{{aspect_ratio}}", aspect_ratio).replace("{{original_prompt}}", idea_full)
    if application and application not in ("", "(custom)"):
        user = (f"Intended application: {application}. Follow that format's conventions "
                f"for medium, layout, typography hierarchy, and palette.\n\n{user}")

    try:
        be = LLMBackend(backend, endpoint, model or None, temperature)
        res = be.send_prompt(system, user, max_tokens=max_tokens)
    except Exception as e:
        return {"ok": False, "error": f"backend error: {e}",
                "prompt_json": "", "high_level": "", "width": 0, "height": 0}

    if not res.get("success"):
        return {"ok": False, "error": res.get("error", "LLM call failed"),
                "prompt_json": "", "high_level": "", "width": 0, "height": 0}

    try:
        cap = _extract_json(res["response"])
    except Exception as e:
        return {"ok": False, "error": f"could not parse model JSON: {e}",
                "prompt_json": (res.get("response") or "")[:2000],
                "high_level": "", "width": 0, "height": 0}

    committed = cap.get("aspect_ratio") if isinstance(cap.get("aspect_ratio"), str) else aspect_ratio
    if not committed or committed.lower() == "auto":
        committed = aspect_ratio if aspect_ratio.lower() != "auto" else "1:1"

    cap = reorder(cap)
    cap.pop("aspect_ratio", None)  # dims passed separately (open-weight schema)
    if not keep_bboxes:
        for e in cap.get("compositional_deconstruction", {}).get("elements", []) or []:
            if isinstance(e, dict):
                e.pop("bbox", None)

    high = cap.get("high_level_description", "")
    out_json = json.dumps(cap, ensure_ascii=False, separators=(",", ":"))
    w, h = aspect_to_dims(committed, megapixels)
    return {"ok": True, "error": "", "prompt_json": out_json, "high_level": high,
            "width": w, "height": h, "aspect": committed, "warnings": _quick_verify(cap)}
