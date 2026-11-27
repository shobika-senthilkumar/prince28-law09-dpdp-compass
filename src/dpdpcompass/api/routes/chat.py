from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dpdpcompass.api.deps import get_llm_gateway
from dpdpcompass.llm.db.llm_calls import daily_usage
from dpdpcompass.llm.gateway import LLMGateway

router = APIRouter(prefix="/v1", tags=["chat"])

PROMPT_PATH = Path("prompts/chat_system_v1.md")


class ChatRequest(BaseModel):
    message: str


def load_system_prompt() -> str:
    """Load the versioned system prompt for chat."""
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def get_gateway() -> LLMGateway:
    """Provide the configured LLM gateway."""
    return get_llm_gateway()


GATEWAY_DEP = Depends(get_gateway)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    gateway: LLMGateway = GATEWAY_DEP,
) -> StreamingResponse:
    """Stream an answer from the LLM gateway."""
    system_prompt = load_system_prompt()
    prompt = f"{system_prompt}\n\nUser question: {request.message}"

    return StreamingResponse(
        gateway.stream(prompt),
        media_type="text/plain",
    )


@router.get("/usage")
async def usage() -> dict:
    """Return today's LLM usage."""
    return daily_usage(date.today())
