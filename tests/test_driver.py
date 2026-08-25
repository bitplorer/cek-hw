"""Driver + Peer port tests. No Host kernel involved."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cek_hw import (
    HW_PAIRS,
    HwPeer,
    HwStore,
    Registry,
    apply_op,
    apply_result,
    demo_press,
    gpio_set,
    inverse_ops,
    is_hw_pair,
    motor_start,
    project_action,
    relay_pulse,
    safe_state,
)
from cek_hw.catalog import split_alias_illegal
from cek_hw.apply import ApplyError
from cek_hw.watchdog import Watchdog


def test_pair_not_concat():
    assert is_hw_pair("hw.gpio", "set")
    assert not is_hw_pair("hw", "gpio.set")
    assert split_alias_illegal("hw", "gpio.set")
    assert ("hw.gpio", "set") in HW_PAIRS


def test_gpio_set_lands():
    store = HwStore()
    apply_op(store, gpio_set("press-01", 13, 1, prior=0))
    assert store.gpio_get("press-01", 13) == 1


def test_refuse_never_mutates():
    peer = HwPeer()
    rec = peer.apply(
        {
            "kind": "authority_refusal",
            "ops": [gpio_set("press-01", 13, 1)],
            "error": "no",
        }
    )
    assert rec.landed == []
    assert peer.store.gpio_get("press-01", 13) is None


def test_unknown_pin_fails_closed():
    reg = Registry()
    reg.add(demo_press())
    peer = HwPeer(registry=reg)
    rec = peer.apply({"kind": "ok", "ops": [gpio_set("press-01", 99, 1)]})
    assert rec.landed == []
    assert rec.failed
    assert peer.store.gpio_get("press-01", 99) is None


def test_fail_batch_aborts_rest():
    peer = HwPeer()
    rec = peer.apply(
        {
            "kind": "ok",
            "ops": [
                {"ns": "ui.dom", "name": "morph", "payload": {"target": "x"}},
                gpio_set("press-01", 13, 1),
            ],
        }
    )
    assert rec.landed == []
    assert len(rec.failed) == 2
    assert peer.store.gpio_get("press-01", 13) is None


def test_inverse_gpio_with_prior():
    op = gpio_set("press-01", 13, 1, prior=0)
    inv = inverse_ops([op])
    assert inv[0]["payload"]["level"] == 0
    store = HwStore()
    apply_op(store, op)
    apply_op(store, inv[0])
    assert store.gpio_get("press-01", 13) == 0


def test_pulse_is_non_reversible():
    op = relay_pulse("press-01", "main", 20)
    assert inverse_ops([op]) == []


def test_motor_start_compensates_with_stop():
    op = motor_start("press-01", "spindle", 3000)
    inv = inverse_ops([op])
    assert inv[0]["ns"] == "hw.motor" and inv[0]["name"] == "stop"


def test_project_action():
    ops = project_action(
        "hw.gpio.write",
        {"device": "press-01", "pin": 13, "level": 1, "prior": 0},
    )
    assert ops[0]["ns"] == "hw.gpio"
    assert ops[0]["name"] == "set"


def test_project_unknown_action():
    with pytest.raises(Exception):
        project_action("kv.write", {"key": "a", "value": 1})


def test_watchdog_trips_safe():
    store = HwStore()
    reg = Registry()
    press = demo_press()
    press.watchdog_ms = 10
    reg.add(press)
    clock = {"t": 0.0}

    def now() -> float:
        return clock["t"]

    wd = Watchdog(store=store, registry=reg, now=now)
    apply_op(store, gpio_set("press-01", 13, 1), registry=reg)
    clock["t"] = 1.0
    events = wd.tick()
    assert events and events[0]["name"] == "hw.watchdog"
    assert store.gpio_get("press-01", 13) == 0  # safe


def test_vectors_pass():
    from cek_hw.cli import run_vectors

    assert run_vectors() == 0


def test_apply_result_helper():
    store = HwStore()
    rec = apply_result(store, {"kind": "ok", "ops": [gpio_set("d", 1, 1)]})
    assert rec.landed
    assert store.gpio_get("d", 1) == 1
