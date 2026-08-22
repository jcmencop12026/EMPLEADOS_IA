"""RIPS — validación estructural por reglas (sin IA)."""
from __future__ import annotations

import json
from typing import Any

RIPS_REQUIRED_SECTIONS = ("usuarios", "consultas", "procedimientos", "medicamentos", "otrosServicios")
RIPS_USER_FIELDS = ("tipoDocumentoIdentificacion", "numDocumentoIdentificacion", "codSexo", "fechaNacimiento")


def _validate_user(user: dict[str, Any], idx: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    uid = user.get("numDocumentoIdentificacion") or f"usuario-{idx + 1}"
    missing = [f for f in RIPS_USER_FIELDS if not user.get(f)]
    if missing:
        findings.append({
            "severity": "error",
            "code": "RIPS_USER_MISSING",
            "message": f"Usuario {uid}: faltan campos obligatorios {', '.join(missing)}.",
            "entity": "usuario",
            "entity_id": uid,
        })
    sexo = user.get("codSexo")
    if sexo and str(sexo) not in ("M", "F", "I"):
        findings.append({
            "severity": "error",
            "code": "RIPS_INVALID_SEX",
            "message": f"Usuario {uid}: codSexo inválido ({sexo}).",
            "entity": "usuario",
            "entity_id": uid,
        })
    return findings


def _validate_consultas(consultas: list[Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, c in enumerate(consultas):
        if not isinstance(c, dict):
            findings.append({"severity": "error", "code": "RIPS_CONSULTA_FORMAT", "message": f"Consulta #{idx + 1} inválida."})
            continue
        if not c.get("codConsulta"):
            findings.append({
                "severity": "error",
                "code": "RIPS_CONSULTA_CODE",
                "message": f"Consulta #{idx + 1}: falta codConsulta (CUPS).",
                "entity": "consulta",
            })
        if not c.get("numDocumentoIdentificacion"):
            findings.append({
                "severity": "error",
                "code": "RIPS_CONSULTA_USER",
                "message": f"Consulta #{idx + 1}: sin paciente asociado.",
                "entity": "consulta",
            })
    return findings


def analyze_rips(payload: dict[str, Any]) -> dict[str, Any]:
    rips_data = payload.get("rips") or payload.get("data") or payload
    if isinstance(rips_data, str):
        try:
            rips_data = json.loads(rips_data)
        except json.JSONDecodeError as exc:
            return {
                "findings": [{"severity": "error", "code": "RIPS_PARSE", "message": f"JSON RIPS inválido: {exc}"}],
                "confidence": 0.0,
                "evidence": [],
                "summary": "Error al parsear RIPS.",
            }

    if not isinstance(rips_data, dict):
        return {
            "findings": [{"severity": "error", "code": "RIPS_FORMAT", "message": "Estructura RIPS debe ser un objeto JSON."}],
            "confidence": 0.0,
            "evidence": [],
            "summary": "Formato RIPS inválido.",
        }

    findings: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = {}

    for section in RIPS_REQUIRED_SECTIONS:
        if section not in rips_data:
            findings.append({
                "severity": "warning",
                "code": "RIPS_SECTION_MISSING",
                "message": f"Sección '{section}' ausente en el archivo RIPS.",
                "section": section,
            })
            rips_data.setdefault(section, [])

    usuarios = rips_data.get("usuarios") or []
    if not usuarios:
        findings.append({"severity": "error", "code": "RIPS_NO_USERS", "message": "RIPS sin usuarios registrados."})
    for idx, user in enumerate(usuarios):
        if isinstance(user, dict):
            findings.extend(_validate_user(user, idx))

    consultas = rips_data.get("consultas") or []
    findings.extend(_validate_consultas(consultas))

    user_docs = {str(u.get("numDocumentoIdentificacion")) for u in usuarios if isinstance(u, dict) and u.get("numDocumentoIdentificacion")}
    for idx, c in enumerate(consultas):
        if isinstance(c, dict):
            doc = str(c.get("numDocumentoIdentificacion") or "")
            if doc and doc not in user_docs:
                findings.append({
                    "severity": "error",
                    "code": "RIPS_ORPHAN_CONSULTA",
                    "message": f"Consulta #{idx + 1}: paciente {doc} no existe en usuarios.",
                    "entity": "consulta",
                })

    evidence = {
        "sections": {s: len(rips_data.get(s) or []) for s in RIPS_REQUIRED_SECTIONS},
        "total_findings": len(findings),
    }

    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    confidence = max(0.0, 1.0 - (errors * 0.2) - (warnings * 0.08))

    if not findings:
        summary = "Validación RIPS: estructura conforme, sin hallazgos."
    else:
        summary = f"Validación RIPS: {errors} error(es), {warnings} advertencia(s)."

    return {
        "findings": findings,
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "summary": summary,
    }
