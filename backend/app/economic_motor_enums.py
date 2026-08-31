"""Enumeraciones unificadas — Motor Económico EIAAX (reutiliza FinOps/MB-07/1210)."""

from __future__ import annotations

# Clasificación de costo (MB-07)
COST_CLASSES = frozenset({"DIRECTO", "TRANSVERSAL_ATRIBUIBLE", "PLATAFORMA"})

# Naturaleza del importe
AMOUNT_KINDS = frozenset({"ESTIMADO", "REAL", "PROYECTADO"})

# Fase indicador Centro de Control
INDICATOR_PHASES = frozenset({"ANTES", "PROYECTADO", "REAL"})


class CostSource:
    CONSUMO_IA = "CONSUMO_IA"
    TOKENS = "TOKENS"
    PROVEEDOR_MODELO = "PROVEEDOR_MODELO"
    INFRAESTRUCTURA = "INFRAESTRUCTURA"
    SERVICIOS_EXTERNOS = "SERVICIOS_EXTERNOS"
    INTEGRACIONES = "INTEGRACIONES"
    IMPLEMENTACION = "IMPLEMENTACION"
    HORAS_RECURSOS = "HORAS_RECURSOS"
    SOPORTE = "SOPORTE"
    OPERACION = "OPERACION"
    LICENCIAS = "LICENCIAS"
    OTRO = "OTRO"

    ALL = (
        CONSUMO_IA,
        TOKENS,
        PROVEEDOR_MODELO,
        INFRAESTRUCTURA,
        SERVICIOS_EXTERNOS,
        INTEGRACIONES,
        IMPLEMENTACION,
        HORAS_RECURSOS,
        SOPORTE,
        OPERACION,
        LICENCIAS,
        OTRO,
    )


class EconomicScope:
    EMPLEADO_IA = "EMPLEADO_IA"
    AGENTE_TRANSVERSAL = "AGENTE_TRANSVERSAL"
    EVALUACION = "EVALUACION"
    OPORTUNIDAD = "OPORTUNIDAD"
    IMPLEMENTACION = "IMPLEMENTACION"
    ORGANIZACION = "ORGANIZACION"

    ALL = (
        EMPLEADO_IA,
        AGENTE_TRANSVERSAL,
        EVALUACION,
        OPORTUNIDAD,
        IMPLEMENTACION,
        ORGANIZACION,
    )


# Mapeo categoría FinOps → fuente motor
FINOPS_CATEGORY_TO_SOURCE: dict[str, str] = {
    "Modelo IA": CostSource.CONSUMO_IA,
    "OCR": CostSource.SERVICIOS_EXTERNOS,
    "API externa": CostSource.SERVICIOS_EXTERNOS,
    "Integración": CostSource.INTEGRACIONES,
    "Almacenamiento": CostSource.INFRAESTRUCTURA,
    "Procesamiento": CostSource.INFRAESTRUCTURA,
    "Ejecución": CostSource.OPERACION,
    "Otro": CostSource.OTRO,
}

# Mapeo certeza FinOps → naturaleza valor
FINOPS_CERTAINTY_TO_NATURE: dict[str, str] = {
    "Real": "VERIFICADO",
    "Estimado": "ESTIMADO",
    "No disponible": "ESTIMADO",
}

# Tipos de valor soportados (alineados 1210)
class EconomicValueType:
    AHORRO = "AHORRO"
    PERDIDA_EVITADA = "PÉRDIDA EVITADA"
    INGRESO_RECUPERADO = "INGRESO RECUPERADO"
    PRODUCTIVIDAD_LIBERADA = "PRODUCTIVIDAD LIBERADA"
    NUEVO_INGRESO = "NUEVO INGRESO"
    OPORTUNIDAD_CAPTURADA = "OPORTUNIDAD CAPTURADA"
    RIESGO_MITIGADO = "RIESGO MITIGADO"
    OTRO = "OTRO"

    ALL = (
        AHORRO,
        PERDIDA_EVITADA,
        INGRESO_RECUPERADO,
        PRODUCTIVIDAD_LIBERADA,
        NUEVO_INGRESO,
        OPORTUNIDAD_CAPTURADA,
        RIESGO_MITIGADO,
        OTRO,
    )


ECONOMIC_TO_FINOPS_VALUE_TYPE: dict[str, str] = {
    EconomicValueType.AHORRO: "Reducción de costo",
    EconomicValueType.PERDIDA_EVITADA: "Pérdida evitada",
    EconomicValueType.INGRESO_RECUPERADO: "Ingreso generado",
    EconomicValueType.PRODUCTIVIDAD_LIBERADA: "Productividad",
    EconomicValueType.NUEVO_INGRESO: "Ingreso generado",
    EconomicValueType.OPORTUNIDAD_CAPTURADA: "Ingreso generado",
    EconomicValueType.RIESGO_MITIGADO: "Pérdida evitada",
    EconomicValueType.OTRO: "Otro",
}


class PriceRecommendationStatus:
    BORRADOR = "BORRADOR"
    REVISADO = "REVISADO"
    DESCARTADO = "DESCARTADO"
