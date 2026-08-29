"""Campos opcionales del contrato semántico P1-ID-02 para DTOs post-V1."""

from __future__ import annotations

from pydantic import BaseModel


class SemanticMetaFields(BaseModel):
    tipo_semantico: str | None = None
    subtipo_semantico: str | None = None
    etiqueta_visible: str | None = None
    tooltip_semantico: str | None = None
