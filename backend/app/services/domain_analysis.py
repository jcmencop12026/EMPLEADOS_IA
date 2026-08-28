"""Interfaz transversal de análisis por dominio — cierre G-01.

Coordinator invoca proveedores registrados en lugar de hardcode SALUD.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

_REGISTRY: dict[str, "DomainAnalysisProvider"] = {}


class DomainAnalysisProvider(ABC):
    """Proveedor analítico de dominio."""

    domain_codes: tuple[str, ...] = ()

    @abstractmethod
    def can_handle(self, request: str, context: dict[str, Any] | None) -> bool:
        ...

    @abstractmethod
    def analyze(
        self,
        db: Session,
        *,
        organization_id: str,
        user_id: str | None,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


def register_provider(provider: DomainAnalysisProvider) -> None:
    for code in provider.domain_codes:
        _REGISTRY[code] = provider


def get_provider_for_request(request: str, context: dict[str, Any] | None) -> DomainAnalysisProvider | None:
    for provider in _REGISTRY.values():
        if provider.can_handle(request, context):
            return provider
    return None


def detect_domain(request: str, context: dict[str, Any] | None) -> tuple[str, str]:
    """Detecta dominio y categoría sin hardcodear SALUD en coordinator."""
    provider = get_provider_for_request(request, context)
    if provider and provider.domain_codes:
        return provider.domain_codes[0], "dominio_registrado"
    text = (request or "").lower()
    ctx = context or {}
    if ctx.get("dominio"):
        return str(ctx["dominio"]), "contexto"
    if any(k in text for k in ("automatiz", "administrativ", "repetitiv")):
        return "administrativo", "operativo"
    if any(k in text for k in ("comercial", "conversión", "conversion", "venta", "cartera")):
        return "comercial", "comercial"
    if any(k in text for k in ("financ", "costo", "presupuesto")):
        return "financiero", "financiero"
    if any(k in text for k in ("cumplim", "regulat", "sanción", "sancion")):
        return "cumplimiento", "regulatorio"
    return "general", "general"


def resolve_capability_code(request: str, context: dict[str, Any] | None) -> tuple[str, str]:
    """Resuelve código de capacidad y categoría — compatible con coordinator."""
    bootstrap_providers()
    ctx = context or {}
    text = (request or "").lower()
    provider = get_provider_for_request(request, context)
    if isinstance(provider, SaludDomainAnalysisProvider):
        if ctx.get("tool") in ("rips", "docint"):
            return ctx["tool"], "salud"
        if ctx.get("analysis_type") == "ips" or ctx.get("ips_analysis"):
            return "ips-analitica", "salud"
        ips_keywords = (
            "ips", "facturación", "facturacion", "radicación", "radicacion",
            "glosa", "cartera", "diagnóstico", "diagnostico", "financiera y operativa",
        )
        if any(kw in text for kw in ips_keywords):
            return "ips-analitica", "salud"
        if "rips" in text:
            return "rips", "salud"
        if any(k in text for k in ("documento", "docint", "documentos")):
            return "docint", "salud"
        if ctx.get("rips") or ctx.get("data", {}).get("usuarios"):
            return "rips", "salud"
        if ctx.get("documents") or ctx.get("documentos"):
            return "docint", "salud"
        if ctx.get("inline_datasets") or ctx.get("datasets"):
            return "ips-analitica", "salud"
        return "docint", "salud"
    if provider:
        code = provider.domain_codes[0] if provider.domain_codes else "general"
        return code, "dominio_registrado"
    dominio, categoria = detect_domain(request, context)
    return dominio, categoria


class SaludDomainAnalysisProvider(DomainAnalysisProvider):
    """Proveedor SALUD — delega a motor IPS existente."""

    domain_codes = ("salud", "ips-analitica", "rips", "docint")

    def can_handle(self, request: str, context: dict[str, Any] | None) -> bool:
        ctx = context or {}
        text = (request or "").lower()
        if ctx.get("tool") in ("rips", "docint"):
            return True
        if ctx.get("analysis_type") == "ips" or ctx.get("ips_analysis"):
            return True
        ips_keywords = (
            "ips", "facturación", "facturacion", "radicación", "radicacion",
            "glosa", "cartera", "diagnóstico", "diagnostico", "financiera y operativa",
        )
        if any(kw in text for kw in ips_keywords):
            return True
        if "rips" in text or ctx.get("rips") or ctx.get("data", {}).get("usuarios"):
            return True
        if any(k in text for k in ("documento", "docint")) or ctx.get("documents"):
            return True
        if ctx.get("inline_datasets") or ctx.get("datasets"):
            return True
        return False

    def analyze(
        self,
        db: Session,
        *,
        organization_id: str,
        user_id: str | None,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.services.salud_engine import run_ips_analysis

        ctx = context or {}
        result = run_ips_analysis(
            db,
            organization_id=organization_id,
            user_id=user_id or "",
            request=request,
            context=ctx,
        )
        return {
            "provider": "salud",
            "dominio": "salud",
            "analysis_id": result.get("analysis_id"),
            "resultado": result,
        }


class GenericDomainAnalysisProvider(DomainAnalysisProvider):
    """Proveedor genérico para dominios no-SALUD."""

    domain_codes = ("administrativo", "comercial", "financiero", "cumplimiento", "general", "operativo")

    def can_handle(self, request: str, context: dict[str, Any] | None) -> bool:
        return True

    def analyze(
        self,
        db: Session,
        *,
        organization_id: str,
        user_id: str | None,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = context or {}
        dominio, _ = detect_domain(request, ctx)
        indicadores = ctx.get("indicadores") or ctx.get("metrics") or {}
        return {
            "provider": "generic",
            "dominio": dominio,
            "indicadores": indicadores,
            "request": request,
            "suficiencia": "PARCIAL" if indicadores else "INSUFICIENTE",
            "datos_faltantes": [] if indicadores else ["indicadores", "histórico"],
        }


def bootstrap_providers() -> None:
    if _REGISTRY:
        return
    register_provider(SaludDomainAnalysisProvider())
    register_provider(GenericDomainAnalysisProvider())
