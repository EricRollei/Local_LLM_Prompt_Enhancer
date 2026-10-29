"""
Your arrangement of the slot buttons: builders_user/button_layout.yaml, written by the panel's
"Arrange" mode and applied to every builder after the shipped YAML and my_buttons.yaml.

    moved:              # a button shown in another section and/or under another group heading
      shot: {section: composition, group: ""}
    order:              # button order inside a section (ids not listed keep their place, after these)
      setting: [location, background, landmark]
    hidden: [nose, lips]

The shipped builders/*.yaml is never changed; "Reset layout" deletes this file.

No ComfyUI dependency.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML ships with ComfyUI
    yaml = None

LAYOUT_FILE = "button_layout.yaml"


def empty_layout() -> Dict:
    return {"moved": {}, "order": {}, "hidden": []}


def read_layout(path: str) -> Dict:
    """The layout file, cleaned. Missing or broken -> an empty layout."""
    layout = empty_layout()
    if yaml is None or not path or not os.path.isfile(path):
        return layout
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as error:
        print(f"[Wildcard Composer] skipped {path}: {error}")
        return layout
    if not isinstance(data, dict):
        return layout
    for slot_id, move in (data.get("moved") or {}).items():
        if isinstance(move, dict):
            entry = {}
            if move.get("section"):
                entry["section"] = str(move["section"]).strip()
            if "group" in move:
                entry["group"] = str(move.get("group") or "").strip()
            if entry:
                layout["moved"][str(slot_id)] = entry
    for section, ids in (data.get("order") or {}).items():
        if isinstance(ids, list):
            layout["order"][str(section)] = [str(slot_id) for slot_id in ids if slot_id]
    layout["hidden"] = sorted({str(slot_id) for slot_id in (data.get("hidden") or []) if slot_id})
    return layout


def write_layout(path: str, layout: Dict) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    header = ("# Your arrangement of the Wildcard Composer buttons (the panel's Arrange mode writes it).\n"
              "# Delete this file, or use Reset layout, to get the shipped layout back.\n")
    clean = {"moved": layout.get("moved") or {}, "order": layout.get("order") or {},
             "hidden": sorted(set(layout.get("hidden") or []))}
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(header + yaml.safe_dump(clean, sort_keys=True, allow_unicode=True, width=120))
    os.replace(temp, path)


def apply_layout(builders: Dict, layout: Dict) -> None:
    """Move, regroup, hide and reorder the slots of every builder (in place)."""
    moved = layout.get("moved") or {}
    hidden = set(layout.get("hidden") or [])
    order = layout.get("order") or {}
    for builder in builders.values():
        for slot in builder.slots:
            move = moved.get(slot.id)
            if move:
                slot.section = move.get("section", slot.section)
                if "group" in move:
                    slot.group = move["group"]
            slot.hidden = slot.id in hidden
        positions = {section: {slot_id: index for index, slot_id in enumerate(ids)} for section, ids in order.items()}
        original = {slot.id: index for index, slot in enumerate(builder.slots)}

        def key(slot):
            listed = positions.get(slot.section, {})
            if slot.id in listed:
                return (0, listed[slot.id], 0)
            return (1, 0, original[slot.id])

        builder.slots.sort(key=key)


def layout_move(layout: Dict, slot_id: str, section: Optional[str] = None, group: Optional[str] = None,
                before: Optional[str] = None, section_ids: Optional[List[str]] = None) -> Dict:
    """
    Record a move: to `section` (and `group`), placed before the button `before` (None = at the end).
    section_ids: the ids currently shown in the target section, in order (from the panel), so the
    new order can be written in full.
    """
    layout = {"moved": dict(layout.get("moved") or {}), "order": dict(layout.get("order") or {}),
              "hidden": list(layout.get("hidden") or [])}
    entry = dict(layout["moved"].get(slot_id, {}))
    if section:
        entry["section"] = section
    if group is not None:
        entry["group"] = group
    if entry:
        layout["moved"][slot_id] = entry
    if section_ids is not None and (section or entry.get("section")):
        target = section or entry["section"]
        ids = [i for i in section_ids if i != slot_id]
        at = ids.index(before) if before in ids else len(ids)
        ids.insert(at, slot_id)
        layout["order"][target] = ids
        for other, other_ids in list(layout["order"].items()):
            if other != target and slot_id in other_ids:
                layout["order"][other] = [i for i in other_ids if i != slot_id]
    return layout


def layout_hide(layout: Dict, slot_id: str, hidden: bool) -> Dict:
    layout = {"moved": dict(layout.get("moved") or {}), "order": dict(layout.get("order") or {}),
              "hidden": list(layout.get("hidden") or [])}
    ids = set(layout["hidden"])
    if hidden:
        ids.add(slot_id)
    else:
        ids.discard(slot_id)
    layout["hidden"] = sorted(ids)
    return layout
