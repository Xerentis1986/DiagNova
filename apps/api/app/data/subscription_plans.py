"""Phase 13 – Tarifkatalog (statisch). Keine echten Preise/PSPs.

LKW/Kombi sind als geplante Tarife hinterlegt (Entitlements leer / gesperrt),
bis Spezifikation und Freigabe vorliegen. Preise sind Demo-Angaben.
"""

from __future__ import annotations

from typing import Any

# Feature-Keys – serverseitig geprüft
ENT_DIAGNOSTICS_READ = "diagnostics.read"
ENT_DIAGNOSTICS_CLEAR = "diagnostics.clear_dtc"
ENT_WORKSHOP = "workshop.customers"
ENT_REPORTS = "reports.pdf"
ENT_SERVICE_SIM = "service.simulated"
ENT_CODING_SIM = "coding.simulated"
ENT_DATA_UPDATES = "data.updates"
ENT_MULTI_DEVICE = "devices.multi"
ENT_LKW = "vehicle.lkw"  # Phase 19 – bewusst nicht freigegeben

PLAN_CATALOG: list[dict[str, Any]] = [
    {
        "code": "pkw_trial",
        "name_de": "PKW Testzeitraum",
        "vehicle_scope": "pkw",
        "billing_period": "trial",
        "price_cents_demo": 0,
        "currency": "EUR",
        "trial_days": 14,
        "max_devices": 1,
        "release_status": "available",
        "description_de": "Optionaler Testzeitraum für PKW-Diagnose (Simulation). Keine echte Zahlung.",
        "entitlements": [
            ENT_DIAGNOSTICS_READ,
            ENT_WORKSHOP,
            ENT_REPORTS,
            ENT_SERVICE_SIM,
            ENT_CODING_SIM,
        ],
    },
    {
        "code": "pkw_basic",
        "name_de": "PKW Basis",
        "vehicle_scope": "pkw",
        "billing_period": "monthly",
        "price_cents_demo": 4900,
        "currency": "EUR",
        "trial_days": 0,
        "max_devices": 2,
        "release_status": "available",
        "description_de": "Demo-Tarif PKW: Lesende Diagnose, Werkstatt, Berichte. Zahlung nur Stub.",
        "entitlements": [
            ENT_DIAGNOSTICS_READ,
            ENT_DIAGNOSTICS_CLEAR,
            ENT_WORKSHOP,
            ENT_REPORTS,
            ENT_SERVICE_SIM,
            ENT_CODING_SIM,
            ENT_MULTI_DEVICE,
        ],
    },
    {
        "code": "pkw_pro",
        "name_de": "PKW Pro",
        "vehicle_scope": "pkw",
        "billing_period": "monthly",
        "price_cents_demo": 9900,
        "currency": "EUR",
        "trial_days": 0,
        "max_devices": 5,
        "release_status": "available",
        "description_de": "Demo-Tarif PKW inkl. Daten-Updates-Admin. Kein echter Payment-Provider.",
        "entitlements": [
            ENT_DIAGNOSTICS_READ,
            ENT_DIAGNOSTICS_CLEAR,
            ENT_WORKSHOP,
            ENT_REPORTS,
            ENT_SERVICE_SIM,
            ENT_CODING_SIM,
            ENT_DATA_UPDATES,
            ENT_MULTI_DEVICE,
        ],
    },
    {
        "code": "lkw_planned",
        "name_de": "LKW (geplant)",
        "vehicle_scope": "lkw",
        "billing_period": "monthly",
        "price_cents_demo": None,
        "currency": "EUR",
        "trial_days": 0,
        "max_devices": 0,
        "release_status": "planned",
        "description_de": "LKW/J1939 – Phase 19. Nicht buchbar, keine Entitlements freigegeben.",
        "entitlements": [],
    },
    {
        "code": "kombi_planned",
        "name_de": "PKW+LKW Kombi (geplant)",
        "vehicle_scope": "kombi",
        "billing_period": "monthly",
        "price_cents_demo": None,
        "currency": "EUR",
        "trial_days": 0,
        "max_devices": 0,
        "release_status": "planned",
        "description_de": "Kombiniertarif geplant. Nicht buchbar ohne Freigabe und Spezifikation.",
        "entitlements": [],
    },
]

# Status: active entitlements; past_due grace; canceled/expired block new ops
ACTIVE_LICENSE_STATUSES = {"trialing", "active", "past_due"}
# past_due: Zahlungsausfall – Grace, neue kritische Starts eingeschränkt, laufende Ops nicht abbrechen
GRACE_STATUSES = {"past_due"}
BLOCKED_NEW_OP_STATUSES = {"canceled", "expired", "unpaid", "incomplete"}


def get_plan(code: str) -> dict[str, Any] | None:
    for plan in PLAN_CATALOG:
        if plan["code"] == code:
            return plan
    return None


def list_plans(*, include_planned: bool = True) -> list[dict[str, Any]]:
    if include_planned:
        return list(PLAN_CATALOG)
    return [p for p in PLAN_CATALOG if p["release_status"] == "available"]
