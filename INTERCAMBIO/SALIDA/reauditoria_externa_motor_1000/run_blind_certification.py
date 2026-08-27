#!/usr/bin/env python3
"""Fase 1 — ejecución CIEGA casos A-E (sin leer resultado_esperado.json).

Uso:
  PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/run_blind_certification.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from certification_common import (
    CASES,
    ROOT,
    SALIDA,
    find_package_root,
    load_case_documents,
    load_operational_datasets,
    resolve_case_dir,
)


def _extract_blind(case_dir: Path, case_id: str) -> dict:
    solicitud_path = case_dir / "solicitud_usuario.txt"
    if not solicitud_path.is_file():
        raise FileNotFoundError(f"Falta solicitud_usuario.txt en {case_dir}")
    request_text = solicitud_path.read_text(encoding="utf-8").strip()
    datasets = load_operational_datasets(case_dir)

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
    assert admin is not None

    docs_loaded = load_case_documents(db, admin.organization_id, admin.id, case_dir)

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
        "documentos_cargados": docs_loaded,
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


def main() -> int:
    try:
        pkg = find_package_root()
    except FileNotFoundError as exc:
        (SALIDA / "PAQUETE_NO_DISPONIBLE.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print(exc, file=sys.stderr)
        return 2

    blind_results = []
    for case in CASES:
        case_dir = resolve_case_dir(pkg, case)
        blind = _extract_blind(case_dir, case)
        out = SALIDA / "brutos" / f"{case}_antes_oraculo.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(blind, ensure_ascii=False, indent=2), encoding="utf-8")
        blind_results.append({"caso": case, "archivo": str(out), "suficiencia": blind.get("suficiencia")})
        print(f"OK {case} → {out.name} (suficiencia={blind.get('suficiencia')})")

    matriz_path = pkg / "MATRIZ_EVALUACION.csv"
    if matriz_path.is_file():
        (SALIDA / "MATRIZ_EVALUACION_COPIA.csv").write_text(matriz_path.read_text(encoding="utf-8"), encoding="utf-8")

    summary = {"paquete": str(pkg), "fase": "CIEGA", "casos": blind_results}
    (SALIDA / "resumen_fase_ciega.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
