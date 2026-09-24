"""Operaciones PATCH SCIM (1380)."""

from __future__ import annotations

from typing import Any

PROTECTED_USER_PATHS = frozenset({"id", "meta", "schemas", "role", "organizationid"})
PROTECTED_GROUP_PATHS = frozenset({"id", "meta", "schemas"})


class ScimPatchError(ValueError):
    pass


def apply_patch(target: dict[str, Any], operations: list[dict], *, protected: frozenset[str]) -> dict[str, Any]:
    data = dict(target)
    for op in operations:
        operation = (op.get("op") or "replace").lower()
        path = (op.get("path") or "").strip()
        value = op.get("value")
        if path:
            key = path.split("[")[0].split(".")[-1]
            if key.lower() in protected:
                raise ScimPatchError(f"Campo protegido: {path}")
        if operation == "replace":
            if path:
                key = path.split("[")[0].split(".")[-1]
                data[key] = value
            elif isinstance(value, dict):
                for k, v in value.items():
                    if k.lower() in protected:
                        raise ScimPatchError(f"Campo protegido: {k}")
                    data[k] = v
        elif operation == "add":
            if path == "members" and isinstance(value, list):
                existing = data.get("members") or []
                data["members"] = existing + value
            elif path:
                data[path.split(".")[-1]] = value
            elif isinstance(value, dict):
                data.update(value)
        elif operation == "remove":
            if path == "members" and isinstance(value, list):
                remove_vals = {m.get("value") for m in value}
                data["members"] = [m for m in (data.get("members") or []) if m.get("value") not in remove_vals]
            elif path:
                data.pop(path.split(".")[-1], None)
        else:
            raise ScimPatchError(f"Operación no soportada: {operation}")
    return data
