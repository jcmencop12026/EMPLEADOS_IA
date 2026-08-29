"""Servicio de línea base, medición e impacto — Bloque 1200."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.baseline_models import (
    ATRIBUCION_NIVELES,
    DIRECCION_INDICADOR,
    ESTADOS_LINEA_BASE,
    EVALUACIONES,
    LineaBase,
    LineaBaseHistorial,
    LineaBaseImpacto,
    LineaBaseMedicion,
    TIPOS_IMPACTO,
)


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _parse_json(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def calculate_variation(valor_base: float, valor_posterior: float) -> tuple[float, float | None]:
    variacion_absoluta = valor_posterior - valor_base
    if valor_base == 0:
        return variacion_absoluta, None
    variacion_porcentual = (variacion_absoluta / valor_base) * 100
    return variacion_absoluta, variacion_porcentual


def evaluate_direction(direccion: str, valor_base: float, valor_posterior: float) -> str:
    if direccion == "INFORMATIVO":
        return "INFORMATIVO"
    if valor_posterior == valor_base:
        return "SIN_CAMBIO"
    if direccion == "MAYOR_ES_MEJOR":
        return "MEJORA" if valor_posterior > valor_base else "DETERIORO"
    if direccion == "MENOR_ES_MEJOR":
        return "MEJORA" if valor_posterior < valor_base else "DETERIORO"
    return "INFORMATIVO"


def resolve_tipo_impacto(
    *,
    atribucion_nivel: str,
    medicion_validada: bool,
    tiene_evidencia: bool,
) -> str:
    if atribucion_nivel in ("ATRIBUIBLE", "PARCIALMENTE_ATRIBUIBLE") and medicion_validada and tiene_evidencia:
        return "VALOR_ATRIBUIDO"
    if medicion_validada and tiene_evidencia:
        return "IMPACTO_REAL"
    return "CAMBIO_OBSERVADO"


def _snapshot_linea_base(lb: LineaBase) -> dict[str, Any]:
    return {
        "indicador": lb.indicador,
        "valor_base": _to_float(lb.valor_base),
        "unidad": lb.unidad,
        "estado": lb.estado,
        "direccion_indicador": lb.direccion_indicador,
        "impacto_esperado": _to_float(lb.impacto_esperado),
        "opportunity_id": lb.opportunity_id,
        "work_plan_id": lb.work_plan_id,
    }


def _record_historial(
    db: Session,
    *,
    linea_base: LineaBase,
    actor_id: str | None,
    accion: str,
    snapshot: dict | None = None,
) -> None:
    db.add(
        LineaBaseHistorial(
            linea_base_id=linea_base.id,
            organization_id=linea_base.organization_id,
            actor_id=actor_id,
            accion=accion,
            snapshot_json=_json(snapshot) if snapshot else None,
        )
    )


def linea_base_to_dict(lb: LineaBase) -> dict[str, Any]:
    return {
        "id": lb.id,
        "organization_id": lb.organization_id,
        "indicador": lb.indicador,
        "descripcion": lb.descripcion,
        "unidad": lb.unidad,
        "valor_base": _to_float(lb.valor_base),
        "fecha_inicio_base": lb.fecha_inicio_base.isoformat() if lb.fecha_inicio_base else None,
        "fecha_fin_base": lb.fecha_fin_base.isoformat() if lb.fecha_fin_base else None,
        "fuente": lb.fuente,
        "metodo_calculo": lb.metodo_calculo,
        "evidencia": _parse_json(lb.evidencia_json),
        "direccion_indicador": lb.direccion_indicador,
        "impacto_esperado": _to_float(lb.impacto_esperado),
        "estado": lb.estado,
        "responsable_id": lb.responsable_id,
        "proceso": lb.proceso,
        "opportunity_id": lb.opportunity_id,
        "work_plan_id": lb.work_plan_id,
        "employee_id": lb.employee_id,
        "accion_referencia": lb.accion_referencia,
        "valor_economico_tipo": lb.valor_economico_tipo,
        "created_at": lb.created_at.isoformat() if lb.created_at else None,
        "updated_at": lb.updated_at.isoformat() if lb.updated_at else None,
    }


def impacto_to_dict(imp: LineaBaseImpacto) -> dict[str, Any]:
    return {
        "id": imp.id,
        "medicion_id": imp.medicion_id,
        "valor_base": _to_float(imp.valor_base),
        "valor_posterior": _to_float(imp.valor_posterior),
        "variacion_absoluta": _to_float(imp.variacion_absoluta),
        "variacion_porcentual": _to_float(imp.variacion_porcentual),
        "evaluacion": imp.evaluacion,
        "tipo_impacto": imp.tipo_impacto,
        "atribucion_nivel": imp.atribucion_nivel,
        "atribucion_porcentaje": _to_float(imp.atribucion_porcentaje),
        "atribucion_justificacion": imp.atribucion_justificacion,
        "atribucion_evidencia": _parse_json(imp.atribucion_evidencia_json),
        "impacto_esperado": _to_float(imp.impacto_esperado),
        "impacto_real": _to_float(imp.impacto_real),
        "congelado": imp.congelado,
        "created_at": imp.created_at.isoformat() if imp.created_at else None,
    }


def medicion_to_dict(med: LineaBaseMedicion, impacto: LineaBaseImpacto | None = None) -> dict[str, Any]:
    return {
        "id": med.id,
        "valor_posterior": _to_float(med.valor_posterior),
        "periodo_inicio": med.periodo_inicio.isoformat() if med.periodo_inicio else None,
        "periodo_fin": med.periodo_fin.isoformat() if med.periodo_fin else None,
        "fuente": med.fuente,
        "evidencia": _parse_json(med.evidencia_json),
        "responsable_id": med.responsable_id,
        "estado": med.estado,
        "created_at": med.created_at.isoformat() if med.created_at else None,
        "validated_at": med.validated_at.isoformat() if med.validated_at else None,
        "validated_by": med.validated_by,
        "impacto": impacto_to_dict(impacto) if impacto else None,
    }


def create_linea_base(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    indicador: str,
    valor_base: float,
    fecha_inicio_base: datetime,
    fecha_fin_base: datetime,
    unidad: str = "unidad",
    descripcion: str | None = None,
    fuente: str = "MANUAL",
    metodo_calculo: str | None = None,
    evidencia: dict | None = None,
    direccion_indicador: str = "MAYOR_ES_MEJOR",
    impacto_esperado: float | None = None,
    estado: str = "BORRADOR",
    proceso: str | None = None,
    opportunity_id: str | None = None,
    work_plan_id: str | None = None,
    employee_id: str | None = None,
    accion_referencia: str | None = None,
    valor_economico_tipo: str | None = None,
) -> LineaBase:
    if direccion_indicador not in DIRECCION_INDICADOR:
        raise ValueError(f"Dirección de indicador inválida: {direccion_indicador}")
    if estado not in ESTADOS_LINEA_BASE:
        raise ValueError(f"Estado inválido: {estado}")

    lb = LineaBase(
        organization_id=organization_id,
        indicador=indicador,
        descripcion=descripcion,
        unidad=unidad,
        valor_base=Decimal(str(valor_base)),
        fecha_inicio_base=fecha_inicio_base,
        fecha_fin_base=fecha_fin_base,
        fuente=fuente,
        metodo_calculo=metodo_calculo,
        evidencia_json=_json(evidencia) if evidencia else None,
        direccion_indicador=direccion_indicador,
        impacto_esperado=Decimal(str(impacto_esperado)) if impacto_esperado is not None else None,
        estado=estado,
        responsable_id=user_id,
        proceso=proceso,
        opportunity_id=opportunity_id,
        work_plan_id=work_plan_id,
        employee_id=employee_id,
        accion_referencia=accion_referencia,
        valor_economico_tipo=valor_economico_tipo,
    )
    db.add(lb)
    db.flush()
    _record_historial(db, linea_base=lb, actor_id=user_id, accion="LINEA_BASE_CREADA", snapshot=_snapshot_linea_base(lb))
    write_audit(
        db,
        action="linea_base.creada",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"indicador={indicador}",
        commit=False,
    )
    return lb


def update_linea_base(
    db: Session,
    linea_base: LineaBase,
    *,
    user_id: str,
    **fields: Any,
) -> LineaBase:
    if linea_base.estado in ("VALIDADA", "CERRADA"):
        raise ValueError("No se puede modificar una línea base validada o cerrada")

    before = _snapshot_linea_base(linea_base)
    allowed = {
        "indicador", "descripcion", "unidad", "valor_base", "fecha_inicio_base", "fecha_fin_base",
        "fuente", "metodo_calculo", "evidencia", "direccion_indicador", "impacto_esperado", "estado",
        "proceso", "opportunity_id", "work_plan_id", "employee_id", "accion_referencia", "valor_economico_tipo",
    }
    for key, value in fields.items():
        if key not in allowed or value is None:
            continue
        if key == "evidencia":
            linea_base.evidencia_json = _json(value)
        elif key in ("valor_base", "impacto_esperado"):
            setattr(linea_base, key, Decimal(str(value)))
        else:
            setattr(linea_base, key, value)

    linea_base.updated_at = _utcnow()
    _record_historial(
        db,
        linea_base=linea_base,
        actor_id=user_id,
        accion="LINEA_BASE_MODIFICADA",
        snapshot={"antes": before, "despues": _snapshot_linea_base(linea_base)},
    )
    write_audit(
        db,
        action="linea_base.modificada",
        organization_id=linea_base.organization_id,
        user_id=user_id,
        detail=f"id={linea_base.id}",
        commit=False,
    )
    return linea_base


def _build_impacto(
    linea_base: LineaBase,
    medicion: LineaBaseMedicion,
    *,
    medicion_validada: bool = False,
    atribucion_nivel: str = "NO_ATRIBUIBLE",
) -> LineaBaseImpacto:
    vb = float(linea_base.valor_base)
    vp = float(medicion.valor_posterior)
    abs_var, pct_var = calculate_variation(vb, vp)
    evaluacion = evaluate_direction(linea_base.direccion_indicador, vb, vp)
    tiene_evidencia = bool(medicion.evidencia_json)
    tipo = resolve_tipo_impacto(
        atribucion_nivel=atribucion_nivel,
        medicion_validada=medicion_validada,
        tiene_evidencia=tiene_evidencia,
    )
    impacto_esperado = _to_float(linea_base.impacto_esperado)
    impacto_real = abs_var if medicion_validada and tiene_evidencia else None

    return LineaBaseImpacto(
        linea_base_id=linea_base.id,
        medicion_id=medicion.id,
        organization_id=linea_base.organization_id,
        valor_base=Decimal(str(vb)),
        valor_posterior=Decimal(str(vp)),
        variacion_absoluta=Decimal(str(round(abs_var, 4))),
        variacion_porcentual=Decimal(str(round(pct_var, 4))) if pct_var is not None else None,
        evaluacion=evaluacion,
        tipo_impacto=tipo,
        atribucion_nivel=atribucion_nivel,
        impacto_esperado=Decimal(str(impacto_esperado)) if impacto_esperado is not None else None,
        impacto_real=Decimal(str(impacto_real)) if impacto_real is not None else None,
        congelado=medicion_validada,
    )


def register_medicion(
    db: Session,
    linea_base: LineaBase,
    *,
    user_id: str,
    valor_posterior: float,
    periodo_inicio: datetime,
    periodo_fin: datetime,
    fuente: str = "MANUAL",
    evidencia: dict | None = None,
) -> tuple[LineaBaseMedicion, LineaBaseImpacto]:
    if linea_base.estado in ("CERRADA",):
        raise ValueError("No se pueden registrar mediciones en una línea base cerrada")

    med = LineaBaseMedicion(
        linea_base_id=linea_base.id,
        organization_id=linea_base.organization_id,
        valor_posterior=Decimal(str(valor_posterior)),
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        fuente=fuente,
        evidencia_json=_json(evidencia) if evidencia else None,
        responsable_id=user_id,
    )
    db.add(med)
    db.flush()

    impacto = _build_impacto(linea_base, med)
    db.add(impacto)

    if linea_base.estado in ("BORRADOR", "ACTIVA"):
        linea_base.estado = "EN_MEDICION"
    linea_base.updated_at = _utcnow()

    _record_historial(
        db,
        linea_base=linea_base,
        actor_id=user_id,
        accion="MEDICION_REGISTRADA",
        snapshot={"medicion_id": med.id, "valor_posterior": valor_posterior},
    )
    write_audit(
        db,
        action="linea_base.medicion_registrada",
        organization_id=linea_base.organization_id,
        user_id=user_id,
        detail=f"linea_base={linea_base.id} medicion={med.id}",
        commit=False,
    )
    return med, impacto


def validate_medicion(
    db: Session,
    linea_base: LineaBase,
    medicion: LineaBaseMedicion,
    impacto: LineaBaseImpacto,
    *,
    user_id: str,
) -> LineaBaseImpacto:
    if medicion.estado == "VALIDADA":
        return impacto
    if impacto.congelado:
        raise ValueError("El impacto ya está congelado")

    medicion.estado = "VALIDADA"
    medicion.validated_at = _utcnow()
    medicion.validated_by = user_id

    impacto.tipo_impacto = resolve_tipo_impacto(
        atribucion_nivel=impacto.atribucion_nivel,
        medicion_validada=True,
        tiene_evidencia=bool(medicion.evidencia_json),
    )
    abs_var = float(impacto.variacion_absoluta)
    impacto.impacto_real = Decimal(str(abs_var)) if medicion.evidencia_json else None
    impacto.congelado = True
    impacto.updated_at = _utcnow()

    linea_base.estado = "VALIDADA"
    linea_base.updated_at = _utcnow()

    _record_historial(
        db,
        linea_base=linea_base,
        actor_id=user_id,
        accion="MEDICION_VALIDADA",
        snapshot={"medicion_id": medicion.id, "impacto_id": impacto.id},
    )
    write_audit(
        db,
        action="linea_base.impacto_validado",
        organization_id=linea_base.organization_id,
        user_id=user_id,
        detail=f"medicion={medicion.id}",
        commit=False,
    )
    return impacto


def update_atribucion(
    db: Session,
    linea_base: LineaBase,
    impacto: LineaBaseImpacto,
    medicion: LineaBaseMedicion,
    *,
    user_id: str,
    atribucion_nivel: str,
    atribucion_porcentaje: float | None = None,
    justificacion: str | None = None,
    evidencia: dict | None = None,
) -> LineaBaseImpacto:
    if atribucion_nivel not in ATRIBUCION_NIVELES:
        raise ValueError(f"Nivel de atribución inválido: {atribucion_nivel}")
    if impacto.congelado:
        raise ValueError("No se puede modificar la atribución de un impacto congelado")

    impacto.atribucion_nivel = atribucion_nivel
    impacto.atribucion_porcentaje = (
        Decimal(str(atribucion_porcentaje)) if atribucion_porcentaje is not None else None
    )
    impacto.atribucion_justificacion = justificacion
    impacto.atribucion_evidencia_json = _json(evidencia) if evidencia else None
    impacto.tipo_impacto = resolve_tipo_impacto(
        atribucion_nivel=atribucion_nivel,
        medicion_validada=medicion.estado == "VALIDADA",
        tiene_evidencia=bool(medicion.evidencia_json or evidencia),
    )
    impacto.updated_at = _utcnow()

    _record_historial(
        db,
        linea_base=linea_base,
        actor_id=user_id,
        accion="ATRIBUCION_MODIFICADA",
        snapshot={"impacto_id": impacto.id, "atribucion_nivel": atribucion_nivel},
    )
    write_audit(
        db,
        action="linea_base.atribucion_modificada",
        organization_id=linea_base.organization_id,
        user_id=user_id,
        detail=f"impacto={impacto.id} nivel={atribucion_nivel}",
        commit=False,
    )
    return impacto


def get_evolucion(db: Session, linea_base_id: str, organization_id: str) -> dict[str, Any]:
    mediciones = (
        db.query(LineaBaseMedicion)
        .filter(
            LineaBaseMedicion.linea_base_id == linea_base_id,
            LineaBaseMedicion.organization_id == organization_id,
        )
        .order_by(LineaBaseMedicion.periodo_fin)
        .all()
    )
    puntos = []
    for med in mediciones:
        impacto = (
            db.query(LineaBaseImpacto)
            .filter(LineaBaseImpacto.medicion_id == med.id)
            .first()
        )
        puntos.append({
            "fecha": med.periodo_fin.isoformat() if med.periodo_fin else None,
            "valor": _to_float(med.valor_posterior),
            "evaluacion": impacto.evaluacion if impacto else None,
            "estado": med.estado,
        })
    return {"linea_base_id": linea_base_id, "puntos": puntos}


def get_historial(db: Session, linea_base_id: str, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LineaBaseHistorial)
        .filter(
            LineaBaseHistorial.linea_base_id == linea_base_id,
            LineaBaseHistorial.organization_id == organization_id,
        )
        .order_by(LineaBaseHistorial.created_at)
        .all()
    )
    return [
        {
            "id": r.id,
            "accion": r.accion,
            "actor_id": r.actor_id,
            "snapshot": _parse_json(r.snapshot_json),
            "fecha": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
