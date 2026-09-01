"""Centro de Control Estratégico/Empresa — cockpit dossier (V1).

Complementa MB-08 operacional. Mismo dossier, múltiples lecturas.
Solo lectura — sin duplicar motores de dominio.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.permissions import user_permissions
from app.services import control_center_adapters as adapters
from app.services import control_center_service as cc_svc
from app.services import evaluacion_service as eval_svc
from app.services import transformacion_service as trans_svc

LECTURAS = [
    {"id": "resumen", "label": "Resumen", "descripcion": "Panorama consolidado del dossier"},
    {"id": "gerencia", "label": "Gerencia", "descripcion": "Valor, riesgos, prioridades e impacto estratégico"},
    {"id": "operacion", "label": "Operación", "descripcion": "Tiempos, reprocesos, cuellos de botella y capacidad"},
    {"id": "sistemas", "label": "Sistemas", "descripcion": "Integraciones, gobierno y dependencias (alto nivel)"},
    {"id": "financiero", "label": "Financiero", "descripcion": "Inversión, ROI, payback y supuestos"},
]

SEMANTICA_VALOR = {
    "ANTES": "Línea base o situación previa documentada",
    "PROYECTADO": "Estimación o proyección — no es realizado",
    "REAL": "Medición o valor verificado con evidencia",
    "nota": "El proyectado nunca se presenta como realizado",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _has(permissions: set[str], code: str) -> bool:
    return code in permissions


def _shared_dossier(db: Session, org_id: str, permissions: set[str]) -> dict[str, Any]:
    if not _has(permissions, "transformacion.view"):
        return {"disponible": False, "estado": "Requiere transformacion.view"}
    dossier = trans_svc.get_dossier_completo(db, org_id, create=False)
    if dossier is None:
        return {
            "disponible": True,
            "dossier": None,
            "recorrido": trans_svc.get_recorrido_estado(db, org_id, None, create=False),
            "cadena_ejecutiva": cc_svc._cadena_ejecutiva(db, org_id, permissions, period_start=None),  # noqa: SLF001
            "expediente_id": None,
        }
    recorrido = trans_svc.get_recorrido_estado(db, org_id, dossier.get("expediente_activo_id"), create=False)
    cadena = cc_svc._cadena_ejecutiva(db, org_id, permissions, period_start=None)  # noqa: SLF001
    return {
        "disponible": True,
        "dossier": dossier,
        "recorrido": recorrido,
        "cadena_ejecutiva": cadena,
        "expediente_id": dossier.get("expediente_activo_id"),
    }


def _graficos_antes_proyectado_real(
    db: Session, org_id: str, expediente_id: str | None, *, vista_entidad: bool,
) -> list[dict[str, Any]]:
    if not expediente_id:
        return []
    impacto = eval_svc.get_impacto_resumen(db, expediente_id, org_id, vista_entidad=vista_entidad)
    charts = []
    for ind in impacto.get("indicadores", [])[:12]:
        charts.append({
            "titulo": ind.get("hallazgo"),
            "tipo": "comparacion",
            "series": [
                {"etiqueta": "ANTES", "valor": ind.get("antes"), "naturaleza": "ANTES"},
                {"etiqueta": "PROYECTADO", "valor": ind.get("proyectado"), "naturaleza": "PROYECTADO"},
                {"etiqueta": "REAL", "valor": ind.get("real"), "naturaleza": "REAL"},
            ],
            "confianza": ind.get("confianza"),
            "nota": "PROYECTADO ≠ REAL" if ind.get("etiqueta_proyeccion") else None,
        })
    return charts


def _lectura_resumen(shared: dict[str, Any], permissions: set[str]) -> dict[str, Any]:
    if not shared.get("disponible"):
        return shared
    d = shared.get("dossier")
    if not d:
        return {"etapa": None, "mensaje": "Sin dossier registrado — use Arquitecto de Transformación"}
    exp = d.get("expediente_activo") or {}
    return {
        "etapa": d.get("etapa_actual"),
        "entidad": exp.get("entidad_nombre"),
        "completitud": d.get("porcentaje_completitud"),
        "confianza": d.get("confianza_global"),
        "alternativas": len(d.get("alternativas", [])),
        "iniciativas": len(d.get("iniciativas", [])),
        "oportunidades_cadena": len(shared.get("cadena_ejecutiva", [])),
        "resumen_texto": d.get("resumen"),
    }


def _lectura_gerencia(db: Session, org_id: str, shared: dict[str, Any], permissions: set[str]) -> dict[str, Any]:
    if not shared.get("disponible"):
        return shared
    d = shared.get("dossier")
    if not d:
        return {"valor": {}, "riesgos": [], "prioridades": [], "oportunidades": [], "mensaje": "Sin dossier"}
    riesgos = [c for c in d.get("causas", []) if c.get("severidad") in ("ALTA", "CRITICA", "ALTO")]
    prioridades = sorted(d.get("iniciativas", []), key=lambda x: x.get("prioridad_score") or 0, reverse=True)[:5]
    oportunidades = []
    if _has(permissions, "oportunidades.view"):
        mod = adapters.OportunidadesAdapter().fetch(db, org_id, permissions=permissions)
        if mod.get("disponible"):
            oportunidades = mod.get("recientes") or []
    valor = {}
    if _has(permissions, "valoracion.view"):
        vr = adapters.ValorRetornoAdapter().fetch(db, org_id, permissions=permissions)
        if vr.get("disponible"):
            valor = {
                "verificado": vr.get("valor_verificado"),
                "estimado": vr.get("valor_estimado"),
                "potencial": vr.get("valor_potencial"),
                "retorno_pct": vr.get("retorno_porcentaje"),
            }
    return {
        "valor": valor,
        "riesgos": [{"titulo": r.get("descripcion"), "severidad": r.get("severidad")} for r in riesgos[:8]],
        "prioridades": [{"nombre": p.get("nombre"), "score": p.get("prioridad_score")} for p in prioridades],
        "oportunidades": oportunidades[:5],
        "alternativas_top": d.get("alternativas", [])[:3],
        "impacto_estrategico": "Derivado de iniciativas y cadena de valor",
    }


def _lectura_operacion_estrategica(db: Session, org_id: str, shared: dict[str, Any], permissions: set[str]) -> dict[str, Any]:
    if not shared.get("disponible"):
        return shared
    d = shared.get("dossier") or {}
    impl = {}
    if _has(permissions, "implementacion.view"):
        impl_mod = adapters.ImplementacionAdapter().fetch(db, org_id, permissions=permissions)
        if impl_mod.get("disponible"):
            impl = {
                "proyectos_activos": impl_mod.get("proyectos_activos"),
                "hitos_en_riesgo": impl_mod.get("hitos_en_riesgo"),
            }
    impacto = {}
    exp_id = shared.get("expediente_id")
    if exp_id and _has(permissions, "evaluacion.view"):
        impacto = eval_svc.get_impacto_resumen(db, exp_id, org_id, vista_entidad=False)
    return {
        "implementacion": impl,
        "indicadores_impacto": impacto.get("indicadores", [])[:8],
        "cuellos_de_botella": [
            c.get("descripcion") for c in d.get("causas", []) if c.get("tipo") == "CUELLO_BOTELLA"
        ][:5],
        "automatizacion": [
            a.get("nombre") for a in d.get("alternativas", []) if a.get("tipo") == "EMPLEADO_IA"
        ][:5],
        "enlace_operacional_mb08": {
            "disponible": _has(permissions, "control_center.view"),
            "ruta": "/centro-control",
            "nota": "Ejecuciones en tiempo real — Centro de Control operacional (MB-08)",
        },
    }


def _lectura_sistemas(db: Session, org_id: str, permissions: set[str]) -> dict[str, Any]:
    integraciones: dict[str, Any] = {"disponible": False}
    if _has(permissions, "integraciones.view"):
        from app.services import integration_service as int_svc

        overview = int_svc.list_connectors_overview(db, org_id)
        integraciones = {
            "disponible": True,
            "conectores": len(overview),
            "activos": sum(1 for c in overview if c.get("status") == "ACTIVE"),
            "enlace": "/integraciones",
            "nota": "Vista de alto nivel — sin detalle reproducible de conocimiento propietario",
        }
    gobernanza = {}
    if _has(permissions, "datos.view"):
        gobernanza = {"enlace": "/gobernanza-datos", "estado": "Políticas de datos disponibles"}
    continuidad = {}
    if _has(permissions, "continuidad.view"):
        cont = adapters.ContinuidadAdapter().fetch(db, org_id, permissions=permissions)
        if cont.get("disponible"):
            continuidad = {
                "incidentes_abiertos": cont.get("incidentes_abiertos"),
                "servicios_degradados": cont.get("servicios_degradados"),
            }
    return {
        "integraciones": integraciones,
        "gobernanza": gobernanza,
        "continuidad": continuidad,
        "arquitectura": "Resumen conceptual — detalle en módulos fuente",
        "dependencias": "Ver integraciones y continuidad",
    }


def _lectura_financiero(db: Session, org_id: str, permissions: set[str], *, incluir_privado: bool) -> dict[str, Any]:
    bloques: dict[str, Any] = {"semantica": SEMANTICA_VALOR}
    if _has(permissions, "valoracion.view"):
        vr = adapters.ValorRetornoAdapter().fetch(db, org_id, permissions=permissions)
        if vr.get("disponible"):
            bloques["valoracion"] = {
                "antes": None,
                "proyectado": vr.get("valor_estimado"),
                "real": vr.get("valor_verificado"),
                "roi_pct": vr.get("retorno_porcentaje"),
                "payback_meses": vr.get("payback_meses"),
                "confianza": vr.get("confianza", "MEDIA"),
            }
    if _has(permissions, "comercial.view"):
        com = adapters.ComercialResumenAdapter().fetch(db, org_id, permissions=permissions)
        if com.get("disponible"):
            bloques["comercial"] = {
                "propuestas": com.get("propuestas_total"),
                "verificado": com.get("valor_verificado"),
                "estimado": com.get("valor_estimado"),
                "potencial": com.get("valor_potencial"),
                "roi_promedio": com.get("roi_promedio"),
            }
    if _has(permissions, "tco.view"):
        tco = adapters.TcoAdapter().fetch(db, org_id, permissions=permissions)
        if tco.get("disponible"):
            bloques["tco"] = {
                "inversion_mensual": tco.get("inversion_total"),
                "antes": None,
                "proyectado": tco.get("inversion_total"),
                "real": tco.get("finops_ia"),
            }
    if incluir_privado and _has(permissions, "strategic_control.economia_privada"):
        bloques["economia_privada"] = {
            "visible_interno": True,
            "nota": "No publicable a la entidad sin autoridad de publicación",
            "consumo_ia_enlace": "/costos-valor",
        }
        if _has(permissions, "finops.view"):
            fin = adapters.FinOpsExtendidoAdapter().fetch(db, org_id, permissions=permissions)
            if fin.get("disponible"):
                bloques["economia_privada"]["costo_periodo"] = fin.get("costo_periodo")
                bloques["economia_privada"]["tokens_periodo"] = fin.get("tokens_periodo")
    else:
        bloques["economia_privada"] = {"visible_interno": False, "restringido": True}
    return bloques


def _vista_entidad_safe(db: Session, org_id: str, expediente_id: str | None, permissions: set[str]) -> dict[str, Any] | None:
    if not expediente_id or not _has(permissions, "evaluacion.vista_entidad"):
        return None
    return eval_svc.get_vista_entidad(db, expediente_id, org_id)


def get_cockpit(
    db: Session,
    user: User,
    org_id: str,
    *,
    lectura: str = "resumen",
    modo_comite: bool = False,
) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    if lectura not in {l["id"] for l in LECTURAS}:
        lectura = "resumen"

    shared = _shared_dossier(db, org_id, permissions)
    exp_id = shared.get("expediente_id")
    incluir_privado = _has(permissions, "strategic_control.economia_privada")

    lecturas_content = {
        "resumen": _lectura_resumen(shared, permissions),
        "gerencia": _lectura_gerencia(db, org_id, shared, permissions),
        "operacion": _lectura_operacion_estrategica(db, org_id, shared, permissions),
        "sistemas": _lectura_sistemas(db, org_id, permissions),
        "financiero": _lectura_financiero(db, org_id, permissions, incluir_privado=incluir_privado),
    }

    payload: dict[str, Any] = {
        "generated_at": _utcnow().isoformat(),
        "organization_id": org_id,
        "dossier_id": (shared.get("dossier") or {}).get("id"),
        "lectura_activa": lectura,
        "modo_comite": modo_comite,
        "lecturas": LECTURAS,
        "semantica_valor": SEMANTICA_VALOR,
        "contenido": lecturas_content[lectura],
        "mismo_dossier": True,
        "nota_comite": "Modo comité: recorra lecturas sin duplicar datos — misma fuente compartida",
        "graficos": _graficos_antes_proyectado_real(db, org_id, exp_id, vista_entidad=False),
        "trazabilidad": {
            "cadena_ejecutiva": shared.get("cadena_ejecutiva", []),
            "recorrido": shared.get("recorrido"),
        },
        "vista_entidad": _vista_entidad_safe(db, org_id, exp_id, permissions),
        "publicacion": {
            "autoridad": "evaluacion.visibility + evaluacion.vista_entidad",
            "nota": "La entidad solo ve hallazgos marcados visible_entidad",
            "economia_privada_publicable": False,
        },
        "enlaces": {
            "operacional_mb08": "/centro-control",
            "arquitecto": "/arquitecto-transformacion",
            "evaluaciones": f"/evaluaciones/{exp_id}" if exp_id else "/evaluaciones",
            "comercial": "/comercial",
            "implementacion": "/implementacion",
        },
        "separacion_mb08": "Cockpit estratégico/empresa. MB-08 cubre ejecuciones y empleados IA.",
    }

    if modo_comite:
        payload["lecturas_preview"] = {k: {"disponible": True, "id": k} for k in lecturas_content}

    return payload


def resolve_organization_id(db: Session, user: User, requested_org_id: str | None) -> str:
    return cc_svc.resolve_organization_id(db, user, requested_org_id)
