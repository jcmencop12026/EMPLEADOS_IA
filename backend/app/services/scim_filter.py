"""Filtros SCIM básicos — eq (1380)."""

from __future__ import annotations

import re
from typing import Any

_FILTER_RE = re.compile(
    r'^\s*([a-zA-Z][\w.]*)\s+eq\s+"([^"]*)"\s*$',
    re.IGNORECASE,
)

SUPPORTED_FILTER_ATTRS = frozenset({"username", "externalid", "active", "displayname"})


class ScimFilterError(ValueError):
    pass


def parse_filter(filter_expr: str | None) -> dict[str, Any] | None:
    if not filter_expr:
        return None
    m = _FILTER_RE.match(filter_expr.strip())
    if not m:
        raise ScimFilterError("Filtro no soportado. Solo se admite eq con comillas dobles.")
    attr = m.group(1).replace(".", "").lower()
    if attr not in SUPPORTED_FILTER_ATTRS:
        raise ScimFilterError(f"Atributo de filtro no soportado: {m.group(1)}")
    value = m.group(2)
    if attr == "active":
        return {"active": value.lower() in ("true", "1", "yes")}
    if attr == "username":
        return {"userName": value}
    if attr == "externalid":
        return {"externalId": value}
    if attr == "displayname":
        return {"displayName": value}
    return None
