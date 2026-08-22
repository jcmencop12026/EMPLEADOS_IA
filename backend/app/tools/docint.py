"""DOCINT — análisis documental por reglas (sin IA)."""
from __future__ import annotations

import json
import re
from typing import Any


REQUIRED_FIELDS = ("tipo_documento", "numero_documento", "fecha", "contenido")
DOC_PATTERNS = {
    "cedula": re.compile(r"^\d{6,12}$"),
    "fecha": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
}


def analyze_documents(payload: dict[str, Any]) -> dict[str, Any]:
    documents = payload.get("documents") or payload.get("documentos") or []
    if isinstance(documents, str):
        try:
            documents = json.loads(documents)
        except json.JSONDecodeError:
            documents = [{"contenido": documents}]

    if not documents:
        return {
            "findings": [{"severity": "error", "code": "DOCINT_EMPTY", "message": "No se recibieron documentos para analizar."}],
            "confidence": 0.0,
            "evidence": [],
            "summary": "Sin documentos de entrada.",
        }

    findings: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    for idx, doc in enumerate(documents):
        if not isinstance(doc, dict):
            findings.append({
                "severity": "error",
                "code": "DOCINT_FORMAT",
                "message": f"Documento #{idx + 1} no es un objeto válido.",
            })
            continue

        doc_id = doc.get("id") or f"doc-{idx + 1}"
        missing = [f for f in REQUIRED_FIELDS if not doc.get(f)]
        if missing:
            findings.append({
                "severity": "error",
                "code": "DOCINT_MISSING_FIELDS",
                "message": f"Documento {doc_id}: faltan campos {', '.join(missing)}.",
                "document_id": doc_id,
            })

        numero = doc.get("numero_documento")
        if numero and not DOC_PATTERNS["cedula"].match(str(numero)):
            findings.append({
                "severity": "warning",
                "code": "DOCINT_INVALID_ID",
                "message": f"Documento {doc_id}: número de documento con formato inválido.",
                "document_id": doc_id,
            })

        fecha = doc.get("fecha")
        if fecha and not DOC_PATTERNS["fecha"].match(str(fecha)):
            findings.append({
                "severity": "warning",
                "code": "DOCINT_INVALID_DATE",
                "message": f"Documento {doc_id}: fecha con formato inválido (esperado YYYY-MM-DD).",
                "document_id": doc_id,
            })

        contenido = str(doc.get("contenido") or "")
        if len(contenido.strip()) < 10:
            findings.append({
                "severity": "warning",
                "code": "DOCINT_SHORT_CONTENT",
                "message": f"Documento {doc_id}: contenido demasiado corto o vacío.",
                "document_id": doc_id,
            })

        evidence.append({"document_id": doc_id, "fields_present": list(doc.keys()), "content_length": len(contenido)})

    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    confidence = max(0.0, 1.0 - (errors * 0.25) - (warnings * 0.1))

    if not findings:
        summary = f"Análisis DOCINT: {len(documents)} documento(s) sin problemas detectados."
    else:
        summary = f"Análisis DOCINT: {errors} error(es), {warnings} advertencia(s) en {len(documents)} documento(s)."

    return {
        "findings": findings,
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "summary": summary,
        "documents_analyzed": len(documents),
    }
