"""Servicio compartido — Presentación ejecutiva DEMO y REAL (V1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.demo_comercial_constants import AUDIENCIAS, DEMO_EMPRESA_FICTICIA, DEMO_PROBLEMA
from app.evaluacion_models import EvaluacionExpediente
from app.services import evaluacion_service as ev_svc
from app.services import resultados_service as res_svc
from app.services.presentacion_publicacion_adapter import (
    PublicacionDenegadaError,
    assert_puede_ver_presentacion_real,
    is_demo_expediente,
)
from app.services.presentacion_pdf_service import render_presentacion_pdf


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _filter_indicadores_publicables(indicadores: list[dict[str, Any]], *, es_demo: bool) -> list[dict[str, Any]]:
    if es_demo:
        return indicadores
    return [i for i in indicadores if i.get("visible_entidad")]


def build_presentacion_core(
    db: Session,
    organization_id: str,
    exp: EvaluacionExpediente,
    *,
    audiencia: str,
    es_demo: bool,
) -> dict[str, Any]:
    audiencia = audiencia.upper()
    if audiencia not in AUDIENCIAS:
        raise ValueError(f"Audiencia no válida: {audiencia}")

    vista = ev_svc.get_vista_entidad(db, exp.id, organization_id)
    apr_raw = res_svc.build_antes_proyectado_real(db, organization_id, expediente_id=exp.id)
    indicadores = _filter_indicadores_publicables(apr_raw.get("indicadores", []), es_demo=es_demo)
    informes = res_svc.list_informes(db, organization_id, expediente_id=exp.id)
    informe = informes[0] if informes else None

    empresa = DEMO_EMPRESA_FICTICIA if es_demo else exp.entidad_nombre
    etiqueta = "DEMO — DATOS SIMULADOS" if es_demo else "PRESENTACIÓN EJECUTIVA"

    base: dict[str, Any] = {
        "es_demo": es_demo,
        "etiqueta": etiqueta,
        "audiencia": audiencia,
        "empresa": empresa,
        "expediente_id": exp.id,
        "expediente_codigo": exp.codigo,
        "fecha": _utcnow().strftime("%Y-%m-%d"),
        "version": informe.get("version", 1) if informe else 1,
        "secciones": [],
        "indicadores": indicadores,
        "graficos": _build_graficos_payload(indicadores, es_demo=es_demo),
        "oportunidades": vista.get("oportunidades", []),
    }

    que_encontramos = [h.get("titulo") for h in vista.get("hallazgos", []) if h.get("titulo")]

    if audiencia == "GERENCIA":
        base["secciones"] = [
            {
                "titulo": "Qué encontramos",
                "contenido": que_encontramos or ["Oportunidades de mejora identificadas en la evaluación"],
            },
            {
                "titulo": "Por qué importa",
                "contenido": [exp.necesidad or exp.objetivo or "Impacto operativo y financiero relevante"],
            },
            {
                "titulo": "Cuánto puede representar",
                "contenido": _lineas_impacto(indicadores, es_demo),
            },
            {
                "titulo": "Qué proponemos a alto nivel",
                "contenido": _propuesta_alto_nivel(vista, es_demo),
            },
            {
                "titulo": "Qué sigue",
                "contenido": [
                    "Validación con datos adicionales de su organización",
                    "Piloto acotado con métricas ANTES / PROYECTADO / REAL",
                ],
            },
        ]
    elif audiencia == "OPERACION":
        base["secciones"] = [
            {"titulo": "Procesos afectados", "contenido": [exp.area_proceso or "Procesos evaluados"]},
            {"titulo": "Hallazgos operativos", "contenido": que_encontramos or ["Sin hallazgos visibles"]},
            {
                "titulo": "Indicadores clave",
                "contenido": [
                    f"{i['nombre']}: ANTES {i['antes']} → REAL {i.get('real', 'pendiente')} {i.get('unidad', '')}"
                    for i in indicadores[:5]
                ],
            },
            {"titulo": "Acciones sugeridas", "contenido": _acciones_sugeridas(vista)},
        ]
    elif audiencia == "SISTEMAS":
        base["secciones"] = [
            {
                "titulo": "Capacidades EIAAX involucradas",
                "contenido": [
                    "Empleados IA especializados (sin exponer prompts ni reglas)",
                    "Integraciones y automatizaciones existentes",
                    "Trazabilidad y auditoría de ejecuciones",
                ],
            },
            {
                "titulo": "Datos y evidencias",
                "contenido": ["Referencias a ejecuciones y logs — sin configuración interna"],
            },
            {"titulo": "Próximos pasos técnicos", "contenido": ["Conector a fuentes reales", "Ambiente piloto aislado"]},
        ]
    else:
        lineas_fin = []
        for i in indicadores:
            lineas_fin.append(
                f"{i['nombre']}: ANTES {i['antes']} | PROY. {i['proyectado']} | REAL {i.get('real', '—')} {i.get('unidad', '')}"
            )
        base["secciones"] = [
            {
                "titulo": "Impacto cuantificado",
                "contenido": lineas_fin or ["Sin indicadores publicables"],
            },
            {
                "titulo": "Nota metodológica",
                "contenido": [
                    "PROYECTADO es escenario esperado, no resultado conseguido",
                    "REAL requiere evidencia registrada posterior",
                ],
            },
            {
                "titulo": "Valor potencial",
                "contenido": [
                    "Estimación orientativa — no compromiso contractual"
                    if not es_demo
                    else "Simulación demo — no compromiso contractual"
                ],
            },
        ]

    if informe and (es_demo or informe.get("visibilidad") == "VISIBLE_ENTIDAD"):
        base["informe_resumen"] = {
            "titulo": informe.get("titulo"),
            "version": informe.get("version"),
            "visibilidad": informe.get("visibilidad"),
        }

    base["proteccion_ip"] = {
        "oculto": [
            "prompts",
            "reglas detalladas",
            "algoritmos internos",
            "mapeos",
            "configuraciones",
            "código",
            "arquitectura reproducible",
            "margen interno",
            "costos internos",
        ]
    }
    return base


def _lineas_impacto(indicadores: list[dict[str, Any]], es_demo: bool) -> list[str]:
    con_real = [i for i in indicadores if i.get("real") is not None]
    prefijo = "demo" if es_demo else "evaluación"
    lineas = [
        f"{len(con_real)} indicador(es) con mejora REAL medida en {prefijo}",
        "Proyecciones no equivalen a resultados garantizados",
    ]
    return lineas


def _propuesta_alto_nivel(vista: dict[str, Any], es_demo: bool) -> list[str]:
    opps = vista.get("oportunidades") or []
    if opps:
        return [o.get("titulo", "Oportunidad") for o in opps[:3]]
    if es_demo:
        return [
            "Empleados IA para codificación y seguimiento de glosas",
            "Automatización de reprocesos y tablero ejecutivo",
        ]
    return ["Plan de mejoramiento basado en hallazgos publicados"]


def _acciones_sugeridas(vista: dict[str, Any]) -> list[str]:
    opps = vista.get("oportunidades") or []
    if opps:
        return [f"Priorizar: {o.get('titulo', 'oportunidad')}" for o in opps[:3]]
    return ["Revisar hallazgos con equipos responsables"]


def _build_graficos_payload(indicadores: list[dict[str, Any]], *, es_demo: bool) -> dict[str, Any]:
    series = []
    for ind in indicadores[:6]:
        series.append({
            "nombre": ind["nombre"],
            "unidad": ind.get("unidad", ""),
            "antes": ind.get("antes"),
            "proyectado": ind.get("proyectado"),
            "real": ind.get("real"),
            "simulado": es_demo,
            "periodo": ind.get("periodo"),
        })
    return {
        "tipo": "antes_proyectado_real",
        "nota": "PROYECTADO no es resultado conseguido",
        "series": series,
        "adapter_centro_control": "reutiliza_datos_resultados_v1",
    }


def build_presentacion_demo(
    db: Session,
    organization_id: str,
    expediente_id: str,
    *,
    audiencia: str,
) -> dict[str, Any]:
    exp = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.id == expediente_id,
            EvaluacionExpediente.organization_id == organization_id,
        )
        .first()
    )
    if not exp:
        raise LookupError("Expediente no encontrado.")
    if not is_demo_expediente(exp):
        raise PermissionError("La presentación demo solo aplica a expedientes marcados como DEMO.")
    return build_presentacion_core(db, organization_id, exp, audiencia=audiencia, es_demo=True)


def build_presentacion_real(
    db: Session,
    organization_id: str,
    expediente_id: str,
    user,
    *,
    audiencia: str,
) -> dict[str, Any]:
    exp = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.id == expediente_id,
            EvaluacionExpediente.organization_id == organization_id,
        )
        .first()
    )
    if not exp:
        raise LookupError("Expediente no encontrado.")
    pub = assert_puede_ver_presentacion_real(db, organization_id, exp, user)
    data = build_presentacion_core(db, organization_id, exp, audiencia=audiencia, es_demo=False)
    data["publicacion"] = pub
    return data


def build_presentacion_pdf(
    db: Session,
    organization_id: str,
    expediente_id: str,
    user,
    *,
    audiencia: str,
    es_demo: bool,
) -> tuple[bytes, str]:
    if es_demo:
        data = build_presentacion_demo(db, organization_id, expediente_id, audiencia=audiencia)
    else:
        data = build_presentacion_real(db, organization_id, expediente_id, user, audiencia=audiencia)
    pdf_bytes = render_presentacion_pdf(data)
    slug = data.get("expediente_codigo", expediente_id[:8])
    filename = f"EIAAX-presentacion-{slug}-{audiencia.lower()}.pdf"
    return pdf_bytes, filename
