# cek-hw

**The missing CEK hardware layer.** L5 `hw.*` Domain pack + Peer driver + serial carrier + Arduino port.

Not law. Not a Host kernel. Not ux-channel.

```text
cek-framework     LAW
cek-runtime       Host/Peer kernels + kv/ui drivers
cek-python        cek-host + cek-surface
ux-channel        wire
cek-hw            hw.* driver · serial · MCU     ← this repo
```

Host still **decides**. Peer still **applies**. GPIO is just another world, like DOM.

```text
mint Cap → submit Intent → Host.verify
        → project_ops (this repo)
        → Result{ hw.gpio.set … }
        → HwPeer.apply / Arduino pins
        → receipt
```

Start at [START.md](START.md). DRY rules: [DRY.md](DRY.md). Research: [docs/RESEARCH.md](docs/RESEARCH.md). Index: [docs/INDEX.md](docs/INDEX.md).

## Install

```bash
pip install -e ".[dev]"
pytest
python -m cek_hw.cli vectors
python -m cek_hw.cli doctor
```

## Use (driver only)

```python
from cek_hw import HwPeer, project_action, gpio_set

peer = HwPeer()
ops = project_action("hw.gpio.write", {"device": "press-01", "pin": 13, "level": 1, "prior": 0})
receipt = peer.apply({"kind": "ok", "ops": ops})
assert peer.store.gpio_get("press-01", 13) == 1
```

A **refused** Result never moves a pin:

```python
peer.apply({"kind": "authority_refusal", "ops": [gpio_set("press-01", 13, 1)], "error": "no"})
assert peer.store.gpio_get("press-01", 13) is None
```

Host integration (does not fork `cek-host`): [docs/HOST_PLUG.md](docs/HOST_PLUG.md).

## What is new vs already shipped

| Already exists | This repo |
|----------------|-----------|
| Cap machine, once, lineage | — |
| Peer apply loop (Rust/JS) | Thin **port** for hw-v1 / MCU |
| `ui.dom.*` driver | `hw.gpio\|relay\|motor\|safe` driver |
| WS / subprocess carriers | **Serial NDJSON** |
| Browser / Node peers | **Arduino** apply-only firmware |

## Profile `hw-v1`

Pairs (identity is `(ns, name)`, not the concatenated string):

- `hw.gpio` `set`
- `hw.relay` `set` / `pulse`
- `hw.motor` `start` / `stop`
- `hw.safe` `state`

Unknown Ops **fail the batch**. Hardware must not skip.

## MCU

[firmware/arduino/cek_hw_peer](firmware/arduino/cek_hw_peer) — JSON floor, no mint, watchdog safe-state.

Bring-up: `HwStore` vectors → serial loopback → USB-serial Uno → real loads.

## License

MIT
