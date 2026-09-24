"""Fachada — inteligencia empresarial adaptativa."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.modules.inteligencia_empresarial.cadena_analitica import (
    construir_cadena_expediente,
    construir_cadena_oportunidad,
)
from app.modules.inteligencia_empresarial.contracts import CONTRATOS_FUTUROS
from app.modules.inteligencia_empresarial.evaluacion_adaptativa import (
    ejecutar_evaluacion_adaptativa,
    plan_informacion_adaptativa,
)
from app.modules.inteligencia_empresarial.motor_proactivo import procesar_nueva_evidencia
from app.modules.inteligencia_empresarial.priorizacion import priorizar_oportunidad, priorizar_portafolio
from app.modules.inteligencia_empresarial.suficiencia import evaluar_suficiencia_unificada


def panorama_expediente(db: Session, organization_id: str, expediente_id: str) -> dict[str, Any]:
    return {
        "plan_adaptativo": plan_informacion_adaptativa(db, expediente_id, organization_id),
        "suficiencia": evaluar_suficiencia_unificada(db, organization_id, expediente_id),
        "cadena_analitica": construir_cadena_expediente(db, organization_id, expediente_id),
        "contratos_futuros": CONTRATOS_FUTUROS,
    }


def panorama_oportunidad(db: Session, organization_id: str, opportunity_id: str) -> dict[str, Any]:
    return {
        "priorizacion": priorizar_oportunidad(db, organization_id, opportunity_id),
        "cadena_analitica": construir_cadena_oportunidad(db, organization_id, opportunity_id),
    }


def panorama_organizacion(db: Session, organization_id: str) -> dict[str, Any]:
    return {
        "priorizacion_portafolio": priorizar_portafolio(db, organization_id),
        "contratos_futuros": CONTRATOS_FUTUROS,
    }
