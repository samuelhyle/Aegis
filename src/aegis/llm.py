from __future__ import annotations

import asyncio
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, ClassVar, cast

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Standardized LLM response wrapper."""

    content: str
    raw: dict[str, Any] | None = None
    model: str | None = None
    usage: dict[str, Any] | None = None
    cost_usd: float = Field(default=0.0, description="Estimated cost in USD")
    latency_ms: float = Field(default=0.0, description="Response latency in milliseconds")


class TokenUsage(BaseModel):
    """Token usage tracking."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    # Model pricing per 1M tokens (input, output) - update as needed
    # Local models (ollama) have zero cost
    PRICING: ClassVar[dict[str, tuple[float, float]]] = {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4-turbo": (10.00, 30.00),
        "gpt-3.5-turbo": (0.50, 1.50),
        "gemma4:26b": (0.0, 0.0),
        "llama3": (0.0, 0.0),
        "mistral": (0.0, 0.0),
        "MiniMax-M3": (0.39, 1.20),
        "MiniMax-M2.7": (0.52, 1.56),
        "MiniMax-M1": (0.52, 1.56),
    }

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> LLMResponse:
        """Complete a chat/completion request with retry logic."""
        raise NotImplementedError

    @abstractmethod
    async def structured_output(
        self,
        system: str,
        user: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> BaseModel:
        """Request structured output validated against a Pydantic model with retry logic."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider display name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Default model name for this provider."""
        raise NotImplementedError

    def _calculate_cost(self, usage: dict[str, Any] | None) -> float:
        """Calculate estimated cost from token usage."""
        if not usage:
            return 0.0

        model = self.model_name
        pricing = self.PRICING.get(model, (0.0, 0.0))
        input_cost_per_m, output_cost_per_m = pricing

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        cost = (prompt_tokens / 1_000_000) * input_cost_per_m + (completion_tokens / 1_000_000) * output_cost_per_m
        return round(cost, 6)

    async def _retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0,
        *args,
        **kwargs,
    ):
        """Execute a function with exponential backoff retry."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    await asyncio.sleep(delay)
                else:
                    raise last_exception
        raise last_exception


class MockProvider(LLMProvider):
    """Mock LLM provider for development and testing without API keys."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-0.1.0"

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> LLMResponse:
        # Simple deterministic mock based on input content
        combined = f"{system}\n{user}"
        word_count = len(combined.split())
        mock_content = f"MVP mock response: {word_count} words processed. System: {system[:20]}... User: {user[:30]}..."
        return LLMResponse(
            content=mock_content,
            model=self.model_name,
            usage={"prompt_tokens": word_count, "completion_tokens": 10, "total_tokens": word_count + 10},
            cost_usd=0.0,
            latency_ms=1.0,
        )

    async def structured_output(
        self,
        system: str,
        user: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> BaseModel:
        # Return a minimal valid instance with defaults for required fields
        defaults = {
            "patient_id": "mock-patient",
            "question": user[:50] if user else "investigation",
            "conclusion": "MVP mock investigation completed.",
            "evidence": [],
            "confidence": 0.5,
            "review_required": True,
            "trace_id": "mock-trace-id",
            "generated_at": datetime.now(timezone.utc),
            "agent_results": [],
        }
        # Remove fields not in the target model
        valid_defaults = {k: v for k, v in defaults.items() if k in response_model.model_fields}
        return cast(BaseModel, response_model.model_validate(valid_defaults))


class OpenAIProvider(LLMProvider):
    """OpenAI provider abstraction - requires OPENAI_API_KEY env var."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self._model_name = model_name

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> LLMResponse:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        async def _call():
            client = OpenAI(api_key=api_key)
            start = time.perf_counter()
            response = client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=temperature,
            )
            latency_ms = (time.perf_counter() - start) * 1000

            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            cost = self._calculate_cost(usage)

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self._model_name,
                usage=usage,
                cost_usd=cost,
                latency_ms=latency_ms,
            )

        return await self._retry_with_backoff(_call, max_retries)

    async def structured_output(
        self,
        system: str,
        user: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> BaseModel:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        async def _call():
            client = OpenAI(api_key=api_key)
            # Use the beta parse method for structured output (OpenAI SDK >= 1.10)
            response = client.beta.chat.completions.parse(
                model=self._model_name,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=temperature,
                response_format=response_model,
            )
            return cast(BaseModel, response.choices[0].message.parsed)

        return await self._retry_with_backoff(_call, max_retries)


class LocalProvider(LLMProvider):
    """Local LLM provider via Ollama - runs Gemma, Llama, Mistral, etc. locally."""

    # Local models have zero API cost
    PRICING: ClassVar[dict[str, tuple[float, float]]] = {
        "gemma4:26b": (0.0, 0.0),
        "llama3": (0.0, 0.0),
        "mistral": (0.0, 0.0),
    }

    def __init__(self, model_name: str = "gemma4:26b", base_url: str = "http://localhost:11434"):
        self._model_name = model_name
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "local"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_retries: int = 2,
    ) -> LLMResponse:
        import httpx

        async def _call():
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self._model_name,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "stream": False,
                }
                start = time.perf_counter()
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                latency_ms = (time.perf_counter() - start) * 1000
                content = data.get("message", {}).get("content", "")

                # Ollama returns token counts in the response
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                }
                cost = 0.0  # Local models have zero cost
                return LLMResponse(
                    content=content,
                    model=self._model_name,
                    usage=usage,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                )

        return await self._retry_with_backoff(_call, max_retries)

    async def structured_output(
        self,
        system: str,
        user: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> BaseModel:
        import json

        import httpx

        # Build a JSON schema instruction for the model
        schema = response_model.model_json_schema()
        schema_prompt = (
            f"\n\nYou MUST respond with valid JSON that matches this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Respond ONLY with the JSON object, no other text."
        )

        async def _call():
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self._model_name,
                    "messages": [
                        {"role": "system", "content": system + schema_prompt},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "format": "json",
                    "stream": False,
                }
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get("message", {}).get("content", "")

                try:
                    parsed = json.loads(content)
                    return cast(BaseModel, response_model.model_validate(parsed))
                except (json.JSONDecodeError, ValueError) as e:
                    raise ValueError(f"Failed to parse LLM JSON output: {e}\nContent: {content}")

        return await self._retry_with_backoff(_call, max_retries)


class MLXProvider(LLMProvider):
    """Native Apple Silicon LLM provider via mlx-lm."""

    PRICING: ClassVar[dict[str, tuple[float, float]]] = {
        "gemma-4-26b-a4b-it-4bit": (0.0, 0.0),
        "gemma-3-1b-it-4bit": (0.0, 0.0),
        "qwen3.5:27b": (0.0, 0.0),
    }

    def __init__(
        self,
        model_path: str | None = None,
        model_name: str | None = None,
    ):
        self._model_path = model_path or os.getenv(
            "MLX_MODEL_PATH",
            os.getenv("LLM_MODEL", "mlx-community/gemma-4-26b-a4b-it-4bit"),
        )
        self._model_name = model_name or os.getenv("LLM_MODEL", "gemma-4-26b")
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self):
        """Lazy-load the model."""
        if self._model is None:
            from mlx_lm import load

            self._model, self._tokenizer = load(self._model_path)

    @property
    def name(self) -> str:
        return "mlx"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> LLMResponse:
        from mlx_lm import generate
        from mlx_lm.generate import make_sampler

        async def _call():
            self._ensure_loaded()
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            text = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            sampler = make_sampler(temp=temperature)
            start = time.perf_counter()
            response = generate(
                self._model,
                self._tokenizer,
                prompt=text,
                max_tokens=2048,
                sampler=sampler,
            )
            latency_ms = (time.perf_counter() - start) * 1000

            # Clean up end tokens
            content = response.split("<end_of_turn>")[0].strip()

            est_tokens = len(content.split()) * 1.3
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": int(est_tokens),
                "total_tokens": int(est_tokens),
            }
            return LLMResponse(
                content=content,
                model=self._model_name,
                usage=usage,
                cost_usd=0.0,
                latency_ms=latency_ms,
            )

        return await self._retry_with_backoff(_call, max_retries)

    async def structured_output(
        self,
        system: str,
        user: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> BaseModel:
        import json

        from mlx_lm import generate
        from mlx_lm.generate import make_sampler

        schema = response_model.model_json_schema()
        schema_prompt = (
            f"\n\nYou MUST respond with valid JSON that matches this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Respond ONLY with the JSON object, no other text."
        )

        async def _call():
            self._ensure_loaded()
            messages = [
                {"role": "system", "content": system + schema_prompt},
                {"role": "user", "content": user},
            ]
            text = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            sampler = make_sampler(temp=temperature)
            response = generate(
                self._model,
                self._tokenizer,
                prompt=text,
                max_tokens=4096,
                sampler=sampler,
            )

            # Clean and parse
            content = response.split("<end_of_turn>")[0].strip()
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            return cast(BaseModel, response_model.model_validate(parsed))

        return await self._retry_with_backoff(_call, max_retries)


class MiniMaxProvider(LLMProvider):
    """MiniMax LLM provider - OpenAI-compatible API at https://api.minimax.io/v1."""

    PRICING: ClassVar[dict[str, tuple[float, float]]] = {
        "MiniMax-M3": (0.39, 1.20),
        "MiniMax-M2.7": (0.52, 1.56),
        "MiniMax-M1": (0.52, 1.56),
    }

    def __init__(
        self,
        model_name: str = "MiniMax-M3",
        base_url: str = "https://api.minimax.io/v1",
        api_key: str | None = None,
    ):
        self._model_name = model_name
        self._base_url = base_url
        self._api_key = api_key or os.getenv("MINIMAX_API_KEY", "")

    @property
    def name(self) -> str:
        return "minimax"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> LLMResponse:
        from openai import OpenAI

        if not self._api_key:
            raise ValueError("MINIMAX_API_KEY environment variable not set")

        async def _call():
            client = OpenAI(api_key=self._api_key, base_url=self._base_url)
            start = time.perf_counter()
            response = client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=temperature,
            )
            latency_ms = (time.perf_counter() - start) * 1000

            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            cost = self._calculate_cost(usage)

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self._model_name,
                usage=usage,
                cost_usd=cost,
                latency_ms=latency_ms,
            )

        return await self._retry_with_backoff(_call, max_retries)

    async def structured_output(
        self,
        system: str,
        user: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> BaseModel:
        import json

        from openai import OpenAI

        if not self._api_key:
            raise ValueError("MINIMAX_API_KEY environment variable not set")

        schema = response_model.model_json_schema()
        schema_prompt = (
            f"\n\nYou MUST respond with valid JSON that matches this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Respond ONLY with the JSON object, no other text."
        )

        async def _call():
            client = OpenAI(api_key=self._api_key, base_url=self._base_url)
            response = client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system + schema_prompt},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""

            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            return cast(BaseModel, response_model.model_validate(parsed))

        return await self._retry_with_backoff(_call, max_retries)


