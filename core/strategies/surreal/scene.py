"""
The first stage of the surreal pipeline: inventory the ordinary scene before anything is changed.

The inventory is deliberately descriptive rather than creative. It gives the critic stable entity roles,
ordinary properties, relationships and a compact scene context that can survive a later transformation without
forcing the final prompt to repeat the original user sentence.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class SceneEntity:
    id: str = ""
    name: str = ""
    kind: str = ""
    role: str = ""
    attributes: List[str] = field(default_factory=list)
    ordinary_properties: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    affordances: List[str] = field(default_factory=list)


@dataclass
class SceneInventory:
    primary_subject: str = ""
    subject_action: str = ""
    setting: str = ""
    light: str = ""
    viewpoint: str = ""
    entities: List[SceneEntity] = field(default_factory=list)
    preserved_scene: str = ""

    def summary(self) -> str:
        parts = []
        if self.primary_subject:
            parts.append(f"subject: {self.primary_subject}")
        if self.subject_action:
            parts.append(f"action: {self.subject_action}")
        if self.setting:
            parts.append(f"setting: {self.setting}")
        if self.light:
            parts.append(f"light: {self.light}")
        if self.viewpoint:
            parts.append(f"viewpoint: {self.viewpoint}")
        if self.entities:
            names = [entity.name for entity in self.entities if entity.name]
            if names:
                parts.append("entities: " + ", ".join(names[:12]))
        return " | ".join(parts)


SCENE_SYSTEM = """You inventory the ORDINARY scene in a user's image idea before a surreal transformation is applied.

Do not improve the image, add symbolism, choose a surreal operation or write a polished prompt. Record only what
the user supplied or directly implied. Give each important entity a short stable id. For each entity, distinguish
its visible attributes, ordinary physical properties, relationships and useful affordances. An affordance is a
visible possibility such as "can be held", "provides human scale", "has an opening", "casts a shadow", "forms a
continuous surface" or "can support another object".

`preserved_scene` is one compact sentence containing the subject, action, setting, light and viewpoint. It is
ordinary and contains every important entity. A later stage will remove or alter individual entities.

Answer with JSON only:
{"primary_subject":"...","subject_action":"...","setting":"...","light":"...","viewpoint":"...",
"entities":[{"id":"...","name":"...","kind":"...","role":"primary|supporting|environment",
"attributes":["..."],"ordinary_properties":["..."],"relationships":["..."],"affordances":["..."]}],
"preserved_scene":"..."}"""


def scene_messages(idea: str) -> Tuple[str, str]:
    return SCENE_SYSTEM, "USER IDEA\n" + (idea or "").strip()


def _first_json_object(text: str) -> Optional[dict]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S | re.I)
    start = text.find("{")
    while start >= 0:
        depth, in_string, escaped = 0, False, False
        for position in range(start, len(text)):
            character = text[position]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[start:position + 1])
                        return value if isinstance(value, dict) else None
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def _short_text(value, words: int = 40) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip().strip('"')
    return " ".join(text.split()[:words])


def _short_list(value, count: int = 8, words: int = 16) -> List[str]:
    if not isinstance(value, list):
        return []
    found = []
    for entry in value:
        text = _short_text(entry, words)
        if text and text not in found:
            found.append(text)
    return found[:count]


def parse_scene_inventory(text: str) -> Tuple[Optional[SceneInventory], List[str]]:
    data = _first_json_object(text)
    if data is None:
        return None, ["the scene inventory returned no JSON object"]
    entities: List[SceneEntity] = []
    for index, raw in enumerate(data.get("entities") or []):
        if not isinstance(raw, dict):
            continue
        name = _short_text(raw.get("name"), 12)
        if not name:
            continue
        entity_id = re.sub(r"[^a-z0-9_]+", "_", _short_text(raw.get("id"), 6).lower()).strip("_")
        entities.append(SceneEntity(
            id=entity_id or f"entity_{index + 1}",
            name=name,
            kind=_short_text(raw.get("kind"), 8),
            role=_short_text(raw.get("role"), 4),
            attributes=_short_list(raw.get("attributes")),
            ordinary_properties=_short_list(raw.get("ordinary_properties")),
            relationships=_short_list(raw.get("relationships")),
            affordances=_short_list(raw.get("affordances")),
        ))
    inventory = SceneInventory(
        primary_subject=_short_text(data.get("primary_subject"), 16),
        subject_action=_short_text(data.get("subject_action"), 20),
        setting=_short_text(data.get("setting"), 24),
        light=_short_text(data.get("light"), 20),
        viewpoint=_short_text(data.get("viewpoint"), 20),
        entities=entities[:16],
        preserved_scene=_short_text(data.get("preserved_scene"), 80),
    )
    if not inventory.primary_subject:
        return None, ["the scene inventory did not identify a primary subject"]
    if not inventory.preserved_scene:
        return None, ["the scene inventory did not return a preserved ordinary scene"]
    return inventory, []


def inventory_for_critic(inventory: Optional[SceneInventory]) -> str:
    if inventory is None:
        return ""
    lines = [
        f"primary subject: {inventory.primary_subject}",
        f"subject action: {inventory.subject_action or '[not specified]'}",
        f"setting: {inventory.setting or '[not specified]'}",
        f"light: {inventory.light or '[not specified]'}",
        f"viewpoint: {inventory.viewpoint or '[not specified]'}",
        f"ordinary scene: {inventory.preserved_scene}",
        "entities:",
    ]
    for entity in inventory.entities:
        details = []
        if entity.attributes:
            details.append("attributes=" + "; ".join(entity.attributes))
        if entity.ordinary_properties:
            details.append("ordinary properties=" + "; ".join(entity.ordinary_properties))
        if entity.relationships:
            details.append("relationships=" + "; ".join(entity.relationships))
        if entity.affordances:
            details.append("affordances=" + "; ".join(entity.affordances))
        lines.append(f"- {entity.id}: {entity.name} ({entity.kind or 'entity'}, {entity.role or 'supporting'})"
                     + (f" | {' | '.join(details)}" if details else ""))
    return "\n".join(lines)
