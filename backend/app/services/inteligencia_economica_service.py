"""Servicio — Inteligencia económica + simulación + valor empresarial EIAAX (1740).

Orquesta FinOps, Motor Económico 1600, MB-07, 1210, 1280, 1200, TCO sin duplicar motores.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.economic_motor_enums import COST_CLASSES, EconomicValueType
from app.economic_motor_models import EconomicCostEntry, EconomicValueEntry
from app.inteligencia_economica_enums import ModoDimensionamiento, TipoEscenarioComparacion
from app.inteligencia_economica_models import EconomicScenarioRun
from app.models import User
from app.orchestration_models import AIEmployee
from app.services import baseline_service as baseline_svc
from app.services import commercial_service as com_svc
from app.services import consumption_planner_service as planner_svc
from app.services import economic_motor_service as motor_svc
from app.services import finops_service as finops_svc
from app.services import tco_service as tco_svc
from app.valuation_enums import RealValueNature

POTENCIAL_NOTE = "POTENCIAL no se incorpora automáticamente al precio sugerido ni al valor realizado."


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _d(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _parse(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_run_resultados(raw: str | None) -> Any:
    """Deserializa resultados persistidos de un run de escenario."""
    return _parse(raw)


def _next_codigo(db: Session, org_id: str) -> str:
    year = _utcnow().year
    prefix = f"SIM-{year}-"
    count = (
        db.query(func.count(EconomicScenarioRun.id))
        .filter(
            EconomicScenarioRun.organization_id == org_id,
            EconomicScenarioRun.codigo.like(f"{prefix}%"),
        )
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


def auditar_capacidades_existentes() -> dict[str, Any]:
    """Inventario estático de capacidades reutilizadas — primera obligación de auditoría."""
    return {
        "finops": {
            "modulo": "950/1110",
            "ruta": "/api/finops",
            "capacidades": ["consumo", "valores", "presupuestos", "tarifas", "drill-down", "planner MB-07"],
        },
        "motor_economico": {
            "modulo": "1600",
            "ruta": "/api/motor-economico",
            "capacidades": ["costos unificados", "valores por naturaleza", "economía privada", "precio recomendado BORRADOR", "indicadores ANTES/PROYECTADO/REAL"],
            "nota": "Facade sobre FinOps — no segundo FinOps",
        },
        "valoracion": {"modulo": "1210", "ruta": "/api/valoracion", "capacidades": ["escenarios", "ROI", "valor real"]},
        "comercial": {"modulo": "1280", "ruta": "/api/comercial", "capacidades": ["propuestas", "simular", "pricing valor"]},
        "centro_negocios": {"modulo": "1700/1710", "ruta": "/api/centro-negocios", "capacidades": ["precio motor", "fases precio", "contrato"]},
        "tco": {"modulo": "1320", "ruta": "/api/tco", "capacidades": ["calcular", "desviación", "simular"]},
        "linea_base": {"modulo": "1200", "ruta": "/api/linea-base", "capacidades": ["mediciones", "impacto real"]},
        "optimizacion": {"modulo": "1290", "ruta": "/api/optimizacion", "capacidades": ["portfolio escenarios"]},
        "brechas_cerradas_1740": [
            "orquestador escenarios multi-tipo",
            "resultado económico unificado",
            "valor empresarial agregado",
            "dimensionamiento capacidad/personal",
            "economía empleado IA facade",
            "economía empresa consolidada",
            "inteligencia comercial interna",
            "pricing valor fracción configurable",
            "contratos integración GENERAL",
        ],
    }


def valor_empresarial(db: Session, org_id: str, *, period_days: int = 30) -> dict[str, Any]:
    """Rollup valor por tipo y naturaleza — POTENCIAL excluido de realizado."""
    period_end = _utcnow()
    period_start = period_end - timedelta(days=period_days)
    by_nature = motor_svc.sum_values_by_nature(db, org_id, period_start=period_start, period_end=period_end)
    rows = (
        db.query(EconomicValueEntry.value_type, EconomicValueEntry.value_nature, func.sum(EconomicValueEntry.amount))
        .filter(
            EconomicValueEntry.organization_id == org_id,
            EconomicValueEntry.created_at >= period_start,
            EconomicValueEntry.created_at <= period_end,
        )
        .group_by(EconomicValueEntry.value_type, EconomicValueEntry.value_nature)
        .all()
    )
    por_tipo: dict[str, dict[str, float]] = {}
    for vtype, nature, total in rows:
        por_tipo.setdefault(vtype, {"VERIFICADO": 0.0, "ESTIMADO": 0.0, "POTENCIAL": 0.0})
        key = (nature or "ESTIMADO").upper()
        if key in por_tipo[vtype]:
            por_tipo[vtype][key] += float(total or 0)
    return {
        "organization_id": org_id,
        "periodo_dias": period_days,
        "resumen_naturaleza": by_nature,
        "por_tipo_valor": por_tipo,
        "tipos_soportados": list(EconomicValueType.ALL),
        "nota_potencial": POTENCIAL_NOTE,
    }


def resultado_economico(db: Session, org_id: str, *, period_days: int = 30) -> dict[str, Any]:
    """Beneficio neto, ROI, payback, proyectado vs real, desviaciones."""
    period_end = _utcnow()
    period_start = period_end - timedelta(days=period_days)
    valores = motor_svc.sum_values_by_nature(db, org_id, period_start=period_start, period_end=period_end)
    costos = motor_svc.sum_costs_by_class_and_kind(db, org_id, period_start=period_start, period_end=period_end)
    finops = finops_svc.dashboard_summary(db, org_id, period_start=period_start, period_end=period_end)
    indicadores = motor_svc.build_indicators(db, org_id, period_days=period_days)

    costo_real = float(finops.get("total_cost") or 0)
    valor_realizado = float(valores.get("valor_realizado") or 0)
    costo_proyectado = float(indicadores.get("fases", {}).get("PROYECTADO", {}).get("costo_total") or 0)
    beneficio_neto = valor_realizado - costo_real
    roi = (beneficio_neto / costo_real * 100) if costo_real > 0 else None
    payback = (costo_real / (valor_realizado / 12)) if valor_realizado > 0 else None
    desviacion_costo = costo_real - costo_proyectado if costo_proyectado else None
    desviacion_pct = (desviacion_costo / costo_proyectado * 100) if costo_proyectado and desviacion_costo is not None else None

    return {
        "organization_id": org_id,
        "periodo": {"inicio": period_start.isoformat(), "fin": period_end.isoformat(), "dias": period_days},
        "beneficio_neto": round(beneficio_neto, 4),
        "roi_pct": round(roi, 2) if roi is not None else None,
        "payback_meses": round(payback, 2) if payback is not None else None,
        "costo_valor_ratio": round(costo_real / valor_realizado, 4) if valor_realizado > 0 else None,
        "proyectado": {
            "costo_total": costo_proyectado,
            "fase": indicadores.get("fases", {}).get("PROYECTADO"),
        },
        "real": {
            "costo_total": costo_real,
            "valor_realizado": valor_realizado,
            "costos_por_clase": costos,
            "finops_roi": finops.get("roi"),
        },
        "desviaciones": {
            "costo_absoluta": round(desviacion_costo, 4) if desviacion_costo is not None else None,
            "costo_pct": round(desviacion_pct, 2) if desviacion_pct is not None else None,
        },
        "separacion": {"costo": costo_real, "valor": valor_realizado, "precio": None, "margen": None},
        "nota_potencial": POTENCIAL_NOTE,
    }


def _escenario_params(base: dict[str, Any], tipo: str) -> dict[str, Any]:
    personas = int(base.get("personas", 10))
    horas = float(base.get("horas_por_persona_mes", 160))
    valor_hora = float(base.get("valor_hora", 25))
    costo_hora = float(base.get("costo_hora", 18))
    empleados_ia = int(base.get("empleados_ia", 0))
    auto_pct = float(base.get("automatizacion_pct", 0))

    if tipo == TipoEscenarioComparacion.ACTUAL:
        return {"personas": personas, "horas": horas * personas, "empleados_ia": 0, "automatizacion_pct": 0}
    if tipo == TipoEscenarioComparacion.OPTIMIZADO_SIN_IA:
        return {"personas": personas, "horas": horas * personas * 0.85, "empleados_ia": 0, "automatizacion_pct": 0.15}
    if tipo == TipoEscenarioComparacion.AUTOMATIZADO:
        return {"personas": max(1, int(personas * 0.8)), "horas": horas * personas * 0.6, "empleados_ia": 0, "automatizacion_pct": 0.4}
    if tipo == TipoEscenarioComparacion.ASISTIDO_POR_IA:
        return {"personas": personas, "horas": horas * personas * 0.7, "empleados_ia": 0, "automatizacion_pct": 0.25, "asistencia_ia": True}
    if tipo == TipoEscenarioComparacion.EMPLEADO_IA:
        return {"personas": max(1, personas - 1), "horas": horas * max(1, personas - 1), "empleados_ia": max(1, empleados_ia or 1), "automatizacion_pct": 0.35}
    if tipo == TipoEscenarioComparacion.SOLUCION_COMBINADA:
        p = int(base.get("personas_escenario") or max(1, personas - 3))
        return {
            "personas": p,
            "horas": horas * p * 0.65,
            "empleados_ia": max(1, empleados_ia or 1),
            "automatizacion_pct": max(auto_pct, 0.45),
        }
    return base


def _calcular_escenario(
    db: Session,
    org_id: str,
    tipo: str,
    params: dict[str, Any],
    *,
    valor_hora: float,
    costo_hora: float,
    days: int,
) -> dict[str, Any]:
    p = _escenario_params(params, tipo)
    personas = int(p.get("personas", 10))
    horas_totales = float(p.get("horas", 160 * personas))
    empleados_ia = int(p.get("empleados_ia", 0))
    auto_pct = float(p.get("automatizacion_pct", 0))

    costo_personas = horas_totales * costo_hora
    planner_sim = planner_svc.simulate(
        db,
        org_id,
        {
            "active_employees": max(empleados_ia, 1) if empleados_ia else 1,
            "days": days,
            "executions_per_day": 15 * (1 + auto_pct),
        },
    )
    costo_ia = float(planner_sim.get("cost_total", 0)) if empleados_ia else float(planner_sim.get("cost_total", 0)) * auto_pct * 0.3
    costo_total = costo_personas + costo_ia
    horas_ahorradas = float(params.get("personas", 10)) * float(params.get("horas_por_persona_mes", 160)) - horas_totales
    valor_generado = horas_ahorradas * valor_hora * (1 + auto_pct * 0.5)
    ahorro = valor_generado - costo_total
    roi = (ahorro / costo_total * 100) if costo_total > 0 else None
    payback = (costo_total / (valor_generado / 12)) if valor_generado > 0 else None

    return {
        "tipo": tipo,
        "personas": personas,
        "horas_totales": round(horas_totales, 2),
        "empleados_ia": empleados_ia,
        "automatizacion_pct": auto_pct,
        "capacidad_liberada_horas": round(max(0, horas_ahorradas), 2),
        "costo_personas": round(costo_personas, 2),
        "costo_ia": round(costo_ia, 2),
        "costo_total": round(costo_total, 2),
        "valor_generado_estimado": round(valor_generado, 2),
        "ahorro_neto": round(ahorro, 2),
        "roi_pct": round(roi, 2) if roi is not None else None,
        "payback_meses": round(payback, 2) if payback is not None else None,
        "riesgo": "BAJO" if auto_pct < 0.3 else "MEDIO" if auto_pct < 0.5 else "ALTO",
        "planner": {"cost_total": planner_sim.get("cost_total"), "capacity": planner_sim.get("capacity")},
    }


def comparar_escenarios(
    db: Session,
    user: User | None,
    org_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Compara escenarios ACTUAL → COMBINADO reutilizando MB-07 para costos IA."""
    tipos = params.get("escenarios") or [e.value for e in TipoEscenarioComparacion]
    days = int(params.get("days", 30))
    valor_hora = float(params.get("valor_hora", 25))
    costo_hora = float(params.get("costo_hora", 18))
    escenarios = [
        _calcular_escenario(db, org_id, t, params, valor_hora=valor_hora, costo_hora=costo_hora, days=days)
        for t in tipos
    ]
    actual = next((e for e in escenarios if e["tipo"] == TipoEscenarioComparacion.ACTUAL), escenarios[0])
    mejor = max(escenarios, key=lambda e: e.get("ahorro_neto", 0))
    resultado = {
        "organization_id": org_id,
        "params_base": params,
        "escenarios": escenarios,
        "comparacion": {
            "referencia": actual["tipo"],
            "mejor_escenario": mejor["tipo"],
            "delta_ahorro": round(mejor["ahorro_neto"] - actual["ahorro_neto"], 2),
            "delta_costo": round(mejor["costo_total"] - actual["costo_total"], 2),
        },
        "nota": "Simulación empresarial — no asume reducción obligatoria de personal",
    }
    if params.get("persistir"):
        row = EconomicScenarioRun(
            organization_id=org_id,
            codigo=_next_codigo(db, org_id),
            titulo=params.get("titulo") or "Comparación escenarios",
            scope_type=params.get("scope_type", "ORGANIZACION"),
            scope_id=params.get("scope_id"),
            params_json=_json(params),
            resultados_json=_json(resultado),
            created_by_id=user.id if user else None,
        )
        db.add(row)
        db.flush()
        resultado["run_id"] = row.id
        resultado["codigo"] = row.codigo
    return resultado


