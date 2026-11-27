import json
import time
from collections.abc import AsyncIterator

import httpx

from .types import LLMError, Reply


class GroqProvider:
    """Groq provider using its OpenAI-compatible endpoint."""

    name = "groq"

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
            raise LLMError(f"Groq request failed: {exc}") from exc

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

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response text chunks from Groq."""
        try:
            async with (
                httpx.AsyncClient(timeout=self.timeout) as client,
                client.stream(
                    "POST",
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
                        "stream": True,
                    },
                ) as response,
            ):
                if response.status_code != 200:
                    await response.aread()
                    raise LLMError(f"Groq request failed: HTTP {response.status_code}")

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    payload = line[5:].strip()

                    if payload == "[DONE]":
                        return

                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    for choice in data.get("choices", []):
                        piece = choice.get("delta", {}).get("content") or ""
                        if piece:
                            yield piece

        except httpx.HTTPError as exc:
            raise LLMError(f"Groq stream failed: {exc}") from exc
