"""Servicio transversal — seguridad, gobierno de datos, trazabilidad y evidencia."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.empresa_audit_labels import (
    ESTADO_CONTROL_ES,
    GRUPO_CONTROLES_ES,
    etiqueta_accion,
    sanitizar_detalle,
)
from app.empresa_seguridad_models import (
    CLASIFICACION_ALIASES,
    ROLES_VINCULO_EVIDENCIA,
    TIPOS_EVIDENCIA,
    TIPOS_OBJETO_CLASIFICABLE,
    EmpresaEvidenciaVinculo,
    EmpresaObjetoClasificacion,
)
from app.gobierno_operacional_models import (
    NIVELES_VISIBILIDAD,
    GobiernoAccionSolicitud,
    GobiernoEvento,
    GobiernoVisibilidadLog,
)
from app.governance_models import GovAccessLog, GovCatalogEntry, GovClassificationLevel, GovSubjectRequest
from app.models import AuditLog, Organization, User
from app.orchestration_models import ApprovalRequest
from app.security_models import SecurityEvent
from app.services import gobierno_operacional_service as gob_svc
from app.services.governance_service import ensure_org_defaults, list_classification_levels


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


def normalizar_codigo_clasificacion(code: str) -> str:
    upper = code.strip().upper()
    return CLASIFICACION_ALIASES.get(upper, upper)


def _resolver_nivel(code: str, db: Session, organization_id: str) -> GovClassificationLevel:
    ensure_org_defaults(db, organization_id)
    norm = normalizar_codigo_clasificacion(code)
    row = (
        db.query(GovClassificationLevel)
        .filter(
            GovClassificationLevel.organization_id == organization_id,
            GovClassificationLevel.code == norm,
            GovClassificationLevel.is_active.is_(True),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=422, detail=f"Clasificación no válida: {code}")
    return row


def asignar_clasificacion(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    objeto_tipo: str,
    objeto_id: str,
    codigo_clasificacion: str,
    motivo: str | None = None,
    catalog_entry_id: str | None = None,
) -> dict[str, Any]:
    if objeto_tipo not in TIPOS_OBJETO_CLASIFICABLE:
        raise HTTPException(status_code=422, detail=f"tipo de objeto no clasificable: {objeto_tipo}")
    nivel = _resolver_nivel(codigo_clasificacion, db, organization_id)
    existing = (
        db.query(EmpresaObjetoClasificacion)
        .filter(
            EmpresaObjetoClasificacion.organization_id == organization_id,
            EmpresaObjetoClasificacion.objeto_tipo == objeto_tipo,
            EmpresaObjetoClasificacion.objeto_id == objeto_id,
            EmpresaObjetoClasificacion.activo.is_(True),
        )
        .first()
    )
    now = _utcnow()
    if existing:
        existing.classification_level_id = nivel.id
        existing.asignado_por = user_id
        existing.motivo = motivo
        existing.catalog_entry_id = catalog_entry_id
        existing.updated_at = now
        row = existing
    else:
        row = EmpresaObjetoClasificacion(
            organization_id=organization_id,
            objeto_tipo=objeto_tipo,
            objeto_id=objeto_id,
            classification_level_id=nivel.id,
            asignado_por=user_id,
            motivo=motivo,
            catalog_entry_id=catalog_entry_id,
            activo=True,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.flush()
    write_audit(
        db,
        action="empresa.clasificacion.asignada",
        organization_id=organization_id,
        user_id=user_id,
        detail=json.dumps(
            {"objeto_tipo": objeto_tipo, "objeto_id": objeto_id, "clasificacion": nivel.code},
            ensure_ascii=False,
        ),
        commit=False,
    )
    gob_svc.registrar_evento(
        db,
        organization_id=organization_id,
        actor_tipo="HUMANO",
        actor_id=user_id,
        accion="clasificacion.asignada",
        recurso_tipo=objeto_tipo,
        recurso_id=objeto_id,
        detalle={"clasificacion": nivel.code, "motivo": motivo},
    )
    return clasificacion_to_dict(db, row)


def obtener_clasificacion(
    db: Session, organization_id: str, objeto_tipo: str, objeto_id: str
) -> dict[str, Any] | None:
    row = (
        db.query(EmpresaObjetoClasificacion)
        .filter(
            EmpresaObjetoClasificacion.organization_id == organization_id,
            EmpresaObjetoClasificacion.objeto_tipo == objeto_tipo,
            EmpresaObjetoClasificacion.objeto_id == objeto_id,
            EmpresaObjetoClasificacion.activo.is_(True),
        )
        .first()
    )
    if not row:
        return None
    return clasificacion_to_dict(db, row)


def clasificacion_to_dict(db: Session, row: EmpresaObjetoClasificacion) -> dict[str, Any]:
    nivel = db.get(GovClassificationLevel, row.classification_level_id)
    return {
        "id": row.id,
        "objeto_tipo": row.objeto_tipo,
        "objeto_id": row.objeto_id,
        "codigo": nivel.code if nivel else None,
        "nombre": nivel.name if nivel else None,
        "sensibilidad": nivel.sensitivity_rank if nivel else None,
        "motivo": row.motivo,
        "catalog_entry_id": row.catalog_entry_id,
        "asignado_por": row.asignado_por,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def listar_clasificaciones_objeto(
    db: Session, organization_id: str, objeto_tipo: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    q = db.query(EmpresaObjetoClasificacion).filter(
        EmpresaObjetoClasificacion.organization_id == organization_id,
        EmpresaObjetoClasificacion.activo.is_(True),
    )
    if objeto_tipo:
        q = q.filter(EmpresaObjetoClasificacion.objeto_tipo == objeto_tipo)
    rows = q.order_by(EmpresaObjetoClasificacion.updated_at.desc()).limit(limit).all()
    return [clasificacion_to_dict(db, r) for r in rows]


def _nivel_desde_visible(visible: bool) -> str:
    return "VISIBLE_ENTIDAD" if visible else "INTERNO_EIAAX"


def set_visibilidad_nivel(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    dominio: str,
    contexto_id: str | None,
    objeto_tipo: str,
    objeto_id: str,
    nivel_visibilidad: str,
    motivo: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    if nivel_visibilidad not in NIVELES_VISIBILIDAD:
        raise HTTPException(status_code=422, detail=f"nivel de visibilidad inválido: {nivel_visibilidad}")
    prev = (
        db.query(GobiernoVisibilidadLog)
        .filter(
            GobiernoVisibilidadLog.organization_id == organization_id,
            GobiernoVisibilidadLog.dominio == dominio,
            GobiernoVisibilidadLog.objeto_id == objeto_id,
        )
        .order_by(GobiernoVisibilidadLog.created_at.desc())
        .first()
    )
    estado_anterior = prev.nivel_visibilidad if prev else None
    version = (prev.version or 0) + 1 if prev else 1
    visible = nivel_visibilidad == "VISIBLE_ENTIDAD"
    log = GobiernoVisibilidadLog(
        organization_id=organization_id,
        dominio=dominio,
        contexto_id=contexto_id,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        visible=visible,
        nivel_visibilidad=nivel_visibilidad,
        estado_anterior=estado_anterior,
        motivo=motivo,
        version=version,
        changed_by=user_id,
        correlation_id=correlation_id,
        created_at=_utcnow(),
    )
    db.add(log)
    write_audit(
        db,
        action="empresa.visibilidad.cambiada",
        organization_id=organization_id,
        user_id=user_id,
        detail=json.dumps(
            {
                "dominio": dominio,
                "objeto_id": objeto_id,
                "anterior": estado_anterior,
                "nuevo": nivel_visibilidad,
                "version": version,
            },
            ensure_ascii=False,
        ),
        commit=False,
    )
    gob_svc.registrar_evento(
        db,
        organization_id=organization_id,
        actor_tipo="HUMANO",
        actor_id=user_id,
        accion="visibilidad.cambiada",
        recurso_tipo=objeto_tipo,
        recurso_id=objeto_id,
        correlation_id=correlation_id,
        detalle={
            "dominio": dominio,
            "nivel": nivel_visibilidad,
            "anterior": estado_anterior,
            "motivo": motivo,
            "version": version,
        },
    )
    db.flush()
    return visibilidad_to_dict(log)


def visibilidad_to_dict(log: GobiernoVisibilidadLog) -> dict[str, Any]:
    return {
        "id": log.id,
        "dominio": log.dominio,
        "contexto_id": log.contexto_id,
        "objeto_tipo": log.objeto_tipo,
        "objeto_id": log.objeto_id,
        "visible": log.visible,
        "nivel_visibilidad": log.nivel_visibilidad,
        "estado_anterior": log.estado_anterior,
        "motivo": log.motivo,
        "version": log.version,
        "changed_by": log.changed_by,
        "correlation_id": log.correlation_id,
        "created_at": log.created_at,
    }


def vincular_evidencia(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    tipo_evidencia: str,
    referencia: str,
    objeto_tipo: str,
    objeto_id: str,
    rol_vinculo: str = "SOPORTE",
    descripcion: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    if tipo_evidencia not in TIPOS_EVIDENCIA:
        raise HTTPException(status_code=422, detail=f"tipo de evidencia inválido: {tipo_evidencia}")
    if rol_vinculo not in ROLES_VINCULO_EVIDENCIA:
        raise HTTPException(status_code=422, detail=f"rol de vínculo inválido: {rol_vinculo}")
    row = EmpresaEvidenciaVinculo(
        organization_id=organization_id,
        tipo_evidencia=tipo_evidencia,
        referencia=referencia,
        descripcion=descripcion,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        rol_vinculo=rol_vinculo,
        correlation_id=correlation_id or _uuid(),
        creado_por=user_id,
        created_at=_utcnow(),
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="empresa.evidencia.vinculada",
        organization_id=organization_id,
        user_id=user_id,
        detail=json.dumps(
            {"objeto_tipo": objeto_tipo, "objeto_id": objeto_id, "referencia": referencia},
            ensure_ascii=False,
        ),
        commit=False,
    )
    gob_svc.registrar_evento(
        db,
        organization_id=organization_id,
        actor_tipo="HUMANO",
        actor_id=user_id,
        accion="evidencia.vinculada",
        recurso_tipo=objeto_tipo,
        recurso_id=objeto_id,
        correlation_id=row.correlation_id,
        detalle={"referencia": referencia, "rol": rol_vinculo},
    )
    return evidencia_to_dict(row)


def listar_evidencias(
    db: Session,
    organization_id: str,
    *,
    objeto_tipo: str | None = None,
    objeto_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    q = db.query(EmpresaEvidenciaVinculo).filter(EmpresaEvidenciaVinculo.organization_id == organization_id)
    if objeto_tipo:
        q = q.filter(EmpresaEvidenciaVinculo.objeto_tipo == objeto_tipo)
    if objeto_id:
        q = q.filter(EmpresaEvidenciaVinculo.objeto_id == objeto_id)
    if correlation_id:
        q = q.filter(EmpresaEvidenciaVinculo.correlation_id == correlation_id)
    rows = q.order_by(EmpresaEvidenciaVinculo.created_at.desc()).limit(limit).all()
    return [evidencia_to_dict(r) for r in rows]


def evidencia_to_dict(row: EmpresaEvidenciaVinculo) -> dict[str, Any]:
    return {
        "id": row.id,
        "tipo_evidencia": row.tipo_evidencia,
        "referencia": row.referencia,
        "descripcion": row.descripcion,
        "objeto_tipo": row.objeto_tipo,
        "objeto_id": row.objeto_id,
        "rol_vinculo": row.rol_vinculo,
        "correlation_id": row.correlation_id,
        "creado_por": row.creado_por,
        "created_at": row.created_at,
    }


def _usuario_nombre(db: Session, user_id: str | None) -> str | None:
    if not user_id:
        return None
    u = db.get(User, user_id)
    return u.username if u else None


def consultar_auditoria(
    db: Session,
    organization_id: str,
    *,
    accion: str | None = None,
    user_id: str | None = None,
    correlation_id: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Auditoría federada comprensible en español — sin duplicar logs completos."""
    resultados: list[dict[str, Any]] = []

    # audit_logs global
    q = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)
    if accion:
        q = q.filter(AuditLog.action.contains(accion))
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if desde:
        q = q.filter(AuditLog.created_at >= desde)
    if hasta:
        q = q.filter(AuditLog.created_at <= hasta)
    for row in q.order_by(AuditLog.created_at.desc()).limit(limit).all():
        det = _loads(row.detail) if row.detail and row.detail.startswith("{") else row.detail
        corr = det.get("correlation_id") if isinstance(det, dict) else None
        if correlation_id and corr != correlation_id and correlation_id not in (row.detail or ""):
            continue
        resultados.append(
            {
                "fuente": "auditoria",
                "id": row.id,
                "accion": row.action,
                "accion_etiqueta": etiqueta_accion(row.action),
                "usuario_id": row.user_id,
                "usuario": _usuario_nombre(db, row.user_id),
                "organizacion_id": row.organization_id,
                "detalle": sanitizar_detalle(row.detail if isinstance(row.detail, str) else json.dumps(det, ensure_ascii=False)),
                "correlation_id": corr,
                "resultado": None,
                "fecha": row.created_at.isoformat() if row.created_at else None,
            }
        )

    # gobierno eventos
    gq = db.query(GobiernoEvento).filter(GobiernoEvento.organization_id == organization_id)
    if accion:
        gq = gq.filter(GobiernoEvento.accion.contains(accion))
    if correlation_id:
        gq = gq.filter(GobiernoEvento.correlation_id == correlation_id)
    for row in gq.order_by(GobiernoEvento.created_at.desc()).limit(limit).all():
        resultados.append(
            {
                "fuente": "gobierno",
                "id": row.id,
                "accion": row.accion,
                "accion_etiqueta": etiqueta_accion(f"gobierno.{row.accion}"),
                "usuario_id": row.actor_id if row.actor_tipo == "HUMANO" else None,
                "usuario": _usuario_nombre(db, row.actor_id) if row.actor_tipo == "HUMANO" else row.actor_tipo,
                "organizacion_id": row.organization_id,
                "detalle": sanitizar_detalle(json.dumps(_loads(row.detalle_json), ensure_ascii=False) if row.detalle_json else None),
                "correlation_id": row.correlation_id,
                "resultado": row.resultado,
                "fecha": row.created_at.isoformat() if row.created_at else None,
            }
        )

    resultados.sort(key=lambda x: x.get("fecha") or "", reverse=True)
    return resultados[:limit]


