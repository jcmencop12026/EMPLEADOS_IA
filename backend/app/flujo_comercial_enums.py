"""Enums — Flujo comercial V1 EIAAX (1730)."""

from __future__ import annotations

from enum import StrEnum


class OrigenOportunidadComercial(StrEnum):
    SOLICITADA = "SOLICITADA"
    INTERNA = "INTERNA"
    EXTERNA = "EXTERNA"


class ClasificacionValorOportunidad(StrEnum):
    VERIFICADO = "VERIFICADO"
    ESTIMADO = "ESTIMADO"
    POTENCIAL = "POTENCIAL"


class TipoInstrumentoContractual(StrEnum):
    NDA = "NDA"
    AUTORIZACION_EVAL = "AUTORIZACION_EVAL"
    TRATAMIENTO_DATOS = "TRATAMIENTO_DATOS"
    DIAGNOSTICO = "DIAGNOSTICO"
    IMPLEMENTACION = "IMPLEMENTACION"
    SERVICIO_EIAAX = "SERVICIO_EIAAX"
    EMPLEADO_IA = "EMPLEADO_IA"
    CONSUMO_IA = "CONSUMO_IA"
    INTEGRACION = "INTEGRACION"
    SLA = "SLA"
    RESULTADOS = "RESULTADOS"
    VARIABLE_EXITO = "VARIABLE_EXITO"


class EstadoInstrumentoContractual(StrEnum):
    BORRADOR = "BORRADOR"
    SELECCIONADO = "SELECCIONADO"
    FIRMADO = "FIRMADO"


class TipoCompromisoGarantia(StrEnum):
    CONTROL_NUESTRO = "CONTROL_NUESTRO"
    RESULTADO_COMPARTIDO = "RESULTADO_COMPARTIDO"
    RESULTADO_EXTERNO = "RESULTADO_EXTERNO"


class EstadoPresentacionEjecutiva(StrEnum):
    BORRADOR = "BORRADOR"
    INTERNA = "INTERNA"
    PRESENTADA = "PRESENTADA"


class SuficienciaEvaluacion(StrEnum):
    SUFICIENTE = "SUFICIENTE"
    PARCIAL = "PARCIAL"
    INSUFICIENTE = "INSUFICIENTE"
