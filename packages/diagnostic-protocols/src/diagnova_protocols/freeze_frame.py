"""Mode 02 Freeze-Frame – Dekodierung bekannter PIDs im Frame."""

from __future__ import annotations

from diagnova_protocols.pids import PID_DEFINITIONS, decode_pid


def decode_freeze_frame(
    frame_payload: list[int] | bytes | tuple[int, ...],
    *,
    dtc_high: int | None = None,
    dtc_low: int | None = None,
) -> dict:
    """
    Interpretiert Freeze-Frame-Daten.

    Erwartet entweder:
    - Rohe PID-Wert-Paare nach Frame-Nummer, oder
    - Einzel-PID-Antwort 42 <pid> <data…>

    Unbekannte PIDs werden als raw belassen – Wert wird nicht als null erfunden.
    """
    data = list(frame_payload)
    readings: list[dict] = []
    unknown: list[dict] = []
    i = 0
    while i < len(data):
        pid = data[i]
        definition = PID_DEFINITIONS.get(pid)
        if definition is None:
            unknown.append(
                {
                    "pid": pid,
                    "pid_hex": f"0x{pid:02X}",
                    "status": "unknown_pid",
                    "message_de": "PID im Freeze-Frame nicht in bekannter Skala – Wert nicht interpretiert.",
                }
            )
            i += 1
            continue
        need = definition.bytes_needed
        if i + 1 + need > len(data):
            unknown.append(
                {
                    "pid": pid,
                    "pid_hex": f"0x{pid:02X}",
                    "status": "truncated",
                    "message_de": "Freeze-Frame-Daten unvollständig für diese PID.",
                }
            )
            break
        chunk = data[i + 1 : i + 1 + need]
        decoded = decode_pid(pid, chunk)
        decoded["status"] = "ok"
        readings.append(decoded)
        i += 1 + need

    dtc_code = None
    if dtc_high is not None and dtc_low is not None:
        from diagnova_protocols.dtc import decode_dtc

        if not (dtc_high == 0 and dtc_low == 0):
            dtc_code = decode_dtc(dtc_high, dtc_low)

    return {
        "dtc": dtc_code,
        "readings": readings,
        "unknown_or_truncated": unknown,
        "status": "ok" if readings or dtc_code else "empty",
        "message_de": (
            "Freeze-Frame dekodiert."
            if readings or dtc_code
            else "Kein Freeze-Frame-Inhalt – Status empty (nicht null)."
        ),
    }
