from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    user_id: str | None,
    action: str,
    resource: str,
    detail: str | None = None,
) -> None:
    db.add(AuditLog(user_id=user_id, action=action, resource=resource, detail=detail))
    db.commit()
