"""Enumeraciones — SCIM 2.0 (1380)."""

from __future__ import annotations


class ScimProvisionStatus:
    PROVISIONADO = "PROVISIONADO"
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    DESACTIVADO = "DESACTIVADO"
    ALL = frozenset({PROVISIONADO, ACTIVO, SUSPENDIDO, DESACTIVADO})


class ScimAuditAction:
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_PATCH = "USER_PATCH"
    USER_DEACTIVATE = "USER_DEACTIVATE"
    USER_REACTIVATE = "USER_REACTIVATE"
    GROUP_CREATE = "GROUP_CREATE"
    GROUP_UPDATE = "GROUP_UPDATE"
    GROUP_PATCH = "GROUP_PATCH"
    GROUP_DELETE = "GROUP_DELETE"
    MEMBERSHIP_ADD = "MEMBERSHIP_ADD"
    MEMBERSHIP_REMOVE = "MEMBERSHIP_REMOVE"
    TOKEN_CREATE = "TOKEN_CREATE"
    TOKEN_ROTATE = "TOKEN_ROTATE"
    TOKEN_REVOKE = "TOKEN_REVOKE"
    CONFLICT = "CONFLICT"
    PRIVILEGE_DENIED = "PRIVILEGE_DENIED"
    RATE_LIMITED = "RATE_LIMITED"


PROTECTED_SCIM_ROLES = frozenset({"superadmin", "platform_admin", "SUPERADMIN", "admin"})

SCIM_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCIM_PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"
SCIM_LIST_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SCIM_ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"
