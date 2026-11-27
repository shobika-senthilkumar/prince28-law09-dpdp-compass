import time

import httpx

from .types import LLMError, Reply


class GeminiProvider:
    """Gemini provider using the OpenAI-compatible Gemini endpoint."""

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def generate(self, prompt: str) -> Reply:
        started = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()

        except httpx.HTTPError as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc

        data = response.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return Reply(
            text=choice["message"]["content"],
            provider=self.name,
            model=self.model,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
