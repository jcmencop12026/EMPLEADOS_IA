"""Experiencia transversal del core — calidad, similitud, feedback y resultados."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.experience_models import EmployeeExperienceRecord

ESTADOS_VALIDOS = frozenset({"EXITO", "PARCIAL", "FRACASO", "INDETERMINADO"})
FEEDBACK_POSITIVO = frozenset({"CORRECTO", "UTIL", "ACCION_ACEPTADA", "PARCIALMENTE_CORRECTO"})
FEEDBACK_NEGATIVO = frozenset({"INCORRECTO", "NO_UTIL", "ACCION_DESCARTADA", "REQUIERE_REVISION"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def calcular_peso_calidad(record: EmployeeExperienceRecord | dict[str, Any]) -> dict[str, Any]:
    """Peso explicable de una experiencia — no nota opaca."""
    if isinstance(record, EmployeeExperienceRecord):
        data = {
            "estado": record.estado,
            "resultado_real": record.resultado_real,
            "feedback_humano": record.feedback_humano,
            "confianza": record.confianza or 0.5,
            "valor_esperado": record.valor_esperado,
            "valor_obtenido": record.valor_obtenido,
            "kpi_antes_json": record.kpi_antes_json,
            "kpi_despues_json": record.kpi_despues_json,
            "condiciones_exito_json": record.condiciones_exito_json,
            "created_at": record.created_at,
            "resultado_actualizado_at": record.resultado_actualizado_at,
        }
    else:
        data = record

    factores: dict[str, float] = {}
    peso = 0.35

    if data.get("resultado_real"):
        factores["resultado_real"] = 0.25
        peso += 0.25
    else:
        factores["solo_hipotesis"] = -0.15
        peso -= 0.15

    estado = data.get("estado", "INDETERMINADO")
    if estado == "EXITO":
        factores["estado_exito"] = 0.20
        peso += 0.20
    elif estado == "PARCIAL":
        factores["estado_parcial"] = 0.08
        peso += 0.08
    elif estado == "FRACASO":
        factores["estado_fracaso"] = -0.20
        peso -= 0.20

    fb = (data.get("feedback_humano") or "").upper()
    if fb in FEEDBACK_POSITIVO:
        factores["feedback_positivo"] = 0.08
        peso += 0.08
        if estado in ("FRACASO", "INDETERMINADO") and not _kpi_mejoro(data):
            factores["feedback_sin_kpi"] = -0.12
            peso -= 0.12
    elif fb in FEEDBACK_NEGATIVO:
        factores["feedback_negativo"] = -0.10
        peso -= 0.10

    if data.get("kpi_antes_json") and data.get("kpi_despues_json"):
        factores["evidencia_kpi"] = 0.10
        peso += 0.10

    if data.get("condiciones_exito_json") or data.get("condiciones_fracaso_json"):
        factores["contexto_comparable"] = 0.05
        peso += 0.05

    created = data.get("created_at")
    if created and hasattr(created, "timestamp"):
        age_days = (_utcnow() - created).days if created.tzinfo else 0
        if age_days <= 90:
            factores["reciente"] = 0.05
            peso += 0.05
        elif age_days > 365:
            factores["antigua"] = -0.05
            peso -= 0.05

    peso = max(0.05, min(1.0, round(peso, 3)))
    return {"peso": peso, "factores": factores}


def _kpi_mejoro(data: dict[str, Any]) -> bool:
    try:
        antes = json.loads(data.get("kpi_antes_json") or "{}")
        despues = json.loads(data.get("kpi_despues_json") or "{}")
    except json.JSONDecodeError:
        return False
    for key, val_antes in antes.items():
        val_despues = despues.get(key)
        if isinstance(val_antes, (int, float)) and isinstance(val_despues, (int, float)):
            if val_despues < val_antes:
                return True
    return bool(despues) and despues != antes


def crear_experiencia(
    db: Session,
    org_id: str,
    *,
    employee_id: str,
    dominio: str,
    tipo_problema: str,
    contexto: dict | None = None,
    senales: dict | None = None,
    hipotesis: str | None = None,
    decision: str | None = None,
    accion: str | None = None,
    resultado_esperado: str | None = None,
    work_plan_id: str | None = None,
    caso_origen_id: str | None = None,
    trazabilidad: dict | None = None,
) -> EmployeeExperienceRecord:
    record = EmployeeExperienceRecord(
        organization_id=org_id,
        employee_id=employee_id,
        dominio=dominio,
        tipo_problema=tipo_problema,
        contexto_json=json.dumps(contexto or {}, ensure_ascii=False),
        senales_json=json.dumps(senales or {}, ensure_ascii=False),
        hipotesis=hipotesis,
        decision=decision,
        accion=accion,
        resultado_esperado=resultado_esperado,
        estado="INDETERMINADO",
        work_plan_id=work_plan_id,
        caso_origen_id=caso_origen_id,
        trazabilidad_json=json.dumps(trazabilidad or {}, ensure_ascii=False),
    )
    calidad = calcular_peso_calidad(record)
    record.peso_calidad = calidad["peso"]
    record.confianza = 0.5
    db.add(record)
    db.flush()
    return record


def actualizar_resultado_experiencia(
    db: Session,
    org_id: str,
    record_id: str,
    *,
    resultado_real: str,
    estado: str,
    kpi_despues: dict | None = None,
    valor_obtenido: float | None = None,
    tiempo_real_horas: float | None = None,
    condiciones_exito: list | None = None,
    condiciones_fracaso: list | None = None,
) -> EmployeeExperienceRecord | None:
    record = (
        db.query(EmployeeExperienceRecord)
        .filter(
            EmployeeExperienceRecord.id == record_id,
            EmployeeExperienceRecord.organization_id == org_id,
        )
        .first()
    )
    if not record:
        return None
    record.resultado_real = resultado_real
    record.estado = estado if estado in ESTADOS_VALIDOS else "INDETERMINADO"
    if kpi_despues is not None:
        record.kpi_despues_json = json.dumps(kpi_despues, ensure_ascii=False)
    if valor_obtenido is not None:
        record.valor_obtenido = valor_obtenido
    if tiempo_real_horas is not None:
        record.tiempo_real_horas = tiempo_real_horas
    if condiciones_exito is not None:
        record.condiciones_exito_json = json.dumps(condiciones_exito, ensure_ascii=False)
    if condiciones_fracaso is not None:
        record.condiciones_fracaso_json = json.dumps(condiciones_fracaso, ensure_ascii=False)
    record.resultado_actualizado_at = _utcnow()
    calidad = calcular_peso_calidad(record)
    record.peso_calidad = calidad["peso"]
    return record


def registrar_feedback_experiencia(
    db: Session,
    org_id: str,
    record_id: str,
    feedback: str,
) -> EmployeeExperienceRecord | None:
    record = (
        db.query(EmployeeExperienceRecord)
        .filter(
            EmployeeExperienceRecord.id == record_id,
            EmployeeExperienceRecord.organization_id == org_id,
        )
        .first()
    )
    if not record:
        return None
    record.feedback_humano = feedback.upper()
    calidad = calcular_peso_calidad(record)
    record.peso_calidad = calidad["peso"]
    return record


def buscar_experiencias_similares(
    db: Session,
    org_id: str,
    *,
    dominio: str | None = None,
    tipo_problema: str | None = None,
    contexto: dict | None = None,
    employee_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Similitud estructurada V1 — interfaz preparada para embeddings futuros."""
    query = db.query(EmployeeExperienceRecord).filter(
        EmployeeExperienceRecord.organization_id == org_id,
    )
    if dominio:
        query = query.filter(EmployeeExperienceRecord.dominio == dominio)
    if tipo_problema:
        query = query.filter(EmployeeExperienceRecord.tipo_problema.contains(tipo_problema))
    if employee_id:
        query = query.filter(EmployeeExperienceRecord.employee_id == employee_id)

    records = query.order_by(EmployeeExperienceRecord.created_at.desc()).limit(100).all()
    scored: list[tuple[float, EmployeeExperienceRecord, dict]] = []

    for rec in records:
        sim = _similitud_estructurada(rec, dominio, tipo_problema, contexto)
        if sim["puntaje"] > 0.1:
            scored.append((sim["puntaje"], rec, sim))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": rec.id,
            "employee_id": rec.employee_id,
            "dominio": rec.dominio,
            "tipo_problema": rec.tipo_problema,
            "estado": rec.estado,
            "similitud": round(score, 3),
            "factores_similitud": sim_detail.get("factores", {}),
            "peso_calidad": rec.peso_calidad,
            "condiciones_exito": json.loads(rec.condiciones_exito_json or "[]"),
            "condiciones_fracaso": json.loads(rec.condiciones_fracaso_json or "[]"),
            "explicacion": sim_detail.get("explicacion", ""),
        }
        for score, rec, sim_detail in scored[:limit]
    ]


