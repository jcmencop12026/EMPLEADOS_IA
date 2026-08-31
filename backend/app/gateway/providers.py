"""Proveedores LLM — catálogo, adaptadores y modos de operación."""

from __future__ import annotations

from app.gateway.provider_status import ProviderAdapterMode

KNOWN_LLM_PROVIDERS = frozenset({"openai", "ollama", "azure-openai", "anthropic", "gemini"})

OPERATIONAL_LLM_PROVIDERS = frozenset({"openai"})
PREPARED_LLM_PROVIDERS = frozenset({"anthropic", "gemini", "azure-openai"})
OPTIONAL_LLM_PROVIDERS = frozenset({"ollama"})

# Todos los proveedores con adaptador implementado.
ADAPTER_LLM_PROVIDERS = OPERATIONAL_LLM_PROVIDERS | PREPARED_LLM_PROVIDERS | OPTIONAL_LLM_PROVIDERS

# Compatibilidad V1 — ejecutables con adaptador.
EXECUTABLE_LLM_PROVIDERS = ADAPTER_LLM_PROVIDERS

NON_LLM_PROVIDER_MARKERS = frozenset(
    {
        "python",
        "rule",
        "tool",
        "rule-engine",
        "rules",
        "deterministic",
        "none",
        "sql",
        "automation",
        "human",
        "hybrid",
        "docint",
        "rips",
        "custom",
    }
)

PROVIDER_LABELS_ES: dict[str, str] = {
    "openai": "OpenAI",
    "ollama": "Ollama",
    "anthropic": "Anthropic",
    "gemini": "Google Gemini",
    "azure-openai": "Azure OpenAI",
}

PROVIDER_MODES: dict[str, ProviderAdapterMode] = {
    "openai": ProviderAdapterMode.OPERATIVO,
    "ollama": ProviderAdapterMode.OPCIONAL,
    "anthropic": ProviderAdapterMode.PREPARADO,
    "gemini": ProviderAdapterMode.PREPARADO,
    "azure-openai": ProviderAdapterMode.PREPARADO,
}


def normalize_provider_type(provider: str | None) -> str:
    return (provider or "").lower().strip()


def is_known_llm_provider(provider: str | None) -> bool:
    return normalize_provider_type(provider) in KNOWN_LLM_PROVIDERS


def is_executable_llm_provider(provider: str | None) -> bool:
    if not provider:
        return False
    normalized = normalize_provider_type(provider)
    if normalized in NON_LLM_PROVIDER_MARKERS:
        return False
    return normalized in EXECUTABLE_LLM_PROVIDERS


def has_adapter(provider: str | None) -> bool:
    return is_executable_llm_provider(provider)


def provider_mode(provider: str | None) -> ProviderAdapterMode | None:
    return PROVIDER_MODES.get(normalize_provider_type(provider))
