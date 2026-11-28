"""ISO 15765-2 ISO-TP Framing (dokumentierte PCI-Typen).

Nur Framing/Segmentierung – keine OEM-Payloads.
PCI-Typen: SF (0x0), FF (0x1), CF (0x2), FC (0x3).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class IsoTpFrameType(str, Enum):
    SINGLE = "single"
    FIRST = "first"
    CONSECUTIVE = "consecutive"
    FLOW_CONTROL = "flow_control"
    UNKNOWN = "unknown"


class FlowStatus(str, Enum):
    CONTINUE = "continue_to_send"
    WAIT = "wait"
    OVERFLOW = "overflow"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IsoTpFrame:
    frame_type: IsoTpFrameType
    payload: tuple[int, ...]
    total_length: int | None = None
    sequence: int | None = None
    flow_status: FlowStatus | None = None
    block_size: int | None = None
    st_min: int | None = None
    raw: tuple[int, ...] = ()


def parse_isotp_pci(data: Iterable[int]) -> IsoTpFrame:
    """Parst ein CAN-Frame (bis 8 Byte klassisch) als ISO-TP."""
    buf = tuple(int(b) & 0xFF for b in data)
    if not buf:
        return IsoTpFrame(IsoTpFrameType.UNKNOWN, (), raw=buf)

    pci = buf[0]
    frame_type_nibble = (pci >> 4) & 0x0F

    if frame_type_nibble == 0x0:
        length = pci & 0x0F
        payload = buf[1 : 1 + length]
        return IsoTpFrame(IsoTpFrameType.SINGLE, tuple(payload), total_length=length, raw=buf)

    if frame_type_nibble == 0x1:
        if len(buf) < 2:
            return IsoTpFrame(IsoTpFrameType.UNKNOWN, (), raw=buf)
        total = ((pci & 0x0F) << 8) | buf[1]
        payload = buf[2:]
        return IsoTpFrame(IsoTpFrameType.FIRST, tuple(payload), total_length=total, raw=buf)

    if frame_type_nibble == 0x2:
        seq = pci & 0x0F
        return IsoTpFrame(IsoTpFrameType.CONSECUTIVE, tuple(buf[1:]), sequence=seq, raw=buf)

    if frame_type_nibble == 0x3:
        fs_n = pci & 0x0F
        fs = {
            0: FlowStatus.CONTINUE,
            1: FlowStatus.WAIT,
            2: FlowStatus.OVERFLOW,
        }.get(fs_n, FlowStatus.UNKNOWN)
        bs = buf[1] if len(buf) > 1 else None
        st = buf[2] if len(buf) > 2 else None
        return IsoTpFrame(
            IsoTpFrameType.FLOW_CONTROL,
            (),
            flow_status=fs,
            block_size=bs,
            st_min=st,
            raw=buf,
        )

    return IsoTpFrame(IsoTpFrameType.UNKNOWN, (), raw=buf)


def reassemble_isotp(frames: list[IsoTpFrame]) -> tuple[bytes | None, str]:
    """Setzt FF+CF zu einem Payload zusammen. Status explizit bei Fehlern."""
    if not frames:
        return None, "empty"
    first = frames[0]
    if first.frame_type == IsoTpFrameType.SINGLE:
        return bytes(first.payload), "ok"
    if first.frame_type != IsoTpFrameType.FIRST or first.total_length is None:
        return None, "expected_first_or_single"
    parts = bytearray(first.payload)
    expected_seq = 1
    for fr in frames[1:]:
        if fr.frame_type != IsoTpFrameType.CONSECUTIVE:
            return None, "unexpected_frame"
        if fr.sequence != (expected_seq & 0x0F):
            return None, "sequence_mismatch"
        parts.extend(fr.payload)
        expected_seq += 1
    if len(parts) < first.total_length:
        return None, "incomplete"
    return bytes(parts[: first.total_length]), "ok"


# Dokumentierte Testvektoren (klassische 8-Byte CAN, öffentlich nachvollziehbar)
TEST_VECTORS: list[dict] = [
    {
        "name": "single_frame_obd_pid",
        "bytes": [0x03, 0x41, 0x0C, 0x1F, 0x40, 0x00, 0x00, 0x00],
        "expect_type": IsoTpFrameType.SINGLE,
        "expect_length": 3,
    },
    {
        "name": "first_frame_vin_start",
        "bytes": [0x10, 0x14, 0x49, 0x02, 0x01, 0x57, 0x56, 0x57],
        "expect_type": IsoTpFrameType.FIRST,
        "expect_length": 20,
    },
    {
        "name": "flow_control_cts",
        "bytes": [0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        "expect_type": IsoTpFrameType.FLOW_CONTROL,
        "expect_flow": FlowStatus.CONTINUE,
    },
]
