# Requirements

## Law constraints (already frozen — we obey, we do not restated as code)

1. Cap-only authority at the Host boundary
2. Effects leave Host only as data Ops
3. Peer never mints root Caps
4. Fail closed on unclear authority
5. Honest reverse or `non_reversible` mark
6. Baseline stays valid; hw is a Domain pack above it
7. trace is not permission
8. Pair identity `(ns, name)`

## Functional

| ID | Requirement | Owner |
|----|-------------|-------|
| F1 | `hw.gpio.set` lands on a declared pin | driver |
| F2 | Unknown pin / device → failed Op, world unchanged | driver + registry |
| F3 | `authority_refusal` / `dispatch_error` → zero GPIO | Peer port |
| F4 | Unknown Op → `fail_batch` (do not skip) | Peer port |
| F5 | Receipt required (`landed` / `failed`) | Peer port |
| F6 | `prior` on set → inverse restores that level | `ops.inverse_op` |
| F7 | `relay.pulse` / `motor.start` reverse classes honest | catalog |
| F8 | Serial NDJSON frames match surface carrier types | serial |
| F9 | MCU watchdog → local `safe_state` + event | firmware / watchdog |
| F10 | Host integration via `project_ops` + stamp extension | project + DRY |

## Non-functional

| ID | Requirement |
|----|-------------|
| N1 | Python 3.10+, zero required deps |
| N2 | MCU peer fits Uno flash; no ArduinoJson required |
| N3 | Inner loop ≤ firmware; Host path is command-rate |
| N4 | Vectors run without `cek-host` installed |
| N5 | Optional `cek-host` plug is documented, not vendored |

## Hardware assumptions (v1)

- Digital GPIO 0/1 only (PWM = hw-v2)
- One Host, many device Peers
- Lost host is unsafe → watchdog to declared safe levels
- Physical actuation is at-least-once on the wire unless `once` Cap + idempotency on Host (upstream)

## Safety

- E-stop hardware is **electrical**, not a Cap. CEK can *authorize* a software safe-state; it must not be the only stop.
- Sealed args bind `{device, pin}` so a UI cannot retarget an e-stop pin.
- Subject bind Cap to `press-01`.
- Production Host: `once` store on disk, not memory.
