"""EU-VIES UID-Prüfung mit Stub-Fallback und Protokollierung.

Live-SOAP: https://ec.europa.eu/taxation_customs/vies/services/checkVatService
Kein Netzwerk in Tests → mode=stub. Live nur wenn VIES_LIVE=1 und erreichbar.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from sqlalchemy.orm import Session

from app.models.commerce import VatCheckLog

_VAT_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{2,12}$")

VIES_SOAP_URL = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"

# Bekannte Demo-UIDs für Stub (keine echte Gültigkeit behaupten außer in Stub-Kontext)
_STUB_VALID = {
    "ATU12345678": {"name": "Demo Firma AT GmbH", "address": "Musterstraße 1\n1010 Wien"},
    "DE123456789": {"name": "Demo Firma DE GmbH", "address": "Beispielweg 2\n10115 Berlin"},
}


def normalize_vat(vat_id: str) -> tuple[str, str]:
    cleaned = re.sub(r"[\s.\-]", "", (vat_id or "").upper())
    if len(cleaned) < 4 or not cleaned[:2].isalpha():
        raise ValueError("UID muss mit Ländercode beginnen (z. B. ATU…)")
    country = cleaned[:2]
    number = cleaned[2:]
    if not number:
        raise ValueError("UID-Nummer fehlt")
    if not _VAT_RE.match(country + number):
        raise ValueError("UID-Format ungültig")
    return country, number


def _soap_envelope(country: str, number: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">'
        "<soapenv:Header/><soapenv:Body>"
        f"<urn:checkVat><urn:countryCode>{country}</urn:countryCode>"
        f"<urn:vatNumber>{number}</urn:vatNumber></urn:checkVat>"
        "</soapenv:Body></soapenv:Envelope>"
    ).encode("utf-8")


def _parse_vies_xml(body: bytes) -> dict[str, Any]:
    root = ET.fromstring(body)
    ns = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "urn": "urn:ec.europa.eu:taxud:vies:services:checkVat:types",
    }
    valid_el = root.find(".//urn:valid", ns)
    name_el = root.find(".//urn:name", ns)
    addr_el = root.find(".//urn:address", ns)
    if valid_el is None:
        # fallback ohne Namespace
        valid_el = root.find(".//{*}valid")
        name_el = root.find(".//{*}name")
        addr_el = root.find(".//{*}address")
    valid = (valid_el.text or "").lower() == "true" if valid_el is not None else False
    return {
        "valid": valid,
        "name": name_el.text if name_el is not None else None,
        "address": addr_el.text if addr_el is not None else None,
    }


def check_vat_live(country: str, number: str, *, timeout: float = 8.0) -> dict[str, Any]:
    req = urllib.request.Request(
        VIES_SOAP_URL,
        data=_soap_envelope(country, number),
        headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        parsed = _parse_vies_xml(raw)
        return {
            "result": "valid" if parsed["valid"] else "invalid",
            "request_mode": "live",
            "name_returned": parsed.get("name"),
            "address_returned": parsed.get("address"),
            "error_detail": None,
            "raw_summary": {"valid": parsed["valid"]},
        }
    except urllib.error.HTTPError as exc:
        return {
            "result": "service_unavailable",
            "request_mode": "live",
            "name_returned": None,
            "address_returned": None,
            "error_detail": f"HTTP {exc.code}",
            "raw_summary": {"error": "http"},
        }
    except Exception as exc:  # noqa: BLE001 – Netzwerkfehler dokumentieren
        return {
            "result": "timeout" if "timed out" in str(exc).lower() else "service_unavailable",
            "request_mode": "live",
            "name_returned": None,
            "address_returned": None,
            "error_detail": str(exc)[:500],
            "raw_summary": {"error": type(exc).__name__},
        }


def check_vat_stub(country: str, number: str) -> dict[str, Any]:
    key = f"{country}{number}"
    if key in _STUB_VALID:
        hit = _STUB_VALID[key]
        return {
            "result": "valid",
            "request_mode": "stub",
            "name_returned": hit["name"],
            "address_returned": hit["address"],
            "error_detail": None,
            "raw_summary": {"stub": True, "valid": True},
        }
    if number.endswith("000"):
        return {
            "result": "invalid",
            "request_mode": "stub",
            "name_returned": None,
            "address_returned": None,
            "error_detail": None,
            "raw_summary": {"stub": True, "valid": False},
        }
    # Default stub: syntaktisch OK → pending/unknown als invalid für Vorsicht
    return {
        "result": "invalid",
        "request_mode": "stub",
        "name_returned": None,
        "address_returned": None,
        "error_detail": "Stub: UID nicht in Demo-Whitelist (ATU12345678, DE123456789).",
        "raw_summary": {"stub": True, "valid": False},
    }


def check_vat(
    db: Session,
    *,
    vat_id: str,
    billing_account_id: str | None = None,
    workshop_id: str | None = None,
    force_stub: bool | None = None,
) -> dict[str, Any]:
    try:
        country, number = normalize_vat(vat_id)
    except ValueError as exc:
        log = VatCheckLog(
            billing_account_id=billing_account_id,
            workshop_id=workshop_id,
            country_code=(vat_id or "")[:2].upper() or "XX",
            vat_number=(vat_id or "")[:32],
            result="invalid_input",
            request_mode="none",
            error_detail=str(exc),
            raw_summary_json="{}",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return {
            "id": log.id,
            "vat_id": vat_id,
            "country_code": log.country_code,
            "result": "invalid_input",
            "request_mode": "none",
            "message_de": str(exc),
            "valid": False,
        }

    use_live = force_stub is False or (
        force_stub is None and os.environ.get("VIES_LIVE", "").strip() in {"1", "true", "yes"}
    )
    outcome = check_vat_live(country, number) if use_live else check_vat_stub(country, number)

    log = VatCheckLog(
        billing_account_id=billing_account_id,
        workshop_id=workshop_id,
        country_code=country,
        vat_number=number,
        result=outcome["result"],
        request_mode=outcome["request_mode"],
        name_returned=outcome.get("name_returned"),
        address_returned=outcome.get("address_returned"),
        error_detail=outcome.get("error_detail"),
        raw_summary_json=json.dumps(outcome.get("raw_summary") or {}, ensure_ascii=False),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    valid = outcome["result"] == "valid"
    return {
        "id": log.id,
        "vat_id": f"{country}{number}",
        "country_code": country,
        "result": outcome["result"],
        "request_mode": outcome["request_mode"],
        "valid": valid,
        "name_returned": outcome.get("name_returned"),
        "address_returned": outcome.get("address_returned"),
        "error_detail": outcome.get("error_detail"),
        "message_de": (
            "UID laut VIES gültig."
            if valid
            else (
                "UID ungültig oder Stub-Whitelist verfehlt."
                if outcome["result"] == "invalid"
                else f"VIES-Prüfung fehlgeschlagen: {outcome['result']}"
            )
        ),
        "legal_note_de": (
            "Live-VIES nur mit VIES_LIVE=1. Fachliche/steuerliche Freigabe vor Prod. "
            "Stub-Ergebnisse sind keine echten UID-Nachweise."
        ),
    }
