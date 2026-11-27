from datetime import date

from sqlalchemy import func, select

from dpdpcompass.db.models import LlmCall
from dpdpcompass.db.session import SessionLocal


def record_call(
    *,
    request_id: str,
    provider: str,
    model: str,
    status: str,
    purpose: str = "chat",
    prompt_version: str = "v1",
    error: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
    latency_ms: int = 0,
    cost_inr: float = 0.0,
    fallback_used: bool = False,
) -> None:
    """Write one LLM call to the database."""

    with SessionLocal() as session:
        session.add(
            LlmCall(
                request_id=request_id,
                provider=provider,
                model=model,
                purpose=purpose,
                prompt_version=prompt_version,
                status=status,
                error=error,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                cost_inr=cost_inr,
                fallback_used=fallback_used,
            )
        )
        session.commit()


def daily_usage(day: date | None = None) -> dict:
    """Return aggregated LLM usage for one day."""

    day = day or date.today()

    with SessionLocal() as session:
        row = session.execute(
            select(
                func.count(LlmCall.id),
                func.coalesce(func.sum(LlmCall.tokens_in), 0),
                func.coalesce(func.sum(LlmCall.tokens_out), 0),
                func.coalesce(func.sum(LlmCall.cost_inr), 0),
            ).where(func.date(LlmCall.created_at) == day)
        ).one()

    return {
        "calls": row[0],
        "tokens_in": row[1],
        "tokens_out": row[2],
        "rupees": float(row[3]),
    }
