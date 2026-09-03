"""Suficiencia unificada — expediente + dossier sin repreguntar información válida."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.evaluacion_models import EvaluacionInformacionItem
from app.services import evaluacion_service as eval_svc
from app.services import transformacion_service as trans_svc
from app.transformacion_models import DossierConocimientoItem, DossierEmpresarial


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dossier_conocimiento_valido(db: Session, org_id: str, campo: str) -> dict[str, Any] | None:
    dossier = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).first()
    if not dossier:
        return None
    item = (
        db.query(DossierConocimientoItem)
        .filter(
            DossierConocimientoItem.dossier_id == dossier.id,
            DossierConocimientoItem.campo == campo,
            DossierConocimientoItem.vigente.is_(True),
        )
        .first()
    )
    if not item or not (item.valor or "").strip():
        return None
    return {
        "campo": campo,
        "valor": item.valor,
        "fuente": item.fuente,
        "calidad": item.calidad,
        "actualizado": item.updated_at.isoformat() if item.updated_at else None,
    }


def evaluar_suficiencia_unificada(
    db: Session,
    organization_id: str,
    expediente_id: str,
) -> dict[str, Any]:
    """Completitud, calidad, actualidad, consistencia, fuente y confianza."""
    base = trans_svc.evaluar_suficiencia(db, organization_id, expediente_id)
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .order_by(EvaluacionInformacionItem.orden)
        .all()
    )

    ya_en_dossier: list[dict[str, Any]] = []
    faltantes_reales: list[dict[str, Any]] = []
    for f in base.get("faltantes", []):
        conocido = _dossier_conocimiento_valido(db, organization_id, f["campo"])
        if conocido:
            ya_en_dossier.append({**f, "dossier": conocido, "no_repreguntar": True})
        else:
            faltantes_reales.append(f)

    recibidos = [i for i in items if i.estado == "RECIBIDO" and i.respuesta]
    con_evidencia = [i for i in recibidos if i.evidencia_ref]
    actualidad = "ACTUAL" if recibidos else "DESACTUALIZADA"
    if recibidos and all(i.updated_at and (_utcnow() - i.updated_at).days < 90 for i in recibidos if i.updated_at):
        actualidad = "ACTUAL"
    elif recibidos:
        actualidad = "REVISAR"

    return {
        **base,
        "nivel": exp.nivel,
        "faltantes": faltantes_reales,
        "cubierto_por_dossier": ya_en_dossier,
        "no_solicitar_duplicado": len(ya_en_dossier) > 0,
        "dimensiones": {
            "completitud": base.get("porcentaje_informacion"),
            "calidad": base.get("calidad"),
            "actualidad": actualidad,
            "consistencia": base["calidad"].get("consistencia") if base.get("calidad") else None,
            "fuente": base["calidad"].get("procedencia") if base.get("calidad") else None,
            "confianza": base.get("confianza_global"),
            "evidencias_documentales": len(con_evidencia),
        },
        "explicacion": (
            f"{len(ya_en_dossier)} campo(s) ya válidos en dossier — no se repreguntan."
            if ya_en_dossier
            else base.get("explicacion")
        ),
    }
