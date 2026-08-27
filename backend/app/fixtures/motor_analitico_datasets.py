"""Datasets adversariales MOTOR-ANALITICO-1000 — patrones distintos por caso."""

from __future__ import annotations

from typing import Any


def get_motor_dataset(case_id: str) -> dict[str, list[dict[str, Any]]]:
    builders = {
        "A": _case_a_radicacion_tardia,
        "B": _case_b_glosas_devoluciones,
        "C": _case_c_pagador_tardio,
        "D": _case_d_combinado,
        "E": _case_e_insuficiente,
        "CONSULTOR": _case_consultor,
    }
    builder = builders.get(case_id.upper())
    if not builder:
        raise ValueError(f"Caso desconocido: {case_id}")
    return builder()


def list_motor_cases() -> list[dict[str, str]]:
    return [
        {"id": "A", "nombre": "Cartera por radicación tardía", "problema": "Demora interna factura→radicación"},
        {"id": "B", "nombre": "Cartera por glosas y devoluciones", "problema": "Objeciones y devoluciones del pagador"},
        {"id": "C", "nombre": "Pagador con comportamiento tardío", "problema": "Proceso interno sólido, mora del pagador"},
        {"id": "D", "nombre": "Problema combinado", "problema": "Radicación + glosas + concentración"},
        {"id": "E", "nombre": "Datos insuficientes", "problema": "No permite causalidad confiable"},
        {"id": "CONSULTOR", "nombre": "Caso consultor comercial", "problema": "Demo rica para IPS"},
    ]


def get_case_request(case_id: str) -> str:
    requests = {
        "A": "¿Por qué aumentó mi cartera? Analiza si la radicación está afectando el recaudo.",
        "B": "Analiza cartera elevada por glosas, devoluciones y respuestas pendientes.",
        "C": "Tenemos buen proceso de radicación pero la cartera sigue alta. ¿Es comportamiento del pagador?",
        "D": "Diagnóstico integral: cartera, radicación, glosas y concentración de pagadores.",
        "E": "¿Por qué aumentó mi cartera?",
        "CONSULTOR": (
            "Necesito un diagnóstico ejecutivo: qué está ocurriendo, por qué, cuánto vale "
            "y qué debemos hacer primero para recuperar flujo de caja."
        ),
    }
    return requests.get(case_id.upper(), requests["CONSULTOR"])


