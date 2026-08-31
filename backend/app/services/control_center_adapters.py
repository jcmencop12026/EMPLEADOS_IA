"""Adaptadores de integración real del Centro de Control — Bloque 1250C."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy import func
from sqlalchemy.orm import Session


class ModuloAdapter(Protocol):
    modulo: str
    bloque: str

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        ...


def _no_disponible(modulo: str, bloque: str, razon: str) -> dict[str, Any]:
    return {
        "disponible": False,
        "estado": "Sin información disponible",
        "modulo": modulo,
        "bloque": bloque,
        "integracion": razon,
    }


def _period_filter(query, column, period_start: datetime | None):
    if period_start is not None:
        return query.filter(column >= period_start)
    return query


SEMANTICA_VALOR = {
    "VERIFICADO": "HECHO",
    "ESTIMADO": "INFERENCIA",
    "POTENCIAL": "INFERENCIA",
    "RECOMENDACION": "RECOMENDACION",
    "SIN_CLASIFICAR": "SIN_CLASIFICAR",
    "nota_potencial": "POTENCIAL no se suma al valor realizado ni entra en ROI/payback realizado",
}


def _sum_valor_por_naturaleza(rows: list[tuple[str | None, Any]]) -> dict[str, float | None]:
    buckets = {"VERIFICADO": 0.0, "ESTIMADO": 0.0, "POTENCIAL": 0.0}
    for nature, total in rows:
        key = (nature or "ESTIMADO").upper()
        if key not in buckets:
            key = "ESTIMADO"
        buckets[key] += float(total or 0)
    verificado = buckets["VERIFICADO"] or None
    estimado = buckets["ESTIMADO"] or None
    potencial = buckets["POTENCIAL"] or None
    realizado = None
    if verificado is not None or estimado is not None:
        realizado = (verificado or 0.0) + (estimado or 0.0)
    return {
        "valor_verificado": verificado,
        "valor_estimado": estimado,
        "valor_potencial": potencial,
        "valor_realizado": realizado if realizado else None,
    }


class OportunidadesAdapter:
    """Bloque 1100 — estados operativos de cierre."""

    modulo = "oportunidades"
    bloque = "1100"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "oportunidades.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere permiso oportunidades.view"), "restringido": True}
        from app.opportunity_models import Opportunity
        from app.services import proactive_service as psvc

        resumen = psvc.business_summary(db, organization_id)
        por_estado = dict(
            db.query(Opportunity.estado, func.count())
            .filter(Opportunity.organization_id == organization_id)
            .group_by(Opportunity.estado)
            .all()
        )
        estados_operativos = {
            "seguimiento": por_estado.get("EN_SEGUIMIENTO", 0),
            "ejecucion": por_estado.get("EN_EJECUCION", 0),
            "materializacion": por_estado.get("MATERIALIZADA", 0),
            "aprobaciones": por_estado.get("PENDIENTE_APROBACION", 0),
            "resultado_cerradas": por_estado.get("CERRADA", 0),
        }
        crit_query = db.query(Opportunity).filter(
            Opportunity.organization_id == organization_id,
            Opportunity.estado.in_(["PENDIENTE_APROBACION", "EN_EJECUCION", "EN_SEGUIMIENTO"]),
            Opportunity.urgencia.in_(["ALTA", "CRITICA"]),
        )
        if estado:
            crit_query = crit_query.filter(Opportunity.estado == estado.upper())
        crit_query = _period_filter(crit_query, Opportunity.fecha_deteccion, period_start)
        criticas = crit_query.order_by(Opportunity.prioridad_score.desc().nullslast()).limit(5).all()
        return {
            "disponible": True,
            "estado": "Integrado con módulo operativo 1100",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "resumen": resumen,
            "por_estado": por_estado,
            "estados_operativos": estados_operativos,
            "criticas": [
                {
                    "id": o.id,
                    "titulo": o.titulo,
                    "estado": o.estado,
                    "urgencia": o.urgencia,
                    "enlace": f"/oportunidades/{o.id}",
                }
                for o in criticas
            ],
            "enlace": "/oportunidades",
        }


class ImpactoAdapter:
    """Bloque 1200 — línea base, medición e impacto real."""

    modulo = "impacto"
    bloque = "1200"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "linea_base.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere permiso linea_base.view"), "restringido": True}
        from app.baseline_models import LineaBase, LineaBaseImpacto, LineaBaseMedicion

        lb_q = db.query(func.count(LineaBase.id)).filter(LineaBase.organization_id == organization_id)
        activas_q = db.query(func.count(LineaBase.id)).filter(
            LineaBase.organization_id == organization_id,
            LineaBase.estado.in_(["ACTIVA", "EN_MEDICION"]),
        )
        med_q = db.query(func.count(LineaBaseMedicion.id)).filter(LineaBaseMedicion.organization_id == organization_id)
        if period_start:
            med_q = med_q.filter(LineaBaseMedicion.created_at >= period_start)

        impacto_q = db.query(LineaBaseImpacto).filter(LineaBaseImpacto.organization_id == organization_id)
        if period_start:
            impacto_q = impacto_q.filter(LineaBaseImpacto.created_at >= period_start)

        total_lb = lb_q.scalar() or 0
        activas = activas_q.scalar() or 0
        mediciones = med_q.scalar() or 0
        impactos = impacto_q.all()
        impactos_reales = sum(1 for i in impactos if i.tipo_impacto == "IMPACTO_REAL" or i.impacto_real is not None)
        cambios_observados = sum(1 for i in impactos if i.tipo_impacto == "CAMBIO_OBSERVADO")
        con_atribucion = sum(1 for i in impactos if i.atribucion_nivel not in (None, "NO_ATRIBUIBLE"))

        med_pendientes = (
            db.query(func.count(LineaBaseMedicion.id))
            .filter(
                LineaBaseMedicion.organization_id == organization_id,
                LineaBaseMedicion.estado == "REGISTRADA",
            )
            .scalar()
            or 0
        )
        med_validadas = (
            db.query(func.count(LineaBaseMedicion.id))
            .filter(
                LineaBaseMedicion.organization_id == organization_id,
                LineaBaseMedicion.estado == "VALIDADA",
            )
            .scalar()
            or 0
        )

        recientes = (
            db.query(LineaBase)
            .filter(LineaBase.organization_id == organization_id)
            .order_by(LineaBase.updated_at.desc())
            .limit(5)
            .all()
        )

        if total_lb == 0 and mediciones == 0 and not impactos:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin líneas base registradas"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/lineas-base",
            }

        return {
            "disponible": True,
            "estado": "Integrado con módulo 1200",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "lineas_base_total": total_lb,
            "lineas_base_activas": activas,
            "mediciones": mediciones,
            "mediciones_validadas": med_validadas,
            "mediciones_pendientes_validacion": med_pendientes,
            "impactos_registrados": len(impactos),
            "impactos_reales": impactos_reales,
            "cambios_observados": cambios_observados,
            "impactos_con_atribucion": con_atribucion,
            "recientes": [
                {
                    "id": lb.id,
                    "indicador": lb.indicador,
                    "estado": lb.estado,
                    "enlace": f"/lineas-base/{lb.id}",
                }
                for lb in recientes
            ],
            "enlace": "/lineas-base",
        }


class FinOpsExtendidoAdapter:
    """Bloque 1110 — consumo, presupuestos, umbrales y bloqueos."""

    modulo = "finops_extendido"
    bloque = "1110"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "finops.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere finops.view"), "restringido": True}
        from app.finops_models import FinOpsBudget, FinOpsBudgetAlertState
        from app.llm_models import LlmInferenceLog
        from app.orchestration_models import FinOpsRecord
        from app.services import finops_service

        budgets_raw = (
            db.query(FinOpsBudget)
            .filter(FinOpsBudget.organization_id == organization_id, FinOpsBudget.active.is_(True))
            .all()
        )
        presupuestos = [finops_service.serialize_budget_detail(db, b) for b in budgets_raw]
        alertas = (
            db.query(func.count(FinOpsBudgetAlertState.id))
            .filter(FinOpsBudgetAlertState.organization_id == organization_id)
            .scalar()
            or 0
        )
        bloqueos = sum(1 for p in presupuestos if p.get("blocks_execution"))

        cons_q = db.query(func.count(FinOpsRecord.id)).filter(FinOpsRecord.organization_id == organization_id)
        if period_start:
            cons_q = cons_q.filter(FinOpsRecord.created_at >= period_start)
        consumos = cons_q.scalar() or 0

        opp_cost_q = (
            db.query(func.count(func.distinct(FinOpsRecord.opportunity_id)))
            .filter(
                FinOpsRecord.organization_id == organization_id,
                FinOpsRecord.opportunity_id.isnot(None),
            )
        )
        if period_start:
            opp_cost_q = opp_cost_q.filter(FinOpsRecord.created_at >= period_start)
        oportunidades_con_costo = opp_cost_q.scalar() or 0

        tokens_q = db.query(func.coalesce(func.sum(LlmInferenceLog.tokens_total), 0)).filter(
            LlmInferenceLog.organization_id == organization_id
        )
        if period_start:
            tokens_q = tokens_q.filter(LlmInferenceLog.created_at >= period_start)
        tokens = int(tokens_q.scalar() or 0)

        costo_q = db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0)).filter(
            FinOpsRecord.organization_id == organization_id
        )
        if period_start:
            costo_q = costo_q.filter(FinOpsRecord.created_at >= period_start)
        costo_total = float(costo_q.scalar() or 0)

        tiene_datos = consumos > 0 or presupuestos or tokens > 0
        return {
            "disponible": tiene_datos or bool(presupuestos),
            "estado": "Integrado con FinOps extendido 1110" if tiene_datos or presupuestos else "Sin información disponible",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "consumos_periodo": consumos,
            "tokens_periodo": tokens,
            "costo_periodo": costo_total if consumos > 0 or costo_total > 0 else None,
            "presupuestos": presupuestos,
            "alertas_registradas": alertas,
            "presupuestos_con_bloqueo": bloqueos,
            "oportunidades_con_costo": oportunidades_con_costo,
            "enlace": "/costos-valor",
        }


class ValorRetornoAdapter:
    """Bloque 1210 — valoración económica y retorno."""

    modulo = "valor_retorno"
    bloque = "1210"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "valoracion.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere valoracion.view"), "restringido": True}
        from app.valuation_models import (
            OpportunityExecutionCost,
            OpportunityValuation,
            OpportunityValuationExpected,
            OpportunityValuationReal,
        )

        val_count = (
            db.query(func.count(OpportunityValuation.id))
            .filter(OpportunityValuation.organization_id == organization_id)
            .scalar()
            or 0
        )
        if val_count == 0:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin valoraciones registradas"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/costos-valor",
            }

        exp_q = (
            db.query(func.sum(OpportunityValuationExpected.adjusted_expected))
            .join(OpportunityValuation, OpportunityValuationExpected.valuation_id == OpportunityValuation.id)
            .filter(OpportunityValuation.organization_id == organization_id)
        )
        valor_esperado = exp_q.scalar()

        real_q = (
            db.query(
                func.sum(OpportunityValuationReal.materialized_value),
                func.sum(OpportunityValuationReal.attributable_value),
            )
            .join(OpportunityValuation, OpportunityValuationReal.valuation_id == OpportunityValuation.id)
            .filter(
                OpportunityValuation.organization_id == organization_id,
                OpportunityValuationReal.is_current.is_(True),
            )
        )
        if period_start:
            real_q = real_q.filter(OpportunityValuationReal.created_at >= period_start)
        mat_sum, attr_sum = real_q.one()

        nature_rows = (
            db.query(
                OpportunityValuationReal.value_nature,
                func.sum(OpportunityValuationReal.attributable_value),
            )
            .join(OpportunityValuation, OpportunityValuationReal.valuation_id == OpportunityValuation.id)
            .filter(
                OpportunityValuation.organization_id == organization_id,
                OpportunityValuationReal.is_current.is_(True),
            )
            .group_by(OpportunityValuationReal.value_nature)
            .all()
        )
        valor_clasificado = _sum_valor_por_naturaleza(nature_rows)

        cost_q = (
            db.query(func.sum(OpportunityExecutionCost.amount))
            .join(OpportunityValuation, OpportunityExecutionCost.valuation_id == OpportunityValuation.id)
            .filter(OpportunityValuation.organization_id == organization_id)
        )
        costo = cost_q.scalar()

        valor_esperado_f = float(valor_esperado) if valor_esperado is not None else None
        valor_materializado_f = float(mat_sum) if mat_sum is not None else None
        valor_atribuible_f = float(attr_sum) if attr_sum is not None else None
        costo_f = float(costo) if costo is not None else None

        beneficio_neto = None
        retorno = None
        if valor_atribuible_f is not None and costo_f is not None and costo_f > 0:
            beneficio_neto = valor_atribuible_f - costo_f
            retorno = round((beneficio_neto / costo_f) * 100, 2)
        elif valor_atribuible_f is not None and (costo_f is None or costo_f == 0):
            beneficio_neto = valor_atribuible_f

        return {
            "disponible": True,
            "estado": "Integrado con motor 1210",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "valoraciones_total": val_count,
            "valor_esperado": valor_esperado_f,
            "valor_materializado": valor_materializado_f,
            "valor_atribuible": valor_atribuible_f,
            "valor_verificado": valor_clasificado["valor_verificado"],
            "valor_estimado": valor_clasificado["valor_estimado"],
            "valor_potencial": valor_clasificado["valor_potencial"],
            "valor_realizado": valor_clasificado["valor_realizado"],
            "costo": costo_f,
            "beneficio_neto": beneficio_neto,
            "retorno_porcentaje": retorno,
            "periodo_recuperacion": None,
            "semantica": SEMANTICA_VALOR,
            "enlace": "/costos-valor",
        }


class DiagnosticoAdapter:
    """Bloque 1220 — diagnósticos transversales."""

    modulo = "diagnostico"
    bloque = "1220"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "diagnosticos.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere diagnosticos.view"), "restringido": True}
        from app.diagnostic_models import Diagnostic, DiagnosticItem, DiagnosticProbableCause, DiagnosticOpportunityLink
        from app.services import diagnostic_service as dsvc

        diag_q = db.query(Diagnostic).filter(
            Diagnostic.organization_id == organization_id,
            Diagnostic.estado != "ARCHIVADO",
        )
        if period_start:
            diag_q = diag_q.filter(Diagnostic.created_at >= period_start)
        if estado:
            diag_q = diag_q.filter(Diagnostic.estado == estado.upper())
        diagnosticos = diag_q.order_by(Diagnostic.prioridad_score.desc().nullslast(), Diagnostic.created_at.desc()).limit(10).all()

        if not diagnosticos:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin diagnósticos activos"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/diagnosticos",
            }

        diag_ids = [d.id for d in diagnosticos]
        hallazgos = (
            db.query(func.count(DiagnosticItem.id))
            .filter(
                DiagnosticItem.organization_id == organization_id,
                DiagnosticItem.diagnostic_id.in_(diag_ids),
                DiagnosticItem.hallazgo_id.isnot(None),
            )
            .scalar()
            or 0
        )
        riesgos = (
            db.query(func.count(DiagnosticProbableCause.id))
            .filter(
                DiagnosticProbableCause.organization_id == organization_id,
                DiagnosticProbableCause.diagnostic_id.in_(diag_ids),
                DiagnosticProbableCause.tipo.in_(["CONFIRMADA", "PROBABLE"]),
            )
            .scalar()
            or 0
        )
        oportunidades_gen = (
            db.query(func.count(DiagnosticOpportunityLink.id))
            .filter(
                DiagnosticOpportunityLink.organization_id == organization_id,
                DiagnosticOpportunityLink.diagnostic_id.in_(diag_ids),
            )
            .scalar()
            or 0
        )

        return {
            "disponible": True,
            "estado": "Integrado con módulo 1220",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "diagnosticos_activos": len(diagnosticos),
            "hallazgos": hallazgos,
            "riesgos": riesgos,
            "oportunidades_generadas": oportunidades_gen,
            "prioritarios": [
                {
                    **dsvc.diagnostic_to_summary(d),
                    "enlace": f"/diagnosticos/{d.id}",
                }
                for d in diagnosticos[:5]
            ],
            "enlace": "/diagnosticos",
        }


class DiagnosticoExplicacionAdapter:
    """Bloque 1220 — explicaciones ejecutivas QUÉ → POR QUÉ → evidencia → certeza."""

    modulo = "explicacion"
    bloque = "1220"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "diagnosticos.view" not in permissions:
            return {
                **_no_disponible(self.modulo, self.bloque, "Requiere diagnosticos.view"),
                "restringido": True,
                "elementos": [],
            }
        from app.services import diagnostic_service as dsvc

        return dsvc.build_executive_explanations(
            db,
            organization_id,
            period_start=period_start,
            proceso=proceso,
            estado=estado,
        )


class SenalesAdapter:
    """Bloque 1120 — señales reales, procesadas y errores de ingesta."""

    modulo = "senales"
    bloque = "1120"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "oportunidades.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere oportunidades.view"), "restringido": True}
        from app.opportunity_models import ProactiveSignal
        from app.services import signal_ingestion_service as sigsvc

        base_q = db.query(ProactiveSignal).filter(ProactiveSignal.organization_id == organization_id)
        if period_start:
            base_q = base_q.filter(ProactiveSignal.created_at >= period_start)
        if proceso:
            base_q = base_q.filter(ProactiveSignal.proceso == proceso)
        if estado:
            base_q = base_q.filter(ProactiveSignal.estado_procesamiento == estado.upper())

        total = base_q.count()
        fuentes = len(sigsvc.list_sources(db, organization_id))

        por_modo = dict(
            db.query(ProactiveSignal.modo_ingesta, func.count())
            .filter(ProactiveSignal.organization_id == organization_id)
            .group_by(ProactiveSignal.modo_ingesta)
            .all()
        )
        por_estado = dict(
            db.query(ProactiveSignal.estado_procesamiento, func.count())
            .filter(ProactiveSignal.organization_id == organization_id)
            .group_by(ProactiveSignal.estado_procesamiento)
            .all()
        )
        sin_procesar = (
            db.query(func.count(ProactiveSignal.id))
            .filter(
                ProactiveSignal.organization_id == organization_id,
                ProactiveSignal.procesada.is_(False),
                ProactiveSignal.estado_procesamiento == "RECIBIDA",
            )
            .scalar()
            or 0
        )
        errores_ingesta = por_estado.get("RECHAZADA", 0) + por_estado.get("DUPLICADA", 0)
        recientes = base_q.order_by(ProactiveSignal.created_at.desc()).limit(5).all()

        return {
            "disponible": total > 0 or fuentes > 0,
            "estado": "Integrado con módulo 1120" if total > 0 or fuentes > 0 else "Sin información disponible",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "fuentes_activas": fuentes,
            "total": total,
            "sin_procesar": sin_procesar,
            "procesadas": por_estado.get("PROCESADA", 0),
            "errores_ingesta": errores_ingesta,
            "por_modo_ingesta": {
                "REAL": por_modo.get("REAL", 0),
                "SINTETICO": por_modo.get("SINTETICO", 0),
                "PRUEBA": por_modo.get("PRUEBA", 0),
            },
            "recientes": [
                {
                    "id": s.id,
                    "tipo": s.tipo,
                    "dominio": s.dominio,
                    "modo_ingesta": s.modo_ingesta,
                    "estado_procesamiento": s.estado_procesamiento,
                    "severidad": s.severidad,
                    "enlace": f"/senales/{s.id}",
                }
                for s in recientes
            ],
            "enlace": "/senales",
        }


class InteligenciaExternaAdapter:
    """Bloque 1240 — inteligencia externa, señales estratégicas y riesgos."""

    modulo = "inteligencia_externa"
    bloque = "1240"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "inteligencia_externa.view" not in permissions:
            return {
                **_no_disponible(self.modulo, self.bloque, "Requiere inteligencia_externa.view"),
                "restringido": True,
            }
        from app.external_intelligence_enums import RelevanceLevel, SignalClassification
        from app.external_models import ExternalSignalExtension, ExternalSource
        from app.opportunity_models import ProactiveSignal

        fuentes_activas = (
            db.query(func.count(ExternalSource.id))
            .filter(
                ExternalSource.organization_id == organization_id,
                ExternalSource.is_active.is_(True),
                ExternalSource.estado == "ACTIVA",
            )
            .scalar()
            or 0
        )

        ext_base = db.query(ExternalSignalExtension).filter(
            ExternalSignalExtension.organization_id == organization_id
        )
        if period_start:
            ext_base = ext_base.filter(ExternalSignalExtension.captured_at >= period_start)

        total_senales = ext_base.count()
        sin_validar = (
            ext_base.filter(ExternalSignalExtension.validated_at.is_(None))
            .count()
        )
        riesgos_abiertos = (
            ext_base.filter(
                ExternalSignalExtension.is_risk.is_(True),
                ExternalSignalExtension.validated_at.is_(None),
            )
            .count()
        )
        oportunidades_ext = (
            ext_base.filter(ExternalSignalExtension.classification == SignalClassification.OPORTUNIDAD)
            .count()
        )
        tendencias = (
            ext_base.filter(ExternalSignalExtension.classification == SignalClassification.TENDENCIA)
            .count()
        )

        por_clasificacion = dict(
            db.query(ExternalSignalExtension.classification, func.count())
            .filter(ExternalSignalExtension.organization_id == organization_id)
            .group_by(ExternalSignalExtension.classification)
            .all()
        )

        recientes_q = (
            db.query(ExternalSignalExtension, ProactiveSignal)
            .join(ProactiveSignal, ProactiveSignal.id == ExternalSignalExtension.signal_id)
            .filter(ExternalSignalExtension.organization_id == organization_id)
            .order_by(ExternalSignalExtension.captured_at.desc())
        )
        if period_start:
            recientes_q = recientes_q.filter(ExternalSignalExtension.captured_at >= period_start)
        recientes_rows = recientes_q.limit(5).all()

        recientes = [
            {
                "id": ext.signal_id,
                "titulo": (sig.tipo or ext.hecho_observado or "Señal externa")[:120],
                "clasificacion": ext.classification,
                "relevancia": ext.relevance,
                "es_riesgo": ext.is_risk,
                "validada": ext.validated_at is not None,
                "freshness": ext.freshness_status,
                "enlace": f"/inteligencia-externa/senales/{ext.signal_id}",
            }
            for ext, sig in recientes_rows
        ]

        tiene_datos = total_senales > 0 or fuentes_activas > 0
        return {
            "disponible": tiene_datos or fuentes_activas > 0,
            "estado": "Integrado con módulo 1240" if tiene_datos or fuentes_activas else "Sin datos",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "origen": "externa",
            "fuentes_activas": fuentes_activas,
            "total_senales": total_senales,
            "sin_validar": sin_validar,
            "riesgos_abiertos": riesgos_abiertos,
            "oportunidades_detectadas": oportunidades_ext,
            "tendencias": tendencias,
            "por_clasificacion": por_clasificacion,
            "recientes": recientes,
            "enlace": "/inteligencia-externa",
        }


class ComercialResumenAdapter:
    """Bloque 1280 — valor comercial por naturaleza (VERIFICADO/ESTIMADO/POTENCIAL)."""

    modulo = "comercial"
    bloque = "1280"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "comercial.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere comercial.view"), "restringido": True}
        from app.commercial_enums import ValueNature
        from app.commercial_models import CommercialProposal, CommercialProposalValue

        prop_q = db.query(CommercialProposal).filter(CommercialProposal.organization_id == organization_id)
        if period_start:
            prop_q = prop_q.filter(CommercialProposal.updated_at >= period_start)
        propuestas = prop_q.all()
        if not propuestas:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin propuestas comerciales"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/comercial",
            }

        prop_ids = [p.id for p in propuestas]
        nature_rows = (
            db.query(
                CommercialProposalValue.naturaleza,
                func.sum(CommercialProposalValue.valor_atribuible),
            )
            .filter(CommercialProposalValue.proposal_id.in_(prop_ids))
            .group_by(CommercialProposalValue.naturaleza)
            .all()
        )
        valor = _sum_valor_por_naturaleza(nature_rows)

        por_estado = dict(
            db.query(CommercialProposal.estado, func.count())
            .filter(CommercialProposal.organization_id == organization_id)
            .group_by(CommercialProposal.estado)
            .all()
        )

        roi_vals = [float(p.roi_pct) for p in propuestas if p.roi_pct is not None]
        payback_vals = [float(p.payback_meses) for p in propuestas if p.payback_meses is not None]
        margen_vals = [float(p.margen_pct) for p in propuestas if p.margen_pct is not None]

        result: dict[str, Any] = {
            "disponible": True,
            "estado": "Integrado con módulo 1280",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "propuestas_total": len(propuestas),
            "por_estado": por_estado,
            "valor_verificado": valor["valor_verificado"],
            "valor_estimado": valor["valor_estimado"],
            "valor_potencial": valor["valor_potencial"],
            "valor_realizado": valor["valor_realizado"],
            "roi_promedio": round(sum(roi_vals) / len(roi_vals), 2) if roi_vals else None,
            "payback_promedio_meses": round(sum(payback_vals) / len(payback_vals), 2) if payback_vals else None,
            "semantica": SEMANTICA_VALOR,
            "enlace": "/comercial",
        }
        if "comercial.approve" in permissions and margen_vals:
            result["margen_promedio_pct"] = round(sum(margen_vals) / len(margen_vals), 2)
        else:
            result["margen_promedio_pct"] = None
            result["margen_restringido"] = True
        return result


class AprendizajeAdapter:
    """Bloque 1260 — ciclos, patrones y recalibraciones."""

    modulo = "aprendizaje"
    bloque = "1260"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "aprendizaje.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere aprendizaje.view"), "restringido": True}
        from app.learning_models import CicloAprendizaje, PatronAprendizaje, Recalibracion
        from app.services import learning_service as lsvc

        ciclo_q = db.query(CicloAprendizaje).filter(CicloAprendizaje.organization_id == organization_id)
        if period_start:
            ciclo_q = ciclo_q.filter(CicloAprendizaje.created_at >= period_start)
        ciclos = ciclo_q.count()
        if ciclos == 0:
            patrones = db.query(func.count(PatronAprendizaje.id)).filter(
                PatronAprendizaje.organization_id == organization_id
            ).scalar() or 0
            if patrones == 0:
                return {
                    **_no_disponible(self.modulo, self.bloque, "Sin ciclos de aprendizaje"),
                    "modulo": self.modulo,
                    "bloque": self.bloque,
                    "enlace": "/aprendizaje",
                }

        por_estado = dict(
            db.query(CicloAprendizaje.estado, func.count())
            .filter(CicloAprendizaje.organization_id == organization_id)
            .group_by(CicloAprendizaje.estado)
            .all()
        )
        patrones_total = (
            db.query(func.count(PatronAprendizaje.id))
            .filter(PatronAprendizaje.organization_id == organization_id)
            .scalar()
            or 0
        )
        recal_pendientes = (
            db.query(func.count(Recalibracion.id))
            .filter(
                Recalibracion.organization_id == organization_id,
                Recalibracion.estado == "SUGERIDA",
            )
            .scalar()
            or 0
        )
        recientes = [
            lsvc.serializar_ciclo(c)
            for c in lsvc.listar_ciclos(db, organization_id)[:5]
        ]
        return {
            "disponible": True,
            "estado": "Integrado con módulo 1260",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "ciclos_total": ciclos,
            "por_estado": por_estado,
            "patrones_detectados": patrones_total,
            "recalibraciones_pendientes": recal_pendientes,
            "recientes": recientes,
            "tipo_contenido": "INFERENCIA",
            "semantica": SEMANTICA_VALOR,
            "enlace": "/aprendizaje",
        }


class OptimizacionAdapter:
    """Bloque 1290 — recomendaciones y simulaciones de portafolio."""

    modulo = "optimizacion"
    bloque = "1290"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "optimizacion.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere optimizacion.view"), "restringido": True}
        from app.optimization_models import OptimizacionRecomendacion
        from app.services import optimization_service as osvc

        rec_q = db.query(OptimizacionRecomendacion).filter(
            OptimizacionRecomendacion.organization_id == organization_id
        )
        if period_start:
            rec_q = rec_q.filter(OptimizacionRecomendacion.created_at >= period_start)
        total = rec_q.count()
        if total == 0:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin recomendaciones de optimización"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/optimizacion",
            }

        por_estado = dict(
            db.query(OptimizacionRecomendacion.estado, func.count())
            .filter(OptimizacionRecomendacion.organization_id == organization_id)
            .group_by(OptimizacionRecomendacion.estado)
            .all()
        )
        recientes_raw = osvc.listar_recomendaciones(db, organization_id, incluir_simulaciones=False)[:5]
        recientes = [
            {
                "id": r.id,
                "titulo": r.codigo,
                "estado": r.estado,
                "objetivo": r.objetivo,
                "tipo_contenido": "RECOMENDACION",
                "enlace": f"/optimizacion/{r.id}",
            }
            for r in recientes_raw
        ]
        return {
            "disponible": True,
            "estado": "Integrado con módulo 1290",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "recomendaciones_total": total,
            "por_estado": por_estado,
            "pendientes_aprobacion": por_estado.get("PROPUESTA", 0) + por_estado.get("REVISADA", 0),
            "aprobadas": por_estado.get("APROBADA", 0),
            "ejecutadas": por_estado.get("EJECUTADA", 0),
            "recientes": recientes,
            "tipo_contenido": "RECOMENDACION",
            "semantica": SEMANTICA_VALOR,
            "enlace": "/optimizacion",
        }


class TcoAdapter:
    """Bloque 1320 — resumen TCO reutilizando motor certificado."""

    modulo = "tco"
    bloque = "1320"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "tco.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere tco.view"), "restringido": True}
        from app.tco_models import TcoCosto
        from app.orchestration_models import FinOpsRecord
        from app.services import tco_service as tcosvc

        costos_count = (
            db.query(func.count(TcoCosto.id))
            .filter(TcoCosto.organization_id == organization_id, TcoCosto.is_active.is_(True))
            .scalar()
            or 0
        )
        finops_count = (
            db.query(func.count(FinOpsRecord.id))
            .filter(FinOpsRecord.organization_id == organization_id)
            .scalar()
            or 0
        )
        if costos_count == 0 and finops_count == 0:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin costos TCO registrados"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/tco",
            }

        tco_calc = tcosvc.calcular_tco(db, organization_id, {"incluir_finops": True}, user_id=None)

        margen = tco_calc.get("margen_pct")
        result: dict[str, Any] = {
            "disponible": True,
            "estado": "Integrado con módulo 1320",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "inversion_total": tco_calc.get("total"),
            "desglose": tco_calc.get("desglose"),
            "finops_ia": tco_calc.get("finops_ia"),
            "ingreso": tco_calc.get("ingreso"),
            "alertas": len(tco_calc.get("alertas") or []),
            "moneda": tco_calc.get("moneda"),
            "tipo_contenido": "INFERENCIA",
            "semantica": SEMANTICA_VALOR,
            "enlace": "/tco",
        }
        if "comercial.approve" in permissions:
            result["margen_pct"] = margen
            result["margen_bruto"] = tco_calc.get("margen_bruto")
        else:
            result["margen_pct"] = None
            result["margen_restringido"] = True
        return result


class ImplementacionAdapter:
    """Bloque 1340 — proyectos, hitos y riesgo de implementación."""

    modulo = "implementacion"
    bloque = "1340"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "implementacion.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere implementacion.view"), "restringido": True}
        from datetime import timezone

        from app.implementacion_enums import EstadoImplementacion
        from app.implementacion_models import ImplementacionHito, ImplementacionProyecto, ImplementacionRiesgo
        from app.services import implementacion_service as isvc

        proj_q = db.query(ImplementacionProyecto).filter(
            ImplementacionProyecto.organization_id == organization_id
        )
        if period_start:
            proj_q = proj_q.filter(ImplementacionProyecto.created_at >= period_start)
        proyectos = proj_q.all()
        if not proyectos:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin proyectos de implementación"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/implementacion",
            }

        activos = sum(
            1 for p in proyectos
            if p.estado not in (EstadoImplementacion.CERRADO, EstadoImplementacion.CANCELADO)
        )
        por_estado = dict(
            db.query(ImplementacionProyecto.estado, func.count())
            .filter(ImplementacionProyecto.organization_id == organization_id)
            .group_by(ImplementacionProyecto.estado)
            .all()
        )
        now = datetime.now(timezone.utc)
        hitos_riesgo = (
            db.query(func.count(ImplementacionHito.id))
            .filter(
                ImplementacionHito.organization_id == organization_id,
                ImplementacionHito.estado.notin_(("COMPLETADO", "CANCELADO")),
                ImplementacionHito.fecha_objetivo.isnot(None),
                ImplementacionHito.fecha_objetivo < now,
            )
            .scalar()
            or 0
        )
        riesgos_abiertos = (
            db.query(func.count(ImplementacionRiesgo.id))
            .filter(
                ImplementacionRiesgo.organization_id == organization_id,
                ImplementacionRiesgo.estado == "ABIERTO",
            )
            .scalar()
            or 0
        )
        recientes = isvc.list_proyectos(db, organization_id)[:5]
        return {
            "disponible": True,
            "estado": "Integrado con módulo 1340",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "proyectos_total": len(proyectos),
            "proyectos_activos": activos,
            "por_estado": por_estado,
            "hitos_en_riesgo": hitos_riesgo,
            "riesgos_abiertos": riesgos_abiertos,
            "recientes": recientes,
            "tipo_contenido": "HECHO",
            "enlace": "/implementacion",
        }


class MultiproveedorAdapter:
    """Bloque 1270 — salud y observabilidad multiproveedor (sin secretos)."""

    modulo = "multiproveedor"
    bloque = "1270"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "llm.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere llm.view"), "restringido": True}
        from app.services import llm_health_service, llm_observability_service

        salud = llm_health_service.list_providers_health(db, organization_id)
        periodo = "30d" if period_start else "mtd"
        observabilidad = llm_observability_service.get_observability_summary(
            db, organization_id, periodo=periodo
        )
        if not salud and not observabilidad.get("total_inferencias"):
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin proveedores ni consumo IA"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/administracion/proveedores-ia",
            }

        degradados = sum(1 for p in salud if p.get("estado") == "DEGRADADO")
        no_config = sum(1 for p in salud if p.get("estado") == "NO_CONFIGURADO")
        return {
            "disponible": True,
            "estado": "Integrado con módulo 1270",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "proveedores_total": len(salud),
            "proveedores_degradados": degradados,
            "proveedores_sin_configurar": no_config,
            "salud": salud,
            "observabilidad": observabilidad,
            "tipo_contenido": "HECHO",
            "enlace": "/administracion/proveedores-ia",
        }


class Mb07PlanificadorAdapter:
    """MB-07 — planificador de consumo, capacidad y costos IA."""

    modulo = "mb07_planificador"
    bloque = "MB-07"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "finops.view" not in permissions and "finops.planner.simulate" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere finops.view"), "restringido": True}
        from app.consumption_planner_models import ConsumptionPlannerOrgConfig
        from app.services import consumption_planner_service as mb07

        config = (
            db.query(ConsumptionPlannerOrgConfig)
            .filter(ConsumptionPlannerOrgConfig.organization_id == organization_id)
            .first()
        )
        if not config:
            return {
                **_no_disponible(self.modulo, self.bloque, "Sin configuración de planificador"),
                "modulo": self.modulo,
                "bloque": self.bloque,
                "enlace": "/costos-valor",
            }
        try:
            contrato = mb07.centro_control_contract(db, organization_id)
        except Exception:
            db.rollback()
            return {**_no_disponible(self.modulo, self.bloque, "Datos de planificador no disponibles"), "modulo": self.modulo, "bloque": self.bloque}
        tiene = any(
            contrato.get(k) is not None
            for k in ("consumo_real", "consumo_proyectado", "presupuesto_limite", "capacidad_riesgo")
        )
        return {
            "disponible": tiene,
            "estado": "Integrado con MB-07" if tiene else "Sin información disponible",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "INFERENCIA",
            "semantica": SEMANTICA_VALOR,
            "consumo_real": contrato.get("consumo_real"),
            "consumo_proyectado": contrato.get("consumo_proyectado"),
            "presupuesto_limite": contrato.get("presupuesto_limite"),
            "presupuesto_utilizacion_pct": contrato.get("presupuesto_utilizacion_pct"),
            "capacidad_riesgo": contrato.get("capacidad_riesgo"),
            "sobreconsumo": contrato.get("sobreconsumo"),
            "margen_bruto_estimado": contrato.get("margen_bruto_estimado"),
            "moneda": contrato.get("currency"),
            "enlace": "/costos-valor",
        }


class Mb11ComunicacionesAdapter:
    """MB-11 — indicadores ejecutivos de comunicaciones."""

    modulo = "mb11_comunicaciones"
    bloque = "MB-11"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "communications.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere communications.view"), "restringido": True}
        from app.services import communications_service as comm

        contrato = comm.contrato_centro_control(db, organization_id)
        total = (contrato.get("enviadas") or 0) + (contrato.get("pendientes") or 0) + (contrato.get("fallidas") or 0)
        return {
            "disponible": total > 0 or contrato.get("canales_degradados", 0) > 0,
            "estado": "Integrado con MB-11" if total > 0 else "Sin mensajes registrados",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "HECHO",
            "enviados": contrato.get("enviadas"),
            "pendientes": contrato.get("pendientes"),
            "fallidos": contrato.get("fallidas"),
            "tasa_fallo_pct": contrato.get("tasa_fallo_pct"),
            "canales_degradados": contrato.get("canales_degradados"),
            "reintentos_pendientes": contrato.get("reintentos_pendientes"),
            "criticas_pendientes": contrato.get("criticas_pendientes"),
            "enlace": "/comunicaciones",
        }


class Mb12MesaAyudaAdapter:
    """MB-12 — indicadores ejecutivos de mesa de ayuda."""

    modulo = "mb12_soporte"
    bloque = "MB-12"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "support.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere support.view"), "restringido": True}
        from app.services import support_service as soporte

        contrato = soporte.contrato_centro_control(db, organization_id)
        return {
            "disponible": True,
            "estado": "Integrado con MB-12",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "HECHO",
            "casos_abiertos": contrato.get("casos_abiertos"),
            "casos_criticos": contrato.get("casos_criticos"),
            "casos_vencidos": contrato.get("casos_vencidos"),
            "tiempo_medio_respuesta_min": contrato.get("tiempo_medio_respuesta_min"),
            "tiempo_medio_resolucion_min": contrato.get("tiempo_medio_resolucion_min"),
            "principales_categorias": contrato.get("principales_categorias"),
            "enlace": "/soporte",
        }


class AuditorEmpleadosAdapter:
    """Auditor de Empleados IA — hallazgos y salud (solo lectura ejecutiva)."""

    modulo = "auditor_empleados"
    bloque = "AUDITOR"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "auditor_empleados.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere auditor_empleados.view"), "restringido": True}
        from app.employee_audit_models import (
            EmployeeAuditFinding,
            EmployeeAuditPolicy,
            EmployeeAuditRun,
            HEALTH_STATUSES,
        )
        from app.orchestration_models import AIEmployee

        org_id = organization_id
        employees = (
            db.query(AIEmployee)
            .filter(AIEmployee.organization_id == org_id, AIEmployee.is_active.is_(True))
            .all()
        )
        counts = {h: 0 for h in HEALTH_STATUSES}
        for emp in employees:
            from app.employee_audit_models import EmployeeAuditAssessment

            latest = (
                db.query(EmployeeAuditAssessment)
                .filter(
                    EmployeeAuditAssessment.organization_id == org_id,
                    EmployeeAuditAssessment.employee_id == emp.id,
                )
                .order_by(EmployeeAuditAssessment.created_at.desc())
                .first()
            )
            st = latest.health_status if latest else "OBSERVAR"
            if st in counts:
                counts[st] += 1
        last_run = (
            db.query(EmployeeAuditRun)
            .filter(EmployeeAuditRun.organization_id == org_id, EmployeeAuditRun.status == "COMPLETED")
            .order_by(EmployeeAuditRun.finished_at.desc())
            .first()
        )
        open_findings = (
            db.query(EmployeeAuditFinding)
            .filter(EmployeeAuditFinding.organization_id == org_id, EmployeeAuditFinding.status == "ABIERTO")
            .count()
        )
        policy = (
            db.query(EmployeeAuditPolicy)
            .filter(EmployeeAuditPolicy.organization_id == org_id, EmployeeAuditPolicy.employee_id.is_(None))
            .first()
        )
        overdue = 0
        if policy and policy.next_scheduled_at:
            from datetime import timezone as tz

            next_at = policy.next_scheduled_at
            if next_at.tzinfo is None:
                next_at = next_at.replace(tzinfo=tz.utc)
            if next_at < datetime.now(tz.utc):
                overdue = 1
        resumen = {
            "total": len(employees),
            "saludables": counts.get("SALUDABLE", 0),
            "requieren_mejora": counts.get("REQUIERE_MEJORA", 0),
            "criticos": counts.get("CRITICO", 0),
            "hallazgos_abiertos": open_findings,
            "auditorias_vencidas": overdue,
            "ultima_auditoria_at": last_run.finished_at if last_run else None,
        }
        return {
            "disponible": resumen.get("total", 0) > 0 or resumen.get("hallazgos_abiertos", 0) > 0,
            "estado": "Integrado con Auditor Empleados IA",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "HECHO",
            "total_empleados": resumen.get("total"),
            "saludables": resumen.get("saludables"),
            "requieren_mejora": resumen.get("requieren_mejora"),
            "criticos": resumen.get("criticos"),
            "hallazgos_abiertos": resumen.get("hallazgos_abiertos"),
            "auditorias_vencidas": resumen.get("auditorias_vencidas"),
            "ultima_auditoria_at": resumen.get("ultima_auditoria_at"),
            "nota_gobierno": "Auditor recomienda. Humano decide. Fábrica ejecuta.",
            "auto_execution_blocked": True,
            "enlace": "/empleados/auditoria",
        }


class MiTrabajoAdapter:
    """Mi Trabajo — resumen ejecutivo (no duplica bandeja)."""

    modulo = "mi_trabajo"
    bloque = "MI_TRABAJO"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
        user: Any | None = None,
    ) -> dict[str, Any]:
        from app.models import User
        from app.permissions import user_permissions
        from app.services import trabajo_service as trabajo

        viewer = user if isinstance(user, User) else None
        if not viewer:
            viewer = db.query(User).filter(User.organization_id == organization_id).first()
        if not viewer:
            return {**_no_disponible(self.modulo, self.bloque, "Sin usuarios en organización"), "modulo": self.modulo, "bloque": self.bloque}
        if not trabajo.can_access_trabajo(viewer, db):
            return {**_no_disponible(self.modulo, self.bloque, "Sin acceso a Mi Trabajo"), "restringido": True}
        try:
            resumen = trabajo.resumen(db, viewer, organization_id=organization_id)
        except Exception:
            db.rollback()
            return {**_no_disponible(self.modulo, self.bloque, "Resumen no disponible temporalmente"), "modulo": self.modulo, "bloque": self.bloque}
        return {
            "disponible": True,
            "estado": "Integrado con Mi Trabajo",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "HECHO",
            "pendientes": resumen.get("pendientes"),
            "vencidas": resumen.get("vencidas"),
            "requieren_aprobacion": resumen.get("requieren_aprobacion"),
            "total_visible": resumen.get("total_visible"),
            "nota": "Resumen ejecutivo — la bandeja completa está en Mi Trabajo",
            "enlace": "/trabajo",
        }


class ContinuidadAdapter:
    """Continuidad y resiliencia — riesgos operativos."""

    modulo = "continuidad"
    bloque = "1360"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "continuidad.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere continuidad.view"), "restringido": True}
        from app.services import continuidad_service as cont

        resumen = cont.centro_control_resumen(db, organization_id)
        tiene = (
            resumen.get("incidentes_abiertos", 0) > 0
            or resumen.get("degradados", 0) > 0
            or resumen.get("backups_fallidos", 0) > 0
            or len(resumen.get("disponibilidad") or []) > 0
        )
        return {
            "disponible": tiene,
            "estado": "Integrado con continuidad" if tiene else "Sin incidentes ni degradación registrada",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "HECHO",
            "servicios_disponibles": len(resumen.get("disponibilidad") or []),
            "servicios_degradados": resumen.get("degradados"),
            "incidentes_abiertos": resumen.get("incidentes_abiertos"),
            "backups_fallidos": resumen.get("backups_fallidos"),
            "alertas": resumen.get("alertas"),
            "enlace": "/continuidad",
        }


class MotorEconomicoAdapter:
    """Motor Económico EIAAX — indicadores ANTES/PROYECTADO/REAL unificados."""

    modulo = "motor_economico"
    bloque = "1600"

    def fetch(
        self,
        db: Session,
        organization_id: str,
        *,
        permissions: set[str],
        period_start: datetime | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        if "finops.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere finops.view"), "restringido": True}
        from app.services import economic_motor_service as motor

        try:
            indicators = motor.build_indicators(db, organization_id)
            entity = motor.entity_view_summary(db, organization_id)
        except Exception:
            db.rollback()
            return {**_no_disponible(self.modulo, self.bloque, "Motor económico no disponible"), "modulo": self.modulo}
        return {
            "disponible": True,
            "estado": "Integrado con Motor Económico EIAAX",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "tipo_contenido": "INFERENCIA",
            "fases": indicators.get("fases"),
            "valor_realizado": entity.get("valores", {}).get("valor_realizado"),
            "valor_potencial": entity.get("valores", {}).get("valor_potencial"),
            "nota_potencial": SEMANTICA_VALOR.get("nota_potencial"),
            "economia_privada_expuesta": False,
            "enlace": "/costos-valor",
        }
