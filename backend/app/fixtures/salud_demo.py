"""Dataset de demostración IPS — datos ficticios sin PII."""

from __future__ import annotations


def get_demo_datasets() -> dict[str, list[dict]]:
    return {
        "facturacion": [
            {"fecha_factura": "2026-01-05", "numero_factura": "F-1001", "valor_facturado": 45000000, "pagador": "EPS Alfa", "contrato": "C-001"},
            {"fecha_factura": "2026-01-12", "numero_factura": "F-1002", "valor_facturado": 32000000, "pagador": "EPS Alfa", "contrato": "C-001"},
            {"fecha_factura": "2026-01-18", "numero_factura": "F-1003", "valor_facturado": 28000000, "pagador": "EPS Beta", "contrato": "C-002"},
            {"fecha_factura": "2026-02-03", "numero_factura": "F-1004", "valor_facturado": 51000000, "pagador": "EPS Alfa", "contrato": "C-001"},
            {"fecha_factura": "2026-02-10", "numero_factura": "F-1005", "valor_facturado": 19000000, "pagador": "EPS Gamma", "contrato": "C-003"},
            {"fecha_factura": "2026-02-15", "numero_factura": "F-1006", "valor_facturado": 38000000, "pagador": "EPS Alfa", "contrato": "C-001"},
            {"fecha_factura": "2026-02-20", "numero_factura": "F-1007", "valor_facturado": 22000000, "pagador": "EPS Beta", "contrato": "C-002"},
            {"fecha_factura": "2026-03-01", "numero_factura": "F-1008", "valor_facturado": 41000000, "pagador": "EPS Alfa", "contrato": "C-001"},
        ],
        "radicacion": [
            {"fecha_factura": "2026-01-05", "fecha_radicacion": "2026-01-20", "numero_factura": "F-1001", "valor_radicado": 45000000, "pagador": "EPS Alfa"},
            {"fecha_factura": "2026-01-12", "fecha_radicacion": "2026-01-25", "numero_factura": "F-1002", "valor_radicado": 32000000, "pagador": "EPS Alfa"},
            {"fecha_factura": "2026-01-18", "fecha_radicacion": "2026-02-05", "numero_factura": "F-1003", "valor_radicado": 28000000, "pagador": "EPS Beta"},
            {"fecha_factura": "2026-02-03", "fecha_radicacion": "2026-02-18", "numero_factura": "F-1004", "valor_radicado": 51000000, "pagador": "EPS Alfa"},
            {"fecha_factura": "2026-02-10", "fecha_radicacion": "2026-02-28", "numero_factura": "F-1005", "valor_radicado": 19000000, "pagador": "EPS Gamma"},
            {"fecha_factura": "2026-02-20", "fecha_radicacion": "2026-03-08", "numero_factura": "F-1007", "valor_radicado": 22000000, "pagador": "EPS Beta"},
        ],
        "glosas": [
            {"numero_factura": "F-1001", "valor_glosado": 4500000, "causal": "G01", "pagador": "EPS Alfa", "servicio": "Consulta", "estado": "NOTIFICADA"},
            {"numero_factura": "F-1002", "valor_glosado": 1600000, "causal": "G03", "pagador": "EPS Alfa", "servicio": "Procedimiento", "estado": "RESPONDIDA"},
            {"numero_factura": "F-1004", "valor_glosado": 8200000, "causal": "G01", "pagador": "EPS Alfa", "servicio": "Hospitalización", "estado": "NOTIFICADA"},
            {"numero_factura": "F-1003", "valor_glosado": 1400000, "causal": "G05", "pagador": "EPS Beta", "servicio": "Imagenología", "estado": "ACEPTADA"},
        ],
        "cartera": [
            {"numero_factura": "F-1001", "saldo": 12000000, "fecha_vencimiento": "2026-03-15", "pagador": "EPS Alfa", "dias_mora": 25},
            {"numero_factura": "F-1004", "saldo": 28000000, "fecha_vencimiento": "2026-02-28", "pagador": "EPS Alfa", "dias_mora": 45},
            {"numero_factura": "F-1006", "saldo": 38000000, "fecha_vencimiento": "2026-01-30", "pagador": "EPS Alfa", "dias_mora": 95},
            {"numero_factura": "F-1008", "saldo": 41000000, "fecha_vencimiento": "2026-04-01", "pagador": "EPS Alfa", "dias_mora": 5},
        ],
        "pagos": [
            {"numero_factura": "F-1002", "valor_pagado": 30400000, "fecha_pago": "2026-02-20", "pagador": "EPS Alfa"},
            {"numero_factura": "F-1005", "valor_pagado": 19000000, "fecha_pago": "2026-03-10", "pagador": "EPS Gamma"},
            {"numero_factura": "F-1007", "valor_pagado": 22000000, "fecha_pago": "2026-03-15", "pagador": "EPS Beta"},
        ],
        "contratos": [
            {"contrato": "C-001", "pagador": "EPS Alfa", "modalidad": "Evento", "tarifa": "Tabla SOAT", "vigencia_inicio": "2025-01-01", "vigencia_fin": "2026-12-31"},
            {"contrato": "C-002", "pagador": "EPS Beta", "modalidad": "Capitación", "tarifa": "PGP", "vigencia_inicio": "2025-06-01", "vigencia_fin": "2026-05-31"},
            {"contrato": "C-003", "pagador": "EPS Gamma", "modalidad": "Evento", "tarifa": "Negociada", "vigencia_inicio": "2025-03-01", "vigencia_fin": "2026-02-28"},
        ],
        "conciliacion": [
            {"numero_factura": "F-1002", "valor_conciliado": 1600000, "fecha_conciliacion": "2026-03-01"},
            {"numero_factura": "F-1003", "valor_conciliado": 1400000, "fecha_conciliacion": "2026-02-15"},
        ],
    }
