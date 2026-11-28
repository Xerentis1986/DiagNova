"""Konfigurierbare Steuerregeln für österreichischen Anbieter (Phase 21).

WICHTIG: review_status=draft_needs_review – keine produktive Steuerfreigabe.
Quellen (Orientierung, keine Rechtsberatung):
- USP.at elektronisch erbrachte Dienstleistungen / OSS
- EU Place of taxation / VAT Directive
"""

from __future__ import annotations

from typing import Any

SUPPLIER_COUNTRY = "AT"
SUPPLIER_LEGAL_REVIEW_REQUIRED = True

# EU-Mitglieder ohne AT (ISO 3166-1 alpha-2) – Stand-Orientierung, wartbar
EU_COUNTRIES_WITHOUT_AT: frozenset[str] = frozenset(
    {
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    }
)

# Standard-MwSt AT (Normal) – konfigurierbar, nicht hart verdrahten in Logik
AT_STANDARD_VAT_BP = 2000  # 20,00 %

# Demo: vereinfachte B2C-OSS-Sätze (müssen vor Prod durch Fachprüfung ersetzt werden)
OSS_DEMO_RATES_BP: dict[str, int] = {
    "DE": 1900,
    "FR": 2000,
    "IT": 2200,
    "ES": 2100,
    "NL": 2100,
    "BE": 2100,
    "PL": 2300,
    "CZ": 2100,
    "HU": 2700,
    "SK": 2000,
    "SI": 2200,
    "HR": 2500,
    "RO": 1900,
    "BG": 2000,
    "GR": 2400,
    "PT": 2300,
    "IE": 2300,
    "FI": 2550,
    "SE": 2500,
    "DK": 2500,
    "LU": 1700,
    "MT": 1800,
    "CY": 1900,
    "EE": 2200,
    "LV": 2100,
    "LT": 2100,
}

TAX_RULE_SEED: list[dict[str, Any]] = [
    {
        "code": "b2b_at_standard",
        "version": "21.0",
        "scenario": "b2b_at",
        "customer_type": "b2b",
        "supplier_country": "AT",
        "customer_country": "AT",
        "vat_rate_bp": AT_STANDARD_VAT_BP,
        "reverse_charge": False,
        "oss_applicable": False,
        "display_gross": False,
        "legal_basis_de": (
            "B2B Inland AT: österreichische USt auf elektronische Dienstleistung. "
            "Fachliche Prüfung vor Produktivbetrieb erforderlich."
        ),
        "review_status": "draft_needs_review",
        "enabled": True,
    },
    {
        "code": "b2c_at_standard",
        "version": "21.0",
        "scenario": "b2c_at",
        "customer_type": "b2c",
        "supplier_country": "AT",
        "customer_country": "AT",
        "vat_rate_bp": AT_STANDARD_VAT_BP,
        "reverse_charge": False,
        "oss_applicable": False,
        "display_gross": True,
        "legal_basis_de": (
            "B2C Inland AT: Bruttopreis inkl. USt. Verbraucherschutz: transparente Bruttopreise."
        ),
        "review_status": "draft_needs_review",
        "enabled": True,
    },
    {
        "code": "b2b_eu_reverse_charge",
        "version": "21.0",
        "scenario": "b2b_reverse_charge",
        "customer_type": "b2b",
        "supplier_country": "AT",
        "customer_country": "EU",  # Platzhalter – Engine matcht per Land + gültige UID
        "vat_rate_bp": 0,
        "reverse_charge": True,
        "oss_applicable": False,
        "display_gross": False,
        "legal_basis_de": (
            "B2B EU (gültig VIES): Reverse Charge / Verlagerung der Steuerschuld, "
            "sofern Voraussetzungen erfüllt. UID-Prüfung Pflicht. Keine Pauschalisierung."
        ),
        "review_status": "draft_needs_review",
        "enabled": True,
    },
    {
        "code": "b2c_eu_oss",
        "version": "21.0",
        "scenario": "b2c_eu_oss",
        "customer_type": "b2c",
        "supplier_country": "AT",
        "customer_country": "EU",
        "vat_rate_bp": -1,  # Engine wählt Landessatz
        "reverse_charge": False,
        "oss_applicable": True,
        "display_gross": True,
        "legal_basis_de": (
            "B2C EU elektronische Dienstleistungen: Leistungsort i. d. R. Kundenmitgliedstaat; "
            "OSS möglich. Landessätze und Schwellen fachlich prüfen (USP/OSS)."
        ),
        "review_status": "draft_needs_review",
        "enabled": True,
    },
    {
        "code": "third_country",
        "version": "21.0",
        "scenario": "third_country",
        "customer_type": "any",
        "supplier_country": "AT",
        "customer_country": "XX",
        "vat_rate_bp": 0,
        "reverse_charge": False,
        "oss_applicable": False,
        "display_gross": True,
        "legal_basis_de": (
            "Drittland: Sonderregeln; oft keine AT-USt auf elektronische DL an Nicht-EU. "
            "Einzelfallprüfung und Dokumentation Pflicht."
        ),
        "review_status": "draft_needs_review",
        "enabled": True,
    },
]

CONSUMER_DISCLAIMERS_DE: dict[str, str] = {
    "gross_prices": "B2C-Preise werden als Bruttopreise ausgewiesen (inkl. USt, soweit anwendbar).",
    "auto_renewal": "Abos verlängern sich automatisch, sofern nicht gekündigt – Kündigungsinfos vor Checkout.",
    "withdrawal": (
        "Widerrufsrecht für Verbraucher: gesetzliche Fristen und mögliche Ausnahmen "
        "(z. B. digitale Inhalte nach Zustimmung/Beginn) müssen vor Veröffentlichung geprüft werden."
    ),
    "order_confirmation": "Bestellbestätigung und Vertragsinformationen werden protokolliert.",
    "legal_review": "Rechtliche Gestaltung vor Veröffentlichung prüfen – keine Rechtsberatung durch diese Software.",
}
