from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from dpdpcompass.api.main import app
from dpdpcompass.api.routes.chat import get_gateway


class StreamingFakeGateway:
    async def stream(
        self,
        prompt: str,
        *,
        purpose: str = "chat",
    ) -> AsyncIterator[str]:
        yield "Hello "
        yield "from DPDP Compass."


class PromptFakeGateway:
    def __init__(self) -> None:
        self.prompt = ""

    async def stream(
        self,
        prompt: str,
        *,
        purpose: str = "chat",
    ) -> AsyncIterator[str]:
        self.prompt = prompt
        yield "OK"


def test_chat_route_streams_response():
    app.dependency_overrides[get_gateway] = lambda: StreamingFakeGateway()

    try:
        client = TestClient(app)

        response = client.post(
            "/v1/chat",
            json={"message": "What is the DPDP Act?"},
        )

        assert response.status_code == 200
        assert response.text == "Hello from DPDP Compass."
    finally:
        app.dependency_overrides.clear()


def test_chat_includes_system_prompt():
    gateway = PromptFakeGateway()
    app.dependency_overrides[get_gateway] = lambda: gateway

    try:
        client = TestClient(app)

        response = client.post(
            "/v1/chat",
            json={"message": "What is DPDP?"},
        )

        assert response.status_code == 200
        assert "You are the assistant inside DPDP Compass." in gateway.prompt
        assert "What is DPDP?" in gateway.prompt
    finally:
        app.dependency_overrides.clear()
