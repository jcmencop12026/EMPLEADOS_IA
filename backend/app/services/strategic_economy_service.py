"""Economía privada del Centro Estratégico — reutiliza Motor Económico 1280/1210/1320/1110."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.commercial_enums import CostCategory, ValueCategory
from app.commercial_models import CommercialProposal, CommercialProposalCost, CommercialProposalValue
from app.services import control_center_adapters as adapters
from app.services import commercial_service as com_svc

NOTA_PRIVACIDAD = (
    "Economía interna — no publicable a prospecto/cliente sin autoridad evaluacion.visibility"
)
NOTA_POTENCIAL = "POTENCIAL no se computa como realizado ni entra al precio sugerido"
FORMULA_PRECIO = (
    "max(valor_atribuible_realizable × fracción, costo_total × (1 + margen_mínimo), precio_base_plan) "
    "— considera valor, complejidad (costos), riesgo/urgencia (escenarios), reutilización y soporte vía plan"
)

_VALUE_CATEGORY_LABELS = {
    ValueCategory.AHORRO: "ahorro",
    ValueCategory.PERDIDA_EVITADA: "perdidas_evitadas",
    ValueCategory.INGRESO_RECUPERADO: "ingreso_recuperable",
    ValueCategory.PRODUCTIVIDAD_LIBERADA: "productividad_liberada",
    ValueCategory.NUEVO_INGRESO: "nuevos_ingresos",
    ValueCategory.OPORTUNIDAD_CAPTURADA: "oportunidades_capturables",
    ValueCategory.MITIGACION_RIESGO: "riesgo_mitigado",
    ValueCategory.REDUCCION_ERRORES: "reduccion_errores",
    ValueCategory.REDUCCION_TIEMPOS: "reduccion_tiempos",
}

_COST_CATEGORY_LABELS = {
    CostCategory.IMPLEMENTACION: "implementacion",
    CostCategory.CONFIGURACION: "configuracion",
    CostCategory.LICENCIAS: "licencias",
    CostCategory.INFRAESTRUCTURA: "infraestructura",
    CostCategory.SOPORTE: "soporte",
    CostCategory.OPERACION: "operacion",
    CostCategory.CONSUMO_IA: "consumo_ia",
    CostCategory.INTEGRACIONES: "integraciones",
    CostCategory.SERVICIOS_ADICIONALES: "servicios_externos",
}


def _has(permissions: set[str], code: str) -> bool:
    return code in permissions


def _latest_proposal(db: Session, org_id: str) -> CommercialProposal | None:
    return (
        db.query(CommercialProposal)
        .filter(CommercialProposal.organization_id == org_id)
        .order_by(CommercialProposal.updated_at.desc().nullslast(), CommercialProposal.created_at.desc())
        .first()
    )


def _aggregate_values_by_category(values: list[CommercialProposalValue]) -> dict[str, float]:
    buckets: dict[str, float] = {v: 0.0 for v in _VALUE_CATEGORY_LABELS.values()}
    for val in values:
        key = _VALUE_CATEGORY_LABELS.get(val.categoria)
        if key:
            buckets[key] += float(val.valor_atribuible or 0)
    return buckets


def _aggregate_costs_by_category(costs: list[CommercialProposalCost]) -> dict[str, float]:
    buckets: dict[str, float] = {v: 0.0 for v in _COST_CATEGORY_LABELS.values()}
    for cost in costs:
        key = _COST_CATEGORY_LABELS.get(cost.categoria)
        if key:
            buckets[key] += float(cost.monto or 0)
    return buckets


def _recurrent_cost_total(costs: list[CommercialProposalCost]) -> float:
    recurrent = {CostCategory.OPERACION, CostCategory.SOPORTE, CostCategory.CONSUMO_IA}
    return sum(float(c.monto or 0) for c in costs if c.categoria in recurrent)


def build_economia_privada(db: Session, org_id: str, permissions: set[str]) -> dict[str, Any]:
    """Visión interna completa para decisión comercial — Motor Económico existente."""
    if not _has(permissions, "strategic_control.economia_privada"):
        return {"visible_interno": False, "restringido": True, "privado": True}

    eco: dict[str, Any] = {
        "visible_interno": True,
        "privado": True,
        "restringido": False,
        "nota": NOTA_PRIVACIDAD,
        "nota_potencial": NOTA_POTENCIAL,
        "formula_precio": FORMULA_PRECIO,
        "motor": "1280_comercial + 1210_valoracion + 1320_tco + 1110_finops",
        "valor": {},
        "costos": {},
        "indicadores": {},
        "supuestos": [],
        "confianza": "MEDIA",
        "propuesta_referencia": None,
    }

    proposal = _latest_proposal(db, org_id)
    values: list[CommercialProposalValue] = []
    costs: list[CommercialProposalCost] = []
    detail: dict[str, Any] | None = None

    if proposal and _has(permissions, "comercial.view"):
        values = db.query(CommercialProposalValue).filter(CommercialProposalValue.proposal_id == proposal.id).all()
        costs = db.query(CommercialProposalCost).filter(CommercialProposalCost.proposal_id == proposal.id).all()
        detail = com_svc.proposal_to_detail(db, org_id, proposal.id)
        eco["propuesta_referencia"] = {
            "id": proposal.id,
            "codigo": proposal.codigo,
            "titulo": proposal.titulo,
            "estado": proposal.estado,
        }
        desglose = detail.get("desglose_naturaleza") or {}
        eco["valor"] = {
            "valor_identificado": detail.get("valor_total_esperado"),
            "valor_verificable": desglose.get("valor_verificado_atribuible") or desglose.get("valor_bruto_verificado"),
            "valor_verificado": desglose.get("valor_verificado_atribuible"),
            "valor_estimado": desglose.get("valor_estimado_atribuible"),
            "valor_potencial": desglose.get("valor_potencial_atribuible"),
            "valor_atribuible_precio": desglose.get("valor_atribuible_precio"),
            "valor_realizable": desglose.get("valor_bruto_realizable"),
            "potencial_excluido_precio": detail.get("valor_potencial_atribuible"),
            "por_categoria": _aggregate_values_by_category(values),
        }
        eco["costos"] = {
            **{k: v for k, v in _aggregate_costs_by_category(costs).items() if v > 0},
            "total": detail.get("costo_total"),
            "recurrente_estimado": _recurrent_cost_total(costs) or None,
        }
        can_margin = _has(permissions, "comercial.approve")
        eco["indicadores"] = {
            "inversion_total_estimada": detail.get("costo_total"),
            "costo_recurrente": eco["costos"].get("recurrente_estimado"),
            "precio_sugerido": detail.get("precio_sugerido"),
            "precio_final": detail.get("precio_final"),
            "margen_estimado_pct": detail.get("margen_pct") if can_margin else None,
            "margen_restringido": not can_margin,
            "beneficio_neto_cliente": detail.get("beneficio_neto_cliente"),
            "roi_pct": detail.get("roi_pct"),
            "payback_meses": detail.get("payback_meses"),
            "pct_valor_capturado": detail.get("pct_valor_capturado_empleados_ia"),
        }
        eco["supuestos"] = [
            {
                "tipo": s.get("scenario_type"),
                "valor_atribuible": s.get("valor_atribuible"),
                "probabilidad": s.get("probabilidad"),
                "costo": s.get("costo"),
                "explicacion": s.get("explicacion"),
            }
            for s in (detail.get("escenarios") or [])
        ]
        if detail.get("plan"):
            eco["plan_comercial"] = {
                "fraccion_valor": detail["plan"].get("fraccion_valor_sugerida"),
                "margen_minimo_pct": detail["plan"].get("margen_minimo_pct"),
                "precio_base_mensual": detail["plan"].get("precio_base_mensual"),
            }

    if _has(permissions, "valoracion.view"):
        vr = adapters.ValorRetornoAdapter().fetch(db, org_id, permissions=permissions)
        if vr.get("disponible"):
            eco.setdefault("valoracion_org", {})
            eco["valoracion_org"] = {
                "valor_verificado": vr.get("valor_verificado"),
                "valor_estimado": vr.get("valor_estimado"),
                "valor_potencial": vr.get("valor_potencial"),
                "beneficio_neto": vr.get("beneficio_neto"),
                "retorno_porcentaje": vr.get("retorno_porcentaje"),
            }
            if not eco["valor"]:
                eco["valor"] = {
                    "valor_verificado": vr.get("valor_verificado"),
                    "valor_estimado": vr.get("valor_estimado"),
                    "valor_potencial": vr.get("valor_potencial"),
                }

    if _has(permissions, "tco.view"):
        tco = adapters.TcoAdapter().fetch(db, org_id, permissions=permissions)
        if tco.get("disponible"):
            eco.setdefault("tco", {})
            eco["tco"] = {
                "inversion_total": tco.get("inversion_total"),
                "desglose": tco.get("desglose"),
                "finops_ia": tco.get("finops_ia"),
                "margen_pct": tco.get("margen_pct"),
            }
            if not eco["indicadores"].get("inversion_total_estimada"):
                eco["indicadores"]["inversion_total_estimada"] = tco.get("inversion_total")

    if _has(permissions, "finops.view"):
        fin = adapters.FinOpsExtendidoAdapter().fetch(db, org_id, permissions=permissions)
        if fin.get("disponible"):
            eco["finops"] = {
                "costo_periodo": fin.get("costo_periodo"),
                "tokens_periodo": fin.get("tokens_periodo"),
                "consumos_periodo": fin.get("consumos_periodo"),
            }
            eco["costos"].setdefault("consumo_ia", fin.get("costo_periodo"))

    if _has(permissions, "finops.view"):
        mb7 = adapters.Mb07PlanificadorAdapter().fetch(db, org_id, permissions=permissions)
        if mb7.get("disponible"):
            eco["planificador"] = {
                "consumo_real": mb7.get("consumo_real"),
                "consumo_proyectado": mb7.get("consumo_proyectado"),
                "margen_bruto_estimado": mb7.get("margen_bruto_estimado"),
            }

    if proposal and proposal.precio_sugerido is None and _has(permissions, "comercial.simulate"):
        try:
            simulated = com_svc.suggest_price(db, org_id, proposal.id)
            eco["indicadores"]["precio_sugerido"] = simulated.get("precio_sugerido")
            eco["indicadores"]["roi_pct"] = simulated.get("roi_pct")
            eco["indicadores"]["payback_meses"] = simulated.get("payback_meses")
            eco["indicadores"]["margen_estimado_pct"] = simulated.get("margen_pct")
            eco["simulacion_precio"] = True
        except Exception:
            pass

    potencial = (eco.get("valor") or {}).get("valor_potencial") or 0
    realizable = (eco.get("valor") or {}).get("valor_atribuible_precio") or (eco.get("valor") or {}).get("valor_realizable")
    eco["separacion_potencial"] = {
        "potencial_no_realizado": True,
        "valor_potencial": potencial,
        "valor_base_precio": realizable,
        "nota": NOTA_POTENCIAL,
    }

    return eco
