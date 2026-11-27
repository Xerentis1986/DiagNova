"""Steuerentscheidung für AT-Anbieter – konfigurierbar, draft_needs_review."""

from __future__ import annotations

from typing import Any

from app.data.tax_rules_at import (
    AT_STANDARD_VAT_BP,
    CONSUMER_DISCLAIMERS_DE,
    EU_COUNTRIES_WITHOUT_AT,
    OSS_DEMO_RATES_BP,
    SUPPLIER_COUNTRY,
    SUPPLIER_LEGAL_REVIEW_REQUIRED,
)


def is_eu(country: str) -> bool:
    c = (country or "").upper()
    return c == "AT" or c in EU_COUNTRIES_WITHOUT_AT


def resolve_tax(
    *,
    customer_type: str,
    customer_country: str,
    vat_id: str | None = None,
    vat_valid: bool | None = None,
    net_cents: int,
) -> dict[str, Any]:
    """Ermittelt Szenario, Satz und Beträge. Keine Rechtsberatung."""
    ctype = (customer_type or "").lower()
    country = (customer_country or "AT").upper()
    if ctype not in {"b2b", "b2c"}:
        raise ValueError("customer_type muss b2b oder b2c sein")
    if net_cents < 0:
        raise ValueError("net_cents darf nicht negativ sein")

    review = "draft_needs_review"
    disclaimers = list(CONSUMER_DISCLAIMERS_DE.values()) if ctype == "b2c" else [
        CONSUMER_DISCLAIMERS_DE["legal_review"]
    ]

    if country == SUPPLIER_COUNTRY:
        scenario = "b2b_at" if ctype == "b2b" else "b2c_at"
        rate = AT_STANDARD_VAT_BP
        reverse = False
        oss = False
        display_gross = ctype == "b2c"
        basis = "Inland AT – Normalsteuersatz (konfigurierbar)."
    elif is_eu(country):
        if ctype == "b2b" and vat_id and vat_valid is True:
            scenario = "b2b_reverse_charge"
            rate = 0
            reverse = True
            oss = False
            display_gross = False
            basis = "B2B EU mit gültiger UID – Reverse Charge (Voraussetzungen prüfen)."
        elif ctype == "b2b":
            # Ohne gültige UID: vorsichtig wie Inland behandeln / blockieren für Prod
            scenario = "b2b_eu_uid_required"
            rate = AT_STANDARD_VAT_BP
            reverse = False
            oss = False
            display_gross = False
            basis = (
                "B2B EU ohne gültige VIES-UID: Reverse Charge nicht anwendbar. "
                "Prod: Bestellung sperren oder AT-USt – Fachprüfung."
            )
        else:
            scenario = "b2c_eu_oss"
            rate = OSS_DEMO_RATES_BP.get(country, AT_STANDARD_VAT_BP)
            reverse = False
            oss = True
            display_gross = True
            basis = (
                "B2C EU elektronische DL – OSS/Landessatz (Demo-Tabelle). "
                "Leistungsort und Schwellen fachlich prüfen."
            )
    else:
        scenario = "third_country"
        rate = 0
        reverse = False
        oss = False
        display_gross = True
        basis = "Drittland – Einzelfallprüfung; Demo: 0 % AT-USt."

    vat_cents = (net_cents * rate) // 10000
    gross_cents = net_cents + vat_cents

    return {
        "supplier_country": SUPPLIER_COUNTRY,
        "customer_type": ctype,
        "customer_country": country,
        "scenario": scenario,
        "vat_rate_bp": rate,
        "vat_rate_percent": round(rate / 100, 2),
        "reverse_charge": reverse,
        "oss_applicable": oss,
        "display_gross": display_gross,
        "net_cents": net_cents,
        "vat_cents": vat_cents,
        "gross_cents": gross_cents,
        "currency": "EUR",
        "legal_basis_de": basis,
        "review_status": review,
        "legal_review_required": SUPPLIER_LEGAL_REVIEW_REQUIRED,
        "vat_id_provided": bool(vat_id),
        "vat_valid": vat_valid,
        "consumer_notes_de": disclaimers if ctype == "b2c" else [],
        "sources_de": [
            "USP.at – elektronisch erbrachte Dienstleistungen",
            "USP.at – Umsatzsteuer One-Stop-Shop (OSS)",
            "EU – Place of taxation / VAT Directive",
        ],
        "message_de": (
            f"Steuerszenario {scenario}: {rate / 100:.2f} % "
            f"(Netto {net_cents}, USt {vat_cents}, Brutto {gross_cents} Cent). "
            "Keine produktive Steuerfreigabe."
        ),
    }
