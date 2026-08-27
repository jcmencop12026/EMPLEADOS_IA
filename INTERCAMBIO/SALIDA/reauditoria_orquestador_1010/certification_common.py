"""Utilidades — reauditoría externa ORQUESTADOR-EXPERIENCIA-1010."""

from __future__ import annotations

import json
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
ENTRADA = ROOT / "INTERCAMBIO" / "ENTRADA"
SALIDA = Path(__file__).resolve().parent
BRUTOS = SALIDA / "brutos"
ZIP_NAME = "ORQUESTADOR_EXPERIENCIA_1010_CERTIFICACION_V1.zip"
EMBEDDED = SALIDA / "paquete_embedded"
CASES = tuple(f"OX_{c}" for c in "ABCDEFGH")


def find_package_root() -> tuple[Path, str]:
    """Retorna (ruta_paquete, fuente)."""
    unpacked = ENTRADA / ZIP_NAME.replace(".zip", "")
    if unpacked.is_dir() and (unpacked / "MANIFIESTO.json").exists():
        return unpacked, "zip_descomprimido"
    zpath = ENTRADA / ZIP_NAME
    if zpath.is_file():
        tmp = Path(tempfile.mkdtemp(prefix="ox_cert_"))
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(tmp)
        for candidate in (tmp, tmp / ZIP_NAME.replace(".zip", "")):
            if (candidate / "MANIFIESTO.json").exists():
                return candidate, "zip"
        return tmp, "zip"
    if EMBEDDED.is_dir() and (EMBEDDED / "MANIFIESTO.json").exists():
        return EMBEDDED, "paquete_embedded_especificacion"
    raise FileNotFoundError(
        f"Paquete {ZIP_NAME} no encontrado en {ENTRADA}. "
        f"Usar paquete externo o sincronizar a INTERCAMBIO/ENTRADA/."
    )


def resolve_case_dir(pkg: Path, case: str) -> Path:
    for candidate in (pkg / "CASOS" / case, pkg / case):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Caso no encontrado: {case}")


def load_case_manifest(case_dir: Path) -> dict[str, Any]:
    manifest = case_dir / "manifest.json"
    if manifest.is_file():
        return json.loads(manifest.read_text(encoding="utf-8"))
    solicitud = (case_dir / "solicitud.txt").read_text(encoding="utf-8").strip()
    oracle_path = case_dir / "resultado_esperado.json"
    oracle = json.loads(oracle_path.read_text(encoding="utf-8")) if oracle_path.is_file() else {}
    setup_path = case_dir / "setup.json"
    setup = json.loads(setup_path.read_text(encoding="utf-8")) if setup_path.is_file() else {}
    return {"solicitud": solicitud, "setup": setup, "oracle": oracle}


def _employee_by_code(db, org_id: str, code: str):
    from app.orchestration_models import AIEmployee

    emp = db.query(AIEmployee).filter(
        AIEmployee.organization_id == org_id,
        AIEmployee.code == code,
    ).first()
    if not emp:
        raise ValueError(f"Empleado no encontrado: {code}")
    return emp


def seed_case_experiences(db, org_id: str, setup: dict[str, Any]) -> list[str]:
    from app.services.experience_core import actualizar_resultado_experiencia, crear_experiencia

    created_ids: list[str] = []
    for spec in setup.get("experiencias", []):
        emp = _employee_by_code(db, org_id, spec["employee_code"])
        count = int(spec.get("count", 1))
        for _ in range(count):
            rec = crear_experiencia(
                db,
                org_id,
                employee_id=emp.id,
                dominio=spec.get("dominio", "general"),
                tipo_problema=spec.get("tipo_problema", "general"),
                contexto=spec.get("contexto"),
                senales=spec.get("senales"),
            )
            estado = spec.get("estado", "INDETERMINADO")
            if estado != "INDETERMINADO":
                actualizar_resultado_experiencia(
                    db,
                    org_id,
                    rec.id,
                    resultado_real=spec.get("resultado_real", f"Resultado {estado}"),
                    estado=estado,
                    kpi_despues=spec.get("kpi_despues"),
                    condiciones_exito=spec.get("condiciones_exito"),
                    condiciones_fracaso=spec.get("condiciones_fracaso"),
                )
            created_ids.append(rec.id)
    return created_ids


