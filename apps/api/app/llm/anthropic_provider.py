"""Anthropic LLM provider implementation."""

import json
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from app.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a legal information assistant for Indian law.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.content[0].text

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        schema = response_model.model_json_schema()
        structured_prompt = (
            f"{prompt}\n\nRespond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        )
        text = await self.generate(structured_prompt, system_prompt, temperature)
        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            return response_model.model_validate(data)
        raise ValueError("Failed to parse structured response from Anthropic")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not provide embeddings; use a separate embedding provider")
