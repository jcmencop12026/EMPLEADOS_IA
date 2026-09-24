"""Servicio — Continuidad operativa y resiliencia (1360)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.continuidad_enums import (
    CausaRaiz,
    Criticidad,
    EstadoBackup,
    EstadoIncidente,
    EstadoOperacional,
    EstadoPlan,
    ResultadoBackup,
    SeveridadIncidente,
    TipoRestore,
)
from app.continuidad_models import (
    ContinuidadAccionCorrectiva,
    ContinuidadAlerta,
    ContinuidadAuditoria,
    ContinuidadBackupEjecucion,
    ContinuidadBackupPolitica,
    ContinuidadBackupVerificacion,
    ContinuidadContingenciaActivacion,
    ContinuidadDependencia,
    ContinuidadDisponibilidad,
    ContinuidadEscalamiento,
    ContinuidadFallback,
    ContinuidadIncidente,
    ContinuidadModoDegradado,
    ContinuidadPlan,
    ContinuidadPostIncidente,
    ContinuidadPrueba,
    ContinuidadRestorePrueba,
    ContinuidadRunbook,
    ContinuidadServicioCritico,
    ContinuidadSlo,
)


class ContinuidadValidationError(ValueError):
    pass


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
    db.add(ContinuidadAuditoria(
        organization_id=org_id, accion=accion, entidad=entidad, entidad_id=entidad_id,
        detalle_json=_json(detalle) if detalle else None, user_id=user_id,
    ))


def _ensure_scope(org_id: str, entity_org: str) -> None:
    if entity_org != org_id:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")


def _alerta(db: Session, org_id: str, tipo: str, mensaje: str, severidad: str = "ALTA", ref: str | None = None) -> None:
    db.add(ContinuidadAlerta(organization_id=org_id, tipo=tipo, mensaje=mensaje, severidad=severidad, entidad_ref=ref))
    db.flush()


def _next_codigo(db: Session, org_id: str, prefix: str, model) -> str:
    n = db.query(func.count(model.id)).filter(model.organization_id == org_id).scalar() or 0
    return f"{prefix}-{n + 1:04d}"


# --- Servicios críticos ---

def create_servicio(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadServicioCritico:
    crit = data.get("criticidad", Criticidad.MEDIA)
    if crit not in Criticidad.ALL:
        raise ContinuidadValidationError(f"Criticidad inválida: {crit}")
    row = ContinuidadServicioCritico(
        organization_id=org_id,
        codigo=data.get("codigo") or _next_codigo(db, org_id, "SVC", ContinuidadServicioCritico),
        nombre=data["nombre"], tipo=data.get("tipo", "OTRO"), criticidad=crit,
        justificacion_criticidad=data.get("justificacion_criticidad"),
        rto_valor=_dec(data.get("rto_valor")), rto_unidad=data.get("rto_unidad"),
        rpo_valor=_dec(data.get("rpo_valor")), rpo_unidad=data.get("rpo_unidad"),
        proveedor_ref=data.get("proveedor_ref"),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "servicio", row.id, user_id, {"codigo": row.codigo})
    return row


def _dec(v: Any) -> Decimal | None:
    return Decimal(str(v)) if v is not None else None


def servicio_to_dict(r: ContinuidadServicioCritico) -> dict[str, Any]:
    return {
        "id": r.id, "codigo": r.codigo, "nombre": r.nombre, "tipo": r.tipo,
        "criticidad": r.criticidad, "rto_valor": float(r.rto_valor) if r.rto_valor else None,
        "rto_unidad": r.rto_unidad, "rpo_valor": float(r.rpo_valor) if r.rpo_valor else None,
        "rpo_unidad": r.rpo_unidad, "estado_operacional": r.estado_operacional,
        "proveedor_ref": r.proveedor_ref,
    }


def get_servicio(db: Session, org_id: str, sid: str) -> ContinuidadServicioCritico:
    row = db.query(ContinuidadServicioCritico).filter(ContinuidadServicioCritico.id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    _ensure_scope(org_id, row.organization_id)
    return row


def list_servicios(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(ContinuidadServicioCritico).filter(
        ContinuidadServicioCritico.organization_id == org_id, ContinuidadServicioCritico.is_active.is_(True),
    ).order_by(ContinuidadServicioCritico.nombre).all()
    return [servicio_to_dict(r) for r in rows]


def update_estado_servicio(db: Session, org_id: str, sid: str, estado: str, mensaje: str | None = None) -> ContinuidadServicioCritico:
    if estado not in EstadoOperacional.ALL:
        raise ContinuidadValidationError(f"Estado operacional inválido: {estado}")
    row = get_servicio(db, org_id, sid)
    row.estado_operacional = estado
    row.ultima_comprobacion = _utcnow()
    db.flush()
    if estado == EstadoOperacional.NO_DISPONIBLE:
        _alerta(db, org_id, "SERVICIO_CAIDO", f"Servicio {row.nombre} no disponible", "CRITICA", row.id)
    elif estado == EstadoOperacional.DEGRADADO:
        _alerta(db, org_id, "SERVICIO_DEGRADADO", f"Servicio {row.nombre} degradado", "ALTA", row.id)
    return row


# --- Dependencias ---

def create_dependencia(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadDependencia:
    get_servicio(db, org_id, data["servicio_origen_id"])
    get_servicio(db, org_id, data["servicio_destino_id"])
    row = ContinuidadDependencia(
        organization_id=org_id, servicio_origen_id=data["servicio_origen_id"],
        servicio_destino_id=data["servicio_destino_id"], tipo=data.get("tipo", "REQUIERE"),
        critica=bool(data.get("critica")), descripcion=data.get("descripcion"),
    )
    db.add(row)
    db.flush()
    return row


def analizar_dependencias(db: Session, org_id: str) -> dict[str, Any]:
    deps = db.query(ContinuidadDependencia).filter(ContinuidadDependencia.organization_id == org_id).all()
    criticas = [d for d in deps if d.critica]
    puntos_falla = []
    for d in criticas:
        dest = get_servicio(db, org_id, d.servicio_destino_id)
        orig = get_servicio(db, org_id, d.servicio_origen_id)
        puntos_falla.append({"origen": orig.nombre, "destino": dest.nombre, "tipo": d.tipo})
    return {"total": len(deps), "criticas": len(criticas), "puntos_falla": puntos_falla}


# --- Planes ---

def create_plan(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadPlan:
    row = ContinuidadPlan(
        organization_id=org_id,
        codigo=_next_codigo(db, org_id, "PLAN", ContinuidadPlan),
        nombre=data["nombre"], alcance=data.get("alcance"),
        servicios_json=_json(data.get("servicios")),
        rto_valor=_dec(data.get("rto_valor")), rto_unidad=data.get("rto_unidad"),
        rpo_valor=_dec(data.get("rpo_valor")), rpo_unidad=data.get("rpo_unidad"),
        activadores=data.get("activadores"), estado=EstadoPlan.BORRADOR,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "plan", row.id, user_id, {"nombre": row.nombre})
    return row


def plan_to_dict(r: ContinuidadPlan) -> dict[str, Any]:
    return {
        "id": r.id, "codigo": r.codigo, "nombre": r.nombre, "estado": r.estado,
        "rto_valor": float(r.rto_valor) if r.rto_valor else None, "rto_unidad": r.rto_unidad,
        "rpo_valor": float(r.rpo_valor) if r.rpo_valor else None, "rpo_unidad": r.rpo_unidad,
        "fecha_revision": r.fecha_revision.isoformat() if r.fecha_revision else None,
    }


def activar_plan(db: Session, org_id: str, plan_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadContingenciaActivacion:
    plan = db.query(ContinuidadPlan).filter(ContinuidadPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    _ensure_scope(org_id, plan.organization_id)
    row = ContinuidadContingenciaActivacion(
        organization_id=org_id, plan_id=plan_id, incidente_id=data.get("incidente_id"),
        motivo=data["motivo"], acciones_activadas_json=_json(data.get("acciones")),
        autorizado_por=user_id,
    )
    plan.estado = EstadoPlan.ACTIVADO
    db.add(row)
    db.flush()
    _audit(db, org_id, "ACTIVACION", "plan", plan_id, user_id, {"motivo": data["motivo"]})
    return row


# --- Backups ---

def create_politica_backup(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadBackupPolitica:
    if data.get("servicio_id"):
        get_servicio(db, org_id, data["servicio_id"])
    row = ContinuidadBackupPolitica(
        organization_id=org_id, servicio_id=data.get("servicio_id"), recurso=data["recurso"],
        frecuencia=data.get("frecuencia", "DIARIA"), retencion_dias=data.get("retencion_dias"),
        ubicacion_logica=data.get("ubicacion_logica"), tipo=data.get("tipo", "COMPLETO"),
        responsable_id=user_id, cifrado_requerido=bool(data.get("cifrado_requerido", True)),
        verificacion_requerida=bool(data.get("verificacion_requerida", True)),
        estado=EstadoBackup.PROGRAMADO,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "backup_politica", row.id, user_id, {"recurso": row.recurso})
    return row


def registrar_ejecucion_backup(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadBackupEjecucion:
    pol = db.query(ContinuidadBackupPolitica).filter(ContinuidadBackupPolitica.id == data["politica_id"]).first()
    if not pol:
        raise HTTPException(status_code=404, detail="Política no encontrada")
    _ensure_scope(org_id, pol.organization_id)
    resultado = data.get("resultado", ResultadoBackup.EXITOSO)
    if resultado not in ResultadoBackup.ALL:
        raise ContinuidadValidationError(f"Resultado inválido: {resultado}")
    row = ContinuidadBackupEjecucion(
        organization_id=org_id, politica_id=pol.id, inicio=data["inicio"], fin=data.get("fin"),
        recurso=pol.recurso, estado_registro=EstadoBackup.EJECUTADO, resultado=resultado,
        tamano_bytes=data.get("tamano_bytes"), hash_referencia=data.get("hash_referencia"),
        ubicacion_logica=data.get("ubicacion_logica") or pol.ubicacion_logica,
        error_seguro=data.get("error_seguro"),
    )
    db.add(row)
    db.flush()
    if resultado == ResultadoBackup.FALLIDO:
        _alerta(db, org_id, "BACKUP_FALLIDO", f"Backup fallido: {pol.recurso}", "CRITICA", row.id)
    _audit(db, org_id, "BACKUP", "backup_ejecucion", row.id, user_id, {
        "resultado": resultado,
        "organization_id": org_id,
        "catalog_entry_id": data.get("catalog_entry_id"),
    })
    return row


def verificar_backup(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadBackupVerificacion:
    ej = db.query(ContinuidadBackupEjecucion).filter(ContinuidadBackupEjecucion.id == data["ejecucion_id"]).first()
    if not ej:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    _ensure_scope(org_id, ej.organization_id)
    ok = data.get("existe") and data.get("tamano_ok") and data.get("integridad_ok") and data.get("vigente")
    explicacion = data.get("explicacion") or ("Verificación exitosa" if ok else "Verificación con hallazgos")
    row = ContinuidadBackupVerificacion(
        organization_id=org_id, ejecucion_id=ej.id, fecha=_utcnow(),
        existe=bool(data.get("existe")), tamano_ok=bool(data.get("tamano_ok")),
        integridad_ok=bool(data.get("integridad_ok")), vigente=bool(data.get("vigente")),
        explicacion=explicacion, verificado_por=user_id,
    )
    if ok:
        ej.estado_registro = EstadoBackup.VERIFICADO
    db.add(row)
    db.flush()
    _audit(db, org_id, "VERIFICACION", "backup", ej.id, user_id, {"ok": ok})
    return row


def registrar_restore(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadRestorePrueba:
    catalog_entry_id = data.get("catalog_entry_id")
    if catalog_entry_id:
        from app.services import integration_wiring as iw

        try:
            iw.validate_restore_privacy(db, org_id, catalog_entry_id, user_id)
        except ValueError as exc:
            raise ContinuidadValidationError(str(exc)) from exc
    tipo = data.get("tipo", TipoRestore.SIMULADA)
    if tipo not in TipoRestore.ALL:
        raise ContinuidadValidationError(f"Tipo restore inválido: {tipo}")
    destino = data.get("entorno_destino", "")
    if destino.upper() in ("PRODUCCION", "PROD", "PRODUCTION") and tipo == TipoRestore.REAL:
        raise ContinuidadValidationError("Restauración real en producción no permitida automáticamente. Use entorno controlado.")
    ej = db.query(ContinuidadBackupEjecucion).filter(ContinuidadBackupEjecucion.id == data["ejecucion_id"]).first()
    if not ej:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    _ensure_scope(org_id, ej.organization_id)
    row = ContinuidadRestorePrueba(
        organization_id=org_id, ejecucion_id=ej.id, tipo=tipo, entorno_destino=destino,
        fecha=data["fecha"], duracion_minutos=_dec(data.get("duracion_minutos")),
        resultado=data.get("resultado", ResultadoBackup.EXITOSO),
        datos_validados=data.get("datos_validados"), evidencia=data.get("evidencia"),
        responsable_id=user_id,
    )
    ej.estado_registro = EstadoBackup.RESTAURADO_EN_PRUEBA
    db.add(row)
    db.flush()
    _audit(db, org_id, "RESTORE_TEST", "restore", row.id, user_id, {"tipo": tipo, "destino": destino})
    return row


# --- Incidentes ---

def create_incidente(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadIncidente:
    sev = data.get("severidad", SeveridadIncidente.SEV3)
    if sev not in SeveridadIncidente.ALL:
        raise ContinuidadValidationError(f"Severidad inválida: {sev}")
    if data.get("servicio_id"):
        get_servicio(db, org_id, data["servicio_id"])
    row = ContinuidadIncidente(
        organization_id=org_id, servicio_id=data.get("servicio_id"), severidad=sev,
        titulo=data["titulo"], descripcion=data.get("descripcion"),
        impacto_json=_json(data.get("impacto")), estado=EstadoIncidente.DETECTADO,
        inicio=data.get("inicio") or _utcnow(), deteccion=_utcnow(), responsable_id=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "INCIDENTE", "incidente", row.id, user_id, {"severidad": sev})
    return row


def incidente_to_dict(r: ContinuidadIncidente) -> dict[str, Any]:
    return {
        "id": r.id, "titulo": r.titulo, "severidad": r.severidad, "estado": r.estado,
        "servicio_id": r.servicio_id, "inicio": r.inicio.isoformat(),
        "impacto": _parse(r.impacto_json),
    }


def update_incidente_estado(db: Session, org_id: str, iid: str, data: dict[str, Any], user_id: str | None) -> ContinuidadIncidente:
    row = db.query(ContinuidadIncidente).filter(ContinuidadIncidente.id == iid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    _ensure_scope(org_id, row.organization_id)
    estado = data["estado"]
    if estado not in EstadoIncidente.ALL:
        raise ContinuidadValidationError(f"Estado inválido: {estado}")
    old = row.estado
    row.estado = estado
    if data.get("causa"):
        row.causa = data["causa"]
    if data.get("causa_raiz_tipo"):
        if data["causa_raiz_tipo"] not in CausaRaiz.ALL:
            raise ContinuidadValidationError("Tipo causa raíz inválido")
        row.causa_raiz_tipo = data["causa_raiz_tipo"]
    if estado == EstadoIncidente.RESUELTO:
        row.recuperacion = _utcnow()
    if estado == EstadoIncidente.CERRADO:
        row.cierre = _utcnow()
    db.flush()
    _audit(db, org_id, "CAMBIO_SEVERIDAD" if estado != old else "INCIDENTE", "incidente", iid, user_id, {"de": old, "a": estado})
    return row


def cerrar_incidente(db: Session, org_id: str, iid: str, user_id: str | None) -> ContinuidadIncidente:
    return update_incidente_estado(db, org_id, iid, {"estado": EstadoIncidente.CERRADO}, user_id)


# --- Modo degradado / fallback ---

def create_modo_degradado(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadModoDegradado:
    get_servicio(db, org_id, data["servicio_id"])
    row = ContinuidadModoDegradado(
        organization_id=org_id, servicio_id=data["servicio_id"],
        funciones_continuan_json=_json(data.get("funciones_continuan")),
        funciones_bloqueadas_json=_json(data.get("funciones_bloqueadas")),
        funciones_limitadas_json=_json(data.get("funciones_limitadas")),
        activo=True,
    )
    get_servicio(db, org_id, data["servicio_id"]).estado_operacional = EstadoOperacional.DEGRADADO
    db.add(row)
    db.flush()
    return row


def create_escalamiento(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadEscalamiento:
    sev = data.get("severidad", SeveridadIncidente.SEV3)
    if sev not in SeveridadIncidente.ALL:
        raise ContinuidadValidationError(f"Severidad inválida: {sev}")
    row = ContinuidadEscalamiento(
        organization_id=org_id, severidad=sev, nivel=int(data.get("nivel", 1)),
        responsable_id=data.get("responsable_id") or user_id,
        tiempo_max_min=data.get("tiempo_max_min"), siguiente_nivel=data.get("siguiente_nivel"),
    )
    db.add(row)
    db.flush()
    return row


def list_planes(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(ContinuidadPlan).filter(ContinuidadPlan.organization_id == org_id).order_by(ContinuidadPlan.nombre).all()
    return [plan_to_dict(r) for r in rows]


def list_incidentes(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(ContinuidadIncidente).filter(ContinuidadIncidente.organization_id == org_id).order_by(ContinuidadIncidente.inicio.desc()).all()
    return [incidente_to_dict(r) for r in rows]


def list_alertas(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(ContinuidadAlerta).filter(
        ContinuidadAlerta.organization_id == org_id, ContinuidadAlerta.resuelta.is_(False),
    ).order_by(ContinuidadAlerta.created_at.desc()).limit(50).all()
    return [{"id": a.id, "tipo": a.tipo, "mensaje": a.mensaje, "severidad": a.severidad} for a in rows]


def create_fallback(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadFallback:
    get_servicio(db, org_id, data["servicio_id"])
    row = ContinuidadFallback(
        organization_id=org_id, servicio_id=data["servicio_id"],
        proveedor_principal_ref=data.get("proveedor_principal_ref"),
        proveedor_alternativo_ref=data.get("proveedor_alternativo_ref"),
        descripcion=data.get("descripcion"),
    )
    db.add(row)
    db.flush()
    return row


# --- SLA / Disponibilidad ---

def create_slo(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadSlo:
    get_servicio(db, org_id, data["servicio_id"])
    row = ContinuidadSlo(
        organization_id=org_id, servicio_id=data["servicio_id"], nombre=data["nombre"],
        objetivo_pct=_dec(data["objetivo_pct"]) or Decimal("99.9"), periodo=data.get("periodo"),
    )
    db.add(row)
    db.flush()
    return row


def medir_slo(db: Session, org_id: str, slo_id: str, medido_pct: float, user_id: str | None) -> ContinuidadSlo:
    row = db.query(ContinuidadSlo).filter(ContinuidadSlo.id == slo_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="SLO no encontrado")
    _ensure_scope(org_id, row.organization_id)
    row.medido_pct = Decimal(str(medido_pct))
    row.incumplido = row.medido_pct < row.objetivo_pct
    db.flush()
    if row.incumplido:
        _alerta(db, org_id, "SLA_INCUMPLIDO", f"SLO {row.nombre} incumplido: {medido_pct}% < {row.objetivo_pct}%", "ALTA", row.id)
    return row


def registrar_disponibilidad(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadDisponibilidad:
    get_servicio(db, org_id, data["servicio_id"])
    disp = _dec(data["tiempo_disponible_min"]) or Decimal("0")
    caido = _dec(data["tiempo_caido_min"]) or Decimal("0")
    total = disp + caido
    pct = (disp / total * 100) if total > 0 else Decimal("100")
    row = ContinuidadDisponibilidad(
        organization_id=org_id, servicio_id=data["servicio_id"], periodo=data["periodo"],
        tiempo_disponible_min=disp, tiempo_caido_min=caido, disponibilidad_pct=pct,
    )
    db.add(row)
    db.flush()
    return row


def evaluar_rto_rpo(db: Session, org_id: str, servicio_id: str, tiempo_recuperacion_min: float, perdida_datos_min: float) -> dict[str, Any]:
    svc = get_servicio(db, org_id, servicio_id)
    rto_ok = True
    rpo_ok = True
    if svc.rto_valor is not None:
        rto_ok = tiempo_recuperacion_min <= float(svc.rto_valor)
    if svc.rpo_valor is not None:
        rpo_ok = perdida_datos_min <= float(svc.rpo_valor)
    if not rto_ok:
        _alerta(db, org_id, "RTO_INCUMPLIDO", f"RTO incumplido en {svc.nombre}: {tiempo_recuperacion_min} > {svc.rto_valor}", "CRITICA", svc.id)
    if not rpo_ok:
        _alerta(db, org_id, "RPO_EN_RIESGO", f"RPO en riesgo en {svc.nombre}", "ALTA", svc.id)
    return {
        "servicio": svc.nombre,
        "rto_objetivo": float(svc.rto_valor) if svc.rto_valor else None,
        "rto_unidad": svc.rto_unidad,
        "rto_cumplido": rto_ok,
        "rpo_objetivo": float(svc.rpo_valor) if svc.rpo_valor else None,
        "rpo_unidad": svc.rpo_unidad,
        "rpo_cumplido": rpo_ok,
        "explicacion_rto": "RTO: tiempo máximo aceptable de recuperación",
        "explicacion_rpo": "RPO: pérdida máxima aceptable de datos",
    }


# --- Runbooks ---

def create_runbook(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadRunbook:
    pasos = data.get("pasos") or []
    for p in pasos:
        if "comando" in p or "cmd" in p:
            raise ContinuidadValidationError("No se permiten comandos ejecutables en procedimientos")
    row = ContinuidadRunbook(
        organization_id=org_id, servicio_id=data.get("servicio_id"),
        nombre=data["nombre"], descripcion=data.get("descripcion"), pasos_json=_json(pasos),
    )
    db.add(row)
    db.flush()
    return row


def runbook_to_dict(r: ContinuidadRunbook) -> dict[str, Any]:
    return {"id": r.id, "nombre": r.nombre, "pasos": _parse(r.pasos_json)}


# --- Pruebas continuidad ---

def create_prueba(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadPrueba:
    row = ContinuidadPrueba(
        organization_id=org_id, plan_id=data.get("plan_id"), tipo=data["tipo"],
        escenario=data["escenario"], objetivo=data.get("objetivo"), resultado=data.get("resultado"),
        rto_obtenido=_dec(data.get("rto_obtenido")), rpo_obtenido=_dec(data.get("rpo_obtenido")),
        hallazgos=data.get("hallazgos"),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "PRUEBA_CONTINUIDAD", "prueba", row.id, user_id, {"escenario": data["escenario"]})
    return row


# --- Post-incidente ---

def create_post_incidente(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadPostIncidente:
    causa_tipo = data.get("causa_raiz_tipo", CausaRaiz.NO_DETERMINADA)
    if causa_tipo not in CausaRaiz.ALL:
        raise ContinuidadValidationError("Tipo causa raíz inválido")
    row = ContinuidadPostIncidente(
        organization_id=org_id, incidente_id=data["incidente_id"],
        que_ocurrio=data.get("que_ocurrio"), impacto=data.get("impacto"), causa=data.get("causa"),
        causa_raiz_tipo=causa_tipo, que_funciono=data.get("que_funciono"), que_fallo=data.get("que_fallo"),
        aprendizaje_ref=f"aprendizaje-prep-{data['incidente_id'][:8]}",
    )
    db.add(row)
    db.flush()
    return row


def create_accion_correctiva(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> ContinuidadAccionCorrectiva:
    row = ContinuidadAccionCorrectiva(
        organization_id=org_id, incidente_id=data.get("incidente_id"),
        post_incidente_id=data.get("post_incidente_id"), accion=data["accion"],
        responsable_id=data.get("responsable_id") or user_id,
        prioridad=data.get("prioridad", "MEDIA"), fecha_objetivo=data.get("fecha_objetivo"),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "ACCION_CORRECTIVA", "accion", row.id, user_id, {"accion": data["accion"][:80]})
    return row


# --- Tablero / Centro control adapter ---

def tablero(db: Session, org_id: str) -> dict[str, Any]:
    servicios = list_servicios(db, org_id)
    incidentes_abiertos = db.query(ContinuidadIncidente).filter(
        ContinuidadIncidente.organization_id == org_id,
        ContinuidadIncidente.estado.notin_([EstadoIncidente.CERRADO, EstadoIncidente.RESUELTO]),
    ).count()
    backups_recientes = db.query(ContinuidadBackupEjecucion).filter(
        ContinuidadBackupEjecucion.organization_id == org_id,
    ).order_by(ContinuidadBackupEjecucion.inicio.desc()).limit(5).all()
    backups_fallidos = db.query(ContinuidadBackupEjecucion).filter(
        ContinuidadBackupEjecucion.organization_id == org_id,
        ContinuidadBackupEjecucion.resultado == ResultadoBackup.FALLIDO,
    ).count()
    restores = db.query(ContinuidadRestorePrueba).filter(ContinuidadRestorePrueba.organization_id == org_id).count()
    alertas = db.query(ContinuidadAlerta).filter(
        ContinuidadAlerta.organization_id == org_id, ContinuidadAlerta.resuelta.is_(False),
    ).order_by(ContinuidadAlerta.created_at.desc()).limit(10).all()
    acciones_pend = db.query(ContinuidadAccionCorrectiva).filter(
        ContinuidadAccionCorrectiva.organization_id == org_id,
        ContinuidadAccionCorrectiva.estado == "PENDIENTE",
    ).count()
    degradados = [s for s in servicios if s.get("estado_operacional") == EstadoOperacional.DEGRADADO]
    return {
        "servicios_criticos": servicios,
        "servicios_degradados": degradados,
        "incidentes_abiertos": incidentes_abiertos,
        "backups_recientes": [{"recurso": b.recurso, "resultado": b.resultado, "estado_registro": b.estado_registro} for b in backups_recientes],
        "backups_fallidos": backups_fallidos,
        "restauraciones_verificadas": restores,
        "acciones_pendientes": acciones_pend,
        "alertas": [
            {
                "id": a.id,
                "tipo": a.tipo,
                "mensaje": a.mensaje,
                "severidad": a.severidad,
                "entidad_ref": a.entidad_ref,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "resuelta": a.resuelta,
            }
            for a in alertas
        ],
        "centro_control_adapter": {
            "disponibilidad": True, "incidentes": incidentes_abiertos > 0,
            "backups": len(backups_recientes), "riesgos": backups_fallidos > 0,
        },
        "integracion_1330_prep": {"reportar_salud": "/api/continuidad/servicios/{id}/estado"},
        "integracion_1260_prep": {"aprendizaje_desde_incidentes": True},
    }


def centro_control_resumen(db: Session, org_id: str) -> dict[str, Any]:
    t = tablero(db, org_id)
    return {
        "disponibilidad": [s for s in t["servicios_criticos"] if s.get("estado_operacional") == "DISPONIBLE"],
        "degradados": t["servicios_degradados"],
        "incidentes_abiertos": t["incidentes_abiertos"],
        "backups_fallidos": t["backups_fallidos"],
        "alertas": t["alertas"][:5],
    }
