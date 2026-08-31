"""Enumeraciones — Valoración económica y ROI por oportunidad (1210)."""

from __future__ import annotations


class ValueType:
    AHORRO = "AHORRO"
    PERDIDA_EVITADA = "PÉRDIDA EVITADA"
    INGRESO_RECUPERADO = "INGRESO RECUPERADO"
    PRODUCTIVIDAD_LIBERADA = "PRODUCTIVIDAD LIBERADA"
    NUEVO_INGRESO = "NUEVO INGRESO"
    OPORTUNIDAD_COMERCIAL = "OPORTUNIDAD COMERCIAL"
    RIESGO_MITIGADO = "RIESGO MITIGADO"
    OTRO = "OTRO"

    ALL = (
        AHORRO,
        PERDIDA_EVITADA,
        INGRESO_RECUPERADO,
        PRODUCTIVIDAD_LIBERADA,
        NUEVO_INGRESO,
        OPORTUNIDAD_COMERCIAL,
        RIESGO_MITIGADO,
        OTRO,
    )


class ValueScope:
    INTERNO = "INTERNO"
    EXTERNO = "EXTERNO"


class ScenarioType:
    CONSERVADOR = "CONSERVADOR"
    BASE = "BASE"
    OPTIMISTA = "OPTIMISTA"

    ALL = (CONSERVADOR, BASE, OPTIMISTA)


class ValueDiscipline:
    """Naturaleza de la cifra — disciplina de valor."""

    MEDIDA = "MEDIDA"
    CALCULADA = "CALCULADA"
    ESTIMADA = "ESTIMADA"
    PROPUESTA = "PROPUESTA"


class RealValueNature:
    VERIFICADO = "VERIFICADO"
    ESTIMADO = "ESTIMADO"
    POTENCIAL = "POTENCIAL"


class AttributionLevel:
    NO_ATRIBUIBLE = "NO ATRIBUIBLE"
    PARCIALMENTE_ATRIBUIBLE = "PARCIALMENTE ATRIBUIBLE"
    ATRIBUIBLE = "ATRIBUIBLE"


class ExecutionCostType:
    IA = "IA"
    HORAS_HUMANAS = "HORAS HUMANAS"
    SERVICIOS = "SERVICIOS"
    INFRAESTRUCTURA = "INFRAESTRUCTURA"
    LICENCIAS = "LICENCIAS"
    OTRO = "OTRO"


class ValuationStatus:
    BORRADOR = "BORRADOR"
    ACTIVA = "ACTIVA"
    VALIDADA = "VALIDADA"


class ValuationHistoryAction:
    CREATED = "valoracion.creada"
    EXPECTED_MODIFIED = "valor.esperado.modificado"
    SCENARIO_MODIFIED = "escenario.modificado"
    REAL_REGISTERED = "valor.real.registrado"
    ATTRIBUTION_MODIFIED = "atribucion.modificada"
    COST_REGISTERED = "costo.registrado"
    VALIDATED = "valoracion.validada"
