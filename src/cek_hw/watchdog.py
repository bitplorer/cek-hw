"""Peer-local fail-safe. NOT a Cap path.

If no authorized apply lands within watchdog_ms, drive safe_state.
This is a hardware interlock (brown-out / lost-host), analogous to
MCU reset — it does not invent business truth and it is not authority.

Emit an event; do not mint a Cap; do not pretend Host authorized it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .ops import safe_state
from .registry import Registry
from .store import HwStore
from .apply import apply_op


NowFn = Callable[[], float]


@dataclass
class Watchdog:
    store: HwStore
    registry: Registry
    now: NowFn = time.monotonic
    last_pet: float = field(init=False)
    tripped: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.last_pet = self.now()

    def pet(self) -> None:
        self.last_pet = self.now()

    def tick(self) -> list[dict[str, Any]]:
        """Apply local safe_state for any device past its deadline. Returns events."""
        events: list[dict[str, Any]] = []
        now = self.now()
        for device in self.registry.devices.values():
            if (now - self.last_pet) * 1000.0 < device.watchdog_ms:
                continue
            if device.id in self.tripped:
                continue
            apply_op(self.store, safe_state(device.id), registry=self.registry)
            self.tripped.append(device.id)
            events.append(
                {
                    "type": "event",
                    "name": "hw.watchdog",
                    "payload": {"device": device.id, "safe": True},
                }
            )
        return events

    def reset_trip(self, device_id: str) -> None:
        if device_id in self.tripped:
            self.tripped.remove(device_id)
