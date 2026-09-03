"""Servicio — evidencias/adjuntos de entregas externas (reutiliza knowledge_storage)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.empresa_seguridad_models import EmpresaEvidenciaVinculo
from app.espacio_externo_models import (
    ESTADOS_ADJUNTO_ENTREGA,
    FUENTES_INFORMACION,
    EvaluacionEntregaAdjunto,
    EvaluacionEntregaExterna,
)
from app.evaluacion_models import EvaluacionInformacionItem
from app.models import User
from app.services import knowledge_storage


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_mime(extension: str, mime_type: str | None) -> None:
    if not mime_type:
        return
    allowed = knowledge_storage.ALLOWED_EXTENSIONS.get(extension, set())
    if allowed and mime_type not in allowed and not mime_type.startswith("text/"):
        raise ValueError(f"Tipo MIME no coincide con extensión {extension}")


def adjunto_dict(row: EvaluacionEntregaAdjunto, *, include_internal: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": row.id,
        "entrega_id": row.entrega_id,
        "grupo_archivo": row.grupo_archivo,
        "nombre": row.nombre_sanitizado,
        "extension": row.extension,
        "mime_type": row.mime_type,
        "size_bytes": row.size_bytes,
        "version": row.version,
        "es_version_actual": row.es_version_actual,
        "estado": row.estado,
        "observacion": row.observacion,
        "fuente_tipo": row.fuente_tipo,
        "fecha": row.created_at.isoformat() if row.created_at else None,
        "reemplaza_id": row.reemplaza_id,
    }
    if include_internal:
        out["observacion_interna"] = row.observacion_interna
        out["storage_key"] = row.storage_key
    return out


def _vincular_dossier(
    db: Session,
    *,
    organization_id: str,
    adjunto: EvaluacionEntregaAdjunto,
    user_id: str,
) -> None:
    db.add(
        EmpresaEvidenciaVinculo(
            organization_id=organization_id,
            tipo_evidencia="documento",
            referencia=adjunto.id,
            descripcion=adjunto.nombre_sanitizado,
            objeto_tipo="expediente",
            objeto_id=adjunto.expediente_id,
            rol_vinculo="RESULTADO",
            correlation_id=adjunto.correlation_id,
            creado_por=user_id,
        )
    )
    if adjunto.informacion_item_id:
        db.add(
            EmpresaEvidenciaVinculo(
                organization_id=organization_id,
                tipo_evidencia="documento",
                referencia=adjunto.id,
                descripcion=adjunto.nombre_sanitizado,
                objeto_tipo="informacion_evaluacion",
                objeto_id=adjunto.informacion_item_id,
                rol_vinculo="SOPORTE",
                correlation_id=adjunto.correlation_id,
                creado_por=user_id,
            )
        )


def list_adjuntos_entrega(
    db: Session,
    organization_id: str,
    entrega_id: str,
    *,
    include_internal: bool = False,
    solo_actuales: bool = True,
) -> list[dict[str, Any]]:
    q = db.query(EvaluacionEntregaAdjunto).filter(
        EvaluacionEntregaAdjunto.organization_id == organization_id,
        EvaluacionEntregaAdjunto.entrega_id == entrega_id,
    )
    if solo_actuales:
        q = q.filter(EvaluacionEntregaAdjunto.es_version_actual.is_(True))
    rows = q.order_by(EvaluacionEntregaAdjunto.created_at.asc()).all()
    return [adjunto_dict(r, include_internal=include_internal) for r in rows]


def list_historial_grupo(
    db: Session,
    organization_id: str,
    grupo_archivo: str,
    *,
    include_internal: bool = False,
) -> list[dict[str, Any]]:
    rows = (
        db.query(EvaluacionEntregaAdjunto)
        .filter(
            EvaluacionEntregaAdjunto.organization_id == organization_id,
            EvaluacionEntregaAdjunto.grupo_archivo == grupo_archivo,
        )
        .order_by(EvaluacionEntregaAdjunto.version.asc())
        .all()
    )
    return [adjunto_dict(r, include_internal=include_internal) for r in rows]


def _get_entrega_for_org(db: Session, organization_id: str, entrega_id: str) -> EvaluacionEntregaExterna:
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


def _get_adjunto_for_org(db: Session, organization_id: str, adjunto_id: str) -> EvaluacionEntregaAdjunto:
    row = (
        db.query(EvaluacionEntregaAdjunto)
        .filter(
            EvaluacionEntregaAdjunto.id == adjunto_id,
            EvaluacionEntregaAdjunto.organization_id == organization_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    return row


def upload_adjuntos_externo(
    db: Session,
    user: User,
    *,
    entrega_id: str | None = None,
    item_id: str | None = None,
    files: list[tuple[str, bytes, str | None]],
    observacion: str | None = None,
    fuente_tipo: str = "SUMINISTRADA_EMPRESA",
    entidad_id: str,
    expediente_id: str,
    correlation_id: str | None,
) -> dict[str, Any]:
    if fuente_tipo not in FUENTES_INFORMACION:
        raise HTTPException(status_code=422, detail="fuente_tipo inválida")
    if not files:
        raise HTTPException(status_code=422, detail="Se requiere al menos un archivo")
    if entrega_id:
        entrega = _get_entrega_for_org(db, user.organization_id, entrega_id)
        if entrega.entidad_id != entidad_id:
            raise HTTPException(status_code=403, detail="Entrega no autorizada")
        if entrega.estado not in ("SOLICITADO", "RECIBIDO", "REQUIERE_COMPLEMENTO", "EN_VALIDACION"):
            raise HTTPException(status_code=409, detail="La entrega no admite nuevos adjuntos")
    elif item_id:
        item = (
            db.query(EvaluacionInformacionItem)
            .filter(
                EvaluacionInformacionItem.id == item_id,
                EvaluacionInformacionItem.expediente_id == expediente_id,
            )
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Ítem de información no encontrado")
        entrega = EvaluacionEntregaExterna(
            organization_id=user.organization_id,
            expediente_id=expediente_id,
            entidad_id=entidad_id,
            informacion_item_id=item.id,
            titulo=item.etiqueta,
            descripcion=item.explicacion,
            estado="RECIBIDO",
            fuente_tipo=fuente_tipo,
            contenido=observacion or "(entrega con adjuntos)",
            entregado_por=user.id,
            entregado_at=_utcnow(),
            correlation_id=correlation_id,
        )
        db.add(entrega)
        db.flush()
        item.estado = "RECIBIDO"
        item.estado_validacion = "EN_VALIDACION"
        item.entregado_por = user.id
    else:
        raise HTTPException(status_code=422, detail="entrega_id o item_id requerido")

    creados: list[dict[str, Any]] = []
    for filename, data, mime_type in files:
        try:
            normalized = knowledge_storage.normalize_filename(filename)
            extension = knowledge_storage.validate_extension(normalized)
            _validate_mime(extension, mime_type)
            adjunto_id = knowledge_storage.new_document_id()
            storage_key = knowledge_storage.save_evidence_bytes(
                user.organization_id, adjunto_id, extension, data
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        adjunto = EvaluacionEntregaAdjunto(
            id=adjunto_id,
            organization_id=user.organization_id,
            expediente_id=expediente_id,
            entidad_id=entidad_id,
            entrega_id=entrega.id,
            informacion_item_id=entrega.informacion_item_id,
            grupo_archivo=_uuid(),
            nombre_original=filename,
            nombre_sanitizado=normalized,
            extension=extension,
            mime_type=mime_type,
            size_bytes=len(data),
            storage_key=storage_key,
            version=1,
            es_version_actual=True,
            estado="RECIBIDO",
            observacion=observacion,
            fuente_tipo=fuente_tipo,
            subido_por=user.id,
            correlation_id=correlation_id,
        )
        db.add(adjunto)
        _vincular_dossier(db, organization_id=user.organization_id, adjunto=adjunto, user_id=user.id)
        creados.append(adjunto_dict(adjunto))

    entrega.estado = "RECIBIDO"
    entrega.entregado_por = user.id
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="espacio_externo.adjunto_upload",
        detail=json.dumps({"entrega_id": entrega.id, "count": len(creados)}),
        commit=False,
    )
    return {"entrega_id": entrega.id, "adjuntos": creados}


def reemplazar_adjunto_externo(
    db: Session,
    user: User,
    adjunto_id: str,
    *,
    filename: str,
    data: bytes,
    mime_type: str | None,
    observacion: str | None = None,
    entidad_id: str,
) -> dict[str, Any]:
    anterior = _get_adjunto_for_org(db, user.organization_id, adjunto_id)
    if anterior.entidad_id != entidad_id:
        raise HTTPException(status_code=403, detail="Adjunto no autorizado")
    if not anterior.es_version_actual:
        raise HTTPException(status_code=409, detail="Solo se reemplaza la versión actual")
    entrega = _get_entrega_for_org(db, user.organization_id, anterior.entrega_id)
    if entrega.estado not in ("RECIBIDO", "REQUIERE_COMPLEMENTO", "EN_VALIDACION"):
        raise HTTPException(status_code=409, detail="La entrega no admite reemplazo")

    try:
        normalized = knowledge_storage.normalize_filename(filename)
        extension = knowledge_storage.validate_extension(normalized)
        _validate_mime(extension, mime_type)
        nuevo_id = knowledge_storage.new_document_id()
        storage_key = knowledge_storage.save_evidence_bytes(
            user.organization_id, nuevo_id, extension, data
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    anterior.es_version_actual = False
    anterior.estado = "REEMPLAZADO"
    nuevo = EvaluacionEntregaAdjunto(
        id=nuevo_id,
        organization_id=user.organization_id,
        expediente_id=anterior.expediente_id,
        entidad_id=anterior.entidad_id,
        entrega_id=anterior.entrega_id,
        informacion_item_id=anterior.informacion_item_id,
        grupo_archivo=anterior.grupo_archivo,
        reemplaza_id=anterior.id,
        nombre_original=filename,
        nombre_sanitizado=normalized,
        extension=extension,
        mime_type=mime_type,
        size_bytes=len(data),
        storage_key=storage_key,
        version=anterior.version + 1,
        es_version_actual=True,
        estado="RECIBIDO",
        observacion=observacion,
        fuente_tipo=anterior.fuente_tipo,
        subido_por=user.id,
        correlation_id=anterior.correlation_id,
    )
    db.add(nuevo)
    _vincular_dossier(db, organization_id=user.organization_id, adjunto=nuevo, user_id=user.id)
    entrega.estado = "RECIBIDO"
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="espacio_externo.adjunto_replace",
        detail=json.dumps({"anterior": anterior.id, "nuevo": nuevo.id, "version": nuevo.version}),
        commit=False,
    )
    return adjunto_dict(nuevo)


def download_adjunto(
    db: Session,
    organization_id: str,
    adjunto_id: str,
    *,
    entidad_id: str | None = None,
    user_id: str | None = None,
    acceso_activo: bool = True,
) -> tuple[str, bytes, str | None]:
    if not acceso_activo:
        raise HTTPException(status_code=403, detail="Acceso revocado")
    row = _get_adjunto_for_org(db, organization_id, adjunto_id)
    if entidad_id and row.entidad_id != entidad_id:
        raise HTTPException(status_code=403, detail="Adjunto de otra organización")
    try:
        data = knowledge_storage.read_evidence_file(row.storage_key)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Archivo no disponible") from exc
    if user_id:
        write_audit(
            db,
            organization_id=organization_id,
            user_id=user_id,
            action="espacio_externo.adjunto_download",
            detail=json.dumps({"adjunto_id": adjunto_id}),
            commit=False,
        )
    return row.nombre_sanitizado, data, row.mime_type


def validar_adjunto_interno(
    db: Session,
    organization_id: str,
    user_id: str,
    adjunto_id: str,
    *,
    estado: str,
    observacion_publica: str | None = None,
    observacion_interna: str | None = None,
) -> dict[str, Any]:
    if estado not in ESTADOS_ADJUNTO_ENTREGA:
        raise HTTPException(status_code=422, detail="estado inválido")
    row = _get_adjunto_for_org(db, organization_id, adjunto_id)
    row.estado = estado
    if observacion_publica is not None:
        row.observacion = observacion_publica
    if observacion_interna is not None:
        row.observacion_interna = observacion_interna
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="espacio_externo.adjunto_validacion",
        detail=json.dumps({"adjunto_id": adjunto_id, "estado": estado}),
        commit=False,
    )
    return adjunto_dict(row, include_internal=True)
