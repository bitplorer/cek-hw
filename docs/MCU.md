# MCU port

cek-runtime already named this port: *“MCU / device → C/Rust embedded Peer with tiny profile”*.

## Duties on silicon

1. Parse JSON floor lines
2. If Result.kind is refuse → do nothing
3. Apply known `hw.*` Ops in order
4. Unknown Op → fail the rest
5. Receipt (even a count is enough on Uno)
6. Watchdog safe-state
7. **Never mint**

## Not on silicon

Cap HMAC, Ed25519, once-store, lineage, Host project, CXB.

## Bring-up order

1. `HwStore` vectors (no hardware)
2. Serial loopback (`MemorySerial`)
3. USB-serial to Uno running `cek_hw_peer.ino`
4. Only then real loads on relays
