"""Servicio — Optimización, priorización avanzada y recomendaciones (Bloque 1290)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from typing import Any

from sqlalchemy.orm import Session

from app.learning_models import CicloAprendizaje, PatronAprendizaje
from app.models import User
from app.opportunity_models import Opportunity
from app.optimization_models import (
    OptimizacionAuditoria,
    OptimizacionConfiguracion,
    OptimizacionItem,
    OptimizacionRecomendacion,
)
from app.valuation_models import OpportunityValuation, OpportunityValuationExpected

MAX_PORTFOLIO_CANDIDATES = 20
MAX_SUBSET_ENUM = 18

_URGENCIA = {"BAJA": 0.25, "MEDIA": 0.5, "ALTA": 0.75, "CRITICA": 1.0}
_RIESGO = {"BAJO": 0.2, "MEDIO": 0.5, "ALTO": 0.8, "CRITICO": 1.0}

PESOS_OBJETIVO: dict[str, dict[str, float]] = {
    "MAXIMIZAR_VALOR": {"valor": 0.45, "impacto": 0.15, "urgencia": 0.1, "confianza": 0.15, "riesgo": -0.1, "costo": -0.05},
    "MAXIMIZAR_ROI": {"valor": 0.35, "impacto": 0.1, "urgencia": 0.05, "confianza": 0.15, "riesgo": -0.1, "costo": -0.25},
    "MAXIMIZAR_IMPACTO": {"valor": 0.15, "impacto": 0.45, "urgencia": 0.15, "confianza": 0.1, "riesgo": -0.1, "costo": -0.05},
    "MINIMIZAR_RIESGO": {"valor": 0.1, "impacto": 0.1, "urgencia": 0.1, "confianza": 0.25, "riesgo": -0.4, "costo": -0.05},
    "RESULTADO_EQUILIBRADO": {"valor": 0.25, "impacto": 0.2, "urgencia": 0.15, "confianza": 0.15, "riesgo": -0.15, "costo": -0.1},
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _json_load(raw: str | None) -> Any:
    if not raw:
        return None
    return json.loads(raw)


def _float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    return float(v)


@dataclass
class Restricciones:
    presupuesto_maximo: float | None = None
    tiempo_maximo_dias: float | None = None
    capacidad_operativa: int | None = None
    max_iniciativas: int | None = None
    riesgo_maximo: float | None = None
    obligatorias: list[str] = field(default_factory=list)
    excluidas: list[str] = field(default_factory=list)
    requiere: list[tuple[str, str]] = field(default_factory=list)  # (dependiente, prerequisito)
    incompatibles: list[tuple[str, str]] = field(default_factory=list)
    orden_previo: list[tuple[str, str]] = field(default_factory=list)  # (antes, despues)

    @classmethod
    def from_dict(cls, data: dict | None) -> Restricciones:
        if not data:
            return cls()
        requiere = []
        for item in data.get("requiere", []) or []:
            if isinstance(item, dict):
                requiere.append((item["dependiente"], item["prerequisito"]))
        incompatibles = []
        for pair in data.get("incompatibles", []) or []:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                incompatibles.append((pair[0], pair[1]))
        orden = []
        for item in data.get("orden_previo", []) or []:
            if isinstance(item, dict):
                orden.append((item["antes"], item["despues"]))
        return cls(
            presupuesto_maximo=data.get("presupuesto_maximo"),
            tiempo_maximo_dias=data.get("tiempo_maximo_dias"),
            capacidad_operativa=data.get("capacidad_operativa"),
            max_iniciativas=data.get("max_iniciativas"),
            riesgo_maximo=data.get("riesgo_maximo"),
            obligatorias=list(data.get("obligatorias", []) or []),
            excluidas=list(data.get("excluidas", []) or []),
            requiere=requiere,
            incompatibles=incompatibles,
            orden_previo=orden,
        )


@dataclass
class OportunidadEvaluada:
    opportunity_id: str
    codigo: str
    titulo: str
    valor: float
    costo: float
    impacto: float
    tiempo_dias: float
    riesgo: float
    confianza: float
    probabilidad_exito: float
    puntuacion: float
    factores: dict[str, Any]
    aprendizaje: dict[str, Any]
    exclusion_razon: str | None = None


def _registrar_auditoria(
    db: Session,
    *,
    org_id: str,
    accion: str,
    actor_id: str | None,
    recomendacion_id: str | None = None,
    detalle: dict | None = None,
) -> None:
    db.add(
        OptimizacionAuditoria(
            organization_id=org_id,
            recomendacion_id=recomendacion_id,
            accion=accion,
            actor_id=actor_id,
            detalle_json=_json_dump(detalle) if detalle else None,
        )
    )


def obtener_configuracion(db: Session, org_id: str) -> OptimizacionConfiguracion:
    cfg = db.query(OptimizacionConfiguracion).filter(OptimizacionConfiguracion.organization_id == org_id).first()
    if not cfg:
        cfg = OptimizacionConfiguracion(
            organization_id=org_id,
            objetivo_default="RESULTADO_EQUILIBRADO",
            pesos_json=_json_dump(PESOS_OBJETIVO["RESULTADO_EQUILIBRADO"]),
        )
        db.add(cfg)
        db.flush()
    return cfg


def actualizar_configuracion(
    db: Session, user: User, *, objetivo_default: str | None = None, pesos: dict | None = None
) -> OptimizacionConfiguracion:
    cfg = obtener_configuracion(db, user.organization_id)
    if objetivo_default:
        cfg.objetivo_default = objetivo_default
    if pesos:
        cfg.pesos_json = _json_dump(pesos)
    cfg.updated_by = user.id
    cfg.updated_at = _utcnow()
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="configuracion.actualizada", actor_id=user.id,
        detalle={"objetivo": objetivo_default, "pesos": pesos},
    )
    return cfg


def _cargar_aprendizaje(db: Session, org_id: str, opp: Opportunity) -> dict[str, Any]:
    influencia: dict[str, Any] = {"ciclos": [], "patrones": [], "ajustes": {}}
    ciclo = (
        db.query(CicloAprendizaje)
        .filter(
            CicloAprendizaje.organization_id == org_id,
            CicloAprendizaje.opportunity_id == opp.id,
            CicloAprendizaje.estado == "EVALUADO",
        )
        .order_by(CicloAprendizaje.evaluado_at.desc())
        .first()
    )
    confianza_adj = _float(opp.confianza, 0.5)
    prob_exito = confianza_adj
    riesgo_adj = _RIESGO.get((opp.riesgo or "MEDIO").upper(), 0.5)
    if ciclo:
        influencia["ciclos"].append({"ciclo_id": ciclo.id, "calidad": ciclo.calidad_recomendacion})
        calidad = ciclo.calidad_recomendacion or "ACEPTABLE"
        if calidad == "EXCELENTE":
            confianza_adj = min(1.0, confianza_adj + 0.1)
            prob_exito = min(1.0, prob_exito + 0.1)
        elif calidad == "DEFICIENTE":
            confianza_adj = max(0.1, confianza_adj - 0.15)
            prob_exito = max(0.1, prob_exito - 0.2)
            riesgo_adj = min(1.0, riesgo_adj + 0.1)
        elif calidad == "DEBIL":
            confianza_adj = max(0.1, confianza_adj - 0.08)
            prob_exito = max(0.1, prob_exito - 0.1)
    patrones = (
        db.query(PatronAprendizaje)
        .filter(
            PatronAprendizaje.organization_id == org_id,
            PatronAprendizaje.dominio == opp.dominio,
            PatronAprendizaje.tipo_oportunidad == opp.tipo,
        )
        .all()
    )
    for p in patrones:
        influencia["patrones"].append({"id": p.id, "tipo": p.tipo_patron, "ocurrencias": p.ocurrencias})
        if p.ocurrencias >= 2 and "DESVIACION_VALOR" in p.tipo_patron:
            confianza_adj = max(0.1, confianza_adj - 0.05)
    influencia["ajustes"] = {
        "confianza_ajustada": round(confianza_adj, 4),
        "probabilidad_exito": round(prob_exito, 4),
        "riesgo_ajustado": round(riesgo_adj, 4),
    }
    return influencia


def _enriquecer_oportunidad(db: Session, org_id: str, opp: Opportunity, pesos: dict[str, float]) -> OportunidadEvaluada:
    valor = _float(opp.valor_potencial)
    costo = max(_float(opp.costo_estimado), 1.0)
    impacto = _float(opp.impacto_estimado)
    tiempo = 30.0
    valuation = (
        db.query(OpportunityValuation)
        .filter(OpportunityValuation.organization_id == org_id, OpportunityValuation.opportunity_id == opp.id)
        .first()
    )
    if valuation:
        exp = (
            db.query(OpportunityValuationExpected)
            .filter(OpportunityValuationExpected.valuation_id == valuation.id)
            .first()
        )
        if exp:
            if exp.adjusted_expected is not None:
                valor = _float(exp.adjusted_expected)
            if exp.execution_cost_expected is not None:
                costo = max(_float(exp.execution_cost_expected), 1.0)
            if exp.period_days is not None:
                tiempo = float(exp.period_days)
    aprendizaje = _cargar_aprendizaje(db, org_id, opp)
    adj = aprendizaje["ajustes"]
    confianza = adj["confianza_ajustada"]
    prob_exito = adj["probabilidad_exito"]
    riesgo = adj["riesgo_ajustado"]
    urgencia = _URGENCIA.get((opp.urgencia or "MEDIA").upper(), 0.5)

    norm_valor = min(valor / 1_000_000.0, 1.0)
    norm_impacto = min(impacto / 1_000_000.0, 1.0)
    norm_costo = min(costo / 500_000.0, 1.0)
    roi = (valor - costo) / costo if costo > 0 else 0.0

    contrib = {
        "valor": round(norm_valor * pesos.get("valor", 0.25), 4),
        "impacto": round(norm_impacto * pesos.get("impacto", 0.2), 4),
        "urgencia": round(urgencia * pesos.get("urgencia", 0.15), 4),
        "confianza": round(confianza * pesos.get("confianza", 0.15), 4),
        "probabilidad_exito": round(prob_exito * 0.1, 4),
        "riesgo": round(riesgo * pesos.get("riesgo", -0.15), 4),
        "costo": round(-norm_costo * abs(pesos.get("costo", -0.1)), 4),
    }
    bonificaciones = []
    penalizaciones = []
    if aprendizaje.get("ciclos"):
        bonificaciones.append("Ajuste por ciclo de aprendizaje evaluado")
    if aprendizaje.get("patrones"):
        penalizaciones.append("Patrones históricos de desviación detectados")

    puntuacion = sum(contrib.values()) * 100
    if roi > 0.5:
        bonificaciones.append(f"ROI favorable ({roi:.2f})")
        puntuacion += min(roi * 5, 10)

    factores = {
        "contribuciones": contrib,
        "pesos_aplicados": pesos,
        "bonificaciones": bonificaciones,
        "penalizaciones": penalizaciones,
        "roi": round(roi, 4),
        "metricas_raw": {
            "valor": valor, "costo": costo, "impacto": impacto, "tiempo_dias": tiempo,
            "riesgo": riesgo, "confianza": confianza, "probabilidad_exito": prob_exito,
        },
        "razon_posicion": "Puntuación = suma ponderada de factores normalizados × 100 + bonificaciones",
    }
    return OportunidadEvaluada(
        opportunity_id=opp.id,
        codigo=opp.codigo,
        titulo=opp.titulo,
        valor=valor,
        costo=costo,
        impacto=impacto,
        tiempo_dias=tiempo,
        riesgo=riesgo,
        confianza=confianza,
        probabilidad_exito=prob_exito,
        puntuacion=round(puntuacion, 4),
        factores=factores,
        aprendizaje=aprendizaje,
    )


def _validar_subset(ids: set[str], restricciones: Restricciones, evaluadas: dict[str, OportunidadEvaluada]) -> tuple[bool, str | None]:
    for exc in restricciones.excluidas:
        if exc in ids:
            return False, f"Oportunidad excluida incluida: {exc}"
    for obl in restricciones.obligatorias:
        if obl not in ids:
            return False, f"Oportunidad obligatoria ausente: {obl}"
    for dep, pre in restricciones.requiere:
        if dep in ids and pre not in ids:
            return False, f"{dep} requiere {pre}"
    for a, b in restricciones.incompatibles:
        if a in ids and b in ids:
            return False, f"Incompatibilidad entre {a} y {b}"
    if restricciones.max_iniciativas is not None and len(ids) > restricciones.max_iniciativas:
        return False, "Supera máximo de iniciativas"
    if restricciones.capacidad_operativa is not None and len(ids) > restricciones.capacidad_operativa:
        return False, "Supera capacidad operativa"
    total_costo = sum(evaluadas[i].costo for i in ids if i in evaluadas)
    total_tiempo = sum(evaluadas[i].tiempo_dias for i in ids if i in evaluadas)
    if restricciones.presupuesto_maximo is not None and total_costo > restricciones.presupuesto_maximo:
        return False, f"Presupuesto excedido ({total_costo} > {restricciones.presupuesto_maximo})"
    if restricciones.tiempo_maximo_dias is not None and total_tiempo > restricciones.tiempo_maximo_dias:
        return False, f"Tiempo excedido ({total_tiempo} > {restricciones.tiempo_maximo_dias})"
    if restricciones.riesgo_maximo is not None and ids:
        riesgo_prom = sum(evaluadas[i].riesgo for i in ids) / len(ids)
        if riesgo_prom > restricciones.riesgo_maximo:
            return False, f"Riesgo promedio {riesgo_prom:.2f} supera máximo {restricciones.riesgo_maximo}"
    return True, None


def _score_portfolio(ids: set[str], evaluadas: dict[str, OportunidadEvaluada], objetivo: str) -> float:
    if not ids:
        return 0.0
    valor = sum(evaluadas[i].valor for i in ids)
    costo = sum(evaluadas[i].costo for i in ids)
    impacto = sum(evaluadas[i].impacto for i in ids)
    riesgo = sum(evaluadas[i].riesgo for i in ids) / len(ids)
    puntuacion = sum(evaluadas[i].puntuacion for i in ids)
    if objetivo == "MAXIMIZAR_VALOR":
        return valor
    if objetivo == "MAXIMIZAR_ROI":
        return (valor - costo) / costo if costo > 0 else 0
    if objetivo == "MAXIMIZAR_IMPACTO":
        return impacto
    if objetivo == "MINIMIZAR_RIESGO":
        return -riesgo
    return puntuacion


def _optimizar_portafolio(
    candidatas: list[OportunidadEvaluada],
    restricciones: Restricciones,
    objetivo: str,
) -> tuple[set[str], bool, list[str]]:
    evaluadas = {c.opportunity_id: c for c in candidatas}
    ids_all = list(evaluadas.keys())
    conflictos: list[str] = []

    for obl in restricciones.obligatorias:
        if obl not in evaluadas:
            conflictos.append(f"Oportunidad obligatoria no encontrada: {obl}")
    if conflictos:
        return set(), False, conflictos

    oblig_set = set(restricciones.obligatorias)
    disponibles = [i for i in ids_all if i not in restricciones.excluidas]
    n = len(disponibles)
    if n > MAX_SUBSET_ENUM:
        disponibles = sorted(disponibles, key=lambda x: evaluadas[x].puntuacion, reverse=True)[:MAX_SUBSET_ENUM]
        n = len(disponibles)

    best_ids: set[str] = set()
    best_score = float("-inf")
    found_feasible = False

    for r in range(len(oblig_set), min(n, restricciones.max_iniciativas or n) + 1):
        for combo in combinations(disponibles, r):
            ids = set(combo) | oblig_set
            ok, reason = _validar_subset(ids, restricciones, evaluadas)
            if not ok:
                continue
            found_feasible = True
            score = _score_portfolio(ids, evaluadas, objetivo)
            if score > best_score:
                best_score = score
                best_ids = ids

    if not found_feasible and oblig_set:
        ok, reason = _validar_subset(oblig_set, restricciones, evaluadas)
        if ok:
            return oblig_set, True, []
        conflictos.append(reason or "Restricciones incompatibles con obligatorias")

    if not found_feasible:
        conflictos.append("SIN SOLUCIÓN FACTIBLE con las restricciones actuales")
        return set(), False, conflictos

    return best_ids, True, conflictos


def _ordenar_seleccion(ids: set[str], evaluadas: dict[str, OportunidadEvaluada], restricciones: Restricciones) -> list[str]:
    ordenados = sorted(ids, key=lambda x: evaluadas[x].puntuacion, reverse=True)
    for antes, despues in restricciones.orden_previo:
        if antes in ordenados and despues in ordenados:
            ia, id_ = ordenados.index(antes), ordenados.index(despues)
            if ia > id_:
                ordenados.remove(antes)
                ordenados.insert(id_, antes)
    return ordenados


def ejecutar_optimizacion(
    db: Session,
    org_id: str,
    *,
    objetivo: str,
    restricciones_data: dict | None,
    pesos_custom: dict | None = None,
    opportunity_ids: list[str] | None = None,
) -> dict[str, Any]:
    restricciones = Restricciones.from_dict(restricciones_data)
    pesos = dict(pesos_custom or PESOS_OBJETIVO.get(objetivo, PESOS_OBJETIVO["RESULTADO_EQUILIBRADO"]))

    q = db.query(Opportunity).filter(
        Opportunity.organization_id == org_id,
        Opportunity.estado.notin_(["DESCARTADA", "CERRADA"]),
    )
    if opportunity_ids:
        q = q.filter(Opportunity.id.in_(opportunity_ids))
    oportunidades = q.limit(MAX_PORTFOLIO_CANDIDATES).all()

    evaluadas_list = [_enriquecer_oportunidad(db, org_id, o, pesos) for o in oportunidades]
    evaluadas_list.sort(key=lambda x: x.puntuacion, reverse=True)

    seleccion, factible, conflictos = _optimizar_portafolio(evaluadas_list, restricciones, objetivo)
    evaluadas_map = {e.opportunity_id: e for e in evaluadas_list}
    orden = _ordenar_seleccion(seleccion, evaluadas_map, restricciones) if factible else []

    explicaciones = {
        "objetivo": objetivo,
        "restricciones": restricciones_data,
        "por_que_primera": None,
        "excluidas": [],
        "restricciones_activas": [],
        "aprendizaje_global": [],
    }
    if orden:
        first = evaluadas_map[orden[0]]
        explicaciones["por_que_primera"] = {
            "opportunity_id": first.opportunity_id,
            "titulo": first.titulo,
            "puntuacion": first.puntuacion,
            "factores": first.factores,
            "aprendizaje": first.aprendizaje,
        }
    for e in evaluadas_list:
        if e.opportunity_id not in seleccion:
            razon = e.exclusion_razon or "No seleccionada en portafolio óptimo bajo restricciones"
            explicaciones["excluidas"].append({
                "opportunity_id": e.opportunity_id,
                "titulo": e.titulo,
                "razon": razon,
                "puntuacion": e.puntuacion,
            })
    if restricciones.presupuesto_maximo:
        explicaciones["restricciones_activas"].append(f"Presupuesto máximo: {restricciones.presupuesto_maximo}")
    if restricciones.max_iniciativas:
        explicaciones["restricciones_activas"].append(f"Máximo iniciativas: {restricciones.max_iniciativas}")

    totales = {"valor": 0.0, "costo": 0.0, "impacto": 0.0, "tiempo": 0.0}
    for oid in seleccion:
        e = evaluadas_map[oid]
        totales["valor"] += e.valor
        totales["costo"] += e.costo
        totales["impacto"] += e.impacto
        totales["tiempo"] += e.tiempo_dias
    roi = (totales["valor"] - totales["costo"]) / totales["costo"] if totales["costo"] > 0 else None
    riesgo_prom = sum(evaluadas_map[i].riesgo for i in seleccion) / len(seleccion) if seleccion else None
    conf_prom = sum(evaluadas_map[i].confianza for i in seleccion) / len(seleccion) if seleccion else None

    return {
        "factible": factible,
        "conflictos": conflictos,
        "seleccion": orden,
        "evaluadas": evaluadas_list,
        "evaluadas_map": evaluadas_map,
        "totales": totales,
        "roi": roi,
        "riesgo_promedio": riesgo_prom,
        "confianza_promedio": conf_prom,
        "explicacion": explicaciones,
        "pesos": pesos,
    }


def _codigo_recomendacion() -> str:
    return f"OPT-{uuid.uuid4().hex[:8].upper()}"


def crear_recomendacion(
    db: Session,
    user: User,
    *,
    objetivo: str,
    restricciones: dict | None,
    es_simulacion: bool = False,
    opportunity_ids: list[str] | None = None,
    pesos: dict | None = None,
    grupo_comparacion_id: str | None = None,
) -> OptimizacionRecomendacion:
    resultado = ejecutar_optimizacion(
        db, user.organization_id,
        objetivo=objetivo,
        restricciones_data=restricciones,
        pesos_custom=pesos,
        opportunity_ids=opportunity_ids,
    )
    rec = OptimizacionRecomendacion(
        organization_id=user.organization_id,
        codigo=_codigo_recomendacion(),
        estado="PROPUESTA",
        objetivo=objetivo,
        es_simulacion=es_simulacion,
        grupo_comparacion_id=grupo_comparacion_id,
        restricciones_json=_json_dump(restricciones),
        resultado_json=_json_dump({"seleccion": resultado["seleccion"], "totales": resultado["totales"]}),
        explicacion_json=_json_dump(resultado["explicacion"]),
        factible=resultado["factible"],
        conflicto_restricciones_json=_json_dump(resultado["conflictos"]) if not resultado["factible"] else None,
        valor_esperado_total=resultado["totales"]["valor"],
        costo_esperado_total=resultado["totales"]["costo"],
        impacto_esperado_total=resultado["totales"]["impacto"],
        tiempo_esperado_total=resultado["totales"]["tiempo"],
        riesgo_promedio=resultado["riesgo_promedio"],
        confianza_promedio=resultado["confianza_promedio"],
        roi_esperado=resultado["roi"],
        created_by=user.id,
    )
    db.add(rec)
    db.flush()

    influencia_global = []
    for ev in resultado["evaluadas"]:
        sel = ev.opportunity_id in resultado["seleccion"]
        orden = resultado["seleccion"].index(ev.opportunity_id) + 1 if sel else None
        if ev.aprendizaje.get("ciclos") or ev.aprendizaje.get("patrones"):
            influencia_global.append({"opportunity_id": ev.opportunity_id, "aprendizaje": ev.aprendizaje})
        db.add(
            OptimizacionItem(
                recomendacion_id=rec.id,
                organization_id=user.organization_id,
                opportunity_id=ev.opportunity_id,
                seleccionado=sel,
                orden=orden,
                puntuacion_total=ev.puntuacion,
                factores_json=_json_dump(ev.factores),
                exclusion_razon=None if sel else "No incluida en portafolio óptimo",
                valor_esperado=ev.valor,
                costo_esperado=ev.costo,
                impacto_esperado=ev.impacto,
                riesgo=ev.riesgo,
                confianza=ev.confianza,
                probabilidad_exito=ev.probabilidad_exito,
                tiempo_esperado_dias=ev.tiempo_dias,
                aprendizaje_json=_json_dump(ev.aprendizaje),
            )
        )
    rec.aprendizaje_influencia_json = _json_dump(influencia_global)
    accion = "simulacion.ejecutada" if es_simulacion else "recomendacion.creada"
    _registrar_auditoria(
        db, org_id=user.organization_id, accion=accion, actor_id=user.id,
        recomendacion_id=rec.id, detalle={"objetivo": objetivo, "factible": resultado["factible"]},
    )
    return rec


def comparar_escenarios(
    db: Session,
    user: User,
    *,
    escenarios: list[dict],
    restricciones_base: dict | None = None,
) -> list[OptimizacionRecomendacion]:
    grupo_id = str(uuid.uuid4())
    recomendaciones = []
    for esc in escenarios:
        obj = esc.get("objetivo", "RESULTADO_EQUILIBRADO")
        rest = {**(restricciones_base or {}), **(esc.get("restricciones") or {})}
        rec = crear_recomendacion(
            db, user,
            objetivo=obj,
            restricciones=rest,
            es_simulacion=True,
            pesos=esc.get("pesos"),
            grupo_comparacion_id=grupo_id,
        )
        recomendaciones.append(rec)
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="escenarios.comparados", actor_id=user.id,
        detalle={"grupo": grupo_id, "cantidad": len(escenarios)},
    )
    return recomendaciones


def recalcular_recomendacion(
    db: Session, user: User, recomendacion_id: str, *, restricciones: dict | None = None, objetivo: str | None = None
) -> OptimizacionRecomendacion:
    origen = obtener_recomendacion(db, user.organization_id, recomendacion_id)
    if not origen:
        raise ValueError("Recomendación no encontrada")
    nueva = crear_recomendacion(
        db, user,
        objetivo=objetivo or origen.objetivo,
        restricciones=restricciones or _json_load(origen.restricciones_json),
        es_simulacion=origen.es_simulacion,
    )
    nueva.estado = "RECALCULADA"
    nueva.recomendacion_origen_id = origen.id
    nueva.version = origen.version + 1
    origen.estado = "RECALCULADA"
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recomendacion.recalculada", actor_id=user.id,
        recomendacion_id=nueva.id, detalle={"origen_id": origen.id},
    )
    return nueva


def aprobar_recomendacion(db: Session, user: User, recomendacion_id: str, justificacion: str) -> OptimizacionRecomendacion:
    rec = obtener_recomendacion(db, user.organization_id, recomendacion_id)
    if not rec:
        raise ValueError("Recomendación no encontrada")
    if rec.estado not in ("PROPUESTA", "REVISADA", "RECALCULADA"):
        raise ValueError("Estado no permite aprobación")
    rec.estado = "APROBADA"
    rec.justificacion_aprobacion = justificacion
    rec.decidida_por = user.id
    rec.decidida_at = _utcnow()
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recomendacion.aprobada", actor_id=user.id,
        recomendacion_id=rec.id, detalle={"justificacion": justificacion},
    )
    return rec


def rechazar_recomendacion(db: Session, user: User, recomendacion_id: str, motivo: str) -> OptimizacionRecomendacion:
    rec = obtener_recomendacion(db, user.organization_id, recomendacion_id)
    if not rec:
        raise ValueError("Recomendación no encontrada")
    if rec.estado in ("APROBADA", "EJECUTADA", "RECHAZADA"):
        raise ValueError("Estado no permite rechazo")
    rec.estado = "RECHAZADA"
    rec.motivo_rechazo = motivo
    rec.decidida_por = user.id
    rec.decidida_at = _utcnow()
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recomendacion.rechazada", actor_id=user.id,
        recomendacion_id=rec.id, detalle={"motivo": motivo},
    )
    return rec


def marcar_revisada(db: Session, user: User, recomendacion_id: str) -> OptimizacionRecomendacion:
    rec = obtener_recomendacion(db, user.organization_id, recomendacion_id)
    if not rec:
        raise ValueError("Recomendación no encontrada")
    rec.estado = "REVISADA"
    _registrar_auditoria(
        db, org_id=user.organization_id, accion="recomendacion.revisada", actor_id=user.id, recomendacion_id=rec.id,
    )
    return rec


def obtener_recomendacion(db: Session, org_id: str, rec_id: str) -> OptimizacionRecomendacion | None:
    return (
        db.query(OptimizacionRecomendacion)
        .filter(OptimizacionRecomendacion.id == rec_id, OptimizacionRecomendacion.organization_id == org_id)
        .first()
    )


def listar_recomendaciones(db: Session, org_id: str, *, incluir_simulaciones: bool = True) -> list[OptimizacionRecomendacion]:
    q = db.query(OptimizacionRecomendacion).filter(OptimizacionRecomendacion.organization_id == org_id)
    if not incluir_simulaciones:
        q = q.filter(OptimizacionRecomendacion.es_simulacion.is_(False))
    return q.order_by(OptimizacionRecomendacion.created_at.desc()).all()


def listar_items(db: Session, org_id: str, recomendacion_id: str) -> list[OptimizacionItem]:
    return (
        db.query(OptimizacionItem)
        .filter(OptimizacionItem.recomendacion_id == recomendacion_id, OptimizacionItem.organization_id == org_id)
        .order_by(OptimizacionItem.orden.asc().nullslast(), OptimizacionItem.puntuacion_total.desc())
        .all()
    )


def listar_auditoria(db: Session, org_id: str, recomendacion_id: str | None = None) -> list[OptimizacionAuditoria]:
    q = db.query(OptimizacionAuditoria).filter(OptimizacionAuditoria.organization_id == org_id)
    if recomendacion_id:
        q = q.filter(OptimizacionAuditoria.recomendacion_id == recomendacion_id)
    return q.order_by(OptimizacionAuditoria.created_at.desc()).all()


def serializar_recomendacion(rec: OptimizacionRecomendacion, items: list[OptimizacionItem] | None = None) -> dict[str, Any]:
    return {
        "id": rec.id,
        "codigo": rec.codigo,
        "estado": rec.estado,
        "objetivo": rec.objetivo,
        "es_simulacion": rec.es_simulacion,
        "grupo_comparacion_id": rec.grupo_comparacion_id,
        "factible": rec.factible,
        "restricciones": _json_load(rec.restricciones_json),
        "resultado": _json_load(rec.resultado_json),
        "explicacion": _json_load(rec.explicacion_json),
        "conflictos": _json_load(rec.conflicto_restricciones_json),
        "aprendizaje_influencia": _json_load(rec.aprendizaje_influencia_json),
        "valor_esperado_total": _float(rec.valor_esperado_total) if rec.valor_esperado_total else 0,
        "costo_esperado_total": _float(rec.costo_esperado_total) if rec.costo_esperado_total else 0,
        "impacto_esperado_total": _float(rec.impacto_esperado_total) if rec.impacto_esperado_total else 0,
        "roi_esperado": _float(rec.roi_esperado) if rec.roi_esperado is not None else None,
        "riesgo_promedio": _float(rec.riesgo_promedio) if rec.riesgo_promedio is not None else None,
        "confianza_promedio": _float(rec.confianza_promedio) if rec.confianza_promedio is not None else None,
        "tiempo_esperado_total": _float(rec.tiempo_esperado_total) if rec.tiempo_esperado_total else 0,
        "version": rec.version,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "items": [serializar_item(i) for i in items] if items is not None else None,
    }


def serializar_item(item: OptimizacionItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "opportunity_id": item.opportunity_id,
        "seleccionado": item.seleccionado,
        "orden": item.orden,
        "puntuacion_total": _float(item.puntuacion_total) if item.puntuacion_total else None,
        "factores": _json_load(item.factores_json),
        "exclusion_razon": item.exclusion_razon,
        "valor_esperado": _float(item.valor_esperado) if item.valor_esperado else None,
        "costo_esperado": _float(item.costo_esperado) if item.costo_esperado else None,
        "impacto_esperado": _float(item.impacto_esperado) if item.impacto_esperado else None,
        "riesgo": _float(item.riesgo) if item.riesgo else None,
        "confianza": _float(item.confianza) if item.confianza else None,
        "aprendizaje": _json_load(item.aprendizaje_json),
    }
