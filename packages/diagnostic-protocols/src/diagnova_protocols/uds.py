"""UDS ISO 14229 – lesende Grundlagen (NRC, Dienst-IDs).

Keine SecurityAccess-, Programming- oder Write-Sessions aktiv.
Nur öffentlich bekannte Konstanten; keine OEM-DIDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Negative Response Codes (Auswahl ISO 14229 – öffentlich dokumentiert)
NEGATIVE_RESPONSE_CODES: dict[int, str] = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooLong",
    0x21: "busyRepeatRequest",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x25: "noResponseFromSubnetComponent",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceedNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x70: "uploadDownloadNotAccepted",
    0x71: "transferDataSuspended",
    0x72: "generalProgrammingFailure",
    0x73: "wrongBlockSequenceCounter",
    0x78: "requestCorrectlyReceivedResponsePending",
    0x7E: "subFunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession",
}


# Lesende / unkritische Dienst-IDs (Request). Schreib-/Flash-Dienste bewusst deaktiviert.
UDS_SERVICES_READ_SAFE: dict[int, dict[str, Any]] = {
    0x10: {
        "name": "DiagnosticSessionControl",
        "enabled": False,
        "reason_de": "Sitzungswechsel nur mit belegter Definition und Freigabe – vorbereitet, nicht aktiv.",
    },
    0x11: {
        "name": "ECUReset",
        "enabled": False,
        "reason_de": "Schreib-/Reset-Pfad gesperrt.",
    },
    0x14: {
        "name": "ClearDiagnosticInformation",
        "enabled": False,
        "reason_de": "Clear nur über OBD Mode 04 Gate (Phase 04); UDS Clear nicht freigegeben.",
    },
    0x19: {
        "name": "ReadDTCInformation",
        "enabled": True,
        "reason_de": "Lesend – Parser/NRC; Payload-Interpretation nur mit Definition.",
    },
    0x22: {
        "name": "ReadDataByIdentifier",
        "enabled": True,
        "reason_de": "Nur bekannte Standard-DIDs; keine erfundenen OEM-DIDs.",
    },
    0x3E: {
        "name": "TesterPresent",
        "enabled": False,
        "reason_de": "Vorbereitet; ohne aktive UDS-Sitzung nicht nötig.",
    },
    0x27: {
        "name": "SecurityAccess",
        "enabled": False,
        "reason_de": "Security/Seed-Key bewusst deaktiviert.",
    },
    0x2E: {
        "name": "WriteDataByIdentifier",
        "enabled": False,
        "reason_de": "Schreiben gesperrt.",
    },
    0x31: {
        "name": "RoutineControl",
        "enabled": False,
        "reason_de": "Routinen/Service erst mit Definition + Freigabe.",
    },
    0x34: {
        "name": "RequestDownload",
        "enabled": False,
        "reason_de": "Flash/Programmierung Phase 12 – gesperrt.",
    },
}


# Standard-DIDs (ISO 14229 / SAE J1979 Überlappung) – keine OEM-Liste
STANDARD_DIDS: dict[int, dict[str, str]] = {
    0xF190: {
        "name": "VINDataIdentifier",
        "source": "ISO 14229 / SAE J1979-DA",
        "notes_de": "VIN – Standard-DID, soweit vom Steuergerät unterstützt.",
    },
    0xF191: {
        "name": "vehicleManufacturerECUHardwareNumber",
        "source": "ISO 14229 Annex",
        "notes_de": "Hardware-Nummer – Inhalt herstellerspezifisch, DID selbst standardisiert.",
    },
    0xF187: {
        "name": "vehicleManufacturerSparePartNumber",
        "source": "ISO 14229 Annex",
        "notes_de": "Ersatzteilnummer – DID standardisiert, Wert OEM.",
    },
    0xF18A: {
        "name": "systemSupplierIdentifier",
        "source": "ISO 14229 Annex",
        "notes_de": "Lieferantenkennung – DID standardisiert.",
    },
    0xF18C: {
        "name": "ECUSerialNumber",
        "source": "ISO 14229 Annex",
        "notes_de": "Seriennummer – DID standardisiert.",
    },
}


NEGATIVE_RESPONSE_SID = 0x7F


@dataclass(frozen=True)
class UdsNegativeResponse:
    request_sid: int
    nrc: int
    nrc_name: str
    raw: tuple[int, ...]


def decode_nrc(code: int) -> str:
    return NEGATIVE_RESPONSE_CODES.get(code & 0xFF, f"unknown_nrc_0x{code & 0xFF:02X}")


def parse_negative_response(data: list[int] | tuple[int, ...]) -> UdsNegativeResponse | None:
    """Erkennt 7F SID NRC."""
    if len(data) < 3:
        return None
    if data[0] != NEGATIVE_RESPONSE_SID:
        return None
    sid = data[1] & 0xFF
    nrc = data[2] & 0xFF
    return UdsNegativeResponse(
        request_sid=sid,
        nrc=nrc,
        nrc_name=decode_nrc(nrc),
        raw=tuple(data),
    )


def is_service_enabled(sid: int) -> bool:
    info = UDS_SERVICES_READ_SAFE.get(sid & 0xFF)
    return bool(info and info.get("enabled"))


def uds_catalog() -> dict[str, Any]:
    return {
        "disclaimer_de": (
            "UDS-Implementierung Phase 05: NRC-Parser und Katalog. "
            "Schreib-/Security-/Flash-Dienste deaktiviert. Keine OEM-DIDs."
        ),
        "negative_response_codes": {
            f"0x{k:02X}": v for k, v in sorted(NEGATIVE_RESPONSE_CODES.items())
        },
        "services": {
            f"0x{k:02X}": v for k, v in sorted(UDS_SERVICES_READ_SAFE.items())
        },
        "standard_dids": {
            f"0x{k:04X}": v for k, v in sorted(STANDARD_DIDS.items())
        },
        "active_write_paths": False,
        "security_access_enabled": False,
    }
