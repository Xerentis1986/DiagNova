"""Supported-PID-Bitmap (Mode 01 PID 00/20/40/60/80/A0)."""

from __future__ import annotations


def parse_pid_bitmap(base_pid: int, data: list[int] | bytes | tuple[int, ...]) -> list[int]:
    """
    Dekodiert 4 Byte Bitmap zu unterstützten PID-Nummern.

    base_pid=0x00 → PIDs 0x01–0x20; base_pid=0x20 → 0x21–0x40; usw.
    Bit 7 von Byte0 = PID (base+1), Bit 0 von Byte3 = PID (base+32).
    """
    if base_pid % 0x20 != 0:
        raise ValueError("base_pid muss 0x00, 0x20, 0x40, … sein")
    payload = list(data)
    if len(payload) < 4:
        raise ValueError(f"PID-Bitmap benötigt 4 Bytes, got {len(payload)}")
    supported: list[int] = []
    for byte_index in range(4):
        byte = payload[byte_index]
        for bit in range(8):
            if byte & (1 << (7 - bit)):
                pid = base_pid + 1 + byte_index * 8 + bit
                supported.append(pid)
    return supported


def merge_supported_pids(bitmaps: dict[int, list[int] | bytes | tuple[int, ...]]) -> list[int]:
    """Merge mehrerer Bitmap-Antworten (z. B. 00 und 20). Sortiert, eindeutig."""
    found: set[int] = set()
    for base, data in bitmaps.items():
        found.update(parse_pid_bitmap(base, data))
    return sorted(found)