def obtener_trazabilidad(
    db: Session, organization_id: str, correlation_id: str
) -> dict[str, Any]:
    """Vista lógica: organización → proceso → evidencia → decisión → acción → resultado."""
    cadena: list[dict[str, Any]] = []

    solicitudes = (
        db.query(GobiernoAccionSolicitud)
        .filter(
            GobiernoAccionSolicitud.organization_id == organization_id,
            GobiernoAccionSolicitud.correlation_id == correlation_id,
        )
        .all()
    )
    for s in solicitudes:
        cadena.append(
            {
                "etapa": "solicitud",
                "tipo": s.tipo_accion,
                "estado": s.estado,
                "descripcion": s.descripcion,
                "fecha": s.created_at.isoformat() if s.created_at else None,
            }
        )

    aprobaciones = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.organization_id == organization_id)
        .all()
    )
    for a in aprobaciones:
        if correlation_id in (a.evidence_json or ""):
            cadena.append(
                {
                    "etapa": "aprobacion_legacy",
                    "estado": a.status,
                    "accion": a.action,
                    "fecha": a.created_at.isoformat() if a.created_at else None,
                }
            )

    eventos = (
        db.query(GobiernoEvento)
        .filter(
            GobiernoEvento.organization_id == organization_id,
            GobiernoEvento.correlation_id == correlation_id,
        )
        .order_by(GobiernoEvento.created_at)
        .all()
    )
    for e in eventos:
        cadena.append(
            {
                "etapa": "evento",
                "accion": e.accion,
                "decision": e.decision,
                "resultado": e.resultado,
                "fecha": e.created_at.isoformat() if e.created_at else None,
            }
        )

    evidencias = listar_evidencias(db, organization_id, correlation_id=correlation_id)
    for ev in evidencias:
        cadena.append(
            {
                "etapa": "evidencia",
                "referencia": ev["referencia"],
                "rol": ev["rol_vinculo"],
                "fecha": ev["created_at"].isoformat() if ev.get("created_at") else None,
            }
        )

    visibilidad = (
        db.query(GobiernoVisibilidadLog)
        .filter(
            GobiernoVisibilidadLog.organization_id == organization_id,
            GobiernoVisibilidadLog.correlation_id == correlation_id,
        )
        .all()
    )
    for v in visibilidad:
        cadena.append(
            {
                "etapa": "visibilidad",
                "nivel": v.nivel_visibilidad,
                "version": v.version,
                "fecha": v.created_at.isoformat() if v.created_at else None,
            }
        )

    cadena.sort(key=lambda x: x.get("fecha") or "")

    return {
        "organization_id": organization_id,
        "correlation_id": correlation_id,
        "cadena": cadena,
        "total_etapas": len(cadena),
    }


