import httpx

from dpdpcompass.config import Settings


def ping_gemini(settings: Settings) -> None:
    url = f"{settings.llm_primary_base_url}chat/completions"
    headers = {"Authorization": f"Bearer {settings.gemini_api_key}"}
    payload = {
        "model": settings.llm_primary_model,
        "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
    }

    response = httpx.post(
        url,
        headers=headers,
        json=payload,
        timeout=settings.llm_timeout_seconds,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    print(f"gemini OK ... {content!r}")


def ping_groq(settings: Settings) -> None:
    url = f"{settings.llm_fallback_base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    payload = {
        "model": settings.llm_fallback_model,
        "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
    }

    response = httpx.post(
        url,
        headers=headers,
        json=payload,
        timeout=settings.llm_timeout_seconds,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    print(f"groq   OK ... {content!r}")


def main() -> None:
    settings = Settings()

    if settings.gemini_api_key:
        try:
            ping_gemini(settings)
        except Exception as exc:
            print(f"gemini ERROR: {exc}")
    else:
        print("gemini SKIP: API key is empty")

    if settings.groq_api_key:
        try:
            ping_groq(settings)
        except Exception as exc:
            print(f"groq   ERROR: {exc}")
    else:
        print("groq   SKIP: API key is empty")


if __name__ == "__main__":
    main()
