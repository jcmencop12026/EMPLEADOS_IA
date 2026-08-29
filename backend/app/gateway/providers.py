"""Proveedores LLM V1 — conocidos vs ejecutables."""

from __future__ import annotations

# Referencia documental / futuro (sin adaptador en V1).
KNOWN_LLM_PROVIDERS = frozenset({"openai", "ollama", "azure-openai", "anthropic", "gemini"})

# Únicos proveedores con adaptador real en V1.
EXECUTABLE_LLM_PROVIDERS = frozenset({"openai", "ollama"})

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


def is_executable_llm_provider(provider: str | None) -> bool:
    if not provider:
        return False
    normalized = provider.lower().strip()
    if normalized in NON_LLM_PROVIDER_MARKERS:
        return False
    return normalized in EXECUTABLE_LLM_PROVIDERS


def has_adapter(provider: str | None) -> bool:
    return is_executable_llm_provider(provider)
