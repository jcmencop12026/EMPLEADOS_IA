"""Filtrado fail-closed — contenido publicable al cliente (V1)."""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.services import evaluacion_service as ev_svc
from app.services import resultados_service as res_svc
from app.services.presentacion_publicacion_adapter import get_estado_publicacion

FORBIDDEN_PAYLOAD_KEYS = frozenset({
    "notas_internas",
    "margen",
    "precio_sugerido",
    "costo_interno",
    "costos_internos",
    "prompt",
    "prompts",
    "scoring",
    "score_interno",
    "economia_privada",
    "finops",
    "reglas_privadas",
    "metodologia_interna",
    "organization_id",
    "created_by",
    "correlation_id",
    "valor_potencial",
    "precio",
    "margen_bruto",
    "costo_ia",
    "consumo_interno",
})

ALLOWED_META_KEYS = frozenset({"nota", "aviso", "audiencia"})

FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"prompt", re.I),
    re.compile(r"margen", re.I),
    re.compile(r"finops", re.I),
    re.compile(r"scoring", re.I),
    re.compile(r"costo[_\s]?interno", re.I),
    re.compile(r"precio[_\s]?sugerido", re.I),
    re.compile(r"regla[s]?[_\s]?privad", re.I),
)

ALLOWED_INDICADOR_KEYS = frozenset({
    "id", "nombre", "antes", "proyectado", "real", "unidad", "etiqueta_proyeccion",
})

ALLOWED_NARRATIVA_KEYS = frozenset({
    "banner", "que_ocurrio", "por_que", "que_significa", "requiere_atencion",
    "oportunidad", "valor", "recomendacion", "indicadores_clave",
})


class PublicableClienteError(PermissionError):
    """Contenido no autorizado para audiencia cliente."""


def _walk_keys(obj: Any, path: str = "", parent_key: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k).lower()
            full = f"{path}.{k}" if path else str(k)
            if key in FORBIDDEN_PAYLOAD_KEYS:
                found.append(full)
            for pat in FORBIDDEN_VALUE_PATTERNS:
                if pat.search(key):
                    found.append(full)
            found.extend(_walk_keys(v, full, key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(_walk_keys(item, f"{path}[{i}]", parent_key))
    elif isinstance(obj, str):
        if parent_key in ALLOWED_META_KEYS:
            return found
        low = obj.lower()
        for pat in FORBIDDEN_VALUE_PATTERNS:
            if pat.search(low) and len(low) < 120:
                found.append(path or "value")
    return found


def assert_payload_publicable(payload: dict[str, Any]) -> None:
    """Validación negativa — lanza si el payload contiene campos prohibidos."""
    violations = _walk_keys(payload)
    if violations:
        raise PublicableClienteError(
            f"Payload publicable contiene campos prohibidos: {', '.join(sorted(set(violations))[:8])}"
        )


def _filter_indicadores(indicadores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ind in indicadores:
        out.append({k: ind[k] for k in ALLOWED_INDICADOR_KEYS if k in ind})
    return out


def _filter_narrativa(interp: dict[str, Any] | None) -> dict[str, Any]:
    if not interp:
        return {}
    return {k: interp[k] for k in ALLOWED_NARRATIVA_KEYS if k in interp}


def build_informe_publicable_cliente(
    db: Session,
    expediente_id: str,
    organization_id: str,
) -> dict[str, Any]:
    """Respuesta exclusiva para audiencia Publicable cliente — whitelist fail-closed."""
    exp = ev_svc.get_vista_entidad(db, expediente_id, organization_id)
    impacto = ev_svc.get_impacto_resumen(db, expediente_id, organization_id, vista_entidad=True)
    vista = exp

    informes_raw = res_svc.list_informes(db, organization_id, expediente_id=expediente_id)
    informes_publicables = [
        {
            "id": i["id"],
            "titulo": i["titulo"],
            "version": i["version"],
            "visibilidad": i["visibilidad"],
        }
        for i in informes_raw
        if i.get("visibilidad") == "VISIBLE_ENTIDAD"
    ]

    estado_pub = get_estado_publicacion(db, organization_id, expediente_id)
    publicado = estado_pub == "PUBLICADO_A_EMPRESA"

    payload: dict[str, Any] = {
        "audiencia": "PUBLICABLE_CLIENTE",
        "expediente_id": expediente_id,
        "codigo": vista.get("codigo"),
        "entidad_nombre": vista.get("entidad_nombre"),
        "estado_publicacion": estado_pub,
        "publicado": publicado,
        "etiqueta_demo": vista.get("etiqueta_demo"),
        "hallazgos": [
            {
                "titulo": h.get("titulo"),
                "tipo_contenido": h.get("tipo_contenido"),
                "confianza": h.get("confianza"),
            }
            for h in (vista.get("hallazgos") or [])
        ],
        "indicadores": _filter_indicadores(impacto.get("indicadores") or []),
        "narrativa": _filter_narrativa(impacto.get("interpretacion")),
        "valor_publicable": vista.get("valor_publicable"),
        "informes_publicables": informes_publicables,
        "nota": (
            "Contenido autorizado para empresa cliente según política de publicación V1."
        ),
    }

    if not publicado:
        payload["aviso"] = (
            "Expediente no publicado a empresa. Vista previa interna con campos autorizados únicamente."
        )

    assert_payload_publicable(payload)
    return payload


def serialize_for_audit(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False).lower()
