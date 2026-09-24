"""Servicio MFA TOTP — Bloque 1300."""

from __future__ import annotations

import base64
import io
from datetime import datetime, timezone

import pyotp
import qrcode
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import User
from app.security_models import UserMfaRecoveryCode, UserMfaSettings
from app.services.mfa_crypto import (
    decrypt_secret,
    encrypt_secret,
    generate_recovery_codes,
    hash_recovery_code,
    verify_recovery_code,
)
from app.services.security_event_service import log_security_event


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_mfa_settings(db: Session, user: User) -> UserMfaSettings:
    row = db.query(UserMfaSettings).filter(UserMfaSettings.user_id == user.id).first()
    if row:
        return row
    row = UserMfaSettings(user_id=user.id, organization_id=user.organization_id)
    db.add(row)
    db.flush()
    return row


def start_mfa_enrollment(db: Session, user: User, *, issuer: str = "EMPLEADOS IA") -> dict:
    settings_row = get_or_create_mfa_settings(db, user)
    if settings_row.enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MFA ya está habilitado.")

    secret = pyotp.random_base32()
    settings_row.pending_secret_encrypted = encrypt_secret(secret)
    settings_row.enabled = False
    settings_row.secret_encrypted = None
    db.flush()

    label = user.email or user.username
    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(name=label, issuer_name=issuer)
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_data_url": qr_data_url,
    }


def confirm_mfa_enrollment(db: Session, user: User, code: str) -> list[str]:
    settings_row = get_or_create_mfa_settings(db, user)
    if settings_row.enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MFA ya está habilitado.")
    if not settings_row.pending_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe iniciar la configuración MFA primero.")

    secret = decrypt_secret(settings_row.pending_secret_encrypted)
    if not pyotp.TOTP(secret).verify(code.strip().replace(" ", ""), valid_window=1):
        log_security_event(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            event_type="MFA_FALLIDO",
            detail="confirmacion_enrolamiento",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código de verificación incorrecto.")

    settings_row.secret_encrypted = settings_row.pending_secret_encrypted
    settings_row.pending_secret_encrypted = None
    settings_row.enabled = True
    settings_row.confirmed_at = _utcnow()

    db.query(UserMfaRecoveryCode).filter(UserMfaRecoveryCode.user_id == user.id).delete()
    plain_codes = generate_recovery_codes()
    for plain in plain_codes:
        db.add(
            UserMfaRecoveryCode(
                user_id=user.id,
                organization_id=user.organization_id,
                code_hash=hash_recovery_code(plain),
            )
        )

    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="MFA_HABILITADO",
        detail="enrolamiento_confirmado",
    )
    write_audit(db, action="security.mfa.enabled", organization_id=user.organization_id, user_id=user.id, commit=False)
    db.flush()
    return plain_codes


def disable_mfa(db: Session, user: User, *, password: str, verify_password_fn) -> None:
    settings_row = get_or_create_mfa_settings(db, user)
    if not settings_row.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA no está habilitado.")
    if not verify_password_fn(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña incorrecta.")

    settings_row.enabled = False
    settings_row.secret_encrypted = None
    settings_row.pending_secret_encrypted = None
    settings_row.confirmed_at = None
    db.query(UserMfaRecoveryCode).filter(UserMfaRecoveryCode.user_id == user.id).delete()

    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="MFA_DESHABILITADO",
        detail="usuario",
    )
    write_audit(db, action="security.mfa.disabled", organization_id=user.organization_id, user_id=user.id, commit=False)


def regenerate_recovery_codes(db: Session, user: User, *, password: str, verify_password_fn) -> list[str]:
    settings_row = get_or_create_mfa_settings(db, user)
    if not settings_row.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA no está habilitado.")
    if not verify_password_fn(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña incorrecta.")

    db.query(UserMfaRecoveryCode).filter(UserMfaRecoveryCode.user_id == user.id).delete()
    plain_codes = generate_recovery_codes()
    for plain in plain_codes:
        db.add(
            UserMfaRecoveryCode(
                user_id=user.id,
                organization_id=user.organization_id,
                code_hash=hash_recovery_code(plain),
            )
        )
    write_audit(
        db,
        action="security.mfa.recovery_regenerated",
        organization_id=user.organization_id,
        user_id=user.id,
        commit=False,
    )
    db.flush()
    return plain_codes


def verify_totp_or_recovery(db: Session, user: User, code: str) -> bool:
    settings_row = get_or_create_mfa_settings(db, user)
    if not settings_row.enabled or not settings_row.secret_encrypted:
        return False

    normalized = code.strip().replace(" ", "")
    secret = decrypt_secret(settings_row.secret_encrypted)
    if pyotp.TOTP(secret).verify(normalized, valid_window=1):
        return True

    normalized_recovery = normalized.upper()
    rows = (
        db.query(UserMfaRecoveryCode)
        .filter(UserMfaRecoveryCode.user_id == user.id, UserMfaRecoveryCode.used_at.is_(None))
        .all()
    )
    for row in rows:
        if verify_recovery_code(normalized_recovery, row.code_hash):
            row.used_at = _utcnow()
            db.flush()
            return True
    return False


def mfa_status(db: Session, user: User) -> dict:
    settings_row = db.query(UserMfaSettings).filter(UserMfaSettings.user_id == user.id).first()
    unused_codes = 0
    if settings_row and settings_row.enabled:
        unused_codes = (
            db.query(UserMfaRecoveryCode)
            .filter(UserMfaRecoveryCode.user_id == user.id, UserMfaRecoveryCode.used_at.is_(None))
            .count()
        )
    return {
        "enabled": bool(settings_row and settings_row.enabled),
        "confirmed_at": settings_row.confirmed_at if settings_row else None,
        "recovery_codes_remaining": unused_codes,
        "enrollment_pending": bool(settings_row and settings_row.pending_secret_encrypted and not settings_row.enabled),
    }
