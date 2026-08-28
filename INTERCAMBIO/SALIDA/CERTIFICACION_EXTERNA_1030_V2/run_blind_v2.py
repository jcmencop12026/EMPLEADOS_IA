#!/usr/bin/env python3
"""Certificación ciega V2 — ejecuta casos desde CASOS/*/entrada.json sin leer ORACULO_SELLADO."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent / "01_PAQUETE"
BRUTOS = Path(__file__).resolve().parent / "02_BRUTOS_ANTES_ORACULO"
CASES = (
    "V2-OP-A", "V2-OP-B", "V2-OP-C", "V2-OP-D", "V2-OP-E", "V2-OP-F",
    "V2-NS-1", "V2-NS-2", "V2-PX-1", "V2-PX-2", "V2-PX-3", "V2-PX-4",
)

sys.path.insert(0, str(ROOT / "backend"))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _fresh_db():
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import (
        automation_models, experience_models, finops_models, knowledge_models,
        models, notifications, opportunity_models, orchestration_models, salud_models,
    )  # noqa: F401
    from app.database import Base
    from app.seed import bootstrap
    from app.seed_orchestration import bootstrap_orchestration
    from app.models import Organization, User
    from app.security import hash_password

    db_file = tempfile.mktemp(suffix="_cert_v2.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    bootstrap(db)
    return db, Session, db_file


def _ensure_org(db, name: str) -> tuple[str, str]:
    from app.models import Organization, User
    from app.seed_orchestration import bootstrap_orchestration
    from app.security import hash_password

    org = db.query(Organization).filter(Organization.name == name).first()
    if not org:
        org = Organization(name=name, status="ACTIVE")
        db.add(org)
        db.flush()
        bootstrap_orchestration(db, org.id)
        user = User(
            username=f"admin-{name[:12].lower()}",
            email=f"{name[:8].lower()}@cert.v2",
            password_hash=hash_password("Admin2026*"),
            organization_id=org.id,
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user = db.query(User).filter(User.organization_id == org.id, User.role == "admin").first()
    db.commit()
    return org.id, user.id


def _dominio_map(d: str) -> str:
    return {
        "OPERACIONES": "operativo", "COMERCIAL": "comercial", "ABASTECIMIENTO": "administrativo",
        "FINANZAS": "financiero", "RIESGO": "comercial", "LOGISTICA": "administrativo",
        "MANUFACTURA": "administrativo", "CONTROL": "administrativo",
    }.get(d, d.lower())


def _opp_snapshot(db, opp_id: str) -> dict:
    from app.opportunity_models import Opportunity
    from app.services.proactive_service import get_full_trace, _parse_json

    opp = db.get(Opportunity, opp_id)
    if not opp:
        return {}
    return {
        "id": opp.id, "codigo": opp.codigo, "estado": opp.estado, "tipo": opp.tipo,
        "dominio": opp.dominio, "signal_id": opp.signal_id, "pertinencia": opp.pertinencia,
        "momento": opp.momento, "confianza": float(opp.confianza or 0),
        "prioridad_score": float(opp.prioridad_score or 0),
        "prioridad_componentes": _parse_json(opp.prioridad_componentes_json),
        "siguiente_accion": _parse_json(opp.siguiente_accion_json),
        "equipo": _parse_json(opp.equipo_json),
        "work_plan_id": opp.work_plan_id, "finops_reference": opp.finops_reference,
        "valor_potencial": float(opp.valor_potencial or 0),
        "valor_materializado": float(opp.valor_materializado or 0),
        "valor_potencial_certidumbre": opp.valor_potencial_certidumbre,
        "atribucion_nivel": opp.atribucion_nivel,
        "contexto": _parse_json(opp.contexto_json),
        "trazas": get_full_trace(db, opp.id, opp.organization_id),
    }


def _build_payload(entrada: dict) -> dict:
    senal = entrada.get("senal", {})
    ctx = entrada.get("contexto", {})
    cid = entrada["id"]
    metricas = dict(senal.get("metricas") or {})
    payload: dict = {
        "titulo": entrada.get("titulo"),
        "indicadores": metricas,
        "historico": {"registrado": True},
        "source_reference": f"cert-v2-{cid}",
    }

    if cid == "V2-OP-A":
        payload.update({
            "tipo_oportunidad": "OPERATIVA", "impacto_estimado": 6_000_000,
            "valor_potencial": 4_200_000, "urgencia": "ALTA", "riesgo": "MEDIO", "esfuerzo": "MEDIO",
            "sla_horas": 36,
        })
    elif cid == "V2-OP-B":
        payload.update({
            "tipo_oportunidad": "COMERCIAL", "impacto_estimado": 800_000,
            "valor_potencial": None, "urgencia": "MEDIA",
        })
        if ctx.get("evidencia_insuficiente") or not ctx.get("datos_financieros_suficientes"):
            payload["indicadores"] = metricas
            payload.pop("historico", None)
    elif cid == "V2-OP-C":
        payload.update({
            "tipo_oportunidad": "AHORRO", "impacto_estimado": 2_500_000,
            "valor_potencial": 1_800_000, "urgencia": "BAJA", "esfuerzo": "MEDIO",
        })
    elif cid == "V2-OP-E":
        payload.update({"tipo_oportunidad": "AHORRO", "impacto_estimado": None, "valor_potencial": None})
        payload.pop("historico", None)
        payload["indicadores"] = metricas
    elif cid == "V2-OP-F":
        evs = senal.get("evidencias", [])
        payload.update({
            "tipo_oportunidad": "RIESGO", "impacto_estimado": 3_000_000,
            "valor_potencial": 2_000_000, "indicadores": {"valor_principal": 0.86, "tasa_conversion": 0.86},
            "conocimiento_autorizado": {"valor": 0.12, "fuente": evs[1]["fuente"] if len(evs) > 1 else "B"},
        })
    elif cid == "V2-NS-1":
        payload.update({
            "tipo_oportunidad": "AUTOMATIZACION", "impacto_estimado": 2_200_000,
            "valor_potencial": 1_500_000, "urgencia": "MEDIA",
        })
    elif cid == "V2-NS-2":
        payload.update({
            "tipo_oportunidad": "PRODUCTIVIDAD", "impacto_estimado": 1_800_000,
            "valor_potencial": 1_200_000,
        })
        if not ctx.get("datos_financieros_suficientes"):
            payload.pop("historico", None)
    return payload


def _run_pipeline(db, org_id: str, user_id: str, entrada: dict, *, source_ref: str | None = None, evento: str | None = None):
    from app.services import proactive_service as svc

    senal = entrada.get("senal", {})
    payload = _build_payload(entrada)
    if source_ref:
        payload["source_reference"] = source_ref
    ev = evento or senal.get("evento", entrada["id"])
    return svc.run_proactive_pipeline(
        db, organization_id=org_id,
        tipo=payload.get("tipo_oportunidad", "OPERATIVA").lower(),
        dominio=_dominio_map(entrada.get("dominio", "operativo")),
        evento=ev, payload=payload, origen=senal.get("fuente", "cert_v2"), user_id=user_id,
    )


def run_case(db, entrada: dict, state: dict) -> dict:
    from app.finops_models import FinOpsValueRecord
    from app.opportunity_models import Opportunity, ProactiveSignal
    from app.services import proactive_service as svc

    cid = entrada["id"]
    org_id, user_id = _ensure_org(db, entrada.get("tenant", "DEFAULT_V2"))
    result: dict = {"caso": cid, "timestamp": _utcnow(), "entrada": entrada, "tenant_id": org_id}

    if cid == "V2-OP-D":
        senal = entrada["senal"]
        runs = []
        for opt in senal.get("opciones", []):
            sub = {
                **entrada,
                "id": f"V2-OP-D-{opt['codigo']}",
                "titulo": f"Competencia {opt['codigo']}",
                "senal": {"fuente": senal["fuente"], "evento": f"competencia_{opt['codigo']}", "metricas": opt},
            }
            payload = {
                "titulo": sub["titulo"], "tipo_oportunidad": "OPERATIVA",
                "indicadores": opt, "historico": {"registrado": True},
                "impacto_estimado": opt["impacto"] * 100_000,
                "valor_potencial": opt["impacto"] * 80_000,
                "urgencia": "ALTA" if opt["urgencia"] >= 80 else "MEDIA",
                "esfuerzo": "ALTO" if opt["esfuerzo"] > 50 else "BAJO",
                "source_reference": f"cert-v2-D-{opt['codigo']}",
            }
            r = svc.run_proactive_pipeline(
                db, organization_id=org_id, tipo="operativa",
                dominio=_dominio_map(entrada["dominio"]),
                evento=f"competencia_{opt['codigo']}", payload=payload,
                origen=senal["fuente"], user_id=user_id,
            )
            db.commit()
            runs.append({"opcion": opt["codigo"], "pipeline": r, "oportunidad": _opp_snapshot(db, r["opportunity_id"])})
        ranking = svc.prioritize_opportunities_global(db, org_id)
        db.commit()
        result["opciones"] = runs
        result["priorizacion_global"] = ranking
        result["decision_final"] = ranking.get("por_que_primero")
        return result

    if cid == "V2-PX-1":
        ref = PKG / "CASOS" / "V2-OP-A" / "entrada.json"
        ref_entrada = json.loads(ref.read_text(encoding="utf-8"))
        clave = entrada.get("contexto", {}).get("misma_clave_idempotencia", "V2-IDEMP-A")
        reps = entrada.get("senal", {}).get("repeticiones", 2) + 1
        ejecuciones = []
        for i in range(reps):
            r = _run_pipeline(db, org_id, user_id, ref_entrada, source_ref=clave, evento="incremento_sostenido_demanda")
            db.commit()
            ejecuciones.append(r)
        signals = {e["signal_id"] for e in ejecuciones}
        opps = {e.get("opportunity_id") for e in ejecuciones if e.get("opportunity_id")}
        result["ejecuciones"] = ejecuciones
        result["signal_ids_unicos"] = len(signals)
        result["opportunity_ids_unicos"] = len(opps)
        result["idempotente"] = len(signals) == 1 and len(opps) <= 1
        return result

    if cid == "V2-PX-2":
        ref = json.loads((PKG / "CASOS" / "V2-OP-A" / "entrada.json").read_text(encoding="utf-8"))
        tenant_a = entrada["senal"]["tenant_origen"]
        tenant_b = entrada["senal"]["tenant_intruso"]
        org_a, user_a = _ensure_org(db, tenant_a)
        org_b, _ = _ensure_org(db, tenant_b)
        r = _run_pipeline(db, org_a, user_a, {**ref, "tenant": tenant_a})
        db.commit()
        opp_id = r["opportunity_id"]
        trace_b = svc.get_full_trace(db, opp_id, org_b)
        leak = db.query(Opportunity).filter(Opportunity.id == opp_id, Opportunity.organization_id == org_b).first()
        result["tenant_a_id"] = org_a
        result["tenant_b_id"] = org_b
        result["oportunidad_a_id"] = opp_id
        result["contaminacion_tenant_b"] = leak is not None
        result["trace_desde_tenant_b"] = trace_b
        result["fail_closed"] = not leak and (not trace_b.get("trazas"))
        return result

    if cid == "V2-PX-3":
        ref = json.loads((PKG / "CASOS" / "V2-OP-C" / "entrada.json").read_text(encoding="utf-8"))
        org_id, user_id = _ensure_org(db, entrada.get("tenant", ref["tenant"]))
        r = _run_pipeline(db, org_id, user_id, ref)
        db.commit()
        snap = _opp_snapshot(db, r["opportunity_id"])
        result["pipeline"] = r
        result["oportunidad"] = snap
        result["valor_potencial"] = snap.get("valor_potencial")
        result["valor_materializado"] = snap.get("valor_materializado")
        result["separados"] = snap.get("valor_potencial", 0) != snap.get("valor_materializado", 0)
        result["plan_no_ejecutado"] = snap.get("work_plan_id") is None
        return result

    if cid == "V2-PX-4":
        ref = json.loads((PKG / "CASOS" / "V2-NS-2" / "entrada.json").read_text(encoding="utf-8"))
        org_id, user_id = _ensure_org(db, entrada.get("tenant", ref["tenant"]))
        r = _run_pipeline(db, org_id, user_id, ref)
        db.commit()
        opp_id = r["opportunity_id"]
        opp = db.get(Opportunity, opp_id)
        if opp and opp.estado in ("PRIORIZADA", "PENDIENTE_APROBACION"):
            svc.approve_opportunity(db, opp, user_id=user_id)
        if opp and opp.estado == "APROBADA":
            svc.activate_opportunity(db, opp, user_id=user_id)
        sim = entrada.get("contexto", {}).get("resultado_simulado", {})
        res = svc.register_result(db, opp, user_id=user_id, valor_real=500_000, evidencia=sim)
        db.commit()
        from app.experience_models import EmployeeExperienceRecord
        exp_count = db.query(EmployeeExperienceRecord).filter(
            EmployeeExperienceRecord.caso_origen_id == opp_id,
        ).count()
        trace = svc.get_full_trace(db, opp_id, org_id)
        result["pipeline"] = r
        result["resultado"] = res
        result["experiencias_registradas"] = exp_count
        result["trazabilidad"] = trace
        result["etapas"] = [t["etapa"] for t in trace.get("trazas", [])]
        return result

    # Casos estándar OP / NS
    r = _run_pipeline(db, org_id, user_id, entrada)
    db.commit()
    result["pipeline"] = r
    if r.get("opportunity_id"):
        snap = _opp_snapshot(db, r["opportunity_id"])
        result["oportunidad"] = snap
        opp = db.get(Opportunity, r["opportunity_id"])
        if opp and opp.estado == "PENDIENTE_APROBACION" and cid == "V2-OP-A":
            svc.approve_opportunity(db, opp, user_id=user_id)
            act = svc.activate_opportunity(db, opp, user_id=user_id)
            db.commit()
            result["aprobacion"] = True
            result["activacion"] = act
            finops = db.query(FinOpsValueRecord).filter(
                FinOpsValueRecord.opportunity_id == opp.id,
            ).all()
            result["finops"] = [{"id": f.id, "work_plan_id": f.work_plan_id, "opportunity_id": f.opportunity_id} for f in finops]
            snap2 = _opp_snapshot(db, opp.id)
            result["oportunidad_post_activacion"] = snap2
    state[cid] = result
    return result


def _save_bruto(case_id: str, data: dict) -> Path:
    BRUTOS.mkdir(parents=True, exist_ok=True)
    path = BRUTOS / f"{case_id}_ANTES_ORACULO.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _freeze_hashes(head: str) -> Path:
    rows = ["caso,archivo,tamano_bytes,sha256,fecha_hora_utc,head_git"]
    for p in sorted(BRUTOS.glob("*_ANTES_ORACULO.json")):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append(f"{p.stem.replace('_ANTES_ORACULO','')},{p.name},{p.stat().st_size},{h},{_utcnow()},{head}")
    out = BRUTOS / "CONGELADO_SHA256.csv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return out


def main() -> int:
    head = _git_head()
    db, _, db_file = _fresh_db()
    state: dict = {}
    saved: list[str] = []
    try:
        for case_id in CASES:
            entrada_path = PKG / "CASOS" / case_id / "entrada.json"
            entrada = json.loads(entrada_path.read_text(encoding="utf-8"))
            data = run_case(db, entrada, state)
            data["head_git"] = head
            data["oraculo_consultado"] = False
            saved.append(str(_save_bruto(case_id, data)))
        freeze = _freeze_hashes(head)
        summary = {
            "fase": "ciega_v2",
            "timestamp": _utcnow(),
            "head_git": head,
            "casos_ejecutados": list(CASES),
            "archivos": saved,
            "congelado": str(freeze),
            "oraculo_consultado": False,
            "db_temporal": db_file,
        }
        (Path(__file__).resolve().parent / "00_CONTROL" / "resumen_fase_ciega_v2.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
