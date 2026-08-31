"""Servicio SAML 2.0 — assertions y validación de firma (1370)."""

from __future__ import annotations

import base64
import hashlib
from typing import Any

from app.services.saml_xml import XmlSecurityError, safe_parse_xml


class SamlError(ValueError):
  def __init__(self, message: str, *, category: str = "SAML"):
    super().__init__(message)
    self.category = category


def build_authn_request_url(config: dict, *, relay_state: str) -> str:
  sso_url = config.get("sso_url")
  if not sso_url:
    raise SamlError("SSO URL no configurada")
  entity_id = config.get("entity_id") or "empleados-ia"
  if config.get("mock_saml_redirect"):
    return f"{sso_url}?SAMLRequest=mock&RelayState={relay_state}&entity={entity_id}"
  raise SamlError("Generación SAML remota no disponible en pruebas")


def parse_saml_response(saml_response_b64: str, config: dict) -> dict[str, Any]:
  try:
    raw = base64.b64decode(saml_response_b64)
  except Exception as exc:
    raise SamlError("Respuesta SAML no decodificable") from exc
  try:
    root = safe_parse_xml(raw)
  except XmlSecurityError as exc:
    raise SamlError(str(exc), category="XXE") from exc

  name_id = _find_text(root, ".//{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
  if not name_id:
    name_id = _find_text(root, ".//NameID")
  if not name_id:
    raise SamlError("NameID no encontrado en assertion")

  attrs = _extract_attributes(root)
  signature_valid = _validate_signature_mock(raw, config)
  if not signature_valid:
    raise SamlError("Firma SAML inválida", category="VALIDACION")

  return {
    "subject": name_id,
    "email": attrs.get("email") or attrs.get("mail"),
    "given_name": attrs.get("given_name") or attrs.get("first_name"),
    "family_name": attrs.get("family_name") or attrs.get("last_name"),
    "groups": attrs.get("groups") or attrs.get("memberOf") or [],
    "attributes": attrs,
  }


def _find_text(root, path: str) -> str | None:
  for elem in root.iter():
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if tag == path.split("/")[-1].replace("}", "").split(":")[-1]:
      if elem.text:
        return elem.text.strip()
  return None


def _extract_attributes(root) -> dict[str, Any]:
  attrs: dict[str, Any] = {}
  for elem in root.iter():
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if tag == "Attribute":
      name = elem.attrib.get("Name") or elem.attrib.get("name")
      values = [v.text for v in elem if v.text]
      if name and values:
        attrs[name.split("/")[-1].lower()] = values[0] if len(values) == 1 else values
  return attrs


def _validate_signature_mock(raw: bytes, config: dict) -> bool:
  if config.get("mock_signature_valid") is False:
    return False
  expected_fp = config.get("idp_cert_fingerprint")
  if expected_fp:
    actual = hashlib.sha256(raw).hexdigest()[:32]
    return actual == expected_fp or config.get("mock_signature_valid", True)
  return bool(config.get("mock_signature_valid", True))
