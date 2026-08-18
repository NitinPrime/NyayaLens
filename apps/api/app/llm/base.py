"""LLM provider abstraction layer."""

import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from app.llm.grounded_mock import build_structured, generate_text

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class MockLLMProvider(LLMProvider):
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        return generate_text(prompt, system_prompt)

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        return build_structured(response_model, prompt)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        dimension = 64
        vectors = []
        for text in texts:
            tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
            vec = [0.0] * dimension
            for i, token in enumerate(sorted(tokens)):
                vec[i % dimension] += hash(token) % 100 / 100.0
            vectors.append(vec)
        return vectors


def get_llm_provider(provider_name: str, **kwargs: Any) -> LLMProvider:
    if provider_name == "mock":
        return MockLLMProvider()
    if provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(**kwargs)
    if provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(**kwargs)
    raise ValueError(f"Unknown LLM provider: {provider_name}")
