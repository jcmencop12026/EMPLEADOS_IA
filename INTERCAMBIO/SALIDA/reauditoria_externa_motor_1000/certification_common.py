"""Utilidades compartidas — reauditoría externa MOTOR-ANALITICO-1000."""

from __future__ import annotations

import csv
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
ENTRADA = ROOT / "INTERCAMBIO" / "ENTRADA"
SALIDA = Path(__file__).resolve().parent
ZIP_NAME = "MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip"
CASES = ("CASO_A", "CASO_B", "CASO_C", "CASO_D", "CASO_E")
DOC_DIR_NAMES = ("documentos", "conocimiento", "docs", "autorizados", "documentacion")


def find_package_root() -> Path:
    unpacked = ENTRADA / ZIP_NAME.replace(".zip", "")
    if unpacked.is_dir() and (unpacked / "README_MAESTRO.md").exists():
        return unpacked
    zpath = ENTRADA / ZIP_NAME
    if zpath.is_file():
        tmp = Path(tempfile.mkdtemp(prefix="motor_cert_"))
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(tmp)
        for candidate in (tmp, tmp / ZIP_NAME.replace(".zip", "")):
            if (candidate / "README_MAESTRO.md").exists():
                return candidate
        return tmp
    raise FileNotFoundError(
        f"Paquete no encontrado. Coloque {ZIP_NAME} en {ENTRADA} o descomprima allí."
    )


def resolve_case_dir(pkg: Path, case: str) -> Path:
    for candidate in (pkg / "CASOS" / case, pkg / case):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Directorio de caso no encontrado: {case}")


def load_json_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    return [data]


def load_operational_datasets(case_dir: Path) -> dict[str, list[dict[str, Any]]]:
    datasets: dict[str, list[dict[str, Any]]] = {}
    datos = case_dir / "datos"
    if not datos.is_dir():
        datos = case_dir / "data"
    if datos.is_dir():
        for f in sorted(datos.iterdir()):
            if f.suffix.lower() == ".json":
                datasets[f.stem] = load_json_file(f)
            elif f.suffix.lower() == ".csv":
                with f.open(encoding="utf-8") as fh:
                    datasets[f.stem] = list(csv.DictReader(fh))
    for f in case_dir.glob("*.json"):
        if f.name != "resultado_esperado.json":
            datasets[f.stem] = load_json_file(f)
    return datasets


def iter_case_documents(case_dir: Path) -> list[Path]:
    files: list[Path] = []
    for dirname in DOC_DIR_NAMES:
        doc_dir = case_dir / dirname
        if not doc_dir.is_dir():
            continue
        for f in sorted(doc_dir.rglob("*")):
            if f.is_file() and f.suffix.lower() in {".txt", ".md", ".text"}:
                files.append(f)
    return files


def load_case_documents(db, organization_id: str, user_id: str, case_dir: Path) -> list[str]:
    """Carga documentos del caso al Centro de Conocimiento y otorga grants."""
    from app.orchestration_models import AIEmployee
    from app.services.knowledge_service import create_text_document, grant_document_to_employee

    doc_ids: list[str] = []
    employees = (
        db.query(AIEmployee)
        .filter(AIEmployee.organization_id == organization_id, AIEmployee.is_active.is_(True))
        .all()
    )
    if not employees:
        return doc_ids

    grant_codes = ("radicacion", "contrato", "glosa", "cartera", "estrateg", "consolid")
    grant_targets = [e for e in employees if any(c in (e.code or "").lower() for c in grant_codes)]
    if not grant_targets:
        grant_targets = employees[:3]

    for doc_path in iter_case_documents(case_dir):
        content = doc_path.read_text(encoding="utf-8")
        meta_path = doc_path.with_suffix(".metadata.json")
        metadata = {"tipo": "contrato", "area": "radicacion"}
        if meta_path.is_file():
            metadata.update(json.loads(meta_path.read_text(encoding="utf-8")))
        doc = create_text_document(
            db,
            organization_id=organization_id,
            user_id=user_id,
            name=doc_path.stem,
            content=content,
            metadata=metadata,
        )
        doc_ids.append(doc["id"])
        for emp in grant_targets:
            grant_document_to_employee(
                db,
                organization_id=organization_id,
                employee_id=emp.id,
                document_id=doc["id"],
                user_id=user_id,
            )
    return doc_ids


def bruto_summary(blind: dict[str, Any]) -> dict[str, Any]:
    ranking = blind.get("priorizacion", {}).get("ranking", [])
    top = ranking[0] if ranking else {}
    hyp = blind.get("hipotesis_principal") or {}
    hallazgos = blind.get("hallazgos") or []
    main_finding = hallazgos[0] if hallazgos else {}
    finops_vals = [
        f.get("beneficio_esperado")
        for f in blind.get("finops", [])
        if isinstance(f.get("beneficio_esperado"), (int, float))
    ]
    return {
        "caso": blind.get("caso"),
        "suficiencia": blind.get("suficiencia"),
        "especialista_lider": blind.get("especialista_lider"),
        "hallazgo_principal": main_finding.get("titulo"),
        "hipotesis_principal": f"{hyp.get('id', '')} — {hyp.get('titulo', '')}".strip(" —"),
        "confianza": hyp.get("confianza"),
        "accion_1": blind.get("accion_1") or top.get("titulo"),
        "valor": max(finops_vals) if finops_vals else None,
        "datos_faltantes": blind.get("informacion_faltante") or [],
    }
