#!/usr/bin/env python3
"""Fases 2, 4, 5, 6 — comparación oráculo, anti-prefab, trazabilidad, tenant.

Requiere brutos congelados en brutos/CASO_*_antes_oraculo.json (Fase 1).

Uso:
  PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/run_post_blind_controls.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from certification_common import (
    CASES,
    ROOT,
    SALIDA,
    bruto_summary,
    find_package_root,
    load_case_documents,
    load_operational_datasets,
    resolve_case_dir,
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _contains(expected: Any, actual: Any) -> bool:
    e, a = _norm(expected), _norm(actual)
    if not e:
        return True
    return e in a or a in e


def _match_list(expected: Any, actual: list) -> bool:
    if not expected:
        return True
    if isinstance(expected, list):
        return any(_contains(item, " ".join(str(x) for x in actual)) for item in expected)
    return _contains(expected, " ".join(str(x) for x in actual))


def compare_case(blind: dict[str, Any], oracle: dict[str, Any]) -> dict[str, Any]:
    hyp = blind.get("hipotesis_principal") or {}
    hallazgos = blind.get("hallazgos") or []
    main_finding = hallazgos[0] if hallazgos else {}
    checks: dict[str, bool] = {}

    oracle_hyp = oracle.get("hipotesis_principal") or oracle.get("causa_principal") or {}
    if isinstance(oracle_hyp, str):
        checks["hipotesis"] = _contains(oracle_hyp, hyp.get("titulo")) or _contains(oracle_hyp, hyp.get("id"))
    else:
        checks["hipotesis"] = (
            _contains(oracle_hyp.get("id"), hyp.get("id"))
            or _contains(oracle_hyp.get("titulo"), hyp.get("titulo"))
            or _contains(oracle_hyp.get("dominio"), hyp.get("dominio"))
        )

    oracle_suf = oracle.get("suficiencia") or oracle.get("suficiencia_datos") or oracle.get("clasificacion_suficiencia")
    if isinstance(oracle_suf, dict):
        oracle_suf = oracle_suf.get("clasificacion")
    checks["suficiencia"] = _contains(oracle_suf, blind.get("suficiencia"))

    oracle_hall = oracle.get("hallazgo_principal") or oracle.get("hallazgo_clave")
    if isinstance(oracle_hall, dict):
        oracle_hall = oracle_hall.get("titulo")
    checks["hallazgo"] = _contains(oracle_hall, main_finding.get("titulo")) if oracle_hall else True

    oracle_conf = oracle.get("confianza") or (oracle_hyp.get("confianza") if isinstance(oracle_hyp, dict) else None)
    checks["confianza"] = _contains(oracle_conf, hyp.get("confianza")) if oracle_conf else True

    oracle_accion = oracle.get("accion_1") or oracle.get("accion_principal") or oracle.get("accion_recomendada")
    checks["accion"] = _contains(oracle_accion, blind.get("accion_1")) if oracle_accion else True

    oracle_faltante = oracle.get("informacion_faltante") or oracle.get("datos_faltantes")
    checks["datos_faltantes"] = _match_list(oracle_faltante, blind.get("informacion_faltante") or [])

    caso_e_insuf = _norm(blind.get("suficiencia")) == "insuficiente"
    if caso_e_insuf:
        checks["no_alucinacion_e"] = len(hallazgos) == 0 or all(
            h.get("tipo") != "HECHO" or h.get("estado") == "INSUFICIENTE" for h in hallazgos
        )
        checks["h0_e"] = hyp.get("id") == "H0"
        checks["sin_finops_e"] = len(blind.get("finops") or []) == 0

    passed = all(checks.values())
    return {
        "caso": blind.get("caso"),
        "checks": checks,
        "veredicto": "PASS" if passed else "FAIL",
        "resumen": bruto_summary(blind),
        "oracle_keys": list(oracle.keys()),
    }


def anti_prefab_check(brutos: list[dict[str, Any]], rules_path: Path | None) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.services.motor_analitico.pipeline import fingerprint_motor_result

    fingerprints = []
    for blind in brutos:
        diag = blind.get("diagnostico_completo") or blind
        motor = {
            "hipotesis_principal": blind.get("hipotesis_principal"),
            "priorizacion": blind.get("priorizacion"),
            "suficiencia_datos": {"clasificacion": blind.get("suficiencia")},
            "finops": blind.get("finops"),
        }
        fingerprints.append(fingerprint_motor_result(motor))

    hyp_ids = [f["hipotesis_principal_id"] for f in fingerprints if f.get("hipotesis_principal_id")]
    unique_hyp = len(set(hyp_ids))
    top_sets = [tuple(f["top_ranking_titulos"]) for f in fingerprints]
    unique_rankings = len(set(top_sets))

    min_unique_hyp = 3
    min_unique_rank = 2
    if rules_path and rules_path.is_file():
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        min_unique_hyp = rules.get("min_hipotesis_principales_distintas", min_unique_hyp)
        min_unique_rank = rules.get("min_rankings_distintos", min_unique_rank)

    passed = unique_hyp >= min_unique_hyp and unique_rankings >= min_unique_rank
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "hipotesis_principales": hyp_ids,
        "hipotesis_unicas": unique_hyp,
        "rankings_unicos": unique_rankings,
        "min_requerido": {"hipotesis": min_unique_hyp, "rankings": min_unique_rank},
    }


def traceability_check(blind: dict[str, Any]) -> dict[str, Any]:
    hallazgos = blind.get("hallazgos") or []
    hipotesis = blind.get("hipotesis") or []
    conocimiento = blind.get("conocimiento") or {}

    hallazgo_ok = all(
        h.get("indicator_code") or h.get("sources") or h.get("evidence") or h.get("tipo") == "INSUFICIENTE"
        for h in hallazgos
    ) if hallazgos else True

    hip_ok = all(
        h.get("evidencia_a_favor") is not None or h.get("estado") in ("NO DEMOSTRADA", "REFUTADA")
        for h in hipotesis
    ) if hipotesis else True

    doc_trace = True
    if conocimiento.get("utilizado"):
        fuentes = conocimiento.get("fuentes_consultadas") or conocimiento.get("fuentes") or []
        doc_trace = any(f.get("document_id") or f.get("titulo") for f in fuentes)

    passed = hallazgo_ok and hip_ok
    return {
        "caso": blind.get("caso"),
        "veredicto": "PASS" if passed else "FAIL",
        "hallazgos_trazables": hallazgo_ok,
        "hipotesis_trazables": hip_ok,
        "conocimiento_documentado": doc_trace,
    }


def tenant_isolation_check(pkg: Path) -> dict[str, Any]:
    """Caso A no debe leer documentos de tenant B (secreto cruzado)."""
    sys.path.insert(0, str(ROOT / "backend"))
    from app.database import Base
    from app.seed import bootstrap
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import models, salud_models, finops_models, orchestration_models, knowledge_models, notifications, automation_models  # noqa: F401
    from app.models import Organization, User
    from app.security import hash_password
    from app.services.knowledge_service import create_text_document, grant_document_to_employee
    from app.services.salud_engine import get_diagnostico, run_ips_analysis
    from app.orchestration_models import AIEmployee

    secret_b = f"TENANT_SECRET_B_{uuid.uuid4().hex[:8]}"
    case_a_dir = resolve_case_dir(pkg, "CASO_A")
    request_text = (case_a_dir / "solicitud_usuario.txt").read_text(encoding="utf-8").strip()
    datasets = load_operational_datasets(case_a_dir)

    db_file = tempfile.mktemp(suffix="_tenant_iso.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    bootstrap(db)

    org_a = db.query(Organization).filter(Organization.name.like("%Default%")).first()
    if not org_a:
        org_a = db.query(Organization).first()
    org_b = Organization(name=f"TenantB-{uuid.uuid4().hex[:6]}")
    db.add(org_b)
    db.flush()
    user_b = User(
        organization_id=org_b.id,
        username=f"tb-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Tb*12345"),
        role="admin",
        is_active=True,
    )
    db.add(user_b)
    db.commit()

    admin = db.query(User).filter(User.organization_id == org_a.id, User.username == "admin").first()
    emp_b = (
        db.query(AIEmployee)
        .filter(AIEmployee.organization_id == org_b.id)
        .first()
    )
    if not emp_b:
        emp_b = AIEmployee(
            organization_id=org_b.id,
            code="ips-radicacion-analyst-b",
            name="Radicación B",
            specialty="salud",
            lifecycle_status="ACTIVE",
            status="DISPONIBLE",
            is_active=True,
        )
        db.add(emp_b)
        db.flush()

    doc_b = create_text_document(
        db,
        organization_id=org_b.id,
        user_id=user_b.id,
        name="Contrato secreto B",
        content=f"Plazo máximo de radicación 12 días. {secret_b}",
        metadata={"tipo": "contrato", "area": "radicacion"},
    )
    grant_document_to_employee(
        db,
        organization_id=org_b.id,
        employee_id=emp_b.id,
        document_id=doc_b["id"],
        user_id=user_b.id,
    )

    load_case_documents(db, admin.organization_id, admin.id, case_a_dir)

    analysis = run_ips_analysis(
        db,
        organization_id=org_a.id,
        user_id=admin.id,
        ips_name="Cert Tenant A",
        request_text=request_text,
        inline_datasets=datasets,
    )
    diag = get_diagnostico(db, org_a.id, analysis.id)
    blob = json.dumps(diag, ensure_ascii=False)
    leak = secret_b in blob

    denied = get_diagnostico(db, org_b.id, analysis.id)
    cross_denied = denied is None

    db.close()
    passed = not leak and cross_denied
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "secreto_b_filtrado": leak,
        "acceso_cruzado_denegado": cross_denied,
    }


def main() -> int:
    try:
        pkg = find_package_root()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2

    brutos: list[dict[str, Any]] = []
    oracle_results = []
    trace_results = []

    for case in CASES:
        bruto_path = SALIDA / "brutos" / f"{case}_antes_oraculo.json"
        if not bruto_path.is_file():
            print(f"FALTA bruto: {bruto_path}", file=sys.stderr)
            return 3
        blind = json.loads(bruto_path.read_text(encoding="utf-8"))
        brutos.append(blind)

        oracle_path = resolve_case_dir(pkg, case) / "resultado_esperado.json"
        if oracle_path.is_file():
            oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
            oracle_results.append(compare_case(blind, oracle))
        else:
            oracle_results.append({"caso": case, "veredicto": "SKIP", "mensaje": "Oráculo ausente"})

        trace_results.append(traceability_check(blind))

    anti_prefab = anti_prefab_check(brutos, pkg / "ANTI_RESPUESTA_PREFABRICADA.json")
    tenant = tenant_isolation_check(pkg)

    matriz = [dict(**r.get("resumen", {}), veredicto=r.get("veredicto")) for r in oracle_results if r.get("resumen")]

    summary = {
        "fase": "POST_CIEGA",
        "comparacion_oraculo": oracle_results,
        "anti_prefabricado": anti_prefab,
        "trazabilidad": trace_results,
        "tenant_isolation": tenant,
        "matriz": matriz,
    }
    (SALIDA / "resumen_post_oraculo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    all_oracle_pass = all(r.get("veredicto") == "PASS" for r in oracle_results)
    all_trace_pass = all(r.get("veredicto") == "PASS" for r in trace_results)
    overall = all_oracle_pass and anti_prefab.get("veredicto") == "PASS" and tenant.get("veredicto") == "PASS" and all_trace_pass
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
