"""Modelos — Inteligencia económica EIAAX (1740)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EconomicScenarioRun(Base):
    """Persistencia de simulaciones comparativas — no reemplaza simuladores de dominio."""

    __tablename__ = "economic_scenario_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ORGANIZACION")
    scope_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultados_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