def seed_finops(db, org_id: str, setup: dict[str, Any]) -> None:
    from app.orchestration_models import FinOpsRecord

    for spec in setup.get("finops", []):
        emp = _employee_by_code(db, org_id, spec["employee_code"])
        db.add(
            FinOpsRecord(
                organization_id=org_id,
                employee_id=emp.id,
                cost=float(spec.get("cost", 0.1)),
            )
        )


def seed_learning_experience(db, org_id: str, spec: dict[str, Any]) -> str:
    from app.services.experience_core import actualizar_resultado_experiencia, crear_experiencia

    emp = _employee_by_code(db, org_id, spec["employee_code"])
    rec = crear_experiencia(
        db,
        org_id,
        employee_id=emp.id,
        dominio=spec.get("dominio", "general"),
        tipo_problema=spec.get("tipo_problema", "general"),
    )
    actualizar_resultado_experiencia(
        db,
        org_id,
        rec.id,
        resultado_real=spec.get("resultado_real_inicial", "Éxito inicial"),
        estado=spec.get("estado_inicial", "EXITO"),
        kpi_despues=spec.get("kpi_inicial"),
    )
    return rec.id


def seed_feedback_experience(db, org_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    from app.services.experience_core import (
        actualizar_resultado_experiencia,
        calcular_peso_calidad,
        crear_experiencia,
        registrar_feedback_experiencia,
    )

    emp = _employee_by_code(db, org_id, spec["employee_code"])
    rec = crear_experiencia(
        db,
        org_id,
        employee_id=emp.id,
        dominio=spec.get("dominio", "general"),
        tipo_problema=spec.get("tipo_problema", "general"),
    )
    if spec.get("kpi_antes"):
        rec.kpi_antes_json = json.dumps(spec["kpi_antes"], ensure_ascii=False)
    actualizar_resultado_experiencia(
        db,
        org_id,
        rec.id,
        resultado_real=spec.get("resultado_real", "Resultado negativo"),
        estado=spec.get("estado_esperado", "FRACASO"),
        kpi_despues=spec.get("kpi_despues"),
    )
    registrar_feedback_experiencia(db, org_id, rec.id, spec.get("feedback", "CORRECTO"))
    calidad = calcular_peso_calidad(rec)
    return {
        "record_id": rec.id,
        "estado": rec.estado,
        "feedback_humano": rec.feedback_humano,
        "peso_calidad": calidad["peso"],
        "factores_calidad": calidad["factores"],
    }


def create_tenant(db, name: str) -> tuple[str, str]:
    from app.models import Organization, User
    from app.security import hash_password
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_salud import bootstrap_salud

    org = Organization(name=name)
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"admin-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("Test2026*"),
        role="admin",
    )
    db.add(user)
    db.flush()
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    db.flush()
    return org.id, user.id


def _candidatos_from_log(db, selection_log_id: str | None) -> list[dict[str, Any]]:
    if not selection_log_id:
        return []
    from app.experience_models import ExperienceSelectionLog

    log = db.query(ExperienceSelectionLog).filter_by(id=selection_log_id).first()
    if not log or not log.candidatos_json:
        return []
    return json.loads(log.candidatos_json)


