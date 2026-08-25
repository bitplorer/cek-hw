# Architecture

```text
L7 app
  → cek-host (decide)     [upstream — not this repo]
  → project_ops from cek_hw.project_action
  → Result{Ops} over ux-channel / serial NDJSON
  → HwPeer / Arduino      [this repo]
       apply_op → HwStore or MCU pins
       receipt → Host.report_receipt
```

Four quadrants, this repo fills the **bottom-right** plus a sliver of Host project:

| | Kernel | Runtime |
|---|---|---|
| Host | *upstream* | stamp + `project_ops` plug |
| Peer | thin hw-v1 port of apply loop | driver + serial + MCU + watchdog |

## Topologies

**A. Gateway (ship first)**  
Python/JS `HwPeer` on a Pi. UART to a dumb MCU, or `HwStore` for bring-up. Kernel unchanged.

**B. Native MCU Peer**  
`firmware/arduino` speaks JSON floor. Host stays on Python.

Do not put Host kernel on the MCU.

## Data

Ops are data:

```json
{"ns":"hw.gpio","name":"set","payload":{"device":"press-01","pin":13,"level":1,"prior":0}}
```

`prior` is ignored at apply (like ui morph `snapshot`). Inverse uses it.

## Watchdog

Peer-local. If Host goes quiet, pins go safe. Event `hw.watchdog` is not a Cap and not lineage until Host chooses to record it.
