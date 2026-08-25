"""Bring-up bench: fake world, no Host, no serial.

This is the KvStore-style first slice. GPIO from Host comes after this is green.
"""

from __future__ import annotations

from cek_hw import HwPeer, Registry, demo_press, project_action


def main() -> None:
    reg = Registry()
    reg.add(demo_press())
    peer = HwPeer(registry=reg)
    ops = project_action(
        "hw.gpio.write",
        {"device": "press-01", "pin": 13, "level": 1, "prior": 0},
    )
    rec = peer.apply({"kind": "ok", "ops": ops})
    print("landed", len(rec.landed), "gpio", peer.store.snapshot()["gpio"])
    rec = peer.apply({"kind": "authority_refusal", "ops": ops, "error": "no"})
    print("refuse landed", len(rec.landed), "gpio still", peer.store.gpio_get("press-01", 13))


if __name__ == "__main__":
    main()
