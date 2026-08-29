"""Modelos de persistencia para LLM Gateway V1 — Paquete B."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LlmProviderConfig(Base):
    """Configuración de proveedor IA por organización (compatible con tenant futuro)."""

    __tablename__ = "llm_provider_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    model_default: Mapped[str | None] = mapped_column(String(120), nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class LlmInferenceLog(Base):
    """Auditoría de inferencias LLM — sin prompts completos ni secretos."""

    __tablename__ = "llm_inference_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_tasks.id"), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OK")
    finish_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    initial_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fallback_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
