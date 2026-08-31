"""Cifrado de secretos MFA — Bloque 1300."""

from __future__ import annotations

import base64
import hashlib
import secrets

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Secreto MFA no válido") from exc


def hash_recovery_code(code: str) -> str:
    normalized = code.strip().replace(" ", "").upper()
    return bcrypt.hashpw(normalized.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_recovery_code(code: str, code_hash: str) -> bool:
    normalized = code.strip().replace(" ", "").upper()
    return bcrypt.checkpw(normalized.encode("utf-8"), code_hash.encode("utf-8"))


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_recovery_codes(count: int = 8) -> list[str]:
    codes: list[str] = []
    for _ in range(count):
        part_a = secrets.token_hex(2).upper()
        part_b = secrets.token_hex(2).upper()
        codes.append(f"{part_a}-{part_b}")
    return codes
