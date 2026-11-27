"""Phase 15 – Threat Model, Security-Dashboard, DSGVO-Prozessübersicht (keine Rechtskonformität)."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.security import PASSWORD_MIN_LENGTH, is_insecure_default_secret
from app.data.software_versions import COMPONENT_VERSIONS
from app.services.tenant import ALL_ROLES


DISCLAIMER_DE = (
    "Sicherheits- und Datenschutzmaßnahmen sind technische Baselines. "
    "Keine rechtliche Konformität (DSGVO/AV) und keine Produktionsfreigabe bei kritischen Lücken. "
    "Demo/Simulation getrennt von Live."
)


def threat_model() -> list[dict]:
    return [
        {
            "id": "T-BROWSER",
            "surface": "Browser / Web-UI",
            "threat": "XSS, Token-Diebstahl aus localStorage, Clickjacking",
            "mitigation_de": (
                "React escape by default; Security-Header X-Frame-Options/nosniff; "
                "Bearer nur über HTTPS in Prod; kein Passwort in Logs."
            ),
            "status": "partial",
            "severity": "high",
        },
        {
            "id": "T-API-AUTH",
            "surface": "API Auth",
            "threat": "Brute-Force Login, schwache Secrets, abgelaufene Tokens",
            "mitigation_de": (
                "bcrypt-Hash, JWT mit exp/iat/typ, Login-Rate-Limit, "
                "Audit login_failed ohne Passwort, Default-Secret-Warnung."
            ),
            "status": "mitigated",
            "severity": "high",
        },
        {
            "id": "T-RBAC-IDOR",
            "surface": "API Mandanten / Rollen",
            "threat": "IDOR über fremde workshop_id / Kunden-IDs",
            "mitigation_de": (
                "workshop_id nur aus JWT/User; assert_same_tenant → 404; "
                "Rollen admin/technician/viewer serverseitig."
            ),
            "status": "mitigated",
            "severity": "critical",
        },
        {
            "id": "T-CORS-CSRF",
            "surface": "CORS / CSRF",
            "threat": "Cross-Origin-Missbrauch",
            "mitigation_de": (
                "CORS-Allowlist; Auth via Bearer (kein Cookie-Session) → CSRF-Risiko gering; "
                "Origin-Prüfung dokumentiert für künftige Cookie-Auth."
            ),
            "status": "mitigated",
            "severity": "medium",
        },
        {
            "id": "T-CONNECTOR",
            "surface": "Windows-Connector",
            "threat": "Offene Ports, Remote-Befehle, Privilege Escalation",
            "mitigation_de": (
                "Loopback-Bindung, Pairing-Token, Origin-Allowlist, OBD-Allowlist, "
                "keine Remote-Rohbefehle."
            ),
            "status": "mitigated",
            "severity": "critical",
        },
        {
            "id": "T-ADAPTER",
            "surface": "OBD-Adapter / Fahrzeug",
            "threat": "Unkontrollierte Schreibbefehle, Abgasumgehung",
            "mitigation_de": (
                "Allowlist + Gates; Clear/Service/Flash nur mit Freigabe; "
                "Live-Schreiben/DPF-Off gesperrt."
            ),
            "status": "partial",
            "severity": "critical",
        },
        {
            "id": "T-UPDATES",
            "surface": "Software- & Daten-Updates",
            "threat": "Manipulierte Pakete, SSRF, ungeprüfte Auto-Installs",
            "mitigation_de": (
                "HMAC/SHA-256, SSRF-HTTPS-Allowlist, Staging/Admin-Freigabe, "
                "Prod-Auto ohne Zertifikat gesperrt."
            ),
            "status": "mitigated",
            "severity": "high",
        },
        {
            "id": "T-SECRETS",
            "surface": "Secrets / Config",
            "threat": "Secrets in Git/Chat, Default-JWT",
            "mitigation_de": (
                ".env / Plesk-Secrets; Demo-HMAC klar gekennzeichnet; "
                "Dashboard warnt bei Default-JWT; keine Secrets committen."
            ),
            "status": "partial",
            "severity": "high",
        },
        {
            "id": "T-INJECTION",
            "surface": "SQL / XSS / SSRF",
            "threat": "Injection über API-Parameter",
            "mitigation_de": "SQLAlchemy ORM; Pydantic-Validierung; SSRF-Guard bei Fetches.",
            "status": "mitigated",
            "severity": "high",
        },
        {
            "id": "T-AUDIT-PII",
            "surface": "Audit / Logs",
            "threat": "Passwörter/VIN/Kundendaten in Audit",
            "mitigation_de": "Redaction in write_audit; VIN/E-Mail/Telefon maskiert.",
            "status": "mitigated",
            "severity": "medium",
        },
        {
            "id": "T-BACKUP",
            "surface": "Backup / Restore",
            "threat": "Datenverlust, unsichere Backups",
            "mitigation_de": "Dokumentierte pg_dump/Plesk-Schritte; Phase-16-Checkliste.",
            "status": "partial",
            "severity": "medium",
        },
    ]


def findings() -> list[dict]:
    insecure = is_insecure_default_secret()
    items = [
        {
            "id": "F-JWT-DEFAULT",
            "title_de": "JWT-Secret Default oder Testwert",
            "severity": "critical" if insecure else "info",
            "status": "open" if insecure else "mitigated",
            "detail_de": (
                "JWT_SECRET muss in Produktion ein langes Zufallsgeheimnis sein "
                "(Umgebung/Plesk). Default/Testwerte sind gesperrt für Freigabe."
                if insecure
                else "JWT_SECRET weicht vom Default ab (Umgebung gesetzt)."
            ),
        },
        {
            "id": "F-CERT",
            "title_de": "Kein produktives Code-Signing-Zertifikat",
            "severity": "high",
            "status": "accepted",
            "detail_de": "BLK-CERT – produktive Auto-Updates bleiben gesperrt (Phase 14).",
        },
        {
            "id": "F-LEGAL",
            "title_de": "DSGVO/AV rechtlich ungeprüft",
            "severity": "medium",
            "status": "documented",
            "detail_de": "BLK-LEGAL – Prozesse dokumentiert, keine Konformität behauptet.",
        },
        {
            "id": "F-MONITOR",
            "title_de": "Kein produktives Alerting",
            "severity": "medium",
            "status": "documented",
            "detail_de": "Health-Endpoint vorhanden; Alarmkanäle nur nach Zustimmung/Phase 16.",
        },
        {
            "id": "F-RATE-MULTI",
            "title_de": "Rate-Limit nur pro Prozess (In-Memory)",
            "severity": "low",
            "status": "accepted",
            "detail_de": "Für Multi-Worker/Prod Redis o. ä. vorsehen; Demo/Single-Process ausreichend.",
        },
    ]
    return items


def build_dashboard() -> dict:
    settings = get_settings()
    insecure = is_insecure_default_secret()
    open_risks = [
        f["detail_de"]
        for f in findings()
        if f["status"] in {"open", "documented", "accepted"} and f["severity"] in {"critical", "high", "medium"}
    ]
    return {
        "version": COMPONENT_VERSIONS["api"],
        "demo_mode": settings.demo_mode,
        "jwt_secret_insecure_default": insecure,
        "cors_origins": settings.cors_origin_list,
        "rate_limits": {
            "login_max": settings.rate_limit_login_max,
            "login_window_sec": settings.rate_limit_login_window_sec,
            "write_max": settings.rate_limit_write_max,
            "write_window_sec": settings.rate_limit_write_window_sec,
        },
        "auth": {
            "password_hash": "bcrypt",
            "token": "JWT Bearer",
            "jwt_algorithm": settings.jwt_algorithm,
            "jwt_expire_minutes": settings.jwt_expire_minutes,
            "password_min_length": PASSWORD_MIN_LENGTH,
            "csrf_note_de": "Bearer-Auth ohne Cookie-Session → CSRF-Risiko gering",
        },
        "rbac_roles": sorted(ALL_ROLES),
        "audit_redaction": True,
        "security_headers": True,
        "ssrf_protection_data_updates": True,
        "connector_loopback_only": True,
        "productive_auto_updates_blocked": not settings.software_update_signing_cert_configured,
        "monitoring_enabled": settings.security_monitoring_enabled,
        "disclaimer_de": DISCLAIMER_DE,
        "threat_model": threat_model(),
        "findings": findings(),
        "open_risks_de": open_risks,
    }


def privacy_overview() -> dict:
    return {
        "disclaimer_de": (
            "Die folgenden Prozesse beschreiben technische Unterstützung für Auskunft, Export, "
            "Löschung und Aufbewahrung. Keine rechtliche Beratung und keine DSGVO-Konformitätszusage."
        ),
        "processes": [
            {
                "id": "P-AUSKUNFT",
                "title_de": "Auskunft / Datenportabilität",
                "description_de": (
                    "Werkstatt-Admin kann Kundenbundle als JSON exportieren "
                    "(nur eigener Mandant)."
                ),
                "api_hint": "GET /api/customers/{id}/export",
                "legal_note_de": "Fristen und Identitätsprüfung organisatorisch – nicht automatisiert.",
            },
            {
                "id": "P-LOESCHUNG",
                "title_de": "Löschung / Anonymisierung",
                "description_de": (
                    "Archive, Anonymize oder Delete mit Konfliktprüfung bei offenen Aufträgen."
                ),
                "api_hint": "POST /api/customers/{id}/privacy",
                "legal_note_de": "Aufbewahrungspflichten (Steuer/Gewähr) vor Löschung klären.",
            },
            {
                "id": "P-RETENTION",
                "title_de": "Aufbewahrung",
                "description_de": "retention_days am Werkstattprofil; Report-Purge nach Frist.",
                "api_hint": "PATCH /api/workshop/me · POST /api/reports/purge",
                "legal_note_de": "Default 365 Tage – rechtliche Prüfung offen (BLK-LEGAL).",
            },
            {
                "id": "P-AV",
                "title_de": "Auftragsverarbeitung",
                "description_de": "AV-Vertrag / TOMs organisatorisch; technisch Mandantentrennung + Audit.",
                "api_hint": None,
                "legal_note_de": "Keine Konformität behauptet; Vorlage extern.",
            },
        ],
        "retention_note_de": "Aufbewahrungsfrist konfigurierbar (30–3650 Tage), Soft-Delete/Purge für Berichte.",
        "av_note_de": "Auftragsverarbeitung erfordert rechtlichen AV-Vertrag – außerhalb dieses Codes.",
    }


def backup_overview() -> dict:
    return {
        "disclaimer_de": (
            "Backup/Restore ist dokumentiert und in Dev/Simulation nachvollziehbar. "
            "Kein automatisches Prod-Backup ohne Zustimmung. Keine Secrets in Dumps committen."
        ),
        "recommended_steps_de": [
            "Vor Migration/Deploy: pg_dump (custom/plain) mit Zeitstempel und Alembic-Revision.",
            "Optional Plesk → Datenbanken → Backup; Dump-Integrität prüfen (Größe / pg_restore --list).",
            "Web/API-Artefakte und Connector-Installer getrennt versionieren (Phase 14).",
            "Dump außerhalb Git lagern; Zugriff beschränken (PII).",
        ],
        "restore_steps_de": [
            "Wartungsmodus / API+Web stoppen.",
            "pg_restore aus bekanntem Stand; Alembic-Version prüfen.",
            "Healthcheck GET /health und Security-Dashboard prüfen.",
            "Stichprobe Login + Mandantenisolation.",
        ],
        "monitoring_hints_de": [
            "GET /health periodisch (Uptime).",
            "Login-Rate-Limit 429 beobachten.",
            "Audit auf login_failed Häufung prüfen.",
            "Produktives Alerting erst nach Zustimmung (Phase 16 Checkliste).",
        ],
        "phase16_checklist_hint": "docs/phase-16-deploy-checklist.md – Deploy bereits weitgehend live; nur ergänzen.",
    }
