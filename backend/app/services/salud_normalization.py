"""Capa de normalización de campos IPS con perfiles por fuente."""

from __future__ import annotations

from typing import Any

# Perfiles de mapeo por tipo de fuente (extensible, no hardcode único)
FIELD_PROFILES: dict[str, dict[str, list[str]]] = {
    "facturacion": {
        "fecha_factura": ["fecha_factura", "Fecha Factura", "fec_fact", "invoice_date", "fecha"],
        "numero_factura": ["numero_factura", "Nro Factura", "num_fact", "invoice_number", "factura"],
        "valor_facturado": ["valor_facturado", "Valor Facturado", "valor", "amount", "total"],
        "pagador": ["pagador", "Pagador", "entidad", "eps", "payer"],
        "contrato": ["contrato", "Contrato", "contract_id"],
    },
    "radicacion": {
        "fecha_factura": ["fecha_factura", "Fecha Factura", "fec_fact"],
        "fecha_radicacion": ["fecha_radicacion", "Fecha Radicación", "fec_radic", "submission_date"],
        "numero_factura": ["numero_factura", "Nro Factura", "num_fact"],
        "valor_radicado": ["valor_radicado", "Valor Radicado", "valor", "amount"],
        "pagador": ["pagador", "Pagador", "entidad", "eps"],
    },
    "glosas": {
        "numero_factura": ["numero_factura", "Nro Factura", "num_fact"],
        "valor_glosado": ["valor_glosado", "Valor Glosa", "valor", "amount"],
        "causal": ["causal", "Causal", "codigo_causal", "reason_code"],
        "pagador": ["pagador", "Pagador", "entidad"],
        "servicio": ["servicio", "Servicio", "service"],
        "estado": ["estado", "Estado", "status"],
        "fecha_glosa": ["fecha_glosa", "Fecha Glosa", "date"],
    },
    "cartera": {
        "numero_factura": ["numero_factura", "Nro Factura"],
        "saldo": ["saldo", "Saldo", "balance", "amount_due"],
        "fecha_vencimiento": ["fecha_vencimiento", "Fecha Vencimiento", "due_date"],
        "pagador": ["pagador", "Pagador", "entidad"],
        "dias_mora": ["dias_mora", "Días Mora", "days_overdue"],
    },
    "pagos": {
        "numero_factura": ["numero_factura", "Nro Factura"],
        "valor_pagado": ["valor_pagado", "Valor Pagado", "amount_paid", "valor"],
        "fecha_pago": ["fecha_pago", "Fecha Pago", "payment_date"],
        "pagador": ["pagador", "Pagador", "entidad"],
    },
    "contratos": {
        "contrato": ["contrato", "Contrato", "contract_id"],
        "pagador": ["pagador", "Pagador", "entidad"],
        "modalidad": ["modalidad", "Modalidad", "modality"],
        "tarifa": ["tarifa", "Tarifa", "rate"],
        "vigencia_inicio": ["vigencia_inicio", "Inicio Vigencia", "start_date"],
        "vigencia_fin": ["vigencia_fin", "Fin Vigencia", "end_date"],
    },
    "conciliacion": {
        "numero_factura": ["numero_factura", "Nro Factura"],
        "valor_conciliado": ["valor_conciliado", "Valor Conciliado", "amount"],
        "fecha_conciliacion": ["fecha_conciliacion", "Fecha Conciliación"],
    },
    "respuestas_glosa": {
        "numero_factura": ["numero_factura", "Nro Factura"],
        "respuesta": ["respuesta", "Respuesta", "response"],
        "valor_recuperado": ["valor_recuperado", "Valor Recuperado", "recovered"],
        "estado": ["estado", "Estado"],
    },
    "devoluciones": {
        "numero_factura": ["numero_factura", "Nro Factura"],
        "valor_devuelto": ["valor_devuelto", "Valor Devuelto", "amount"],
        "motivo": ["motivo", "Motivo", "reason"],
        "pagador": ["pagador", "Pagador", "entidad"],
        "fecha_devolucion": ["fecha_devolucion", "Fecha Devolución", "date"],
    },
}


