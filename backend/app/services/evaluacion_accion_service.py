"""Acciones externas y capacidades — Bloque Producto 2."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.evaluacion_models import (
    ACCION_ESTADOS,
    ACCION_TIPOS,
    CAPACIDADES_EXTERNAS,
    EvaluacionAccionEvento,
    EvaluacionAccionExterna,
    EvaluacionExpediente,
    EvaluacionHallazgo,
    EvaluacionIndicador,
)
from app.services import evaluacion_service as exp_svc
from app.services.evaluacion_proveedor_externo_service import estado_capacidad_es
from app.services.piiax_bridge_service import (
    CAPACIDAD_LABELS,
    TIPO_ACCION_LABELS,
    TIPO_REQUIERE_APROBACION,
    get_detalle_tecnico_link,
    get_piiax_status,
    solicitar_ejecucion_piiax,
    _org_piiax_config,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _log_evento(
    db: Session,
    *,
    organization_id: str,
    accion_id: str,
    expediente_id: str,
    tipo_evento: str,
    actor_id: str | None,
    correlation_id: str | None,
    detalle: dict[str, Any] | None = None,
) -> None:
    db.add(
        EvaluacionAccionEvento(
            organization_id=organization_id,
            accion_id=accion_id,
            expediente_id=expediente_id,
            tipo_evento=tipo_evento,
            actor_id=actor_id,
            correlation_id=correlation_id,
            detalle=json.dumps(detalle, ensure_ascii=False) if detalle else None,
        )
    )


def _accion_dict(db: Session, a: EvaluacionAccionExterna, org_id: str) -> dict[str, Any]:
    org_cfg = _org_piiax_config(db, org_id)
    piiax = get_piiax_status(db, org_id)
    estado_es = estado_capacidad_es(a.estado, piiax.get("disponible", False))
    return {
        "id": a.id,
        "expediente_id": a.expediente_id,
        "hallazgo_id": a.hallazgo_id,
        "capacidad": a.capacidad,
        "capacidad_etiqueta": CAPACIDAD_LABELS.get(a.capacidad, a.capacidad),
        "tipo_accion": a.tipo_accion,
        "tipo_accion_etiqueta": TIPO_ACCION_LABELS.get(a.tipo_accion, a.tipo_accion),
        "titulo": a.titulo,
        "descripcion": a.descripcion,
        "estado": a.estado,
        "estado_es": estado_es,
        "proveedor_codigo": a.proveedor_codigo,
        "requiere_aprobacion": a.requiere_aprobacion,
        "aprobado_por": a.aprobado_por,
        "aprobado_at": a.aprobado_at.isoformat() if a.aprobado_at else None,
        "correlation_id": a.correlation_id,
        "referencia_externa": a.referencia_externa,
        "resultado_resumen": a.resultado_resumen,
        "evidencia_ref": a.evidencia_ref,
        "error_mensaje": a.error_mensaje,
        "detalle_tecnico_url": get_detalle_tecnico_link(a.referencia_externa, org_cfg),
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def list_acciones(db: Session, expediente_id: str, organization_id: str) -> list[dict[str, Any]]:
    exp_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    rows = (
        db.query(EvaluacionAccionExterna)
        .filter(
            EvaluacionAccionExterna.expediente_id == expediente_id,
            EvaluacionAccionExterna.organization_id == organization_id,
        )
        .order_by(EvaluacionAccionExterna.created_at.desc())
        .all()
    )
    return [_accion_dict(db, r, organization_id) for r in rows]


def crear_accion(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
    capacidad: str,
    tipo_accion: str,
    titulo: str,
    descripcion: str | None = None,
    hallazgo_id: str | None = None,
    parametros: dict[str, Any] | None = None,
    solicitar: bool = False,
) -> EvaluacionAccionExterna:
    if capacidad not in CAPACIDADES_EXTERNAS:
        raise HTTPException(status_code=422, detail=f"Capacidad no reconocida: {capacidad}")
    if tipo_accion not in ACCION_TIPOS:
        raise HTTPException(status_code=422, detail=f"Tipo de acción inválido: {tipo_accion}")

    exp = exp_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    if hallazgo_id:
        h = db.query(EvaluacionHallazgo).filter(
            EvaluacionHallazgo.id == hallazgo_id,
            EvaluacionHallazgo.expediente_id == exp.id,
        ).first()
        if not h:
            raise HTTPException(status_code=404, detail="Hallazgo no encontrado")

    requiere_aprobacion = tipo_accion in TIPO_REQUIERE_APROBACION
    corr = str(uuid.uuid4())
    accion = EvaluacionAccionExterna(
        organization_id=organization_id,
        expediente_id=exp.id,
        hallazgo_id=hallazgo_id,
        capacidad=capacidad,
        tipo_accion=tipo_accion,
        titulo=titulo,
        descripcion=descripcion,
        estado="BORRADOR",
        requiere_aprobacion=requiere_aprobacion,
        correlation_id=corr,
        parametros_json=json.dumps(parametros, ensure_ascii=False) if parametros else None,
        created_by=user_id,
    )
    db.add(accion)
    db.flush()
    _log_evento(
        db,
        organization_id=organization_id,
        accion_id=accion.id,
        expediente_id=exp.id,
        tipo_evento="CREACION",
        actor_id=user_id,
        correlation_id=corr,
        detalle={"capacidad": capacidad, "tipo_accion": tipo_accion},
    )
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="evaluacion.accion.create",
        detail=json.dumps({"accion_id": accion.id, "capacidad": capacidad}),
        commit=False,
    )
    if solicitar:
        solicitar_accion(db, accion.id, organization_id, user_id=user_id)
    return accion


def solicitar_accion(
    db: Session,
    accion_id: str,
    organization_id: str,
    *,
    user_id: str,
) -> EvaluacionAccionExterna:
    accion = (
        db.query(EvaluacionAccionExterna)
        .filter(
            EvaluacionAccionExterna.id == accion_id,
            EvaluacionAccionExterna.organization_id == organization_id,
        )
        .first()
    )
    if not accion:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    if accion.estado not in ("BORRADOR", "APROBADA"):
        raise HTTPException(status_code=409, detail=f"No se puede solicitar en estado {accion.estado}")

    if accion.estado == "BORRADOR" and accion.requiere_aprobacion:
        accion.estado = "PENDIENTE_APROBACION"
        accion.updated_at = _utcnow()
        _log_evento(
            db,
            organization_id=organization_id,
            accion_id=accion.id,
            expediente_id=accion.expediente_id,
            tipo_evento="PENDIENTE_APROBACION",
            actor_id=user_id,
            correlation_id=accion.correlation_id,
        )
        return accion

    piiax = get_piiax_status(db, organization_id)
    params = json.loads(accion.parametros_json) if accion.parametros_json else None
    handoff = solicitar_ejecucion_piiax(
        db=db,
        organization_id=organization_id,
        capacidad=accion.capacidad,
        tipo_accion=accion.tipo_accion,
        correlation_id=accion.correlation_id,
        parametros=params,
        piiax_disponible=piiax["disponible"],
    )
    accion.estado = handoff["estado"]
    accion.proveedor_codigo = handoff.get("proveedor")
    accion.referencia_externa = handoff.get("referencia_externa")
    if not handoff["enviado"]:
        accion.error_mensaje = handoff["mensaje"]
    accion.updated_at = _utcnow()
    _log_evento(
        db,
        organization_id=organization_id,
        accion_id=accion.id,
        expediente_id=accion.expediente_id,
        tipo_evento="SOLICITUD",
        actor_id=user_id,
        correlation_id=accion.correlation_id,
        detalle=handoff,
    )
    return accion


def aprobar_accion(
    db: Session,
    accion_id: str,
    organization_id: str,
    *,
    user_id: str,
    aprobado: bool,
    motivo: str | None = None,
) -> EvaluacionAccionExterna:
    accion = (
        db.query(EvaluacionAccionExterna)
        .filter(
            EvaluacionAccionExterna.id == accion_id,
            EvaluacionAccionExterna.organization_id == organization_id,
        )
        .first()
    )
    if not accion:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    if accion.estado != "PENDIENTE_APROBACION":
        raise HTTPException(status_code=409, detail="La acción no está pendiente de aprobación")

    if aprobado:
        accion.estado = "APROBADA"
        accion.aprobado_por = user_id
        accion.aprobado_at = _utcnow()
        _log_evento(
            db,
            organization_id=organization_id,
            accion_id=accion.id,
            expediente_id=accion.expediente_id,
            tipo_evento="APROBACION",
            actor_id=user_id,
            correlation_id=accion.correlation_id,
        )
        solicitar_accion(db, accion.id, organization_id, user_id=user_id)
    else:
        accion.estado = "RECHAZADA"
        accion.rechazo_motivo = motivo
        accion.updated_at = _utcnow()
        _log_evento(
            db,
            organization_id=organization_id,
            accion_id=accion.id,
            expediente_id=accion.expediente_id,
            tipo_evento="RECHAZO",
            actor_id=user_id,
            correlation_id=accion.correlation_id,
            detalle={"motivo": motivo},
        )
    return accion


def registrar_resultado_compatible(
    db: Session,
    accion_id: str,
    organization_id: str,
    *,
    user_id: str,
    resultado_resumen: str,
    evidencia_ref: str | None = None,
    referencia_externa: str | None = None,
    estado: str = "COMPLETADA",
) -> EvaluacionAccionExterna:
    """Incorpora resultado compatible (p. ej. callback futuro PIIAX o prueba)."""
    if estado not in ACCION_ESTADOS:
        raise HTTPException(status_code=422, detail="Estado inválido")
    accion = (
        db.query(EvaluacionAccionExterna)
        .filter(
            EvaluacionAccionExterna.id == accion_id,
            EvaluacionAccionExterna.organization_id == organization_id,
        )
        .first()
    )
    if not accion:
        raise HTTPException(status_code=404, detail="Acción no encontrada")

    accion.estado = estado
    accion.resultado_resumen = resultado_resumen
    accion.evidencia_ref = evidencia_ref
    if referencia_externa:
        accion.referencia_externa = referencia_externa
    accion.updated_at = _utcnow()
    _log_evento(
        db,
        organization_id=organization_id,
        accion_id=accion.id,
        expediente_id=accion.expediente_id,
        tipo_evento="RESULTADO",
        actor_id=user_id,
        correlation_id=accion.correlation_id,
        detalle={"resumen": resultado_resumen[:200]},
    )
    return accion


def get_trazabilidad_acciones(db: Session, expediente_id: str, organization_id: str) -> list[dict[str, Any]]:
    exp_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    acciones = (
        db.query(EvaluacionAccionExterna)
        .filter(
            EvaluacionAccionExterna.expediente_id == expediente_id,
            EvaluacionAccionExterna.organization_id == organization_id,
        )
        .all()
    )
    accion_ids = [a.id for a in acciones]
    eventos = (
        db.query(EvaluacionAccionEvento)
        .filter(EvaluacionAccionEvento.accion_id.in_(accion_ids))
        .order_by(EvaluacionAccionEvento.created_at)
        .all()
        if accion_ids
        else []
    )
    return [
        {
            "accion_id": e.accion_id,
            "tipo_evento": e.tipo_evento,
            "detalle": e.detalle,
            "actor_id": e.actor_id,
            "correlation_id": e.correlation_id,
            "fecha": e.created_at.isoformat() if e.created_at else None,
        }
        for e in eventos
    ]


# --- Indicadores ---

def _indicador_dict(ind: EvaluacionIndicador) -> dict[str, Any]:
    return {
        "id": ind.id,
        "nombre": ind.nombre,
        "unidad": ind.unidad,
        "valor_antes": ind.valor_antes,
        "valor_proyectado": ind.valor_proyectado,
        "valor_real": ind.valor_real,
        "fuente": ind.fuente,
        "visible_entidad": ind.visible_entidad,
        "hallazgo_id": ind.hallazgo_id,
        "notas": ind.notas,
        "tiene_datos_grafico": any([ind.valor_antes, ind.valor_proyectado, ind.valor_real]),
    }


def list_indicadores(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    vista_entidad: bool = False,
) -> list[dict[str, Any]]:
    exp_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    q = db.query(EvaluacionIndicador).filter(
        EvaluacionIndicador.expediente_id == expediente_id,
        EvaluacionIndicador.organization_id == organization_id,
    )
    if vista_entidad:
        q = q.filter(EvaluacionIndicador.visible_entidad.is_(True))
    rows = q.order_by(EvaluacionIndicador.nombre).all()
    return [_indicador_dict(r) for r in rows]


def crear_indicador(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
    nombre: str,
    unidad: str | None = None,
    valor_antes: str | None = None,
    valor_proyectado: str | None = None,
    valor_real: str | None = None,
    hallazgo_id: str | None = None,
    fuente: str = "MANUAL",
    visible_entidad: bool = False,
) -> EvaluacionIndicador:
    exp_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    ind = EvaluacionIndicador(
        organization_id=organization_id,
        expediente_id=expediente_id,
        hallazgo_id=hallazgo_id,
        nombre=nombre,
        unidad=unidad,
        valor_antes=valor_antes,
        valor_proyectado=valor_proyectado,
        valor_real=valor_real,
        fuente=fuente,
        visible_entidad=visible_entidad,
    )
    db.add(ind)
    db.flush()
    return ind


def actualizar_indicador_piiax(
    db: Session,
    indicador_id: str,
    organization_id: str,
    *,
    valor_real: str | None = None,
    valor_proyectado: str | None = None,
    fuente: str = "PIIAX",
) -> EvaluacionIndicador:
    ind = (
        db.query(EvaluacionIndicador)
        .filter(
            EvaluacionIndicador.id == indicador_id,
            EvaluacionIndicador.organization_id == organization_id,
        )
        .first()
    )
    if not ind:
        raise HTTPException(status_code=404, detail="Indicador no encontrado")
    if valor_real is not None:
        ind.valor_real = valor_real
    if valor_proyectado is not None:
        ind.valor_proyectado = valor_proyectado
    ind.fuente = fuente
    ind.updated_at = _utcnow()
    return ind