def run_selection_blind(
    db,
    org_id: str,
    solicitud: str,
    available_data: list[str] | None,
    setup: dict[str, Any] | None = None,
    caso_id: str | None = None,
    *,
    skip_seed: bool = False,
) -> dict[str, Any]:
    from app.services.orchestrator_selection import select_team

    if setup and not skip_seed:
        seed_case_experiences(db, org_id, setup)
        seed_finops(db, org_id, setup)
        if setup.get("experiencia_aprendizaje"):
            setup["_learning_record_id"] = seed_learning_experience(
                db, org_id, setup["experiencia_aprendizaje"]
            )
        if setup.get("experiencia_feedback"):
            setup["_feedback_result"] = seed_feedback_experience(
                db, org_id, setup["experiencia_feedback"]
            )
        db.flush()

    plan = select_team(
        db,
        org_id,
        solicitud,
        available_data=available_data,
        persist_log=True,
        caso_origen_id=caso_id,
    )

    candidatos = _candidatos_from_log(db, plan.get("selection_log_id"))

    complementarios = [
        m for m in plan.get("equipo", []) if m.get("rol") == "ESPECIALISTA_COMPLEMENTARIO"
    ]
    lider = plan.get("lider") or {}
    validador = plan.get("validador")
    disidente = plan.get("disidente")

    exp_utilizadas: list[str] = []
    for a in plan.get("asignaciones", []):
        exp_utilizadas.extend(a.get("experiencia_consultada") or [])

    return {
        "caso": caso_id,
        "organization_id": org_id,
        "solicitud": solicitud,
        "available_data": available_data or [],
        "dominio_principal": plan.get("dominio_principal"),
        "tipo_problema": plan.get("tipo_problema"),
        "candidatos": candidatos[:15],
        "candidatos_evaluados": plan.get("candidatos_evaluados"),
        "lider": _member_summary(lider),
        "complementarios": [_member_summary(c) for c in complementarios],
        "validador": _member_summary(validador) if validador else None,
        "disidente": _member_summary(disidente) if disidente else None,
        "equipo": plan.get("equipo"),
        "experiencias_utilizadas": exp_utilizadas,
        "factores_pesos": plan.get("factores_pesos"),
        "razon_seleccion_global": plan.get("razon_seleccion_global"),
        "selection_log_id": plan.get("selection_log_id"),
        "asignaciones": plan.get("asignaciones"),
        "setup_meta": {
            k: v
            for k, v in (setup or {}).items()
            if not k.startswith("_") and k not in ("experiencias", "finops")
        },
    }


def ranking_from_candidatos(candidatos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(candidatos, key=lambda c: c.get("score", 0), reverse=True)
    return [
        {
            "employee_code": c.get("employee_code"),
            "employee_name": c.get("employee_name"),
            "score": c.get("score"),
            "factores": c.get("factores") or c.get("factors"),
        }
        for c in ordered[:8]
    ]


def _member_summary(m: dict | None) -> dict | None:
    if not m:
        return None
    return {
        "employee_id": m.get("employee_id"),
        "employee_code": m.get("employee_code"),
        "employee_name": m.get("employee_name"),
        "specialty": m.get("specialty"),
        "domain": m.get("domain"),
        "rol": m.get("rol"),
        "score": m.get("score"),
        "factores": m.get("factores") or m.get("factors"),
        "razon_seleccion": m.get("razon_seleccion") or m.get("razon_rol"),
        "finops": m.get("finops"),
        "experiencia_consultada": m.get("experiencia_consultada"),
    }


def bruto_summary(blind: dict[str, Any]) -> dict[str, Any]:
    lider = blind.get("lider") or {}
    factores = lider.get("factores") or {}
    return {
        "caso": blind.get("caso"),
        "problema": blind.get("tipo_problema") or blind.get("dominio_principal"),
        "lider": lider.get("employee_name"),
        "complementarios": [c.get("employee_name") for c in blind.get("complementarios", [])],
        "validador": (blind.get("validador") or {}).get("employee_name"),
        "disidente": (blind.get("disidente") or {}).get("employee_name"),
        "experiencia_utilizada": blind.get("experiencias_utilizadas"),
        "peso": factores.get("experiencia"),
        "costo": (lider.get("finops") or {}).get("costo_promedio"),
        "riesgo": factores.get("riesgo"),
        "razon": blind.get("razon_seleccion_global"),
        "organization_id": blind.get("organization_id"),
    }


def fresh_db_session(case_suffix: str):
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
        orchestration_models,
        salud_models,
    )  # noqa: F401
    from app.database import Base
    from app.seed import bootstrap

    db_file = tempfile.mktemp(suffix=f"_{case_suffix}.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    bootstrap(db)
    from app.models import User

    admin = db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    return db, admin.organization_id, db_file