def dimensionar_capacidad(db: Session, org_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Dimensionamiento: ej. 10 personas → 7 + automatización + empleado IA."""
    personas_actual = int(params.get("personas_actual", 10))
    personas_escenario = int(params.get("personas_escenario", 7))
    empleados_ia = int(params.get("empleados_ia", 1))
    modo = params.get("modo", ModoDimensionamiento.CAPACIDAD_LIBERADA)
    horas_persona = float(params.get("horas_por_persona_mes", 160))
    auto_pct = float(params.get("automatizacion_pct", 0.35))

    horas_actuales = personas_actual * horas_persona
    horas_escenario = personas_escenario * horas_persona * (1 - auto_pct * 0.4)
    capacidad_liberada = horas_actuales - horas_escenario
    if modo == ModoDimensionamiento.CRECIMIENTO_SIN_CONTRATAR:
        interpretacion = f"Capacidad para ~{round(capacidad_liberada / horas_persona, 1)} FTE adicionales sin contratar"
    elif modo == ModoDimensionamiento.REASIGNACION:
        interpretacion = f"{round(capacidad_liberada, 0)} horas/mes disponibles para reasignación"
    elif modo == ModoDimensionamiento.REDUCCION_REPROCESOS:
        interpretacion = f"Reducción estimada de reprocesos: {round(auto_pct * 100, 0)}%"
    else:
        interpretacion = f"Capacidad liberada: {round(capacidad_liberada, 0)} horas/mes"

    sim = comparar_escenarios(
        db,
        None,
        org_id,
        {
            "personas": personas_actual,
            "personas_escenario": personas_escenario,
            "empleados_ia": empleados_ia,
            "automatizacion_pct": auto_pct,
            "horas_por_persona_mes": horas_persona,
            "escenarios": [TipoEscenarioComparacion.ACTUAL, TipoEscenarioComparacion.SOLUCION_COMBINADA],
        },
    )
    comb = next((e for e in sim["escenarios"] if e["tipo"] == TipoEscenarioComparacion.SOLUCION_COMBINADA), {})
    return {
        "organization_id": org_id,
        "situacion_actual": {"personas": personas_actual, "horas_mes": horas_actuales},
        "escenario": {
            "personas": personas_escenario,
            "empleados_ia": empleados_ia,
            "automatizacion_pct": auto_pct,
            "modo": modo,
        },
        "impacto": {
            "capacidad_liberada_horas": round(capacidad_liberada, 2),
            "interpretacion": interpretacion,
            "no_implica_despido_obligatorio": True,
        },
        "economia": comb,
    }


def economia_empleado(db: Session, org_id: str, employee_id: str, *, days: int = 30) -> dict[str, Any]:
    """Facade economía Empleado IA — reutiliza planner + motor + FinOps."""
    detail = planner_svc.employee_cost_detail(db, org_id, employee_id, days=days)
    period_end = _utcnow()
    period_start = period_end - timedelta(days=days)
    valores = (
        db.query(func.sum(EconomicValueEntry.amount))
        .filter(
            EconomicValueEntry.organization_id == org_id,
            EconomicValueEntry.employee_id == employee_id,
            EconomicValueEntry.value_nature.in_([RealValueNature.VERIFICADO, RealValueNature.ESTIMADO]),
            EconomicValueEntry.created_at >= period_start,
        )
        .scalar()
    )
    costo_real = detail["real"]["cost_total"]
    valor_gen = float(valores or 0)
    ratio = round(costo_real / valor_gen, 4) if valor_gen > 0 else None
    estimado = detail.get("estimated_monthly_single", {})
    desviacion = None
    if estimado and estimado.get("cost_total"):
        desviacion = round(costo_real - float(estimado["cost_total"]), 2)
    return {
        "employee_id": employee_id,
        "employee_name": detail.get("employee_name"),
        "periodo_dias": days,
        "costo_mensual_estimado": estimado.get("cost_total"),
        "costo_real": costo_real,
        "desviacion": desviacion,
        "consumo_ia": detail["real"].get("cost_ia"),
        "herramientas_otros": detail["real"].get("cost_other"),
        "tokens": {"in": detail["real"].get("tokens_in"), "out": detail["real"].get("tokens_out")},
        "valor_generado": valor_gen or None,
        "costo_valor_ratio": ratio,
        "utilizacion": {"ejecuciones": detail["real"].get("executions")},
    }


def economia_empresa(db: Session, org_id: str, *, period_days: int = 30) -> dict[str, Any]:
    """Presupuesto, consumo, capacidad, proyección, alertas."""
    indicadores = motor_svc.build_indicators(db, org_id, period_days=period_days)
    presupuesto = planner_svc.presupuesto_summary(db, org_id)
    capacidad = planner_svc.org_resumen(db, org_id)
    resultado = resultado_economico(db, org_id, period_days=period_days)
    alertas = []
    util = indicadores.get("fases", {}).get("PROYECTADO", {}).get("desviacion_vs_presupuesto")
    if util and util >= 90:
        alertas.append({"nivel": "ALTO", "mensaje": f"Utilización presupuesto {util}%"})
    if resultado.get("desviaciones", {}).get("costo_pct") and resultado["desviaciones"]["costo_pct"] > 15:
        alertas.append({"nivel": "MEDIO", "mensaje": "Desviación costo real vs proyectado > 15%"})
    return {
        "organization_id": org_id,
        "presupuesto": presupuesto or indicadores.get("presupuesto_ia"),
        "consumo": indicadores.get("fases", {}).get("REAL"),
        "capacidad": capacidad,
        "proyeccion": indicadores.get("fases", {}).get("PROYECTADO"),
        "resultado": resultado,
        "alertas": alertas,
    }


def inteligencia_comercial_interna(
    db: Session,
    org_id: str,
    user: User,
    *,
    proposal_id: str | None = None,
) -> dict[str, Any]:
    """Cálculo interno — NUNCA publica precio automáticamente."""
    private = motor_svc.private_economy_to_dict(motor_svc.get_private_economy(db, org_id))
    consumo = planner_svc.aggregate_real_consumption(db, org_id)
    tco_resumen = None
    if proposal_id:
        try:
            tco_resumen = tco_svc.calcular_tco(db, org_id, {"tipo": "ESTIMADO", "proposal_id": proposal_id})
        except Exception:
            tco_resumen = None
    return {
        "organization_id": org_id,
        "proposal_id": proposal_id,
        "inversion_estimada": {
            "implementacion": None,
            "ia_consumo": consumo.get("by_class", {}).get("DIRECTO"),
            "infraestructura": consumo.get("by_class", {}).get("PLATAFORMA"),
            "integraciones": consumo.get("by_class", {}).get("TRANSVERSAL_ATRIBUIBLE"),
            "soporte": private.get("support_cost") if private else None,
        },
        "economia_privada": private,
        "tco_propuesta": tco_resumen,
        "precio_sugerido": private.get("suggested_price") if private else None,
        "margen": private.get("margin") if private else None,
        "modalidad_pago": None,
        "auto_publicado": False,
        "nota": "Uso interno operador — no exponer al cliente",
    }


def recomendar_precio_valor(
    db: Session,
    user: User,
    org_id: str,
    *,
    fraccion_valor: float = 0.4,
    attributable_value: float | None = None,
    proposal_id: str | None = None,
    margen_min: float = 0.2,
) -> dict[str, Any]:
    """Pricing basado en valor — separa COSTO/PRECIO/VALOR/MARGEN. Siempre BORRADOR."""
    valores = motor_svc.sum_values_by_nature(db, org_id)
    valor_base = _d(attributable_value or valores.get("valor_realizado") or 0)
    costos = motor_svc.sum_costs_by_class_and_kind(db, org_id)
    costo_total = sum(
        v.get("REAL", 0) + v.get("ESTIMADO", 0)
        for v in costos.get("by_class", {}).values()
    )
    comercial = com_svc._compute_economics(
        valor_atribuible=valor_base,
        costo_total=_d(costo_total),
        fraccion=_d(fraccion_valor),
        margen_min=_d(margen_min),
    )
    motor_rec = motor_svc.recommend_price(
        db,
        user,
        org_id,
        scope_type="ORGANIZACION",
        scope_id=proposal_id,
        attributable_value=valor_base,
        persist=True,
    )
    return {
        "valor_atribuible": float(valor_base),
        "valor_potencial_excluido": valores.get("valor_potencial"),
        "fraccion_valor_aplicada": fraccion_valor,
        "costo_total_interno": costo_total,
        "comercial": comercial,
        "motor_recomendacion": motor_rec,
        "separacion": {
            "costo": costo_total,
            "precio_comercial": comercial.get("precio_sugerido"),
            "precio_motor": motor_rec.get("recommended_price"),
            "valor": float(valor_base),
            "margen_pct": comercial.get("margen_pct"),
        },
        "status": "BORRADOR",
        "auto_publicado": False,
        "nota_potencial": POTENCIAL_NOTE,
    }
