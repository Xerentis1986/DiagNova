"""Mode 01 PID 01 – MIL-Status und Readiness-Monitore (SAE J1979)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessStatus:
    mil_on: bool
    dtc_count: int
    ignition_type: str  # "spark" | "compression" | "unknown"
    monitors: dict[str, dict[str, bool | str]]
    # Jeder Monitor: {"available": bool, "complete": bool} – nie null
    raw_a: int
    raw_b: int
    raw_c: int
    raw_d: int


_SPARK_NAMES = [
    ("misfire", 0),
    ("fuel_system", 1),
    ("components", 2),
    # Bit 3 reserved
    ("catalyst", 0),  # C bit0 / D bit0 incomplete
    ("heated_catalyst", 1),
    ("evap", 2),
    ("secondary_air", 3),
    ("ac_refrigerant", 4),
    ("o2_sensor", 5),
    ("o2_heater", 6),
    ("egr", 7),
]


def decode_readiness(data: list[int] | bytes | tuple[int, ...]) -> ReadinessStatus:
    """
    A = MIL + DTC count; B = continuous monitors;
    C/D = non-continuous (spark vs compression je nach Bit 3 von B).
    Unbekannte/unsupported Monitore: available=False, complete bleibt False – nicht null.
    """
    payload = list(data)
    if len(payload) < 4:
        raise ValueError(f"Readiness PID 01 benötigt 4 Bytes, got {len(payload)}")
    a, b, c, d = payload[0], payload[1], payload[2], payload[3]

    mil_on = bool(a & 0x80)
    dtc_count = a & 0x7F
    compression = bool(b & 0x08)
    ignition = "compression" if compression else "spark"

    monitors: dict[str, dict[str, bool | str]] = {}

    # Continuous (spark & compression): bits 0–2 in B available, bits 4–6 incomplete
    for name, bit in (("misfire", 0), ("fuel_system", 1), ("components", 2)):
        available = bool(b & (1 << bit))
        incomplete = bool(b & (1 << (bit + 4)))
        monitors[name] = {
            "available": available,
            "complete": available and not incomplete,
            "status": "complete" if (available and not incomplete) else ("incomplete" if available else "not_supported"),
        }

    if not compression:
        spark_map = [
            ("catalyst", 0),
            ("heated_catalyst", 1),
            ("evap", 2),
            ("secondary_air", 3),
            ("ac_refrigerant", 4),
            ("o2_sensor", 5),
            ("o2_heater", 6),
            ("egr", 7),
        ]
        for name, bit in spark_map:
            available = bool(c & (1 << bit))
            incomplete = bool(d & (1 << bit))
            monitors[name] = {
                "available": available,
                "complete": available and not incomplete,
                "status": "complete" if (available and not incomplete) else ("incomplete" if available else "not_supported"),
            }
    else:
        diesel_map = [
            ("nmhc_catalyst", 0),
            ("nox_scr", 1),
            ("reserved", 2),
            ("boost_pressure", 3),
            ("exhaust_gas_sensor", 5),
            ("pm_filter", 6),
            ("egr_vvt", 7),
        ]
        for name, bit in diesel_map:
            if name == "reserved":
                continue
            available = bool(c & (1 << bit))
            incomplete = bool(d & (1 << bit))
            monitors[name] = {
                "available": available,
                "complete": available and not incomplete,
                "status": "complete" if (available and not incomplete) else ("incomplete" if available else "not_supported"),
            }

    return ReadinessStatus(
        mil_on=mil_on,
        dtc_count=dtc_count,
        ignition_type=ignition,
        monitors=monitors,
        raw_a=a,
        raw_b=b,
        raw_c=c,
        raw_d=d,
    )


def readiness_as_simple_bool_map(status: ReadinessStatus) -> dict[str, bool]:
    """UI-kompatible Map: True = complete (oder not_supported → False für 'offen'-Anzeige)."""
    return {name: bool(info["complete"]) for name, info in status.monitors.items()}