def _case_a_radicacion_tardia() -> dict[str, list[dict]]:
    """Cartera explicada por radicación tardía; glosas bajas; pagos normales post-radicación."""
    return {
        "facturacion": [
            {"fecha_factura": "2025-10-01", "numero_factura": "A-001", "valor_facturado": 80000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2025-10-15", "numero_factura": "A-002", "valor_facturado": 65000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2025-11-01", "numero_factura": "A-003", "valor_facturado": 72000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2025-11-20", "numero_factura": "A-004", "valor_facturado": 90000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2025-12-05", "numero_factura": "A-005", "valor_facturado": 55000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2025-12-20", "numero_factura": "A-006", "valor_facturado": 48000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2026-01-10", "numero_factura": "A-007", "valor_facturado": 62000000, "pagador": "EPS Norte", "contrato": "CN-01"},
            {"fecha_factura": "2026-02-01", "numero_factura": "A-008", "valor_facturado": 70000000, "pagador": "EPS Norte", "contrato": "CN-01"},
        ],
        "radicacion": [
            {"fecha_factura": "2025-10-01", "fecha_radicacion": "2025-10-28", "numero_factura": "A-001", "valor_radicado": 80000000, "pagador": "EPS Norte"},
            {"fecha_factura": "2025-10-15", "fecha_radicacion": "2025-11-18", "numero_factura": "A-002", "valor_radicado": 65000000, "pagador": "EPS Norte"},
            {"fecha_factura": "2025-11-01", "fecha_radicacion": "2025-12-05", "numero_factura": "A-003", "valor_radicado": 72000000, "pagador": "EPS Norte"},
            {"fecha_factura": "2025-11-20", "fecha_radicacion": "2025-12-30", "numero_factura": "A-004", "valor_radicado": 90000000, "pagador": "EPS Norte"},
            {"fecha_factura": "2025-12-05", "fecha_radicacion": "2026-01-22", "numero_factura": "A-005", "valor_radicado": 55000000, "pagador": "EPS Norte"},
        ],
        "glosas": [
            {"numero_factura": "A-001", "valor_glosado": 1200000, "causal": "G02", "pagador": "EPS Norte", "servicio": "Consulta", "estado": "RESPONDIDA"},
            {"numero_factura": "A-003", "valor_glosado": 900000, "causal": "G04", "pagador": "EPS Norte", "servicio": "Procedimiento", "estado": "ACEPTADA"},
        ],
        "cartera": [
            {"numero_factura": "A-006", "saldo": 48000000, "fecha_vencimiento": "2026-02-15", "pagador": "EPS Norte", "dias_mora": 35},
            {"numero_factura": "A-007", "saldo": 62000000, "fecha_vencimiento": "2026-03-01", "pagador": "EPS Norte", "dias_mora": 20},
            {"numero_factura": "A-008", "saldo": 70000000, "fecha_vencimiento": "2026-03-20", "pagador": "EPS Norte", "dias_mora": 5},
            {"numero_factura": "A-005", "saldo": 22000000, "fecha_vencimiento": "2026-02-28", "pagador": "EPS Norte", "dias_mora": 42},
        ],
        "pagos": [
            {"numero_factura": "A-001", "valor_pagado": 78800000, "fecha_pago": "2025-12-10", "pagador": "EPS Norte"},
            {"numero_factura": "A-002", "valor_pagado": 65000000, "fecha_pago": "2025-12-20", "pagador": "EPS Norte"},
            {"numero_factura": "A-003", "valor_pagado": 71100000, "fecha_pago": "2026-01-15", "pagador": "EPS Norte"},
        ],
        "contratos": [
            {"contrato": "CN-01", "pagador": "EPS Norte", "modalidad": "Evento", "tarifa": "SOAT", "vigencia_inicio": "2025-01-01", "vigencia_fin": "2026-12-31"},
        ],
    }


