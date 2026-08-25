"""Op constructors + inverse + Baseline lowering.

Same shape as cek_contract::ui / baseline: data-only Ops, pair identity.
Does not mint Caps. Does not apply.
"""

from __future__ import annotations

from typing import Any

from .catalog import HW_REVERSE, is_hw_pair

Op = dict[str, Any]


def _op(ns: str, name: str, payload: dict[str, Any]) -> Op:
    return {"ns": ns, "name": name, "payload": payload}


def gpio_set(device: str, pin: int, level: int, *, prior: int | None = None) -> Op:
    payload: dict[str, Any] = {"device": device, "pin": int(pin), "level": int(level)}
    if prior is not None:
        payload["prior"] = int(prior)
    return _op("hw.gpio", "set", payload)


def relay_set(device: str, relay_id: str, level: int, *, prior: int | None = None) -> Op:
    payload: dict[str, Any] = {"device": device, "id": relay_id, "level": int(level)}
    if prior is not None:
        payload["prior"] = int(prior)
    return _op("hw.relay", "set", payload)


def relay_pulse(device: str, relay_id: str, ms: int) -> Op:
    return _op("hw.relay", "pulse", {"device": device, "id": relay_id, "ms": int(ms)})


def motor_start(device: str, motor_id: str, rpm: int | None = None) -> Op:
    payload: dict[str, Any] = {"device": device, "id": motor_id}
    if rpm is not None:
        payload["rpm"] = int(rpm)
    return _op("hw.motor", "start", payload)


def motor_stop(device: str, motor_id: str) -> Op:
    return _op("hw.motor", "stop", {"device": device, "id": motor_id})


def safe_state(device: str) -> Op:
    return _op("hw.safe", "state", {"device": device})


def inverse_op(op: Op) -> Op | None:
    """Pack inverse. Host lineage.inverse_ops does not yet know hw.* —

    Until cek-host grows the same 4-line snapshot branch ui.dom.morph has,
    callers apply this inverse as compensation Ops (still under a Cap).
    Do not copy lineage.py here.
    """
    ns = str(op.get("ns") or "")
    name = str(op.get("name") or "")
    p = dict(op.get("payload") or {})
    if not is_hw_pair(ns, name):
        return None
    klass = HW_REVERSE.get((ns, name), "non_reversible")
    if klass == "snapshot":
        if "prior" not in p:
            return None
        nxt = dict(p)
        nxt["level"] = int(p["prior"])
        nxt["prior"] = int(p.get("level", 0))
        return _op(ns, name, nxt)
    if klass == "compensation" and ns == "hw.motor" and name == "start":
        return motor_stop(str(p.get("device") or ""), str(p.get("id") or ""))
    return None


def inverse_ops(ops: list[Op]) -> list[Op]:
    out: list[Op] = []
    for op in reversed(ops):
        inv = inverse_op(op)
        if inv is not None:
            out.append(inv)
    return out


def reverse_class_for(ops: list[Op]) -> str:
    """inverse if every mutate Op has an inverse; else non_reversible."""
    for op in ops:
        ns = str(op.get("ns") or "")
        name = str(op.get("name") or "")
        if not is_hw_pair(ns, name):
            continue
        if inverse_op(op) is None:
            return "non_reversible"
    return "inverse" if ops else "non_reversible"


def lower_to_baseline(op: Op) -> Op | None:
    """Audit shadow only — kv.set of hw:{device}:{pin|id}.

    A Baseline Peer storing this is NOT actuating GPIO. Actuation requires
    hw-v1. Host reverse of kv.set is kv.delete, which is the wrong physics
    for a pin — do not use lowering as the reverse plan.
    """
    ns = str(op.get("ns") or "")
    name = str(op.get("name") or "")
    p = dict(op.get("payload") or {})
    device = p.get("device")
    if not device:
        return None
    if ns == "hw.gpio" and name == "set":
        key = f"hw:{device}:gpio:{p.get('pin')}"
        return {"ns": "kv", "name": "set", "payload": {"key": key, "value": p.get("level")}}
    if ns == "hw.relay" and name == "set":
        key = f"hw:{device}:relay:{p.get('id')}"
        return {"ns": "kv", "name": "set", "payload": {"key": key, "value": p.get("level")}}
    return None
