import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

from .db.llm_calls import record_call
from .types import LLMError, LLMUnavailable, Reply

PRICES_USD = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
}

MAX_WAIT = 20.0


@dataclass
class Circuit:
    failures: int = 0
    opened_at: float | None = None

    @property
    def open(self) -> bool:
        if self.opened_at is None:
            return False
        return time.monotonic() - self.opened_at < 30.0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= 2:
            self.opened_at = time.monotonic()

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None


class LLMGateway:
    """Primary/fallback LLM gateway with retry and circuit breaking."""

    def __init__(
        self,
        providers: list,
        *,
        max_attempts: int = 2,
        max_wait: float = MAX_WAIT,
    ) -> None:
        self.providers = providers
        self.max_attempts = max_attempts
        self.max_wait = max_wait
        self.circuits = {provider.name: Circuit() for provider in providers}

    def _cost_inr(self, reply: Reply) -> float:
        price = PRICES_USD.get(reply.model)
        if price is None:
            return 0.0

        input_price, output_price = price
        usd = (
            reply.tokens_in * input_price / 1_000_000 + reply.tokens_out * output_price / 1_000_000
        )
        return usd * 95.0

    async def generate(self, prompt: str, *, purpose: str = "chat") -> Reply:
        request_id = uuid.uuid4().hex
        last_error: Exception | None = None
        fallback_used = False

        for provider_index, provider in enumerate(self.providers):
            circuit = self.circuits[provider.name]

            if circuit.open:
                continue

            if provider_index > 0:
                fallback_used = True

            for attempt in range(self.max_attempts):
                try:
                    reply = await asyncio.wait_for(
                        provider.generate(prompt),
                        timeout=self.max_wait,
                    )

                    circuit.record_success()

                    reply.fallback_used = fallback_used

                    record_call(
                        request_id=request_id,
                        provider=reply.provider,
                        model=reply.model,
                        status="ok",
                        purpose=purpose,
                        tokens_in=reply.tokens_in,
                        tokens_out=reply.tokens_out,
                        latency_ms=reply.latency_ms,
                        cost_inr=self._cost_inr(reply),
                        fallback_used=fallback_used,
                    )

                    return reply

                except Exception as exc:
                    last_error = exc
                    circuit.record_failure()

                    record_call(
                        request_id=request_id,
                        provider=provider.name,
                        model=provider.model,
                        status="error",
                        purpose=purpose,
                        error=str(exc),
                        fallback_used=fallback_used,
                    )

                    if attempt + 1 < self.max_attempts:
                        await asyncio.sleep(0.1)

        raise LLMUnavailable(f"All LLM providers failed: {last_error}")

    async def stream(
        self,
        prompt: str,
        *,
        purpose: str = "chat",
    ) -> AsyncIterator[str]:
        """Stream from the first available provider.

        A provider switch is allowed only before any content is shown.
        """

        request_id = uuid.uuid4().hex

        for provider_index, provider in enumerate(self.providers):
            circuit = self.circuits[provider.name]

            if circuit.open:
                continue

            fallback_used = provider_index > 0
            shown = False

            try:
                started = time.perf_counter()

                async for chunk in provider.stream(prompt):
                    if chunk:
                        shown = True
                        yield chunk

                circuit.record_success()

                record_call(
                    request_id=request_id,
                    provider=provider.name,
                    model=provider.model,
                    status="ok",
                    purpose=purpose,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    fallback_used=fallback_used,
                )

                return

            except Exception as exc:
                circuit.record_failure()

                record_call(
                    request_id=request_id,
                    provider=provider.name,
                    model=provider.model,
                    status="error",
                    purpose=purpose,
                    error=str(exc),
                    fallback_used=fallback_used,
                )

                if shown:
                    raise LLMError("Provider failed after streaming had already started") from exc

        raise LLMUnavailable("No LLM provider is available")
