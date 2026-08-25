"""HwStore — the world. Peer-outer, like KvStore / UiStore.

Not a kernel. Does not mint, verify, or refuse Caps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _pin_key(device: str, pin: int) -> tuple[str, int]:
    return (device, int(pin))


def _id_key(device: str, ident: str) -> tuple[str, str]:
    return (device, ident)


@dataclass
class HwStore:
    """In-memory digital world. Gateway and tests use this; MCU has registers."""

    gpio: dict[tuple[str, int], int] = field(default_factory=dict)
    relays: dict[tuple[str, str], int] = field(default_factory=dict)
    motors: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    pulses: list[dict[str, Any]] = field(default_factory=list)
    safe_applied: list[str] = field(default_factory=list)

    def gpio_set(self, device: str, pin: int, level: int) -> None:
        self.gpio[_pin_key(device, pin)] = 1 if int(level) else 0

    def gpio_get(self, device: str, pin: int) -> int | None:
        return self.gpio.get(_pin_key(device, pin))

    def relay_set(self, device: str, relay_id: str, level: int) -> None:
        self.relays[_id_key(device, relay_id)] = 1 if int(level) else 0

    def relay_get(self, device: str, relay_id: str) -> int | None:
        return self.relays.get(_id_key(device, relay_id))

    def relay_pulse(self, device: str, relay_id: str, ms: int) -> None:
        self.pulses.append({"device": device, "id": relay_id, "ms": int(ms)})
        # Pulse ends at 0. Record the landing state.
        self.relays[_id_key(device, relay_id)] = 0

    def motor_start(self, device: str, motor_id: str, rpm: int | None = None) -> None:
        self.motors[_id_key(device, motor_id)] = {
            "running": True,
            "rpm": 0 if rpm is None else int(rpm),
        }

    def motor_stop(self, device: str, motor_id: str) -> None:
        cur = self.motors.get(_id_key(device, motor_id), {})
        self.motors[_id_key(device, motor_id)] = {
            "running": False,
            "rpm": 0,
            "prior_rpm": cur.get("rpm"),
        }

    def apply_safe(self, device: str, gpio_pins: dict[int, int], relay_ids: dict[str, int]) -> None:
        for pin, level in gpio_pins.items():
            self.gpio_set(device, pin, level)
        for rid, level in relay_ids.items():
            self.relay_set(device, rid, level)
        for (dev, mid), _st in list(self.motors.items()):
            if dev == device:
                self.motor_stop(dev, mid)
        self.safe_applied.append(device)

    def snapshot(self) -> dict[str, Any]:
        return {
            "gpio": {f"{d}:{p}": v for (d, p), v in sorted(self.gpio.items())},
            "relays": {f"{d}:{i}": v for (d, i), v in sorted(self.relays.items())},
            "motors": {f"{d}:{i}": dict(st) for (d, i), st in sorted(self.motors.items())},
            "pulses": list(self.pulses),
            "safe_applied": list(self.safe_applied),
        }
