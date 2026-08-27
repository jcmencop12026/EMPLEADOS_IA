#!/usr/bin/env python3
"""Fase 1 — congelación CIEGA casos OX-A…OX-H (sin leer oráculo para corregir).

Uso:
  PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_orquestador_1010/run_blind_certification.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from certification_common import (
    BRUTOS,
    CASES,
    ROOT,
    SALIDA,
    find_package_root,
    fresh_db_session,
    load_case_manifest,
    ranking_from_candidatos,
    resolve_case_dir,
    run_selection_blind,
    seed_case_experiences,
    seed_finops,
)


def run_case_ox_h(pkg) -> dict:
    """OX-H: experiencia favorable en TENANT_B, selección en TENANT_A."""
    from certification_common import create_tenant, seed_learning_experience

    case_dir = resolve_case_dir(pkg, "OX_H")
    manifest = load_case_manifest(case_dir)
    setup = manifest["setup"]
    solicitud = manifest["solicitud"]
    available = setup.get("available_data")

    sys.path.insert(0, str(ROOT / "backend"))
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import (
        automation_models,
        experience_models,
        finops_models,
        knowledge_models,
        models,
        notifications,
        orchestration_models,
        salud_models,
    )  # noqa: F401
    from app.database import Base
    import tempfile

    db_file = tempfile.mktemp(suffix="_OX_H.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    org_a_id, _ = create_tenant(db, "TENANT_A")
    org_b_id, _ = create_tenant(db, "TENANT_B")
    db.commit()

    tb_spec = setup.get("tenant_b_experiencia", {})
    if tb_spec:
        seed_case_experiences(
            db,
            org_b_id,
            {
                "experiencias": [
                    {
                        **tb_spec,
                        "count": tb_spec.get("count", 1),
                    }
                ]
            },
        )
        db.commit()

    blind = run_selection_blind(
        db,
        org_a_id,
        solicitud,
        available,
        setup={k: v for k, v in setup.items() if k not in ("tenant_b_experiencia",)},
        caso_id="OX_H",
    )
    blind["tenant_a_id"] = org_a_id
    blind["tenant_b_id"] = org_b_id
    blind["tenant_b_seeded"] = bool(tb_spec)
    db.close()
    return blind


def run_standard_case(pkg, case: str) -> dict:
    case_dir = resolve_case_dir(pkg, case)
    manifest = load_case_manifest(case_dir)
    setup = manifest["setup"]
    solicitud = manifest["solicitud"]
    available = setup.get("available_data")

    db, org_id, _ = fresh_db_session(case)
    blind = run_selection_blind(db, org_id, solicitud, available, setup=setup, caso_id=case)

    if case == "OX_F" and setup.get("experiencia_aprendizaje"):
        blind["ranking_antes"] = ranking_from_candidatos(blind.get("candidatos", []))
        lider = blind.get("lider") or {}
        blind["peso_antes"] = (lider.get("factores") or {}).get("experiencia")
        blind["explicacion_antes"] = blind.get("razon_seleccion_global")

    if case == "OX_G" and setup.get("experiencia_feedback"):
        blind["feedback_control"] = setup.get("_feedback_result")

    db.close()
    return blind


def main() -> int:
    try:
        pkg, fuente = find_package_root()
    except FileNotFoundError as exc:
        (SALIDA / "PAQUETE_NO_DISPONIBLE.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print(exc, file=sys.stderr)
        return 2

    sys.path.insert(0, str(ROOT / "backend"))
    BRUTOS.mkdir(parents=True, exist_ok=True)

    blind_results = []
    for case in CASES:
        if case == "OX_H":
            blind = run_case_ox_h(pkg)
        else:
            blind = run_standard_case(pkg, case)

        out = BRUTOS / f"{case}_ANTES_ORACULO.json"
        out.write_text(json.dumps(blind, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        blind_results.append(
            {
                "caso": case,
                "archivo": str(out),
                "lider": (blind.get("lider") or {}).get("employee_name"),
                "dominio": blind.get("dominio_principal"),
            }
        )
        print(f"OK {case} → {out.name} líder={(blind.get('lider') or {}).get('employee_name')}")

    matriz_path = pkg / "MATRIZ_EVALUACION.csv"
    if matriz_path.is_file():
        (SALIDA / "MATRIZ_EVALUACION_COPIA.csv").write_text(
            matriz_path.read_text(encoding="utf-8"), encoding="utf-8"
        )

    summary = {"paquete": str(pkg), "fuente": fuente, "fase": "CIEGA", "casos": blind_results}
    (SALIDA / "resumen_fase_ciega.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
