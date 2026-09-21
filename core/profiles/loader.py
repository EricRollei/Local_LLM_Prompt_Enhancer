"""
ProfileLibrary: reads platform profiles (*.yaml) from one or more folders.

Search folders, highest priority first. When an id exists in several folders the first folder
wins, so a copy in your own folder replaces the shipped profile without editing the package:
    1. extra paths passed by the caller
    2. "profile_paths" in <package>/config.json
    3. <package>/profiles_user/        your own and your edited profiles (not shipped, not overwritten by updates)
    4. <package>/profiles/             profiles that ship with the package

Files whose name starts with "_" are skipped (notes, templates). A broken file never stops the
others from loading; the problem is kept in .warnings. Files are re-read when their mtime changes.

`extends: other_id` inherits from another profile: dictionaries merge key by key, everything
else (strings, numbers, lists) is replaced by the child's value.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .schema import Profile, profile_from_dict

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILTIN_PROFILE_DIR = os.path.join(PACKAGE_DIR, "profiles")
USER_PROFILE_DIR = os.path.join(PACKAGE_DIR, "profiles_user")
CONFIG_PATH = os.path.join(PACKAGE_DIR, "config.json")

MAX_EXTENDS_DEPTH = 5


def configured_paths() -> List[str]:
    """Extra profile folders from config.json -> "profile_paths": ["D:/my_profiles", ...]."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            paths = json.load(handle).get("profile_paths", [])
    except (OSError, ValueError):
        return []
    if isinstance(paths, str):
        paths = [paths]
    return [str(path) for path in paths if path]


def _deep_merge(parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(parent)
    for key, value in child.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: str) -> Any:
    import yaml  # PyYAML ships with ComfyUI
    with open(path, "r", encoding="utf-8-sig") as handle:
        return yaml.safe_load(handle)


class ProfileLibrary:
    def __init__(self, search_paths: Iterable[str]):
        self.search_paths: List[str] = []
        for path in search_paths:
            absolute = os.path.abspath(path)
            if absolute not in self.search_paths:
                self.search_paths.append(absolute)
        self.warnings: List[str] = []
        self._profiles: Dict[str, Profile] = {}
        self._order: List[str] = []
        self._stamp: Tuple[Tuple[str, float], ...] = ()
        self.shadowed: Dict[str, List[str]] = {}     # id -> files that lost to an earlier folder

    # -- scanning ----------------------------------------------------------------------
    def _files(self) -> List[str]:
        found: List[str] = []
        for folder in self.search_paths:
            if not os.path.isdir(folder):
                continue
            for root, dirs, names in os.walk(folder):
                dirs.sort()
                for name in sorted(names):
                    if name.startswith("_") or not name.lower().endswith((".yaml", ".yml")):
                        continue
                    found.append(os.path.join(root, name))
        return found

    def _current_stamp(self, files: List[str]) -> Tuple[Tuple[str, float], ...]:
        stamp = []
        for path in files:
            try:
                stamp.append((path, os.path.getmtime(path)))
            except OSError:
                continue
        return tuple(stamp)

    def refresh(self, force: bool = False) -> None:
        files = self._files()
        stamp = self._current_stamp(files)
        if not force and stamp == self._stamp and self._profiles:
            return

        self.warnings = []
        self.shadowed = {}
        raw: Dict[str, Dict[str, Any]] = {}
        origin: Dict[str, str] = {}
        order: List[str] = []

        for path in files:
            try:
                data = _read_yaml(path)
            except Exception as error:
                self.warnings.append(f"{path}: could not be read as YAML ({error})")
                continue
            documents = data if isinstance(data, list) else [data]
            for document in documents:
                if not isinstance(document, dict) or not document.get("id"):
                    self.warnings.append(f"{path}: no 'id' key, skipped")
                    continue
                profile_id = str(document["id"])
                if profile_id in raw:
                    self.shadowed.setdefault(profile_id, []).append(path)
                    continue
                raw[profile_id] = document
                origin[profile_id] = path
                order.append(profile_id)

        profiles: Dict[str, Profile] = {}
        for profile_id in order:
            data = self._resolve_extends(profile_id, raw, depth=0)
            if data is None:
                continue
            profile, problems = profile_from_dict(data, origin=origin[profile_id])
            self.warnings.extend(problems)
            if profile is not None:
                profiles[profile_id] = profile

        self._profiles = profiles
        self._order = [profile_id for profile_id in order if profile_id in profiles]
        self._stamp = stamp

    def _resolve_extends(self, profile_id: str, raw: Dict[str, Dict[str, Any]], depth: int) -> Optional[Dict[str, Any]]:
        data = raw[profile_id]
        parent_id = data.get("extends")
        if not parent_id:
            return data
        if depth >= MAX_EXTENDS_DEPTH:
            self.warnings.append(f"{profile_id}: 'extends' chain deeper than {MAX_EXTENDS_DEPTH}, profile skipped")
            return None
        if parent_id not in raw:
            self.warnings.append(f"{profile_id}: extends unknown profile '{parent_id}', profile skipped")
            return None
        parent = self._resolve_extends(str(parent_id), raw, depth + 1)
        if parent is None:
            return None
        inherited = {key: value for key, value in parent.items() if key not in ("hidden",)}
        return _deep_merge(inherited, data)

    # -- lookups ------------------------------------------------------------------------
    def get(self, profile_id: str) -> Optional[Profile]:
        self.refresh()
        return self._profiles.get(profile_id)

    def all(self, modality: Optional[str] = None, task: Optional[str] = None, include_hidden: bool = False) -> List[Profile]:
        self.refresh()
        selected: List[Profile] = []
        for profile_id in self._order:
            profile = self._profiles[profile_id]
            if profile.hidden and not include_hidden:
                continue
            if modality and profile.modality != modality:
                continue
            if task and task not in profile.tasks:
                continue
            selected.append(profile)
        return selected

    def ids(self, modality: Optional[str] = None, task: Optional[str] = None) -> List[str]:
        return [profile.id for profile in self.all(modality=modality, task=task)]


_LIBRARIES: Dict[Tuple[str, ...], ProfileLibrary] = {}


def get_library(extra_paths: Optional[Iterable[str]] = None) -> ProfileLibrary:
    """Shared library for the given extra paths (config, user and shipped folders are always included)."""
    paths = [os.path.abspath(path) for path in (extra_paths or []) if path]
    paths += configured_paths() + [USER_PROFILE_DIR, BUILTIN_PROFILE_DIR]
    key = tuple(paths)
    if key not in _LIBRARIES:
        _LIBRARIES[key] = ProfileLibrary(paths)
    return _LIBRARIES[key]
