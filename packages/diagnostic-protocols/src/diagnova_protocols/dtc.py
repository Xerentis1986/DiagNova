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


# Mode → Status-Label (SAE J1979)
DTC_MODE_STATUS = {
    0x03: "stored",
    0x07: "pending",
    0x0A: "permanent",
}


def parse_mode_dtc_response(
    service_response: int,
    data: bytes | list[int],
    *,
    ecu_id: str | None = None,
) -> list[dict]:
    """
    Parst positive Mode-03/07/0A-Antworten (43/47/4A).
    Manche ECUs liefern Count-Byte zuerst – wird erkannt.
    Permanente DTCs (0A) sind nicht löschbar.
    """
    request_mode = service_response - 0x40
    status = DTC_MODE_STATUS.get(request_mode)
    if status is None:
        raise ValueError(f"Unsupported DTC response service 0x{service_response:02X}")

    raw = list(data)
    # Optional leading count (number of codes)
    if raw and raw[0] <= 16 and len(raw) == 1 + raw[0] * 2:
        raw = raw[1:]
    elif raw and len(raw) % 2 == 1:
        raw = raw[1:]

    codes = parse_dtc_bytes(raw)
    clearable = status != "permanent"
    return [
        {
            "code": code,
            "status": status,
            "clearable": clearable,
            "ecu_id": ecu_id if ecu_id is not None else "unknown",
            "message_de": (
                "Permanenter DTC – nicht durch Mode 04 löschbar."
                if not clearable
                else f"DTC ({status})."
            ),
        }
        for code in codes
    ]
