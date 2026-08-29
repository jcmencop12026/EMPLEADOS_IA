"""Seguridad avanzada — MFA, sesiones, políticas y eventos."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.database import get_db
from app.deps import get_current_session_id, get_current_user
from app.models import User
from app.permissions import check_permission, require_permission
from app.schemas_security import (
    MfaConfirmRequest,
    MfaEnrollStartResponse,
    MfaPasswordConfirmRequest,
    MfaRecoveryCodesResponse,
    MfaStatusOut,
    SecurityEventOut,
    SecurityPolicyOut,
    SecurityPolicyUpdate,
    SessionOut,
)
from app.security import verify_password
from app.services import mfa_service
from app.services.request_context import client_ip
from app.services.security_event_service import list_security_events, log_security_event
from app.services.semantic_enrichment_post_v1 import enrich_list_semantic, from_security_event
from app.services.security_policy_service import (
    get_or_create_policy,
    is_mfa_required_for_user,
    parse_required_roles,
    update_policy,
)
from app.services.session_service import (
    get_valid_session,
    list_org_sessions,
    list_user_sessions,
    revoke_other_sessions,
    revoke_session,
)

router = APIRouter(prefix="/api/security", tags=["security"])


def _session_out(session, *, current_sid: str | None) -> SessionOut:
    return SessionOut(
        id=session.id,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        created_at=session.created_at,
        last_activity_at=session.last_activity_at,
        expires_at=session.expires_at,
        mfa_verified=session.mfa_verified,
        current=bool(current_sid and session.id == current_sid),
    )


@router.get("/mfa/status", response_model=MfaStatusOut)
def mfa_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    status_data = mfa_service.mfa_status(db, user)
    return MfaStatusOut(
        **status_data,
        mfa_required_by_policy=is_mfa_required_for_user(db, user),
    )


@router.post("/mfa/enroll/start", response_model=MfaEnrollStartResponse)
def mfa_enroll_start(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = mfa_service.start_mfa_enrollment(db, user)
    db.commit()
    return MfaEnrollStartResponse(**data)


@router.post("/mfa/enroll/confirm", response_model=MfaRecoveryCodesResponse)
def mfa_enroll_confirm(
    body: MfaConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    codes = mfa_service.confirm_mfa_enrollment(db, user, body.code)
    db.commit()
    return MfaRecoveryCodesResponse(recovery_codes=codes)


@router.post("/mfa/disable")
def mfa_disable(
    body: MfaPasswordConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mfa_service.disable_mfa(db, user, password=body.password, verify_password_fn=verify_password)
    db.commit()
    return {"message": "Autenticación multifactor deshabilitada."}


@router.post("/mfa/recovery/regenerate", response_model=MfaRecoveryCodesResponse)
def mfa_regenerate_recovery(
    body: MfaPasswordConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    codes = mfa_service.regenerate_recovery_codes(
        db,
        user,
        password=body.password,
        verify_password_fn=verify_password,
    )
    db.commit()
    return MfaRecoveryCodesResponse(recovery_codes=codes)


@router.get("/sessions", response_model=list[SessionOut])
def my_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_sid: str | None = Depends(get_current_session_id),
):
    sessions = list_user_sessions(db, user.id)
    return [_session_out(s, current_sid=current_sid) for s in sessions]


@router.delete("/sessions/{session_id}")
def revoke_my_session(
    session_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_valid_session(db, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada.")
    revoke_session(db, session, reason="user_revoke")
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="SESION_REVOCADA",
        detail=session_id,
        ip_address=client_ip(request),
    )
    write_audit(
        db,
        action="security.session.revoked",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=session_id,
        commit=False,
    )
    db.commit()
    return {"message": "Sesión cerrada correctamente."}


@router.post("/sessions/revoke-others")
def revoke_other_my_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_sid: str | None = Depends(get_current_session_id),
):
    if not current_sid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo identificar la sesión actual.")
    count = revoke_other_sessions(db, user.id, current_sid, reason="user_revoke_others")
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="SESION_REVOCADA",
        detail=f"revoke_others:{count}",
        ip_address=client_ip(request),
    )
    db.commit()
    return {"message": f"Se cerraron {count} sesión(es).", "revoked": count}


@router.get("/policy", response_model=SecurityPolicyOut)
def get_policy(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("seguridad.manage_policy")),
):
    policy = get_or_create_policy(db, user.organization_id)
    return SecurityPolicyOut(
        mfa_mode=policy.mfa_mode,
        mfa_required_roles=sorted(parse_required_roles(policy.mfa_required_roles_json)),
        session_duration_minutes=policy.session_duration_minutes,
        max_active_sessions=policy.max_active_sessions,
        login_max_attempts=policy.login_max_attempts,
        lockout_minutes=policy.lockout_minutes,
        revoke_sessions_on_password_change=policy.revoke_sessions_on_password_change,
        excess_session_policy=policy.excess_session_policy,
    )


@router.put("/policy", response_model=SecurityPolicyOut)
def update_security_policy(
    body: SecurityPolicyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("seguridad.manage_policy")),
):
    policy = update_policy(
        db,
        organization_id=user.organization_id,
        updates=body.model_dump(exclude_unset=True),
    )
    write_audit(
        db,
        action="security.policy.updated",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=json.dumps(body.model_dump(exclude_unset=True), ensure_ascii=False)[:500],
        commit=False,
    )
    db.commit()
    return SecurityPolicyOut(
        mfa_mode=policy.mfa_mode,
        mfa_required_roles=sorted(parse_required_roles(policy.mfa_required_roles_json)),
        session_duration_minutes=policy.session_duration_minutes,
        max_active_sessions=policy.max_active_sessions,
        login_max_attempts=policy.login_max_attempts,
        lockout_minutes=policy.lockout_minutes,
        revoke_sessions_on_password_change=policy.revoke_sessions_on_password_change,
        excess_session_policy=policy.excess_session_policy,
    )


@router.get("/events", response_model=list[SecurityEventOut])
def security_events(
    limit: int = 50,
    event_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("seguridad.audit")),
):
    rows = list_security_events(db, organization_id=user.organization_id, limit=min(limit, 200), event_type=event_type)
    enriched = enrich_list_semantic(
        [SecurityEventOut.model_validate(row).model_dump() for row in rows],
        from_security_event,
    )
    return [SecurityEventOut(**row) for row in enriched]


@router.get("/admin/sessions", response_model=list[SessionOut])
def admin_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("seguridad.revoke_sessions")),
):
    sessions = list_org_sessions(db, user.organization_id)
    return [_session_out(s, current_sid=None) for s in sessions]


@router.delete("/admin/sessions/{session_id}")
def admin_revoke_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("seguridad.revoke_sessions")),
):
    session = get_valid_session(db, session_id)
    if not session or session.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada.")
    revoke_session(db, session, reason="admin_revoke")
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="SESION_REVOCADA",
        detail=f"admin:{session.user_id}",
        ip_address=client_ip(request),
    )
    write_audit(
        db,
        action="security.session.admin_revoked",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=session_id,
        commit=False,
    )
    db.commit()
    return {"message": "Sesión revocada correctamente."}


@router.get("/overview")
def security_overview(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("seguridad.view")),
):
    check_permission(user, "seguridad.view", db)
    from app.services import admin_service as admin_svc

    summary = admin_svc.security_summary(db, user.organization_id)
    policy = get_or_create_policy(db, user.organization_id)
    events = list_security_events(db, organization_id=user.organization_id, limit=10)
    return {
        **summary,
        "policy": {
            "mfa_mode": policy.mfa_mode,
            "max_active_sessions": policy.max_active_sessions,
        },
        "security_events": [
            {
                "event_type": ev.event_type,
                "detail": ev.detail,
                "created_at": ev.created_at,
            }
            for ev in events
        ],
    }
