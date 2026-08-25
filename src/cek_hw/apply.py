"""apply_op — the driver entry. Same job as cek_ops_ui::apply_op.

Peer kernel (or the thin hw-v1 port) calls this AFTER Host already decided.
Refuse Results never reach here — the apply loop short-circuits them.
"""

from __future__ import annotations

from typing import Any

from .catalog import is_hw_pair
from .registry import Registry
from .store import HwStore


class ApplyError(ValueError):
    """Driver refused to land this Op (missing pin, bad payload). Not a Cap refuse."""


def _level(v: Any) -> int:
    n = int(v)
    if n not in (0, 1):
        raise ApplyError("level must be 0 or 1")
    return n


def _pin(v: Any) -> int:
    n = int(v)
    if n < 0 or n > 255:
        raise ApplyError("pin out of range")
    return n


def apply_op(store: HwStore, op: dict[str, Any], *, registry: Registry | None = None) -> None:
    ns = str(op.get("ns") or "")
    name = str(op.get("name") or "")
    if not is_hw_pair(ns, name):
        raise ApplyError(f"not an hw pair: {ns}.{name}")
    p = dict(op.get("payload") or {})
    device = p.get("device")
    if not isinstance(device, str) or not device:
        raise ApplyError("device required")

    bound = registry.get(device) if registry is not None else None
    if registry is not None and bound is None:
        raise ApplyError(f"unknown device: {device}")

    if ns == "hw.gpio" and name == "set":
        pin = _pin(p.get("pin"))
        if bound is not None and not bound.known_gpio(pin):
            raise ApplyError(f"unknown pin {pin} on {device}")
        store.gpio_set(device, pin, _level(p.get("level")))
        return
    if ns == "hw.relay" and name == "set":
        rid = str(p.get("id") or "")
        if not rid:
            raise ApplyError("relay id required")
        if bound is not None and not bound.known_relay(rid):
            raise ApplyError(f"unknown relay {rid} on {device}")
        store.relay_set(device, rid, _level(p.get("level")))
        return
    if ns == "hw.relay" and name == "pulse":
        rid = str(p.get("id") or "")
        ms = int(p.get("ms") or 0)
        if not rid or ms <= 0:
            raise ApplyError("relay pulse needs id and ms>0")
        if bound is not None and not bound.known_relay(rid):
            raise ApplyError(f"unknown relay {rid} on {device}")
        store.relay_pulse(device, rid, ms)
        return
    if ns == "hw.motor" and name == "start":
        mid = str(p.get("id") or "")
        if not mid:
            raise ApplyError("motor id required")
        if bound is not None and not bound.known_motor(mid):
            raise ApplyError(f"unknown motor {mid} on {device}")
        rpm = p.get("rpm")
        store.motor_start(device, mid, int(rpm) if rpm is not None else None)
        return
    if ns == "hw.motor" and name == "stop":
        mid = str(p.get("id") or "")
        if not mid:
            raise ApplyError("motor id required")
        store.motor_stop(device, mid)
        return
    if ns == "hw.safe" and name == "state":
        if bound is None:
            # Unbound store: pull nothing down; still record the request.
            store.safe_applied.append(device)
            return
        store.apply_safe(device, bound.gpio_safe_map(), bound.relay_safe_map())
        return
    raise ApplyError(f"unhandled pair {ns}.{name}")
