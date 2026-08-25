"""Optional: only runs if cek-host is installed. Skips cleanly otherwise."""

from __future__ import annotations

try:
    from cek_host import Host
    from cek_host.legal import BASELINE_PAIRS, normalize_stamp
except ImportError:
    print("cek-host not installed — driver-only bench is demos/bench.py")
    raise SystemExit(0)

from cek_hw import HW_STAMP, HwPeer, Registry, demo_press, project_action


def main() -> None:
    host = Host.demo()
    # dicts and tuples are both legal stamp items; HW_STAMP is the extension.
    host.stamp = normalize_stamp([*BASELINE_PAIRS, *HW_STAMP])
    args = {"device": "press-01", "pin": 13, "level": 1, "prior": 0}
    cap = host.mint("hw.gpio.write", args=args, seal_args=True, once=True, subject="press-01")
    result = host.submit(
        action="hw.gpio.write",
        args=args,
        cap=cap,
        project_ops=project_action("hw.gpio.write", args),
    )
    print("host", result.kind, "ops", result.ops)
    reg = Registry()
    reg.add(demo_press())
    peer = HwPeer(registry=reg)
    rec = peer.apply(result.to_dict())
    print("peer landed", len(rec.landed), "gpio", peer.store.gpio_get("press-01", 13))


if __name__ == "__main__":
    main()
