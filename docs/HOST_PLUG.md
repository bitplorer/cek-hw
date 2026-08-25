# Host plug (cek-host 0.1.3+)

cek-host already:

- accepts `submit(..., project_ops=[...])`
- lets `normalize_stamp` take structure-valid extension pairs (`hw.gpio` is `family.scope`)
- fails closed on bad Caps

You do **not** patch `host_project.py` to add `hw.gpio.write`. Pass Ops in.

```python
from cek_host import Host
from cek_host.legal import normalize_stamp, BASELINE_PAIRS
from cek_hw import HW_STAMP, project_action, HwPeer, Registry, demo_press, inverse_ops

host = Host.demo()  # production: Host.production(secret, once=FileOnceBackend(...))
host.stamp = normalize_stamp([*BASELINE_PAIRS, *HW_STAMP])

args = {"device": "press-01", "pin": 13, "level": 1, "prior": 0}
cap = host.mint(
    "hw.gpio.write",
    args=args,
    seal_args=True,
    once=True,
    subject="press-01",
    scopes=["device:press-01"],
)
result = host.submit(
    action="hw.gpio.write",
    args=args,
    cap=cap,
    activity_id="job-1",
    project_ops=project_action("hw.gpio.write", args),
    idempotency_key="job-1:gpio13",
)
assert result.kind == "ok"

reg = Registry(); reg.add(demo_press())
peer = HwPeer(registry=reg)
receipt = peer.apply(result.to_dict())
host.report_receipt("job-1", receipt=receipt.to_dict())

# Reverse: until cek-host.lineage knows hw.*, use pack inverse.
rev = inverse_ops(receipt.landed)
peer.apply({"kind": "ok", "ops": rev})
```

Refuse path (expired / replayed once-Cap / wrong pin in sealed args): `result.ops == []`. Peer must still be called only if you want a receipt of “nothing”; applying a refusal is a no-op.
