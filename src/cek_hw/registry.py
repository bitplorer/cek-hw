"""Device registry — identity, pin map, safe levels, transport.

Runtime (Host-adjacent), not a kernel. Caps still bind subject/scopes;
the registry only answers 'does this pin exist on this device?'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PinDecl:
    name: str
    number: int
    safe: int = 0
    role: str = "gpio"  # gpio | relay | motor


@dataclass
class Device:
    id: str
    profile: str = "hw-v1"
    transport: str = "memory"  # memory | serial | websocket
    serial_port: str | None = None
    baud: int = 115200
    watchdog_ms: int = 1500
    pins: dict[int, PinDecl] = field(default_factory=dict)
    relays: dict[str, PinDecl] = field(default_factory=dict)
    motors: dict[str, PinDecl] = field(default_factory=dict)

    def gpio_safe_map(self) -> dict[int, int]:
        return {n: p.safe for n, p in self.pins.items()}

    def relay_safe_map(self) -> dict[str, int]:
        return {i: p.safe for i, p in self.relays.items()}

    def known_gpio(self, pin: int) -> bool:
        return int(pin) in self.pins

    def known_relay(self, relay_id: str) -> bool:
        return relay_id in self.relays

    def known_motor(self, motor_id: str) -> bool:
        return motor_id in self.motors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile": self.profile,
            "transport": self.transport,
            "serial_port": self.serial_port,
            "baud": self.baud,
            "watchdog_ms": self.watchdog_ms,
            "pins": {str(n): {"name": p.name, "safe": p.safe} for n, p in self.pins.items()},
            "relays": {i: {"name": p.name, "safe": p.safe} for i, p in self.relays.items()},
            "motors": {i: {"name": p.name} for i, p in self.motors.items()},
        }


@dataclass
class Registry:
    devices: dict[str, Device] = field(default_factory=dict)

    def add(self, device: Device) -> None:
        self.devices[device.id] = device

    def get(self, device_id: str) -> Device | None:
        return self.devices.get(device_id)

    def require(self, device_id: str) -> Device:
        d = self.get(device_id)
        if d is None:
            raise KeyError(f"unknown device: {device_id}")
        return d


def demo_press() -> Device:
    """One factory press — used by tests and the lab."""
    pins = {
        13: PinDecl("led", 13, safe=0),
        7: PinDecl("coil", 7, safe=0),
        3: PinDecl("estop_sense", 3, safe=1, role="gpio"),
    }
    return Device(
        id="press-01",
        pins=pins,
        relays={"main": PinDecl("main", 8, safe=0, role="relay")},
        motors={"spindle": PinDecl("spindle", 9, safe=0, role="motor")},
        watchdog_ms=1500,
    )