class ProviderFactory:
    """Factory for creating LLM provider instances from config."""

    _providers: ClassVar[dict[str, type[LLMProvider]]] = {
        "mock": MockProvider,
        "openai": OpenAIProvider,
        "local": LocalProvider,
        "mlx": MLXProvider,
        "minimax": MiniMaxProvider,
    }

    @classmethod
    def create(
        cls,
        provider_type: str | None = None,
        **kwargs: Any,
    ) -> LLMProvider:
        """Create a provider instance based on type string."""
        type_ = provider_type or os.getenv("LLM_PROVIDER", "mock")
        provider_class = cls._providers.get(type_)
        if not provider_class:
            raise ValueError(f"Unknown LLM provider: {type_}")

        # Pass model name from env if not explicitly provided
        if "model_name" not in kwargs and type_ == "local":
            kwargs["model_name"] = os.getenv("LLM_MODEL", "gemma4:26b")
        if "base_url" not in kwargs and type_ == "local":
            kwargs["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if type_ == "mlx" and "model_path" not in kwargs:
            kwargs["model_path"] = os.getenv("MLX_MODEL_PATH", os.getenv("LLM_MODEL", ""))
        if type_ == "minimax":
            if "model_name" not in kwargs:
                kwargs["model_name"] = os.getenv("LLM_MODEL", "MiniMax-M3")
            if "api_key" not in kwargs:
                kwargs["api_key"] = os.getenv("MINIMAX_API_KEY", "")
            if "base_url" not in kwargs:
                kwargs["base_url"] = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")

        return provider_class(**kwargs)

    @classmethod
    def from_env(cls) -> LLMProvider:
        """Create provider from LLM_PROVIDER env var."""
        return cls.create(os.getenv("LLM_PROVIDER", "mock"))
