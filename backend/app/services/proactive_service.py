"""Motor transversal de inteligencia proactiva y oportunidades — 1030."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.opportunity_models import (
    Opportunity,
    OpportunityTrace,
    OpportunityTracking,
    OpportunityTransition,
    ProactiveSignal,
)

# --- Constantes ---

OPPORTUNITY_TYPES = frozenset({
    "INGRESO", "AHORRO", "RECUPERACION", "PRODUCTIVIDAD", "CALIDAD", "RIESGO",
    "CUMPLIMIENTO", "AUTOMATIZACION", "CAPACIDAD", "COMERCIAL", "OPERATIVA",
    "FINANCIERA", "EXPERIENCIA", "OTRO",
})

ESTADOS_VALIDOS = frozenset({
    "DETECTADA", "EN_EVALUACION", "PRIORIZADA", "PROPUESTA", "PENDIENTE_APROBACION",
    "APROBADA", "EN_EJECUCION", "EN_SEGUIMIENTO", "MATERIALIZADA", "CERRADA",
    "DESCARTADA", "POSPUESTA", "NO_PERTINENTE", "SIN_CAPACIDAD", "DATOS_INSUFICIENTES",
    "FALLIDA", "CANCELADA",
})

TRANSICIONES_PERMITIDAS: dict[str, set[str]] = {
    "DETECTADA": {"EN_EVALUACION", "DESCARTADA", "DATOS_INSUFICIENTES"},
    "EN_EVALUACION": {"PRIORIZADA", "NO_PERTINENTE", "DATOS_INSUFICIENTES", "DESCARTADA", "POSPUESTA"},
    "PRIORIZADA": {"PROPUESTA", "PENDIENTE_APROBACION", "APROBADA", "POSPUESTA", "DESCARTADA"},
    "PROPUESTA": {"PENDIENTE_APROBACION", "APROBADA", "DESCARTADA"},
    "PENDIENTE_APROBACION": {"APROBADA", "DESCARTADA", "CANCELADA"},
    "APROBADA": {"EN_EJECUCION", "SIN_CAPACIDAD", "CANCELADA"},
    "EN_EJECUCION": {"EN_SEGUIMIENTO", "FALLIDA", "CANCELADA"},
    "EN_SEGUIMIENTO": {"MATERIALIZADA", "FALLIDA", "CERRADA"},
    "MATERIALIZADA": {"CERRADA"},
    "DATOS_INSUFICIENTES": {"EN_EVALUACION", "DESCARTADA"},
    "SIN_CAPACIDAD": {"EN_EVALUACION", "DESCARTADA", "POSPUESTA"},
    "NO_PERTINENTE": {"CERRADA"},
    "POSPUESTA": {"EN_EVALUACION", "DESCARTADA"},
    "FALLIDA": {"CERRADA", "EN_EVALUACION"},
    "CANCELADA": {"CERRADA"},
    "DESCARTADA": {"CERRADA"},
    "CERRADA": set(),
}

PERTINENCIA_RESULTADOS = frozenset({
    "ACTUAR", "OBSERVAR", "POSPONER", "DESCARTAR", "SOLICITAR_DATOS", "SOLICITAR_APROBACION",
})

MOMENTO_RESULTADOS = frozenset({"AHORA", "PROGRAMAR", "ESPERAR_EVENTO", "OBSERVAR", "NO_APLICA"})

HUMAN_GATE = frozenset({
    "AUTOMATICA_PERMITIDA", "AUTOMATICA_BAJO_POLITICA", "REQUIERE_APROBACION", "PROHIBIDA",
})

ATRIBUCION_NIVELES = frozenset({
    "NO_ATRIBUIBLE", "INFLUENCIADO", "PARCIALMENTE_ATRIBUIBLE", "ATRIBUIBLE",
})

_DEDUPE_WINDOW_HOURS = 24


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse_json(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _new_correlation() -> str:
    return str(uuid.uuid4())


def _make_dedupe_key(
    org_id: str,
    tipo: str,
    origen: str,
    source_ref: str | None,
    evento: str,
) -> str:
    raw = f"{org_id}|{tipo}|{origen}|{source_ref or ''}|{evento}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _next_codigo(db: Session, org_id: str) -> str:
    count = db.query(func.count(Opportunity.id)).filter(Opportunity.organization_id == org_id).scalar() or 0
    return f"OPP-{count + 1:05d}"


def add_trace(
    db: Session,
    *,
    organization_id: str,
    correlation_id: str,
    etapa: str,
    opportunity_id: str | None = None,
    signal_id: str | None = None,
    detalle: dict | None = None,
) -> OpportunityTrace:
    trace = OpportunityTrace(
        organization_id=organization_id,
        opportunity_id=opportunity_id,
        signal_id=signal_id,
        correlation_id=correlation_id,
        etapa=etapa,
        detalle_json=_json(detalle) if detalle else None,
    )
    db.add(trace)
    return trace


# --- Señales ---

def create_signal(
    db: Session,
    *,
    organization_id: str,
    tipo: str,
    dominio: str,
    origen: str,
    evento: str,
    source_reference: str | None = None,
    payload: dict | None = None,
    severidad: str = "MEDIA",
    confianza: float = 0.5,
    correlation_id: str | None = None,
) -> tuple[ProactiveSignal, bool]:
    """Crea señal con deduplicación. Retorna (señal, es_nueva)."""
    dedupe_key = _make_dedupe_key(organization_id, tipo, origen, source_reference, evento)
    window_start = _utcnow() - timedelta(hours=_DEDUPE_WINDOW_HOURS)
    existing = (
        db.query(ProactiveSignal)
        .filter(
            ProactiveSignal.organization_id == organization_id,
            ProactiveSignal.dedupe_key == dedupe_key,
            ProactiveSignal.created_at >= window_start,
        )
        .first()
    )
    if existing:
        return existing, False

    corr = correlation_id or _new_correlation()
    signal = ProactiveSignal(
        organization_id=organization_id,
        tipo=tipo,
        dominio=dominio,
        origen=origen,
        source_reference=source_reference,
        evento=evento,
        payload_json=_json(payload) if payload else None,
        severidad=severidad,
        confianza=confianza,
        dedupe_key=dedupe_key,
        correlation_id=corr,
    )
    db.add(signal)
    db.flush()
    add_trace(db, organization_id=organization_id, correlation_id=corr, etapa="SENAL_CREADA",
              signal_id=signal.id, detalle={"evento": evento, "tipo": tipo})
    return signal, True


# --- Contexto 360 ---

def build_context_360(
    db: Session,
    *,
    organization_id: str,
    dominio: str,
    payload: dict | None = None,
    opportunity_id: str | None = None,
) -> dict[str, Any]:
    """Construye contexto disponible y clasifica suficiencia."""
    payload = payload or {}
    indicadores = payload.get("indicadores") or {}
    historico = payload.get("historico") or {}
    eventos = payload.get("eventos") or []
    conocimiento = payload.get("conocimiento_autorizado")
    workplans_abiertos = payload.get("workplans_abiertos", 0)
    oportunidades_similares = 0
    if opportunity_id:
        oportunidades_similares = (
            db.query(func.count(Opportunity.id))
            .filter(
                Opportunity.organization_id == organization_id,
                Opportunity.dominio == dominio,
                Opportunity.id != opportunity_id,
                Opportunity.estado.notin_(["CERRADA", "DESCARTADA", "CANCELADA"]),
            )
            .scalar() or 0
        )

    componentes = {
        "organization_id": organization_id,
        "dominio": dominio,
        "indicadores": indicadores,
        "historico": historico,
        "eventos": eventos,
        "conocimiento_autorizado": conocimiento,
        "workplans_abiertos": workplans_abiertos,
        "oportunidades_similares": oportunidades_similares,
        "payload": payload,
    }

    tiene_indicadores = bool(indicadores)
    tiene_historico = bool(historico)
    faltantes: list[str] = []
    if not tiene_indicadores:
        faltantes.append("indicadores")
    if not tiene_historico and dominio not in ("administrativo", "comercial"):
        faltantes.append("histórico")

    # Contradicción: indicadores vs conocimiento
    conflicto = False
    if conocimiento and indicadores:
        conocimiento_val = conocimiento.get("valor") if isinstance(conocimiento, dict) else None
        indicador_val = indicadores.get("valor_principal") or indicadores.get("tasa_conversion")
        if conocimiento_val is not None and indicador_val is not None:
            try:
                a, b = float(conocimiento_val), float(indicador_val)
                denom = max(abs(a), abs(b), 0.001)
                if abs(a - b) / denom > 0.3:
                    conflicto = True
            except (TypeError, ValueError):
                pass

    if conflicto:
        suficiencia = "PARCIAL"
        componentes["conflicto"] = True
        componentes["conflicto_detalle"] = "Indicadores y conocimiento autorizado divergen"
    elif not tiene_indicadores:
        suficiencia = "INSUFICIENTE"
    elif not tiene_historico and len(faltantes) > 0:
        suficiencia = "PARCIAL"
    else:
        suficiencia = "SUFICIENTE"

    return {
        "componentes": componentes,
        "suficiencia": suficiencia,
        "faltantes": faltantes,
        "conflicto": conflicto,
    }


# --- Capacidad 360 ---

def assess_capability_360(
    db: Session,
    *,
    organization_id: str,
    dominio: str,
    riesgo: str = "MEDIO",
    costo_estimado: float | None = None,
) -> dict[str, Any]:
    """Evalúa capacidad real disponible."""
    from app.enums import EmployeeLifecycleStatus
    from app.orchestration_models import AIEmployee, EmployeeCapability, Capability

    active_statuses = {
        EmployeeLifecycleStatus.ACTIVE,
        EmployeeLifecycleStatus.PUBLISHED,
        EmployeeLifecycleStatus.CERTIFIED,
    }
    employees = (
        db.query(AIEmployee)
        .filter(
            AIEmployee.organization_id == organization_id,
            AIEmployee.lifecycle_status.in_(active_statuses),
        )
        .all()
    )
    empleados_disponibles = len(employees)
    herramientas = db.query(Capability).filter(Capability.is_active.is_(True)).count()

    ejecutable = empleados_disponibles > 0
    requiere_aprobacion = riesgo in ("ALTO", "CRITICO") or (costo_estimado or 0) > 5_000_000

    gate = "AUTOMATICA_PERMITIDA"
    if not ejecutable:
        gate = "PROHIBIDA"
    elif requiere_aprobacion:
        gate = "REQUIERE_APROBACION"
    elif riesgo == "MEDIO":
        gate = "AUTOMATICA_BAJO_POLITICA"

    return {
        "empleados_disponibles": empleados_disponibles,
        "herramientas_activas": herramientas,
        "ejecutable": ejecutable,
        "requiere_aprobacion": requiere_aprobacion,
        "human_gate": gate,
        "limitaciones": [] if ejecutable else ["Sin empleados IA activos"],
        "mensaje": "Capacidad disponible" if ejecutable else "ACCIÓN RECOMENDABLE PERO NO EJECUTABLE AÚN",
    }


# --- Pertinencia ---

def evaluate_pertinence(
    contexto: dict[str, Any],
    *,
    impacto: float | None = None,
    duplicada: bool = False,
    capacidad: dict | None = None,
) -> dict[str, Any]:
    suficiencia = contexto.get("suficiencia", "INSUFICIENTE")
    conflicto = contexto.get("conflicto", False)
    componentes = contexto.get("componentes", {})
    oportunidades_similares = componentes.get("oportunidades_similares", 0)

    if suficiencia == "INSUFICIENTE":
        return {
            "resultado": "SOLICITAR_DATOS",
            "razon": f"Contexto insuficiente — faltan: {', '.join(contexto.get('faltantes', []))}",
            "bloqueado": "impacto, ROI, acción definitiva",
        }
    if conflicto:
        return {
            "resultado": "SOLICITAR_APROBACION",
            "razon": "Información contradictoria — requiere validación humana",
            "confianza_reducida": True,
        }
    if duplicada or oportunidades_similares > 2:
        return {"resultado": "OBSERVAR", "razon": "Oportunidad similar ya en curso"}
    if not capacidad or not capacidad.get("ejecutable"):
        return {"resultado": "POSPONER", "razon": capacidad.get("mensaje", "Sin capacidad")}
    if impacto is not None and impacto < 100_000:
        return {"resultado": "OBSERVAR", "razon": "Impacto bajo — observar tendencia"}
    if capacidad.get("requiere_aprobacion"):
        return {"resultado": "SOLICITAR_APROBACION", "razon": "Riesgo o costo requiere aprobación"}
    return {"resultado": "ACTUAR", "razon": "Evidencia, impacto y capacidad suficientes"}


# --- Momento ---

def evaluate_momento(
    *,
    urgencia: str = "MEDIA",
    sla_horas: int | None = None,
    tendencia: str | None = None,
    capacidad: dict | None = None,
) -> dict[str, Any]:
    if not capacidad or not capacidad.get("ejecutable"):
        return {"resultado": "OBSERVAR", "razon": "Esperar capacidad disponible"}
    if urgencia in ("CRITICA", "ALTA") or (sla_horas is not None and sla_horas <= 48):
        return {"resultado": "AHORA", "razon": "Urgencia alta o SLA próximo"}
    if tendencia == "EMPEORANDO":
        return {"resultado": "AHORA", "razon": "Tendencia negativa"}
    if urgencia == "BAJA":
        return {"resultado": "PROGRAMAR", "razon": "Urgencia baja — programar ventana"}
    return {"resultado": "AHORA", "razon": "Condiciones operativas favorables"}


# --- Priorización global ---

def _score_opportunity(opp: Opportunity | dict) -> dict[str, Any]:
    if isinstance(opp, Opportunity):
        impacto = float(opp.impacto_estimado or 0)
        urgencia_map = {"CRITICA": 1.0, "ALTA": 0.8, "MEDIA": 0.5, "BAJA": 0.2}
        urgencia = urgencia_map.get(opp.urgencia or "MEDIA", 0.5)
        confianza = float(opp.confianza or 0.5)
        riesgo_map = {"CRITICO": 0.2, "ALTO": 0.4, "MEDIO": 0.6, "BAJO": 0.9}
        riesgo_inv = riesgo_map.get(opp.riesgo or "MEDIO", 0.6)
        esfuerzo_map = {"ALTO": 0.2, "MEDIO": 0.5, "BAJO": 0.9}
        esfuerzo_inv = esfuerzo_map.get(opp.esfuerzo or "MEDIO", 0.5)
        valor = float(opp.valor_potencial or 0)
        prob = float(opp.probabilidad or 0.5)
        opp_id = opp.id
        titulo = opp.titulo
    else:
        impacto = float(opp.get("impacto_estimado") or 0)
        urgencia_map = {"CRITICA": 1.0, "ALTA": 0.8, "MEDIA": 0.5, "BAJA": 0.2}
        urgencia = urgencia_map.get(opp.get("urgencia", "MEDIA"), 0.5)
        confianza = float(opp.get("confianza") or 0.5)
        riesgo_map = {"CRITICO": 0.2, "ALTO": 0.4, "MEDIO": 0.6, "BAJO": 0.9}
        riesgo_inv = riesgo_map.get(opp.get("riesgo", "MEDIO"), 0.6)
        esfuerzo_map = {"ALTO": 0.2, "MEDIO": 0.5, "BAJO": 0.9}
        esfuerzo_inv = esfuerzo_map.get(opp.get("esfuerzo", "MEDIO"), 0.5)
        valor = float(opp.get("valor_potencial") or 0)
        prob = float(opp.get("probabilidad") or 0.5)
        opp_id = opp.get("id")
        titulo = opp.get("titulo")

    impacto_norm = min(impacto / 10_000_000, 1.0) if impacto else 0.1
    valor_norm = min(valor / 10_000_000, 1.0) if valor else 0.1

    componentes = {
        "impacto": round(impacto_norm * 0.25, 4),
        "urgencia": round(urgencia * 0.20, 4),
        "confianza": round(confianza * 0.15, 4),
        "riesgo_inverso": round(riesgo_inv * 0.10, 4),
        "esfuerzo_inverso": round(esfuerzo_inv * 0.10, 4),
        "valor_esperado": round(valor_norm * prob * 0.12, 4),
        "probabilidad": round(prob * 0.08, 4),
    }
    score = round(sum(componentes.values()), 4)
    return {
        "opportunity_id": opp_id,
        "titulo": titulo,
        "prioridad_score": score,
        "componentes": componentes,
    }


def prioritize_opportunities_global(
    db: Session,
    organization_id: str,
    *,
    estados: list[str] | None = None,
) -> dict[str, Any]:
    estados = estados or [
        "DETECTADA", "EN_EVALUACION", "PRIORIZADA", "PROPUESTA",
        "PENDIENTE_APROBACION", "APROBADA",
    ]
    opps = (
        db.query(Opportunity)
        .filter(
            Opportunity.organization_id == organization_id,
            Opportunity.estado.in_(estados),
        )
        .all()
    )
    scored = [_score_opportunity(o) for o in opps]
    scored.sort(key=lambda x: x["prioridad_score"], reverse=True)
    for i, item in enumerate(scored):
        item["ranking"] = i + 1
        opp = next((o for o in opps if o.id == item["opportunity_id"]), None)
        if opp:
            opp.prioridad_score = item["prioridad_score"]
            opp.prioridad_componentes_json = _json(item["componentes"])
    top = scored[0] if scored else None
    por_que = None
    if top:
        best_factor = max(top["componentes"], key=top["componentes"].get)
        por_que = f"Priorizada por {best_factor} (score={top['prioridad_score']})"
    return {
        "metodologia": "Score explicable multi-factor",
        "ranking": scored,
        "por_que_primero": por_que,
        "total": len(scored),
    }


# --- Siguiente mejor acción ---

def compute_next_best_action(
    db: Session,
    opportunity: Opportunity,
    *,
    capacidad: dict | None = None,
    equipo: dict | None = None,
) -> dict[str, Any]:
    capacidad = capacidad or assess_capability_360(
        db, organization_id=opportunity.organization_id, dominio=opportunity.dominio,
        riesgo=opportunity.riesgo, costo_estimado=float(opportunity.costo_estimado or 0),
    )
    gate = capacidad.get("human_gate", "REQUIERE_APROBACION")
    lider = None
    if equipo:
        lider = equipo.get("lider") or (equipo.get("equipo") or [{}])[0]
    lider_nombre = lider.get("nombre") if isinstance(lider, dict) else None
    lider_id = lider.get("employee_id") if isinstance(lider, dict) else None

    acciones_por_tipo = {
        "AUTOMATIZACION": "Diseñar e implementar automatización del proceso repetitivo",
        "FINANCIERA": "Ejecutar acción de recuperación financiera prioritaria",
        "CUMPLIMIENTO": "Mitigar riesgo regulatorio con plan de cumplimiento",
        "COMERCIAL": "Activar campaña de conversión con capacidad disponible",
        "RIESGO": "Implementar controles de mitigación de riesgo",
    }
    que = acciones_por_tipo.get(opportunity.tipo, f"Atender oportunidad: {opportunity.titulo}")
    por_que = opportunity.pertinencia_razon or "Priorizada por score global"
    cuando = opportunity.momento or "AHORA"
    quien = lider_nombre or "Equipo IA asignado"
    herramienta = "Orquestador + capacidades asignadas"
    canal = "Centro de operaciones" if gate == "REQUIERE_APROBACION" else "Automatización"
    costo = float(opportunity.costo_estimado or 0)
    autorizacion = gate
    resultado_esperado = f"Materializar valor potencial estimado"
    kpi = _parse_json(opportunity.evidencia_json) or {}
    kpi_objetivo = kpi.get("kpi_objetivo", "mejora_indicador_principal")

    accion = {
        "que": que,
        "por_que": por_que,
        "cuando": cuando,
        "quien": quien,
        "quien_id": lider_id,
        "herramienta": herramienta,
        "canal": canal,
        "costo_estimado": costo,
        "autorizacion": autorizacion,
        "resultado_esperado": resultado_esperado,
        "kpi_objetivo": kpi_objetivo,
        "reevaluar_en_horas": 72,
        "escalar_si": "Sin avance en 7 días o KPI empeora",
        "abandonar_si": "Capacidad no disponible tras 30 días",
        "ejecutable": capacidad.get("ejecutable", False),
    }
    opportunity.siguiente_accion_json = _json(accion)
    return accion


# --- Equipo IA (Orquestador 1010) ---

def select_team_for_opportunity(
    db: Session,
    opportunity: Opportunity,
    *,
    request: str | None = None,
) -> dict[str, Any]:
    from app.services.orchestrator_selection import select_team

    req = request or opportunity.titulo
    ctx = _parse_json(opportunity.contexto_json) or {}
    equipo = select_team(
        db,
        opportunity.organization_id,
        req,
        available_data=ctx.get("datos_disponibles"),
        contexto=ctx.get("componentes", ctx),
        caso_origen_id=opportunity.id,
    )
    opportunity.equipo_json = _json(equipo)
    return equipo


# --- Transiciones de estado ---

def transition_state(
    db: Session,
    opportunity: Opportunity,
    nuevo_estado: str,
    *,
    actor_id: str | None = None,
    motivo: str | None = None,
    evidencia: dict | None = None,
) -> OpportunityTransition:
    if nuevo_estado not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado inválido: {nuevo_estado}")
    anterior = opportunity.estado
    permitidos = TRANSICIONES_PERMITIDAS.get(anterior, set())
    if nuevo_estado not in permitidos and anterior != nuevo_estado:
        raise ValueError(f"Transición no permitida: {anterior} → {nuevo_estado}")

    trans = OpportunityTransition(
        opportunity_id=opportunity.id,
        organization_id=opportunity.organization_id,
        estado_anterior=anterior,
        estado_nuevo=nuevo_estado,
        actor_id=actor_id,
        motivo=motivo,
        evidencia_json=_json(evidencia) if evidencia else None,
    )
    db.add(trans)
    opportunity.estado = nuevo_estado
    opportunity.updated_at = _utcnow()
    if nuevo_estado in ("CERRADA", "MATERIALIZADA", "DESCARTADA", "CANCELADA"):
        opportunity.fecha_cierre = _utcnow()
    add_trace(
        db,
        organization_id=opportunity.organization_id,
        correlation_id=opportunity.correlation_id or _new_correlation(),
        etapa=f"TRANSICION_{nuevo_estado}",
        opportunity_id=opportunity.id,
        detalle={"anterior": anterior, "nuevo": nuevo_estado, "motivo": motivo},
    )
    return trans


# --- Procesar señal → oportunidad ---

def signal_to_opportunity_type(signal: ProactiveSignal, payload: dict) -> str:
    mapping = {
        "automatizacion": "AUTOMATIZACION",
        "conversion": "COMERCIAL",
        "cartera": "FINANCIERA",
        "cumplimiento": "CUMPLIMIENTO",
        "riesgo": "RIESGO",
        "productividad": "PRODUCTIVIDAD",
        "costo": "AHORRO",
    }
    for key, tipo in mapping.items():
        if key in signal.evento.lower() or key in signal.tipo.lower():
            return tipo
    return payload.get("tipo_oportunidad", "OPERATIVA")


def process_signal(
    db: Session,
    signal: ProactiveSignal,
    *,
    user_id: str | None = None,
) -> Opportunity | None:
    if signal.procesada:
        existing = (
            db.query(Opportunity)
            .filter(Opportunity.signal_id == signal.id)
            .first()
        )
        return existing

    payload = _parse_json(signal.payload_json) or {}
    contexto = build_context_360(
        db,
        organization_id=signal.organization_id,
        dominio=signal.dominio,
        payload=payload,
    )

    tipo = signal_to_opportunity_type(signal, payload)
    impacto = payload.get("impacto_estimado")
    valor_potencial = payload.get("valor_potencial")
    certidumbre = "ESTIMADO" if valor_potencial else "NO_CUANTIFICABLE"

    opp = Opportunity(
        organization_id=signal.organization_id,
        codigo=_next_codigo(db, signal.organization_id),
        tipo=tipo,
        dominio=signal.dominio,
        signal_id=signal.id,
        titulo=payload.get("titulo") or f"Oportunidad detectada: {signal.evento}",
        descripcion=payload.get("descripcion"),
        contexto_json=_json(contexto),
        evidencia_json=_json(payload.get("evidencia") or payload),
        impacto_estimado=impacto,
        urgencia=payload.get("urgencia", "MEDIA"),
        riesgo=payload.get("riesgo", "MEDIO"),
        probabilidad=payload.get("probabilidad", 0.6),
        esfuerzo=payload.get("esfuerzo", "MEDIO"),
        costo_estimado=payload.get("costo_estimado"),
        valor_potencial=valor_potencial,
        valor_potencial_certidumbre=certidumbre,
        confianza=float(signal.confianza),
        correlation_id=signal.correlation_id,
        estado="DETECTADA",
    )
    db.add(opp)
    db.flush()

    capacidad = assess_capability_360(
        db, organization_id=signal.organization_id, dominio=signal.dominio,
        riesgo=opp.riesgo, costo_estimado=float(opp.costo_estimado or 0),
    )
    pert = evaluate_pertinence(contexto, impacto=float(impacto or 0), capacidad=capacidad)
    opp.pertinencia = pert["resultado"]
    opp.pertinencia_razon = pert["razon"]

    if pert["resultado"] == "SOLICITAR_DATOS":
        transition_state(db, opp, "DATOS_INSUFICIENTES", motivo=pert["razon"])
    elif pert["resultado"] == "DESCARTAR":
        transition_state(db, opp, "NO_PERTINENTE", motivo=pert["razon"])
    else:
        transition_state(db, opp, "EN_EVALUACION", motivo="Señal procesada")
        momento = evaluate_momento(
            urgencia=opp.urgencia,
            sla_horas=payload.get("sla_horas"),
            tendencia=payload.get("tendencia"),
            capacidad=capacidad,
        )
        opp.momento = momento["resultado"]
        if contexto.get("conflicto"):
            opp.confianza = max(0.1, float(opp.confianza) * 0.5)
        transition_state(db, opp, "PRIORIZADA", motivo="Evaluación completada")

    prioritize_opportunities_global(db, signal.organization_id)
    equipo = select_team_for_opportunity(db, opp)
    compute_next_best_action(db, opp, capacidad=capacidad, equipo=equipo)

    signal.procesada = True
    signal.processed_at = _utcnow()
    add_trace(db, organization_id=signal.organization_id, correlation_id=signal.correlation_id or opp.correlation_id,
              etapa="OPORTUNIDAD_CREADA", opportunity_id=opp.id, signal_id=signal.id,
              detalle={"codigo": opp.codigo, "tipo": opp.tipo, "estado": opp.estado})
    return opp


# --- Activación ---

def activate_opportunity(
    db: Session,
    opportunity: Opportunity,
    *,
    user_id: str,
    auto_execute: bool = False,
) -> dict[str, Any]:
    from app.enums import WorkPlanStatus
    from app.orchestration_models import WorkPlan

    if opportunity.estado not in ("APROBADA", "PRIORIZADA", "PROPUESTA", "EN_EJECUCION", "EN_SEGUIMIENTO"):
        if opportunity.estado == "PENDIENTE_APROBACION":
            raise ValueError("Oportunidad pendiente de aprobación")
        transition_state(db, opportunity, "APROBADA", actor_id=user_id, motivo="Activación directa")

    if opportunity.work_plan_id:
        wp = db.query(WorkPlan).filter(WorkPlan.id == opportunity.work_plan_id).first()
        return {"work_plan_id": opportunity.work_plan_id, "idempotent": True, "work_plan": wp}

    accion = _parse_json(opportunity.siguiente_accion_json) or {}
    prioridad = "ALTA" if opportunity.urgencia in ("ALTA", "CRITICA") else "MEDIA"
    corr = opportunity.correlation_id or _new_correlation()
    wp = WorkPlan(
        organization_id=opportunity.organization_id,
        user_id=user_id,
        correlation_id=corr,
        request=accion.get("que", opportunity.titulo)[:4000],
        objective=f"[OPP] {opportunity.titulo}",
        status=WorkPlanStatus.READY,
        prioridad=prioridad,
        summary=f"Origen oportunidad · {opportunity.codigo}",
    )
    db.add(wp)
    db.flush()
    opportunity.work_plan_id = wp.id
    transition_state(db, opportunity, "EN_EJECUCION", actor_id=user_id, motivo="WorkPlan creado")

    # G-02: registrar valor potencial en FINOPS con work_plan_id
    if opportunity.valor_potencial and float(opportunity.valor_potencial) > 0:
        from app.services.motor_analitico.finops_bridge import register_finops_values
        register_finops_values(
            db,
            organization_id=opportunity.organization_id,
            user_id=user_id,
            analysis_id=opportunity.id,
            estimates=[{
                "beneficio_esperado": float(opportunity.valor_potencial),
                "certidumbre": opportunity.valor_potencial_certidumbre,
                "metodologia": "Valor potencial de oportunidad — no materializado",
                "referencia": opportunity.codigo,
            }],
            work_plan_id=wp.id,
            opportunity_id=opportunity.id,
        )
        opportunity.finops_reference = f"finops:opp:{opportunity.id}"

    tracking = OpportunityTracking(
        opportunity_id=opportunity.id,
        organization_id=opportunity.organization_id,
        accion=accion.get("que", "Seguimiento inicial"),
        responsable_id=user_id,
        kpi_objetivo_json=_json({"kpi": accion.get("kpi_objetivo")}),
        proxima_revision=_utcnow() + timedelta(hours=accion.get("reevaluar_en_horas", 72)),
    )
    db.add(tracking)
    transition_state(db, opportunity, "EN_SEGUIMIENTO", actor_id=user_id, motivo="Seguimiento activo iniciado")
    add_trace(db, organization_id=opportunity.organization_id,
              correlation_id=opportunity.correlation_id or _new_correlation(),
              etapa="ACTIVACION", opportunity_id=opportunity.id,
              detalle={"work_plan_id": wp.id})

    result = {"work_plan_id": wp.id, "opportunity_id": opportunity.id, "auto_execute": auto_execute}
    if auto_execute:
        from app.services.coordinator import execute_plan
        execute_plan(db, wp.id, user_id=user_id)
    return result


# --- Aprobación ---

def approve_opportunity(
    db: Session,
    opportunity: Opportunity,
    *,
    user_id: str,
    aprobado: bool = True,
    motivo: str | None = None,
) -> Opportunity:
    if opportunity.estado not in ("PENDIENTE_APROBACION", "PROPUESTA", "PRIORIZADA"):
        raise ValueError(f"No se puede aprobar desde estado {opportunity.estado}")
    if aprobado:
        transition_state(db, opportunity, "APROBADA", actor_id=user_id, motivo=motivo or "Aprobada")
    else:
        transition_state(db, opportunity, "DESCARTADA", actor_id=user_id, motivo=motivo or "Rechazada")
    return opportunity


# --- Resultado y valor materializado ---

def register_result(
    db: Session,
    opportunity: Opportunity,
    *,
    user_id: str,
    valor_real: float | None = None,
    valor_esperado: float | None = None,
    evidencia: dict | None = None,
    estado_resultado: str = "EXITO",
) -> dict[str, Any]:
    valor_esp = valor_esperado or float(opportunity.valor_potencial or 0)
    valor_mat = valor_real
    diferencia = (valor_mat - valor_esp) if valor_mat is not None and valor_esp else None

    resultado = {
        "valor_esperado": valor_esp,
        "valor_real": valor_mat,
        "diferencia": diferencia,
        "evidencia": evidencia,
        "estado": estado_resultado,
        "fecha": _utcnow().isoformat(),
        "confianza": 0.8 if evidencia else 0.5,
    }
    opportunity.resultado_json = _json(resultado)
    if valor_mat is not None:
        opportunity.valor_materializado = Decimal(str(round(valor_mat, 2)))
        from app.services.finops_service import registrar_valor
        registrar_valor(
            db,
            organization_id=opportunity.organization_id,
            user_id=user_id,
            work_plan_id=opportunity.work_plan_id,
            opportunity_id=opportunity.id,
            value_type="valor_materializado",
            certainty="Real",
            amount=Decimal(str(round(valor_mat, 2))),
            currency="COP",
            methodology="Valor materializado post-ejecución",
            source=f"oportunidad:{opportunity.id}",
            notes=opportunity.codigo,
        )

    atribucion = _compute_attribution(opportunity, resultado)
    opportunity.atribucion_nivel = atribucion["nivel"]
    opportunity.atribucion_razon = atribucion["razon"]

    transition_state(db, opportunity, "MATERIALIZADA", actor_id=user_id, motivo="Resultado registrado")
    register_opportunity_learning(db, opportunity, user_id=user_id, resultado=resultado)
    add_trace(db, organization_id=opportunity.organization_id,
              correlation_id=opportunity.correlation_id or _new_correlation(),
              etapa="RESULTADO", opportunity_id=opportunity.id, detalle=resultado)
    return resultado


def _compute_attribution(opportunity: Opportunity, resultado: dict) -> dict[str, str]:
    if not resultado.get("valor_real"):
        return {"nivel": "NO_ATRIBUIBLE", "razon": "Sin valor real comprobado", "confianza": "0.3"}
    if opportunity.work_plan_id and resultado.get("evidencia"):
        return {"nivel": "ATRIBUIBLE", "razon": "WorkPlan ejecutado con evidencia de resultado", "confianza": "0.75"}
    if opportunity.work_plan_id:
        return {"nivel": "PARCIALMENTE_ATRIBUIBLE", "razon": "WorkPlan ejecutado sin evidencia completa", "confianza": "0.55"}
    return {"nivel": "INFLUENCIADO", "razon": "Oportunidad gestionada sin ejecución directa", "confianza": "0.4"}


def register_opportunity_learning(
    db: Session,
    opportunity: Opportunity,
    *,
    user_id: str,
    resultado: dict,
) -> None:
    from app.services.experience_core import crear_experiencia, actualizar_resultado_experiencia

    equipo = _parse_json(opportunity.equipo_json) or {}
    lider = equipo.get("lider") or {}
    employee_id = lider.get("employee_id") if isinstance(lider, dict) else None
    if not employee_id:
        return
    record = crear_experiencia(
        db,
        opportunity.organization_id,
        employee_id=employee_id,
        dominio=opportunity.dominio,
        tipo_problema=opportunity.tipo,
        contexto={"titulo": opportunity.titulo},
        accion=(_parse_json(opportunity.siguiente_accion_json) or {}).get("que"),
        resultado_esperado=str(resultado.get("valor_esperado")),
        work_plan_id=opportunity.work_plan_id,
        caso_origen_id=opportunity.id,
    )
    if resultado.get("valor_real") is not None:
        actualizar_resultado_experiencia(
            db,
            opportunity.organization_id,
            record.id,
            resultado_real=str(resultado.get("valor_real")),
            estado=resultado.get("estado", "EXITO"),
            valor_obtenido=resultado.get("valor_real"),
        )


# --- Resumen negocio ---

def business_summary(db: Session, organization_id: str) -> dict[str, Any]:
    total = db.query(func.count(Opportunity.id)).filter(Opportunity.organization_id == organization_id).scalar() or 0
    pertinentes = db.query(func.count(Opportunity.id)).filter(
        Opportunity.organization_id == organization_id,
        Opportunity.pertinencia == "ACTUAR",
    ).scalar() or 0
    activadas = db.query(func.count(Opportunity.id)).filter(
        Opportunity.organization_id == organization_id,
        Opportunity.work_plan_id.isnot(None),
    ).scalar() or 0
    materializadas = db.query(func.count(Opportunity.id)).filter(
        Opportunity.organization_id == organization_id,
        Opportunity.estado == "MATERIALIZADA",
    ).scalar() or 0
    valor_pot = db.query(func.sum(Opportunity.valor_potencial)).filter(
        Opportunity.organization_id == organization_id,
    ).scalar() or 0
    valor_mat = db.query(func.sum(Opportunity.valor_materializado)).filter(
        Opportunity.organization_id == organization_id,
    ).scalar() or 0
    pendientes_aprob = db.query(func.count(Opportunity.id)).filter(
        Opportunity.organization_id == organization_id,
        Opportunity.estado == "PENDIENTE_APROBACION",
    ).scalar() or 0
    return {
        "oportunidades_detectadas": total,
        "pertinentes": pertinentes,
        "activadas": activadas,
        "materializadas": materializadas,
        "valor_potencial_total": float(valor_pot or 0),
        "valor_materializado_total": float(valor_mat or 0),
        "pendientes_aprobacion": pendientes_aprob,
    }


# --- Trazabilidad completa ---

def get_full_trace(db: Session, opportunity_id: str, organization_id: str) -> dict[str, Any]:
    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.organization_id == organization_id,
    ).first()
    if not opp:
        return {}
    traces = (
        db.query(OpportunityTrace)
        .filter(OpportunityTrace.correlation_id == opp.correlation_id)
        .order_by(OpportunityTrace.created_at)
        .all()
    )
    transitions = (
        db.query(OpportunityTransition)
        .filter(OpportunityTransition.opportunity_id == opportunity_id)
        .order_by(OpportunityTransition.created_at)
        .all()
    )
    tracking = (
        db.query(OpportunityTracking)
        .filter(OpportunityTracking.opportunity_id == opportunity_id)
        .order_by(OpportunityTracking.created_at)
        .all()
    )
    return {
        "opportunity_id": opportunity_id,
        "correlation_id": opp.correlation_id,
        "estado": opp.estado,
        "trazas": [{"etapa": t.etapa, "detalle": _parse_json(t.detalle_json), "fecha": t.created_at.isoformat()} for t in traces],
        "transiciones": [{"de": t.estado_anterior, "a": t.estado_nuevo, "motivo": t.motivo} for t in transitions],
        "seguimiento": [{"accion": t.accion, "resultado": t.resultado} for t in tracking],
    }


# --- Flujo proactivo completo ---

def run_proactive_pipeline(
    db: Session,
    *,
    organization_id: str,
    tipo: str,
    dominio: str,
    evento: str,
    payload: dict | None = None,
    origen: str = "scheduler",
    user_id: str | None = None,
) -> dict[str, Any]:
    """Pipeline proactivo sin prompt humano."""
    signal, is_new = create_signal(
        db,
        organization_id=organization_id,
        tipo=tipo,
        dominio=dominio,
        origen=origen,
        evento=evento,
        payload=payload,
        severidad=payload.get("severidad", "MEDIA") if payload else "MEDIA",
        confianza=payload.get("confianza", 0.7) if payload else 0.7,
        source_reference=payload.get("source_reference") if payload else None,
    )
    if not is_new:
        opp = db.query(Opportunity).filter(Opportunity.signal_id == signal.id).first()
        return {"signal_id": signal.id, "opportunity_id": opp.id if opp else None, "deduplicated": True}

    opp = process_signal(db, signal, user_id=user_id)
    if not opp:
        return {"signal_id": signal.id, "opportunity_id": None}

    capacidad = assess_capability_360(db, organization_id=organization_id, dominio=dominio)
    accion = _parse_json(opp.siguiente_accion_json) or {}
    gate = accion.get("autorizacion", "REQUIERE_APROBACION")

    if gate == "AUTOMATICA_PERMITIDA" and opp.estado == "PRIORIZADA":
        transition_state(db, opp, "APROBADA", motivo="Política automática")
        activate_opportunity(db, opp, user_id=user_id or "", auto_execute=False)
    elif gate == "REQUIERE_APROBACION" and opp.estado == "PRIORIZADA":
        transition_state(db, opp, "PENDIENTE_APROBACION", motivo="Requiere aprobación humana")

    return {
        "signal_id": signal.id,
        "opportunity_id": opp.id,
        "codigo": opp.codigo,
        "estado": opp.estado,
        "pertinencia": opp.pertinencia,
        "prioridad_score": float(opp.prioridad_score or 0),
        "siguiente_accion": accion,
        "capacidad": capacidad,
        "deduplicated": False,
    }