def _case_b_glosas_devoluciones() -> dict[str, list[dict]]:
    """Cartera por glosas altas y devoluciones; radicación ágil."""
    return {
        "facturacion": [
            {"fecha_factura": "2025-11-01", "numero_factura": "B-101", "valor_facturado": 120000000, "pagador": "EPS Andina", "contrato": "CB-01"},
            {"fecha_factura": "2025-11-15", "numero_factura": "B-102", "valor_facturado": 95000000, "pagador": "EPS Andina", "contrato": "CB-01"},
            {"fecha_factura": "2025-12-01", "numero_factura": "B-103", "valor_facturado": 110000000, "pagador": "EPS Andina", "contrato": "CB-01"},
            {"fecha_factura": "2025-12-15", "numero_factura": "B-104", "valor_facturado": 88000000, "pagador": "EPS Pacífico", "contrato": "CB-02"},
            {"fecha_factura": "2026-01-05", "numero_factura": "B-105", "valor_facturado": 102000000, "pagador": "EPS Andina", "contrato": "CB-01"},
            {"fecha_factura": "2026-01-20", "numero_factura": "B-106", "valor_facturado": 76000000, "pagador": "EPS Pacífico", "contrato": "CB-02"},
        ],
        "radicacion": [
            {"fecha_factura": "2025-11-01", "fecha_radicacion": "2025-11-05", "numero_factura": "B-101", "valor_radicado": 120000000, "pagador": "EPS Andina"},
            {"fecha_factura": "2025-11-15", "fecha_radicacion": "2025-11-19", "numero_factura": "B-102", "valor_radicado": 95000000, "pagador": "EPS Andina"},
            {"fecha_factura": "2025-12-01", "fecha_radicacion": "2025-12-04", "numero_factura": "B-103", "valor_radicado": 110000000, "pagador": "EPS Andina"},
            {"fecha_factura": "2025-12-15", "fecha_radicacion": "2025-12-18", "numero_factura": "B-104", "valor_radicado": 88000000, "pagador": "EPS Pacífico"},
            {"fecha_factura": "2026-01-05", "fecha_radicacion": "2026-01-08", "numero_factura": "B-105", "valor_radicado": 102000000, "pagador": "EPS Andina"},
            {"fecha_factura": "2026-01-20", "fecha_radicacion": "2026-01-23", "numero_factura": "B-106", "valor_radicado": 76000000, "pagador": "EPS Pacífico"},
        ],
        "glosas": [
            {"numero_factura": "B-101", "valor_glosado": 28000000, "causal": "G01", "pagador": "EPS Andina", "servicio": "Hospitalización", "estado": "NOTIFICADA"},
            {"numero_factura": "B-102", "valor_glosado": 19000000, "causal": "G01", "pagador": "EPS Andina", "servicio": "UCI", "estado": "DEVUELTA"},
            {"numero_factura": "B-103", "valor_glosado": 22000000, "causal": "G03", "pagador": "EPS Andina", "servicio": "Procedimiento", "estado": "NOTIFICADA"},
            {"numero_factura": "B-104", "valor_glosado": 15000000, "causal": "G05", "pagador": "EPS Pacífico", "servicio": "Imagenología", "estado": "DEVUELTA"},
            {"numero_factura": "B-105", "valor_glosado": 24000000, "causal": "G01", "pagador": "EPS Andina", "servicio": "Hospitalización", "estado": "NOTIFICADA"},
        ],
        "devoluciones": [
            {"numero_factura": "B-102", "valor_devuelto": 19000000, "motivo": "Soporte incompleto", "pagador": "EPS Andina", "fecha_devolucion": "2025-12-10"},
            {"numero_factura": "B-104", "valor_devuelto": 15000000, "motivo": "RIPS inconsistente", "pagador": "EPS Pacífico", "fecha_devolucion": "2026-01-05"},
        ],
        "cartera": [
            {"numero_factura": "B-101", "saldo": 92000000, "fecha_vencimiento": "2026-02-01", "pagador": "EPS Andina", "dias_mora": 55},
            {"numero_factura": "B-103", "saldo": 88000000, "fecha_vencimiento": "2026-02-15", "pagador": "EPS Andina", "dias_mora": 40},
            {"numero_factura": "B-105", "saldo": 78000000, "fecha_vencimiento": "2026-03-01", "pagador": "EPS Andina", "dias_mora": 25},
        ],
        "pagos": [
            {"numero_factura": "B-106", "valor_pagado": 61000000, "fecha_pago": "2026-02-28", "pagador": "EPS Pacífico"},
        ],
        "contratos": [
            {"contrato": "CB-01", "pagador": "EPS Andina", "modalidad": "Evento", "tarifa": "Negociada", "vigencia_inicio": "2025-01-01", "vigencia_fin": "2026-12-31"},
            {"contrato": "CB-02", "pagador": "EPS Pacífico", "modalidad": "Evento", "tarifa": "SOAT", "vigencia_inicio": "2025-06-01", "vigencia_fin": "2026-05-31"},
        ],
    }


