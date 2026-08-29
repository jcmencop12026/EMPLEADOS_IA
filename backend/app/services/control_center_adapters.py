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
            "costo": costo_f,
            "beneficio_neto": beneficio_neto,
            "retorno_porcentaje": retorno,
            "periodo_recuperacion": None,
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
    ) -> dict[str, Any]:
        if "oportunidades.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere oportunidades.view"), "restringido": True}
        from app.opportunity_models import ProactiveSignal
        from app.services import signal_ingestion_service as sigsvc

        base_q = db.query(ProactiveSignal).filter(ProactiveSignal.organization_id == organization_id)
        if period_start:
            base_q = base_q.filter(ProactiveSignal.created_at >= period_start)

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
