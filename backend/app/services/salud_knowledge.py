"""Integración SALUD ↔ Centro de Conocimiento (SALUD-CONOCIMIENTO-971)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.knowledge_models import KnowledgeActivity
from app.services.knowledge_retrieval import retrieve_knowledge
from app.services.knowledge_service import log_consultation

DOMAIN_QUERIES: dict[str, list[str]] = {
    "radicacion": ["plazo radicación", "procedimiento radicación", "contrato radicación"],
    "contratos": ["plazo máximo radicación", "contrato EPS", "obligaciones contractuales"],
    "glosas": ["procedimiento glosas", "respuesta glosas", "causales glosa"],
    "cartera": ["política cartera", "cobro cartera", "acuerdos de pago"],
    "facturacion": ["manual facturación", "procedimiento facturación"],
    "estrategico": ["políticas institucionales", "lineamientos operativos"],
}

KNOWLEDGE_DOMAINS = {"radicacion", "contratos", "glosas", "cartera", "facturacion"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def specialist_needs_knowledge(domain: str, request_text: str) -> bool:
    if domain in KNOWLEDGE_DOMAINS:
        return True
    text = request_text.lower()
    return any(k in text for k in ("contrato", "pactado", "procedimiento", "política", "norma", "manual"))


def build_domain_query(domain: str, request_text: str, ips_name: str) -> str:
    parts = DOMAIN_QUERIES.get(domain, ["lineamientos operativos"])
    if "contrato" in request_text.lower() or domain == "contratos":
        return "plazo radicación"
    return parts[0]


def build_domain_queries(domain: str, request_text: str) -> list[str]:
    queries = list(DOMAIN_QUERIES.get(domain, ["lineamientos operativos"]))
    if "contrato" in request_text.lower() or domain in {"contratos", "radicacion"}:
        queries = ["radicación", "plazo", *queries]
    deduped: list[str] = []
    for q in queries:
        if q not in deduped:
            deduped.append(q)
    return deduped[:4]


def source_reference(
    fragment: dict[str, Any],
    *,
    query: str,
    employee_id: str | None,
    analysis_id: str,
    domain: str,
) -> dict[str, Any]:
    metadata = fragment.get("metadata") or {}
    return {
        "tipo": "CONOCIMIENTO",
        "document_id": fragment.get("document_id"),
        "chunk_id": fragment.get("chunk_id"),
        "titulo": fragment.get("document_name"),
        "categoria": metadata.get("tipo") or metadata.get("area") or fragment.get("section"),
        "consulta": query,
        "especialista_id": employee_id,
        "analysis_id": analysis_id,
        "dominio": domain,
        "fecha": _utcnow().isoformat(),
        "relevancia": fragment.get("relevance"),
        "extracto": (fragment.get("content") or "")[:240],
    }


def _domain_relevance(domain: str, fragment: dict[str, Any]) -> bool:
    content = (fragment.get("content") or "").lower()
    name = (fragment.get("document_name") or "").lower()
    metadata = fragment.get("metadata") or {}
    area = str(metadata.get("area", "")).lower()
    doc_type = str(metadata.get("tipo", "")).lower()

    irrelevant_markers = ("recursos humanos", "manual de contratación de personal", "nómina")
    if any(marker in content or marker in name for marker in irrelevant_markers):
        if domain not in {"estrategico"} and "rh" not in domain:
            return False

    domain_terms = {
        "radicacion": ("radic", "factura", "plazo"),
        "contratos": ("contrato", "plazo", "eps", "pact"),
        "glosas": ("glosa", "objec", "causal"),
        "cartera": ("cartera", "cobro", "mora", "pago"),
        "facturacion": ("factur", "tarifa"),
    }
    terms = domain_terms.get(domain, ())
    if not terms:
        return True
    haystack = f"{content} {name} {area} {doc_type}"
    return any(term in haystack for term in terms)


def extract_deadline_days(text: str) -> list[int]:
    """Extrae plazos de radicación evitando confundir plazos de pago en el mismo documento."""
    found: list[int] = []
    lower = text.lower()
    for segment in re.split(r"[.;]", lower):
        if "pago" in segment:
            continue
        if "radic" not in segment and "plazo" not in segment:
            continue
        for match in re.finditer(r"(\d+)\s*d[ií]as?", segment):
            found.append(int(match.group(1)))
        for match in re.finditer(r"\((\d+)\)\s*d[ií]as?", segment):
            found.append(int(match.group(1)))
        for match in re.finditer(r"plazo\s*(?:m[aá]ximo)?\s*(?:de)?\s*(\d+)", segment):
            found.append(int(match.group(1)))
    return found


def analyze_fragments(fragments: list[dict[str, Any]]) -> dict[str, Any]:
    deadlines: list[dict[str, Any]] = []
    for frag in fragments:
        days = extract_deadline_days(frag.get("content") or "")
        if not days:
            continue
        metadata = frag.get("metadata") or {}
        deadlines.append(
            {
                "document_id": frag.get("document_id"),
                "document_name": frag.get("document_name"),
                "chunk_id": frag.get("chunk_id"),
                "dias": days,
                "vigente_desde": metadata.get("vigente_desde"),
                "vigente_hasta": metadata.get("vigente_hasta"),
            }
        )

    conflict = False
    validation_required = False
    unique_limits = sorted({d for item in deadlines for d in item["dias"]})
    if len(unique_limits) > 1:
        conflict = True
        validation_required = True

    preferred_limit: int | None = None
    if deadlines:
        scored = sorted(
            deadlines,
            key=lambda item: (
                1 if item.get("vigente_hasta") else 0,
                max(item["dias"]) if item["dias"] else 0,
            ),
            reverse=True,
        )
        preferred = scored[0]
        if not conflict:
            preferred_limit = max(preferred["dias"]) if preferred["dias"] else None
        elif preferred.get("vigente_hasta"):
            preferred_limit = max(preferred["dias"]) if preferred["dias"] else None
        else:
            preferred_limit = None
            validation_required = True

    return {
        "plazos_detectados": deadlines,
        "conflicto": conflict,
        "requiere_validacion": validation_required,
        "plazo_preferido_dias": preferred_limit,
        "limites_unicos": unique_limits,
    }


def fetch_specialist_knowledge(
    db: Session,
    *,
    organization_id: str,
    analysis_id: str,
    user_id: str | None,
    employee_id: str,
    domain: str,
    request_text: str,
    ips_name: str,
    limit: int = 5,
) -> dict[str, Any]:
    queries = build_domain_queries(domain, request_text)
    seen_chunks: set[str] = set()
    relevant: list[dict[str, Any]] = []
    query_log: list[str] = []
    for query in queries:
        query_log.append(query)
        raw = retrieve_knowledge(
            db,
            tenant_id=organization_id,
            query=query,
            limit=limit,
            employee_id=employee_id,
        )
        for frag in raw:
            chunk_id = frag.get("chunk_id")
            if chunk_id and chunk_id in seen_chunks:
                continue
            if chunk_id:
                seen_chunks.add(chunk_id)
            if _domain_relevance(domain, frag):
                relevant.append(frag)
        if len(relevant) >= limit:
            break

    refs: list[dict[str, Any]] = []
    for frag in relevant[:limit]:
        refs.append(
            source_reference(
                frag,
                query=queries[0],
                employee_id=employee_id,
                analysis_id=analysis_id,
                domain=domain,
            )
        )
        if frag.get("document_id"):
            log_consultation(
                db,
                organization_id=organization_id,
                document_id=frag["document_id"],
                user_id=user_id,
                query=f"SALUD:{analysis_id}:{domain}:{queries[0][:120]}",
            )
    analysis = analyze_fragments(relevant[:limit])
    return {
        "dominio": domain,
        "consulta": ", ".join(query_log),
        "especialista_id": employee_id,
        "fragmentos": len(relevant[:limit]),
        "fuentes": refs,
        "analisis": analysis,
        "experiencia_separada": True,
    }


def collect_analysis_knowledge(
    db: Session,
    *,
    organization_id: str,
    analysis_id: str,
    user_id: str | None,
    request_text: str,
    ips_name: str,
    specialists: dict[str, Any],
) -> dict[str, Any]:
    bundles: list[dict[str, Any]] = []
    assignments = specialists.get("asignaciones") or []
    for assignment in assignments:
        domain = assignment.get("domain")
        employee_id = assignment.get("employee_id")
        if not domain or not employee_id:
            continue
        if not specialist_needs_knowledge(domain, request_text):
            continue
        bundles.append(
            fetch_specialist_knowledge(
                db,
                organization_id=organization_id,
                analysis_id=analysis_id,
                user_id=user_id,
                employee_id=employee_id,
                domain=domain,
                request_text=request_text,
                ips_name=ips_name,
            )
        )

    all_sources = [src for bundle in bundles for src in bundle.get("fuentes", [])]
    merged_fragments: list[dict[str, Any]] = []
    for bundle in bundles:
        for src in bundle.get("fuentes", []):
            merged_fragments.append(
                {
                    "document_id": src.get("document_id"),
                    "document_name": src.get("titulo"),
                    "chunk_id": src.get("chunk_id"),
                    "content": src.get("extracto", ""),
                    "metadata": {},
                }
            )
    merged_analysis = analyze_fragments(merged_fragments) if merged_fragments else {}
    conflicts = [b for b in bundles if b.get("analisis", {}).get("conflicto")]
    if merged_analysis.get("conflicto"):
        conflicts.append({"analisis": merged_analysis, "dominio": "contratos", "fuentes": all_sources})
    return {
        "utilizado": bool(all_sources),
        "mensaje": (
            "No se encontró conocimiento documental autorizado adicional."
            if not all_sources
            else None
        ),
        "consultas": bundles,
        "fuentes_consultadas": all_sources,
        "conflictos": conflicts,
        "requiere_validacion": merged_analysis.get("requiere_validacion")
        or any(b.get("analisis", {}).get("requiere_validacion") for b in bundles),
        "analisis_global": merged_analysis,
    }


def detect_contract_radicacion_breach(
    indicators: dict[str, Any],
    knowledge_ctx: dict[str, Any],
) -> dict[str, Any] | None:
    rad = indicators.get("radicacion", {})
    if not rad.get("disponible"):
        return None

    plazo_dias = None
    supporting_sources: list[dict[str, Any]] = []
    for bundle in knowledge_ctx.get("consultas", []):
        analysis = bundle.get("analisis", {})
        if analysis.get("conflicto"):
            continue
        if analysis.get("plazo_preferido_dias"):
            plazo_dias = analysis["plazo_preferido_dias"]
            supporting_sources.extend(bundle.get("fuentes", []))
            break

    if plazo_dias is None:
        return None

    delays = rad.get("evidencia", {}).get("dias_por_factura") or []
    breaches = [d for d in delays if isinstance(d.get("dias"), (int, float)) and d["dias"] > plazo_dias]
    if not breaches:
        return None

    worst = max(breaches, key=lambda x: x["dias"])
    exceso = int(worst["dias"] - plazo_dias)
    return {
        "category": "radicacion",
        "title": f"Incumplimiento contractual de radicación (+{exceso} días)",
        "description": (
            f"La factura {worst.get('numero_factura', 'N/A')} tardó {int(worst['dias'])} días en radicarse; "
            f"el plazo contractual autorizado es {plazo_dias} días."
        ),
        "kind": "HECHO",
        "indicator_code": "incumplimiento_plazo_radicacion",
        "indicator_value": str(exceso),
        "severity": "ALTA" if exceso >= 5 else "MEDIA",
        "confidence": "ALTA" if not knowledge_ctx.get("conflictos") else "MEDIA",
        "confidence_criteria": {
            "datos": "radicacion",
            "documento": "contrato_autorizado",
            "exceso_dias": exceso,
            "plazo_contractual": plazo_dias,
        },
        "probable_cause": "Retraso operativo en radicación respecto al plazo pactado.",
        "economic_impact": None,
        "sources": [
            {"dataset": "facturacion+radicacion", "regla": "dias_factura_radicacion"},
            *[
                {
                    "tipo": "CONOCIMIENTO",
                    "document_id": s.get("document_id"),
                    "chunk_id": s.get("chunk_id"),
                    "titulo": s.get("titulo"),
                }
                for s in supporting_sources
            ],
        ],
        "evidence": {
            "datos": worst,
            "documental": supporting_sources,
            "clasificacion": "HECHO",
        },
    }


def apply_knowledge_to_hallazgos(
    hallazgos: list[dict[str, Any]],
    knowledge_ctx: dict[str, Any],
    indicators: dict[str, Any],
) -> list[dict[str, Any]]:
    enriched = list(hallazgos)
    breach = detect_contract_radicacion_breach(indicators, knowledge_ctx)
    if breach:
        enriched.insert(0, breach)

    if knowledge_ctx.get("conflictos"):
        enriched.append(
            {
                "category": "contratos",
                "title": "Conflicto documental en plazos de radicación",
                "description": (
                    "Existen documentos autorizados con plazos distintos. "
                    "Se requiere validación humana antes de concluir cumplimiento contractual."
                ),
                "kind": "INSUFICIENTE",
                "indicator_code": "conflicto_conocimiento",
                "indicator_value": None,
                "severity": "MEDIA",
                "confidence": "BAJA",
                "confidence_criteria": {"motivo": "documentos_contradictorios"},
                "probable_cause": None,
                "economic_impact": None,
                "sources": knowledge_ctx.get("fuentes_consultadas", []),
                "evidence": {"conflictos": knowledge_ctx.get("conflictos")},
            }
        )

    for hallazgo in enriched:
        existing = hallazgo.get("sources") or []
        doc_sources = [
            s for s in knowledge_ctx.get("fuentes_consultadas", [])
            if s.get("dominio") == hallazgo.get("category")
        ]
        if doc_sources:
            hallazgo["sources"] = existing + doc_sources[:3]
            evidence = hallazgo.get("evidence") or {}
            if isinstance(evidence, dict):
                evidence["fuentes_documentales"] = doc_sources[:3]
                hallazgo["evidence"] = evidence
    return enriched


def log_salud_knowledge_audit(
    db: Session,
    *,
    organization_id: str,
    analysis_id: str,
    user_id: str | None,
    knowledge_ctx: dict[str, Any],
) -> None:
    for source in knowledge_ctx.get("fuentes_consultadas", []):
        doc_id = source.get("document_id")
        if not doc_id:
            continue
        db.add(
            KnowledgeActivity(
                document_id=doc_id,
                organization_id=organization_id,
                user_id=user_id,
                action="CONSULTA_SALUD",
                detail=json.dumps(
                    {
                        "analysis_id": analysis_id,
                        "dominio": source.get("dominio"),
                        "consulta": source.get("consulta"),
                        "chunk_id": source.get("chunk_id"),
                    },
                    ensure_ascii=False,
                )[:500],
            )
        )