def _case_c_pagador_tardio() -> dict[str, list[dict]]:
    """Radicación excelente y glosas bajas; mora por pagador lento."""
    return {
        "facturacion": [
            {"fecha_factura": "2025-09-01", "numero_factura": "C-201", "valor_facturado": 50000000, "pagador": "EPS Lenta", "contrato": "CC-01"},
            {"fecha_factura": "2025-10-01", "numero_factura": "C-202", "valor_facturado": 48000000, "pagador": "EPS Lenta", "contrato": "CC-01"},
            {"fecha_factura": "2025-11-01", "numero_factura": "C-203", "valor_facturado": 52000000, "pagador": "EPS Lenta", "contrato": "CC-01"},
            {"fecha_factura": "2025-12-01", "numero_factura": "C-204", "valor_facturado": 55000000, "pagador": "EPS Lenta", "contrato": "CC-01"},
            {"fecha_factura": "2026-01-01", "numero_factura": "C-205", "valor_facturado": 51000000, "pagador": "EPS Lenta", "contrato": "CC-01"},
            {"fecha_factura": "2026-02-01", "numero_factura": "C-206", "valor_facturado": 49000000, "pagador": "EPS Lenta", "contrato": "CC-01"},
        ],
        "radicacion": [
            {"fecha_factura": "2025-09-01", "fecha_radicacion": "2025-09-03", "numero_factura": "C-201", "valor_radicado": 50000000, "pagador": "EPS Lenta"},
            {"fecha_factura": "2025-10-01", "fecha_radicacion": "2025-10-02", "numero_factura": "C-202", "valor_radicado": 48000000, "pagador": "EPS Lenta"},
            {"fecha_factura": "2025-11-01", "fecha_radicacion": "2025-11-03", "numero_factura": "C-203", "valor_radicado": 52000000, "pagador": "EPS Lenta"},
            {"fecha_factura": "2025-12-01", "fecha_radicacion": "2025-12-02", "numero_factura": "C-204", "valor_radicado": 55000000, "pagador": "EPS Lenta"},
            {"fecha_factura": "2026-01-01", "fecha_radicacion": "2026-01-03", "numero_factura": "C-205", "valor_radicado": 51000000, "pagador": "EPS Lenta"},
            {"fecha_factura": "2026-02-01", "fecha_radicacion": "2026-02-03", "numero_factura": "C-206", "valor_radicado": 49000000, "pagador": "EPS Lenta"},
        ],
        "glosas": [
            {"numero_factura": "C-201", "valor_glosado": 500000, "causal": "G02", "pagador": "EPS Lenta", "servicio": "Consulta", "estado": "ACEPTADA"},
        ],
        "cartera": [
            {"numero_factura": "C-201", "saldo": 49500000, "fecha_vencimiento": "2025-11-01", "pagador": "EPS Lenta", "dias_mora": 120},
            {"numero_factura": "C-202", "saldo": 48000000, "fecha_vencimiento": "2025-12-01", "pagador": "EPS Lenta", "dias_mora": 95},
            {"numero_factura": "C-203", "saldo": 52000000, "fecha_vencimiento": "2026-01-01", "pagador": "EPS Lenta", "dias_mora": 65},
            {"numero_factura": "C-204", "saldo": 55000000, "fecha_vencimiento": "2026-02-01", "pagador": "EPS Lenta", "dias_mora": 35},
            {"numero_factura": "C-205", "saldo": 51000000, "fecha_vencimiento": "2026-03-01", "pagador": "EPS Lenta", "dias_mora": 10},
        ],
        "pagos": [
            {"numero_factura": "C-206", "valor_pagado": 49000000, "fecha_pago": "2026-03-10", "pagador": "EPS Lenta"},
        ],
        "contratos": [
            {"contrato": "CC-01", "pagador": "EPS Lenta", "modalidad": "Evento", "tarifa": "PGP", "vigencia_inicio": "2025-01-01", "vigencia_fin": "2026-12-31"},
        ],
    }


