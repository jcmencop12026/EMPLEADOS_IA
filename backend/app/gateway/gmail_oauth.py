"""OAuth 2.0 para autenticacion SMTP Gmail sin contrasenas de aplicacion."""
from __future__ import annotations

import base64
import smtplib

import httpx

TOKEN_URL = "https://oauth2.googleapis.com/token"


def refresh_access_token(*, client_id: str, client_secret: str, refresh_token: str) -> str:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    response.raise_for_status()
    token = str(response.json().get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Google OAuth no devolvio access_token.")
    return token


def smtp_xoauth2_login(smtp: smtplib.SMTP, *, username: str, access_token: str) -> None:
    raw = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    code, response = smtp.docmd("AUTH", "XOAUTH2 " + encoded)
    if code == 235:
        return
    if code == 334:
        code, response = smtp.docmd("")
    raise smtplib.SMTPAuthenticationError(code, response)


def send_gmail_api_message(*, access_token: str, message_bytes: bytes) -> str:
    raw = base64.urlsafe_b64encode(message_bytes).decode("ascii")
    response = httpx.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw},
        timeout=20,
    )
    response.raise_for_status()
    return str(response.json().get("id") or "")
