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


CLEAR_PHRASE = "FEHLERCODES LOESCHEN"

# Simulierter Clear-State: gelöschte stored/pending pro vehicle (permanent bleibt)
_cleared_nonpermanent: set[str] = set()


def clear_dtc_warnings() -> dict:
    return {
        "data_source": "simulated",
        "warnings_de": [
            "Mode 04 löscht gespeicherte und pending DTCs sowie Freeze-Frame-Daten.",
            "Readiness-Monitore werden zurückgesetzt – AU kann betroffen sein.",
            "Permanente DTCs (Mode 0A) werden NICHT gelöscht und sind nicht als löschbar darzustellen.",
            "Vorher-Bericht speichern, bestätigen, nach dem Löschen erneut auslesen.",
            "Dieser API-Pfad ist simuliert – keine echte Fahrzeugkommunikation.",
        ],
        "permanent_dtcs_clearable": False,
        "requires_confirmation_phrase": CLEAR_PHRASE,
        "hardware_live": False,
    }


def clear_dtcs_simulated(
    vehicle_id: str,
    *,
    confirmation_phrase: str,
    acknowledge_freeze_frame_loss: bool,
    acknowledge_readiness_reset: bool,
    acknowledge_permanent_remain: bool,
    pre_report_saved: bool,
) -> dict:
    """Freigabegeschützte simulierte Fehlerlöschung – permanente DTCs bleiben."""
    if confirmation_phrase.strip() != CLEAR_PHRASE:
        return {
            "success": False,
            "data_source": "simulated",
            "message_de": f"Bestätigungsphrase muss exakt „{CLEAR_PHRASE}“ lauten.",
        }
    if not (
        acknowledge_freeze_frame_loss
        and acknowledge_readiness_reset
        and acknowledge_permanent_remain
        and pre_report_saved
    ):
        return {
            "success": False,
            "data_source": "simulated",
            "message_de": "Alle Warnhinweise und Vorher-Bericht müssen bestätigt werden.",
        }

    before = [d.model_dump() for d in list_dtcs(vehicle_id)]
    _cleared_nonpermanent.add(vehicle_id)
    after_raw = list_dtcs(vehicle_id)
    # list_dtcs respektiert Clear-State
    after = [d.model_dump() for d in after_raw]
    return {
        "success": True,
        "data_source": "simulated",
        "message_de": "Simulierte Mode-04-Löschung. Permanente DTCs bleiben. Kein Hardwarezugriff.",
        "before": before,
        "after": after,
        "permanent_remain": [d for d in after if d["status"] == "permanent"],
        "note_de": "Live-Clear nur über Windows-Connector mit Freigabe-Token und Hardware.",
    }


def list_dtcs(vehicle_id: str) -> list[DtcOut]:
    """Deterministic-ish DTC set; nach simuliertem Clear ohne stored/pending."""
    seed = sum(ord(c) for c in vehicle_id)
    rng = random.Random(seed)
    codes = list(DTC_CATALOG.keys())
    pick = rng.sample(codes, k=rng.randint(1, 3))
    pending_pool = [c for c in codes if c not in pick]
    pending = rng.sample(pending_pool, k=1) if pending_pool else []
    permanent_pool = [c for c in codes if c not in pick and c not in pending]
    permanent = rng.sample(permanent_pool, k=1) if permanent_pool else []
    result: list[DtcOut] = []
    cleared = vehicle_id in _cleared_nonpermanent
    if not cleared:
        for code in pick:
            desc, sev = DTC_CATALOG[code]
            result.append(DtcOut(code=code, status="stored", description_de=desc, severity=sev))  # type: ignore[arg-type]
        for code in pending:
            desc, sev = DTC_CATALOG[code]
            result.append(DtcOut(code=code, status="pending", description_de=desc, severity=sev))  # type: ignore[arg-type]
    for code in permanent:
        desc, sev = DTC_CATALOG[code]
        result.append(DtcOut(code=code, status="permanent", description_de=desc, severity=sev))  # type: ignore[arg-type]
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
