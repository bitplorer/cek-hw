"""Host-side project: action → Ops. Plug into cek-host via project_ops.

Does not verify Caps. Does not apply. Same job as cek_host.host_project
for the hw actions only — do not fork host_project.py; pass the list in.

    ops = project_action("hw.gpio.write", args)
    host.submit(action="hw.gpio.write", args=args, cap=cap, project_ops=ops)
"""

from __future__ import annotations

from typing import Any

from .catalog import HW_ACTIONS
from .ops import gpio_set, motor_start, motor_stop, relay_pulse, relay_set, safe_state


class ProjectError(ValueError):
    """Unknown action or bad args. Host maps this to dispatch_error."""


def _str(args: dict[str, Any], key: str) -> str:
    v = args.get(key)
    if not isinstance(v, str) or not v:
        raise ProjectError(f"{key} required string")
    return v


def _int(args: dict[str, Any], key: str) -> int:
    if key not in args:
        raise ProjectError(f"{key} required")
    return int(args[key])


def project_action(action: str, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    args = dict(args or {})
    if action not in HW_ACTIONS:
        raise ProjectError(f"unknown action: {action}")
    if action == "hw.gpio.write":
        prior = args["prior"] if "prior" in args else None
        return [
            gpio_set(
                _str(args, "device"),
                _int(args, "pin"),
                _int(args, "level"),
                prior=None if prior is None else int(prior),
            )
        ]
    if action == "hw.relay.write":
        prior = args["prior"] if "prior" in args else None
        return [
            relay_set(
                _str(args, "device"),
                _str(args, "id"),
                _int(args, "level"),
                prior=None if prior is None else int(prior),
            )
        ]
    if action == "hw.relay.pulse":
        return [relay_pulse(_str(args, "device"), _str(args, "id"), _int(args, "ms"))]
    if action == "hw.motor.start":
        rpm = args.get("rpm")
        return [
            motor_start(
                _str(args, "device"),
                _str(args, "id"),
                None if rpm is None else int(rpm),
            )
        ]
    if action == "hw.motor.stop":
        return [motor_stop(_str(args, "device"), _str(args, "id"))]
    if action == "hw.safe.apply":
        return [safe_state(_str(args, "device"))]
    raise ProjectError(f"unknown action: {action}")
