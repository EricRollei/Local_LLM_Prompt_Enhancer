"""
Official rewriter prompts: fetch once, cache, tailor in the open.

Several labs publish the system prompt their own prompt rewriter uses (Wan, LTX, Qwen-Image,
FLUX.2, Krea 2, Hunyuan, Ideogram, MiniMax H3). Those are the best available description of what
each model was trained to read, so a profile can point at one and the rewriter will use it as
the base of its system prompt - the same design as the Ideogram Magic Prompt node.

Nothing is shipped or redistributed: each file is downloaded from the vendor's repository the
first time it is needed and kept in <package>/cache/official_prompts/<profile id>/. To work
offline, put the file there yourself under the name shown in the node's notes output.

Three file shapes are understood:
    text         the whole file is the prompt
    python_var   a .py file; the prompt is a string assigned to `variable` (read with ast, never executed)
    sections     an Ideogram-style file with [SYSTEM] / [USER] headers; `variable` names the section

Tailoring is explicit and logged: `drop_lines` regexes remove matching lines (used to take the
vendor's content-moderation rules out of Wan's rewriter, which would otherwise silently replace
the user's prompt), and every removal is reported in the notes.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .schema import OfficialPrompt, Profile

FETCH_TIMEOUT_SECONDS = 15
MIN_PROMPT_CHARS = 200
USER_AGENT = "comfyui-video-prompter-profiles"

AUTO_MAX_CHARS = 30000      # in auto mode, longer vendor prompts are skipped: they overflow small LLM contexts

MODE_AUTO = "auto"          # use the vendor prompt when the profile has one and it is not huge; download once
MODE_ON = "on"              # use it whatever its size
MODE_OFF = "off"            # never; always build the instructions from the profile's own fields
MODE_REFRESH = "refresh"    # like on, but download again first, replacing the cached copy
MODES = (MODE_AUTO, MODE_ON, MODE_OFF, MODE_REFRESH)


RETRY_AFTER_SECONDS = 600   # after a failed download, do not try that URL again for ten minutes
_FAILED_AT: Dict[str, float] = {}


@dataclass
class OfficialResult:
    text: str = ""
    used: bool = False
    notes: List[str] = field(default_factory=list)
    cache_file: str = ""


def cache_name(entry: OfficialPrompt) -> str:
    """Readable, collision-free file name for a URL."""
    base = os.path.basename(entry.url.split("?")[0]) or "prompt.txt"
    digest = hashlib.sha1(entry.url.encode("utf-8")).hexdigest()[:8]
    stem, extension = os.path.splitext(base)
    return f"{stem}.{digest}{extension or '.txt'}"


def _download(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8")


def _string_assigned(body: list, variable: str) -> Optional[str]:
    for node in body:
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            targets = [node.target.id]
            value = node.value
        else:
            continue
        if variable in targets:
            try:
                literal = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return None
            return literal if isinstance(literal, str) else None
    return None


def extract_python_string(source: str, variable: str) -> Optional[str]:
    """
    The string literal assigned to `variable`. The file is parsed with ast, never run.
    "NAME" looks at module level; "function.NAME" looks inside that function, which is where
    Qwen-Image keeps its prompts (polish_prompt_en.SYSTEM_PROMPT).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    function_name, _, name = variable.rpartition(".")
    if not function_name:
        return _string_assigned(tree.body, name)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return _string_assigned([child for child in ast.walk(node)], name)
    return None


def extract_section(source: str, section: str) -> Optional[str]:
    """[SYSTEM] ... [USER] ... files, as used by Ideogram's magic prompt."""
    wanted = (section or "system").lower()
    sections: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and " " not in stripped:
            current = stripped[1:-1].lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    if wanted not in sections:
        return None
    return "\n".join(sections[wanted]).strip()


def _extract(entry: OfficialPrompt, source: str) -> Optional[str]:
    if entry.format == "python_var":
        return extract_python_string(source, entry.variable)
    if entry.format == "sections":
        return extract_section(source, entry.variable)
    return source.strip()


def _drop_lines(text: str, patterns: List[str], notes: List[str]) -> str:
    if not patterns:
        return text
    compiled = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as error:
            notes.append(f"tailoring pattern {pattern!r} is not a valid regex ({error}); ignored")
    kept: List[str] = []
    removed = 0
    for line in text.splitlines():
        if any(regex.search(line) for regex in compiled):
            removed += 1
            continue
        kept.append(line)
    if removed:
        notes.append(f"tailoring: removed {removed} line(s) from the official prompt (see the profile's drop_lines)")
    return "\n".join(kept)


def load_official(profile: Profile, task: str, cache_dir: str, mode: str = MODE_AUTO) -> OfficialResult:
    """
    The vendor's rewriter prompt for this profile and task, or an empty result.
    Never raises: a missing network, a moved file or a changed variable name all come back as a
    note, and the caller falls back to the prompt built from the profile's own fields.
    """
    result = OfficialResult()
    if mode == MODE_OFF:
        return result
    entry = profile.official_for(task)
    if entry is None:
        return result

    folder = os.path.join(cache_dir, "official_prompts", profile.id)
    path = os.path.join(folder, cache_name(entry))
    result.cache_file = path

    source: Optional[str] = None
    if mode != MODE_REFRESH and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                source = handle.read()
        except OSError as error:
            result.notes.append(f"cached official prompt unreadable ({error})")

    if source is None:
        failed_at = _FAILED_AT.get(entry.url)
        if failed_at is not None and mode != MODE_REFRESH and time.time() - failed_at < RETRY_AFTER_SECONDS:
            result.notes.append(f"official prompt could not be downloaded a moment ago; using the built-in rules. Offline: save {entry.url} as {path}")
            return result
        try:
            source = _download(entry.url)
            os.makedirs(folder, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(source)
            result.notes.append(f"official prompt downloaded and cached: {path}")
        except Exception as error:
            _FAILED_AT[entry.url] = time.time()
            result.notes.append(
                f"official prompt not available ({error}); using the built-in rules. "
                f"To use it offline save {entry.url} as {path}"
            )
            return result

    text = _extract(entry, source)
    if not text or len(text) < MIN_PROMPT_CHARS:
        where = f"variable {entry.variable}" if entry.format == "python_var" else f"format {entry.format}"
        result.notes.append(f"official prompt file changed shape ({where} not found in {path}); using the built-in rules")
        return result

    if mode == MODE_AUTO and len(text) > AUTO_MAX_CHARS:
        result.notes.append(
            f"the official prompt is {len(text):,} characters, too long for a small LLM context, so the built-in "
            f"rules were used. Set official_prompt to 'on' to use it anyway (needs a context of 12k tokens or more)."
        )
        return result

    result.text = _drop_lines(text, entry.drop_lines, result.notes)
    if entry.preamble:
        result.text = f"{entry.preamble}\n\n{result.text}"
    result.used = True
    result.notes.append(f"base: official {profile.developer or profile.name} rewriter prompt ({entry.url})")
    if entry.note:
        result.notes.append(entry.note)
    return result
