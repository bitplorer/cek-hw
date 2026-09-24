# Research — what already exists, what this repo is allowed to own

Inventory of `cek-framework`, `cek-runtime`, `cek-python`, `ux-channel` as of
the hw-v1 cut. This file is the reason `cek-hw` does **not** reimplement a
Host, a Peer kernel, or a third IR.

## Law (`bitplorer/cek-framework`)

Already frozen. Names we inherit, never rename:

Cap, Intent, Host, Peer, Ops, Result, lineage, reverse, Baseline, profile, receipt.

Hardware is **not** a fifth noun. Device is an L5 Domain pack (`hw.*`) on a Peer,
the same way DOM is `ui.dom.*`. Inner control loops (PID, PWM ticks) are firmware,
not Caps.

## Kernels (`bitplorer/cek-runtime`)

| Piece | Status | Consequence |
|-------|--------|-------------|
| Host kernel | shipped | mint / verify / once / dispatch / lineage / reverse stay there |
| Peer kernel apply loop | shipped (Rust + JS port) | refuse → no mutate; fail_batch vs skip; receipts |
| `cek-ops-baseline` | shipped | kv / log. Do not copy |
| `cek-ops-ui` | shipped | `ui.dom.*`. Pattern to **mirror**, not fork |
| Device in TOPOLOGY / 10-ports | **named, no driver** | this repo's job |
| MCU port | named as future C/Rust Peer | Arduino JSON-floor Peer lives here first |

`host_project` / `domain.rs` already treat pair identity as `(ns, name)`. A
concatenated FQ is a display string. `hw.gpio` + `set` is legal structure
(`family.scope` + token). `hw` + `gpio.set` is a split alias and illegal.

## Host carrier (`bitplorer/cek-python`)

| Piece | Status | How we plug |
|-------|--------|-------------|
| `cek_host.Host.submit(..., project_ops=)` | shipped | pass `project_action(...)` in. Do not patch `host_project.py` |
| `normalize_stamp(..., allow_extension=True)` | shipped | `HW_STAMP` is a structure-valid extension |
| `lineage.inverse_ops` | knows `kv.*`, `ui.dom.morph+snapshot` | **gap**: no `hw.*` branch. Pack `inverse_ops` is the workaround until a 4-line upstream patch |
| once / sealed-args / subject / scopes | shipped | bind `{device, pin}` and `subject=press-01` |
| `cek_surface.carrier` messages | apply / stamp / chrome / done | serial reuses the **shapes**, not the ASGI stack |

## Wire (`bitplorer/ux-channel`)

JSON floor is IR 0.1 and is forever the MCU dialect. CXB is an upgrade for
browsers / runtimes with RAM, not for a 2 KB sketch. Serial NDJSON is framing
of the same messages. Do not invent `hw-bin-0.1`.

## Repeated patterns (DRY isolation)

These show up in every library. **One owner each.**

| Pattern | Owner | Do not |
|---------|-------|--------|
| Cap mint / HMAC / once | Host kernel | mint on Peer or MCU |
| BoundAsk, refuse | Host kernel | "USB is trusted so skip Caps" |
| Apply loop (refuse / order / fail_batch / receipt) | Peer kernel | grow a second kernel here; thin **port** only |
| World + `apply_op` | driver crate per world | mix kv and gpio in one store |
| Pair identity `(ns, name)` | contract + `cek_host.catalog` | concatenate as identity |
| Carrier types `apply/applied/stamp` | surface / ux-channel | new verbs per transport |
| JSON floor | ux-channel SPEC | binary IR on UART |
| Catalog file → constructors → apply → vector | every Domain pack | a fourth FQ list in firmware comments |

What is **new** (this repo only): `catalog/hw-v1.json`, `HwStore`, `hw.*`
constructors + inverse, serial UART framing, device registry, watchdog
interlock, Arduino apply-only firmware, Host `project_ops` helper for hw
actions.

## Topology decision

Gateway Peer first (Python `HwPeer` / Pi, `HwStore` or UART to a dumb MCU).
Native MCU Peer second (this firmware). Host on MCU: never. USB "the host
laptop is trusted" is not authority.

## Reverse physics

| Op | class | why |
|----|-------|-----|
| `hw.gpio.set` + `prior` | snapshot | same role as `ui.dom.morph` snapshot |
| `hw.relay.set` + `prior` | snapshot | |
| `hw.relay.pulse` | non_reversible | the pulse already happened |
| `hw.motor.start` | compensation | inverse is `stop`, not true physics inverse |
| `hw.motor.stop` | non_reversible | |
| `hw.safe.state` | non_reversible | interlock; Host may record the event later |

Lowering `hw.gpio.set → kv.set` is an **audit shadow**. A Baseline Peer storing
that key is not actuating a pin. Reverse of `kv.set` is `kv.delete` — the wrong
physics for GPIO. Do not use lowering as the reverse plan.

## Safety (research, not theatre)

- E-stop is electrical. CEK may authorize software safe-state; it must not be the only stop.
- Watchdog is Peer-local (brown-out / lost-host), analogous to MCU reset. It is not a Cap.
- Sealed args bind `{device,pin}` so a UI cannot retarget.
- Production `once` store is on disk, not process memory.

## Bring-up order ( empirically the only order that does not skip)

1. `HwStore` vectors (this package, no silicon)
2. `MemorySerial` loopback
3. USB-serial to Uno running `cek_hw_peer.ino`
4. Real loads on relays

Skipping 1→3 and wiring a press on day one is how you weld a coil on.