def _control(
    id_: str,
    nombre: str,
    grupo: str,
    estado: str,
    evidencia: str | None = None,
    detalle: dict | None = None,
) -> dict[str, Any]:
    return {
        "id": id_,
        "nombre": nombre,
        "grupo": grupo,
        "grupo_etiqueta": GRUPO_CONTROLES_ES.get(grupo, grupo),
        "estado": estado,
        "estado_etiqueta": ESTADO_CONTROL_ES.get(estado, estado),
        "evidencia": evidencia,
        "detalle": detalle,
    }


def get_centro_confianza_empresarial(db: Session, organization_id: str) -> dict[str, Any]:
    """Centro de Confianza evolucionado — solo controles verificables, agrupados."""
    base = gob_svc.get_centro_confianza(db, organization_id)
    controles: list[dict[str, Any]] = []

    # Mapear controles base a grupos con estados normalizados
    grupo_map = {
        "aislamiento": "acceso",
        "rbac": "acceso",
        "auditoria": "auditoria",
        "acciones_controladas": "aprobaciones",
        "aprobaciones": "aprobaciones",
        "gobierno_ia": "ia",
        "proveedores_modelos": "ia",
        "visibilidad": "trazabilidad",
    }
    for c in base.get("controles", []):
        grupo = grupo_map.get(c["id"], "datos")
        estado = "IMPLEMENTADO" if c.get("estado") == "ACTIVO" else "CONFIGURADO"
        controles.append(
            _control(c["id"], c["nombre"], grupo, estado, c.get("evidencia"), c.get("detalle"))
        )

    # Gobierno de datos 1350
    ensure_org_defaults(db, organization_id)
    catalog_count = (
        db.query(func.count(GovCatalogEntry.id))
        .filter(GovCatalogEntry.organization_id == organization_id, GovCatalogEntry.status == "ACTIVO")
        .scalar()
        or 0
    )
    cls_count = (
        db.query(func.count(GovClassificationLevel.id))
        .filter(GovClassificationLevel.organization_id == organization_id, GovClassificationLevel.is_active.is_(True))
        .scalar()
        or 0
    )
    if cls_count > 0:
        controles.append(
            _control(
                "clasificacion_datos",
                "Clasificación de información",
                "datos",
                "CONFIGURADO" if catalog_count == 0 else "IMPLEMENTADO",
                f"{cls_count} nivel(es) de clasificación",
                {"niveles": cls_count, "catalogo_activo": catalog_count},
            )
        )
    if catalog_count > 0:
        controles.append(
            _control(
                "catalogo_datos",
                "Catálogo de datos",
                "datos",
                "IMPLEMENTADO",
                f"{catalog_count} entrada(s) catalogadas",
                {"entradas": catalog_count},
            )
        )

    emp_cls = (
        db.query(func.count(EmpresaObjetoClasificacion.id))
        .filter(EmpresaObjetoClasificacion.organization_id == organization_id, EmpresaObjetoClasificacion.activo.is_(True))
        .scalar()
        or 0
    )
    if emp_cls > 0:
        controles.append(
            _control(
                "clasificacion_transversal",
                "Clasificación transversal de objetos",
                "datos",
                "IMPLEMENTADO",
                f"{emp_cls} objeto(s) clasificado(s)",
                {"objetos": emp_cls},
            )
        )

    # Privacidad — solicitudes de titular
    subject_count = (
        db.query(func.count(GovSubjectRequest.id))
        .filter(GovSubjectRequest.organization_id == organization_id)
        .scalar()
        or 0
    )
    if subject_count > 0:
        controles.append(
            _control(
                "privacidad_solicitudes",
                "Solicitudes de titular de datos",
                "privacidad",
                "IMPLEMENTADO",
                f"{subject_count} solicitud(es) registrada(s)",
                {"solicitudes": subject_count},
            )
        )
    else:
        controles.append(
            _control(
                "privacidad_solicitudes",
                "Solicitudes de titular de datos",
                "privacidad",
                "CONFIGURADO",
                "Módulo de privacidad disponible",
                None,
            )
        )

    # Seguridad — eventos
    sec_count = (
        db.query(func.count(SecurityEvent.id))
        .filter(SecurityEvent.organization_id == organization_id)
        .scalar()
        or 0
    )
    if sec_count > 0:
        controles.append(
            _control(
                "seguridad_eventos",
                "Eventos de seguridad",
                "acceso",
                "IMPLEMENTADO",
                f"{sec_count} evento(s) de seguridad",
                {"eventos": sec_count},
            )
        )

    # Trazabilidad — evidencias vinculadas
    evid_count = (
        db.query(func.count(EmpresaEvidenciaVinculo.id))
        .filter(EmpresaEvidenciaVinculo.organization_id == organization_id)
        .scalar()
        or 0
    )
    if evid_count > 0:
        controles.append(
            _control(
                "evidencia_vinculada",
                "Evidencia vinculada a decisiones",
                "trazabilidad",
                "IMPLEMENTADO",
                f"{evid_count} vínculo(s) de evidencia",
                {"vinculos": evid_count},
            )
        )

    # Continuidad — indicar disponibilidad sin afirmar certificación
    try:
        from app.continuidad_models import ContinuidadPlan

        plan_count = (
            db.query(func.count(ContinuidadPlan.id))
            .filter(ContinuidadPlan.organization_id == organization_id)
            .scalar()
            or 0
        )
        if plan_count > 0:
            controles.append(
                _control(
                    "continuidad_planes",
                    "Planes de continuidad",
                    "continuidad",
                    "IMPLEMENTADO",
                    f"{plan_count} plan(es) registrado(s)",
                    {"planes": plan_count},
                )
            )
        else:
            controles.append(
                _control(
                    "continuidad_planes",
                    "Planes de continuidad",
                    "continuidad",
                    "CONFIGURADO",
                    "Módulo de continuidad disponible",
                    None,
                )
            )
    except Exception:
        controles.append(
            _control(
                "continuidad_planes",
                "Planes de continuidad",
                "continuidad",
                "NO_DISPONIBLE",
                None,
                None,
            )
        )

    # IA — catálogo proveedores reservado BP2
    controles.append(
        _control(
            "catalogo_proveedores_ia",
            "Catálogo cerrado de proveedores IA",
            "ia",
            "PENDIENTE",
            "Reservado para integración BP2 — no certificado",
            {"integracion": "BP2_GENERAL"},
        )
    )

    # Agrupar
    grupos: dict[str, list] = {}
    for c in controles:
        g = c["grupo"]
        grupos.setdefault(g, []).append(c)

    return {
        "organization_id": organization_id,
        "generado_en": _utcnow().isoformat(),
        "controles": controles,
        "grupos": [
            {"id": g, "etiqueta": GRUPO_CONTROLES_ES.get(g, g), "controles": items}
            for g, items in grupos.items()
        ],
        "resumen": {
            "total_controles": len(controles),
            "implementados": sum(1 for c in controles if c["estado"] == "IMPLEMENTADO"),
            "configurados": sum(1 for c in controles if c["estado"] == "CONFIGURADO"),
            "pendientes": sum(1 for c in controles if c["estado"] == "PENDIENTE"),
            "no_disponibles": sum(1 for c in controles if c["estado"] == "NO_DISPONIBLE"),
            "solo_evidencia_real": True,
        },
    }


