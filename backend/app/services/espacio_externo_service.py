"""Servicio — espacio externo controlado empresa/prospecto/cliente V1."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.communications_models import CommMessage
from app.espacio_externo_models import (
    AUDIENCIAS_PUBLICACION,
    CAPACIDADES_CONTRATO_CLIENTE,
    ESTADOS_PUBLICACION,
    ESTADOS_RELACION,
    ESTADOS_VALIDACION_EXTERNA,
    FUENTES_INFORMACION,
    PAQUETES_PUBLICACION,
    ROLES_ACCESO_EXTERNO,
    EmpresaPublicacion,
    EmpresaPublicacionHistorial,
    EntidadEmpresa,
    EntidadEmpresaAcceso,
    EvaluacionEntregaExterna,
)
from app.evaluacion_models import EvaluacionInformacionItem
from app.models import User
from app.orchestration_models import AIEmployee
from app.security import hash_password
from app.services import agent_factory as agent_svc
from app.services import communications_service as comm_svc
from app.services import evaluacion_service as eval_svc
from app.services import evidencia_entrega_service as evid_svc
from app.services import implementacion_service as impl_svc
from app.services import support_service as support_svc
from app.services.espacio_externo_adapters import (
    adaptar_empleado_ia_detalle_externo,
    adaptar_empleados_ia_externo,
    adaptar_implementacion_externa,
    adaptar_informe_detalle_externo,
    adaptar_informes_externo,
    adaptar_resultados_externo,
    adaptar_soporte_caso_externo,
    adaptar_soporte_lista_externa,
)

# Paquetes visibles por estado de relación
_PAQUETES_POR_ESTADO: dict[str, frozenset[str]] = {
    "PROSPECTO_EVALUACION": frozenset({"INICIO", "INFORMACION"}),
    "PROSPECTO_RESULTADOS": frozenset({"INICIO", "INFORMACION", "RESULTADOS", "PROPUESTA"}),
    "CLIENTE_CONTRATADO": frozenset(PAQUETES_PUBLICACION),
}

_DEFAULT_PAQUETES = tuple(sorted(PAQUETES_PUBLICACION))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


def _parse_contrato(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {"capacidades": [], "empleados_ia_ids": []}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"capacidades": [], "empleados_ia_ids": []}
    if isinstance(parsed, list):
        return {"capacidades": list(parsed), "empleados_ia_ids": []}
    return {
        "capacidades": list(parsed.get("capacidades") or []),
        "empleados_ia_ids": list(parsed.get("empleados_ia_ids") or []),
    }


def _dump_contrato(capacidades: list[str], empleados_ia_ids: list[str] | None = None) -> str:
    payload: dict[str, Any] = {"capacidades": capacidades}
    if empleados_ia_ids:
        payload["empleados_ia_ids"] = empleados_ia_ids
    return json.dumps(payload)


def _cliente_tiene_capacidad(entidad: EntidadEmpresa, capacidad: str) -> bool:
    if entidad.estado_relacion != "CLIENTE_CONTRATADO":
        return False
    return capacidad in _parse_contrato(entidad.capacidades_contrato_json)["capacidades"]


def _assert_cliente_capacidad(entidad: EntidadEmpresa, capacidad: str) -> None:
    if not _cliente_tiene_capacidad(entidad, capacidad):
        raise HTTPException(status_code=403, detail=f"Contrato sin capacidad {capacidad}")


def _entidad_dict(e: EntidadEmpresa) -> dict[str, Any]:
    contrato = _parse_contrato(e.capacidades_contrato_json)
    return {
        "id": e.id,
        "expediente_id": e.expediente_id,
        "nombre": e.nombre,
        "contacto_email": e.contacto_email,
        "estado_relacion": e.estado_relacion,
        "contrato_ref": e.contrato_ref,
        "proyecto_id": e.proyecto_id,
        "capacidades_contrato": contrato["capacidades"],
        "empleados_ia_ids": contrato["empleados_ia_ids"],
        "correlation_id": e.correlation_id,
        "promoted_at": e.promoted_at.isoformat() if e.promoted_at else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _publicacion_dict(p: EmpresaPublicacion) -> dict[str, Any]:
    return {
        "id": p.id,
        "paquete": p.paquete,
        "estado": p.estado,
        "version": p.version,
        "destinatario": p.destinatario,
        "audiencia": p.audiencia,
        "snapshot_hash": p.snapshot_hash,
        "publicado_por": p.publicado_por,
        "publicado_at": p.publicado_at.isoformat() if p.publicado_at else None,
    }


def _entrega_dict(
    e: EvaluacionEntregaExterna,
    db: Session | None = None,
    *,
    include_internal: bool = False,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": e.id,
        "titulo": e.titulo,
        "descripcion": e.descripcion,
        "estado": e.estado,
        "fuente_tipo": e.fuente_tipo,
        "contenido": e.contenido,
        "evidencia_ref": e.evidencia_ref,
        "version": e.version,
        "informacion_item_id": e.informacion_item_id,
        "observacion_publica": e.observacion_publica,
        "solicitado_at": e.solicitado_at.isoformat() if e.solicitado_at else None,
        "entregado_at": e.entregado_at.isoformat() if e.entregado_at else None,
        "validado_at": e.validado_at.isoformat() if e.validado_at else None,
        "suficiencia_minima_at": e.suficiencia_minima_at.isoformat() if e.suficiencia_minima_at else None,
    }
    if include_internal:
        out["observacion_interna"] = e.observacion_interna
    if db is not None:
        out["adjuntos"] = evid_svc.list_adjuntos_entrega(
            db, e.organization_id, e.id, include_internal=include_internal
        )
    return out


def _get_entidad(db: Session, entidad_id: str, organization_id: str) -> EntidadEmpresa:
    row = (
        db.query(EntidadEmpresa)
        .filter(EntidadEmpresa.id == entidad_id, EntidadEmpresa.organization_id == organization_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Entidad empresa no encontrada")
    return row


def _ensure_publicaciones_default(db: Session, entidad: EntidadEmpresa) -> list[EmpresaPublicacion]:
    existing = {
        p.paquete: p
        for p in db.query(EmpresaPublicacion)
        .filter(EmpresaPublicacion.entidad_id == entidad.id)
        .all()
    }
    out: list[EmpresaPublicacion] = []
    for paquete in _DEFAULT_PAQUETES:
        if paquete in existing:
            out.append(existing[paquete])
            continue
        p = EmpresaPublicacion(
            organization_id=entidad.organization_id,
            entidad_id=entidad.id,
            expediente_id=entidad.expediente_id,
            paquete=paquete,
            estado="PRIVADO",
            version=1,
        )
        db.add(p)
        out.append(p)
    db.flush()
    return out


def create_entidad_from_expediente(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    expediente_id: str,
    contacto_email: str | None = None,
) -> dict[str, Any]:
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    existing = (
        db.query(EntidadEmpresa)
        .filter(
            EntidadEmpresa.organization_id == organization_id,
            EntidadEmpresa.expediente_id == expediente_id,
        )
        .first()
    )
    if existing:
        return {"entidad": _entidad_dict(existing), "reused": True}
    entidad = EntidadEmpresa(
        organization_id=organization_id,
        expediente_id=exp.id,
        nombre=exp.entidad_nombre,
        contacto_email=contacto_email,
        estado_relacion="PROSPECTO_EVALUACION",
        correlation_id=exp.correlation_id,
        created_by=user_id,
    )
    db.add(entidad)
    db.flush()
    pubs = _ensure_publicaciones_default(db, entidad)
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.entidad_created",
        detail=json.dumps({"entidad_id": entidad.id, "expediente_id": exp.id}),
        commit=False,
    )
    return {
        "entidad": _entidad_dict(entidad),
        "publicaciones": [_publicacion_dict(p) for p in pubs],
        "reused": False,
    }


def invite_external_user(
    db: Session,
    organization_id: str,
    admin_id: str,
    *,
    entidad_id: str,
    email: str,
    full_name: str,
    rol_externo: str = "PROSPECTO",
    password: str | None = None,
) -> dict[str, Any]:
    if rol_externo not in ROLES_ACCESO_EXTERNO:
        raise HTTPException(status_code=422, detail="rol_externo inválido")
    entidad = _get_entidad(db, entidad_id, organization_id)
    username = email.strip().lower()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        pwd = password or f"Ext-{uuid.uuid4().hex[:10]}!"
        user = User(
            organization_id=organization_id,
            username=username,
            email=email,
            full_name=full_name,
            password_hash=hash_password(pwd),
            role="external_prospect",
            status="ACTIVE",
            is_active=True,
            created_by_id=admin_id,
        )
        db.add(user)
        db.flush()
    acceso = (
        db.query(EntidadEmpresaAcceso)
        .filter(EntidadEmpresaAcceso.entidad_id == entidad.id, EntidadEmpresaAcceso.user_id == user.id)
        .first()
    )
    if acceso:
        acceso.activo = True
        acceso.revoked_at = None
        acceso.revoked_by = None
        acceso.rol_externo = rol_externo
    else:
        acceso = EntidadEmpresaAcceso(
            organization_id=organization_id,
            entidad_id=entidad.id,
            user_id=user.id,
            rol_externo=rol_externo,
            invited_by=admin_id,
            activo=True,
        )
        db.add(acceso)
    write_audit(
        db,
        organization_id=organization_id,
        user_id=admin_id,
        action="espacio_externo.acceso_invited",
        detail=json.dumps({"entidad_id": entidad.id, "user_id": user.id, "rol": rol_externo}),
        commit=False,
    )
    return {"user_id": user.id, "username": user.username, "acceso_id": acceso.id, "rol_externo": rol_externo}


def revoke_access(
    db: Session,
    organization_id: str,
    admin_id: str,
    acceso_id: str,
) -> dict[str, Any]:
    acceso = (
        db.query(EntidadEmpresaAcceso)
        .filter(
            EntidadEmpresaAcceso.id == acceso_id,
            EntidadEmpresaAcceso.organization_id == organization_id,
        )
        .first()
    )
    if not acceso:
        raise HTTPException(status_code=404, detail="Acceso no encontrado")
    acceso.activo = False
    acceso.revoked_by = admin_id
    acceso.revoked_at = _utcnow()
    write_audit(
        db,
        organization_id=organization_id,
        user_id=admin_id,
        action="espacio_externo.acceso_revoked",
        detail=json.dumps({"acceso_id": acceso.id}),
        commit=False,
    )
    return {"id": acceso.id, "activo": False}


def promote_to_cliente(
    db: Session,
    organization_id: str,
    user_id: str,
    entidad_id: str,
    *,
    contrato_ref: str | None = None,
    capacidades: list[str] | None = None,
) -> dict[str, Any]:
    entidad = _get_entidad(db, entidad_id, organization_id)
    prev = entidad.estado_relacion
    entidad.estado_relacion = "CLIENTE_CONTRATADO"
    entidad.contrato_ref = contrato_ref or entidad.contrato_ref
    entidad.promoted_at = _utcnow()
    entidad.updated_at = _utcnow()
    if capacidades is not None:
        invalid = [c for c in capacidades if c not in CAPACIDADES_CONTRATO_CLIENTE]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Capacidades inválidas: {invalid}")
        contrato = _parse_contrato(entidad.capacidades_contrato_json)
        entidad.capacidades_contrato_json = _dump_contrato(capacidades, contrato["empleados_ia_ids"])
    elif not entidad.capacidades_contrato_json:
        entidad.capacidades_contrato_json = _dump_contrato(["RESULTADOS", "INFORMES", "SOPORTE"])
    for acc in (
        db.query(EntidadEmpresaAcceso)
        .filter(EntidadEmpresaAcceso.entidad_id == entidad.id, EntidadEmpresaAcceso.activo.is_(True))
        .all()
    ):
        acc.rol_externo = "CLIENTE"
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.promoted_cliente",
        detail=json.dumps({"entidad_id": entidad.id, "antes": prev}),
        commit=False,
    )
    return _entidad_dict(entidad)


def link_proyecto(
    db: Session,
    organization_id: str,
    user_id: str,
    entidad_id: str,
    *,
    proyecto_id: str,
) -> dict[str, Any]:
    entidad = _get_entidad(db, entidad_id, organization_id)
    impl_svc._get_proyecto(db, organization_id, proyecto_id)  # noqa: SLF001
    entidad.proyecto_id = proyecto_id
    entidad.updated_at = _utcnow()
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.link_proyecto",
        detail=json.dumps({"entidad_id": entidad.id, "proyecto_id": proyecto_id}),
        commit=False,
    )
    return _entidad_dict(entidad)


def configure_contrato(
    db: Session,
    organization_id: str,
    user_id: str,
    entidad_id: str,
    *,
    capacidades: list[str],
    empleados_ia_ids: list[str] | None = None,
) -> dict[str, Any]:
    invalid = [c for c in capacidades if c not in CAPACIDADES_CONTRATO_CLIENTE]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Capacidades inválidas: {invalid}")
    entidad = _get_entidad(db, entidad_id, organization_id)
    entidad.capacidades_contrato_json = _dump_contrato(capacidades, empleados_ia_ids)
    entidad.updated_at = _utcnow()
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.configure_contrato",
        detail=json.dumps({"entidad_id": entidad.id, "capacidades": capacidades}),
        commit=False,
    )
    return _entidad_dict(entidad)


def set_publicacion_estado(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    publicacion_id: str,
    estado: str,
    destinatario: str | None = None,
    motivo: str | None = None,
    audiencia: str | None = None,
) -> dict[str, Any]:
    if estado not in ESTADOS_PUBLICACION:
        raise HTTPException(status_code=422, detail="estado de publicación inválido")
    if audiencia is not None and audiencia not in AUDIENCIAS_PUBLICACION:
        raise HTTPException(status_code=422, detail="audiencia inválida")
    pub = (
        db.query(EmpresaPublicacion)
        .filter(
            EmpresaPublicacion.id == publicacion_id,
            EmpresaPublicacion.organization_id == organization_id,
        )
        .first()
    )
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    prev = pub.estado
    if estado == "PUBLICADO_EMPRESA" and prev == "PUBLICADO_EMPRESA":
        raise HTTPException(
            status_code=409,
            detail="Versión ya publicada; cree nueva versión antes de modificar contenido compartido",
        )
    if estado == "PUBLICADO_EMPRESA":
        vista = eval_svc.get_vista_entidad(db, pub.expediente_id, organization_id)
        pub.snapshot_hash = hashlib.sha256(json.dumps(vista, sort_keys=True, default=str).encode()).hexdigest()[:16]
        pub.publicado_por = user_id
        pub.publicado_at = _utcnow()
        pub.version += 1 if prev == "PUBLICADO_EMPRESA" else 0
    pub.estado = estado
    if destinatario:
        pub.destinatario = destinatario
    if audiencia is not None:
        pub.audiencia = audiencia
    pub.updated_at = _utcnow()
    hist = EmpresaPublicacionHistorial(
        publicacion_id=pub.id,
        organization_id=organization_id,
        estado_anterior=prev,
        estado_nuevo=estado,
        version=pub.version,
        destinatario=pub.destinatario,
        motivo=motivo,
        changed_by=user_id,
    )
    db.add(hist)
    if estado == "PUBLICADO_EMPRESA":
        entidad = _get_entidad(db, pub.entidad_id, organization_id)
        if entidad.estado_relacion == "PROSPECTO_EVALUACION" and pub.paquete in ("RESULTADOS", "PROPUESTA"):
            entidad.estado_relacion = "PROSPECTO_RESULTADOS"
            entidad.updated_at = _utcnow()
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.publicacion",
        detail=json.dumps({"publicacion_id": pub.id, "estado": estado, "version": pub.version}),
        commit=False,
    )
    return _publicacion_dict(pub)


def get_publicacion_historial(db: Session, organization_id: str, publicacion_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(EmpresaPublicacionHistorial)
        .filter(
            EmpresaPublicacionHistorial.publicacion_id == publicacion_id,
            EmpresaPublicacionHistorial.organization_id == organization_id,
        )
        .order_by(EmpresaPublicacionHistorial.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "estado_anterior": r.estado_anterior,
            "estado_nuevo": r.estado_nuevo,
            "version": r.version,
            "destinatario": r.destinatario,
            "motivo": r.motivo,
            "changed_by": r.changed_by,
            "fecha": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def list_entidades(db: Session, organization_id: str, *, expediente_id: str | None = None) -> list[dict[str, Any]]:
    q = db.query(EntidadEmpresa).filter(EntidadEmpresa.organization_id == organization_id)
    if expediente_id:
        q = q.filter(EntidadEmpresa.expediente_id == expediente_id)
    return [_entidad_dict(e) for e in q.order_by(EntidadEmpresa.created_at.desc()).all()]


def get_entidad_detail(db: Session, organization_id: str, entidad_id: str) -> dict[str, Any]:
    entidad = _get_entidad(db, entidad_id, organization_id)
    pubs = (
        db.query(EmpresaPublicacion)
        .filter(EmpresaPublicacion.entidad_id == entidad.id)
        .order_by(EmpresaPublicacion.paquete)
        .all()
    )
    accesos = (
        db.query(EntidadEmpresaAcceso)
        .filter(EntidadEmpresaAcceso.entidad_id == entidad.id)
        .all()
    )
    return {
        "entidad": _entidad_dict(entidad),
        "publicaciones": [_publicacion_dict(p) for p in pubs],
        "accesos": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "rol_externo": a.rol_externo,
                "activo": a.activo,
                "revoked_at": a.revoked_at.isoformat() if a.revoked_at else None,
            }
            for a in accesos
        ],
    }


def _resolve_external_acceso(db: Session, user: User) -> EntidadEmpresaAcceso:
    acceso = (
        db.query(EntidadEmpresaAcceso)
        .filter(
            EntidadEmpresaAcceso.user_id == user.id,
            EntidadEmpresaAcceso.organization_id == user.organization_id,
            EntidadEmpresaAcceso.activo.is_(True),
        )
        .first()
    )
    if not acceso:
        raise HTTPException(status_code=403, detail="Sin acceso al espacio externo")
    return acceso


def _paquete_publicado(db: Session, entidad_id: str, paquete: str) -> bool:
    pub = (
        db.query(EmpresaPublicacion)
        .filter(
            EmpresaPublicacion.entidad_id == entidad_id,
            EmpresaPublicacion.paquete == paquete,
        )
        .first()
    )
    return pub is not None and pub.estado == "PUBLICADO_EMPRESA"


def _assert_paquete_accesible(entidad: EntidadEmpresa, paquete: str, *, requiere_publicado: bool = True) -> None:
    permitidos = _PAQUETES_POR_ESTADO.get(entidad.estado_relacion, frozenset())
    if paquete not in permitidos:
        raise HTTPException(status_code=403, detail=f"Paquete {paquete} no disponible en esta etapa")


def get_portal_context(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    pubs = (
        db.query(EmpresaPublicacion)
        .filter(EmpresaPublicacion.entidad_id == entidad.id)
        .all()
    )
    paquetes_visibles = _PAQUETES_POR_ESTADO.get(entidad.estado_relacion, frozenset())
    secciones: list[dict[str, Any]] = []
    for paquete in sorted(paquetes_visibles):
        pub = next((p for p in pubs if p.paquete == paquete), None)
        secciones.append({
            "paquete": paquete,
            "estado_publicacion": pub.estado if pub else "PRIVADO",
            "accesible": pub is not None and pub.estado == "PUBLICADO_EMPRESA",
            "version": pub.version if pub else 0,
        })
    return {
        "entidad": _entidad_dict(entidad),
        "rol_externo": acceso.rol_externo,
        "estado_relacion": entidad.estado_relacion,
        "contrato_ref": entidad.contrato_ref if entidad.estado_relacion == "CLIENTE_CONTRATADO" else None,
        "secciones": secciones,
    }


def get_portal_inicio(db: Session, user: User) -> dict[str, Any]:
    ctx = get_portal_context(db, user)
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    exp = eval_svc._get_expediente(db, entidad.expediente_id, user.organization_id)  # noqa: SLF001
    return {
        **ctx,
        "expediente": {
            "codigo": exp.codigo,
            "titulo": exp.titulo,
            "estado": exp.estado,
            "nivel": exp.nivel,
            "objetivo": exp.objetivo,
        },
    }


def get_portal_informacion(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "INFORMACION", requiere_publicado=False)
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == entidad.expediente_id)
        .order_by(EvaluacionInformacionItem.orden)
        .all()
    )
    entregas = (
        db.query(EvaluacionEntregaExterna)
        .filter(EvaluacionEntregaExterna.entidad_id == entidad.id)
        .order_by(EvaluacionEntregaExterna.solicitado_at.desc())
        .all()
    )
    return {
        "solicitudes": [
            {
                "id": i.id,
                "etiqueta": i.etiqueta,
                "explicacion": i.explicacion,
                "obligatorio": i.obligatorio,
                "estado": i.estado,
                "estado_validacion": i.estado_validacion or "PENDIENTE",
                "puede_entregar": i.estado in ("PENDIENTE", "INCOMPLETO") or i.estado_validacion == "REQUIERE_COMPLEMENTO",
            }
            for i in items
            if i.obligatorio or i.estado != "OPCIONAL"
        ],
        "entregas": [_entrega_dict(e, db) for e in entregas],
    }


def external_entregar(
    db: Session,
    user: User,
    *,
    item_id: str | None = None,
    entrega_id: str | None = None,
    contenido: str,
    evidencia_ref: str | None = None,
    fuente_tipo: str = "SUMINISTRADA_EMPRESA",
) -> dict[str, Any]:
    if fuente_tipo not in FUENTES_INFORMACION:
        raise HTTPException(status_code=422, detail="fuente_tipo inválida")
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    now = _utcnow()
    if entrega_id:
        entrega = (
            db.query(EvaluacionEntregaExterna)
            .filter(
                EvaluacionEntregaExterna.id == entrega_id,
                EvaluacionEntregaExterna.entidad_id == entidad.id,
            )
            .first()
        )
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada")
        if entrega.estado == "VALIDADO":
            entrega.version += 1
        entrega.contenido = contenido
        entrega.evidencia_ref = evidencia_ref
        entrega.fuente_tipo = fuente_tipo
        entrega.estado = "RECIBIDO"
        entrega.entregado_por = user.id
        entrega.entregado_at = now
        item_id = entrega.informacion_item_id
    elif item_id:
        item = (
            db.query(EvaluacionInformacionItem)
            .filter(
                EvaluacionInformacionItem.id == item_id,
                EvaluacionInformacionItem.expediente_id == entidad.expediente_id,
            )
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Ítem de información no encontrado")
        entrega = EvaluacionEntregaExterna(
            organization_id=user.organization_id,
            expediente_id=entidad.expediente_id,
            entidad_id=entidad.id,
            informacion_item_id=item.id,
            titulo=item.etiqueta,
            descripcion=item.explicacion,
            estado="RECIBIDO",
            fuente_tipo=fuente_tipo,
            contenido=contenido,
            evidencia_ref=evidencia_ref,
            entregado_por=user.id,
            entregado_at=now,
            correlation_id=entidad.correlation_id,
        )
        db.add(entrega)
        item.respuesta = contenido
        item.evidencia_ref = evidencia_ref
        item.fuente_tipo = fuente_tipo
        item.estado = "RECIBIDO"
        item.estado_validacion = "EN_VALIDACION"
        item.entregado_por = user.id
        item.entregado_at = now
        item.updated_at = now
    else:
        raise HTTPException(status_code=422, detail="item_id o entrega_id requerido")
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="espacio_externo.entrega",
        detail=json.dumps({"entrega_id": entrega.id, "item_id": item_id}),
        commit=False,
    )
    db.flush()
    return _entrega_dict(entrega, db)


def upload_adjuntos_portal(
    db: Session,
    user: User,
    *,
    entrega_id: str | None = None,
    item_id: str | None = None,
    files: list[tuple[str, bytes, str | None]],
    observacion: str | None = None,
    fuente_tipo: str = "SUMINISTRADA_EMPRESA",
) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    return evid_svc.upload_adjuntos_externo(
        db,
        user,
        entrega_id=entrega_id,
        item_id=item_id,
        files=files,
        observacion=observacion,
        fuente_tipo=fuente_tipo,
        entidad_id=entidad.id,
        expediente_id=entidad.expediente_id,
        correlation_id=entidad.correlation_id,
    )


def reemplazar_adjunto_portal(
    db: Session,
    user: User,
    adjunto_id: str,
    *,
    filename: str,
    data: bytes,
    mime_type: str | None,
    observacion: str | None = None,
) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    return evid_svc.reemplazar_adjunto_externo(
        db,
        user,
        adjunto_id,
        filename=filename,
        data=data,
        mime_type=mime_type,
        observacion=observacion,
        entidad_id=entidad.id,
    )


def download_adjunto_portal(db: Session, user: User, adjunto_id: str) -> tuple[str, bytes, str | None]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    return evid_svc.download_adjunto(
        db,
        user.organization_id,
        adjunto_id,
        entidad_id=entidad.id,
        user_id=user.id,
        acceso_activo=acceso.activo,
    )


def list_adjuntos_entrega_interna(db: Session, organization_id: str, entrega_id: str) -> list[dict[str, Any]]:
    _get_entrega_for_validation(db, organization_id, entrega_id)
    return evid_svc.list_adjuntos_entrega(db, organization_id, entrega_id, include_internal=True)


def list_historial_adjunto_interna(
    db: Session, organization_id: str, grupo_archivo: str
) -> list[dict[str, Any]]:
    return evid_svc.list_historial_grupo(db, organization_id, grupo_archivo, include_internal=True)


def download_adjunto_interna(
    db: Session, organization_id: str, user_id: str, adjunto_id: str
) -> tuple[str, bytes, str | None]:
    return evid_svc.download_adjunto(
        db, organization_id, adjunto_id, user_id=user_id, acceso_activo=True
    )


def validar_adjunto_interna(
    db: Session,
    organization_id: str,
    user_id: str,
    adjunto_id: str,
    *,
    estado: str,
    observacion_publica: str | None = None,
    observacion_interna: str | None = None,
) -> dict[str, Any]:
    return evid_svc.validar_adjunto_interno(
        db,
        organization_id,
        user_id,
        adjunto_id,
        estado=estado,
        observacion_publica=observacion_publica,
        observacion_interna=observacion_interna,
    )


def _get_entrega_for_validation(db: Session, organization_id: str, entrega_id: str) -> EvaluacionEntregaExterna:
    entrega = (
        db.query(EvaluacionEntregaExterna)
        .filter(
            EvaluacionEntregaExterna.id == entrega_id,
            EvaluacionEntregaExterna.organization_id == organization_id,
        )
        .first()
    )
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    return entrega


def validar_entrega_interna(
    db: Session,
    organization_id: str,
    user_id: str,
    entrega_id: str,
    *,
    estado: str,
    marcar_suficiencia: bool = False,
    observacion_publica: str | None = None,
    observacion_interna: str | None = None,
) -> dict[str, Any]:
    if estado not in ESTADOS_VALIDACION_EXTERNA:
        raise HTTPException(status_code=422, detail="estado de validación inválido")
    entrega = (
        db.query(EvaluacionEntregaExterna)
        .filter(
            EvaluacionEntregaExterna.id == entrega_id,
            EvaluacionEntregaExterna.organization_id == organization_id,
        )
        .first()
    )
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    now = _utcnow()
    entrega.estado = estado
    entrega.validado_por = user_id
    entrega.validado_at = now
    if observacion_publica is not None:
        entrega.observacion_publica = observacion_publica
    if observacion_interna is not None:
        entrega.observacion_interna = observacion_interna
    if marcar_suficiencia:
        entrega.suficiencia_minima_at = now
    if entrega.informacion_item_id:
        item = db.query(EvaluacionInformacionItem).filter(EvaluacionInformacionItem.id == entrega.informacion_item_id).first()
        if item:
            item.estado_validacion = estado
            if estado == "VALIDADO":
                item.estado = "RECIBIDO"
            elif estado == "REQUIERE_COMPLEMENTO":
                item.estado = "INCOMPLETO"
            item.validado_at = now
            if marcar_suficiencia:
                item.suficiencia_minima_at = now
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.validacion",
        detail=json.dumps({"entrega_id": entrega.id, "estado": estado}),
        commit=False,
    )
    return _entrega_dict(entrega, db, include_internal=True)


def get_portal_estado(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    exp = eval_svc._get_expediente(db, entidad.expediente_id, user.organization_id)  # noqa: SLF001
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == entidad.expediente_id)
        .all()
    )
    obligatorios = [i for i in items if i.obligatorio]
    recibidos = sum(1 for i in obligatorios if i.estado == "RECIBIDO")
    suficiencia = any(i.suficiencia_minima_at for i in obligatorios)
    return {
        "estado_relacion": entidad.estado_relacion,
        "expediente_estado": exp.estado,
        "porcentaje_informacion": exp.porcentaje_informacion,
        "informacion_minima_suficiente": suficiencia,
        "pendientes": [
            i.etiqueta for i in obligatorios
            if i.estado in ("PENDIENTE", "INCOMPLETO") and i.estado_validacion != "VALIDADO"
        ],
    }


def get_portal_vista_entidad(db: Session, user: User, paquete: str = "RESULTADOS") -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, paquete)
    if not _paquete_publicado(db, entidad.id, paquete):
        raise HTTPException(status_code=403, detail="Contenido no publicado para la empresa")
    vista = adaptar_resultados_externo(
        eval_svc.get_vista_entidad(db, entidad.expediente_id, user.organization_id)
    )
    pub = (
        db.query(EmpresaPublicacion)
        .filter(EmpresaPublicacion.entidad_id == entidad.id, EmpresaPublicacion.paquete == paquete)
        .first()
    )
    return {
        "paquete": paquete,
        "version": pub.version if pub else 0,
        "audiencia": pub.audiencia if pub else None,
        "vista": vista,
    }


def get_portal_implementacion(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "IMPLEMENTACION")
    _assert_cliente_capacidad(entidad, "IMPLEMENTACION")
    if not _paquete_publicado(db, entidad.id, "IMPLEMENTACION"):
        raise HTTPException(status_code=403, detail="Implementación no publicada para la empresa")
    if not entidad.proyecto_id:
        raise HTTPException(status_code=404, detail="Proyecto de implementación no vinculado")
    tablero = impl_svc.tablero_proyecto(db, user.organization_id, entidad.proyecto_id)
    detalle = impl_svc.detalle_proyecto(db, user.organization_id, entidad.proyecto_id)
    return {
        "adaptador": "implementacion_service.tablero_proyecto",
        "implementacion": adaptar_implementacion_externa(tablero, detalle),
    }


def get_portal_empleados_ia(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "EMPLEADOS_IA")
    _assert_cliente_capacidad(entidad, "EMPLEADOS_IA")
    if not _paquete_publicado(db, entidad.id, "EMPLEADOS_IA"):
        raise HTTPException(status_code=403, detail="Empleados IA no publicados para la empresa")
    contrato = _parse_contrato(entidad.capacidades_contrato_json)
    employees = agent_svc.list_employees(db, user.organization_id, status=None)
    if contrato["empleados_ia_ids"]:
        allowed = set(contrato["empleados_ia_ids"])
        employees = [e for e in employees if e["id"] in allowed]
    else:
        employees = [
            e for e in employees
            if (e.get("lifecycle_status") or "").upper() in ("PRODUCTION", "ACTIVE", "CERTIFIED")
        ]
    return {
        "adaptador": "agent_factory.list_employees",
        "empleados": adaptar_empleados_ia_externo(employees),
    }


def get_portal_empleado_ia(db: Session, user: User, employee_id: str) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "EMPLEADOS_IA")
    _assert_cliente_capacidad(entidad, "EMPLEADOS_IA")
    if not _paquete_publicado(db, entidad.id, "EMPLEADOS_IA"):
        raise HTTPException(status_code=403, detail="Empleados IA no publicados para la empresa")
    contrato = _parse_contrato(entidad.capacidades_contrato_json)
    if contrato["empleados_ia_ids"] and employee_id not in contrato["empleados_ia_ids"]:
        raise HTTPException(status_code=403, detail="Empleado IA no asignado a su organización")
    emp_org = db.query(AIEmployee).filter(
        AIEmployee.id == employee_id,
        AIEmployee.organization_id == user.organization_id,
    ).first()
    if not emp_org:
        raise HTTPException(status_code=404, detail="Empleado IA no encontrado")
    detail = agent_svc.get_employee_detail(db, user.organization_id, employee_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Empleado IA no encontrado")
    safe = adaptar_empleado_ia_detalle_externo(detail)
    safe.pop("instructions_full", None)
    return {"adaptador": "agent_factory.get_employee_detail", "empleado": safe}


def _informes_autorizados(
    db: Session,
    organization_id: str,
    user: User,
    entidad: EntidadEmpresa,
) -> list[dict[str, Any]]:
    pub = (
        db.query(EmpresaPublicacion)
        .filter(
            EmpresaPublicacion.entidad_id == entidad.id,
            EmpresaPublicacion.paquete == "INFORMES",
        )
        .first()
    )
    audiencia = pub.audiencia if pub else None
    rows = (
        db.query(CommMessage)
        .filter(
            CommMessage.organization_id == organization_id,
            CommMessage.estado.in_(("ENVIADA", "ENTREGADA")),
        )
        .order_by(CommMessage.created_at.desc())
        .limit(200)
        .all()
    )
    email = (user.email or entidad.contacto_email or "").strip().lower()
    out: list[dict[str, Any]] = []
    for row in rows:
        tipo = (row.tipo_comunicacion or "").upper()
        if "INFORME" not in tipo and tipo not in ("REPORTE", "REPORT", "INFORME_MENSUAL"):
            continue
        dest_ok = (
            row.destinatario_id == user.id
            or (row.destinatario_externo and row.destinatario_externo.strip().lower() == email)
            or row.destinatario_externo == entidad.contacto_email
        )
        if not dest_ok:
            continue
        out.append(comm_svc.message_to_dict(row, db))
    return adaptar_informes_externo(out, audiencia=audiencia)


def get_portal_informes(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "INFORMES")
    _assert_cliente_capacidad(entidad, "INFORMES")
    if not _paquete_publicado(db, entidad.id, "INFORMES"):
        raise HTTPException(status_code=403, detail="Informes no publicados para la empresa")
    return {
        "adaptador": "communications_service.list_messages",
        "informes": _informes_autorizados(db, user.organization_id, user, entidad),
    }


def get_portal_informe(db: Session, user: User, message_id: str) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "INFORMES")
    _assert_cliente_capacidad(entidad, "INFORMES")
    if not _paquete_publicado(db, entidad.id, "INFORMES"):
        raise HTTPException(status_code=403, detail="Informes no publicados para la empresa")
    try:
        detail = comm_svc.get_message_detail(db, user.organization_id, message_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if detail.get("estado") not in ("ENVIADA", "ENTREGADA"):
        raise HTTPException(status_code=403, detail="Informe no publicado")
    email = (user.email or entidad.contacto_email or "").strip().lower()
    dest_ok = (
        detail.get("destinatario_id") == user.id
        or (detail.get("destinatario_externo") or "").strip().lower() == email
    )
    if not dest_ok:
        raise HTTPException(status_code=403, detail="Informe no autorizado para su organización")
    pub = (
        db.query(EmpresaPublicacion)
        .filter(EmpresaPublicacion.entidad_id == entidad.id, EmpresaPublicacion.paquete == "INFORMES")
        .first()
    )
    return {
        "adaptador": "communications_service.get_message_detail",
        "informe": adaptar_informe_detalle_externo(detail, audiencia=pub.audiencia if pub else None),
    }


def get_portal_soporte(db: Session, user: User) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "SOPORTE")
    _assert_cliente_capacidad(entidad, "SOPORTE")
    if not _paquete_publicado(db, entidad.id, "SOPORTE"):
        raise HTTPException(status_code=403, detail="Soporte no publicado para la empresa")
    cases = support_svc.list_cases(
        db,
        user.organization_id,
        user=user,
        can_view_all=False,
        solo_mios=True,
    )
    return {
        "adaptador": "support_service.list_cases",
        "casos": adaptar_soporte_lista_externa(cases),
    }


def create_portal_soporte_caso(
    db: Session,
    user: User,
    *,
    asunto: str,
    descripcion: str,
    tipo: str = "SOLICITUD",
    prioridad: str = "MEDIA",
) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "SOPORTE")
    _assert_cliente_capacidad(entidad, "SOPORTE")
    if not _paquete_publicado(db, entidad.id, "SOPORTE"):
        raise HTTPException(status_code=403, detail="Soporte no publicado para la empresa")
    try:
        case = support_svc.create_case_manual(
            db,
            user.organization_id,
            user,
            {
                "asunto": asunto,
                "descripcion": descripcion,
                "tipo": tipo,
                "prioridad": prioridad,
                "entidad_relacionada": entidad.nombre,
                "correlation_id": entidad.correlation_id,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="espacio_externo.soporte_caso",
        detail=json.dumps({"case_id": case["id"]}),
        commit=False,
    )
    return adaptar_soporte_caso_externo(case)


def get_portal_soporte_caso(db: Session, user: User, case_id: str) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_paquete_accesible(entidad, "SOPORTE")
    _assert_cliente_capacidad(entidad, "SOPORTE")
    if not _paquete_publicado(db, entidad.id, "SOPORTE"):
        raise HTTPException(status_code=403, detail="Soporte no publicado para la empresa")
    detail = support_svc.get_case_detail(
        db,
        user.organization_id,
        case_id,
        can_view_internal=False,
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    if detail.get("solicitante_id") != user.id:
        raise HTTPException(status_code=403, detail="Caso de otro solicitante")
    return {
        "adaptador": "support_service.get_case_detail",
        "caso": adaptar_soporte_caso_externo(detail),
    }


def add_portal_soporte_comentario(
    db: Session,
    user: User,
    case_id: str,
    *,
    cuerpo: str,
    evidencia_ref: str | None = None,
) -> dict[str, Any]:
    acceso = _resolve_external_acceso(db, user)
    entidad = _get_entidad(db, acceso.entidad_id, user.organization_id)
    _assert_cliente_capacidad(entidad, "SOPORTE")
    detail = support_svc.get_case_detail(db, user.organization_id, case_id, can_view_internal=False)
    if not detail or detail.get("solicitante_id") != user.id:
        raise HTTPException(status_code=403, detail="Caso no autorizado")
    try:
        comment = support_svc.add_comment(
            db,
            user.organization_id,
            case_id,
            user,
            cuerpo=cuerpo,
            evidencia_ref=evidencia_ref,
            es_interno=False,
            can_view_internal=False,
        )
    except (LookupError, PermissionError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return comment


def crear_solicitud_informacion(
    db: Session,
    organization_id: str,
    user_id: str,
    entidad_id: str,
    *,
    titulo: str,
    descripcion: str | None = None,
    informacion_item_id: str | None = None,
) -> dict[str, Any]:
    entidad = _get_entidad(db, entidad_id, organization_id)
    entrega = EvaluacionEntregaExterna(
        organization_id=organization_id,
        expediente_id=entidad.expediente_id,
        entidad_id=entidad.id,
        informacion_item_id=informacion_item_id,
        titulo=titulo,
        descripcion=descripcion,
        estado="SOLICITADO",
        solicitado_por=user_id,
        correlation_id=entidad.correlation_id,
    )
    db.add(entrega)
    db.flush()
    return _entrega_dict(entrega, db)
