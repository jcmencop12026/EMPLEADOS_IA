"""Respuestas y errores SCIM 2.0 (1380)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.scim_enums import SCIM_ERROR_SCHEMA, SCIM_GROUP_SCHEMA, SCIM_LIST_SCHEMA, SCIM_USER_SCHEMA


def scim_error(status: int, detail: str, scim_type: str | None = None) -> JSONResponse:
    body: dict[str, Any] = {
        "schemas": [SCIM_ERROR_SCHEMA],
        "status": str(status),
        "detail": detail,
    }
    if scim_type:
        body["scimType"] = scim_type
    return JSONResponse(status_code=status, content=body)


def scim_meta(*, resource_type: str, created: datetime, modified: datetime, location: str, version: int) -> dict:
    return {
        "resourceType": resource_type,
        "created": created.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "lastModified": modified.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "location": location,
        "version": f'W/"{version}"',
    }


def user_to_scim(row, *, base_url: str, groups: list[str] | None = None) -> dict:
    from app.scim_models import ScimUserResource
    assert isinstance(row, ScimUserResource)
    active = row.provision_status in ("PROVISIONADO", "ACTIVO")
    emails = []
    if row.emails_json:
        import json
        try:
            emails = json.loads(row.emails_json)
        except json.JSONDecodeError:
            emails = []
    return {
        "schemas": [SCIM_USER_SCHEMA],
        "id": row.id,
        "externalId": row.external_id,
        "userName": row.user_name,
        "name": {"formatted": row.display_name or row.user_name},
        "displayName": row.display_name or row.user_name,
        "emails": emails or [{"value": row.user_name, "primary": True}],
        "active": active,
        "groups": [{"value": g} for g in (groups or [])],
        "meta": scim_meta(
            resource_type="User",
            created=row.created_at,
            modified=row.updated_at,
            location=f"{base_url}/scim/v2/Users/{row.id}",
            version=row.version,
        ),
    }


def group_to_scim(group, members: list[dict], *, base_url: str) -> dict:
    return {
        "schemas": [SCIM_GROUP_SCHEMA],
        "id": group.id,
        "externalId": group.external_id,
        "displayName": group.display_name,
        "members": members,
        "meta": scim_meta(
            resource_type="Group",
            created=group.created_at,
            modified=group.updated_at,
            location=f"{base_url}/scim/v2/Groups/{group.id}",
            version=group.version,
        ),
    }


def list_response(resources: list[dict], *, total: int, start: int, count: int) -> dict:
    return {
        "schemas": [SCIM_LIST_SCHEMA],
        "totalResults": total,
        "startIndex": start,
        "itemsPerPage": count,
        "Resources": resources,
    }


SERVICE_PROVIDER_CONFIG = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
    "patch": {"supported": True},
    "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
    "filter": {"supported": True, "maxResults": 200},
    "changePassword": {"supported": False},
    "sort": {"supported": False},
    "etag": {"supported": True},
    "authenticationSchemes": [
        {
            "type": "oauthbearertoken",
            "name": "Bearer Token",
            "description": "Token de aprovisionamiento SCIM por organización",
        }
    ],
}

RESOURCE_TYPES = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
    "Resources": [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "User",
            "name": "User",
            "endpoint": "/Users",
            "schema": SCIM_USER_SCHEMA,
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "Group",
            "name": "Group",
            "endpoint": "/Groups",
            "schema": SCIM_GROUP_SCHEMA,
        },
    ],
}

SCHEMAS = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
    "Resources": [
        {
            "id": SCIM_USER_SCHEMA,
            "name": "User",
            "attributes": [
                {"name": "userName", "type": "string", "required": True},
                {"name": "externalId", "type": "string"},
                {"name": "displayName", "type": "string"},
                {"name": "active", "type": "boolean"},
            ],
        },
        {
            "id": SCIM_GROUP_SCHEMA,
            "name": "Group",
            "attributes": [
                {"name": "displayName", "type": "string", "required": True},
                {"name": "externalId", "type": "string"},
                {"name": "members", "type": "complex", "multiValued": True},
            ],
        },
    ],
}