def exportar_evidencia_gobierno(
    db: Session, organization_id: str, *, limit: int = 200
) -> dict[str, Any]:
    """Exportación consultable de evidencia de gobierno — sin generador paralelo."""
    auditoria = consultar_auditoria(db, organization_id, limit=limit)
    clasificaciones = listar_clasificaciones_objeto(db, organization_id, limit=limit)
    evidencias = listar_evidencias(db, organization_id, limit=limit)
    for c in clasificaciones:
        for key in ("created_at", "updated_at"):
            if c.get(key) and hasattr(c[key], "isoformat"):
                c[key] = c[key].isoformat()
    for e in evidencias:
        if e.get("created_at") and hasattr(e["created_at"], "isoformat"):
            e["created_at"] = e["created_at"].isoformat()
    return {
        "organization_id": organization_id,
        "exportado_en": _utcnow().isoformat(),
        "auditoria": auditoria,
        "clasificaciones": clasificaciones,
        "evidencias": evidencias,
        "total_registros": len(auditoria) + len(clasificaciones) + len(evidencias),
    }


def obtener_gobierno_objeto(
    db: Session, organization_id: str, objeto_tipo: str, objeto_id: str
) -> dict[str, Any]:
    """Vista consolidada de gobierno de datos para un objeto."""
    cls = obtener_clasificacion(db, organization_id, objeto_tipo, objeto_id)
    evidencias = listar_evidencias(db, organization_id, objeto_tipo=objeto_tipo, objeto_id=objeto_id)
    vis = (
        db.query(GobiernoVisibilidadLog)
        .filter(
            GobiernoVisibilidadLog.organization_id == organization_id,
            GobiernoVisibilidadLog.objeto_tipo == objeto_tipo,
            GobiernoVisibilidadLog.objeto_id == objeto_id,
        )
        .order_by(GobiernoVisibilidadLog.created_at.desc())
        .limit(10)
        .all()
    )
    catalog = None
    if cls and cls.get("catalog_entry_id"):
        entry = db.get(GovCatalogEntry, cls["catalog_entry_id"])
        if entry:
            catalog = {"id": entry.id, "nombre": entry.name, "estado": entry.status}
    return {
        "objeto_tipo": objeto_tipo,
        "objeto_id": objeto_id,
        "clasificacion": cls,
        "catalogo": catalog,
        "evidencias": evidencias,
        "visibilidad": [visibilidad_to_dict(v) for v in vis],
    }
