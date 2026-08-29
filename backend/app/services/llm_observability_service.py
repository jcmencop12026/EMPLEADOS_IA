"""Observabilidad y agregaciones de inferencia IA — Bloque 1270."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.llm_models import LlmInferenceLog


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _period_start(periodo: str | None) -> datetime | None:
    now = _utcnow()
    if periodo == "7d":
        return now - timedelta(days=7)
    if periodo == "30d":
        return now - timedelta(days=30)
    if periodo == "24h":
        return now - timedelta(hours=24)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_observability_summary(db: Session, organization_id: str, *, periodo: str | None = "mtd") -> dict[str, Any]:
    start = _period_start(periodo)
    base = db.query(LlmInferenceLog).filter(LlmInferenceLog.organization_id == organization_id)
    if start:
        base = base.filter(LlmInferenceLog.created_at >= start)

    total = base.count()
    ok = base.filter(LlmInferenceLog.status == "OK").count()
    errors = total - ok
    fallbacks = base.filter(LlmInferenceLog.fallback_used.is_(True)).count()

    avg_latency = (
        db.query(func.avg(LlmInferenceLog.latency_ms))
        .filter(LlmInferenceLog.organization_id == organization_id)
        .filter(LlmInferenceLog.latency_ms.isnot(None))
    )
    if start:
        avg_latency = avg_latency.filter(LlmInferenceLog.created_at >= start)
    avg_latency_val = avg_latency.scalar()

    tokens = (
        db.query(func.coalesce(func.sum(LlmInferenceLog.tokens_total), 0))
        .filter(LlmInferenceLog.organization_id == organization_id)
    )
    if start:
        tokens = tokens.filter(LlmInferenceLog.created_at >= start)
    tokens_total = int(tokens.scalar() or 0)

    cost_q = (
        db.query(func.coalesce(func.sum(LlmInferenceLog.cost), 0))
        .filter(LlmInferenceLog.organization_id == organization_id, LlmInferenceLog.cost.isnot(None))
    )
    if start:
        cost_q = cost_q.filter(LlmInferenceLog.created_at >= start)
    cost_sum = cost_q.scalar()
    cost_total = float(cost_sum) if cost_sum is not None else None

    by_provider = (
        db.query(LlmInferenceLog.provider, func.count())
        .filter(LlmInferenceLog.organization_id == organization_id)
    )
    if start:
        by_provider = by_provider.filter(LlmInferenceLog.created_at >= start)
    provider_counts = {
        (provider if provider is not None else "desconocido"): count
        for provider, count in by_provider.group_by(LlmInferenceLog.provider).all()
    }

    by_error = (
        db.query(LlmInferenceLog.error_category, func.count())
        .filter(
            LlmInferenceLog.organization_id == organization_id,
            LlmInferenceLog.status != "OK",
            LlmInferenceLog.error_category.isnot(None),
        )
    )
    if start:
        by_error = by_error.filter(LlmInferenceLog.created_at >= start)
    error_counts = {
        (category if category is not None else "sin_categoria"): count
        for category, count in by_error.group_by(LlmInferenceLog.error_category).all()
    }

    success_rate = round((ok / total) * 100, 2) if total else None

    return {
        "periodo": periodo,
        "total_inferencias": total,
        "exitosas": ok,
        "errores": errors,
        "tasa_exito": success_rate,
        "latencia_promedio_ms": round(float(avg_latency_val), 2) if avg_latency_val is not None else None,
        "tokens_total": tokens_total if tokens_total > 0 else None,
        "costo_total": cost_total,
        "fallbacks": fallbacks,
        "por_proveedor": provider_counts,
        "errores_por_categoria": error_counts,
    }
