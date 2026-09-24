# DRY — what this repo owns, what it must not copy

Repeated patterns already exist in `cek-framework`, `cek-runtime`, `cek-python`, `ux-channel`. Copying them here would fork the law.

Research notes: [docs/RESEARCH.md](docs/RESEARCH.md).

## Single sources (do not reimplement)

| Pattern | Lives in | This repo does |
|---------|----------|----------------|
| Cap mint / verify / once / sealed-args / subject / scopes | `cek-host` / `cek-host-kernel` | Call `Host.submit(..., project_ops=...)` |
| BoundAsk, fail-closed refuse | Host kernel | Nothing |
| lineage commit + `end_activity` | `cek_host.lineage` | Export `inverse_ops` for hw snapshot; do not copy `lineage.py` |
| Peer apply loop (skip / fail_batch / receipt) | `cek-peer-kernel` | **Thin port** in `peer.py` / MCU `.ino` — same semantics, documented as a port |
| kv / log / ui.dom drivers | `cek-ops-baseline`, `cek-ops-ui` | New world `HwStore` only |
| Intent / Result / Op JSON shapes | `cek-contract` + ux-channel SPEC | Reuse the dicts; no new IR |
| Carrier protocol `apply/stamp/chrome/done` | `cek_surface.carrier` | `serial.py` is **framing** (UART NDJSON), same messages |
| Pair identity `(ns, name)` | `cek_host.catalog` / `domain.rs` | hw packs only; `normalize_stamp` already accepts extension pairs |
| Structure gate (`family.scope`, token name) | `cek_host.structure` | `hw.gpio` already passes `validate_pair` |
| JSON floor | ux-channel IR 0.1 | MCU speaks JSON floor; no custom binary IR |

## Isolated once here (the actual product)

| Unit | Analog upstream | Why it is new |
|------|-----------------|---------------|
| `catalog/hw-v1.json` | `domain.rs` UI decls | New L5 pack |
| `ops.py` constructors + inverse | `ui.rs` | New pairs |
| `store.py` HwStore | `KvStore` / `UiStore` | New world |
| `apply.py` `apply_op` | `cek_ops_ui::apply_op` | New driver |
| `project.py` | `host_project.project_action` | hw actions only; passed in, not patched into cek-host |
| `serial.py` MemorySerial / NDJSON | `SubprocessNdjsonCarrier` | UART framing |
| `registry.py` | (none) | Device identity + pin map |
| `watchdog.py` | (none) | Peer-local interlock |
| `firmware/arduino` | `ports/cek-peer-js` | MCU port |

## How to plug without forks

```python
from cek_host import Host
from cek_host.catalog import normalize_stamp, BASELINE_PAIRS
from cek_hw import HW_STAMP, project_action, HwPeer, demo_press, Registry

host = Host(secret=secret)
host.stamp = normalize_stamp([*BASELINE_PAIRS, *HW_STAMP])

args = {"device": "press-01", "pin": 13, "level": 1, "prior": 0, "subject": "press-01"}
cap = host.mint("hw.gpio.write", args=args, seal_args=True, once=True, subject="press-01")
ops = project_action("hw.gpio.write", args)          # this repo
result = host.submit(action="hw.gpio.write", args=args, cap=cap, project_ops=ops)

reg = Registry(); reg.add(demo_press())
peer = HwPeer(registry=reg)                          # this repo
receipt = peer.apply(result.to_dict())
host.report_receipt("job-1", receipt=receipt.to_dict())
```

`cek-host` does not need a new action table if you always pass `project_ops`.

## Inverse gap (one upstream patch, not a copy)

`cek_host.lineage.inverse_ops` knows `kv.*` and `ui.dom.morph+snapshot`. It does not know `hw.gpio.set+prior`.

Until that 4-line branch lands upstream, **this pack's `inverse_ops`** is the reverse plan. Apply it as compensation Ops under a recovery Cap (or `host.submit_ops`). Do not copy `lineage.py`.

Suggested upstream patch (for later, not here):

```python
elif ns == "hw.gpio" and name == "set" and "prior" in payload:
    inv.append({... level: payload["prior"] ...})
```

## Catalog is the one file that must not fork

`catalog/hw-v1.json` → Python `catalog.py` loader → JS `HW_PAIRS` (keep in sync) → Arduino `KNOWN_PINS` (device-local).

If you add an Op: edit the JSON, then constructors, `apply_op`, one vector. Never a fourth list of FQs.

## Inner loop is not CEK

PID / PWM ticks stay in firmware. CEK authorizes `hw.motor.start {rpm: 3000}` once. Repeating Host.submit at 1 kHz is a misuse, not a missing feature.
