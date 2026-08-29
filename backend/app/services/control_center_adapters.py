"""Contratos/adaptadores para integración futura del Centro de Control — Bloque 1230.

No duplican persistencia. Cada adaptador consulta el módulo origen cuando está
disponible o devuelve estado controlado «Sin información disponible».
"""

from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session


class ModuloAdapter(Protocol):
    modulo: str
    bloque: str

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        ...


def _no_disponible(modulo: str, bloque: str, razon: str) -> dict[str, Any]:
    return {
        "disponible": False,
        "estado": "Sin información disponible",
        "modulo": modulo,
        "bloque": bloque,
        "integracion": razon,
    }


class OportunidadesAdapter:
    """Bloque 1100 — cierre operativo UI (rama separada). Backend 1030 disponible en base."""

    modulo = "oportunidades"
    bloque = "1100"

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        if "oportunidades.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere permiso oportunidades.view"), "restringido": True}
        from app.services import proactive_service as psvc

        resumen = psvc.business_summary(db, organization_id)
        from app.opportunity_models import Opportunity
        from sqlalchemy import func

        por_estado = dict(
            db.query(Opportunity.estado, func.count())
            .filter(Opportunity.organization_id == organization_id)
            .group_by(Opportunity.estado)
            .all()
        )
        criticas = (
            db.query(Opportunity)
            .filter(
                Opportunity.organization_id == organization_id,
                Opportunity.estado.in_(["PENDIENTE_APROBACION", "EN_EJECUCION"]),
                Opportunity.urgencia.in_(["ALTA", "CRITICA"]),
            )
            .order_by(Opportunity.prioridad_score.desc().nullslast())
            .limit(5)
            .all()
        )
        return {
            "disponible": True,
            "estado": "Datos consolidados desde módulo 1030",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "integracion_ui_1100": "Pendiente — usar rama cursor/1100-cierre-operativo-oportunidades",
            "resumen": resumen,
            "por_estado": por_estado,
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
        }


class ImpactoAdapter:
    """Bloque 1200 — línea base e impacto (rama cursor/1200-linea-base-impacto)."""

    modulo = "impacto"
    bloque = "1200"

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        if "linea_base.view" not in permissions:
            return {
                **_no_disponible(
                    self.modulo,
                    self.bloque,
                    "Integrar vía GET /api/lineas-base cuando el bloque 1200 esté desplegado",
                ),
                "restringido": "linea_base.view" not in permissions,
                "contrato": {
                    "endpoints": ["/api/lineas-base", "/api/lineas-base/{id}", "/api/lineas-base/oportunidad/{id}"],
                    "permiso": "linea_base.view",
                },
            }
        try:
            from app.baseline_models import LineaBase
            from sqlalchemy import func

            total = db.query(func.count(LineaBase.id)).filter(LineaBase.organization_id == organization_id).scalar() or 0
            activas = (
                db.query(func.count(LineaBase.id))
                .filter(LineaBase.organization_id == organization_id, LineaBase.estado.in_(["ACTIVA", "EN_MEDICION"]))
                .scalar()
                or 0
            )
            return {
                "disponible": True,
                "estado": "Módulo 1200 integrado",
                "modulo": self.modulo,
                "bloque": self.bloque,
                "lineas_base_total": total,
                "lineas_base_activas": activas,
                "enlace": "/lineas-base",
            }
        except Exception:
            return {
                **_no_disponible(
                    self.modulo,
                    self.bloque,
                    "Desplegar bloque 1200 — adaptador compatible sin duplicar modelos",
                ),
                "contrato": {
                    "endpoints": ["/api/lineas-base"],
                    "campos": ["linea_base", "medicion", "impacto_esperado", "impacto_real", "atribucion"],
                },
            }


class FinOpsExtendidoAdapter:
    """Bloque 1110 — extensiones FinOps (rama separada)."""

    modulo = "finops_extendido"
    bloque = "1110"

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        base = {
            "modulo": self.modulo,
            "bloque": self.bloque,
            "integracion_1110": "Pendiente — consumir endpoints FinOps extendidos del bloque 1110",
        }
        if "finops.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere finops.view"), **base, "restringido": True}
        return {**base, "disponible": False, "estado": "Sin información disponible", "nota": "FinOps base disponible en sección finops"}


class ValorRetornoAdapter:
    """Bloque 1210 — valoración y retorno (en desarrollo paralelo)."""

    modulo = "valor_retorno"
    bloque = "1210"

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        return {
            **_no_disponible(self.modulo, self.bloque, "Integrar motor económico 1210 sin duplicar FinOps"),
            "contrato": {
                "campos_futuros": [
                    "valor_esperado",
                    "valor_materializado",
                    "valor_atribuible",
                    "costo_total",
                    "beneficio_neto",
                    "retorno",
                    "periodo_recuperacion",
                ],
            },
        }


class DiagnosticoAdapter:
    """Bloque 1220 — diagnóstico ejecutivo (en desarrollo paralelo)."""

    modulo = "diagnostico"
    bloque = "1220"

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        return {
            **_no_disponible(self.modulo, self.bloque, "Integrar hallazgos/riesgos del bloque 1220"),
            "contrato": {
                "campos_futuros": ["hallazgos", "riesgos", "causas_probables", "prioridades", "oportunidades_generadas"],
            },
        }


class SenalesAdapter:
    """Bloque 1120 — señales (rama separada). Tabla proactive_signals disponible en base."""

    modulo = "senales"
    bloque = "1120"

    def fetch(self, db: Session, organization_id: str, *, permissions: set[str]) -> dict[str, Any]:
        if "oportunidades.view" not in permissions:
            return {**_no_disponible(self.modulo, self.bloque, "Requiere oportunidades.view"), "restringido": True}
        from app.opportunity_models import ProactiveSignal
        from sqlalchemy import func

        total = db.query(func.count(ProactiveSignal.id)).filter(ProactiveSignal.organization_id == organization_id).scalar() or 0
        sin_procesar = (
            db.query(func.count(ProactiveSignal.id))
            .filter(ProactiveSignal.organization_id == organization_id, ProactiveSignal.procesada.is_(False))
            .scalar()
            or 0
        )
        recientes = (
            db.query(ProactiveSignal)
            .filter(ProactiveSignal.organization_id == organization_id)
            .order_by(ProactiveSignal.created_at.desc())
            .limit(5)
            .all()
        )
        return {
            "disponible": total > 0,
            "estado": "Consolidado desde proactive_signals" if total else "Sin información disponible",
            "modulo": self.modulo,
            "bloque": self.bloque,
            "integracion_1120": "Completar con ingestión/errores del bloque 1120",
            "fuentes_activas": len({s.origen for s in recientes}) if recientes else 0,
            "total": total,
            "sin_procesar": sin_procesar,
            "procesadas": total - sin_procesar,
            "recientes": [
                {
                    "id": s.id,
                    "tipo": s.tipo,
                    "dominio": s.dominio,
                    "severidad": s.severidad,
                    "procesada": s.procesada,
                    "fecha": s.created_at.isoformat() if s.created_at else None,
                }
                for s in recientes
            ],
        }