def _similitud_estructurada(
    rec: EmployeeExperienceRecord,
    dominio: str | None,
    tipo_problema: str | None,
    contexto: dict | None,
) -> dict[str, Any]:
    factores: dict[str, float] = {}
    puntaje = 0.0

    if dominio and rec.dominio == dominio:
        factores["dominio"] = 0.30
        puntaje += 0.30

    if tipo_problema and tipo_problema.lower() in rec.tipo_problema.lower():
        factores["tipo_problema"] = 0.25
        puntaje += 0.25

    if contexto:
        try:
            ctx_rec = json.loads(rec.contexto_json or "{}")
            senales_rec = json.loads(rec.senales_json or "{}")
        except json.JSONDecodeError:
            ctx_rec, senales_rec = {}, {}

        for key in ("sector", "escala", "fuente", "variables"):
            if key in contexto and contexto[key] == ctx_rec.get(key):
                factores[f"contexto_{key}"] = 0.08
                puntaje += 0.08

        for key, val in (contexto.get("variables") or {}).items():
            if senales_rec.get(key) == val or ctx_rec.get(key) == val:
                factores["variable"] = factores.get("variable", 0) + 0.05
                puntaje += 0.05

    if rec.estado == "EXITO":
        factores["resultado_exitoso"] = 0.10
        puntaje += 0.10
    elif rec.estado == "FRACASO":
        factores["resultado_fracaso"] = 0.05
        puntaje += 0.05

    if rec.peso_calidad:
        boost = rec.peso_calidad * 0.15
        factores["calidad_experiencia"] = round(boost, 3)
        puntaje += boost

    explicacion_parts = [f"{k}={v}" for k, v in factores.items()]
    return {
        "puntaje": round(min(puntaje, 1.0), 3),
        "factores": factores,
        "explicacion": "; ".join(explicacion_parts) if explicacion_parts else "baja similitud",
    }


