"""Autenticación — login, MFA y recuperación de contraseña."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.database import get_db
from app.deps import get_current_session_id, get_current_user
from app.events.bus import EventMessage, publish
from app.models import Organization, User
from app.permissions import user_permissions
from app.schemas import LoginRequest, TokenResponse, UserMe
from app.schemas_security import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MfaChallengeResponse,
    MfaVerifyRequest,
    ResetPasswordRequest,
)
from app.security import create_access_token, create_mfa_pending_token, decode_access_token, hash_password, verify_password
from app.services import mfa_service
from app.services.password_recovery_service import request_password_reset, reset_password_with_token
from app.services.rate_limit_service import (
    check_login_allowed,
    check_mfa_rate_limit,
    check_recovery_rate_limit,
    record_login_attempt,
)
from app.services.request_context import client_ip, client_user_agent
from app.services.security_event_service import log_security_event
from app.services.security_policy_service import get_or_create_policy, is_mfa_required_for_user, user_has_mfa_enabled
from app.services.session_service import create_session, revoke_all_user_sessions, revoke_other_sessions

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_session_token(db: Session, user: User, *, ip: str | None, user_agent: str | None, mfa_verified: bool) -> str:
    session = create_session(
        db,
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        mfa_verified=mfa_verified,
    )
    policy = get_or_create_policy(db, user.organization_id)
    return create_access_token(
        user.id,
        {"role": user.role, "org": user.organization_id, "sid": session.id},
        expires_minutes=policy.session_duration_minutes,
    )


@router.post("/login", response_model=Union[TokenResponse, MfaChallengeResponse])
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    user = db.query(User).filter(User.username == body.username).first()
    org_id = user.organization_id if user else None

    if user and org_id:
        check_login_allowed(db, username=body.username, organization_id=org_id, ip_address=ip)

    if not user or not verify_password(body.password, user.password_hash):
        if user and org_id:
            record_login_attempt(db, username=body.username, ip_address=ip, success=False)
            log_security_event(
                db,
                organization_id=org_id,
                user_id=user.id,
                event_type="LOGIN_FALLIDO",
                ip_address=ip,
            )
            publish(
                EventMessage(
                    event_type="TENANT_SECURITY_EVENT",
                    organization_id=org_id,
                    user_id=user.id,
                    payload={"kind": "invalid_login", "username": body.username},
                ),
                db,
            )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    if not user.is_active or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o bloqueado")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org or org.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La empresa está inactiva o no está disponible")

    record_login_attempt(db, username=body.username, ip_address=ip, success=True)

    mfa_required = is_mfa_required_for_user(db, user)
    if mfa_required:
        if not user_has_mfa_enabled(db, user.id):
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debe configurar autenticación multifactor antes de iniciar sesión. Contacte a su administrador.",
            )
        log_security_event(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            event_type="MFA_REQUERIDO",
            ip_address=ip,
        )
        mfa_token = create_mfa_pending_token(user.id, organization_id=user.organization_id, role=user.role)
        db.commit()
        return MfaChallengeResponse(mfa_token=mfa_token)

    token = _issue_session_token(db, user, ip=ip, user_agent=client_user_agent(request), mfa_verified=False)
    user.last_login_at = datetime.now(timezone.utc)
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="LOGIN_EXITOSO",
        ip_address=ip,
    )
    write_audit(db, action="auth.login", organization_id=user.organization_id, user_id=user.id, detail=user.username, commit=False)
    db.commit()
    return TokenResponse(access_token=token)


@router.post("/mfa/verify", response_model=TokenResponse)
def verify_mfa(
    body: MfaVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = client_ip(request)
    token = body.mfa_token
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token MFA requerido")

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "mfa_pending":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token MFA inválido o expirado")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido")

    check_mfa_rate_limit(user_id=user.id, ip_address=ip)
    if not mfa_service.verify_totp_or_recovery(db, user, body.code):
        log_security_event(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            event_type="MFA_FALLIDO",
            ip_address=ip,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código de verificación incorrecto")

    access_token = _issue_session_token(
        db,
        user,
        ip=ip,
        user_agent=client_user_agent(request),
        mfa_verified=True,
    )
    user.last_login_at = datetime.now(timezone.utc)
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="MFA_EXITOSO",
        ip_address=ip,
    )
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="LOGIN_EXITOSO",
        ip_address=ip,
    )
    write_audit(db, action="auth.login.mfa", organization_id=user.organization_id, user_id=user.id, detail=user.username, commit=False)
    db.commit()
    return TokenResponse(access_token=access_token)


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    current_sid: str | None = Depends(get_current_session_id),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual incorrecta")

    policy = get_or_create_policy(db, user.organization_id)
    revoke_others = (
        body.revoke_other_sessions
        if body.revoke_other_sessions is not None
        else policy.revoke_sessions_on_password_change
    )
    user.password_hash = hash_password(body.new_password)
    if revoke_others:
        revoke_all_user_sessions(db, user.id, reason="password_change", except_session_id=current_sid)
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="CAMBIO_PASSWORD",
        ip_address=client_ip(request),
    )
    write_audit(db, action="auth.password_change", organization_id=user.organization_id, user_id=user.id, commit=False)
    db.commit()
    return {"message": "Contraseña actualizada correctamente."}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    check_recovery_rate_limit(ip_address=client_ip(request))
    request_password_reset(db, email_or_username=body.email_or_username)
    db.commit()
    return ForgotPasswordResponse(
        message="Si existe una cuenta asociada, recibirá instrucciones para restablecer su contraseña.",
    )


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_password_with_token(db, token=body.token, new_password=body.new_password)
    db.commit()
    return {"message": "Contraseña restablecida correctamente. Inicie sesión con su nueva contraseña."}


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    return UserMe(
        id=user.id,
        username=user.username,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org.name if org else "",
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        permissions=sorted(user_permissions(user, db)),
    )
