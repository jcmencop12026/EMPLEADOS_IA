"""Parser XML seguro — protección XXE (1370)."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET


class XmlSecurityError(ValueError):
    pass


_DOCTYPE_RE = re.compile(r"<!DOCTYPE", re.IGNORECASE)
_ENTITY_RE = re.compile(r"<!ENTITY", re.IGNORECASE)


def safe_parse_xml(content: bytes | str) -> ET.Element:
  """Parsea XML sin resolver entidades externas ni DOCTYPE."""
  if isinstance(content, str):
    data = content.encode("utf-8")
  else:
    data = content
  text = data.decode("utf-8", errors="replace")
  if _DOCTYPE_RE.search(text) or _ENTITY_RE.search(text):
    raise XmlSecurityError("XML con DOCTYPE o entidades no permitido")
  try:
    return ET.fromstring(data)
  except ET.ParseError as exc:
    raise XmlSecurityError("XML mal formado") from exc