def experiencia_score_para_empleado(
    db: Session,
    org_id: str,
    employee_id: str,
    dominio: str,
    tipo_problema: str,
    contexto: dict | None = None,
) -> dict[str, Any]:
    """Puntaje de experiencia para selección — con explicación."""
    similares = buscar_experiencias_similares(
        db, org_id,
        dominio=dominio,
        tipo_problema=tipo_problema,
        contexto=contexto,
        employee_id=employee_id,
        limit=20,
    )
    if not similares:
        return {"score": 0.35, "factores": {"sin_experiencia": 0.35}, "casos": 0, "explicacion": "Sin experiencia comparable"}

    exitos = [s for s in similares if s["estado"] == "EXITO"]
    fracasos = [s for s in similares if s["estado"] == "FRACASO"]
    peso_prom = sum(s.get("peso_calidad") or 0.5 for s in similares) / len(similares)
    sim_prom = sum(s["similitud"] for s in similares) / len(similares)

    score = min(1.0, 0.2 + sim_prom * 0.35 + peso_prom * 0.25)
    if exitos and fracasos:
        score *= 0.85
        explicacion = (
            f"Experiencia contradictoria: {len(exitos)} éxitos y {len(fracasos)} fracasos "
            f"en contextos similares — revisar condiciones"
        )
    elif exitos:
        score = min(1.0, score + 0.1)
        explicacion = f"{len(exitos)} experiencias exitosas en {dominio}"
    elif fracasos:
        score = max(0.1, score - 0.15)
        explicacion = f"{len(fracasos)} fracasos previos en {dominio}"
    else:
        explicacion = f"{len(similares)} experiencias parciales/indeterminadas"

    return {
        "score": round(score, 3),
        "factores": {
            "similitud_promedio": round(sim_prom, 3),
            "peso_calidad_promedio": round(peso_prom, 3),
            "exitos": len(exitos),
            "fracasos": len(fracasos),
        },
        "casos": len(similares),
        "explicacion": explicacion,
        "experiencias_consultadas": [s["id"] for s in similares[:5]],
    }
