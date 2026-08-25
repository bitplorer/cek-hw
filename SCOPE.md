# Scope

## In

- L5 `hw.*` Domain pack (decls, constructors, inverse, lowering-as-audit)
- Peer driver `HwStore` + `apply_op`
- Thin hw-v1 Peer port (receipt, fail_batch, no mint)
- Serial NDJSON carrier (JSON floor)
- Device registry + watchdog interlock
- Arduino apply-only firmware
- Conformance vectors for the pack
- Host **project** helper (`project_ops` plug)

## Out

- Law / axioms (`cek-framework`)
- Host kernel (`cek-host`, `cek-host-kernel`)
- Full Peer kernel (`cek-peer-kernel`) except the documented thin port
- ux-channel codecs, CXB, ASGI
- kv / log / ui.dom worlds
- Realtime control loops
- New Cap kinds

## Kill if

- A PR adds `mint` to Peer or firmware
- A PR verifies Caps on the MCU
- A PR introduces a second IR beside JSON floor
- A PR copies `lineage.py` / `host.py` / `cap.py`
- A PR treats USB “trusted” as authority
