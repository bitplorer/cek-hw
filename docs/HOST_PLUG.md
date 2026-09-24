# Host plug (cek-host 0.2.0+)

cek-host already:

- accepts `submit(..., project_ops=[...])`
- lets `normalize_stamp` take structure-valid extension pairs (`hw.gpio` is `family.scope`)
- fails closed on bad Caps

You do **not** patch `host_project.py` to add `hw.gpio.write`. Pass Ops in.

`cek_host.legal` is not installed on 0.2.0. Stamp helpers live on `cek_host.catalog`. Host mode is `dev` or `prod`. Cap.subject must equal `args["subject"]`. `resource_of` maps `hw.gpio.write` to `("action", "hw.gpio.write")`, so the scope is `action:hw.gpio.write`, not `device:`.

```python
from cek_host import Host
from cek_host.catalog import normalize_stamp, BASELINE_PAIRS
from cek_host.once import FileOnceBackend
from cek_hw import HW_STAMP, project_action, HwPeer, Registry, demo_press, inverse_ops

host = Host.dev()  # production: Host.prod(secret, FileOnceBackend(...))
host.stamp = normalize_stamp([*BASELINE_PAIRS, *HW_STAMP])

args = {"device": "press-01", "pin": 13, "level": 1, "prior": 0, "subject": "press-01"}
cap = host.mint(
    "hw.gpio.write",
    args=args,
    seal_args=True,
    once=True,
    subject="press-01",
    scopes=["action:hw.gpio.write"],
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
