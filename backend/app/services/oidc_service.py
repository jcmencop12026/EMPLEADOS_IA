"""Servicio OIDC — discovery, PKCE, validación JWT/JWKS (1370)."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from jose import jwt
from jose.exceptions import JWTError

from app.gateway.secrets import resolve_secret


class OidcError(ValueError):
  def __init__(self, message: str, *, category: str = "OIDC"):
    super().__init__(message)
    self.category = category


_JWKS_CACHE: dict[str, tuple[float, dict]] = {}
_JWKS_TTL = 300


def generate_pkce() -> tuple[str, str]:
  verifier = secrets.token_urlsafe(64)
  challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
  return verifier, challenge


def discover_oidc(config: dict) -> dict:
  if config.get("mock_discovery"):
    return config["mock_discovery"]
  issuer = config.get("issuer")
  if not issuer:
    raise OidcError("Issuer OIDC no configurado")
  well_known = issuer.rstrip("/") + "/.well-known/openid-configuration"
  raise OidcError(f"Descubrimiento remoto no disponible en pruebas: {well_known}")


def get_jwks(config: dict) -> dict:
  cache_key = config.get("jwks_uri") or config.get("issuer") or "mock"
  cached = _JWKS_CACHE.get(cache_key)
  now = time.time()
  if cached and now - cached[0] < _JWKS_TTL:
    return cached[1]
  if config.get("mock_jwks"):
    jwks = config["mock_jwks"]
    _JWKS_CACHE[cache_key] = (now, jwks)
    return jwks
  raise OidcError("JWKS no configurado")


def build_authorization_url(config: dict, *, state: str, nonce: str, redirect_uri: str, pkce_challenge: str) -> str:
  discovery = discover_oidc(config)
  auth_endpoint = discovery.get("authorization_endpoint") or config.get("authorization_endpoint")
  if not auth_endpoint:
    raise OidcError("Authorization endpoint no disponible")
  client_id = config.get("client_id")
  if not client_id:
    raise OidcError("Client ID no configurado")
  scopes = config.get("scopes") or "openid profile email"
  params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": scopes,
    "state": state,
    "nonce": nonce,
    "code_challenge": pkce_challenge,
    "code_challenge_method": "S256",
  }
  return f"{auth_endpoint}?{urlencode(params)}"


def exchange_code_mock(config: dict, *, code: str) -> dict:
  mock_tokens = config.get("mock_tokens") or {}
  if code not in mock_tokens and "default" not in mock_tokens:
    raise OidcError("Código de autorización inválido", category="AUTENTICACION")
  return mock_tokens.get(code) or mock_tokens["default"]


def validate_id_token(
  id_token: str,
  config: dict,
  *,
  nonce: str | None,
  expected_audience: str | None = None,
) -> dict[str, Any]:
  if not id_token or id_token.count(".") != 2:
    raise OidcError("Token ID mal formado", category="VALIDACION")
  header = jwt.get_unverified_header(id_token)
  alg = header.get("alg", "")
  if alg.lower() == "none":
    raise OidcError("Algoritmo none no permitido", category="VALIDACION")
  if alg.upper() not in ("RS256", "HS256"):
    raise OidcError(f"Algoritmo no permitido: {alg}", category="VALIDACION")

  issuer = config.get("issuer")
  audience = expected_audience or config.get("client_id")
  try:
    if alg.upper() == "HS256":
      secret = resolve_secret(config.get("secret_ref")) or config.get("mock_hmac_secret")
      if not secret:
        raise OidcError("Secreto OIDC no configurado", category="AUTENTICACION")
      claims = jwt.decode(id_token, secret, algorithms=["HS256"], audience=audience, issuer=issuer)
    else:
      jwks = get_jwks(config)
      claims = jwt.decode(id_token, jwks, algorithms=["RS256"], audience=audience, issuer=issuer)
  except JWTError as exc:
    raise OidcError(f"Token ID inválido: {exc}", category="VALIDACION") from exc

  if nonce and claims.get("nonce") != nonce:
    raise OidcError("Nonce inválido", category="VALIDACION")
  exp = claims.get("exp")
  if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
    raise OidcError("Token expirado", category="VALIDACION")
  return claims
