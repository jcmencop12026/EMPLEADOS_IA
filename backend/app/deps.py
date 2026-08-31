from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, User
from app.security import decode_access_token
from app.services.session_service import get_valid_session, touch_session
from app.tenant_scope import ensure_organization_active

bearer = HTTPBearer(auto_error=False)


def _resolve_user_from_payload(payload: dict, db: Session) -> User:
    if payload.get("type") == "mfa_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe completar la verificación MFA.",
        )
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    ensure_organization_active(org)
    session_id = payload.get("sid")
    if session_id:
        session = get_valid_session(db, str(session_id))
        if not session or session.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o revocada")
        touch_session(db, session)
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    payload = decode_access_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return _resolve_user_from_payload(payload, db)


def get_mfa_pending_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    payload = decode_access_token(creds.credentials)
    if not payload or payload.get("type") != "mfa_pending" or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token MFA inválido o expirado")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    ensure_organization_active(org)
    return user


def get_current_session_id(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str | None:
    if creds is None or not creds.credentials:
        return None
    payload = decode_access_token(creds.credentials)
    if not payload:
        return None
    sid = payload.get("sid")
    return str(sid) if sid else None
