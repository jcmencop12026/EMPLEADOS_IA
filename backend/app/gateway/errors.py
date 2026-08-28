"""Errores normalizados del LLM Gateway — mensajes en español."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class LlmErrorCategory(StrEnum):
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    AUTH_ERROR = "AUTH_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    ALL_PROVIDERS_FAILED = "ALL_PROVIDERS_FAILED"


_ERROR_MESSAGES_ES: dict[LlmErrorCategory, str] = {
    LlmErrorCategory.PROVIDER_UNAVAILABLE: "El proveedor de IA no está disponible.",
    LlmErrorCategory.TIMEOUT: "La inferencia excedió el tiempo de espera configurado.",
    LlmErrorCategory.AUTH_ERROR: "Error de autenticación con el proveedor de IA.",
    LlmErrorCategory.RATE_LIMIT: "El proveedor de IA aplicó límite de tasa; intente más tarde.",
    LlmErrorCategory.MODEL_NOT_FOUND: "El modelo solicitado no existe o no está disponible.",
    LlmErrorCategory.INVALID_RESPONSE: "La respuesta del proveedor de IA no es válida.",
    LlmErrorCategory.CONFIGURATION_ERROR: "La configuración del proveedor de IA es inválida.",
    LlmErrorCategory.ALL_PROVIDERS_FAILED: "Todos los proveedores de IA configurados fallaron.",
}


@dataclass
class LlmGatewayError:
    category: LlmErrorCategory
    message: str
    provider: str | None = None
    model: str | None = None
    technical_detail: str | None = None
    raw_metadata: dict[str, Any] | None = None

    @classmethod
    def from_category(
        cls,
        category: LlmErrorCategory,
        *,
        provider: str | None = None,
        model: str | None = None,
        technical_detail: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> "LlmGatewayError":
        base = _ERROR_MESSAGES_ES.get(category, "Error de inferencia de IA.")
        return cls(
            category=category,
            message=base,
            provider=provider,
            model=model,
            technical_detail=technical_detail,
            raw_metadata=raw_metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "message": self.message,
            "provider": self.provider,
            "model": self.model,
            "technical_detail": self.technical_detail,
        }


FALLBACK_ELIGIBLE: set[LlmErrorCategory] = {
    LlmErrorCategory.PROVIDER_UNAVAILABLE,
    LlmErrorCategory.TIMEOUT,
    LlmErrorCategory.RATE_LIMIT,
    LlmErrorCategory.MODEL_NOT_FOUND,
}
