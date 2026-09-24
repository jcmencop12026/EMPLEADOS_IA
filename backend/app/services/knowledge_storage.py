"""Almacenamiento seguro de archivos de conocimiento."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.config import DATA_DIR

KNOWLEDGE_ROOT = DATA_DIR / "knowledge"
EVIDENCE_ROOT = DATA_DIR / "evidence"
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".txt": {"text/plain"},
    ".csv": {"text/csv", "application/csv", "text/plain"},
    ".json": {"application/json", "text/plain"},
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
}


def normalize_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^\w.\- áéíóúñÁÉÍÓÚÑ]", "_", base, flags=re.UNICODE).strip("._")
    return cleaned or "documento"


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("El formato del archivo no es compatible.")
    return ext


def build_storage_path(organization_id: str, document_id: str, extension: str) -> Path:
    safe_ext = extension if extension.startswith(".") else f".{extension}"
    folder = KNOWLEDGE_ROOT / organization_id / document_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"original{safe_ext}"


def read_bytes_from_root(storage_key: str, root: Path) -> bytes:
    path = (DATA_DIR / storage_key).resolve()
    resolved_root = root.resolve()
    if not str(path).startswith(str(resolved_root)):
        raise ValueError("Ruta de almacenamiento inválida.")
    if not path.is_file():
        raise FileNotFoundError("El documento no existe o no está disponible.")
    return path.read_bytes()


def save_bytes_to_root(
    root: Path,
    organization_id: str,
    document_id: str,
    extension: str,
    data: bytes,
    *,
    filename_stem: str = "original",
) -> str:
    if not data:
        raise ValueError("El archivo está vacío.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido.")
    safe_ext = extension if extension.startswith(".") else f".{extension}"
    folder = root / organization_id / document_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{filename_stem}{safe_ext}"
    path.write_bytes(data)
    return str(path.relative_to(DATA_DIR))


def save_bytes(organization_id: str, document_id: str, extension: str, data: bytes) -> str:
    if not data:
        raise ValueError("El archivo está vacío.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido.")
    path = build_storage_path(organization_id, document_id, extension)
    path.write_bytes(data)
    return str(path.relative_to(DATA_DIR))


def read_stored_file(storage_key: str) -> bytes:
    return read_bytes_from_root(storage_key, KNOWLEDGE_ROOT)


def save_evidence_bytes(organization_id: str, evidence_id: str, extension: str, data: bytes) -> str:
    """Persistencia de evidencias externas — misma política que conocimiento."""
    return save_bytes_to_root(EVIDENCE_ROOT, organization_id, evidence_id, extension, data)


def read_evidence_file(storage_key: str) -> bytes:
    return read_bytes_from_root(storage_key, EVIDENCE_ROOT)


def delete_stored_file(storage_key: str | None) -> None:
    if not storage_key:
        return
    path = (DATA_DIR / storage_key).resolve()
    root = KNOWLEDGE_ROOT.resolve()
    if str(path).startswith(str(root)) and path.is_file():
        path.unlink(missing_ok=True)
        parent = path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def new_document_id() -> str:
    return str(uuid.uuid4())
