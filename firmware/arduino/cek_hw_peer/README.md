# Arduino hw-v1 Peer

Apply-only. **No mint. No Cap verify.** Host already decided.

## Wire

115200 8N1. JSON floor, one object per line (same as `cek_surface` NDJSON).

Host → device:

```json
{"type":"apply","result":{"kind":"ok","ops":[{"ns":"hw.gpio","name":"set","payload":{"device":"press-01","pin":13,"level":1}}]}}
```

`kind=authority_refusal` → pins unchanged.

Device → host:

```json
{"type":"applied","receipt":{"landed_count":1,"failed_count":0}}
```

Lost host → watchdog drives every known pin to `SAFE_LEVEL` and emits `hw.watchdog`. That is an interlock, not a Cap.

## Pins (edit in `.ino`)

Default known set: 3, 7, 13. Unknown pin → failed, not invented.

## Do not

- Verify Caps on the MCU
- Skip unknown Ops (fail the batch)
- Run a PID / inner loop through CEK — firmware keeps realtime; CEK authorizes set-points
