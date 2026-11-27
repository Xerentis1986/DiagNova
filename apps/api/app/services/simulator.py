"""Simulierter OBD-Adapter – erzeugt keine echten Fahrzeugbefehle."""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone

from diagnova_protocols import PID_DEFINITIONS, decode_pid

from app.schemas.api import ConnectionStatusOut, DtcOut, LiveDataOut, PidReadingOut

SIMULATOR_VIN_SUFFIX = {
    # deterministic per vehicle make for demo consistency
}


DTC_CATALOG: dict[str, tuple[str, str]] = {
    "P0301": ("Zündaussetzer Zylinder 1", "warning"),
    "P0171": ("Gemisch zu mager (Bank 1)", "warning"),
    "P0420": ("Katalysatorwirkungsgrad unter Schwellwert (Bank 1)", "critical"),
    "P0128": ("Kühlmittelthermostat – Temperatur unter Regelbereich", "info"),
    "U0100": ("Kommunikationsverlust mit ECM/PCM", "critical"),
    "C0035": ("Raddrehzahlsensor vorne links – Störung", "warning"),
}


def connection_status() -> ConnectionStatusOut:
    return ConnectionStatusOut(
        connected=True,
        mode="simulator",
        adapter_name="DiagNova OBD-Simulator v1",
        data_source="simulated",
        message_de="Simulierter Adapter aktiv – keine echte Fahrzeugverbindung.",
        last_heartbeat=datetime.now(timezone.utc),
    )


def simulated_vin(make: str, vehicle_id: str) -> str:
    """Generate a plausible demo VIN (not a real vehicle)."""
    wmi = {
        "Volkswagen": "WVW",
        "Audi": "WAU",
        "BMW": "WBA",
        "Mercedes-Benz": "WDD",
        "Škoda": "TMB",
        "Seat": "VSS",
        "Opel": "W0L",
        "Ford": "WF0",
        "Toyota": "JTD",
    }.get(make, "XXX")
    digest = "".join(c for c in vehicle_id.upper() if c.isalnum())[:8].ljust(8, "0")
    return f"{wmi}ZZZ{digest}DEMO"[:17]


def list_dtcs(vehicle_id: str) -> list[DtcOut]:
    """Deterministic-ish DTC set based on vehicle id hash."""
    seed = sum(ord(c) for c in vehicle_id)
    rng = random.Random(seed)
    codes = list(DTC_CATALOG.keys())
    pick = rng.sample(codes, k=rng.randint(1, 3))
    pending_pool = [c for c in codes if c not in pick]
    pending = rng.sample(pending_pool, k=1) if pending_pool else []
    result: list[DtcOut] = []
    for code in pick:
        desc, sev = DTC_CATALOG[code]
        result.append(DtcOut(code=code, status="stored", description_de=desc, severity=sev))  # type: ignore[arg-type]
    for code in pending:
        desc, sev = DTC_CATALOG[code]
        result.append(DtcOut(code=code, status="pending", description_de=desc, severity=sev))  # type: ignore[arg-type]
    return result


def _oscillate(base: float, amplitude: float, phase: float) -> float:
    t = datetime.now(timezone.utc).timestamp()
    return base + amplitude * math.sin(t / 3.0 + phase)


def live_data(vehicle_id: str, vin: str) -> LiveDataOut:
    now = datetime.now(timezone.utc)
    seed = sum(ord(c) for c in vehicle_id)
    rng = random.Random(seed + int(now.timestamp()) // 2)

    raw_map = {
        0x04: [int(_oscillate(90, 20, 0.1) * 255 / 100)],
        0x05: [int(_oscillate(90, 5, 0.2) + 40)],
        0x0C: _rpm_bytes(_oscillate(1800, 400, 0.5)),
        0x0D: [int(max(0, _oscillate(48, 20, 1.0)))],
        0x0F: [int(_oscillate(28, 4, 0.7) + 40)],
        0x10: _maf_bytes(_oscillate(12.5, 3.0, 0.3)),
        0x11: [int(_oscillate(18, 8, 0.9) * 255 / 100)],
        0x2F: [int(62 * 255 / 100)],
        0x42: _voltage_bytes(_oscillate(13.8, 0.3, 0.4)),
    }

    readings: list[PidReadingOut] = []
    for pid, data in raw_map.items():
        decoded = decode_pid(pid, data)
        readings.append(
            PidReadingOut(
                **decoded,
                timestamp=now,
            )
        )

    readiness = {
        "misfire": True,
        "fuel_system": True,
        "components": True,
        "catalyst": rng.random() > 0.3,
        "heated_catalyst": False,
        "evap": rng.random() > 0.4,
        "secondary_air": False,
        "o2_sensor": True,
        "o2_heater": True,
        "egr": rng.random() > 0.5,
    }

    freeze = {
        "rpm": next(r.value for r in readings if r.name == "rpm"),
        "speed": next(r.value for r in readings if r.name == "speed"),
        "coolant_temp": next(r.value for r in readings if r.name == "coolant_temp"),
        "load": next(r.value for r in readings if r.name == "engine_load"),
        "note": "Simulierter Freeze-Frame (Demo)",
    }

    return LiveDataOut(
        data_source="simulated",
        vehicle_id=vehicle_id,
        vin=vin,
        readings=readings,
        readiness=readiness,
        freeze_frame=freeze,
    )


def _rpm_bytes(rpm: float) -> list[int]:
    raw = int(max(0, rpm) * 4)
    return [(raw >> 8) & 0xFF, raw & 0xFF]


def _maf_bytes(maf: float) -> list[int]:
    raw = int(max(0, maf) * 100)
    return [(raw >> 8) & 0xFF, raw & 0xFF]


def _voltage_bytes(volts: float) -> list[int]:
    raw = int(max(0, volts) * 1000)
    return [(raw >> 8) & 0xFF, raw & 0xFF]


def supported_pids() -> list[dict]:
    return [
        {
            "pid": d.pid,
            "pid_hex": f"0x{d.pid:02X}",
            "name": d.name,
            "unit": d.unit,
            "description_de": d.description_de,
        }
        for d in PID_DEFINITIONS.values()
    ]
