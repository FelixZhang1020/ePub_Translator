"""Cached LLM Gateway wrapper for transparent response caching.

This module provides a caching layer for LLM gateways. It wraps any LLMGateway
implementation and adds transparent caching without changing the interface.

Usage:
    # Wrap any gateway with caching
    base_gateway = OpenAIGateway(api_key="...", model="gpt-4o")
    cached_gateway = CachedLLMGateway(base_gateway, project_id="uuid")

    # Use exactly the same as the base gateway
    response = await cached_gateway.call(bundle)  # May hit cache

The cache is project-scoped and fully transparent to callers.
"""

import json
import logging
from typing import AsyncIterator, Optional

from app.core.translation.pipeline.llm_gateway import LLMGateway
from app.core.translation.models.prompt import PromptBundle
from app.core.translation.models.response import LLMResponse, TokenUsage
from app.core.cache.llm_cache import get_cache

logger = logging.getLogger(__name__)


class CachedLLMGateway(LLMGateway):
    """Caching wrapper for LLM gateways.

    Transparently caches LLM responses based on prompt content and parameters.
    Streaming calls bypass the cache.
    """

    def __init__(
        self,
        gateway: LLMGateway,
        project_id: str,
        enable_cache: bool = True,
        ttl_seconds: Optional[int] = None
    ):
        """Initialize cached gateway.

        Args:
            gateway: Base LLM gateway to wrap
            project_id: Project UUID for scoped cache
            enable_cache: Enable/disable caching (useful for testing)
            ttl_seconds: Custom TTL for cache entries (None = use default)
        """
        self._gateway = gateway
        self._project_id = project_id
        self._enable_cache = enable_cache
        self._cache = get_cache(project_id, ttl_seconds)

        logger.info(
            f"[CachedGateway] Initialized for {gateway.provider}/{gateway.model} "
            f"(project={project_id}, cache={'enabled' if enable_cache else 'disabled'})"
        )

    @property
    def provider(self) -> str:
        """Get provider name from underlying gateway."""
        return self._gateway.provider

    @property
    def model(self) -> str:
        """Get model from underlying gateway."""
        return self._gateway.model

    def _prompt_bundle_to_string(self, bundle: PromptBundle) -> str:
        """Convert prompt bundle to canonical string for caching.

        Args:
            bundle: Prompt bundle

        Returns:
            Deterministic string representation
        """
        # Serialize messages to OpenAI format for consistency
        messages = bundle.to_openai_format()

        # Create deterministic representation
        return json.dumps({
            "messages": messages,
            "temperature": bundle.temperature,
            "max_tokens": bundle.max_tokens,
        }, sort_keys=True)

    def _llm_response_to_dict(self, response: LLMResponse) -> dict:
        """Convert LLMResponse to cacheable dict.

        Args:
            response: LLM response object

        Returns:
            Dictionary representation
        """
        return {
            "content": response.content,
            "provider": response.provider,
            "model": response.model,
            "raw_response": response.raw_response,
            "latency_ms": response.latency_ms,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

    def _dict_to_llm_response(self, data: dict) -> LLMResponse:
        """Convert cached dict back to LLMResponse.

        Args:
            data: Dictionary from cache

        Returns:
            Reconstructed LLMResponse
        """
        usage = TokenUsage(**data["usage"]) if data.get("usage") else TokenUsage()

        return LLMResponse(
            content=data["content"],
            provider=data["provider"],
            model=data["model"],
            raw_response=data.get("raw_response"),
            latency_ms=data.get("latency_ms", 0),
            usage=usage,
        )

    async def call(self, bundle: PromptBundle) -> LLMResponse:
        """Make LLM call with caching.

        Args:
            bundle: Prompt bundle

        Returns:
            LLMResponse (from cache or fresh API call)
        """
        # If caching disabled, pass through to base gateway
        if not self._enable_cache:
            return await self._gateway.call(bundle)

        # Try cache first
        prompt_str = self._prompt_bundle_to_string(bundle)

        cached_response = self._cache.get(
            provider=self.provider,
            model=self.model,
            prompt=prompt_str,
            temperature=bundle.temperature,
            max_tokens=bundle.max_tokens,
        )

        if cached_response:
            logger.info(
                f"[CachedGateway] Cache HIT for {self.provider}/{self.model} "
                f"(prompt_hash={self._cache._compute_prompt_hash(prompt_str)})"
            )
            return self._dict_to_llm_response(cached_response)

        # Cache miss - call API
        logger.info(
            f"[CachedGateway] Cache MISS for {self.provider}/{self.model} "
            f"(prompt_hash={self._cache._compute_prompt_hash(prompt_str)})"
        )

        response = await self._gateway.call(bundle)

        # Store in cache
        response_dict = self._llm_response_to_dict(response)
        cache_key = self._cache.set(
            provider=self.provider,
            model=self.model,
            prompt=prompt_str,
            response=response_dict,
            temperature=bundle.temperature,
            max_tokens=bundle.max_tokens,
        )

        logger.debug(
            f"[CachedGateway] Stored response in cache (key={cache_key[:16]}...)"
        )

        return response

    async def stream(self, bundle: PromptBundle) -> AsyncIterator[LLMResponse]:
        """Make streaming LLM call.

        Note: Streaming calls bypass the cache and go directly to the underlying gateway.

        Args:
            bundle: Prompt bundle

        Yields:
            LLMResponse chunks
        """
        # Streaming bypasses cache - delegate to base gateway
        logger.debug(
            f"[CachedGateway] Streaming call (bypassing cache) for {self.provider}/{self.model}"
        )

        async for chunk in self._gateway.stream(bundle):
            yield chunk

    async def health_check(self) -> bool:
        """Check provider availability.

        Returns:
            True if provider is reachable
        """
        return await self._gateway.health_check()

    def get_cache_stats(self) -> dict:
        """Get cache statistics for this project.

        Returns:
            Dictionary with cache stats
        """
        return self._cache.get_stats()

    def clear_cache(self) -> int:
        """Clear all cached responses for this project.

        Returns:
            Number of entries deleted
        """
        count = self._cache.clear_all()
        logger.info(f"[CachedGateway] Cleared {count} cache entries for project {self._project_id}")
        return count

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries.

        Returns:
            Number of expired entries deleted
        """
        count = self._cache.clear_expired()
        logger.info(f"[CachedGateway] Cleared {count} expired cache entries")
        return count
