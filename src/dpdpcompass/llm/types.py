from dataclasses import dataclass


class LLMError(Exception):
    """Base error for LLM provider failures."""


class LLMUnavailable(LLMError):
    """Raised when no LLM provider is available."""


@dataclass
class Reply:
    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    fallback_used: bool = False