def _find_canonical_key(source_type: str, raw_key: str) -> str | None:
    profile = FIELD_PROFILES.get(source_type, {})
    raw_lower = raw_key.strip().lower()
    for canonical, aliases in profile.items():
        if raw_lower == canonical.lower():
            return canonical
        for alias in aliases:
            if raw_lower == alias.strip().lower():
                return canonical
    return None


def normalize_record(source_type: str, record: dict[str, Any], profile_code: str | None = None) -> dict[str, Any]:
    """Mapea variaciones de campos a conceptos canónicos."""
    profile = FIELD_PROFILES.get(source_type, {})
    if profile_code and profile_code in FIELD_PROFILES:
        profile = FIELD_PROFILES[profile_code]

    normalized: dict[str, Any] = {}
    unmapped: dict[str, Any] = {}

    for key, value in record.items():
        canonical = _find_canonical_key(source_type, key)
        if canonical:
            normalized[canonical] = value
        else:
            unmapped[key] = value

    if unmapped:
        normalized["_sin_mapear"] = unmapped
    return normalized


def normalize_dataset(source_type: str, records: list[dict[str, Any]], profile_code: str | None = None) -> list[dict[str, Any]]:
    return [normalize_record(source_type, r, profile_code) for r in records]


def profile_data_quality(source_type: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Perfilado de datos antes del análisis."""
    profile = FIELD_PROFILES.get(source_type, {})
    expected_fields = list(profile.keys())

    if not records:
        return {
            "fuente": source_type,
            "registros": 0,
            "campos_disponibles": [],
            "campos_faltantes": expected_fields,
            "fechas": {"minima": None, "maxima": None},
            "duplicados": 0,
            "nulos_por_campo": {},
            "inconsistencias": ["Sin registros"],
            "nivel_calidad": "INSUFICIENTE",
        }

    available: set[str] = set()
    nulls: dict[str, int] = {f: 0 for f in expected_fields}
    dates: list[str] = []
    keys_seen: list[str] = []
    inconsistencies: list[str] = []

    for rec in records:
        norm = normalize_record(source_type, rec)
        for f in expected_fields:
            if f in norm and norm[f] is not None and str(norm[f]).strip() != "":
                available.add(f)
            else:
                nulls[f] += 1
        for date_field in ("fecha_factura", "fecha_radicacion", "fecha_glosa", "fecha_pago", "fecha_vencimiento"):
            if date_field in norm and norm[date_field]:
                dates.append(str(norm[date_field]))
        inv_key = str(norm.get("numero_factura", ""))
        if inv_key:
            keys_seen.append(inv_key)

    duplicates = len(keys_seen) - len(set(keys_seen)) if keys_seen else 0
    missing = [f for f in expected_fields if f not in available]

    if duplicates > 0:
        inconsistencies.append(f"{duplicates} registros duplicados por número de factura")

    total_nulls = sum(nulls.values())
    total_cells = len(records) * max(len(expected_fields), 1)
    completeness = 1 - (total_nulls / total_cells) if total_cells else 0

    if completeness >= 0.85:
        quality = "ALTA"
    elif completeness >= 0.6:
        quality = "MEDIA"
    elif completeness >= 0.3:
        quality = "BAJA"
    else:
        quality = "INSUFICIENTE"

    return {
        "fuente": source_type,
        "registros": len(records),
        "campos_disponibles": sorted(available),
        "campos_faltantes": missing,
        "fechas": {
            "minima": min(dates) if dates else None,
            "maxima": max(dates) if dates else None,
        },
        "duplicados": duplicates,
        "nulos_por_campo": {k: v for k, v in nulls.items() if v > 0},
        "inconsistencias": inconsistencies,
        "completitud": round(completeness, 3),
        "nivel_calidad": quality,
    }
