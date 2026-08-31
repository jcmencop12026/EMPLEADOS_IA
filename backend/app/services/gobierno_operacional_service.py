"""Servicio de gobierno operacional EIAAX — acciones, aprobaciones, visibilidad e IA."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.gobierno_operacional_models import (
    DOMINIOS_VISIBILIDAD,
    ESTADOS_SOLICITUD,
    TIPOS_ACCION,
    GobiernoAccionPolicy,
    GobiernoAccionSolicitud,
    GobiernoEvento,
    GobiernoIaPolicy,
    GobiernoVisibilidadLog,
)
from app.models import AuditLog, Organization, Role, RolePermission, User
from app.orchestration_models import ApprovalRequest


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


def _loads(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _dumps(data: Any) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


DEFAULT_ACCION_POLICIES: list[dict[str, Any]] = [
    {"tipo_accion": "LECTURA", "requiere_aprobacion_humana": False, "auto_ejecutar": True},
    {"tipo_accion": "ANALISIS", "requiere_aprobacion_humana": False, "auto_ejecutar": True},
    {"tipo_accion": "PROPUESTA", "requiere_aprobacion_humana": True, "auto_ejecutar": False},
    {"tipo_accion": "EJECUCION", "requiere_aprobacion_humana": True, "auto_ejecutar": False, "criticidad": "HIGH"},
]


def ensure_default_policies(db: Session, organization_id: str) -> None:
    existing = (
        db.query(GobiernoAccionPolicy)
        .filter(GobiernoAccionPolicy.organization_id == organization_id)
        .count()
    )
    if existing:
        return
    now = _utcnow()
    for spec in DEFAULT_ACCION_POLICIES:
        db.add(
            GobiernoAccionPolicy(
                organization_id=organization_id,
                tipo_accion=spec["tipo_accion"],
                criticidad=spec.get("criticidad", "MEDIUM"),
                requiere_aprobacion_humana=spec["requiere_aprobacion_humana"],
                auto_ejecutar=spec["auto_ejecutar"],
                activo=True,
                created_at=now,
                updated_at=now,
            )
        )
    db.flush()


def ensure_default_ia_policy(db: Session, organization_id: str) -> None:
    existing = (
        db.query(GobiernoIaPolicy)
        .filter(GobiernoIaPolicy.organization_id == organization_id, GobiernoIaPolicy.activo.is_(True))
        .first()
    )
    if existing:
        return
    now = _utcnow()
    db.add(
        GobiernoIaPolicy(
            organization_id=organization_id,
            nombre="Política IA base",
            proveedores_permitidos_json=_dumps([]),
            modelos_permitidos_json=_dumps([]),
            acciones_permitidas_json=_dumps(list(TIPOS_ACCION)),
            herramientas_permitidas_json=_dumps([]),
            limites_json=_dumps({"max_tokens_por_dia": None}),
            requiere_aprobacion_humana_json=_dumps({"EJECUCION": True, "PROPUESTA": True}),
            datos_permitidos_json=_dumps(["operacionales", "evaluacion"]),
            auto_ejecutar=False,
            activo=True,
            created_at=now,
            updated_at=now,
        )
    )
    db.flush()


def registrar_evento(
    db: Session,
    *,
    organization_id: str,
    actor_tipo: str,
    actor_id: str | None,
    accion: str,
    recurso_tipo: str | None = None,
    recurso_id: str | None = None,
    decision: str | None = None,
    aprobacion_id: str | None = None,
    resultado: str | None = None,
    correlation_id: str | None = None,
    detalle: dict[str, Any] | None = None,
    commit: bool = False,
) -> GobiernoEvento:
    evt = GobiernoEvento(
        organization_id=organization_id,
        correlation_id=correlation_id or _uuid(),
        actor_tipo=actor_tipo,
        actor_id=actor_id,
        accion=accion,
        recurso_tipo=recurso_tipo,
        recurso_id=recurso_id,
        decision=decision,
        aprobacion_id=aprobacion_id,
        resultado=resultado,
        detalle_json=_dumps(detalle),
        created_at=_utcnow(),
    )
    db.add(evt)
    write_audit(
        db,
        action=f"gobierno.{accion}",
        organization_id=organization_id,
        user_id=actor_id if actor_tipo == "HUMANO" else None,
        detail=_dumps(
            {
                "actor_tipo": actor_tipo,
                "recurso_tipo": recurso_tipo,
                "recurso_id": recurso_id,
                "decision": decision,
                "resultado": resultado,
                "correlation_id": evt.correlation_id,
            }
        ),
        commit=False,
    )
    if commit:
        db.commit()
    else:
        db.flush()
    return evt


def evaluar_accion(
    db: Session,
    organization_id: str,
    *,
    tipo_accion: str,
    recurso_tipo: str | None = None,
    criticidad: str = "MEDIUM",
    capacidad_externa: str | None = None,
    empleado_ia_id: str | None = None,
) -> dict[str, Any]:
    if tipo_accion not in TIPOS_ACCION:
        raise HTTPException(status_code=422, detail=f"tipo_accion inválido: {tipo_accion}")
    ensure_default_policies(db, organization_id)
    q = db.query(GobiernoAccionPolicy).filter(
        GobiernoAccionPolicy.organization_id == organization_id,
        GobiernoAccionPolicy.tipo_accion == tipo_accion,
        GobiernoAccionPolicy.activo.is_(True),
    )
    policy = None
    if recurso_tipo:
        policy = q.filter(GobiernoAccionPolicy.recurso_tipo == recurso_tipo).first()
    if not policy:
        policy = q.filter(GobiernoAccionPolicy.recurso_tipo.is_(None)).first()
    if not policy:
        return {
            "tipo_accion": tipo_accion,
            "requiere_aprobacion_humana": tipo_accion in {"PROPUESTA", "EJECUCION"},
            "auto_ejecutar": tipo_accion in {"LECTURA", "ANALISIS"},
            "politica_id": None,
            "motivo": "Política por defecto del sistema",
        }
    if capacidad_externa and policy.capacidad_externa and policy.capacidad_externa != capacidad_externa:
        return {
            "tipo_accion": tipo_accion,
            "requiere_aprobacion_humana": True,
            "auto_ejecutar": False,
            "politica_id": policy.id,
            "motivo": "Capacidad externa no autorizada por política",
        }
    if empleado_ia_id and policy.empleado_ia_id and policy.empleado_ia_id != empleado_ia_id:
        return {
            "tipo_accion": tipo_accion,
            "requiere_aprobacion_humana": True,
            "auto_ejecutar": False,
            "politica_id": policy.id,
            "motivo": "Empleado IA no autorizado por política",
        }
    crit_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    if crit_order.get(criticidad, 1) >= crit_order.get(policy.criticidad, 1) and policy.requiere_aprobacion_humana:
        return {
            "tipo_accion": tipo_accion,
            "requiere_aprobacion_humana": True,
            "auto_ejecutar": policy.auto_ejecutar,
            "politica_id": policy.id,
            "motivo": f"Criticidad {criticidad} requiere aprobación humana",
        }
    return {
        "tipo_accion": tipo_accion,
        "requiere_aprobacion_humana": policy.requiere_aprobacion_humana,
        "auto_ejecutar": policy.auto_ejecutar,
        "politica_id": policy.id,
        "motivo": None,
    }


def list_policies(db: Session, organization_id: str) -> list[GobiernoAccionPolicy]:
    ensure_default_policies(db, organization_id)
    return (
        db.query(GobiernoAccionPolicy)
        .filter(GobiernoAccionPolicy.organization_id == organization_id, GobiernoAccionPolicy.activo.is_(True))
        .order_by(GobiernoAccionPolicy.tipo_accion)
        .all()
    )


def create_policy(db: Session, organization_id: str, data: dict[str, Any]) -> GobiernoAccionPolicy:
    if data["tipo_accion"] not in TIPOS_ACCION:
        raise HTTPException(status_code=422, detail="tipo_accion inválido")
    now = _utcnow()
    row = GobiernoAccionPolicy(
        organization_id=organization_id,
        tipo_accion=data["tipo_accion"],
        recurso_tipo=data.get("recurso_tipo"),
        criticidad=data.get("criticidad", "MEDIUM"),
        requiere_aprobacion_humana=data.get("requiere_aprobacion_humana", False),
        rol_aprobador=data.get("rol_aprobador"),
        capacidad_externa=data.get("capacidad_externa"),
        empleado_ia_id=data.get("empleado_ia_id"),
        auto_ejecutar=data.get("auto_ejecutar", True),
        config_json=_dumps(data.get("config")),
        activo=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    return row


def policy_to_dict(row: GobiernoAccionPolicy) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "tipo_accion": row.tipo_accion,
        "recurso_tipo": row.recurso_tipo,
        "criticidad": row.criticidad,
        "requiere_aprobacion_humana": row.requiere_aprobacion_humana,
        "rol_aprobador": row.rol_aprobador,
        "capacidad_externa": row.capacidad_externa,
        "empleado_ia_id": row.empleado_ia_id,
        "auto_ejecutar": row.auto_ejecutar,
        "activo": row.activo,
        "config": _loads(row.config_json),
        "created_at": row.created_at,
    }


def solicitud_to_dict(row: GobiernoAccionSolicitud) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "correlation_id": row.correlation_id,
        "tipo_accion": row.tipo_accion,
        "recurso_tipo": row.recurso_tipo,
        "recurso_id": row.recurso_id,
        "criticidad": row.criticidad,
        "descripcion": row.descripcion,
        "payload": _loads(row.payload_json),
        "estado": row.estado,
        "actor_tipo": row.actor_tipo,
        "solicitado_por": row.solicitado_por,
        "aprobado_por": row.aprobado_por,
        "rechazado_por": row.rechazado_por,
        "motivo_solicitud": row.motivo_solicitud,
        "motivo_decision": row.motivo_decision,
        "resultado": _loads(row.resultado_json),
        "created_at": row.created_at,
        "decided_at": row.decided_at,
        "executed_at": row.executed_at,
    }


def crear_solicitud(
    db: Session,
    organization_id: str,
    user_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    if data["tipo_accion"] not in TIPOS_ACCION:
        raise HTTPException(status_code=422, detail="tipo_accion inválido")
    evaluacion = evaluar_accion(
        db,
        organization_id,
        tipo_accion=data["tipo_accion"],
        recurso_tipo=data.get("recurso_tipo"),
        criticidad=data.get("criticidad", "MEDIUM"),
    )
    correlation_id = data.get("correlation_id") or _uuid()
    estado = "PENDIENTE" if evaluacion["requiere_aprobacion_humana"] else "APROBADA"
    row = GobiernoAccionSolicitud(
        organization_id=organization_id,
        correlation_id=correlation_id,
        tipo_accion=data["tipo_accion"],
        recurso_tipo=data["recurso_tipo"],
        recurso_id=data.get("recurso_id"),
        criticidad=data.get("criticidad", "MEDIUM"),
        descripcion=data["descripcion"],
        payload_json=_dumps(data.get("payload")),
        estado=estado,
        actor_tipo=data.get("actor_tipo", "HUMANO"),
        solicitado_por=user_id,
        motivo_solicitud=data.get("motivo_solicitud"),
        created_at=_utcnow(),
    )
    db.add(row)
    db.flush()
    registrar_evento(
        db,
        organization_id=organization_id,
        actor_tipo=row.actor_tipo,
        actor_id=user_id,
        accion="accion.solicitada",
        recurso_tipo=row.recurso_tipo,
        recurso_id=row.recurso_id,
        correlation_id=correlation_id,
        aprobacion_id=row.id,
        detalle={"estado": estado, "tipo_accion": row.tipo_accion},
    )
    if estado == "APROBADA":
        row.executed_at = _utcnow()
        row.resultado_json = _dumps({"auto": True, "mensaje": "Ejecución automática permitida"})
        registrar_evento(
            db,
            organization_id=organization_id,
            actor_tipo="SISTEMA",
            actor_id=None,
            accion="accion.ejecutada",
            recurso_tipo=row.recurso_tipo,
            recurso_id=row.recurso_id,
            correlation_id=correlation_id,
            aprobacion_id=row.id,
            resultado="EJECUTADA",
        )
    return solicitud_to_dict(row)


def decidir_solicitud(
    db: Session,
    organization_id: str,
    solicitud_id: str,
    user_id: str,
    *,
    decision: str,
    motivo: str | None = None,
) -> dict[str, Any]:
    row = (
        db.query(GobiernoAccionSolicitud)
        .filter(
            GobiernoAccionSolicitud.id == solicitud_id,
            GobiernoAccionSolicitud.organization_id == organization_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if row.estado not in {"PENDIENTE", "SOLICITADA"}:
        raise HTTPException(status_code=400, detail="Solicitud ya decidida o finalizada")
    now = _utcnow()
    row.decided_at = now
    row.motivo_decision = motivo
    if decision == "approve":
        row.estado = "APROBADA"
        row.aprobado_por = user_id
        row.executed_at = now
        row.resultado_json = _dumps({"aprobado_por": user_id, "motivo": motivo})
        registrar_evento(
            db,
            organization_id=organization_id,
            actor_tipo="HUMANO",
            actor_id=user_id,
            accion="accion.aprobada",
            recurso_tipo=row.recurso_tipo,
            recurso_id=row.recurso_id,
            decision="APROBADA",
            aprobacion_id=row.id,
            correlation_id=row.correlation_id,
            detalle={"motivo": motivo},
        )
        row.estado = "EJECUTADA"
        registrar_evento(
            db,
            organization_id=organization_id,
            actor_tipo="HUMANO",
            actor_id=user_id,
            accion="accion.ejecutada",
            recurso_tipo=row.recurso_tipo,
            recurso_id=row.recurso_id,
            aprobacion_id=row.id,
            correlation_id=row.correlation_id,
            resultado="EJECUTADA",
        )
    elif decision == "reject":
        row.estado = "RECHAZADA"
        row.rechazado_por = user_id
        registrar_evento(
            db,
            organization_id=organization_id,
            actor_tipo="HUMANO",
            actor_id=user_id,
            accion="accion.rechazada",
            recurso_tipo=row.recurso_tipo,
            recurso_id=row.recurso_id,
            decision="RECHAZADA",
            aprobacion_id=row.id,
            correlation_id=row.correlation_id,
            resultado="RECHAZADA",
            detalle={"motivo": motivo},
        )
    elif decision == "cancel":
        row.estado = "CANCELADA"
        registrar_evento(
            db,
            organization_id=organization_id,
            actor_tipo="HUMANO",
            actor_id=user_id,
            accion="accion.cancelada",
            recurso_tipo=row.recurso_tipo,
            recurso_id=row.recurso_id,
            aprobacion_id=row.id,
            correlation_id=row.correlation_id,
            resultado="CANCELADA",
            detalle={"motivo": motivo},
        )
    else:
        raise HTTPException(status_code=422, detail="decision inválida")
    db.flush()
    return solicitud_to_dict(row)


def list_solicitudes(
    db: Session,
    organization_id: str,
    *,
    estado: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    q = db.query(GobiernoAccionSolicitud).filter(GobiernoAccionSolicitud.organization_id == organization_id)
    if estado:
        q = q.filter(GobiernoAccionSolicitud.estado == estado)
    rows = q.order_by(GobiernoAccionSolicitud.created_at.desc()).limit(limit).all()
    return [solicitud_to_dict(r) for r in rows]


def set_visibilidad_general(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    dominio: str,
    contexto_id: str | None,
    objeto_tipo: str,
    objeto_id: str,
    visible: bool,
    correlation_id: str | None = None,
) -> GobiernoVisibilidadLog:
    if dominio not in DOMINIOS_VISIBILIDAD:
        raise HTTPException(status_code=422, detail=f"dominio inválido: {dominio}")
    log = GobiernoVisibilidadLog(
        organization_id=organization_id,
        dominio=dominio,
        contexto_id=contexto_id,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        visible=visible,
        changed_by=user_id,
        correlation_id=correlation_id,
        created_at=_utcnow(),
    )
    db.add(log)
    registrar_evento(
        db,
        organization_id=organization_id,
        actor_tipo="HUMANO",
        actor_id=user_id,
        accion="visibilidad.cambiada",
        recurso_tipo=objeto_tipo,
        recurso_id=objeto_id,
        correlation_id=correlation_id,
        detalle={"dominio": dominio, "visible": visible, "contexto_id": contexto_id},
    )
    db.flush()
    return log


def list_visibilidad(
    db: Session,
    organization_id: str,
    *,
    dominio: str | None = None,
    contexto_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    q = db.query(GobiernoVisibilidadLog).filter(GobiernoVisibilidadLog.organization_id == organization_id)
    if dominio:
        q = q.filter(GobiernoVisibilidadLog.dominio == dominio)
    if contexto_id:
        q = q.filter(GobiernoVisibilidadLog.contexto_id == contexto_id)
    rows = q.order_by(GobiernoVisibilidadLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "dominio": r.dominio,
            "contexto_id": r.contexto_id,
            "objeto_tipo": r.objeto_tipo,
            "objeto_id": r.objeto_id,
            "visible": r.visible,
            "changed_by": r.changed_by,
            "correlation_id": r.correlation_id,
            "created_at": r.created_at,
        }
        for r in rows
    ]


def ia_policy_to_dict(row: GobiernoIaPolicy) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "nombre": row.nombre,
        "proveedores_permitidos": _loads(row.proveedores_permitidos_json) or [],
        "modelos_permitidos": _loads(row.modelos_permitidos_json) or [],
        "acciones_permitidas": _loads(row.acciones_permitidas_json) or [],
        "herramientas_permitidas": _loads(row.herramientas_permitidas_json) or [],
        "limites": _loads(row.limites_json),
        "requiere_aprobacion_humana": _loads(row.requiere_aprobacion_humana_json) or {},
        "datos_permitidos": _loads(row.datos_permitidos_json) or [],
        "auto_ejecutar": row.auto_ejecutar,
        "activo": row.activo,
        "created_at": row.created_at,
    }


def list_ia_policies(db: Session, organization_id: str) -> list[dict[str, Any]]:
    ensure_default_ia_policy(db, organization_id)
    rows = (
        db.query(GobiernoIaPolicy)
        .filter(GobiernoIaPolicy.organization_id == organization_id, GobiernoIaPolicy.activo.is_(True))
        .order_by(GobiernoIaPolicy.created_at.desc())
        .all()
    )
    return [ia_policy_to_dict(r) for r in rows]


def create_ia_policy(db: Session, organization_id: str, data: dict[str, Any]) -> dict[str, Any]:
    now = _utcnow()
    row = GobiernoIaPolicy(
        organization_id=organization_id,
        nombre=data["nombre"],
        proveedores_permitidos_json=_dumps(data.get("proveedores_permitidos")),
        modelos_permitidos_json=_dumps(data.get("modelos_permitidos")),
        acciones_permitidas_json=_dumps(data.get("acciones_permitidas")),
        herramientas_permitidas_json=_dumps(data.get("herramientas_permitidas")),
        limites_json=_dumps(data.get("limites")),
        requiere_aprobacion_humana_json=_dumps(data.get("requiere_aprobacion_humana")),
        datos_permitidos_json=_dumps(data.get("datos_permitidos")),
        auto_ejecutar=data.get("auto_ejecutar", False),
        activo=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    registrar_evento(
        db,
        organization_id=organization_id,
        actor_tipo="HUMANO",
        actor_id=None,
        accion="ia.politica.creada",
        recurso_tipo="gobierno_ia_policy",
        recurso_id=row.id,
        detalle={"nombre": row.nombre},
    )
    return ia_policy_to_dict(row)


def check_ia_policy(
    db: Session,
    organization_id: str,
    *,
    proveedor: str | None = None,
    modelo: str | None = None,
    tipo_accion: str | None = None,
    herramienta: str | None = None,
) -> dict[str, Any]:
    ensure_default_ia_policy(db, organization_id)
    policy = (
        db.query(GobiernoIaPolicy)
        .filter(GobiernoIaPolicy.organization_id == organization_id, GobiernoIaPolicy.activo.is_(True))
        .order_by(GobiernoIaPolicy.created_at.desc())
        .first()
    )
    if not policy:
        return {"permitido": False, "requiere_aprobacion": True, "auto_ejecutar": False, "razones": ["Sin política IA"]}
    razones: list[str] = []
    proveedores = _loads(policy.proveedores_permitidos_json) or []
    modelos = _loads(policy.modelos_permitidos_json) or []
    acciones = _loads(policy.acciones_permitidas_json) or []
    herramientas = _loads(policy.herramientas_permitidas_json) or []
    aprob_map = _loads(policy.requiere_aprobacion_humana_json) or {}
    if proveedor and proveedores and proveedor not in proveedores:
        razones.append(f"Proveedor {proveedor} no permitido")
    if modelo and modelos and modelo not in modelos:
        razones.append(f"Modelo {modelo} no permitido")
    if tipo_accion and acciones and tipo_accion not in acciones:
        razones.append(f"Acción {tipo_accion} no permitida")
    if herramienta and herramientas and herramienta not in herramientas:
        razones.append(f"Herramienta {herramienta} no permitida")
    requiere = bool(aprob_map.get(tipo_accion or "", False))
    return {
        "permitido": len(razones) == 0,
        "requiere_aprobacion": requiere,
        "auto_ejecutar": policy.auto_ejecutar and not requiere,
        "razones": razones,
    }


def list_eventos(db: Session, organization_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.query(GobiernoEvento)
        .filter(GobiernoEvento.organization_id == organization_id)
        .order_by(GobiernoEvento.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "correlation_id": r.correlation_id,
            "actor_tipo": r.actor_tipo,
            "actor_id": r.actor_id,
            "accion": r.accion,
            "recurso_tipo": r.recurso_tipo,
            "recurso_id": r.recurso_id,
            "decision": r.decision,
            "aprobacion_id": r.aprobacion_id,
            "resultado": r.resultado,
            "detalle": _loads(r.detalle_json),
            "created_at": r.created_at,
        }
        for r in rows
    ]


def _count_roles_with_permissions(db: Session, organization_id: str) -> int:
    return (
        db.query(func.count(func.distinct(Role.id)))
        .join(RolePermission, RolePermission.role_id == Role.id)
        .filter(
            (Role.organization_id == organization_id) | (Role.organization_id.is_(None)),
            Role.is_active.is_(True),
        )
        .scalar()
        or 0
    )


def get_centro_confianza(db: Session, organization_id: str) -> dict[str, Any]:
    """Vista compacta basada SOLO en controles implementados con evidencia."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    controles: list[dict[str, Any]] = []

    # Aislamiento multitenant
    org_count = db.query(func.count(Organization.id)).scalar() or 0
    if org_count >= 1:
        controles.append(
            {
                "id": "aislamiento",
                "nombre": "Aislamiento por organización",
                "estado": "ACTIVO",
                "evidencia": f"Organización activa: {org.name}",
                "detalle": {"organization_id": organization_id, "organizaciones_registradas": org_count},
            }
        )

    # RBAC
    roles_count = _count_roles_with_permissions(db, organization_id)
    if roles_count > 0:
        controles.append(
            {
                "id": "rbac",
                "nombre": "Control de acceso basado en roles",
                "estado": "ACTIVO",
                "evidencia": f"{roles_count} rol(es) con permisos asignados",
                "detalle": {"roles_con_permisos": roles_count},
            }
        )

    # Auditoría
    audit_count = (
        db.query(func.count(AuditLog.id)).filter(AuditLog.organization_id == organization_id).scalar() or 0
    )
    if audit_count > 0:
        controles.append(
            {
                "id": "auditoria",
                "nombre": "Registro de auditoría",
                "estado": "ACTIVO",
                "evidencia": f"{audit_count} evento(s) de auditoría",
                "detalle": {"eventos": audit_count},
            }
        )

    # Gobierno operacional / aprobaciones
    ensure_default_policies(db, organization_id)
    policies_count = (
        db.query(func.count(GobiernoAccionPolicy.id))
        .filter(GobiernoAccionPolicy.organization_id == organization_id, GobiernoAccionPolicy.activo.is_(True))
        .scalar()
        or 0
    )
    solicitudes_count = (
        db.query(func.count(GobiernoAccionSolicitud.id))
        .filter(GobiernoAccionSolicitud.organization_id == organization_id)
        .scalar()
        or 0
    )
    approval_ops_count = (
        db.query(func.count(ApprovalRequest.id))
        .filter(ApprovalRequest.organization_id == organization_id)
        .scalar()
        or 0
    )
    if policies_count > 0:
        controles.append(
            {
                "id": "acciones_controladas",
                "nombre": "Políticas de acción operacional",
                "estado": "ACTIVO",
                "evidencia": f"{policies_count} política(s) de acción",
                "detalle": {"politicas": policies_count, "tipos": list(TIPOS_ACCION)},
            }
        )
    if solicitudes_count > 0 or approval_ops_count > 0:
        controles.append(
            {
                "id": "aprobaciones",
                "nombre": "Flujo de aprobaciones",
                "estado": "ACTIVO",
                "evidencia": f"{solicitudes_count} solicitud(es) gobierno + {approval_ops_count} aprobación(es) operaciones",
                "detalle": {"solicitudes_gobierno": solicitudes_count, "aprobaciones_operaciones": approval_ops_count},
            }
        )

    # Gobierno IA
    ensure_default_ia_policy(db, organization_id)
    ia_policies = list_ia_policies(db, organization_id)
    if ia_policies:
        p = ia_policies[0]
        proveedores = p.get("proveedores_permitidos") or []
        modelos = p.get("modelos_permitidos") or []
        controles.append(
            {
                "id": "gobierno_ia",
                "nombre": "Políticas de gobierno IA",
                "estado": "ACTIVO",
                "evidencia": f"Política activa: {p['nombre']}",
                "detalle": {
                    "politicas": len(ia_policies),
                    "proveedores_configurados": len(proveedores),
                    "modelos_configurados": len(modelos),
                    "auto_ejecutar": p.get("auto_ejecutar"),
                },
            }
        )
        if proveedores or modelos:
            controles.append(
                {
                    "id": "proveedores_modelos",
                    "nombre": "Proveedores y modelos permitidos",
                    "estado": "CONFIGURADO",
                    "evidencia": f"{len(proveedores)} proveedor(es), {len(modelos)} modelo(s)",
                    "detalle": {"proveedores": proveedores, "modelos": modelos},
                }
            )

    # Visibilidad generalizada
    vis_count = (
        db.query(func.count(GobiernoVisibilidadLog.id))
        .filter(GobiernoVisibilidadLog.organization_id == organization_id)
        .scalar()
        or 0
    )
    if vis_count > 0:
        controles.append(
            {
                "id": "visibilidad",
                "nombre": "Trazabilidad de visibilidad",
                "estado": "ACTIVO",
                "evidencia": f"{vis_count} cambio(s) registrado(s)",
                "detalle": {"cambios": vis_count, "dominios": list(DOMINIOS_VISIBILIDAD)},
            }
        )

    gob_eventos = (
        db.query(func.count(GobiernoEvento.id))
        .filter(GobiernoEvento.organization_id == organization_id)
        .scalar()
        or 0
    )

    return {
        "organization_id": organization_id,
        "generado_en": _utcnow().isoformat(),
        "controles": controles,
        "resumen": {
            "controles_activos": len(controles),
            "eventos_gobierno": gob_eventos,
            "solo_evidencia_real": True,
        },
    }
