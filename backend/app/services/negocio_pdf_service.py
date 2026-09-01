"""Generación PDF formal de propuesta comercial — sin motor documental paralelo."""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import Organization, User
from app.negocio_labels import label_proposal_status
from app.negocio_models import NegocioProposalDocument, NegocioProposalVersion


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_lines(text: str, width: int = 90) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        trial = " ".join(current + [w])
        if len(trial) <= width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def build_proposal_pdf_bytes(payload: dict[str, Any]) -> bytes:
    """PDF mínimo profesional en español — texto estructurado, sin datos internos."""
    lines: list[str] = []
    lines.append("PROPUESTA COMERCIAL EIAAX")
    lines.append("")
    lines.append(f"Código: {payload.get('codigo', '—')}")
    lines.append(f"Título: {payload.get('titulo', '—')}")
    lines.append(f"Versión: {payload.get('version', '—')}")
    lines.append(f"Estado: {payload.get('estado_label', '—')}")
    lines.append(f"Organización: {payload.get('organizacion', '—')}")
    lines.append(f"Prospecto: {payload.get('prospecto', '—')}")
    lines.append("")
    sections = [
        ("Resumen ejecutivo", payload.get("resumen_ejecutivo")),
        ("Situación / necesidad", payload.get("situacion")),
        ("Hallazgos relevantes", payload.get("hallazgos")),
        ("Oportunidad", payload.get("oportunidad")),
        ("Solución propuesta", payload.get("solucion")),
        ("Alcance", payload.get("alcance")),
        ("Exclusiones", payload.get("exclusiones")),
        ("Perspectiva Gerencia", payload.get("perspectiva_gerencia")),
        ("Perspectiva Operaciones", payload.get("perspectiva_operaciones")),
        ("Perspectiva Sistemas", payload.get("perspectiva_sistemas")),
        ("Implementación", payload.get("implementacion")),
        ("Cronograma / hitos", payload.get("cronograma")),
        ("Indicadores", payload.get("indicadores")),
        ("Inversión autorizada", payload.get("inversion")),
        ("Modalidad comercial", payload.get("modalidad_comercial")),
        ("Consumo IA", payload.get("consumo_ia")),
        ("Soporte / SLA", payload.get("soporte_sla")),
        ("Supuestos", payload.get("supuestos")),
        ("Responsabilidades", payload.get("responsabilidades")),
        ("Próximos pasos", payload.get("proximos_pasos")),
    ]
    for title, content in sections:
        if content is None or content == "" or content == [] or content == {}:
            continue
        lines.append(f"--- {title} ---")
        if isinstance(content, (dict, list)):
            import json

            text = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            text = str(content)
        lines.extend(_wrap_lines(text))
        lines.append("")
    if payload.get("nota_potencial"):
        lines.append("Nota: " + str(payload["nota_potencial"]))
    body = "\n".join(lines)
    content_lines = []
    y = 800
    for line in body.split("\n"):
        content_lines.append(f"BT /F1 10 Tf 50 {y} Td ({_pdf_escape(line)}) Tj ET")
        y -= 14
        if y < 50:
            break
    stream = "\n".join(content_lines)
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(f"4 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode() + stream_bytes + b"\nendstream\nendobj\n")
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    pdf = io.BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(pdf.tell())
        pdf.write(obj)
    xref_pos = pdf.tell()
    pdf.write(f"xref\n0 {len(offsets)}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.write(f"{off:010d} 00000 n \n".encode())
    pdf.write(f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return pdf.getvalue()


def document_payload_from_cliente(
    doc: dict[str, Any],
    *,
    org_name: str,
    prospecto: str | None,
    perspectivas: dict[str, Any] | None,
) -> dict[str, Any]:
    pers = perspectivas or {}
    ger = pers.get("GERENCIA") or {}
    ops = pers.get("OPERACIONES") or {}
    sis = pers.get("SISTEMAS") or {}
    return {
        "codigo": doc.get("codigo"),
        "titulo": doc.get("titulo"),
        "version": doc.get("version"),
        "estado_label": label_proposal_status(doc.get("estado")),
        "organizacion": org_name,
        "prospecto": prospecto or "—",
        "resumen_ejecutivo": doc.get("resumen_ejecutivo"),
        "situacion": doc.get("situacion"),
        "hallazgos": doc.get("hallazgos"),
        "oportunidad": doc.get("oportunidad"),
        "solucion": doc.get("solucion"),
        "alcance": doc.get("alcance"),
        "exclusiones": doc.get("exclusiones"),
        "perspectiva_gerencia": ger,
        "perspectiva_operaciones": ops,
        "perspectiva_sistemas": sis,
        "implementacion": doc.get("implementacion"),
        "cronograma": doc.get("cronograma"),
        "indicadores": doc.get("indicadores"),
        "inversion": doc.get("inversion"),
        "modalidad_comercial": doc.get("modalidad_comercial"),
        "consumo_ia": doc.get("consumo_ia"),
        "soporte_sla": doc.get("soporte_sla"),
        "supuestos": doc.get("supuestos"),
        "responsabilidades": doc.get("responsabilidades"),
        "proximos_pasos": doc.get("proximos_pasos"),
        "nota_potencial": doc.get("nota_potencial"),
    }


def generate_and_store_pdf(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    version: NegocioProposalVersion,
    cliente_doc: dict[str, Any],
    *,
    prospecto: str | None = None,
    perspectivas: dict[str, Any] | None = None,
) -> NegocioProposalDocument:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    payload = document_payload_from_cliente(
        cliente_doc,
        org_name=org.name if org else org_id,
        prospecto=prospecto,
        perspectivas=perspectivas,
    )
    pdf_bytes = build_proposal_pdf_bytes(payload)
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    filename = f"{cliente_doc.get('codigo', proposal_id)}_v{version.version_number}.pdf"
    doc_row = NegocioProposalDocument(
        proposal_id=proposal_id,
        organization_id=org_id,
        version_id=version.id,
        version_number=version.version_number,
        filename=filename,
        content_sha256=sha,
        content_bytes=pdf_bytes,
        generated_by_id=user.id,
    )
    db.add(doc_row)
    db.flush()
    version.pdf_document_id = doc_row.id
    db.flush()
    return doc_row
