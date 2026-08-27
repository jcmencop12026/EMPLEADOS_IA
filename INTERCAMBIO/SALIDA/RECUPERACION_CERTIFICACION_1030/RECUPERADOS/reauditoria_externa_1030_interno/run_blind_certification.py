#!/usr/bin/env python3
"""Fase ciega — casos OP-A…F, NS-1/2, PX-1…4 (sin consultar oráculo externo).

Uso:
  PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_externa_1030/run_blind_certification.py
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BRUTOS = Path(__file__).resolve().parent / "brutos"
BRUTOS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "backend"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _signal_payload(case: str) -> dict:
    cases = {
        "OP-A": {
            "titulo": "Recuperación financiera urgente",
            "tipo_oportunidad": "FINANCIERA",
            "indicadores": {"cartera_vencida": 45_000_000, "dias_mora": 90},
            "impacto_estimado": 12_000_000,
            "valor_potencial": 8_000_000,
            "urgencia": "CRITICA",
            "riesgo": "ALTO",
            "esfuerzo": "MEDIO",
            "source_reference": f"op-a-{uuid.uuid4().hex[:6]}",
        },
        "OP-B": {
            "titulo": "Automatización alto volumen bajo valor unitario",
            "tipo_oportunidad": "AUTOMATIZACION",
            "indicadores": {"volumen": 5000, "valor_unitario": 500},
            "impacto_estimado": 500_000,
            "valor_potencial": 400_000,
            "urgencia": "BAJA",
            "esfuerzo": "BAJO",
            "source_reference": f"op-b-{uuid.uuid4().hex[:6]}",
        },
        "OP-C": {
            "titulo": "Riesgo de cumplimiento regulatorio",
            "tipo_oportunidad": "CUMPLIMIENTO",
            "indicadores": {"incumplimientos": 3, "sla_horas": 24},
            "impacto_estimado": 20_000_000,
            "valor_potencial": 15_000_000,
            "urgencia": "ALTA",
            "riesgo": "CRITICO",
            "sla_horas": 36,
            "source_reference": f"op-c-{uuid.uuid4().hex[:6]}",
        },
        "OP-D": {
            "titulo": "Competencia por capacidad — recuperación cartera",
            "tipo_oportunidad": "FINANCIERA",
            "indicadores": {"cartera": 30_000_000},
            "impacto_estimado": 10_000_000,
            "valor_potencial": 7_000_000,
            "urgencia": "ALTA",
            "source_reference": f"op-d1-{uuid.uuid4().hex[:6]}",
        },
        "OP-D2": {
            "titulo": "Competencia por capacidad — automatización",
            "tipo_oportunidad": "AUTOMATIZACION",
            "indicadores": {"volumen": 800},
            "impacto_estimado": 9_000_000,
            "valor_potencial": 6_500_000,
            "urgencia": "ALTA",
            "source_reference": f"op-d2-{uuid.uuid4().hex[:6]}",
        },
        "OP-E": {
            "titulo": "Datos insuficientes para conclusión",
            "tipo_oportunidad": "OPERATIVA",
            "indicadores": {},
            "source_reference": f"op-e-{uuid.uuid4().hex[:6]}",
        },
        "OP-F": {
            "titulo": "Información contradictoria",
            "tipo_oportunidad": "COMERCIAL",
            "indicadores": {"tasa_conversion": 0.35, "valor_principal": 0.35},
            "conocimiento_autorizado": {"valor": 0.08, "fuente": "manual_comercial"},
            "impacto_estimado": 5_000_000,
            "valor_potencial": 3_000_000,
            "source_reference": f"op-f-{uuid.uuid4().hex[:6]}",
        },
        "NS-1": {
            "titulo": "Automatizar proceso administrativo repetitivo",
            "tipo_oportunidad": "AUTOMATIZACION",
            "indicadores": {"volumen_mensual": 450, "repeticiones": 30},
            "impacto_estimado": 2_500_000,
            "valor_potencial": 1_800_000,
            "source_reference": f"ns-1-{uuid.uuid4().hex[:6]}",
        },
        "NS-2": {
            "titulo": "Recuperar conversión comercial",
            "tipo_oportunidad": "COMERCIAL",
            "indicadores": {"tasa_conversion": 0.12, "capacidad_ociosa_pct": 35},
            "impacto_estimado": 8_000_000,
            "valor_potencial": 5_500_000,
            "urgencia": "ALTA",
            "tendencia": "EMPEORANDO",
            "source_reference": f"ns-2-{uuid.uuid4().hex[:6]}",
        },
    }
    return cases[case]


def _fresh_db():
    import tempfile
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import (
        automation_models,
        experience_models,
        finops_models,
        knowledge_models,
        models,
        notifications,
        opportunity_models,
        orchestration_models,
        salud_models,
    )  # noqa: F401
    from app.database import Base
    from app.models import Organization, User
    from app.security import hash_password

    db_file = tempfile.mktemp(suffix="_1030_blind.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    org = Organization(name="CertOrg", status="ACTIVE")
    db.add(org)
    db.flush()
    admin = User(
        username="admin",
        email="admin@cert.test",
        password_hash=hash_password("Admin2026*"),
        organization_id=org.id,
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return db, org.id, admin.id


def _run_case(db, org_id: str, user_id: str, case: str, dominio: str | None = None) -> dict:
    from app.opportunity_models import Opportunity
    from app.services import proactive_service as svc

    payload = _signal_payload(case)
    dom = dominio
    if dom is None:
        dom = {
            "NS-1": "administrativo",
            "NS-2": "comercial",
            "OP-F": "comercial",
            "OP-B": "administrativo",
        }.get(case, "financiero")
    result = svc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        tipo=payload.get("tipo_oportunidad", "OPERATIVA").lower(),
        dominio=dom,
        evento=f"certificacion_{case.lower()}",
        payload=payload,
        origen="blind_cert",
        user_id=user_id,
    )
    db.commit()
    opp = db.query(Opportunity).get(result["opportunity_id"])
    return {
        "caso": case,
        "timestamp": _utcnow_iso(),
        "pipeline": result,
        "oportunidad": {
            "id": opp.id,
            "codigo": opp.codigo,
            "estado": opp.estado,
            "dominio": opp.dominio,
            "tipo": opp.tipo,
            "pertinencia": opp.pertinencia,
            "momento": opp.momento,
            "prioridad_score": float(opp.prioridad_score or 0),
            "prioridad_componentes": json.loads(opp.prioridad_componentes_json or "{}"),
            "siguiente_accion": json.loads(opp.siguiente_accion_json or "{}"),
            "valor_potencial": float(opp.valor_potencial or 0),
            "valor_materializado": float(opp.valor_materializado or 0),
            "contexto": json.loads(opp.contexto_json or "{}"),
        },
    }


def _save(name: str, data: dict) -> Path:
    path = BRUTOS / f"{name}_ANTES_ORACULO.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_op_d(db, org_id: str, user_id: str) -> dict:
    from app.services import proactive_service as svc

    r1 = _run_case(db, org_id, user_id, "OP-D")
    r2 = _run_case(db, org_id, user_id, "OP-D2", dominio="administrativo")
    ranking = svc.prioritize_opportunities_global(db, org_id)
    db.commit()
    return {
        "caso": "OP-D",
        "timestamp": _utcnow_iso(),
        "oportunidades": [r1["oportunidad"], r2["oportunidad"]],
        "priorizacion_global": ranking,
    }


def run_px1(db, org_id: str) -> dict:
    from app.services import proactive_scheduler
    from app.services.proactive_scheduler import run_proactive_tick_once

    proactive_scheduler._synthetic_indicators = lambda _: [{
        "tipo": "px1_scheduler",
        "dominio": "administrativo",
        "evento": "px1_proactividad_real",
        "payload": _signal_payload("NS-1"),
    }]
    results = run_proactive_tick_once(db)
    db.commit()
    trace = None
    if results and results[0].get("opportunity_id"):
        from app.services import proactive_service as svc
        trace = svc.get_full_trace(db, results[0]["opportunity_id"], org_id)
    return {
        "caso": "PX-1",
        "timestamp": _utcnow_iso(),
        "sin_prompt_humano": True,
        "origen": "proactive_scheduler",
        "tick_results": results,
        "trazabilidad": trace,
    }


def run_px2(db, org_id: str, user_id: str) -> dict:
    from app.opportunity_models import Opportunity
    from app.services import proactive_service as svc

    payload = _signal_payload("NS-1")
    payload["source_reference"] = "px2-idempotencia-fixed"
    runs = []
    for i in range(3):
        r = svc.run_proactive_pipeline(
            db, organization_id=org_id, tipo="automatizacion", dominio="administrativo",
            evento="px2_idempotencia", payload=payload, origen="blind_cert", user_id=user_id,
        )
        db.commit()
        runs.append(r)
    opp_count = db.query(Opportunity).filter(
        Opportunity.organization_id == org_id,
        Opportunity.titulo.contains("administrativo"),
    ).count()
    return {
        "caso": "PX-2",
        "timestamp": _utcnow_iso(),
        "ejecuciones": runs,
        "signal_ids_unicos": len({r["signal_id"] for r in runs}),
        "oportunidades_activas_equivalentes": opp_count,
        "idempotente": runs[0]["signal_id"] == runs[1]["signal_id"] == runs[2]["signal_id"],
    }


def run_px3(db, org_id: str, user_id: str) -> dict:
    from app.opportunity_models import Opportunity
    from app.services import proactive_service as svc

    payload = _signal_payload("OP-A")
    payload["valor_potencial"] = 80_000_000
    payload["source_reference"] = f"px3-{uuid.uuid4().hex[:6]}"
    result = svc.run_proactive_pipeline(
        db, organization_id=org_id, tipo="financiera", dominio="financiero",
        evento="px3_valor", payload=payload, origen="blind_cert", user_id=user_id,
    )
    db.commit()
    opp = db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(db, opp, user_id=user_id)
    svc.activate_opportunity(db, opp, user_id=user_id)
    svc.register_result(db, opp, user_id=user_id, valor_real=31_000_000, evidencia={"kpi": "px3"})
    db.commit()
    return {
        "caso": "PX-3",
        "timestamp": _utcnow_iso(),
        "valor_potencial": float(opp.valor_potencial or 0),
        "valor_materializado": float(opp.valor_materializado or 0),
        "separados": float(opp.valor_potencial or 0) != float(opp.valor_materializado or 0),
        "oportunidad_id": opp.id,
    }


def run_px4(db) -> dict:
    from app.models import Organization, User
    from app.opportunity_models import Opportunity
    from app.security import hash_password
    from app.services import proactive_service as svc

    org_a = db.query(Organization).filter(Organization.name == "CertOrg").first()
    org_b = Organization(name=f"TenantB-{uuid.uuid4().hex[:6]}", status="ACTIVE")
    db.add(org_b)
    db.flush()
    user_b = User(
        username=f"adminb-{uuid.uuid4().hex[:6]}",
        email=f"b-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        organization_id=org_b.id,
        role="admin",
        is_active=True,
    )
    db.add(user_b)
    db.commit()

    opp_b = svc.run_proactive_pipeline(
        db, organization_id=org_b.id, tipo="comercial", dominio="comercial",
        evento="px4_tenant_b", payload={"titulo": "B-only", "indicadores": {"x": 1},
                                         "source_reference": "px4-b-only", "tipo_oportunidad": "COMERCIAL",
                                         "impacto_estimado": 1_000_000},
        user_id=user_b.id,
    )
    db.commit()
    leak = db.query(Opportunity).filter(
        Opportunity.id == opp_b["opportunity_id"],
        Opportunity.organization_id == org_a.id,
    ).first()
    cross = svc.get_full_trace(db, opp_b["opportunity_id"], org_a.id)
    return {
        "caso": "PX-4",
        "timestamp": _utcnow_iso(),
        "tenant_a_id": org_a.id,
        "tenant_b_id": org_b.id,
        "oportunidad_b_id": opp_b["opportunity_id"],
        "contaminacion_tenant_a": leak is not None,
        "trace_desde_tenant_a": cross,
        "fail_closed": cross.get("error") is not None or len(cross.get("trazas", [])) == 0,
    }


def main() -> int:
    db, org_id, user_id = _fresh_db()
    saved: list[str] = []
    try:
        for case in ("OP-A", "OP-B", "OP-C", "OP-E", "OP-F", "NS-1", "NS-2"):
            data = _run_case(db, org_id, user_id, case)
            saved.append(str(_save(case, data)))

        saved.append(str(_save("OP-D", run_op_d(db, org_id, user_id))))

        for name, runner in (
            ("PX-1", lambda: run_px1(db, org_id)),
            ("PX-2", lambda: run_px2(db, org_id, user_id)),
            ("PX-3", lambda: run_px3(db, org_id, user_id)),
            ("PX-4", lambda: run_px4(db)),
        ):
            saved.append(str(_save(name, runner())))

        resumen = {
            "fase": "ciega",
            "timestamp": _utcnow_iso(),
            "paquete_externo": "NO_DISPONIBLE",
            "casos_ejecutados": ["OP-A", "OP-B", "OP-C", "OP-D", "OP-E", "OP-F", "NS-1", "NS-2",
                                 "PX-1", "PX-2", "PX-3", "PX-4"],
            "archivos": saved,
            "nota": "Resultados congelados antes de consultar oráculo externo.",
        }
        summary_path = Path(__file__).resolve().parent / "resumen_fase_ciega.json"
        summary_path.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
