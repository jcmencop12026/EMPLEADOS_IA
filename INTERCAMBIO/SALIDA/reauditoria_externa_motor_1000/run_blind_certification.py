#!/usr/bin/env python3
"""Reauditoría externa MOTOR-ANALITICO-1000 — ejecución ciega casos A-E.

Uso:
  PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/run_blind_certification.py

Requiere paquete en:
  INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip
  o directorio descomprimido:
  INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION/

PROHIBIDO pasar resultado_esperado.json al motor.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENTRADA = ROOT / "INTERCAMBIO" / "ENTRADA"
SALIDA = Path(__file__).resolve().parent
ZIP_NAME = "MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip"
CASES = ("CASO_A", "CASO_B", "CASO_C", "CASO_D", "CASO_E")


def _find_package_root() -> Path:
    unpacked = ENTRADA / ZIP_NAME.replace(".zip", "")
    if unpacked.is_dir() and (unpacked / "README_MAESTRO.md").exists():
        return unpacked
    zpath = ENTRADA / ZIP_NAME
    if zpath.is_file():
        tmp = Path(tempfile.mkdtemp(prefix="motor_cert_"))
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(tmp)
        root = tmp
        for candidate in (root, root / ZIP_NAME.replace(".zip", "")):
            if (candidate / "README_MAESTRO.md").exists():
                return candidate
        return root
    raise FileNotFoundError(
        f"Paquete no encontrado. Coloque {ZIP_NAME} en {ENTRADA} o descomprima allí."
    )


def _load_json_file(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    return [data]


def _load_operational_datasets(case_dir: Path) -> dict[str, list[dict]]:
    datasets: dict[str, list[dict]] = {}
    datos = case_dir / "datos"
    if not datos.is_dir():
        datos = case_dir / "data"
    if datos.is_dir():
        for f in sorted(datos.iterdir()):
            if f.suffix.lower() == ".json":
                datasets[f.stem] = _load_json_file(f)
            elif f.suffix.lower() == ".csv":
                import csv as csvmod
                with f.open(encoding="utf-8") as fh:
                    datasets[f.stem] = list(csvmod.DictReader(fh))
    for f in case_dir.glob("*.json"):
        if f.name != "resultado_esperado.json":
            datasets[f.stem] = _load_json_file(f)
    return datasets


def _extract_blind(case_dir: Path, case_id: str) -> dict:
    solicitud_path = case_dir / "solicitud_usuario.txt"
    if not solicitud_path.is_file():
        raise FileNotFoundError(f"Falta solicitud_usuario.txt en {case_dir}")
    request_text = solicitud_path.read_text(encoding="utf-8").strip()
    datasets = _load_operational_datasets(case_dir)

    sys.path.insert(0, str(ROOT / "backend"))
    from app.database import Base
    from app.seed import bootstrap
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import models, salud_models, finops_models, orchestration_models, knowledge_models, notifications, automation_models  # noqa: F401
    from app.models import User
    from app.services.salud_engine import get_diagnostico, run_ips_analysis

    db_file = tempfile.mktemp(suffix=f"_{case_id}.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    bootstrap(db)
    admin = db.query(User).filter(User.username == "admin").first()

  # TODO: cargar documentos permitidos del caso al Centro de Conocimiento (tenant admin)

    analysis = run_ips_analysis(
        db,
        organization_id=admin.organization_id,
        user_id=admin.id,
        ips_name=f"Cert {case_id}",
        request_text=request_text,
        inline_datasets=datasets,
    )
    diag = get_diagnostico(db, admin.organization_id, analysis.id)
    db.close()

    ranking = diag.get("priorizacion", {}).get("ranking", [])
    top = ranking[0] if ranking else {}
    hyp = diag.get("hipotesis_principal") or {}
    specialists = diag.get("especialistas", {}).get("asignaciones", [])
    leader = specialists[0] if specialists else {}

    return {
        "caso": case_id,
        "solicitud": request_text,
        "suficiencia": diag.get("suficiencia_datos", {}).get("clasificacion"),
        "informacion_faltante": diag.get("suficiencia_datos", {}).get("informacion_faltante_critica", []),
        "especialista_lider": leader.get("employee_name"),
        "razon_seleccion": (diag.get("trazabilidad", {}).get("motor", {}).get("especialistas") or [{}])[0].get("razon_seleccion"),
        "hallazgos": diag.get("hallazgos", []),
        "hipotesis": diag.get("hipotesis", []),
        "hipotesis_principal": hyp,
        "contrastes": diag.get("contrastes", []),
        "alternativas": diag.get("alternativas", []),
        "priorizacion": diag.get("priorizacion", {}),
        "accion_1": top.get("accion") or top.get("titulo"),
        "finops": diag.get("finops", []),
        "escenarios": diag.get("escenarios", {}),
        "recomendacion_consolidada": diag.get("recomendacion_consolidada", {}),
        "conocimiento": diag.get("conocimiento", {}),
        "diagnostico_completo": diag,
    }


def _compare_oracle(blind: dict, oracle_path: Path) -> dict:
    if not oracle_path.is_file():
        return {"disponible": False, "mensaje": "Oráculo no presente"}
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    return {
        "disponible": True,
        "oracle": oracle,
        "coincidencia_semantica": {
            "hipotesis_dominio": blind.get("hipotesis_principal", {}).get("dominio"),
            "oracle_causa": oracle.get("causa_principal") or oracle.get("hipotesis_principal"),
        },
    }


def main() -> int:
    try:
        pkg = _find_package_root()
    except FileNotFoundError as exc:
        (SALIDA / "PAQUETE_NO_DISPONIBLE.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print(exc, file=sys.stderr)
        return 2

    blind_results = []
    comparisons = []
    for case in CASES:
        case_dir = pkg / "CASOS" / case
        if not case_dir.is_dir():
            case_dir = pkg / case
        blind = _extract_blind(case_dir, case)
        out = SALIDA / "brutos" / f"{case}_antes_oraculo.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(blind, ensure_ascii=False, indent=2), encoding="utf-8")
        blind_results.append(blind)
        comparisons.append(_compare_oracle(blind, case_dir / "resultado_esperado.json"))

    matriz_path = pkg / "MATRIZ_EVALUACION.csv"
    if matriz_path.is_file():
        (SALIDA / "MATRIZ_EVALUACION_COPIA.csv").write_text(matriz_path.read_text(encoding="utf-8"), encoding="utf-8")

    summary = {
        "paquete": str(pkg),
        "casos_ejecutados": [b["caso"] for b in blind_results],
        "comparaciones": comparisons,
    }
    (SALIDA / "resumen_post_oraculo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
