"""Servicio — Aprendizaje, retroalimentación y repriorización (Bloque 1260)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.learning_models import (
    AprendizajeAuditoria,
    CicloAprendizaje,
    PatronAprendizaje,
    Recalibracion,
    Retroalimentacion,
)
from app.models import User
from app.opportunity_models import Opportunity
from app.valuation_models import OpportunityValuation, OpportunityValuationExpected, OpportunityValuationReal

_URGENCIA_SCORE = {"BAJA": 0.25, "MEDIA": 0.5, "ALTA": 0.75, "CRITICA": 1.0}
_RIESGO_SCORE = {"BAJO": 0.2, "MEDIO": 0.5, "ALTO": 0.8, "CRITICO": 1.0}
_ESFUERZO_SCORE = {"BAJO": 0.25, "MEDIO": 0.5, "ALTO": 0.75, "MUY_ALTO": 1.0}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _json_load(raw: str | None) -> Any:
    if not raw:
        return None
    return json.loads(raw)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _get_opportunity(db: Session, org_id: str, opportunity_id: str) -> Opportunity:
    opp = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.organization_id == org_id)
        .first()
    )
    if not opp:
        raise ValueError("Oportunidad no encontrada")
    return opp


def _registrar_auditoria(
    db: Session,
    *,
    org_id: str,
    accion: str,
    actor_id: str | None,
    ciclo_id: str | None = None,
    recalibracion_id: str | None = None,
    opportunity_id: str | None = None,
    detalle: dict | None = None,
) -> None:
    db.add(
        AprendizajeAuditoria(
            organization_id=org_id,
            ciclo_id=ciclo_id,
            recalibracion_id=recalibracion_id,
            opportunity_id=opportunity_id,
            accion=accion,
            actor_id=actor_id,
            detalle_json=_json_dump(detalle) if detalle else None,
        )
    )


def _cargar_referencias_esperadas(db: Session, org_id: str, opp: Opportunity) -> dict[str, Any]:
    refs: dict[str, Any] = {
        "opportunity_id": opp.id,
        "signal_id": opp.signal_id,
        "work_plan_id": opp.work_plan_id,
        "impacto_esperado": _float_or_none(opp.impacto_estimado),
        "valor_esperado": _float_or_none(opp.valor_potencial),
        "costo_esperado": _float_or_none(opp.costo_estimado),
        "tiempo_esperado_dias": None,
        "valuation_id": None,
        "linea_base_id": None,
        "diagnostic_id": None,
    }
    valuation = (
        db.query(OpportunityValuation)
        .filter(
            OpportunityValuation.organization_id == org_id,
            OpportunityValuation.opportunity_id == opp.id,
        )
        .first()
    )
    if valuation:
        refs["valuation_id"] = valuation.id
        expected = (
            db.query(OpportunityValuationExpected)
            .filter(OpportunityValuationExpected.valuation_id == valuation.id)
            .first()
        )
        if expected:
            if expected.adjusted_expected is not None:
                refs["valor_esperado"] = _float_or_none(expected.adjusted_expected)
            if expected.execution_cost_expected is not None:
                refs["costo_esperado"] = _float_or_none(expected.execution_cost_expected)
            if expected.period_days is not None:
                refs["tiempo_esperado_dias"] = float(expected.period_days)
        real = (
            db.query(OpportunityValuationReal)
            .filter(OpportunityValuationReal.valuation_id == valuation.id)
            .order_by(OpportunityValuationReal.created_at.desc())
            .first()
        )
        if real:
            if real.materialized_value is not None and refs.get("valor_real") is None:
                refs["valor_real_sugerido"] = _float_or_none(real.materialized_value)
            if real.attributable_value is not None and refs.get("impacto_real") is None:
                refs["impacto_real_sugerido"] = _float_or_none(real.attributable_value)
    return refs


def _calcular_desviacion(esperado: float | None, real: float | None) -> dict[str, Any] | None:
    if esperado is None or real is None:
        return None
    absoluta = real - esperado
    porcentual = (absoluta / esperado * 100.0) if esperado != 0 else None
    direccion = "SIN_CAMBIO"
    if absoluta > 0:
        direccion = "SUPERIOR"
    elif absoluta < 0:
        direccion = "INFERIOR"
    return {
        "esperado": esperado,
        "real": real,
        "absoluta": absoluta,
        "porcentual": porcentual,
        "direccion": direccion,
    }


def _calidad_por_desviacion(desviaciones: dict[str, Any]) -> str:
    pcts = []
    for key in ("impacto", "valor", "costo", "tiempo"):
        block = desviaciones.get(key)
        if block and block.get("porcentual") is not None:
            pcts.append(abs(float(block["porcentual"])))
    if not pcts:
        return "ACEPTABLE"
    max_pct = max(pcts)
    if max_pct < 10:
        return "EXCELENTE"
    if max_pct < 25:
        return "ACEPTABLE"
    if max_pct < 50:
        return "DEBIL"
    return "DEFICIENTE"


def _urgencia_score(urgencia: str | None) -> float:
    return _URGENCIA_SCORE.get((urgencia or "MEDIA").upper(), 0.5)


def _riesgo_score(riesgo: str | None) -> float:
    return _RIESGO_SCORE.get((riesgo or "MEDIO").upper(), 0.5)


def _calcular_prioridad_explicable(opp: Opportunity, desviaciones: dict[str, Any], calidad: str) -> tuple[float, dict[str, Any]]:
    impacto = _float_or_none(opp.impacto_estimado) or 0.0
    valor = _float_or_none(opp.valor_potencial) or 0.0
    confianza = _float_or_none(opp.confianza) or 0.5
    urgencia = _urgencia_score(opp.urgencia)
    riesgo = _riesgo_score(opp.riesgo)
    costo = _float_or_none(opp.costo_estimado) or 0.0

    impacto_norm = min(impacto / 1_000_000.0, 1.0) if impacto else 0.0
    valor_norm = min(valor / 1_000_000.0, 1.0) if valor else 0.0
    costo_penalty = min(costo / 500_000.0, 1.0) if costo else 0.0

    valor_block = desviaciones.get("valor") or {}
    impacto_block = desviaciones.get("impacto") or {}
    factor_desviacion = 1.0
    if valor_block.get("direccion") == "INFERIOR":
        factor_desviacion -= 0.15
    elif valor_block.get("direccion") == "SUPERIOR":
        factor_desviacion += 0.05
    if impacto_block.get("direccion") == "INFERIOR":
        factor_desviacion -= 0.1
    if calidad == "DEFICIENTE":
        factor_desviacion -= 0.2
    elif calidad == "EXCELENTE":
        factor_desviacion += 0.05
    factor_desviacion = max(0.1, min(1.5, factor_desviacion))

    componentes = {
        "impacto": round(impacto_norm * 0.25, 4),
        "valor": round(valor_norm * 0.25, 4),
        "urgencia": round(urgencia * 0.15, 4),
        "riesgo_inverso": round((1 - riesgo) * 0.1, 4),
        "confianza": round(confianza * 0.15, 4),
        "costo_penalty": round(-costo_penalty * 0.1, 4),
        "factor_desviacion": round(factor_desviacion, 4),
    }
    base = sum(v for k, v in componentes.items() if k != "factor_desviacion")
    score = round(max(0.0, min(100.0, base * factor_desviacion * 100)), 4)
    explicacion = {
        "formula": "prioridad = (impacto + valor + urgencia + confianza - riesgo - costo) × factor_desviación",
        "componentes": componentes,
        "score": score,
        "factores_considerados": [
            "impacto estimado",
            "valor potencial",
            "urgencia",
            "riesgo",
            "confianza",
            "costo estimado",
            "desviación valor/impacto",
            f"calidad recomendación: {calidad}",
        ],
    }
    return score, explicacion


def crear_ciclo_aprendizaje(
    db: Session,
    user: User,
    *,
    opportunity_id: str,
    impacto_real: float | None = None,
    valor_real: float | None = None,
    costo_real: float | None = None,
    tiempo_real_dias: float | None = None,
) -> CicloAprendizaje:
    opp = _get_opportunity(db, user.organization_id, opportunity_id)
    refs = _cargar_referencias_esperadas(db, user.organization_id, opp)
    ciclo = CicloAprendizaje(
        organization_id=user.organization_id,
        opportunity_id=opp.id,
        work_plan_id=refs.get("work_plan_id"),
        signal_id=refs.get("signal_id"),
        valuation_id=refs.get("valuation_id"),
        linea_base_id=refs.get("linea_base_id"),
        diagnostic_id=refs.get("diagnostic_id"),
        impacto_esperado=refs.get("impacto_esperado"),
        valor_esperado=refs.get("valor_esperado"),
        costo_esperado=refs.get("costo_esperado"),
        tiempo_esperado_dias=refs.get("tiempo_esperado_dias"),
        impacto_real=impacto_real if impacto_real is not None else refs.get("impacto_real_sugerido"),
        valor_real=valor_real if valor_real is not None else refs.get("valor_real_sugerido"),
        costo_real=costo_real,
        tiempo_real_dias=tiempo_real_dias,
        prioridad_anterior=_float_or_none(opp.prioridad_score),
        referencias_json=_json_dump(refs),
        created_by=user.id,
    )
    db.add(ciclo)
    db.flush()
    _registrar_auditoria(
        db,
        org_id=user.organization_id,
        accion="ciclo.creado",
        actor_id=user.id,
        ciclo_id=ciclo.id,
        opportunity_id=opp.id,
        detalle={"opportunity_id": opp.id},
    )
    return ciclo


def evaluar_ciclo(
    db: Session,
    user: User,
    ciclo_id: str,
    *,
    impacto_real: float | None = None,
    valor_real: float | None = None,
    costo_real: float | None = None,
    tiempo_real_dias: float | None = None,
    tipo_explicacion: str = "PROBABLE",
    notas: str | None = None,
) -> dict[str, Any]:
    ciclo = (
        db.query(CicloAprendizaje)
        .filter(CicloAprendizaje.id == ciclo_id, CicloAprendizaje.organization_id == user.organization_id)
        .first()
    )
    if not ciclo:
        raise ValueError("Ciclo de aprendizaje no encontrado")
    opp = _get_opportunity(db, user.organization_id, ciclo.opportunity_id)

    if impacto_real is not None:
        ciclo.impacto_real = impacto_real
    if valor_real is not None:
        ciclo.valor_real = valor_real
    if costo_real is not None:
        ciclo.costo_real = costo_real
    if tiempo_real_dias is not None:
        ciclo.tiempo_real_dias = tiempo_real_dias

    desviaciones = {
        "impacto": _calcular_desviacion(_float_or_none(ciclo.impacto_esperado), _float_or_none(ciclo.impacto_real)),
        "valor": _calcular_desviacion(_float_or_none(ciclo.valor_esperado), _float_or_none(ciclo.valor_real)),
        "costo": _calcular_desviacion(_float_or_none(ciclo.costo_esperado), _float_or_none(ciclo.costo_real)),
        "tiempo": _calcular_desviacion(_float_or_none(ciclo.tiempo_esperado_dias), _float_or_none(ciclo.tiempo_real_dias)),
    }
    calidad = _calidad_por_desviacion(desviaciones)
    prioridad_propuesta, explicacion = _calcular_prioridad_explicable(opp, desviaciones, calidad)

    ciclo.desviaciones_json = _json_dump(desviaciones)
    ciclo.calidad_recomendacion = calidad
    ciclo.prioridad_propuesta = prioridad_propuesta
    ciclo.explicacion_prioridad_json = _json_dump(explicacion)
    ciclo.estado = "EVALUADO"
    ciclo.evaluado_por = user.id
    ciclo.evaluado_at = _utcnow()
    ciclo.updated_at = _utcnow()

    retro = Retroalimentacion(
        organization_id=user.organization_id,
        ciclo_id=ciclo.id,
        opportunity_id=ciclo.opportunity_id,
        tipo_explicacion=tipo_explicacion,
        calidad_recomendacion=calidad,
        resumen=f"Evaluación del ciclo — calidad {calidad}",
        detalle=notas,
        lecciones_json=_json_dump(_extraer_lecciones(desviaciones, calidad)),
        evidencia_json=ciclo.desviaciones_json,
        created_by=user.id,
    )
    db.add(retro)
    db.flush()

    patrones = detectar_patrones(db, user.organization_id, ciclo=ciclo, desviaciones=desviaciones)
    recalibraciones = proponer_recalibraciones(db, user, ciclo, opp, desviaciones, explicacion)

    _registrar_auditoria(
        db,
        org_id=user.organization_id,
        accion="ciclo.evaluado",
        actor_id=user.id,
        ciclo_id=ciclo.id,
        opportunity_id=ciclo.opportunity_id,
        detalle={"calidad": calidad, "prioridad_propuesta": prioridad_propuesta},
    )
    return {
        "ciclo": ciclo,
        "retroalimentacion": retro,
        "patrones": patrones,
        "recalibraciones": recalibraciones,
        "desviaciones": desviaciones,
        "explicacion_prioridad": explicacion,
    }


def _extraer_lecciones(desviaciones: dict[str, Any], calidad: str) -> list[str]:
    lecciones = []
    for metrica, block in desviaciones.items():
        if not block:
            continue
        dir_ = block.get("direccion")
        if dir_ and dir_ != "SIN_CAMBIO":
            lecciones.append(f"La métrica {metrica} resultó {dir_.lower()} a lo esperado.")
    if calidad in {"DEBIL", "DEFICIENTE"}:
        lecciones.append("Revisar supuestos de priorización y estimaciones iniciales.")
    if calidad == "EXCELENTE":
        lecciones.append("La recomendación previa se alineó bien con el resultado observado.")
    return lecciones


def detectar_patrones(
    db: Session,
    org_id: str,
    *,
    ciclo: CicloAprendizaje,
    desviaciones: dict[str, Any],
) -> list[PatronAprendizaje]:
    opp = _get_opportunity(db, org_id, ciclo.opportunity_id)
    detectados: list[PatronAprendizaje] = []
    for metrica, block in desviaciones.items():
        if not block or block.get("direccion") in (None, "SIN_CAMBIO"):
            continue
        tipo_patron = f"DESVIACION_{metrica.upper()}"
        clave = f"{opp.tipo}|{opp.dominio}|{block['direccion']}"
        existente = (
            db.query(PatronAprendizaje)
            .filter(
                PatronAprendizaje.organization_id == org_id,
                PatronAprendizaje.tipo_patron == tipo_patron,
                PatronAprendizaje.clave_patron == clave,
            )
            .first()
        )
        if existente:
            existente.ocurrencias += 1
            existente.ultima_deteccion_at = _utcnow()
            existente.detalle_json = _json_dump({"ultimo_ciclo_id": ciclo.id, "desviacion": block})
            detectados.append(existente)
        else:
            patron = PatronAprendizaje(
                organization_id=org_id,
                tipo_patron=tipo_patron,
                clave_patron=clave,
                dominio=opp.dominio,
                tipo_oportunidad=opp.tipo,
                ocurrencias=1,
                resumen=f"Patrón {metrica} {block['direccion']} en {opp.dominio}/{opp.tipo}",
                detalle_json=_json_dump({"ciclo_id": ciclo.id, "desviacion": block}),
            )
            db.add(patron)
            db.flush()
            detectados.append(patron)
    return detectados


def proponer_recalibraciones(
    db: Session,
    user: User,
    ciclo: CicloAprendizaje,
    opp: Opportunity,
    desviaciones: dict[str, Any],
    explicacion: dict[str, Any],
) -> list[Recalibracion]:
    propuestas: list[Recalibracion] = []
    prioridad_anterior = _float_or_none(opp.prioridad_score)
    prioridad_nueva = _float_or_none(ciclo.prioridad_propuesta)
    if prioridad_nueva is not None and prioridad_nueva != prioridad_anterior:
        propuestas.append(
            _nueva_recalibracion(
                db, user, ciclo, opp,
                campo="prioridad_score",
                valor_anterior=str(prioridad_anterior) if prioridad_anterior is not None else None,
                valor_nuevo=str(prioridad_nueva),
                justificacion="Ajuste de prioridad según desviaciones observadas y fórmula explicable.",
                factores=explicacion,
            )
        )
    valor_block = desviaciones.get("valor")
    if valor_block and valor_block.get("direccion") == "INFERIOR":
        conf_anterior = _float_or_none(opp.confianza)
        conf_nueva = max(0.1, (conf_anterior or 0.5) - 0.1)
        propuestas.append(
            _nueva_recalibracion(
                db, user, ciclo, opp,
                campo="confianza",
                valor_anterior=str(conf_anterior) if conf_anterior is not None else None,
                valor_nuevo=str(round(conf_nueva, 4)),
                justificacion="Reducir confianza tras desviación negativa de valor real vs esperado.",
                factores={"desviacion_valor": valor_block},
            )
        )
    impacto_block = desviaciones.get("impacto")
    if impacto_block and impacto_block.get("direccion") == "INFERIOR":
        urgencia_actual = opp.urgencia
        nueva_urgencia = "ALTA" if urgencia_actual in {"MEDIA", "BAJA"} else urgencia_actual
        if nueva_urgencia != urgencia_actual:
            propuestas.append(
                _nueva_recalibracion(
                    db, user, ciclo, opp,
                    campo="urgencia",
                    valor_anterior=urgencia_actual,
                    valor_nuevo=nueva_urgencia,
                    justificacion="Incrementar urgencia ante impacto real inferior al esperado.",
                    factores={"desviacion_impacto": impacto_block},
                )
            )
    return propuestas


def _nueva_recalibracion(
    db: Session,
    user: User,
    ciclo: CicloAprendizaje,
    opp: Opportunity,
    *,
    campo: str,
    valor_anterior: str | None,
    valor_nuevo: str,
    justificacion: str,
    factores: dict | None = None,
) -> Recalibracion:
    rec = Recalibracion(
        organization_id=user.organization_id,
        ciclo_id=ciclo.id,
        opportunity_id=opp.id,
        estado="SUGERIDA",
        campo=campo,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        justificacion=justificacion,
        factores_json=_json_dump(factores) if factores else None,
        sugerida_por=user.id,
    )
    db.add(rec)
    db.flush()
    _registrar_auditoria(
        db,
        org_id=user.organization_id,
        accion="recalibracion.sugerida",
        actor_id=user.id,
        ciclo_id=ciclo.id,
        recalibracion_id=rec.id,
        opportunity_id=opp.id,
        detalle={"campo": campo, "valor_nuevo": valor_nuevo},
    )
    return rec


def aprobar_recalibracion(db: Session, user: User, recalibracion_id: str) -> Recalibracion:
    rec = _get_recalibracion(db, user.organization_id, recalibracion_id)
    if rec.estado != "SUGERIDA":
        raise ValueError("Solo se pueden aprobar recalibraciones sugeridas")
    rec.estado = "APROBADA"
    rec.decidida_por = user.id
    rec.decidida_at = _utcnow()
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recalibracion.aprobada",
        actor_id=user.id, ciclo_id=rec.ciclo_id, recalibracion_id=rec.id, opportunity_id=rec.opportunity_id,
    )
    return rec


def rechazar_recalibracion(db: Session, user: User, recalibracion_id: str, motivo: str) -> Recalibracion:
    rec = _get_recalibracion(db, user.organization_id, recalibracion_id)
    if rec.estado != "SUGERIDA":
        raise ValueError("Solo se pueden rechazar recalibraciones sugeridas")
    rec.estado = "RECHAZADA"
    rec.decidida_por = user.id
    rec.decidida_at = _utcnow()
    rec.motivo_rechazo = motivo
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recalibracion.rechazada",
        actor_id=user.id, ciclo_id=rec.ciclo_id, recalibracion_id=rec.id,
        opportunity_id=rec.opportunity_id, detalle={"motivo": motivo},
    )
    return rec


def aplicar_recalibracion(db: Session, user: User, recalibracion_id: str) -> Recalibracion:
    rec = _get_recalibracion(db, user.organization_id, recalibracion_id)
    if rec.estado != "APROBADA":
        raise ValueError("Solo se pueden aplicar recalibraciones aprobadas")
    opp = _get_opportunity(db, user.organization_id, rec.opportunity_id)
    campo = rec.campo
    valor_nuevo = rec.valor_nuevo
    if valor_nuevo is None:
        raise ValueError("Recalibración sin valor nuevo")
    if campo == "prioridad_score":
        opp.prioridad_score = float(valor_nuevo)
        opp.prioridad_componentes_json = rec.factores_json
    elif campo == "confianza":
        opp.confianza = float(valor_nuevo)
    elif campo == "urgencia":
        opp.urgencia = valor_nuevo
    elif campo == "riesgo":
        opp.riesgo = valor_nuevo
    elif campo == "impacto_estimado":
        opp.impacto_estimado = float(valor_nuevo)
    elif campo == "valor_potencial":
        opp.valor_potencial = float(valor_nuevo)
    else:
        raise ValueError(f"Campo no aplicable automáticamente: {campo}")
    opp.fecha_revaluacion = _utcnow()
    opp.updated_at = _utcnow()
    rec.estado = "APLICADA"
    rec.aplicada_por = user.id
    rec.aplicada_at = _utcnow()
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recalibracion.aplicada",
        actor_id=user.id, ciclo_id=rec.ciclo_id, recalibracion_id=rec.id,
        opportunity_id=rec.opportunity_id,
        detalle={"campo": campo, "valor_anterior": rec.valor_anterior, "valor_nuevo": valor_nuevo},
    )
    from app.audit import write_audit
    write_audit(
        db,
        action="aprendizaje.recalibracion_aplicada",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=f"Campo {campo}: {rec.valor_anterior} → {valor_nuevo}",
        commit=False,
    )
    return rec


def _get_recalibracion(db: Session, org_id: str, recalibracion_id: str) -> Recalibracion:
    rec = (
        db.query(Recalibracion)
        .filter(Recalibracion.id == recalibracion_id, Recalibracion.organization_id == org_id)
        .first()
    )
    if not rec:
        raise ValueError("Recalibración no encontrada")
    return rec


def listar_ciclos(db: Session, org_id: str, *, opportunity_id: str | None = None) -> list[CicloAprendizaje]:
    q = db.query(CicloAprendizaje).filter(CicloAprendizaje.organization_id == org_id)
    if opportunity_id:
        q = q.filter(CicloAprendizaje.opportunity_id == opportunity_id)
    return q.order_by(CicloAprendizaje.created_at.desc()).all()


def obtener_ciclo(db: Session, org_id: str, ciclo_id: str) -> CicloAprendizaje | None:
    return (
        db.query(CicloAprendizaje)
        .filter(CicloAprendizaje.id == ciclo_id, CicloAprendizaje.organization_id == org_id)
        .first()
    )


def listar_patrones(db: Session, org_id: str) -> list[PatronAprendizaje]:
    return (
        db.query(PatronAprendizaje)
        .filter(PatronAprendizaje.organization_id == org_id)
        .order_by(PatronAprendizaje.ocurrencias.desc(), PatronAprendizaje.ultima_deteccion_at.desc())
        .all()
    )


def listar_recalibraciones(db: Session, org_id: str, *, ciclo_id: str | None = None) -> list[Recalibracion]:
    q = db.query(Recalibracion).filter(Recalibracion.organization_id == org_id)
    if ciclo_id:
        q = q.filter(Recalibracion.ciclo_id == ciclo_id)
    return q.order_by(Recalibracion.sugerida_at.desc()).all()


def listar_auditoria(db: Session, org_id: str, *, ciclo_id: str | None = None) -> list[AprendizajeAuditoria]:
    q = db.query(AprendizajeAuditoria).filter(AprendizajeAuditoria.organization_id == org_id)
    if ciclo_id:
        q = q.filter(AprendizajeAuditoria.ciclo_id == ciclo_id)
    return q.order_by(AprendizajeAuditoria.created_at.desc()).all()


def serializar_ciclo(ciclo: CicloAprendizaje) -> dict[str, Any]:
    return {
        "id": ciclo.id,
        "organization_id": ciclo.organization_id,
        "opportunity_id": ciclo.opportunity_id,
        "work_plan_id": ciclo.work_plan_id,
        "signal_id": ciclo.signal_id,
        "estado": ciclo.estado,
        "impacto_esperado": _float_or_none(ciclo.impacto_esperado),
        "valor_esperado": _float_or_none(ciclo.valor_esperado),
        "costo_esperado": _float_or_none(ciclo.costo_esperado),
        "tiempo_esperado_dias": _float_or_none(ciclo.tiempo_esperado_dias),
        "impacto_real": _float_or_none(ciclo.impacto_real),
        "valor_real": _float_or_none(ciclo.valor_real),
        "costo_real": _float_or_none(ciclo.costo_real),
        "tiempo_real_dias": _float_or_none(ciclo.tiempo_real_dias),
        "desviaciones": _json_load(ciclo.desviaciones_json),
        "calidad_recomendacion": ciclo.calidad_recomendacion,
        "prioridad_anterior": _float_or_none(ciclo.prioridad_anterior),
        "prioridad_propuesta": _float_or_none(ciclo.prioridad_propuesta),
        "explicacion_prioridad": _json_load(ciclo.explicacion_prioridad_json),
        "referencias": _json_load(ciclo.referencias_json),
        "evaluado_at": ciclo.evaluado_at.isoformat() if ciclo.evaluado_at else None,
        "created_at": ciclo.created_at.isoformat() if ciclo.created_at else None,
    }
