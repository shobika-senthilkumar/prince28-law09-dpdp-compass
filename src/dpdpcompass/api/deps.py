from collections.abc import Generator

from dpdpcompass.config import get_settings
from dpdpcompass.db.repository import DocumentRepository
from dpdpcompass.db.session import SessionLocal
from dpdpcompass.llm.gateway import LLMGateway
from dpdpcompass.llm.gemini import GeminiProvider
from dpdpcompass.llm.groq import GroqProvider


def get_document_repository() -> Generator[DocumentRepository, None, None]:
    """Provide a PostgreSQL document repository for a request."""
    with SessionLocal() as session:
        yield DocumentRepository(session)


def get_llm_gateway() -> LLMGateway:
    """Provide the configured Gemini/Groq LLM gateway."""
    settings = get_settings()

    gemini = GeminiProvider(
        api_key=settings.gemini_api_key,
        model=settings.llm_primary_model,
        base_url=settings.llm_primary_base_url,
        timeout=settings.llm_timeout_seconds,
    )
    groq = GroqProvider(
        api_key=settings.groq_api_key,
        model=settings.llm_fallback_model,
        base_url=settings.llm_fallback_base_url,
        timeout=settings.llm_timeout_seconds,
    )

    return LLMGateway([gemini, groq])
