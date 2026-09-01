"""Generación PDF ejecutivo — presentación EIAAX sin dependencias externas."""

from __future__ import annotations

from typing import Any


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_lines(text: str, max_chars: int = 90) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        add = len(word) + (1 if current else 0)
        if length + add > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += add
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def render_presentacion_pdf(data: dict[str, Any]) -> bytes:
    """PDF mínimo válido (texto) derivado de la misma estructura que la vista."""
    lines: list[tuple[str, int]] = []
    y = 800
    size_title = 16
    size_body = 11
    size_small = 9

    def add(text: str, size: int = size_body, gap: int = 18) -> None:
        nonlocal y
        for part in _wrap_lines(text, 85):
            lines.append((part, size))
            y -= gap
        y -= 4

    add("EIAAX — Presentación ejecutiva", size_title, 22)
    add(f"Empresa: {data.get('empresa', '—')}", size_body)
    add(f"Expediente: {data.get('expediente_codigo', '—')}", size_body)
    add(f"Fecha: {data.get('fecha', '—')} · Versión: {data.get('version', 1)}", size_body)
    add(f"Audiencia: {data.get('audiencia', '—')}", size_body)
    if data.get("es_demo"):
        add("DEMO — DATOS SIMULADOS", size_body)
    add("", size_body, 8)

    for sec in data.get("secciones", []):
        add(sec.get("titulo", "Sección"), size_title, 20)
        for item in sec.get("contenido", []):
            add(f"• {item}", size_body)
        add("", size_body, 6)

    indicadores = data.get("indicadores") or []
    if indicadores:
        add("Indicadores", size_title, 20)
        for ind in indicadores[:8]:
            sim = " [SIMULADO]" if data.get("es_demo") else ""
            add(
                f"{ind.get('nombre')}: ANTES {ind.get('antes')} | PROY. {ind.get('proyectado')} "
                f"| REAL {ind.get('real', '—')} {ind.get('unidad', '')}{sim}",
                size_body,
            )

    add("", size_body, 6)
    add(
        "Documento ejecutivo — sin prompts, reglas internas, costos internos ni lógica propietaria.",
        size_small,
        14,
    )

    content_lines = ["BT"]
    y_pos = 800
    for text, size in lines:
        content_lines.append(f"/F1 {size} Tf")
        content_lines.append(f"50 {y_pos} Td")
        content_lines.append(f"({_escape_pdf_text(text)}) Tj")
        content_lines.append("0 -18 Td")
        y_pos -= 18
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode()
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return bytes(pdf)
