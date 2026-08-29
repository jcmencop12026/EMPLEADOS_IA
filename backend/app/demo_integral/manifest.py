"""Manifiesto de compatibilidad para módulos aún no convergidos en esta rama."""

from __future__ import annotations

from typing import Any

from app.demo_integral.constants import DEMO_CORRELATION_ID, DEMO_OPP_CODE

COMPATIBILITY_MANIFEST: dict[str, Any] = {
    "version": "fase2-demo-1",
    "correlation_id": DEMO_CORRELATION_ID,
    "semantica": {
        "HECHO": "Evidencia verificada con fuente trazable",
        "INFERENCIA": "Proyección o aprendizaje sustentado, no hecho",
        "RECOMENDACION": "Sugerencia sujeta a aprobación humana",
    },
    "reglas_valor": [
        "POTENCIAL no es valor realizado",
        "POTENCIAL no entra al precio sugerido",
        "Correlación no implica causalidad",
    ],
    "integraciones_1330": {
        "catalogo": {"codigo": "DEMO-INT-ERP-FICTICIO", "tipo": "ERP", "estado": "HABILITADA"},
        "politica": {"nombre": "Demo solo lectura", "preflight": True},
        "ejecucion": {"modo": "SIMULADA", "correlation_id": DEMO_CORRELATION_ID},
        "linaje": {"origen": DEMO_OPP_CODE, "destino": "demo-destino-ficticio"},
        "nota": "Datos preparados; GENERAL convergerá conector real en Fase 2 central",
    },
    "gobierno_1350": {
        "clasificacion": "INTERNO",
        "retencion_dias": 365,
        "correlation_id": DEMO_CORRELATION_ID,
        "nota": "Manifiesto de compatibilidad; sin PII real",
    },
    "continuidad_1360": {
        "escenarios": [
            {"tipo": "SERVICIO_SALUDABLE", "estado": "OK"},
            {"tipo": "INCIDENTE", "codigo": "DEMO-INC-001", "estado": "RECUPERADO"},
            {"tipo": "INTEGRACION_SALUD_RECUPERADA", "estado": "SIMULADO"},
            {"tipo": "RESTORE_BLOQUEADO_PRIVACIDAD", "estado": "SIMULADO_NO_EJECUTADO"},
        ],
        "nota": "Sin operaciones destructivas; solo demostración visual futura",
    },
    "comercial_1280": {
        "plan": {
            "codigo": "DEMO-PLAN-PRO",
            "empleados_ia": 5,
            "usuarios": 25,
            "automatizaciones": 10,
            "integraciones": 3,
            "consumo_ia_tokens": 2_000_000,
            "ia_ilimitada": False,
            "credential_mode": "MANAGED",
        },
        "propuesta": {
            "codigo": "DEMO-PROP-001",
            "valor_verificado": 1_200_000,
            "valor_estimado": 800_000,
            "valor_potencial": 2_500_000,
            "potencial_en_precio": False,
            "correlation_id": DEMO_CORRELATION_ID,
        },
        "nota": "Compatible con rama comercial; seed DB al converger",
    },
    "implementacion_1310": {
        "ciclo": [
            "diagnostico",
            "configuracion",
            "implementacion",
            "adopcion",
            "medicion",
            "seguimiento",
        ],
        "estado_actual": "medicion",
        "correlation_id": DEMO_CORRELATION_ID,
        "nota": "Compatible con rama implementación; seed DB al converger",
    },
}


def get_compatibility_manifest() -> dict[str, Any]:
    return COMPATIBILITY_MANIFEST
