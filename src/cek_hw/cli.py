"""cek-hw CLI — vectors + doctor. Does not mint Caps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import HW_PAIRS, PROFILE_HW, load_catalog
from .peer import HwPeer
from .registry import Registry, demo_press
from .store import HwStore


def _vectors_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "vectors"


def _fresh_peer() -> HwPeer:
    """One world per vector. Shared-peer leakage is not a legal test."""
    reg = Registry()
    reg.add(demo_press())
    return HwPeer(store=HwStore(), registry=reg)


def run_vectors() -> int:
    n = 0
    failed = 0
    for path in sorted(_vectors_dir().glob("*.json")):
        n += 1
        vec = json.loads(path.read_text(encoding="utf-8"))
        peer = _fresh_peer()
        result = vec.get("peer_result") or vec.get("result")
        rec = peer.apply(result)
        exp_gpio = vec.get("expect_gpio")
        if exp_gpio is not None:
            if exp_gpio == {}:
                if peer.store.gpio:
                    print(f"FAIL {path.name}: world mutated, gpio={peer.store.snapshot()['gpio']}")
                    failed += 1
            else:
                for key, level in exp_gpio.items():
                    device, pin_s = key.split(":")
                    got = peer.store.gpio_get(device, int(pin_s))
                    if got != level:
                        print(f"FAIL {path.name}: gpio {key} got {got} want {level}")
                        failed += 1
        if vec.get("expect_landed") is not None:
            if len(rec.landed) != int(vec["expect_landed"]):
                print(f"FAIL {path.name}: landed {len(rec.landed)} want {vec['expect_landed']}")
                failed += 1
        if vec.get("expect_failed") is not None:
            if len(rec.failed) != int(vec["expect_failed"]):
                print(f"FAIL {path.name}: failed {len(rec.failed)} want {vec['expect_failed']}")
                failed += 1
        expect_kind = vec.get("expect_kind")
        if expect_kind in ("authority_refusal", "dispatch_error"):
            if rec.landed or rec.failed:
                print(f"FAIL {path.name}: {expect_kind} mutated receipt")
                failed += 1
            if rec.landed or peer.store.gpio:
                print(f"FAIL {path.name}: {expect_kind} mutated world")
                failed += 1
    print(f"{n} vectors, {failed} failed, profile={PROFILE_HW}")
    return 1 if failed else 0


def doctor() -> int:
    cat = load_catalog()
    print("cek-hw doctor")
    print(f"  law        {cat['law_generation']}")
    print(f"  profile    {cat['profile']}")
    print(f"  pairs      {len(HW_PAIRS)}")
    print(f"  mint       no")
    print(f"  policy     {cat['unknown_op_policy']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cek-hw")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("vectors")
    sub.add_parser("doctor")
    args = p.parse_args(argv)
    if args.cmd == "vectors":
        return run_vectors()
    if args.cmd == "doctor":
        return doctor()
    return 2


if __name__ == "__main__":
    sys.exit(main())
