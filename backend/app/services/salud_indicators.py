"""Indicadores determinísticos IPS — cálculos fuera del LLM."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.services.salud_normalization import normalize_dataset

INSUFICIENTE = "Información insuficiente"


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def _safe_pct(num: float, den: float) -> float | str:
    if den == 0:
        return INSUFICIENTE
    return round((num / den) * 100, 2)


def calc_facturacion(records: list[dict[str, Any]]) -> dict[str, Any]:
    norm = normalize_dataset("facturacion", records)
    valores = [_to_float(r.get("valor_facturado")) for r in norm]
    valores_ok = [v for v in valores if v is not None]
    if not valores_ok:
        return {"disponible": False, "mensaje": INSUFICIENTE}

    por_pagador: dict[str, float] = defaultdict(float)
    por_periodo: dict[str, float] = defaultdict(float)
    for r in norm:
        v = _to_float(r.get("valor_facturado"))
        if v is None:
            continue
        pag = str(r.get("pagador", "Sin pagador"))
        por_pagador[pag] += v
        fecha = _parse_date(r.get("fecha_factura"))
        periodo = fecha.strftime("%Y-%m") if fecha else "Sin período"
        por_periodo[periodo] += v

    total = sum(valores_ok)
    sorted_pag = sorted(por_pagador.items(), key=lambda x: x[1], reverse=True)
    concentracion = round((sorted_pag[0][1] / total) * 100, 2) if sorted_pag and total else INSUFICIENTE

    return {
        "disponible": True,
        "valor_facturado": total,
        "cantidad_facturas": len(valores_ok),
        "facturacion_por_pagador": dict(sorted_pag),
        "facturacion_por_periodo": dict(sorted(por_periodo.items())),
        "concentracion_principal_pagador_pct": concentracion,
        "evidencia": {"fuente": "facturacion", "registros": len(norm)},
    }


def calc_radicacion(fact_records: list[dict], rad_records: list[dict]) -> dict[str, Any]:
    fact = normalize_dataset("facturacion", fact_records)
    rad = normalize_dataset("radicacion", rad_records)

    fact_map: dict[str, dict] = {}
    for r in fact:
        inv = str(r.get("numero_factura", ""))
        if inv:
            fact_map[inv] = r

    rad_map: dict[str, dict] = {}
    for r in rad:
        inv = str(r.get("numero_factura", ""))
        if inv:
            rad_map[inv] = r

    if not fact_map and not rad_map:
        return {"disponible": False, "mensaje": INSUFICIENTE}

    valor_facturado = sum(_to_float(r.get("valor_facturado")) or 0 for r in fact)
    valor_radicado = sum(_to_float(r.get("valor_radicado")) or 0 for r in rad)

    no_radicadas = [inv for inv in fact_map if inv not in rad_map]
    dias_radicacion: list[float] = []
    dias_por_factura: list[dict[str, Any]] = []
    for inv, rr in rad_map.items():
        ff = _parse_date(fact_map.get(inv, {}).get("fecha_factura"))
        fr = _parse_date(rr.get("fecha_radicacion"))
        if ff and fr:
            delta = (fr - ff).days
            dias_radicacion.append(delta)
            dias_por_factura.append({"numero_factura": inv, "dias": delta})

    return {
        "disponible": True,
        "valor_facturado": valor_facturado if fact_map else INSUFICIENTE,
        "valor_radicado": valor_radicado if rad_map else INSUFICIENTE,
        "diferencia_facturado_radicado": (valor_facturado - valor_radicado) if fact_map and rad_map else INSUFICIENTE,
        "facturas_no_radicadas": len(no_radicadas),
        "porcentaje_radicado": _safe_pct(valor_radicado, valor_facturado) if fact_map else INSUFICIENTE,
        "tiempo_promedio_factura_radicacion_dias": round(sum(dias_radicacion) / len(dias_radicacion), 1) if dias_radicacion else INSUFICIENTE,
        "evidencia": {"facturas": len(fact_map), "radicadas": len(rad_map), "dias_por_factura": dias_por_factura},
    }


def calc_glosas(glosa_records: list[dict], fact_records: list[dict] | None = None) -> dict[str, Any]:
    glosas = normalize_dataset("glosas", glosa_records)
    valores = [_to_float(g.get("valor_glosado")) for g in glosas]
    valores_ok = [v for v in valores if v is not None]
    if not valores_ok:
        return {"disponible": False, "mensaje": INSUFICIENTE}

    total_glosado = sum(valores_ok)
    por_causal: dict[str, float] = defaultdict(float)
    por_pagador: dict[str, float] = defaultdict(float)
    por_servicio: dict[str, float] = defaultdict(float)
    estados: dict[str, int] = defaultdict(int)

    for g in glosas:
        v = _to_float(g.get("valor_glosado")) or 0
        por_causal[str(g.get("causal", "Sin causal"))] += v
        por_pagador[str(g.get("pagador", "Sin pagador"))] += v
        por_servicio[str(g.get("servicio", "Sin servicio"))] += v
        estados[str(g.get("estado", "Sin estado"))] += 1

    base_facturado = None
    if fact_records:
        fact = calc_facturacion(fact_records)
        if fact.get("disponible"):
            base_facturado = fact["valor_facturado"]

    pct_glosa = _safe_pct(total_glosado, base_facturado) if base_facturado else INSUFICIENTE

    return {
        "disponible": True,
        "valor_glosado": total_glosado,
        "porcentaje_glosa": pct_glosa,
        "por_causal": dict(sorted(por_causal.items(), key=lambda x: x[1], reverse=True)),
        "por_pagador": dict(por_pagador),
        "por_servicio": dict(por_servicio),
        "por_estado": dict(estados),
        "evidencia": {"registros": len(glosas)},
    }


def calc_cartera(cartera_records: list[dict], pago_records: list[dict] | None = None) -> dict[str, Any]:
    cartera = normalize_dataset("cartera", cartera_records)
    saldos = [_to_float(c.get("saldo")) for c in cartera]
    saldos_ok = [s for s in saldos if s is not None]
    if not saldos_ok:
        return {"disponible": False, "mensaje": INSUFICIENTE}

    aging = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "91+": 0.0}
    por_entidad: dict[str, float] = defaultdict(float)
    dias_pago: list[float] = []

    for c in cartera:
        saldo = _to_float(c.get("saldo")) or 0
        dias = _to_float(c.get("dias_mora"))
        if dias is not None:
            if dias <= 30:
                aging["0-30"] += saldo
            elif dias <= 60:
                aging["31-60"] += saldo
            elif dias <= 90:
                aging["61-90"] += saldo
            else:
                aging["91+"] += saldo
        por_entidad[str(c.get("pagador", "Sin pagador"))] += saldo

    total_recaudo = 0.0
    if pago_records:
        pagos = normalize_dataset("pagos", pago_records)
        total_recaudo = sum(_to_float(p.get("valor_pagado")) or 0 for p in pagos)

    return {
        "disponible": True,
        "saldo_total": sum(saldos_ok),
        "aging": aging,
        "por_entidad": dict(sorted(por_entidad.items(), key=lambda x: x[1], reverse=True)),
        "recaudo": total_recaudo if pago_records else INSUFICIENTE,
        "evidencia": {"registros": len(cartera)},
    }


def calc_contratos(contrato_records: list[dict]) -> dict[str, Any]:
    contratos = normalize_dataset("contratos", contrato_records)
    if not contratos:
        return {"disponible": False, "mensaje": INSUFICIENTE}

    por_pagador: dict[str, int] = defaultdict(int)
    modalidades: dict[str, int] = defaultdict(int)
    for c in contratos:
        por_pagador[str(c.get("pagador", "Sin pagador"))] += 1
        modalidades[str(c.get("modalidad", "Sin modalidad"))] += 1

    return {
        "disponible": True,
        "cantidad_contratos": len(contratos),
        "por_pagador": dict(por_pagador),
        "por_modalidad": dict(modalidades),
        "evidencia": {"registros": len(contratos)},
    }


def calc_traceability(
    fact_records: list[dict],
    rad_records: list[dict] | None = None,
    glosa_records: list[dict] | None = None,
    conciliacion_records: list[dict] | None = None,
    cartera_records: list[dict] | None = None,
    pago_records: list[dict] | None = None,
) -> dict[str, Any]:
    """Cadena: Facturado → Radicado → Glosado → Recuperado → CxC → Pagado."""
    fact = calc_facturacion(fact_records)
    chain: dict[str, Any] = {"facturado": fact.get("valor_facturado", INSUFICIENTE)}

    if rad_records:
        rad = calc_radicacion(fact_records, rad_records)
        chain["radicado"] = rad.get("valor_radicado", INSUFICIENTE)
        chain["diferencia_facturado_radicado"] = rad.get("diferencia_facturado_radicado", INSUFICIENTE)
    else:
        chain["radicado"] = INSUFICIENTE

    if glosa_records:
        glosas = calc_glosas(glosa_records, fact_records)
        chain["glosado"] = glosas.get("valor_glosado", INSUFICIENTE)
    else:
        chain["glosado"] = INSUFICIENTE

    if conciliacion_records:
        conc = normalize_dataset("conciliacion", conciliacion_records)
        chain["recuperado_conciliado"] = sum(_to_float(c.get("valor_conciliado")) or 0 for c in conc)
    else:
        chain["recuperado_conciliado"] = INSUFICIENTE

    if cartera_records:
        car = calc_cartera(cartera_records, pago_records)
        chain["cuenta_por_cobrar"] = car.get("saldo_total", INSUFICIENTE)
    else:
        chain["cuenta_por_cobrar"] = INSUFICIENTE

    if pago_records:
        pagos = normalize_dataset("pagos", pago_records)
        chain["pagado"] = sum(_to_float(p.get("valor_pagado")) or 0 for p in pagos)
    else:
        chain["pagado"] = INSUFICIENTE

    return chain


def compute_all_indicators(datasets: dict[str, list[dict]]) -> dict[str, Any]:
    """Calcula todos los indicadores posibles con los datasets disponibles."""
    result: dict[str, Any] = {"disponibles": [], "no_disponibles": []}

    if "facturacion" in datasets:
        result["facturacion"] = calc_facturacion(datasets["facturacion"])
        if result["facturacion"].get("disponible"):
            result["disponibles"].append("facturacion")
        else:
            result["no_disponibles"].append("facturacion")
    else:
        result["facturacion"] = {"disponible": False, "mensaje": INSUFICIENTE}
        result["no_disponibles"].append("facturacion")

    if "radicacion" in datasets and "facturacion" in datasets:
        result["radicacion"] = calc_radicacion(datasets["facturacion"], datasets["radicacion"])
        if result["radicacion"].get("disponible"):
            result["disponibles"].append("radicacion")
        else:
            result["no_disponibles"].append("radicacion")
    else:
        result["radicacion"] = {"disponible": False, "mensaje": INSUFICIENTE}
        result["no_disponibles"].append("radicacion")

    if "glosas" in datasets:
        fact = datasets.get("facturacion")
        result["glosas"] = calc_glosas(datasets["glosas"], fact)
        if result["glosas"].get("disponible"):
            result["disponibles"].append("glosas")
        else:
            result["no_disponibles"].append("glosas")
    else:
        result["glosas"] = {"disponible": False, "mensaje": INSUFICIENTE}
        result["no_disponibles"].append("glosas")

    if "cartera" in datasets:
        pagos = datasets.get("pagos")
        result["cartera"] = calc_cartera(datasets["cartera"], pagos)
        if result["cartera"].get("disponible"):
            result["disponibles"].append("cartera")
        else:
            result["no_disponibles"].append("cartera")
    else:
        result["cartera"] = {"disponible": False, "mensaje": INSUFICIENTE}
        result["no_disponibles"].append("cartera")

    if "contratos" in datasets:
        result["contratos"] = calc_contratos(datasets["contratos"])
        if result["contratos"].get("disponible"):
            result["disponibles"].append("contratos")
    else:
        result["contratos"] = {"disponible": False, "mensaje": INSUFICIENTE}

    result["trazabilidad"] = calc_traceability(
        datasets.get("facturacion", []),
        datasets.get("radicacion"),
        datasets.get("glosas"),
        datasets.get("conciliacion"),
        datasets.get("cartera"),
        datasets.get("pagos"),
    )

    return result
