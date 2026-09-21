"""
Named direction axes: "ordinary -> uncanny", "new -> decayed", ...

An axis is two sets of example phrases (YAML: name -> {description, from: [...], to: [...]}).
Its vector is centroid(to) - centroid(from) in whatever embedder is in use, so the same file works
for every embedder; the vectors are computed once per embedder and kept in memory, and the example
phrases themselves go through the on-disk vector cache like any other phrase.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

NONE = "none"


@dataclass
class DirectionAxis:
    name: str
    description: str = ""
    start: List[str] = field(default_factory=list)      # the `from` phrases
    end: List[str] = field(default_factory=list)        # the `to` phrases


def load_directions(paths: Iterable[str]) -> Dict[str, DirectionAxis]:
    """Read axis files in order; a later file replaces an axis of the same name. Bad files are skipped."""
    axes: Dict[str, DirectionAxis] = {}
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            import yaml
            with open(path, "r", encoding="utf-8-sig") as handle:
                data = yaml.safe_load(handle) or {}
        except Exception as error:
            print(f"[Semantic Variation] direction file {path} could not be read: {error}")
            continue
        if not isinstance(data, dict):
            continue
        for name, body in data.items():
            if not isinstance(body, dict):
                continue
            start = [str(item) for item in (body.get("from") or []) if str(item).strip()]
            end = [str(item) for item in (body.get("to") or []) if str(item).strip()]
            if len(start) >= 2 and len(end) >= 2:
                axes[str(name)] = DirectionAxis(str(name), str(body.get("description", "")), start, end)
    return axes
