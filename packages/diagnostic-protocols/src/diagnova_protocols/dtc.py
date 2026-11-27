"""DTC decoding for standard OBD-II two-byte codes (SAE J2012 style)."""

from __future__ import annotations

_SYSTEM = {
    0: "P",  # Powertrain
    1: "C",  # Chassis
    2: "B",  # Body
    3: "U",  # Network
}


def format_dtc(code: str) -> str:
    """Normalize a DTC string to uppercase without spaces."""
    return code.strip().upper().replace(" ", "")


def decode_dtc(high: int, low: int) -> str:
    """Decode two DTC bytes into a 5-character code (e.g. P0301)."""
    if not (0 <= high <= 255 and 0 <= low <= 255):
        raise ValueError("DTC bytes must be 0..255")
    system = _SYSTEM[(high >> 6) & 0x03]
    first_digit = (high >> 4) & 0x03
    second = high & 0x0F
    return f"{system}{first_digit}{second:X}{low:02X}"


def parse_dtc_bytes(data: bytes | list[int]) -> list[str]:
    """Parse a sequence of DTC byte pairs; skip 0x0000 empty slots."""
    raw = list(data)
    if len(raw) % 2 != 0:
        raise ValueError("DTC payload length must be even")
    codes: list[str] = []
    for i in range(0, len(raw), 2):
        high, low = raw[i], raw[i + 1]
        if high == 0 and low == 0:
            continue
        codes.append(decode_dtc(high, low))
    return codes
