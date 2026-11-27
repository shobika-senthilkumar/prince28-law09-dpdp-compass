from typing import Protocol

from .types import Reply


class LLMProvider(Protocol):
    """Common interface implemented by Gemini and Groq providers."""

    name: str
    model: str

    async def generate(self, prompt: str) -> Reply:
        """Generate a complete response."""
        ...

    async def stream(self, prompt: str):
        """Stream response chunks."""
        ...
