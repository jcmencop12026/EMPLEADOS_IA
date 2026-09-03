"""Contratos de integración futura — fail-closed, sin acoplamiento directo."""

from __future__ import annotations

from typing import Any, TypedDict


class ContratoMotorEconomicoB(TypedDict, total=False):
    """Agente B — motor económico. Solo lectura de IDs; sin duplicar cálculos."""

    expediente_id: str | None
    dossier_id: str | None
    oportunidad_id: str | None
    escenario_tipo: str | None
    nota: str


class ContratoCentroControl(TypedDict, total=False):
    organization_id: str
    expediente_id: str | None
    lectura_sugerida: str
    enlace: str


class ContratoAsistenteEiaax(TypedDict, total=False):
    expediente_id: str
    contexto_minimo: dict[str, Any]
    restriccion: str


class ContratoPiiax(TypedDict, total=False):
    capacidad_codigo: str | None
    estado: str
    nota: str


class ContratoResultados(TypedDict, total=False):
    oportunidad_id: str | None
    linea_base_id: str | None
    nota: str


CONTRATOS_FUTUROS = {
    "motor_economico_b": {
        "version": "0.1",
        "descripcion": "Cuantificación económica de escenarios transformación",
        "payload_ejemplo": ContratoMotorEconomicoB(
            expediente_id=None,
            dossier_id=None,
            escenario_tipo="OPTIMIZADO",
            nota="Integración posterior vía API estable — no calcular aquí",
        ),
    },
    "centro_control": {
        "version": "0.1",
        "descripcion": "Lecturas estratégicas/operacionales del dossier",
        "payload_ejemplo": ContratoCentroControl(
            organization_id="",
            lectura_sugerida="gerencia",
            enlace="/centro-estrategico",
        ),
    },
    "asistente_eiaax": {
        "version": "0.1",
        "descripcion": "Contexto mínimo para preguntas adaptativas",
    },
    "documentos": {
        "version": "0.1",
        "descripcion": "Evidencias documentales referenciadas en expediente",
    },
    "piiax": {
        "version": "0.1",
        "descripcion": "Capacidades externas sin scraping",
    },
    "resultados": {
        "version": "0.1",
        "descripcion": "Medición ANTES/PROYECTADO/REAL post-implementación",
    },
}

CADENA_PASOS = (
    "EVIDENCIA",
    "ANALISIS",
    "HALLAZGO",
    "CAUSA",
    "IMPACTO",
    "OPORTUNIDAD",
    "RECOMENDACION",
    "ACCION",
)

OPORTUNIDAD_CATEGORIAS = frozenset({
    "AHORRO",
    "PRODUCTIVIDAD",
    "RECUPERACION_INGRESOS",
    "NUEVOS_INGRESOS",
    "RIESGO",
    "CALIDAD",
    "EXPERIENCIA",
    "CUMPLIMIENTO",
    "EXPANSION",
})

DECISION_PRIORIDAD = frozenset({"HACER", "ESTUDIAR", "ESPERAR", "DESCARTAR"})
