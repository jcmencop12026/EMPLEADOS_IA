"""Servicio — Demo comercial ficticia EIAAX (V1)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.demo_comercial_constants import (
    AUDIENCIAS,
    DEMO_AREAS,
    DEMO_CORRELATION_PREFIX,
    DEMO_EMPRESA_FICTICIA,
    DEMO_ENTIDAD_PREFIX,
    DEMO_PROBLEMA,
    INFORMES_PERIODICIDAD,
)
from app.evaluacion_models import EvaluacionExpediente
from app.resultados_models import ResultadoInformeImpacto
from app.services import baseline_service as baseline_svc
from app.services import evaluacion_service as ev_svc
from app.services import resultados_service as res_svc


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_demo_expediente(exp: EvaluacionExpediente) -> bool:
    if exp.correlation_id and exp.correlation_id.startswith(DEMO_CORRELATION_PREFIX):
        return True
    return exp.entidad_nombre.startswith(DEMO_ENTIDAD_PREFIX)


def _demo_entidad_label() -> str:
    return f"{DEMO_ENTIDAD_PREFIX} {DEMO_EMPRESA_FICTICIA}"


def seed_demo_comercial(db: Session, organization_id: str, user_id: str) -> dict[str, Any]:
    """Semilla unificada — datos ficticios aislados por correlation_id DEMO."""
    existing = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.organization_id == organization_id,
            EvaluacionExpediente.correlation_id.like(f"{DEMO_CORRELATION_PREFIX}%"),
        )
        .first()
    )
    if existing:
        informe = (
            db.query(ResultadoInformeImpacto)
            .filter(
                ResultadoInformeImpacto.expediente_id == existing.id,
                ResultadoInformeImpacto.organization_id == organization_id,
            )
            .order_by(ResultadoInformeImpacto.created_at.desc())
            .first()
        )
        return _manifest_from_expediente(existing, informe.id if informe else None, reused=True)

    now = _utcnow()
    exp = ev_svc.create_expediente(
        db,
        organization_id=organization_id,
        user_id=user_id,
        titulo="Evaluación preliminar — Demo comercial",
        entidad_nombre=_demo_entidad_label(),
        necesidad=DEMO_PROBLEMA,
        objetivo="Reducir glosas, acelerar respuesta y demostrar valor con Empleados IA",
        area_proceso="Salud / Facturación y cartera",
        nivel="PRELIMINAR",
    )
    exp.correlation_id = f"{DEMO_CORRELATION_PREFIX}-{exp.id[:8]}"
    exp.estado = "PRELIMINAR"
    exp.porcentaje_informacion = 78
    exp.confianza_global = "MEDIA"
    db.flush()

    hallazgos_demo = [
        ("Glosas por codificación incorrecta", "HECHO", True),
        ("Reprocesos manuales en facturación", "HECHO", True),
        ("Oportunidad de automatización con Empleado IA", "RECOMENDACION", True),
        ("Nota interna de calibración", "INFERENCIA", False),
    ]
    for titulo, tipo, visible in hallazgos_demo:
        ev_svc.create_hallazgo(
            db,
            exp.id,
            organization_id,
            user_id=user_id,
            titulo=titulo,
            descripcion=f"Hallazgo demo: {titulo}",
            tipo_contenido=tipo,
            confianza="MEDIA",
            visible_entidad=visible,
        )

    lb = baseline_svc.create_linea_base(
        db,
        organization_id=organization_id,
        user_id=user_id,
        indicador="tasa_glosas",
        descripcion="Porcentaje de facturas con glosa (demo)",
        unidad="%",
        valor_base=19.5,
        fecha_inicio_base=now - timedelta(days=120),
        fecha_fin_base=now - timedelta(days=90),
        impacto_esperado=10.0,
        proceso="Facturación",
    )
    res_svc.sync_indicador_from_linea_base(db, lb.id, organization_id)

    ind = res_svc.create_indicador(
        db,
        organization_id,
        nombre="Días respuesta glosa",
        unidad="días",
        valor_antes=16.0,
        valor_proyectado=7.0,
        expediente_id=exp.id,
        proceso="Facturación",
        periodo="2026-Q1",
        tipo_analitica="COMPARATIVA",
    )
    res_svc.register_medicion_real(
        db, ind["id"], organization_id, valor_real=9.5, evidencia_ref="demo:informe-marzo-2026"
    )
    ind2 = res_svc.create_indicador(
        db,
        organization_id,
        nombre="Recuperación cartera glosada",
        unidad="%",
        valor_antes=58.0,
        valor_proyectado=82.0,
        expediente_id=exp.id,
    )
    res_svc.register_medicion_real(
        db, ind2["id"], organization_id, valor_real=69.0, evidencia_ref="demo:cierre-Q1"
    )
    res_svc.create_indicador(
        db,
        organization_id,
        nombre="Horas reproceso manual",
        unidad="h/mes",
        valor_antes=320.0,
        valor_proyectado=120.0,
        expediente_id=exp.id,
    )

    res_svc.create_plan_accion(
        db,
        organization_id,
        expediente_id=exp.id,
        accion="Capacitación codificación CUPS + reglas Empleado IA",
        indicador_id=ind["id"],
        causa="Errores recurrentes en codificación",
    )

    informe = res_svc.generate_informe_impacto(
        db, organization_id, user_id, expediente_id=exp.id, visibilidad="VISIBLE_ENTIDAD"
    )
    db.commit()
    db.refresh(exp)
    return _manifest_from_expediente(exp, informe["id"], reused=False)


def _manifest_from_expediente(
    exp: EvaluacionExpediente,
    informe_id: str | None,
    *,
    reused: bool,
) -> dict[str, Any]:
    return {
        "es_demo": True,
        "etiqueta": "DEMO — DATOS SIMULADOS",
        "empresa_ficticia": DEMO_EMPRESA_FICTICIA,
        "problema": DEMO_PROBLEMA,
        "expediente_id": exp.id,
        "expediente_codigo": exp.codigo,
        "informe_id": informe_id,
        "areas": [{"id": a, "label": l} for a, l in DEMO_AREAS],
        "enlaces": {
            "hub": "/demo",
            "evaluacion": f"/evaluaciones/{exp.id}",
            "vista_entidad": f"/evaluaciones/{exp.id}?tab=vista-entidad",
            "resultados": f"/resultados?expediente_id={exp.id}",
            "informe": f"/resultados/informes/{informe_id}" if informe_id else None,
            "presentacion": f"/demo/presentacion/{exp.id}",
            "diagnostico_ips": "/salud/diagnostico",
            "centro_control": "/",
            "comercial": "/comercial",
            "evaluar_real": "/evaluaciones?nuevo=1",
        },
        "reused": reused,
    }


def get_manifest(db: Session, organization_id: str) -> dict[str, Any]:
    exp = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.organization_id == organization_id,
            EvaluacionExpediente.correlation_id.like(f"{DEMO_CORRELATION_PREFIX}%"),
        )
        .order_by(EvaluacionExpediente.created_at.desc())
        .first()
    )
    if not exp:
        return {
            "es_demo": True,
            "etiqueta": "DEMO — DATOS SIMULADOS",
            "semilla_disponible": True,
            "empresa_ficticia": DEMO_EMPRESA_FICTICIA,
            "problema": DEMO_PROBLEMA,
            "areas": [{"id": a, "label": l} for a, l in DEMO_AREAS],
            "enlaces": {
                "hub": "/demo",
                "diagnostico_ips": "/salud/diagnostico",
                "evaluar_real": "/evaluaciones?nuevo=1",
            },
        }
    informe = (
        db.query(ResultadoInformeImpacto)
        .filter(
            ResultadoInformeImpacto.expediente_id == exp.id,
            ResultadoInformeImpacto.organization_id == organization_id,
        )
        .order_by(ResultadoInformeImpacto.created_at.desc())
        .first()
    )
    return _manifest_from_expediente(exp, informe.id if informe else None, reused=True)


def build_presentacion(
    db: Session,
    organization_id: str,
    expediente_id: str,
    *,
    audiencia: str,
) -> dict[str, Any]:
    """Presentación ejecutiva por audiencia — sin exponer IP interna."""
    audiencia = audiencia.upper()
    if audiencia not in AUDIENCIAS:
        raise ValueError(f"Audiencia no válida: {audiencia}")
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
    if not _is_demo_expediente(exp):
        raise PermissionError("La presentación demo solo aplica a expedientes marcados como DEMO.")

    vista = ev_svc.get_vista_entidad(db, expediente_id, organization_id)
    apr = res_svc.build_antes_proyectado_real(db, organization_id, expediente_id=expediente_id)
    informes = res_svc.list_informes(db, organization_id, expediente_id=expediente_id)
    informe = informes[0] if informes else None

    base = {
        "etiqueta": "DEMO — DATOS SIMULADOS",
        "audiencia": audiencia,
        "empresa": DEMO_EMPRESA_FICTICIA,
        "expediente_codigo": exp.codigo,
        "secciones": [],
    }

    que_encontramos = [h.get("titulo") for h in vista.get("hallazgos", []) if h.get("titulo")]
    indicadores = apr.get("indicadores", [])

    if audiencia == "GERENCIA":
        base["secciones"] = [
            {
                "titulo": "Qué encontramos",
                "contenido": que_encontramos or ["Oportunidades de mejora en facturación y glosas"],
            },
            {
                "titulo": "Por qué importa",
                "contenido": [exp.necesidad or DEMO_PROBLEMA],
            },
            {
                "titulo": "Cuánto podría representar",
                "contenido": [
                    f"{len([i for i in indicadores if i.get('real') is not None])} indicador(es) con mejora REAL medida en demo",
                    "Proyecciones no equivalen a resultados garantizados",
                ],
            },
            {
                "titulo": "Qué proponemos a alto nivel",
                "contenido": [
                    "Empleados IA para codificación y seguimiento de glosas",
                    "Automatización de reprocesos y tablero ejecutivo",
                ],
            },
            {
                "titulo": "Qué sigue",
                "contenido": [
                    "Evaluación con datos reales de su organización",
                    "Piloto acotado con métricas ANTES / PROYECTADO / REAL",
                ],
            },
        ]
    elif audiencia == "OPERACION":
        base["secciones"] = [
            {"titulo": "Procesos afectados", "contenido": [exp.area_proceso or "Facturación IPS"]},
            {"titulo": "Hallazgos operativos", "contenido": que_encontramos},
            {
                "titulo": "Indicadores clave",
                "contenido": [
                    f"{i['nombre']}: ANTES {i['antes']} → REAL {i.get('real', 'pendiente')} {i.get('unidad', '')}"
                    for i in indicadores[:5]
                ],
            },
            {"titulo": "Acciones sugeridas", "contenido": ["Capacitación CUPS", "Reglas de validación previa"]},
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
            {"titulo": "Datos y evidencias", "contenido": ["Referencias a ejecuciones y logs — no copia de configuración interna"]},
            {"titulo": "Próximos pasos técnicos", "contenido": ["Conector a fuentes reales", "Ambiente piloto aislado"]},
        ]
    else:  # FINANCIERO
        lineas_fin = []
        for i in indicadores:
            lineas_fin.append(
                f"{i['nombre']}: ANTES {i['antes']} | PROY. {i['proyectado']} | REAL {i.get('real', '—')} {i.get('unidad', '')}"
            )
        base["secciones"] = [
            {"titulo": "Impacto cuantificado (demo)", "contenido": lineas_fin or ["Sin indicadores"]},
            {
                "titulo": "Nota metodológica",
                "contenido": [
                    "PROYECTADO es escenario esperado, no resultado conseguido",
                    "REAL requiere evidencia registrada posterior",
                ],
            },
            {"titulo": "Valor potencial", "contenido": ["Simulación disponible en Comercial y valor — no compromiso contractual"]},
        ]

    if informe:
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
        ]
    }
    return base


def informes_periodicos_plantillas() -> list[dict[str, Any]]:
    """Plantillas de informes periódicos — configuración conceptual reutilizable."""
    return [
        {
            "periodicidad": p,
            "audiencias": list(AUDIENCIAS),
            "canal": "CORREO_ELECTRONICO",
            "contenido_email": "Resumen ejecutivo + enlace seguro al informe completo",
            "sensible": p in ("MENSUAL", "TRIMESTRAL"),
        }
        for p in INFORMES_PERIODICIDAD
    ]
