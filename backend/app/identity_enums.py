"""Enumeraciones — Identidad empresarial y SSO (1370)."""

from __future__ import annotations


class AuthMode:
    SOLO_LOCAL = "SOLO_LOCAL"
    LOCAL_Y_SSO = "LOCAL_Y_SSO"
    SOLO_SSO = "SOLO_SSO"
    ALL = frozenset({SOLO_LOCAL, LOCAL_Y_SSO, SOLO_SSO})


class IdPType:
    OIDC = "OIDC"
    SAML = "SAML"
    ALL = frozenset({OIDC, SAML})


class IdPStatus:
    BORRADOR = "BORRADOR"
    CONFIGURADO = "CONFIGURADO"
    VERIFICADO = "VERIFICADO"
    ACTIVO = "ACTIVO"
    ERROR = "ERROR"
    DESHABILITADO = "DESHABILITADO"
    ALL = frozenset({BORRADOR, CONFIGURADO, VERIFICADO, ACTIVO, ERROR, DESHABILITADO})


class MfaSsoMode:
    EAIOS = "EAIOS"
    IDP = "IDP"
    ADICIONAL = "ADICIONAL"
    ALL = frozenset({EAIOS, IDP, ADICIONAL})


class SsoLoginResult:
    EXITOSO = "EXITOSO"
    FALLIDO = "FALLIDO"
    MFA_REQUERIDO = "MFA_REQUERIDO"


FORBIDDEN_AUTO_ROLES = frozenset({"superadmin", "platform_admin", "SUPERADMIN", "admin"})
