import asyncio

import pytest

from dpdpcompass.llm.gateway import LLMGateway
from dpdpcompass.llm.types import LLMError, LLMUnavailable, Reply


class FakeLLM:
    def __init__(
        self,
        name: str,
        model: str = "test-model",
        responses: list[str] | None = None,
        failures: int = 0,
        chunks: list[str] | None = None,
    ):
        self.name = name
        self.model = model
        self.responses = responses or ["hello"]
        self.failures = failures
        self.chunks = chunks or ["hello"]

        self.calls = 0
        self.stream_calls = 0

    async def generate(self, prompt: str) -> Reply:
        self.calls += 1

        if self.calls <= self.failures:
            raise LLMError(f"{self.name} failed")

        return Reply(
            text=self.responses[min(self.calls - self.failures - 1, len(self.responses) - 1)],
            provider=self.name,
            model=self.model,
            tokens_in=10,
            tokens_out=5,
            latency_ms=10,
        )

    async def stream(self, prompt: str):
        self.stream_calls += 1

        if self.stream_calls <= self.failures:
            raise LLMError(f"{self.name} failed")

        for chunk in self.chunks:
            yield chunk


@pytest.fixture
def no_record(monkeypatch):
    monkeypatch.setattr(
        "dpdpcompass.llm.gateway.record_call",
        lambda **kwargs: None,
    )


@pytest.mark.asyncio
async def test_primary_provider_answers(no_record):
    primary = FakeLLM("gemini")
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])

    reply = await gateway.generate("hello")

    assert reply.text == "hello"
    assert reply.provider == "gemini"
    assert primary.calls == 1
    assert fallback.calls == 0


@pytest.mark.asyncio
async def test_primary_retry_succeeds(no_record):
    primary = FakeLLM("gemini", failures=1)
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback], max_attempts=2)

    reply = await gateway.generate("hello")

    assert reply.provider == "gemini"
    assert primary.calls == 2
    assert fallback.calls == 0


@pytest.mark.asyncio
async def test_primary_failure_uses_fallback(no_record):
    primary = FakeLLM("gemini", failures=2)
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback], max_attempts=2)

    reply = await gateway.generate("hello")

    assert reply.provider == "groq"
    assert reply.fallback_used is True
    assert primary.calls == 2
    assert fallback.calls == 1


@pytest.mark.asyncio
async def test_fallback_not_used_when_primary_succeeds(no_record):
    primary = FakeLLM("gemini")
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])

    reply = await gateway.generate("hello")

    assert reply.fallback_used is False


@pytest.mark.asyncio
async def test_all_providers_fail(no_record):
    primary = FakeLLM("gemini", failures=2)
    fallback = FakeLLM("groq", failures=2)

    gateway = LLMGateway([primary, fallback], max_attempts=2)

    with pytest.raises(LLMUnavailable):
        await gateway.generate("hello")


@pytest.mark.asyncio
async def test_primary_circuit_opens_after_failures(no_record):
    primary = FakeLLM("gemini", failures=10)
    fallback = FakeLLM("groq", failures=10)

    gateway = LLMGateway([primary, fallback], max_attempts=2)

    with pytest.raises(LLMUnavailable):
        await gateway.generate("hello")

    assert gateway.circuits["gemini"].open is True


@pytest.mark.asyncio
async def test_open_circuit_skips_provider(no_record):
    primary = FakeLLM("gemini")
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])
    gateway.circuits["gemini"].opened_at = asyncio.get_running_loop().time()

    reply = await gateway.generate("hello")

    assert reply.provider == "groq"
    assert primary.calls == 0
    assert fallback.calls == 1


@pytest.mark.asyncio
async def test_circuit_closes_after_cooldown(no_record):
    primary = FakeLLM("gemini")
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])

    circuit = gateway.circuits["gemini"]
    circuit.opened_at = 0.0

    assert circuit.open is False


@pytest.mark.asyncio
async def test_success_resets_failures(no_record):
    primary = FakeLLM("gemini")
    gateway = LLMGateway([primary])

    circuit = gateway.circuits["gemini"]
    circuit.failures = 1

    await gateway.generate("hello")

    assert circuit.failures == 0
    assert circuit.opened_at is None


