"""cek-hw — L5 hardware pack + Peer driver + serial carrier + MCU port.

Not a Host kernel. Not ux-channel. Not Baseline.
See DRY.md for what this package refuses to copy.
"""

from __future__ import annotations

from .apply import ApplyError, apply_op
from .catalog import (
    HW_ACTIONS,
    HW_FQS,
    HW_PAIRS,
    HW_PACKS,
    HW_STAMP,
    LAW_GENERATION,
    PROFILE_HW,
    is_hw_pair,
    load_catalog,
)
from .ops import (
    gpio_set,
    inverse_op,
    inverse_ops,
    lower_to_baseline,
    motor_start,
    motor_stop,
    relay_pulse,
    relay_set,
    reverse_class_for,
    safe_state,
)
from .peer import HwPeer, Receipt, apply_result
from .project import ProjectError, project_action
from .registry import Device, PinDecl, Registry, demo_press
from .serial import MemorySerial, SerialCarrier, SerialPeerAdapter, open_serial_memory
from .store import HwStore
from .watchdog import Watchdog

__version__ = "0.1.0"

__all__ = [
    "HW_ACTIONS",
    "HW_FQS",
    "HW_PAIRS",
    "HW_PACKS",
    "HW_STAMP",
    "LAW_GENERATION",
    "PROFILE_HW",
    "ApplyError",
    "Device",
    "HwPeer",
    "HwStore",
    "MemorySerial",
    "PinDecl",
    "ProjectError",
    "Receipt",
    "Registry",
    "SerialCarrier",
    "SerialPeerAdapter",
    "Watchdog",
    "apply_op",
    "apply_result",
    "demo_press",
    "gpio_set",
    "inverse_op",
    "inverse_ops",
    "is_hw_pair",
    "load_catalog",
    "lower_to_baseline",
    "motor_start",
    "motor_stop",
    "open_serial_memory",
    "project_action",
    "relay_pulse",
    "relay_set",
    "reverse_class_for",
    "safe_state",
    "__version__",
]
