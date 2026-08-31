"""Servicio — Implementación y éxito del cliente (1340)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.commercial_models import CommercialProposal
from app.continuidad_comercial_enums import AceptacionEntregable, EstadoEntregable
from app.implementacion_enums import (
    CausaDesviacion,
    EstadoImplementacion,
    EstadoRenovacion,
    EstadoValor,
    ReadinessResultado,
    ResponsabilidadTipo,
    ResultadoPiloto,
    SaludCliente,
    TipoBloqueador,
)
from app.implementacion_models import (
    ExitoClienteExpansion,
    ExitoClienteObjetivo,
    ExitoClientePlan,
    ExitoClientePlanAccion,
    ExitoClienteRenovacion,
    ExitoClienteRevision,
    ExitoClienteSalud,
    ImplementacionAdopcion,
    ImplementacionAlerta,
    ImplementacionAuditoria,
    ImplementacionBloqueador,
    ImplementacionCapacitacion,
    ImplementacionEntregable,
    ImplementacionFase,
    ImplementacionHito,
    ImplementacionPiloto,
    ImplementacionPlanAdopcion,
    ImplementacionProyecto,
    ImplementacionReadiness,
    ImplementacionRequisito,
    ImplementacionRiesgo,
    ImplementacionTarea,
)
from app.services import tco_service


class ImplementacionValidationError(ValueError):
    pass


READINESS_DIMENSIONS = frozenset({
    "DATOS", "TECNOLOGIA", "INTEGRACIONES", "PERSONAL", "GOBIERNO", "SEGURIDAD", "PROCESOS", "APROBACIONES",
})

SALUD_PESOS = {
    "adopcion": Decimal("0.25"),
    "valor": Decimal("0.25"),
    "hitos": Decimal("0.15"),
    "bloqueos": Decimal("0.15"),
    "riesgos": Decimal("0.10"),
    "uso": Decimal("0.10"),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _audit(db: Session, org_id: str, accion: str, entidad: str, entidad_id: str | None, user_id: str | None, detalle: Any = None) -> None:
    db.add(ImplementacionAuditoria(
        organization_id=org_id, accion=accion, entidad=entidad, entidad_id=entidad_id,
        detalle_json=_json(detalle) if detalle else None, user_id=user_id,
    ))


def _ensure_scope(db: Session, org_id: str, entity_org: str) -> None:
    if entity_org != org_id:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")


def _get_proyecto(db: Session, org_id: str, proyecto_id: str) -> ImplementacionProyecto:
    row = db.query(ImplementacionProyecto).filter(ImplementacionProyecto.id == proyecto_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    return row


def _next_codigo(db: Session, org_id: str) -> str:
    n = db.query(func.count(ImplementacionProyecto.id)).filter(ImplementacionProyecto.organization_id == org_id).scalar() or 0
    return f"IMPL-{n + 1:04d}"


def _snapshot_valor_compromiso(db: Session, proposal_id: str | None) -> dict[str, Any] | None:
    if not proposal_id:
        return None
    prop = db.query(CommercialProposal).filter(CommercialProposal.id == proposal_id).first()
    if not prop:
        return None
    return {
        "proposal_id": prop.id,
        "codigo": prop.codigo,
        "valor_total_esperado": float(prop.valor_total_esperado) if prop.valor_total_esperado else None,
        "valor_atribuible_total": float(prop.valor_atribuible_total) if prop.valor_atribuible_total else None,
        "precio_final": float(prop.precio_final) if prop.precio_final else None,
        "precio_sugerido": float(prop.precio_sugerido) if prop.precio_sugerido else None,
        "roi_pct": float(prop.roi_pct) if prop.roi_pct else None,
        "payback_meses": float(prop.payback_meses) if prop.payback_meses else None,
        "margen_pct": float(prop.margen_pct) if prop.margen_pct else None,
        "supuestos": _parse(prop.supuestos_json),
    }


# --- Proyectos ---

def create_proyecto(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionProyecto:
    compromiso = _snapshot_valor_compromiso(db, data.get("proposal_id"))
    row = ImplementacionProyecto(
        organization_id=org_id,
        codigo=_next_codigo(db, org_id),
        titulo=data["titulo"],
        proposal_id=data.get("proposal_id"),
        plan_id=data.get("plan_id"),
        responsable_id=data.get("responsable_id") or user_id,
        fecha_inicio=data.get("fecha_inicio"),
        fecha_objetivo=data.get("fecha_objetivo"),
        alcance=data.get("alcance"),
        objetivos=data.get("objetivos"),
        valor_compromiso_json=_json(compromiso) if compromiso else None,
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "proyecto", row.id, user_id, {"codigo": row.codigo})
    return row


def proyecto_to_dict(row: ImplementacionProyecto) -> dict[str, Any]:
    return {
        "id": row.id, "codigo": row.codigo, "titulo": row.titulo, "estado": row.estado,
        "proposal_id": row.proposal_id, "opportunity_id": row.opportunity_id,
        "evaluacion_id": row.evaluacion_id, "contract_id": row.contract_id,
        "version_contratada": row.version_contratada, "documento_contrato_id": row.documento_contrato_id,
        "finops_budget_id": row.finops_budget_id,
        "plan_id": row.plan_id, "responsable_id": row.responsable_id,
        "fecha_inicio": row.fecha_inicio.isoformat() if row.fecha_inicio else None,
        "fecha_objetivo": row.fecha_objetivo.isoformat() if row.fecha_objetivo else None,
        "alcance": row.alcance, "objetivos": row.objetivos, "avance_pct": float(row.avance_pct),
        "valor_compromiso": _parse(row.valor_compromiso_json),
        "compromiso_contractual": _parse(row.compromiso_contractual_json),
        "go_live_aprobado": row.go_live_aprobado,
        "go_live_fecha": row.go_live_fecha.isoformat() if row.go_live_fecha else None,
    }


def list_proyectos(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(ImplementacionProyecto).filter(ImplementacionProyecto.organization_id == org_id).order_by(ImplementacionProyecto.created_at.desc()).all()
    return [proyecto_to_dict(r) for r in rows]


def update_proyecto(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionProyecto:
    row = _get_proyecto(db, org_id, proyecto_id)
    if data.get("estado"):
        if data["estado"] not in EstadoImplementacion.ALL:
            raise ImplementacionValidationError(f"Estado inválido: {data['estado']}")
        old = row.estado
        row.estado = data["estado"]
        _audit(db, org_id, "CAMBIO_FASE", "proyecto", row.id, user_id, {"de": old, "a": row.estado})
    if data.get("avance_pct") is not None:
        row.avance_pct = Decimal(str(data["avance_pct"]))
    if data.get("alcance") is not None:
        row.alcance = data["alcance"]
    if data.get("objetivos") is not None:
        row.objetivos = data["objetivos"]
    db.flush()
    return row


# --- Fases ---

def create_fase(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionFase:
    _get_proyecto(db, org_id, proyecto_id)
    resp = data.get("responsabilidad", ResponsabilidadTipo.NUESTRO_EQUIPO)
    if resp not in ResponsabilidadTipo.ALL:
        raise ImplementacionValidationError(f"Responsabilidad inválida: {resp}")
    row = ImplementacionFase(
        proyecto_id=proyecto_id, organization_id=org_id, nombre=data["nombre"], orden=data.get("orden", 0),
        responsable_id=data.get("responsable_id"), responsabilidad=resp,
        fecha_inicio=data.get("fecha_inicio"), fecha_fin=data.get("fecha_fin"),
        criterio_entrada=data.get("criterio_entrada"), criterio_salida=data.get("criterio_salida"),
        dependencias_json=_json(data.get("dependencias")),
    )
    db.add(row)
    db.flush()
    return row


def fase_to_dict(r: ImplementacionFase) -> dict[str, Any]:
    return {"id": r.id, "nombre": r.nombre, "orden": r.orden, "estado": r.estado, "responsabilidad": r.responsabilidad}


# --- Hitos ---

def create_hito(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionHito:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionHito(
        proyecto_id=proyecto_id, organization_id=org_id,
        codigo=data.get("codigo") or f"HITO-{data['nombre'][:20].upper().replace(' ', '_')}",
        nombre=data["nombre"], fase_id=data.get("fase_id"),
        responsable_id=data.get("responsable_id"), responsabilidad=data.get("responsabilidad", ResponsabilidadTipo.NUESTRO_EQUIPO),
        proveedor_id=data.get("proveedor_id"), fecha_objetivo=data.get("fecha_objetivo"),
        dependencias_json=_json(data.get("dependencias")),
    )
    db.add(row)
    db.flush()
    return row


def completar_hito(db: Session, org_id: str, hito_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionHito:
    row = db.query(ImplementacionHito).filter(ImplementacionHito.id == hito_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Hito no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    deps = _parse(row.dependencias_json) or []
    if deps:
        pending = (
            db.query(ImplementacionHito)
            .filter(
                ImplementacionHito.proyecto_id == row.proyecto_id,
                ImplementacionHito.codigo.in_(deps),
                ImplementacionHito.estado != "COMPLETADO",
            )
            .count()
        )
        if pending:
            raise ImplementacionValidationError(f"Dependencias pendientes: {deps}")
    row.estado = "COMPLETADO"
    row.evidencia = data.get("evidencia")
    row.fecha_real = data.get("fecha_real") or _utcnow()
    db.flush()
    _audit(db, org_id, "CIERRE_HITO", "hito", row.id, user_id, {"nombre": row.nombre})
    _recalcular_avance(db, row.proyecto_id)
    return row


def _recalcular_avance(db: Session, proyecto_id: str) -> None:
    total = db.query(func.count(ImplementacionHito.id)).filter(ImplementacionHito.proyecto_id == proyecto_id).scalar() or 0
    if total == 0:
        return
    done = db.query(func.count(ImplementacionHito.id)).filter(
        ImplementacionHito.proyecto_id == proyecto_id, ImplementacionHito.estado == "COMPLETADO",
    ).scalar() or 0
    proj = db.query(ImplementacionProyecto).filter(ImplementacionProyecto.id == proyecto_id).first()
    if proj:
        proj.avance_pct = Decimal(str(round(done / total * 100, 2)))


# --- Tareas ---

def create_tarea(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionTarea:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionTarea(
        proyecto_id=proyecto_id, organization_id=org_id, titulo=data["titulo"], descripcion=data.get("descripcion"),
        fase_id=data.get("fase_id"), responsable_id=data.get("responsable_id"),
        responsabilidad=data.get("responsabilidad", ResponsabilidadTipo.NUESTRO_EQUIPO),
        proveedor_id=data.get("proveedor_id"), prioridad=data.get("prioridad", "MEDIA"),
        fecha_objetivo=data.get("fecha_objetivo"), dependencias_json=_json(data.get("dependencias")),
    )
    db.add(row)
    db.flush()
    return row


def tarea_to_dict(r: ImplementacionTarea) -> dict[str, Any]:
    return {
        "id": r.id, "titulo": r.titulo, "estado": r.estado, "prioridad": r.prioridad,
        "responsabilidad": r.responsabilidad, "evidencia": r.evidencia,
    }


def completar_tarea(db: Session, org_id: str, tarea_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionTarea:
    row = db.query(ImplementacionTarea).filter(ImplementacionTarea.id == tarea_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    _ensure_scope(db, org_id, row.organization_id)
    row.estado = "COMPLETADA"
    row.evidencia = data.get("evidencia") or row.evidencia
    row.resultado = data.get("resultado") or row.resultado
    db.flush()
    _audit(db, org_id, "COMPLETAR_TAREA", "tarea", row.id, user_id, {"titulo": row.titulo})
    return row


# --- Requisitos ---

def create_requisito(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionRequisito:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionRequisito(
        proyecto_id=proyecto_id, organization_id=org_id, tipo=data["tipo"], descripcion=data["descripcion"],
        responsable_id=data.get("responsable_id"), responsabilidad=data.get("responsabilidad", ResponsabilidadTipo.CLIENTE),
        proveedor_id=data.get("proveedor_id"), fecha_requerida=data.get("fecha_requerida"),
        bloqueante=bool(data.get("bloqueante")),
    )
    db.add(row)
    db.flush()
    if row.bloqueante:
        _crear_alerta(db, org_id, proyecto_id, "REQUISITO_BLOQUEANTE", f"Requisito bloqueante pendiente: {row.descripcion}")
    return row


def requisito_to_dict(r: ImplementacionRequisito) -> dict[str, Any]:
    return {"id": r.id, "tipo": r.tipo, "descripcion": r.descripcion, "estado": r.estado, "bloqueante": r.bloqueante}


def completar_requisito(db: Session, org_id: str, requisito_id: str, user_id: str | None) -> ImplementacionRequisito:
    row = db.query(ImplementacionRequisito).filter(ImplementacionRequisito.id == requisito_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    row.estado = "COMPLETADO"
    row.fecha_recibida = _utcnow()
    db.flush()
    _audit(db, org_id, "COMPLETAR_REQUISITO", "requisito", row.id, user_id, {})
    return row


# --- Readiness ---

def evaluar_readiness(db: Session, org_id: str, proyecto_id: str, dimensiones: dict[str, Any], user_id: str | None) -> ImplementacionReadiness:
    _get_proyecto(db, org_id, proyecto_id)
    no_listo = []
    observaciones = []
    for dim, val in dimensiones.items():
        if dim.upper() not in READINESS_DIMENSIONS:
            continue
        score = val if isinstance(val, (int, float)) else (1 if val else 0)
        if score < 0.5:
            no_listo.append(dim)
        elif score < 0.8:
            observaciones.append(dim)
    if no_listo:
        resultado = ReadinessResultado.NO_LISTO
        explicacion = f"No listo. Dimensiones insuficientes: {', '.join(no_listo)}"
    elif observaciones:
        resultado = ReadinessResultado.LISTO_CON_OBSERVACIONES
        explicacion = f"Listo con observaciones en: {', '.join(observaciones)}"
    else:
        resultado = ReadinessResultado.LISTO
        explicacion = "Cliente listo para iniciar implementación"
    row = ImplementacionReadiness(
        proyecto_id=proyecto_id, organization_id=org_id, dimensiones_json=_json(dimensiones),
        resultado=resultado, explicacion=explicacion, evaluado_por=user_id,
    )
    db.add(row)
    db.flush()
    return row


# --- Bloqueadores ---

def create_bloqueador(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionBloqueador:
    _get_proyecto(db, org_id, proyecto_id)
    tipo = data.get("tipo", TipoBloqueador.OTRO)
    if tipo not in TipoBloqueador.ALL:
        raise ImplementacionValidationError(f"Tipo bloqueador inválido: {tipo}")
    row = ImplementacionBloqueador(
        proyecto_id=proyecto_id, organization_id=org_id, tipo=tipo, descripcion=data["descripcion"],
        impacto=data.get("impacto", "ALTO"), responsable_id=data.get("responsable_id"),
        accion=data.get("accion"), critico=bool(data.get("critico")),
    )
    db.add(row)
    db.flush()
    if row.critico:
        _crear_alerta(db, org_id, proyecto_id, "BLOQUEADOR_CRITICO", row.descripcion)
    _audit(db, org_id, "BLOQUEADOR", "bloqueador", row.id, user_id, {"tipo": tipo})
    return row


def bloqueador_to_dict(r: ImplementacionBloqueador) -> dict[str, Any]:
    return {"id": r.id, "tipo": r.tipo, "descripcion": r.descripcion, "estado": r.estado, "critico": r.critico}


def resolver_bloqueador(db: Session, org_id: str, bloqueador_id: str, user_id: str | None, observaciones: str | None = None) -> ImplementacionBloqueador:
    row = db.query(ImplementacionBloqueador).filter(ImplementacionBloqueador.id == bloqueador_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bloqueador no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    row.estado = "RESUELTO"
    row.resuelto_at = _utcnow()
    if observaciones:
        row.accion = observaciones
    db.flush()
    _audit(db, org_id, "RESOLVER_BLOQUEADOR", "bloqueador", row.id, user_id, {})
    return row


# --- Riesgos ---

def create_riesgo(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionRiesgo:
    _get_proyecto(db, org_id, proyecto_id)
    prob_map = {"BAJA": 1, "MEDIA": 2, "ALTA": 3}
    imp_map = {"BAJO": 1, "MEDIO": 2, "ALTO": 3}
    p = prob_map.get(data.get("probabilidad", "MEDIA"), 2)
    i = imp_map.get(data.get("impacto", "MEDIO"), 2)
    nivel_score = p * i
    nivel = "BAJO" if nivel_score <= 2 else ("ALTO" if nivel_score >= 6 else "MEDIO")
    row = ImplementacionRiesgo(
        proyecto_id=proyecto_id, organization_id=org_id, descripcion=data["descripcion"],
        probabilidad=data.get("probabilidad", "MEDIA"), impacto=data.get("impacto", "MEDIO"), nivel=nivel,
        mitigacion=data.get("mitigacion"), responsable_id=data.get("responsable_id"),
        referencia_externa=data.get("referencia_externa"),
    )
    db.add(row)
    db.flush()
    if nivel == "ALTO":
        _crear_alerta(db, org_id, proyecto_id, "RIESGO_ALTO", row.descripcion)
    return row


# --- Piloto ---

def create_piloto(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionPiloto:
    proj = _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionPiloto(
        proyecto_id=proyecto_id, organization_id=org_id, alcance=data.get("alcance"),
        usuarios_json=_json(data.get("usuarios")), procesos_json=_json(data.get("procesos")),
        empleados_ia_json=_json(data.get("empleados_ia")), duracion_dias=data.get("duracion_dias"),
        metricas_objetivo_json=_json(data.get("metricas_objetivo")),
        criterios_exito=data.get("criterios_exito"), criterios_suspension=data.get("criterios_suspension"),
    )
    db.add(row)
    proj.estado = EstadoImplementacion.PILOTO
    db.flush()
    return row


def registrar_resultado_piloto(db: Session, org_id: str, piloto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionPiloto:
    row = db.query(ImplementacionPiloto).filter(ImplementacionPiloto.id == piloto_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Piloto no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    resultado = data["resultado"]
    if resultado not in ResultadoPiloto.ALL:
        raise ImplementacionValidationError(f"Resultado piloto inválido: {resultado}")
    row.resultado = resultado
    row.resultado_explicacion = data.get("explicacion")
    row.evidencia = data.get("evidencia")
    row.estado = "CONCLUIDO"
    if resultado == ResultadoPiloto.NO_CONCLUYENTE:
        _crear_alerta(db, org_id, row.proyecto_id, "PILOTO_NO_CONCLUYENTE", row.resultado_explicacion or "Piloto no concluyente")
    db.flush()
    _audit(db, org_id, "APROBACION_PILOTO", "piloto", row.id, user_id, {"resultado": resultado})
    return row


def aprobar_piloto_produccion(db: Session, org_id: str, piloto_id: str, user_id: str | None, observaciones: str | None = None) -> ImplementacionPiloto:
    row = db.query(ImplementacionPiloto).filter(ImplementacionPiloto.id == piloto_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Piloto no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    if row.resultado not in (ResultadoPiloto.EXITOSO, ResultadoPiloto.EXITOSO_CON_AJUSTES):
        raise ImplementacionValidationError("Solo se puede aprobar producción con piloto exitoso o con ajustes")
    row.aprobado_produccion = True
    row.aprobado_por = user_id
    row.aprobado_at = _utcnow()
    proj = _get_proyecto(db, org_id, row.proyecto_id)
    proj.estado = EstadoImplementacion.VALIDACION
    db.flush()
    _audit(db, org_id, "APROBACION_PILOTO", "piloto", row.id, user_id, {"observaciones": observaciones})
    return row


# --- Go-live ---

GO_LIVE_ITEMS = frozenset({
    "configuracion", "usuarios", "permisos", "integraciones", "seguridad",
    "datos", "monitoreo", "soporte", "respaldo", "documentacion", "capacitacion",
})


def aprobar_go_live(db: Session, org_id: str, proyecto_id: str, checklist: dict[str, bool], user_id: str | None, observaciones: str | None = None) -> ImplementacionProyecto:
    proj = _get_proyecto(db, org_id, proyecto_id)
    criticos = db.query(ImplementacionBloqueador).filter(
        ImplementacionBloqueador.proyecto_id == proyecto_id,
        ImplementacionBloqueador.estado == "ABIERTO", ImplementacionBloqueador.critico.is_(True),
    ).count()
    if criticos > 0:
        raise ImplementacionValidationError(f"No se puede aprobar go-live: {criticos} bloqueador(es) crítico(s) abierto(s)")
    req_bloq = db.query(ImplementacionRequisito).filter(
        ImplementacionRequisito.proyecto_id == proyecto_id,
        ImplementacionRequisito.bloqueante.is_(True), ImplementacionRequisito.estado != "COMPLETADO",
    ).count()
    if req_bloq > 0:
        raise ImplementacionValidationError(f"No se puede aprobar go-live: {req_bloq} requisito(s) bloqueante(s) pendiente(s)")
    faltantes = [k for k in GO_LIVE_ITEMS if not checklist.get(k)]
    if faltantes:
        raise ImplementacionValidationError(f"Checklist incompleto: {', '.join(faltantes)}")
    piloto_ok = db.query(ImplementacionPiloto).filter(
        ImplementacionPiloto.proyecto_id == proyecto_id, ImplementacionPiloto.aprobado_produccion.is_(True),
    ).first()
    if not piloto_ok:
        raise ImplementacionValidationError("Se requiere aprobación de piloto antes de go-live")
    proj.go_live_aprobado = True
    proj.go_live_fecha = _utcnow()
    proj.go_live_aprobado_por = user_id
    proj.go_live_checklist_json = _json(checklist)
    proj.go_live_observaciones = observaciones
    proj.estado = EstadoImplementacion.EN_PRODUCCION
    db.flush()
    _audit(db, org_id, "APROBACION_PRODUCCION", "proyecto", proj.id, user_id, {"checklist": checklist})
    return proj


# --- Adopción ---

def registrar_adopcion(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionAdopcion:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionAdopcion(
        proyecto_id=proyecto_id, organization_id=org_id,
        periodo=data.get("periodo"), metricas_json=_json(data.get("metricas", {})),
    )
    db.add(row)
    db.flush()
    metricas = data.get("metricas", {})
    hab = metricas.get("usuarios_habilitados", 0)
    act = metricas.get("usuarios_activos", 0)
    if hab and act / hab < 0.3:
        _crear_alerta(db, org_id, proyecto_id, "BAJA_ADOPCION", f"Adopción baja: {act}/{hab} usuarios activos")
    return row


def create_plan_adopcion(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionPlanAdopcion:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionPlanAdopcion(
        proyecto_id=proyecto_id, organization_id=org_id, tipo_accion=data["tipo_accion"],
        descripcion=data["descripcion"], responsable_id=data.get("responsable_id"),
        fecha_objetivo=data.get("fecha_objetivo"),
    )
    db.add(row)
    db.flush()
    return row


def create_capacitacion(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionCapacitacion:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionCapacitacion(
        proyecto_id=proyecto_id, organization_id=org_id, tema=data["tema"], grupo=data.get("grupo"),
        fecha=data.get("fecha"), asistentes=data.get("asistentes"),
        responsable_id=user_id, resultado=data.get("resultado"), evidencia=data.get("evidencia"),
    )
    db.add(row)
    db.flush()
    return row


# --- Éxito del cliente ---

def create_plan_exito(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ExitoClientePlan:
    proj = _get_proyecto(db, org_id, data["proyecto_id"])
    compromiso = _parse(proj.valor_compromiso_json)
    row = ExitoClientePlan(
        organization_id=org_id, proyecto_id=data["proyecto_id"], titulo=data["titulo"],
        valor_esperado=Decimal(str(data["valor_esperado"])) if data.get("valor_esperado") else None,
        valor_compromiso_json=proj.valor_compromiso_json,
        periodicidad_revision=data.get("periodicidad_revision", "MENSUAL"),
        responsable_id=data.get("responsable_id") or user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "plan_exito", row.id, user_id, {"titulo": row.titulo})
    return row


def create_objetivo(db: Session, org_id: str, plan_id: str, data: dict[str, Any], user_id: str | None) -> ExitoClienteObjetivo:
    plan = db.query(ExitoClientePlan).filter(ExitoClientePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    _ensure_scope(db, org_id, plan.organization_id)
    row = ExitoClienteObjetivo(
        plan_id=plan_id, organization_id=org_id, nombre=data["nombre"], indicador=data.get("indicador"),
        valor_esperado=Decimal(str(data["valor_esperado"])) if data.get("valor_esperado") else None,
        opportunity_id=data.get("opportunity_id"),
    )
    db.add(row)
    db.flush()
    return row


def medir_objetivo(db: Session, org_id: str, objetivo_id: str, valor_medido: float, user_id: str | None) -> ExitoClienteObjetivo:
    row = db.query(ExitoClienteObjetivo).filter(ExitoClienteObjetivo.id == objetivo_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    row.valor_medido = Decimal(str(valor_medido))
    if row.valor_esperado is None or row.valor_esperado == 0:
        row.estado_valor = EstadoValor.NO_MEDIDO
    else:
        pct = float(row.valor_medido / row.valor_esperado * 100)
        if pct < 80:
            row.estado_valor = EstadoValor.POR_DEBAJO
        elif pct > 120:
            row.estado_valor = EstadoValor.POR_ENCIMA
        else:
            row.estado_valor = EstadoValor.EN_LINEA
    db.flush()
    if row.estado_valor == EstadoValor.POR_DEBAJO:
        plan = db.query(ExitoClientePlan).filter(ExitoClientePlan.id == row.plan_id).first()
        if plan:
            _crear_alerta(db, org_id, plan.proyecto_id, "VALOR_DEBAJO_ESPERADO", f"Objetivo {row.nombre} por debajo del esperado")
    return row


def create_plan_accion(db: Session, org_id: str, plan_id: str, data: dict[str, Any], user_id: str | None) -> ExitoClientePlanAccion:
    plan = db.query(ExitoClientePlan).filter(ExitoClientePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    _ensure_scope(db, org_id, plan.organization_id)
    causa = data.get("causa", CausaDesviacion.OTRO)
    if causa not in CausaDesviacion.ALL:
        raise ImplementacionValidationError(f"Causa inválida: {causa}")
    row = ExitoClientePlanAccion(
        plan_id=plan_id, organization_id=org_id, objetivo_id=data.get("objetivo_id"),
        causa=causa, accion=data["accion"], responsable_id=data.get("responsable_id"),
        fecha_objetivo=data.get("fecha_objetivo"), impacto_esperado=data.get("impacto_esperado"),
    )
    db.add(row)
    db.flush()
    return row


def create_revision(db: Session, org_id: str, plan_id: str, data: dict[str, Any], user_id: str | None) -> ExitoClienteRevision:
    plan = db.query(ExitoClientePlan).filter(ExitoClientePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    _ensure_scope(db, org_id, plan.organization_id)
    row = ExitoClienteRevision(
        plan_id=plan_id, organization_id=org_id, fecha=data["fecha"],
        periodicidad=data.get("periodicidad", "MENSUAL"),
        indicadores_json=_json(data.get("indicadores")),
        valor_json=_json(data.get("valor")), riesgos_json=_json(data.get("riesgos")),
        bloqueos_json=_json(data.get("bloqueos")), acciones_json=_json(data.get("acciones")),
        decisiones=data.get("decisiones"), revisado_por=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "REVISION", "plan_exito", plan_id, user_id, {"fecha": data["fecha"].isoformat()})
    return row


# --- Salud ---

def calcular_salud(db: Session, org_id: str, proyecto_id: str, user_id: str | None) -> dict[str, Any]:
    proj = _get_proyecto(db, org_id, proyecto_id)
    factores: list[dict[str, Any]] = []

    adop = db.query(ImplementacionAdopcion).filter(ImplementacionAdopcion.proyecto_id == proyecto_id).order_by(ImplementacionAdopcion.created_at.desc()).first()
    adop_score = Decimal("0.5")
    if adop:
        m = _parse(adop.metricas_json) or {}
        hab, act = m.get("usuarios_habilitados", 0), m.get("usuarios_activos", 0)
        adop_score = Decimal(str(min(1.0, act / hab))) if hab else Decimal("0.3")
    factores.append({"factor": "adopcion", "peso": float(SALUD_PESOS["adopcion"]), "valor": float(adop_score), "razon": "Usuarios activos vs habilitados"})

    objetivos = db.query(ExitoClienteObjetivo).join(ExitoClientePlan).filter(ExitoClientePlan.proyecto_id == proyecto_id).all()
    valor_score = Decimal("0.5")
    if objetivos:
        ok = sum(1 for o in objetivos if o.estado_valor in (EstadoValor.EN_LINEA, EstadoValor.POR_ENCIMA))
        valor_score = Decimal(str(ok / len(objetivos)))
    factores.append({"factor": "valor", "peso": float(SALUD_PESOS["valor"]), "valor": float(valor_score), "razon": "Objetivos en línea o por encima"})

    hitos_total = db.query(func.count(ImplementacionHito.id)).filter(ImplementacionHito.proyecto_id == proyecto_id).scalar() or 0
    hitos_ok = db.query(func.count(ImplementacionHito.id)).filter(ImplementacionHito.proyecto_id == proyecto_id, ImplementacionHito.estado == "COMPLETADO").scalar() or 0
    hitos_score = Decimal(str(hitos_ok / hitos_total)) if hitos_total else Decimal("0.5")
    factores.append({"factor": "hitos", "peso": float(SALUD_PESOS["hitos"]), "valor": float(hitos_score), "razon": "Hitos completados"})

    bloq_abiertos = db.query(func.count(ImplementacionBloqueador.id)).filter(
        ImplementacionBloqueador.proyecto_id == proyecto_id, ImplementacionBloqueador.estado == "ABIERTO",
    ).scalar() or 0
    bloq_score = Decimal("1") if bloq_abiertos == 0 else Decimal(str(max(0, 1 - bloq_abiertos * 0.25)))
    factores.append({"factor": "bloqueos", "peso": float(SALUD_PESOS["bloqueos"]), "valor": float(bloq_score), "razon": f"{bloq_abiertos} bloqueador(es) abierto(s)"})

    riesgos_altos = db.query(func.count(ImplementacionRiesgo.id)).filter(
        ImplementacionRiesgo.proyecto_id == proyecto_id, ImplementacionRiesgo.nivel == "ALTO", ImplementacionRiesgo.estado == "ABIERTO",
    ).scalar() or 0
    riesgo_score = Decimal("1") if riesgos_altos == 0 else Decimal("0.3")
    factores.append({"factor": "riesgos", "peso": float(SALUD_PESOS["riesgos"]), "valor": float(riesgo_score), "razon": f"{riesgos_altos} riesgo(s) alto(s)"})

    uso_score = adop_score
    factores.append({"factor": "uso", "peso": float(SALUD_PESOS["uso"]), "valor": float(uso_score), "razon": "Frecuencia de uso estimada"})

    puntuacion = sum(Decimal(str(f["peso"])) * Decimal(str(f["valor"])) for f in factores) * Decimal("100")
    if puntuacion >= 75:
        resultado = SaludCliente.SALUDABLE
    elif puntuacion >= 50:
        resultado = SaludCliente.ATENCION
    else:
        resultado = SaludCliente.RIESGO
    explicacion = f"Salud {resultado}: puntuación {float(puntuacion):.1f}/100"
    snap = ExitoClienteSalud(
        organization_id=org_id, proyecto_id=proyecto_id, resultado=resultado,
        puntuacion=puntuacion, factores_json=_json(factores), explicacion=explicacion,
    )
    db.add(snap)
    db.flush()
    _audit(db, org_id, "SALUD", "proyecto", proyecto_id, user_id, {"resultado": resultado, "puntuacion": float(puntuacion)})
    return {"resultado": resultado, "puntuacion": float(puntuacion), "factores": factores, "explicacion": explicacion}


# --- Entregables ---

def create_entregable(db: Session, org_id: str, proyecto_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionEntregable:
    _get_proyecto(db, org_id, proyecto_id)
    row = ImplementacionEntregable(
        proyecto_id=proyecto_id,
        organization_id=org_id,
        nombre=data["nombre"],
        descripcion=data.get("descripcion"),
        responsable_id=data.get("responsable_id") or user_id,
        fecha_objetivo=data.get("fecha_objetivo"),
        estado=data.get("estado", EstadoEntregable.PENDIENTE),
        documento_id=data.get("documento_id"),
        version_referencia=data.get("version_referencia"),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR_ENTREGABLE", "entregable", row.id, user_id, {"nombre": row.nombre})
    return row


def entregable_to_dict(r: ImplementacionEntregable) -> dict[str, Any]:
    return {
        "id": r.id,
        "nombre": r.nombre,
        "descripcion": r.descripcion,
        "responsable_id": r.responsable_id,
        "fecha_objetivo": r.fecha_objetivo.isoformat() if r.fecha_objetivo else None,
        "estado": r.estado,
        "evidencia": r.evidencia,
        "documento_id": r.documento_id,
        "aceptacion": r.aceptacion,
        "observaciones": r.observaciones,
        "version_referencia": r.version_referencia,
    }


def update_entregable(db: Session, org_id: str, entregable_id: str, data: dict[str, Any], user_id: str | None) -> ImplementacionEntregable:
    row = db.query(ImplementacionEntregable).filter(ImplementacionEntregable.id == entregable_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Entregable no encontrado")
    _ensure_scope(db, org_id, row.organization_id)
    for field in ("nombre", "descripcion", "responsable_id", "fecha_objetivo", "estado", "evidencia", "documento_id", "observaciones", "version_referencia"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    if data.get("aceptacion") in AceptacionEntregable.ALL:
        row.aceptacion = data["aceptacion"]
        if row.aceptacion == AceptacionEntregable.ACEPTADO:
            row.estado = EstadoEntregable.ACEPTADO
        elif row.aceptacion == AceptacionEntregable.RECHAZADO:
            row.estado = EstadoEntregable.RECHAZADO
    row.updated_at = _utcnow()
    db.flush()
    _audit(db, org_id, "ACTUALIZAR_ENTREGABLE", "entregable", row.id, user_id, {"estado": row.estado})
    return row


def list_entregables(db: Session, org_id: str, proyecto_id: str) -> list[dict[str, Any]]:
    _get_proyecto(db, org_id, proyecto_id)
    rows = db.query(ImplementacionEntregable).filter(ImplementacionEntregable.proyecto_id == proyecto_id).all()
    return [entregable_to_dict(r) for r in rows]


# --- Renovación / Expansión ---

def create_renovacion(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ExitoClienteRenovacion:
    proj = _get_proyecto(db, org_id, data["proyecto_id"])
    salud = db.query(ExitoClienteSalud).filter(ExitoClienteSalud.proyecto_id == data["proyecto_id"]).order_by(ExitoClienteSalud.created_at.desc()).first()
    row = ExitoClienteRenovacion(
        organization_id=org_id, proyecto_id=data["proyecto_id"], plan_id=data.get("plan_id"),
        fecha_renovacion=data.get("fecha_renovacion"), estado=data.get("estado", EstadoRenovacion.PENDIENTE),
        salud=salud.resultado if salud else None, notas=data.get("notas"),
        opportunity_id=data.get("opportunity_id"),
    )
    if data.get("crear_oportunidad"):
        from app.services import continuidad_comercial_service as cont_svc

        opp = cont_svc.create_opportunity_from_continuidad(
            db, org_id,
            titulo=data.get("titulo_oportunidad") or f"Renovación — {proj.titulo}",
            descripcion=data.get("notas") or "Renovación detectada desde implementación",
            tipo="RENOVACION",
            proyecto_id=proj.id,
            proposal_id=proj.proposal_id,
            origen="RENOVACION",
        )
        row.opportunity_id = opp.id
    db.add(row)
    db.flush()
    _audit(db, org_id, "RENOVACION", "renovacion", row.id, user_id, {"opportunity_id": row.opportunity_id})
    return row


def create_expansion(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ExitoClienteExpansion:
    proj = _get_proyecto(db, org_id, data["proyecto_id"])
    row = ExitoClienteExpansion(
        organization_id=org_id, proyecto_id=data["proyecto_id"], tipo=data["tipo"],
        descripcion=data["descripcion"], recomendacion=data.get("recomendacion"),
        opportunity_id=data.get("opportunity_id"),
    )
    if data.get("crear_oportunidad"):
        from app.services import continuidad_comercial_service as cont_svc

        opp = cont_svc.create_opportunity_from_continuidad(
            db, org_id,
            titulo=data.get("titulo_oportunidad") or f"Ampliación — {data['tipo']}",
            descripcion=data["descripcion"],
            tipo="EXPANSION",
            proyecto_id=proj.id,
            proposal_id=proj.proposal_id,
            origen="EXPANSION",
        )
        row.opportunity_id = opp.id
    db.add(row)
    db.flush()
    _audit(db, org_id, "EXPANSION", "expansion", row.id, user_id, {"tipo": data["tipo"], "opportunity_id": row.opportunity_id})
    return row


def update_renovacion_estado(db: Session, org_id: str, renovacion_id: str, estado: str, user_id: str | None) -> ExitoClienteRenovacion:
    row = db.query(ExitoClienteRenovacion).filter(
        ExitoClienteRenovacion.id == renovacion_id,
        ExitoClienteRenovacion.organization_id == org_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Renovación no encontrada")
    row.estado = estado
    db.flush()
    return row


# --- Alertas ---

def _crear_alerta(db: Session, org_id: str, proyecto_id: str, tipo: str, mensaje: str, severidad: str = "ALTA") -> None:
    db.add(ImplementacionAlerta(organization_id=org_id, proyecto_id=proyecto_id, tipo=tipo, mensaje=mensaje, severidad=severidad))


# --- Tablero / Trazabilidad ---

def tablero_proyecto(db: Session, org_id: str, proyecto_id: str) -> dict[str, Any]:
    proj = _get_proyecto(db, org_id, proyecto_id)
    fases = db.query(ImplementacionFase).filter(ImplementacionFase.proyecto_id == proyecto_id).order_by(ImplementacionFase.orden).all()
    hitos = db.query(ImplementacionHito).filter(ImplementacionHito.proyecto_id == proyecto_id).all()
    bloqueadores = db.query(ImplementacionBloqueador).filter(ImplementacionBloqueador.proyecto_id == proyecto_id, ImplementacionBloqueador.estado == "ABIERTO").all()
    riesgos = db.query(ImplementacionRiesgo).filter(ImplementacionRiesgo.proyecto_id == proyecto_id, ImplementacionRiesgo.estado == "ABIERTO").all()
    adop = db.query(ImplementacionAdopcion).filter(ImplementacionAdopcion.proyecto_id == proyecto_id).order_by(ImplementacionAdopcion.created_at.desc()).first()
    plan = db.query(ExitoClientePlan).filter(ExitoClientePlan.proyecto_id == proyecto_id).first()
    salud = db.query(ExitoClienteSalud).filter(ExitoClienteSalud.proyecto_id == proyecto_id).order_by(ExitoClienteSalud.created_at.desc()).first()
    renov = db.query(ExitoClienteRenovacion).filter(ExitoClienteRenovacion.proyecto_id == proyecto_id).order_by(ExitoClienteRenovacion.created_at.desc()).first()
    alertas = db.query(ImplementacionAlerta).filter(ImplementacionAlerta.proyecto_id == proyecto_id, ImplementacionAlerta.resuelta.is_(False)).limit(10).all()

    tco_resumen = None
    try:
        tco_resumen = tco_service.calcular_tco(db, org_id, {"tipo": "ESTIMADO", "incluir_finops": True, "proposal_id": proj.proposal_id}, None)
    except Exception:
        pass

    objetivos_valor = []
    if plan:
        objs = db.query(ExitoClienteObjetivo).filter(ExitoClienteObjetivo.plan_id == plan.id).all()
        objetivos_valor = [{"nombre": o.nombre, "esperado": float(o.valor_esperado) if o.valor_esperado else None, "medido": float(o.valor_medido) if o.valor_medido else None, "estado": o.estado_valor} for o in objs]

    return {
        "proyecto": proyecto_to_dict(proj),
        "fase_actual": next((f.nombre for f in fases if f.estado != "COMPLETADO"), fases[-1].nombre if fases else None),
        "avance_pct": float(proj.avance_pct),
        "hitos": {"total": len(hitos), "completados": sum(1 for h in hitos if h.estado == "COMPLETADO"), "atrasados": sum(1 for h in hitos if h.fecha_objetivo and h.fecha_objetivo < _utcnow() and h.estado != "COMPLETADO")},
        "bloqueadores": [bloqueador_to_dict(b) for b in bloqueadores],
        "riesgos": [{"descripcion": r.descripcion, "nivel": r.nivel} for r in riesgos],
        "adopcion": _parse(adop.metricas_json) if adop else None,
        "valor_esperado": float(plan.valor_esperado) if plan and plan.valor_esperado else _parse(proj.valor_compromiso_json),
        "objetivos_valor": objetivos_valor,
        "salud": {"resultado": salud.resultado, "puntuacion": float(salud.puntuacion)} if salud else None,
        "proxima_revision": plan.proxima_revision.isoformat() if plan and plan.proxima_revision else None,
        "renovacion": {"estado": renov.estado, "fecha": renov.fecha_renovacion.isoformat() if renov and renov.fecha_renovacion else None} if renov else None,
        "tco": {"total": tco_resumen["total"], "margen_pct": tco_resumen.get("margen_pct")} if tco_resumen else None,
        "alertas": [{"tipo": a.tipo, "mensaje": a.mensaje} for a in alertas],
        "trazabilidad": {
            "que_vendimos": _parse(proj.valor_compromiso_json),
            "que_prometimos": proj.objetivos,
            "que_implementamos": proj.alcance,
            "fase_actual": proj.estado,
            "go_live": proj.go_live_aprobado,
        },
    }


def detalle_proyecto(db: Session, org_id: str, proyecto_id: str) -> dict[str, Any]:
    proj = _get_proyecto(db, org_id, proyecto_id)
    return {
        **proyecto_to_dict(proj),
        "fases": [fase_to_dict(f) for f in db.query(ImplementacionFase).filter(ImplementacionFase.proyecto_id == proyecto_id).order_by(ImplementacionFase.orden).all()],
        "hitos": [{"id": h.id, "codigo": h.codigo, "nombre": h.nombre, "estado": h.estado, "proveedor_id": h.proveedor_id} for h in db.query(ImplementacionHito).filter(ImplementacionHito.proyecto_id == proyecto_id).all()],
        "tareas": [tarea_to_dict(t) for t in db.query(ImplementacionTarea).filter(ImplementacionTarea.proyecto_id == proyecto_id).all()],
        "entregables": list_entregables(db, org_id, proyecto_id),
        "requisitos": [requisito_to_dict(r) for r in db.query(ImplementacionRequisito).filter(ImplementacionRequisito.proyecto_id == proyecto_id).all()],
        "tablero": tablero_proyecto(db, org_id, proyecto_id),
    }