@pytest.mark.asyncio
async def test_generate_records_success(no_record, monkeypatch):
    records = []

    monkeypatch.setattr(
        "dpdpcompass.llm.gateway.record_call",
        lambda **kwargs: records.append(kwargs),
    )

    gateway = LLMGateway([FakeLLM("gemini")])

    await gateway.generate("hello")

    assert records[0]["status"] == "ok"
    assert records[0]["provider"] == "gemini"


@pytest.mark.asyncio
async def test_generate_records_failure(no_record, monkeypatch):
    records = []

    monkeypatch.setattr(
        "dpdpcompass.llm.gateway.record_call",
        lambda **kwargs: records.append(kwargs),
    )

    primary = FakeLLM("gemini", failures=2)
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback], max_attempts=2)

    await gateway.generate("hello")

    assert any(record["status"] == "error" for record in records)


@pytest.mark.asyncio
async def test_stream_primary_provider(no_record):
    primary = FakeLLM("gemini", chunks=["hello", " world"])
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])

    chunks = [chunk async for chunk in gateway.stream("hello")]

    assert chunks == ["hello", " world"]
    assert primary.stream_calls == 1
    assert fallback.stream_calls == 0


@pytest.mark.asyncio
async def test_stream_fallback_before_content(no_record):
    primary = FakeLLM("gemini", failures=1)
    fallback = FakeLLM("groq", chunks=["fallback"])

    gateway = LLMGateway([primary, fallback])

    chunks = [chunk async for chunk in gateway.stream("hello")]

    assert chunks == ["fallback"]
    assert primary.stream_calls == 1
    assert fallback.stream_calls == 1


@pytest.mark.asyncio
async def test_stream_does_not_switch_after_content(no_record):
    primary = FakeLLM("gemini", chunks=["first"])
    fallback = FakeLLM("groq")

    async def broken_stream(prompt):
        yield "first"
        raise LLMError("stream broke")

    primary.stream = broken_stream

    gateway = LLMGateway([primary, fallback])

    with pytest.raises(LLMError, match="already started"):
        [chunk async for chunk in gateway.stream("hello")]

    assert fallback.stream_calls == 0


@pytest.mark.asyncio
async def test_stream_open_circuit_skips_provider(no_record):
    primary = FakeLLM("gemini")
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])
    gateway.circuits["gemini"].opened_at = asyncio.get_running_loop().time()

    chunks = [chunk async for chunk in gateway.stream("hello")]

    assert chunks == ["hello"]
    assert primary.stream_calls == 0
    assert fallback.stream_calls == 1


@pytest.mark.asyncio
async def test_stream_records_success(no_record, monkeypatch):
    records = []

    monkeypatch.setattr(
        "dpdpcompass.llm.gateway.record_call",
        lambda **kwargs: records.append(kwargs),
    )

    gateway = LLMGateway([FakeLLM("gemini")])

    chunks = [chunk async for chunk in gateway.stream("hello")]

    assert chunks == ["hello"]
    assert records[0]["status"] == "ok"


@pytest.mark.asyncio
async def test_stream_records_failure(no_record, monkeypatch):
    records = []

    monkeypatch.setattr(
        "dpdpcompass.llm.gateway.record_call",
        lambda **kwargs: records.append(kwargs),
    )

    primary = FakeLLM("gemini", failures=1)
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])

    chunks = [chunk async for chunk in gateway.stream("hello")]

    assert chunks == ["hello"]
    assert any(record["status"] == "error" for record in records)


@pytest.mark.asyncio
async def test_provider_order_is_preserved(no_record):
    first = FakeLLM("first", responses=["first answer"])
    second = FakeLLM("second", responses=["second answer"])
    third = FakeLLM("third", responses=["third answer"])

    gateway = LLMGateway([first, second, third])

    reply = await gateway.generate("hello")

    assert reply.provider == "first"
    assert second.calls == 0
    assert third.calls == 0


@pytest.mark.asyncio
async def test_open_circuit_blocks_provider_during_cooldown(no_record):
    primary = FakeLLM("gemini")
    fallback = FakeLLM("groq")

    gateway = LLMGateway([primary, fallback])

    circuit = gateway.circuits["gemini"]
    circuit.opened_at = asyncio.get_running_loop().time()

    reply = await gateway.generate("hello")

    assert reply.provider == "groq"
    assert primary.calls == 0
    assert fallback.calls == 1
