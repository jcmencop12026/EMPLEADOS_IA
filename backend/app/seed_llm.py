"""Bootstrap de proveedores IA y tarifas por defecto — Paquete B."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.finops_models import FinOpsRate
from app.gateway.secrets import build_env_secret_ref
from app.llm_models import LlmProviderConfig


def bootstrap_llm(db: Session, organization_id: str) -> None:
    if db.query(LlmProviderConfig).filter(LlmProviderConfig.organization_id == organization_id).first():
        return

    openai = LlmProviderConfig(
        organization_id=organization_id,
        name="OpenAI (principal)",
        provider_type="openai",
        model_default="gpt-4o-mini",
        endpoint="https://api.openai.com/v1/chat/completions",
        timeout_seconds=settings.llm_default_timeout_seconds,
        priority=10,
        is_enabled=True,
        is_fallback=False,
        secret_ref=build_env_secret_ref("OPENAI_API_KEY"),
    )
    ollama = LlmProviderConfig(
        organization_id=organization_id,
        name="Ollama (local)",
        provider_type="ollama",
        model_default="llama3.2",
        endpoint=settings.ollama_base_url,
        timeout_seconds=settings.llm_default_timeout_seconds,
        priority=100,
        is_enabled=True,
        is_fallback=True,
        secret_ref=None,
    )
    db.add(openai)
    db.add(ollama)

    if not db.query(FinOpsRate).filter(
        FinOpsRate.organization_id == organization_id,
        FinOpsRate.provider == "openai",
        FinOpsRate.model_service == "gpt-4o-mini",
    ).first():
        db.add(
            FinOpsRate(
                organization_id=organization_id,
                provider="openai",
                model_service="gpt-4o-mini",
                category="Modelo IA",
                price_input=Decimal("0.00015"),
                price_output=Decimal("0.0006"),
                currency="USD",
                active=True,
            )
        )
    if not db.query(FinOpsRate).filter(
        FinOpsRate.organization_id == organization_id,
        FinOpsRate.provider == "ollama",
    ).first():
        db.add(
            FinOpsRate(
                organization_id=organization_id,
                provider="ollama",
                model_service="llama3.2",
                category="Modelo IA",
                price_input=Decimal("0"),
                price_output=Decimal("0"),
                currency="USD",
                active=True,
            )
        )

    db.commit()
