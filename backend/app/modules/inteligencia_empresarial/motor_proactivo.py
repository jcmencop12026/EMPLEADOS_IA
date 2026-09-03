"""Procesar nueva evidencia — señal proactiva sin decisiones automáticas."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import User
from app.services import proactive_service as opp_svc


REACCIONES_PERMITIDAS = frozenset({
    "crear_senal",
    "actualizar_hallazgo",
    "generar_oportunidad",
    "modificar_prioridad",
    "solicitar_informacion",
})


def procesar_nueva_evidencia(
    db: Session,
    organization_id: str,
    user: User,
    *,
    titulo: str,
    descripcion: str,
    dominio: str = "procesos",
    correlation_id: str | None = None,
) -> dict[str, Any]:
    signal, es_nueva = opp_svc.create_signal(
        db,
        organization_id=organization_id,
        tipo="EVIDENCIA_EMPRESARIAL",
        dominio=dominio,
        origen="inteligencia_empresarial",
        evento=titulo[:120],
        payload={"descripcion": descripcion, "titulo": titulo},
        correlation_id=correlation_id,
    )
    write_audit(
        db,
        action="inteligencia_empresarial.evidencia.procesada",
        organization_id=organization_id,
        user_id=user.id,
        detail=json.dumps({
            "signal_id": signal.id,
            "es_nueva": es_nueva,
            "reacciones_posibles": list(REACCIONES_PERMITIDAS),
            "decision_automatica": False,
        }, ensure_ascii=False),
        commit=False,
    )
    return {
        "senal_id": signal.id,
        "es_nueva": es_nueva,
        "estado": "SENAL_CREADA",
        "siguiente_paso": f"POST /api/oportunidades/senales/{signal.id}/procesar",
        "reacciones_disponibles": list(REACCIONES_PERMITIDAS),
        "nota": "Requiere revisión humana — no se ejecutan decisiones automáticamente",
    }
