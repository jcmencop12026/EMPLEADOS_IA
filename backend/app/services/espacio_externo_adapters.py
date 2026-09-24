"""Adaptadores — reutilizan servicios existentes y sanitizan salida externa."""

from __future__ import annotations

from typing import Any


def adaptar_implementacion_externa(tablero: dict[str, Any], detalle: dict[str, Any] | None = None) -> dict[str, Any]:
    """Implementación autorizada — sin economía interna ni riesgos no publicados."""
    proyecto = tablero.get("proyecto") or {}
    traz = tablero.get("trazabilidad") or {}
    hitos_raw = (detalle or {}).get("hitos") or []
    entregables = [
        {
            "codigo": h.get("codigo"),
            "nombre": h.get("nombre"),
            "estado": h.get("estado"),
        }
        for h in hitos_raw
    ]
    bloqueadores = tablero.get("bloqueadores") or []
    dependencias_cliente = [
        {
            "descripcion": b.get("descripcion") or b.get("titulo"),
            "estado": b.get("estado"),
            "fecha_limite": b.get("fecha_limite"),
        }
        for b in bloqueadores
        if (b.get("tipo") or "").upper() in ("CLIENTE", "DEPENDENCIA_CLIENTE", "EXTERNO")
        or b.get("responsable") == "CLIENTE"
    ]
    return {
        "alcance_contratado": traz.get("que_prometimos") or proyecto.get("alcance"),
        "objetivos": proyecto.get("objetivos"),
        "estado": proyecto.get("estado"),
        "fase_actual": tablero.get("fase_actual"),
        "avance_pct": tablero.get("avance_pct"),
        "hitos": tablero.get("hitos"),
        "entregables": entregables,
        "dependencias_cliente": dependencias_cliente,
        "pendientes": [
            b.get("descripcion") or b.get("titulo")
            for b in bloqueadores
            if (b.get("estado") or "").upper() == "ABIERTO"
        ],
        "fechas": {
            "inicio": proyecto.get("fecha_inicio"),
            "objetivo": proyecto.get("fecha_objetivo"),
            "go_live": proyecto.get("go_live_fecha"),
        },
        "go_live_aprobado": proyecto.get("go_live_aprobado"),
        "alertas": [
            {"tipo": a.get("tipo"), "mensaje": a.get("mensaje")}
            for a in (tablero.get("alertas") or [])
            if not a.get("interno")
        ],
    }


def adaptar_empleados_ia_externo(employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Empleados IA — sin prompts, secretos ni configuración propietaria."""
    out: list[dict[str, Any]] = []
    for emp in employees:
        out.append({
            "id": emp.get("id"),
            "nombre": emp.get("name"),
            "proposito": emp.get("objective") or emp.get("description") or emp.get("specialty"),
            "estado": emp.get("lifecycle_status") or emp.get("status"),
            "capacidades_funcionales": emp.get("capabilities") or [],
            "certificacion": emp.get("last_certification"),
            "actividad_relevante": {
                "certificacion_at": emp.get("last_certification_at"),
                "maturity": emp.get("maturity"),
            },
        })
    return out


def adaptar_empleado_ia_detalle_externo(detail: dict[str, Any]) -> dict[str, Any]:
    base = adaptar_empleados_ia_externo([detail])[0]
    base["consumo_permitido"] = detail.get("consumo_permitido")
    return base


def adaptar_resultados_externo(vista: dict[str, Any]) -> dict[str, Any]:
    """ANTES / PROYECTADO / REAL — POTENCIAL nunca como realizado."""
    safe = dict(vista)
    safe.pop("notas_internas", None)
    safe.pop("valor_potencial", None)
    safe.pop("costos", None)
    safe.pop("margen", None)
    safe.pop("prompts", None)
    oportunidades = []
    for opp in safe.get("oportunidades") or []:
        oportunidades.append({
            "codigo": opp.get("codigo"),
            "titulo": opp.get("titulo"),
            "estado": opp.get("estado"),
            "tipo": "POTENCIAL",
            "nota": "POTENCIAL no equivale a resultado realizado",
        })
    safe["oportunidades"] = oportunidades
    impacto = safe.get("impacto") or {}
    if isinstance(impacto, dict):
        impacto = dict(impacto)
        impacto.pop("valor_potencial", None)
        indicadores = []
        for ind in impacto.get("indicadores") or []:
            indicadores.append({
                "hallazgo": ind.get("hallazgo"),
                "antes": ind.get("antes"),
                "proyectado": ind.get("proyectado"),
                "real": ind.get("real"),
                "etiqueta_proyeccion": ind.get("etiqueta_proyeccion"),
                "confianza": ind.get("confianza"),
            })
        impacto["indicadores"] = indicadores
        safe["impacto"] = impacto
    return safe


def adaptar_informes_externo(messages: list[dict[str, Any]], *, audiencia: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for msg in messages:
        out.append({
            "id": msg.get("id"),
            "nombre": msg.get("asunto"),
            "periodo": msg.get("origen_id"),
            "audiencia": audiencia or msg.get("audiencia"),
            "fecha": msg.get("enviada_at") or msg.get("created_at"),
            "estado": msg.get("estado"),
            "descarga_disponible": msg.get("estado") in ("ENVIADA", "ENTREGADA"),
        })
    return out


def adaptar_informe_detalle_externo(detail: dict[str, Any], *, audiencia: str | None = None) -> dict[str, Any]:
    base = adaptar_informes_externo([detail], audiencia=audiencia)[0]
    base["contenido"] = detail.get("contenido")
    return base


def adaptar_soporte_lista_externa(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": c.get("id"),
            "numero": c.get("numero"),
            "asunto": c.get("asunto"),
            "tipo": c.get("tipo"),
            "estado": c.get("estado"),
            "prioridad": c.get("prioridad"),
            "sla_estado": c.get("sla_estado"),
            "created_at": c.get("created_at"),
            "resolucion": c.get("resolucion") if c.get("estado") in ("RESUELTO", "CERRADO") else None,
        }
        for c in cases
    ]


def adaptar_soporte_caso_externo(detail: dict[str, Any]) -> dict[str, Any]:
    comentarios = [
        {
            "id": c.get("id"),
            "cuerpo": c.get("cuerpo"),
            "evidencia_ref": c.get("evidencia_ref"),
            "created_at": c.get("created_at"),
        }
        for c in (detail.get("comentarios") or [])
        if not c.get("es_interno")
    ]
    return {
        "id": detail.get("id"),
        "numero": detail.get("numero"),
        "asunto": detail.get("asunto"),
        "descripcion": detail.get("descripcion"),
        "tipo": detail.get("tipo"),
        "estado": detail.get("estado"),
        "prioridad": detail.get("prioridad"),
        "sla_estado": detail.get("sla_estado"),
        "resolucion": detail.get("resolucion"),
        "comentarios": comentarios,
        "created_at": detail.get("created_at"),
        "updated_at": detail.get("updated_at"),
    }
