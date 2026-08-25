"""Serial NDJSON carrier — framing only.

Message shapes are identical to cek-surface carriers:
  apply / applied / stamp / stamp_ack / chrome / done / event

Do not invent a second IR. JSON floor forever; CXB is an ux-channel upgrade
and does not belong on a 2KB MCU.

pyserial is optional. Tests use MemorySerial (two ends of a fake UART).
"""

from __future__ import annotations

import json
from typing import Any

from .peer import HwPeer, Receipt


def encode(msg: dict[str, Any]) -> bytes:
    return (json.dumps(msg, separators=(",", ":")) + "\n").encode("utf-8")


def decode_line(line: str | bytes) -> dict[str, Any] | None:
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    line = line.strip()
    if not line:
        return None
    return json.loads(line)


class MemorySerial:
    """Loopback UART for tests. Host writes to `tx`, Peer reads `tx` as rx."""

    def __init__(self) -> None:
        self.host_to_peer: list[bytes] = []
        self.peer_to_host: list[bytes] = []

    def host_send(self, msg: dict[str, Any]) -> None:
        self.host_to_peer.append(encode(msg))

    def peer_recv(self) -> dict[str, Any] | None:
        if not self.host_to_peer:
            return None
        return decode_line(self.host_to_peer.pop(0))

    def peer_send(self, msg: dict[str, Any]) -> None:
        self.peer_to_host.append(encode(msg))

    def host_recv(self) -> dict[str, Any] | None:
        if not self.peer_to_host:
            return None
        return decode_line(self.peer_to_host.pop(0))


class SerialPeerAdapter:
    """Drive an HwPeer over NDJSON frames. Transport, not a kernel."""

    def __init__(self, peer: HwPeer, link: MemorySerial | None = None) -> None:
        self.peer = peer
        self.link = link or MemorySerial()

    def on_frame(self, msg: dict[str, Any]) -> dict[str, Any]:
        kind = msg.get("type")
        if kind == "hello":
            return {"type": "manifest", "manifest": self.peer.manifest()}
        if kind == "stamp":
            return {"type": "stamp_ack", "pairs": msg.get("pairs") or []}
        if kind == "apply":
            receipt: Receipt = self.peer.apply(msg.get("result") or {})
            return {
                "type": "applied",
                "receipt": receipt.to_dict(),
                "world": self.peer.store.snapshot(),
            }
        if kind == "done":
            return {"type": "bye"}
        return {"type": "unknown", "got": kind}

    def pump(self) -> dict[str, Any] | None:
        msg = self.link.peer_recv()
        if msg is None:
            return None
        reply = self.on_frame(msg)
        self.link.peer_send(reply)
        return reply


class SerialCarrier:
    """Host-side carrier matching cek_surface.Carrier protocol (subset)."""

    name = "serial"

    def __init__(self, adapter: SerialPeerAdapter) -> None:
        self.adapter = adapter

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        self.adapter.link.host_send({"type": "apply", "result": result})
        reply = self.adapter.pump()
        return reply or {"type": "applied", "receipt": {"landed": [], "failed": []}}

    def stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        self.adapter.link.host_send({"type": "stamp", "pairs": pairs})
        return self.adapter.pump() or {"type": "stamp_ack", "pairs": pairs}

    def close(self) -> None:
        self.adapter.link.host_send({"type": "done"})
        self.adapter.pump()


def open_serial_memory(peer: HwPeer | None = None) -> SerialCarrier:
    peer = peer or HwPeer()
    adapter = SerialPeerAdapter(peer)
    return SerialCarrier(adapter)
