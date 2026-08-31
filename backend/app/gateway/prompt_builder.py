"""Constructor de prompts — separación sistema / empleado / conocimiento / usuario."""

from __future__ import annotations

from typing import Any

from app.gateway.types import LlmMessage
from app.orchestration_models import EmployeeInstructions


def build_system_instructions(
    instructions: EmployeeInstructions | None,
    *,
    extra_system: str | None = None,
) -> str | None:
    parts: list[str] = []
    if instructions:
        for field in (
            instructions.system_purpose,
            instructions.role_text,
            instructions.objective_text,
            instructions.operating_rules,
            instructions.constraints_text,
            instructions.output_contract,
        ):
            if field and field.strip():
                parts.append(field.strip())
    if extra_system and extra_system.strip():
        parts.append(extra_system.strip())
    if not parts:
        return None
    return "\n\n".join(parts)


def build_knowledge_context(chunks: list[dict[str, Any]], max_chars: int = 4000) -> str | None:
    if not chunks:
        return None
    lines: list[str] = ["Contexto de conocimiento empresarial:"]
    total = 0
    for chunk in chunks:
        title = chunk.get("document_name") or chunk.get("titulo") or "Documento"
        content = (chunk.get("content") or chunk.get("extracto") or "")[:800]
        line = f"- [{title}] {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines) if len(lines) > 1 else None


def assemble_messages(
    *,
    user_prompt: str,
    system_instructions: str | None = None,
    knowledge_context: str | None = None,
) -> list[LlmMessage]:
    messages: list[LlmMessage] = []
    user_parts: list[str] = []
    if knowledge_context:
        user_parts.append(knowledge_context)
    if user_prompt.strip():
        user_parts.append(user_prompt.strip())
    content = "\n\n".join(user_parts) if user_parts else user_prompt
    messages.append(LlmMessage(role="user", content=content))
    return messages


def trace_components(
    *,
    has_instructions: bool,
    knowledge_chunk_count: int,
    user_prompt_length: int,
) -> dict[str, Any]:
    return {
        "system_instructions": has_instructions,
        "knowledge_chunks": knowledge_chunk_count,
        "user_prompt_chars": user_prompt_length,
    }
