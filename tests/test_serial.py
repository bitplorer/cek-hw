from cek_hw import HwPeer, gpio_set, open_serial_memory
from cek_hw.serial import MemorySerial, SerialPeerAdapter, encode, decode_line


def test_ndjson_roundtrip():
    raw = encode({"type": "apply", "result": {"kind": "ok", "ops": []}})
    assert raw.endswith(b"\n")
    msg = decode_line(raw)
    assert msg["type"] == "apply"


def test_serial_apply_lands():
    carrier = open_serial_memory()
    result = {"kind": "ok", "ops": [gpio_set("press-01", 13, 1, prior=0)]}
    reply = carrier.apply(result)
    assert reply["type"] == "applied"
    assert reply["receipt"]["landed"]
    assert reply["world"]["gpio"]["press-01:13"] == 1


def test_serial_refuse_silent():
    carrier = open_serial_memory()
    reply = carrier.apply(
        {
            "kind": "authority_refusal",
            "ops": [gpio_set("press-01", 13, 1)],
            "error": "no",
        }
    )
    assert reply["receipt"]["landed"] == []
    assert "press-01:13" not in reply["world"]["gpio"]


def test_stamp_ack():
    link = MemorySerial()
    adapter = SerialPeerAdapter(HwPeer(), link)
    link.host_send({"type": "stamp", "pairs": [{"ns": "hw.gpio", "name": "set"}]})
    reply = adapter.pump()
    assert reply["type"] == "stamp_ack"
