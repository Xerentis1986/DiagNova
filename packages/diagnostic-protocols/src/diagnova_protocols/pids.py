"""Standard Mode 01 PID definitions and scaling (subset for MVP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PidDefinition:
    pid: int
    name: str
    unit: str
    description_de: str
    bytes_needed: int
    formula: Callable[[list[int]], float]


def _a(data: list[int]) -> float:
    return float(data[0])


def _a_minus_40(data: list[int]) -> float:
    return float(data[0] - 40)


def _rpm(data: list[int]) -> float:
    return ((data[0] * 256) + data[1]) / 4.0


def _speed(data: list[int]) -> float:
    return float(data[0])


def _load(data: list[int]) -> float:
    return data[0] * 100.0 / 255.0


def _maf(data: list[int]) -> float:
    return ((data[0] * 256) + data[1]) / 100.0


def _fuel(data: list[int]) -> float:
    return data[0] * 100.0 / 255.0


def _throttle(data: list[int]) -> float:
    return data[0] * 100.0 / 255.0


def _voltage(data: list[int]) -> float:
    return ((data[0] * 256) + data[1]) / 1000.0


PID_DEFINITIONS: dict[int, PidDefinition] = {
    0x04: PidDefinition(0x04, "engine_load", "%", "Berechnete Motorlast", 1, _load),
    0x05: PidDefinition(0x05, "coolant_temp", "°C", "Kühlmitteltemperatur", 1, _a_minus_40),
    0x0C: PidDefinition(0x0C, "rpm", "1/min", "Motordrehzahl", 2, _rpm),
    0x0D: PidDefinition(0x0D, "speed", "km/h", "Fahrzeuggeschwindigkeit", 1, _speed),
    0x0F: PidDefinition(0x0F, "intake_temp", "°C", "Ansauglufttemperatur", 1, _a_minus_40),
    0x10: PidDefinition(0x10, "maf", "g/s", "Luftmassenstrom", 2, _maf),
    0x11: PidDefinition(0x11, "throttle", "%", "Drosselklappenstellung", 1, _throttle),
    0x2F: PidDefinition(0x2F, "fuel_level", "%", "Kraftstofffüllstand", 1, _fuel),
    0x42: PidDefinition(0x42, "control_module_voltage", "V", "Steuergerätespannung", 2, _voltage),
}


def scale_pid_a_b(a: int, b: int = 0, *, pid: int) -> float:
    """Convenience scaler for one- or two-byte PID payloads."""
    definition = PID_DEFINITIONS.get(pid)
    if definition is None:
        raise KeyError(f"Unsupported PID 0x{pid:02X}")
    data = [a] if definition.bytes_needed == 1 else [a, b]
    return definition.formula(data)


def decode_pid(pid: int, data: list[int] | bytes) -> dict:
    """Decode raw PID bytes into a structured reading."""
    definition = PID_DEFINITIONS.get(pid)
    if definition is None:
        raise KeyError(f"Unsupported PID 0x{pid:02X}")
    payload = list(data)
    if len(payload) < definition.bytes_needed:
        raise ValueError(
            f"PID 0x{pid:02X} needs {definition.bytes_needed} bytes, got {len(payload)}"
        )
    value = definition.formula(payload[: definition.bytes_needed])
    return {
        "pid": pid,
        "pid_hex": f"0x{pid:02X}",
        "name": definition.name,
        "description_de": definition.description_de,
        "value": round(value, 3),
        "unit": definition.unit,
    }
