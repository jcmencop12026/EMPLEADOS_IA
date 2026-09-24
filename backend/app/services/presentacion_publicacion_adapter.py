"""Adapter de publicación para presentación ejecutiva real — fail-closed."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.demo_comercial_constants import DEMO_CORRELATION_PREFIX, DEMO_ENTIDAD_PREFIX
from app.evaluacion_models import EvaluacionExpediente
from app.presentacion_models import ESTADOS_PUBLICACION, PresentacionPublicacion
from app.resultados_models import ResultadoInformeImpacto, VISIBILIDAD_INFORME


class PublicacionDenegadaError(PermissionError):
    """Presentación no autorizada para visualización."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def is_demo_expediente(exp: EvaluacionExpediente) -> bool:
    if exp.correlation_id and exp.correlation_id.startswith(DEMO_CORRELATION_PREFIX):
        return True
    return exp.entidad_nombre.startswith(DEMO_ENTIDAD_PREFIX)


def get_publicacion(
    db: Session,
    organization_id: str,
    expediente_id: str,
) -> PresentacionPublicacion | None:
    return (
        db.query(PresentacionPublicacion)
        .filter(
            PresentacionPublicacion.organization_id == organization_id,
            PresentacionPublicacion.expediente_id == expediente_id,
        )
        .first()
    )


def get_estado_publicacion(
    db: Session,
    organization_id: str,
    expediente_id: str,
) -> str:
    row = get_publicacion(db, organization_id, expediente_id)
    return row.estado if row else "PRIVADO"


def _latest_informe_visibilidad(
    db: Session,
    organization_id: str,
    expediente_id: str,
) -> str | None:
    inf = (
        db.query(ResultadoInformeImpacto)
        .filter(
            ResultadoInformeImpacto.expediente_id == expediente_id,
            ResultadoInformeImpacto.organization_id == organization_id,
        )
        .order_by(ResultadoInformeImpacto.created_at.desc())
        .first()
    )
    return inf.visibilidad if inf else None


def _user_permissions(user) -> set[str]:
    perms: set[str] = set()
    role = getattr(user, "role", None)
    if role == "admin":
        return {
            "evaluacion.view",
            "evaluacion.manage",
            "evaluacion.visibility",
            "evaluacion.vista_entidad",
        }
    if hasattr(user, "permissions") and user.permissions:
        perms.update(user.permissions)
    return perms


def assert_puede_ver_presentacion_real(
    db: Session,
    organization_id: str,
    expediente: EvaluacionExpediente,
    user,
) -> dict[str, Any]:
    """Fail-closed: exige estado de publicación e informe publicable cuando aplica."""
    if is_demo_expediente(expediente):
        raise PublicacionDenegadaError(
            "Use la ruta demo para expedientes ficticios; la presentación real no aplica."
        )

    estado = get_estado_publicacion(db, organization_id, expediente.id)
    perms = _user_permissions(user)

    if estado == "PRIVADO":
        if "evaluacion.manage" not in perms:
            raise PublicacionDenegadaError(
                "Presentación en estado PRIVADO. Publique el expediente antes de compartir."
            )
    elif estado == "PREPARADO_PARA_PRESENTAR":
        if not ({"evaluacion.manage", "evaluacion.visibility"} & perms):
            raise PublicacionDenegadaError(
                "Presentación en preparación. Requiere permisos internos de evaluación."
            )
    elif estado == "PUBLICADO_A_EMPRESA":
        if not ({"evaluacion.view", "evaluacion.vista_entidad", "evaluacion.manage"} & perms):
            raise PublicacionDenegadaError("No tiene permisos para ver presentaciones publicadas.")
    else:
        raise PublicacionDenegadaError(f"Estado de publicación no válido: {estado}")

    informe_vis = _latest_informe_visibilidad(db, organization_id, expediente.id)
    if informe_vis == "INTERNO" and estado == "PUBLICADO_A_EMPRESA":
        raise PublicacionDenegadaError(
            "El informe vinculado es INTERNO. Cambie visibilidad a VISIBLE_ENTIDAD antes de publicar."
        )

    return {
        "estado": estado,
        "informe_visibilidad": informe_vis,
        "adapter": "presentacion_publicacion_v1",
        "nota_integracion": (
            "Autoridad definitiva de publicación puede integrarse vía este adapter "
            "sin duplicar estados."
        ),
    }


def set_estado_publicacion(
    db: Session,
    organization_id: str,
    expediente_id: str,
    user_id: str,
    *,
    estado: str,
    notas: str | None = None,
) -> dict[str, Any]:
    estado = estado.upper()
    if estado not in ESTADOS_PUBLICACION:
        raise ValueError(f"Estado no válido: {estado}")

    exp = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.id == expediente_id,
            EvaluacionExpediente.organization_id == organization_id,
        )
        .first()
    )
    if not exp:
        raise LookupError("Expediente no encontrado.")
    if is_demo_expediente(exp):
        raise ValueError("No se publica presentación real para expedientes DEMO.")

    if estado == "PUBLICADO_A_EMPRESA":
        informe_vis = _latest_informe_visibilidad(db, organization_id, expediente_id)
        if informe_vis == "INTERNO":
            raise ValueError(
                "No puede publicar: el informe de impacto es INTERNO. "
                "Genere o actualice el informe con visibilidad VISIBLE_ENTIDAD."
            )

    row = get_publicacion(db, organization_id, expediente_id)
    now = _utcnow()
    if not row:
        row = PresentacionPublicacion(
            organization_id=organization_id,
            expediente_id=expediente_id,
            estado=estado,
            notas=notas,
            actualizado_por=user_id,
            publicado_at=now if estado == "PUBLICADO_A_EMPRESA" else None,
        )
        db.add(row)
    else:
        row.estado = estado
        row.notas = notas
        row.actualizado_por = user_id
        row.updated_at = now
        if estado == "PUBLICADO_A_EMPRESA":
            row.publicado_at = now
    db.flush()
    return publicacion_to_dict(row)


def publicacion_to_dict(row: PresentacionPublicacion) -> dict[str, Any]:
    return {
        "expediente_id": row.expediente_id,
        "estado": row.estado,
        "notas": row.notas,
        "publicado_at": row.publicado_at.isoformat() if row.publicado_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "estados_permitidos": list(ESTADOS_PUBLICACION),
        "visibilidad_informe_valores": list(VISIBILIDAD_INFORME),
    }
