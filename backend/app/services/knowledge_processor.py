"""Extracción de texto y fragmentación — CONOCIMIENTO-930."""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Contrato futuro OCR — no implementado en V1
OCR_SUPPORTED = False


def detect_file_type(filename: str | None, mime_type: str | None) -> str | None:
    if not filename:
        return None
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext or None


def extract_text_from_bytes(data: bytes, file_type: str | None, filename: str | None = None) -> str:
    ft = (file_type or "").lower()
    if ft in {"txt", "text"}:
        return _decode_text(data)
    if ft == "csv":
        return _extract_csv(data)
    if ft == "json":
        return _extract_json(data)
    if ft == "docx":
        return _extract_docx(data)
    if ft == "xlsx":
        return _extract_xlsx(data)
    if ft == "pdf":
        return _extract_pdf_basic(data)
    raise ValueError("El formato del archivo no es compatible.")


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = data.decode(encoding)
            if text.strip():
                return text
        except UnicodeDecodeError:
            continue
    raise ValueError("El archivo está vacío.")


def _extract_csv(data: bytes) -> str:
    text = _decode_text(data)
    reader = csv.reader(io.StringIO(text))
    rows = [" | ".join(cell.strip() for cell in row) for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        raise ValueError("El archivo está vacío.")
    return "\n".join(rows)


def _extract_json(data: bytes) -> str:
    text = _decode_text(data)
    payload = json.loads(text)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _extract_docx(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ValueError("El formato del archivo no es compatible.") from exc
    root = ET.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        if texts:
            paragraphs.append("".join(texts))
    content = "\n".join(paragraphs).strip()
    if not content:
        raise ValueError("El archivo está vacío.")
    return content


def _extract_xlsx(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            shared = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for item in shared_root.findall(".//m:si", ns):
                    texts = [t.text for t in item.findall(".//m:t", ns) if t.text]
                    shared.append("".join(texts))
            sheet_name = next((n for n in archive.namelist() if n.startswith("xl/worksheets/sheet")), None)
            if not sheet_name:
                raise ValueError("El archivo está vacío.")
            sheet_root = ET.fromstring(archive.read(sheet_name))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            rows = []
            for row in sheet_root.findall(".//m:row", ns):
                cells = []
                for cell in row.findall("m:c", ns):
                    value = cell.find("m:v", ns)
                    if value is None or value.text is None:
                        continue
                    if cell.attrib.get("t") == "s":
                        cells.append(shared[int(value.text)])
                    else:
                        cells.append(value.text)
                if cells:
                    rows.append(" | ".join(cells))
    except (KeyError, zipfile.BadZipFile, ValueError, IndexError) as exc:
        raise ValueError("El formato del archivo no es compatible.") from exc
    content = "\n".join(rows).strip()
    if not content:
        raise ValueError("El archivo está vacío.")
    return content


def _extract_pdf_basic(data: bytes) -> str:
    # V1 sin dependencia OCR/PDF: extracción heurística de streams de texto.
    raw = data.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^()\\]*(?:\\.[^()\\]*)*)\)", raw)
    text = "\n".join(chunk.replace("\\n", "\n").replace("\\r", "") for chunk in chunks if len(chunk.strip()) > 2)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 20:
        raise ValueError("No fue posible procesar el documento.")
    return text


def chunk_text(text: str, *, document_id: str, organization_id: str) -> list[dict]:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []
    chunks: list[dict] = []
    start = 0
    position = 0
    length = len(normalized)
    while start < length:
        end = min(start + CHUNK_SIZE, length)
        if end < length:
            break_at = normalized.rfind("\n\n", start, end)
            if break_at <= start:
                break_at = normalized.rfind(" ", start, end)
            if break_at > start:
                end = break_at
        content = normalized[start:end].strip()
        if content:
            chunks.append(
                {
                    "document_id": document_id,
                    "organization_id": organization_id,
                    "position": position,
                    "page_number": None,
                    "section": None,
                    "content": content,
                    "metadata_json": None,
                }
            )
            position += 1
        if end >= length:
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks
