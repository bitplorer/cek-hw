# Implementation map

## Layout

```text
catalog/hw-v1.json          human copy of the pack
src/cek_hw/data/hw-v1.json  loaded at runtime (source of pairs)
src/cek_hw/catalog.py       pair identity
src/cek_hw/ops.py           constructors, inverse, lowering
src/cek_hw/store.py         world
src/cek_hw/apply.py         driver
src/cek_hw/peer.py          thin apply loop (port)
src/cek_hw/project.py       Host action → Ops
src/cek_hw/serial.py        NDJSON framing
src/cek_hw/registry.py      device map
src/cek_hw/watchdog.py      local interlock
js/hw_apply.mjs             same driver for gateway / lab
firmware/arduino/           MCU port
vectors/                    pack vectors (Peer-only)
```

## Adding an Op

1. Edit `hw-v1.json` (both copies — or only `src/cek_hw/data` + sync).
2. Constructor in `ops.py`.
3. Branch in `apply.py` + `js/hw_apply.mjs`.
4. MCU only if the Uno must speak it.
5. One vector: lands / fails / refuse.
6. Never add mint.

## Testing

```bash
pip install -e ".[dev]"
pytest
python -m cek_hw.cli vectors
python -m cek_hw.cli doctor
```

No `cek-host` required for pack tests.

## Rust

`rust/cek-ops-hw` is a source sketch matching `cek-ops-ui`. Vendor into `cek-runtime` when that workspace is ready to take a third driver crate. Do not publish a second Peer kernel.
