"""Thin hw-v1 Peer port of cek-peer-kernel::Peer.apply.

THIS IS THE JUSTIFIED COPY. MCU / gateway cannot link the Rust kernel.
Keep this file small. Semantics must match:

- authority_refusal / dispatch_error → zero world changes
- apply in order
- unknown Op → fail_batch (hardware must not skip)
- receipt reports landed vs failed — never a Cap

If the kernel apply loop changes, port the change here. Do not grow
features that belong on cek-peer-kernel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .apply import ApplyError, apply_op
from .catalog import (
    HW_PAIRS,
    LAW_GENERATION,
    PROFILE_HW,
    UNKNOWN_OP_POLICY,
    is_hw_pair,
    split_alias_illegal,
)
from .registry import Registry
from .store import HwStore
from .watchdog import Watchdog


@dataclass
class Receipt:
    landed: list[dict[str, Any]] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"landed": list(self.landed), "failed": list(self.failed)}


class HwPeer:
    """Apply-only. There is no mint API. Do not add one."""

    def __init__(
        self,
        *,
        store: HwStore | None = None,
        registry: Registry | None = None,
        unknown_op_policy: str = UNKNOWN_OP_POLICY,
        watchdog: Watchdog | None = None,
    ) -> None:
        self.store = store or HwStore()
        self.registry = registry
        self.unknown_op_policy = unknown_op_policy
        self.watchdog = watchdog
        self.profile = PROFILE_HW

    def manifest(self) -> dict[str, Any]:
        return {
            "law_generation": LAW_GENERATION,
            "profiles": [PROFILE_HW],
            "apply_set": sorted(f"{n}.{m}" for n, m in HW_PAIRS),
            "unknown_op_policy": self.unknown_op_policy,
            "receipts": "required",
            "mint": False,
        }

    def can_apply(self, op: dict[str, Any]) -> bool:
        ns = str(op.get("ns") or "")
        name = str(op.get("name") or "")
        if split_alias_illegal(ns, name):
            return False
        return is_hw_pair(ns, name)

    def apply(self, result: dict[str, Any]) -> Receipt:
        kind = result.get("kind")
        if kind in ("authority_refusal", "dispatch_error"):
            return Receipt([], [])
        landed: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        abort = False
        for op in list(result.get("ops") or []):
            if abort:
                failed.append(op)
                continue
            if not self.can_apply(op):
                failed.append(op)
                if self.unknown_op_policy == "fail_batch":
                    abort = True
                continue
            try:
                apply_op(self.store, op, registry=self.registry)
                landed.append(op)
            except (ApplyError, TypeError, ValueError):
                failed.append(op)
        if self.watchdog is not None and landed:
            self.watchdog.pet()
        return Receipt(landed, failed)


def apply_result(
    store: HwStore,
    result: dict[str, Any],
    *,
    registry: Registry | None = None,
) -> Receipt:
    return HwPeer(store=store, registry=registry).apply(result)
