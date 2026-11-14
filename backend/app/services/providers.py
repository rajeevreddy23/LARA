"""Swappable async model boundary. No tool is executed by a provider."""
import asyncio
from typing import Protocol, AsyncIterator
from app.config import settings


class ProviderUnavailable(RuntimeError):
    pass


class ModelProvider(Protocol):
    configured: bool
    model_name: str

    async def complete(self, system: str, messages: list[dict], schema: dict | None = None) -> str: ...
    def stream(self, system: str, messages: list[dict]) -> AsyncIterator[str]: ...


class GeminiProvider:
    def __init__(self):
        self.configured = bool(settings.GEMINI_API_KEY.strip())
        self.model_name = settings.MODEL_NAME

    def _client(self):
        from google import genai
        return genai.Client(api_key=settings.GEMINI_API_KEY,
                            http_options={"timeout": int(settings.MODEL_TIMEOUT_SECONDS * 1000)})

    def _contents(self, messages):
        return [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in messages if m["role"] in ("assistant", "user")]

    def _config(self, system, schema=None):
        config = {"system_instruction": system, "temperature": settings.TEMPERATURE,
                  "max_output_tokens": settings.MAX_OUTPUT_TOKENS}
        if schema:
            config.update(response_mime_type="application/json", response_json_schema=schema, temperature=0)
        return config

    async def complete(self, system, messages, schema=None):
        try:
            async with asyncio.timeout(settings.MODEL_TIMEOUT_SECONDS):
                async with self._client().aio as client:
                    response = await client.models.generate_content(model=self.model_name,
                        contents=self._contents(messages), config=self._config(system, schema))
        except Exception as exc:
            raise ProviderUnavailable("Model provider is unavailable.") from exc
        return response.text or ""

    async def stream(self, system, messages):
        async with asyncio.timeout(settings.MODEL_TIMEOUT_SECONDS):
            async with self._client().aio as client:
                async for chunk in await client.models.generate_content_stream(model=self.model_name,
                    contents=self._contents(messages), config=self._config(system)):
                    if chunk.text:
                        yield chunk.text


def create_provider() -> ModelProvider:
    if settings.AI_PROVIDER != "gemini":
        raise ValueError("Unsupported AI_PROVIDER; register its ModelProvider implementation first.")
    return GeminiProvider()