def _case_d_combinado() -> dict[str, list[dict]]:
    """Radicación tardía + glosas altas + concentración en un pagador."""
    return {
        "facturacion": [
            {"fecha_factura": "2025-10-01", "numero_factura": "D-301", "valor_facturado": 200000000, "pagador": "EPS Mega", "contrato": "CD-01"},
            {"fecha_factura": "2025-10-20", "numero_factura": "D-302", "valor_facturado": 180000000, "pagador": "EPS Mega", "contrato": "CD-01"},
            {"fecha_factura": "2025-11-10", "numero_factura": "D-303", "valor_facturado": 15000000, "pagador": "EPS Menor", "contrato": "CD-02"},
            {"fecha_factura": "2025-12-01", "numero_factura": "D-304", "valor_facturado": 220000000, "pagador": "EPS Mega", "contrato": "CD-01"},
            {"fecha_factura": "2026-01-15", "numero_factura": "D-305", "valor_facturado": 12000000, "pagador": "EPS Menor", "contrato": "CD-02"},
        ],
        "radicacion": [
            {"fecha_factura": "2025-10-01", "fecha_radicacion": "2025-11-05", "numero_factura": "D-301", "valor_radicado": 200000000, "pagador": "EPS Mega"},
            {"fecha_factura": "2025-10-20", "fecha_radicacion": "2025-11-28", "numero_factura": "D-302", "valor_radicado": 180000000, "pagador": "EPS Mega"},
            {"fecha_factura": "2025-11-10", "fecha_radicacion": "2025-11-14", "numero_factura": "D-303", "valor_radicado": 15000000, "pagador": "EPS Menor"},
        ],
        "glosas": [
            {"numero_factura": "D-301", "valor_glosado": 45000000, "causal": "G01", "pagador": "EPS Mega", "servicio": "Hospitalización", "estado": "NOTIFICADA"},
            {"numero_factura": "D-302", "valor_glosado": 38000000, "causal": "G03", "pagador": "EPS Mega", "servicio": "UCI", "estado": "NOTIFICADA"},
            {"numero_factura": "D-304", "valor_glosado": 52000000, "causal": "G01", "pagador": "EPS Mega", "servicio": "Hospitalización", "estado": "NOTIFICADA"},
        ],
        "cartera": [
            {"numero_factura": "D-304", "saldo": 168000000, "fecha_vencimiento": "2026-02-01", "pagador": "EPS Mega", "dias_mora": 50},
            {"numero_factura": "D-301", "saldo": 155000000, "fecha_vencimiento": "2026-01-15", "pagador": "EPS Mega", "dias_mora": 70},
            {"numero_factura": "D-302", "saldo": 142000000, "fecha_vencimiento": "2026-01-30", "pagador": "EPS Mega", "dias_mora": 55},
        ],
        "pagos": [
            {"numero_factura": "D-303", "valor_pagado": 15000000, "fecha_pago": "2025-12-20", "pagador": "EPS Menor"},
        ],
        "contratos": [
            {"contrato": "CD-01", "pagador": "EPS Mega", "modalidad": "Evento", "tarifa": "Negociada", "vigencia_inicio": "2025-01-01", "vigencia_fin": "2026-12-31"},
            {"contrato": "CD-02", "pagador": "EPS Menor", "modalidad": "Capitación", "tarifa": "PGP", "vigencia_inicio": "2025-06-01", "vigencia_fin": "2026-05-31"},
        ],
    }


def _case_e_insuficiente() -> dict[str, list[dict]]:
    """Solo facturación mínima — no permite diagnóstico causal."""
    return {
        "facturacion": [
            {"fecha_factura": "2026-01-01", "numero_factura": "E-001", "valor_facturado": 10000000, "pagador": "EPS X"},
            {"numero_factura": "E-002", "valor_facturado": 8000000},
        ],
    }


def _case_consultor() -> dict[str, list[dict]]:
    """Dataset rico para demo comercial — combina señales accionables sin hardcode."""
    base = _case_d_combinado()
    # Enriquecer con pagos parciales, conciliación y respuestas glosa
    base["pagos"] = base.get("pagos", []) + [
        {"numero_factura": "D-301", "valor_pagado": 45000000, "fecha_pago": "2026-02-15", "pagador": "EPS Mega"},
    ]
    base["conciliacion"] = [
        {"numero_factura": "D-302", "valor_conciliado": 8000000, "fecha_conciliacion": "2026-02-01"},
    ]
    base["respuestas_glosa"] = [
        {"numero_factura": "D-301", "respuesta": "Sustentación técnica", "valor_recuperado": 12000000, "estado": "PARCIAL"},
    ]
    return base
