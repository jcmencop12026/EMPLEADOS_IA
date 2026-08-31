"""Adaptador reemplazable — vista compromiso → resultado (sin recalcular indicadores)."""

from __future__ import annotations

import json
from typing import Any, Protocol

from sqlalchemy.orm import Session


class ResultadoContinuidadPort(Protocol):
    def fetch_real(
        self,
        db: Session,
        organization_id: str,
        *,
        opportunity_id: str | None = None,
        proyecto_id: str | None = None,
        include_private: bool = False,
    ) -> dict[str, Any]:
        ...


class LocalResultadoContinuidadAdapter:
    """Agrega fuentes existentes hasta integrar Inteligencia de Resultados."""

    def fetch_real(
        self,
        db: Session,
        organization_id: str,
        *,
        opportunity_id: str | None = None,
        proyecto_id: str | None = None,
        include_private: bool = False,
    ) -> dict[str, Any]:
        from app.implementacion_models import ExitoClienteObjetivo, ExitoClientePlan, ImplementacionProyecto
        from app.valuation_models import OpportunityValuation, OpportunityValuationReal

        real: dict[str, Any] = {
            "fuente": "local_adapter",
            "reemplazable_por": "inteligencia_resultados",
            "valoracion_real": [],
            "objetivos_exito": [],
        }

        if opportunity_id:
            rows = (
                db.query(OpportunityValuationReal)
                .join(OpportunityValuation, OpportunityValuationReal.valuation_id == OpportunityValuation.id)
                .filter(
                    OpportunityValuation.organization_id == organization_id,
                    OpportunityValuation.opportunity_id == opportunity_id,
                )
                .limit(20)
                .all()
            )
            real["valoracion_real"] = [
                {
                    "materializado": float(r.materialized_value) if r.materialized_value else None,
                    "atribuible": float(r.attributable_value) if r.attributable_value else None,
                    "naturaleza": r.value_nature,
                    "fuente": r.source,
                }
                for r in rows
            ]

        if proyecto_id:
            plan = db.query(ExitoClientePlan).filter(ExitoClientePlan.proyecto_id == proyecto_id).first()
            if plan:
                objs = db.query(ExitoClienteObjetivo).filter(ExitoClienteObjetivo.plan_id == plan.id).all()
                real["objetivos_exito"] = [
                    {
                        "nombre": o.nombre,
                        "esperado": float(o.valor_esperado) if o.valor_esperado else None,
                        "medido": float(o.valor_medido) if o.valor_medido else None,
                        "estado": o.estado_valor,
                    }
                    for o in objs
                ]
            proj = db.query(ImplementacionProyecto).filter(ImplementacionProyecto.id == proyecto_id).first()
            if proj and proj.valor_compromiso_json:
                try:
                    real["compromiso_snapshot"] = json.loads(proj.valor_compromiso_json)
                except json.JSONDecodeError:
                    pass

        return real


_adapter: ResultadoContinuidadPort | None = None


def get_resultado_adapter() -> ResultadoContinuidadPort:
    global _adapter
    if _adapter is None:
        _adapter = LocalResultadoContinuidadAdapter()
    return _adapter
