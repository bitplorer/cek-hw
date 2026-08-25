"""hw-v1 Domain catalog — sole source of hw pair identity.

Mirrors cek-contract domain.rs + cek_host.legal, but ONLY the hw packs.
Baseline / ui.dom live upstream. Do not copy them here.

Wire identity is the pair (ns, name). Concatenation is never identity.
`name` is a single token. `ns` is the pack (`family.scope`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LAW_GENERATION = "cek-law-1"
PROFILE_HW = "hw-v1"
UNKNOWN_OP_POLICY = "fail_batch"

_CATALOG_CANDIDATES = (
    Path(__file__).resolve().parent / "data" / "hw-v1.json",
    Path(__file__).resolve().parents[2] / "catalog" / "hw-v1.json",
)


def _load() -> dict[str, Any]:
    for path in _CATALOG_CANDIDATES:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("hw-v1.json catalog missing")


def load_catalog() -> dict[str, Any]:
    return _load()


def _pairs_from_catalog() -> frozenset[tuple[str, str]]:
    data = _load()
    out: set[tuple[str, str]] = set()
    for pack in data["packs"]:
        ns = pack["pack"]
        for op in pack["ops"]:
            out.add((ns, op["name"]))
    return frozenset(out)


def _actions_from_catalog() -> dict[str, tuple[str, str]]:
    data = _load()
    return {a["action"]: (a["ns"], a["name"]) for a in data["actions"]}


def _reverse_from_catalog() -> dict[tuple[str, str], str]:
    data = _load()
    out: dict[tuple[str, str], str] = {}
    for pack in data["packs"]:
        ns = pack["pack"]
        for op in pack["ops"]:
            out[(ns, op["name"])] = op["reverse"]
    return out


HW_PAIRS: frozenset[tuple[str, str]] = _pairs_from_catalog()
HW_ACTIONS: dict[str, tuple[str, str]] = _actions_from_catalog()
HW_REVERSE: dict[tuple[str, str], str] = _reverse_from_catalog()
HW_PACKS: frozenset[str] = frozenset(p[0] for p in HW_PAIRS)
HW_FQS: frozenset[str] = frozenset(f"{ns}.{name}" for ns, name in HW_PAIRS)

# Session stamp = these pairs. Host.normalize_stamp already accepts
# structure-valid extension pairs; pass HW_STAMP into Host.stamp.
HW_STAMP: tuple[dict[str, str], ...] = tuple(
    {"ns": ns, "name": name} for ns, name in sorted(HW_PAIRS)
)


def name_is_token(name: str) -> bool:
    return bool(name) and name.isalnum() and name == name.lower() and "." not in name


def is_hw_pair(ns: str, name: str) -> bool:
    return name_is_token(name) and (ns, name) in HW_PAIRS


def fq_of(ns: str, name: str) -> str:
    return f"{ns}.{name}"


def split_alias_illegal(ns: str, name: str) -> bool:
    """True if this looks like a concatenated split of a legal pair."""
    if is_hw_pair(ns, name):
        return False
    glued = f"{ns}.{name}" if name else ns
    return glued in HW_FQS
