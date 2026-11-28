"""Lizenzverwaltung: serverseitige Prüfung, Gerätebindung, Offline-Toleranz-Hinweis.

Kein Fake-„Lizenz gültig“ ohne Abo-Status.
Phase 23: signierte Offline-Tokens (HMAC) für Connector-Gate.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscriptions import DeviceBinding, Subscription
from app.services.audit import write_audit
from app.services.subscriptions import refresh_subscription_status, subscription_to_dict


OFFLINE_TOLERANCE_HOURS = 72


def _now() -> datetime:
    return datetime.now(timezone.utc)


def license_overview(db: Session, workshop_id: str) -> dict[str, Any]:
    subs = (
        db.query(Subscription)
        .filter(Subscription.workshop_id == workshop_id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    devices = (
        db.query(DeviceBinding)
        .filter(DeviceBinding.workshop_id == workshop_id)
        .order_by(DeviceBinding.created_at.desc())
        .all()
    )
    active = [s for s in subs if s.status in {"trialing", "active"}]
    return {
        "workshop_id": workshop_id,
        "active_licenses": len(active),
        "subscriptions": [subscription_to_dict(db, s) for s in subs],
        "devices": [
            {
                "id": d.id,
                "device_name": d.device_name,
                "device_fingerprint": d.device_fingerprint,
                "platform": d.platform,
                "subscription_id": d.subscription_id,
                "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                "revoked": d.revoked_at is not None,
            }
            for d in devices
        ],
        "offline_tolerance_hours": OFFLINE_TOLERANCE_HOURS,
        "message_de": (
            "Lizenzprüfung serverseitig. Offline-Toleranz ist ein Connector-Hinweis – "
            "kein Ersatz für Server-Validierung nach Ablauf."
        ),
    }


def activate_or_refresh_license(
    db: Session,
    *,
    workshop_id: str,
    subscription_id: str,
    device_name: str,
    device_fingerprint: str,
    platform: str = "windows",
) -> dict[str, Any]:
    sub = db.get(Subscription, subscription_id)
    if not sub or sub.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Subscription nicht gefunden")
    refresh_subscription_status(sub)
    if sub.status not in {"trialing", "active"}:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Lizenz nicht aktiv (status={sub.status})",
        )

    binding = (
        db.query(DeviceBinding)
        .filter(
            DeviceBinding.workshop_id == workshop_id,
            DeviceBinding.device_fingerprint == device_fingerprint,
        )
        .first()
    )
    if binding and binding.revoked_at is not None:
        binding.revoked_at = None
    if binding is None:
        binding = DeviceBinding(
            workshop_id=workshop_id,
            subscription_id=subscription_id,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            platform=platform,
            is_example_data=False,
        )
        db.add(binding)
    else:
        binding.subscription_id = subscription_id
        binding.device_name = device_name
        binding.platform = platform
    binding.last_seen_at = _now()
    db.commit()
    db.refresh(binding)
    write_audit(
        db,
        user_id=None,
        action="license_device_bind",
        resource="device_binding",
        detail=binding.id,
        workshop_id=workshop_id,
    )
    return {
        "ok": True,
        "license_status": sub.status,
        "plan_code": sub.plan_code,
        "device_binding_id": binding.id,
        "offline_valid_until": (_now() + timedelta(hours=OFFLINE_TOLERANCE_HOURS)).isoformat(),
        "entitlements": subscription_to_dict(db, sub).get("entitlements"),
        "message_de": "Gerät gebunden / Lizenz bestätigt.",
    }


def revoke_device(
    db: Session,
    *,
    workshop_id: str,
    binding_id: str,
) -> dict[str, Any]:
    binding = db.get(DeviceBinding, binding_id)
    if not binding or binding.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Gerätebindung nicht gefunden")
    binding.revoked_at = _now()
    db.commit()
    write_audit(
        db,
        user_id=None,
        action="license_device_revoke",
        resource="device_binding",
        detail=binding_id,
        workshop_id=workshop_id,
    )
    return {"ok": True, "revoked": True, "id": binding_id}


def verify_connector_license(
    db: Session,
    *,
    workshop_id: str,
    device_fingerprint: str,
) -> dict[str, Any]:
    binding = (
        db.query(DeviceBinding)
        .filter(
            DeviceBinding.workshop_id == workshop_id,
            DeviceBinding.device_fingerprint == device_fingerprint,
            DeviceBinding.revoked_at.is_(None),
        )
        .first()
    )
    if binding is None:
        return {
            "ok": False,
            "allowed": False,
            "reason": "device_not_bound",
            "message_de": "Gerät nicht lizenziert.",
        }
    sub = db.get(Subscription, binding.subscription_id) if binding.subscription_id else None
    if sub is None:
        return {
            "ok": False,
            "allowed": False,
            "reason": "no_subscription",
            "message_de": "Keine Subscription an Gerätebindung.",
        }
    refresh_subscription_status(sub)
    allowed = sub.status in {"trialing", "active"}
    binding.last_seen_at = _now()
    db.commit()
    return {
        "ok": True,
        "allowed": allowed,
        "license_status": sub.status,
        "plan_code": sub.plan_code,
        "offline_tolerance_hours": OFFLINE_TOLERANCE_HOURS,
        "message_de": "Lizenz aktiv." if allowed else f"Lizenz gesperrt ({sub.status}).",
    }


def _hmac_hex(payload: str) -> str:
    secret = (get_settings().license_hmac_secret or "").encode("utf-8")
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_signed_offline_token(
    db: Session,
    *,
    workshop_id: str,
    device_fingerprint: str,
    valid_hours: int | None = None,
) -> dict[str, Any]:
    """Erzeugt HMAC-signiertes Offline-Token für Connector ApplySignedToken."""
    verify = verify_connector_license(
        db, workshop_id=workshop_id, device_fingerprint=device_fingerprint
    )
    hours = max(1, min(int(valid_hours or OFFLINE_TOLERANCE_HOURS), 72))
    exp = int((_now() + timedelta(hours=hours)).timestamp())
    payload_obj = {
        "device_id": device_fingerprint,
        "workshop_id": workshop_id,
        "plan_code": verify.get("plan_code") or "none",
        "exp": exp,
        "jti": uuid.uuid4().hex,
        "allowed": bool(verify.get("allowed")),
        "entitlements": ["obd_live", "dtc_read"] if verify.get("allowed") else [],
    }
    payload = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True)
    sig = _hmac_hex(payload)
    return {
        **verify,
        "payload": payload,
        "signature": sig,
        "offline_hours": hours,
        "apply_hint": "POST connector /license/gate/apply mit {payload, signature}",
    }
