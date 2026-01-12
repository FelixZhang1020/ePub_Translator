"""LLM Response Caching Service.

This module provides caching for LLM API responses to reduce costs and improve performance.
Cache entries are stored in project-scoped directories and include TTL management.

Cache Structure:
    projects/{project_id}/cache/
    ├── llm_responses/
    │   ├── {hash}.json          # Cached response
    │   └── {hash}.meta.json     # Cache metadata
    └── embeddings/              # Future: embedding cache
        └── {hash}.npy

Cache Key Generation:
    Hash is based on: provider + model + prompt + temperature + other params
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Cached LLM response with metadata."""

    # Response data
    response: dict  # The actual LLM response

    # Cache metadata
    cache_key: str  # Hash of the request
    provider: str  # LLM provider (openai, anthropic, etc.)
    model: str  # Model name
    prompt_hash: str  # Hash of just the prompt content

    # Timestamps
    created_at: float  # Unix timestamp
    accessed_at: float  # Last access timestamp
    access_count: int  # Number of times accessed

    # Expiration
    ttl_seconds: Optional[int]  # Time-to-live in seconds (None = no expiry)

    # Request metadata (for debugging)
    request_metadata: dict  # Original request parameters

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds is None:
            return False

        age_seconds = time.time() - self.created_at
        return age_seconds > self.ttl_seconds

    def update_access(self) -> None:
        """Update access timestamp and count."""
        self.accessed_at = time.time()
        self.access_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)


class LLMCache:
    """Manage LLM response caching for a project."""

    # Default TTL: 30 days
    DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60

    # Cache subdirectory names
    RESPONSES_DIR = "llm_responses"
    EMBEDDINGS_DIR = "embeddings"

    def __init__(self, project_id: str, ttl_seconds: Optional[int] = None):
        """Initialize cache for a project.

        Args:
            project_id: Project UUID
            ttl_seconds: Default TTL in seconds (None = use default)
        """
        self.project_id = project_id
        self.ttl_seconds = ttl_seconds or self.DEFAULT_TTL_SECONDS

        # Cache directories
        from app.core.project_storage import ProjectStorage
        self.cache_dir = ProjectStorage.get_cache_dir(project_id)
        self.responses_dir = self.cache_dir / self.RESPONSES_DIR
        self.embeddings_dir = self.cache_dir / self.EMBEDDINGS_DIR

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create cache directories if they don't exist."""
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

    def _compute_cache_key(
        self,
        provider: str,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Compute cache key from request parameters.

        Args:
            provider: LLM provider name
            model: Model name
            prompt: Prompt text
            temperature: Temperature parameter
            **kwargs: Additional parameters to include in hash

        Returns:
            SHA256 hash as hex string
        """
        # Create deterministic string representation
        params = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            **kwargs
        }

        # Sort keys for deterministic hashing
        params_str = json.dumps(params, sort_keys=True)

        # Compute SHA256 hash
        return hashlib.sha256(params_str.encode()).hexdigest()

    def _compute_prompt_hash(self, prompt: str) -> str:
        """Compute hash of just the prompt content.

        Args:
            prompt: Prompt text

        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file.

        Args:
            cache_key: Cache key hash

        Returns:
            Path to cache JSON file
        """
        return self.responses_dir / f"{cache_key}.json"

    def get(
        self,
        provider: str,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Optional[dict]:
        """Get cached response if available.

        Args:
            provider: LLM provider name
            model: Model name
            prompt: Prompt text
            temperature: Temperature parameter
            **kwargs: Additional parameters

        Returns:
            Cached response dict or None if not found/expired
        """
        cache_key = self._compute_cache_key(provider, model, prompt, temperature, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            # Load cache entry
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entry = CacheEntry.from_dict(data)

            # Check expiration
            if entry.is_expired():
                # Delete expired entry
                cache_path.unlink()
                return None

            # Update access metadata
            entry.update_access()

            # Save updated metadata
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)

            return entry.response

        except (json.JSONDecodeError, KeyError, IOError):
            # Invalid cache file, delete it
            cache_path.unlink(missing_ok=True)
            return None

    def set(
        self,
        provider: str,
        model: str,
        prompt: str,
        response: dict,
        temperature: Optional[float] = None,
        ttl_seconds: Optional[int] = None,
        **kwargs
    ) -> str:
        """Store LLM response in cache.

        Args:
            provider: LLM provider name
            model: Model name
            prompt: Prompt text
            response: LLM response to cache
            temperature: Temperature parameter
            ttl_seconds: Custom TTL (None = use default)
            **kwargs: Additional parameters

        Returns:
            Cache key (hash)
        """
        cache_key = self._compute_cache_key(provider, model, prompt, temperature, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        prompt_hash = self._compute_prompt_hash(prompt)

        # Create cache entry
        entry = CacheEntry(
            response=response,
            cache_key=cache_key,
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            ttl_seconds=ttl_seconds or self.ttl_seconds,
            request_metadata={
                "temperature": temperature,
                **kwargs
            }
        )

        # Save to file
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)

        return cache_key

    def invalidate(self, cache_key: str) -> bool:
        """Invalidate (delete) a specific cache entry.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if entry was deleted, False if not found
        """
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear_all(self) -> int:
        """Clear all cache entries for this project.

        Returns:
            Number of entries deleted
        """
        count = 0
        for cache_file in self.responses_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def clear_expired(self) -> int:
        """Clear all expired cache entries.

        Returns:
            Number of expired entries deleted
        """
        count = 0
        for cache_file in self.responses_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                entry = CacheEntry.from_dict(data)
                if entry.is_expired():
                    cache_file.unlink()
                    count += 1

            except (json.JSONDecodeError, KeyError, IOError):
                # Invalid file, delete it
                cache_file.unlink()
                count += 1

        return count

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = 0
        expired_entries = 0
        total_size_bytes = 0
        total_accesses = 0

        oldest_entry = None
        newest_entry = None

        for cache_file in self.responses_dir.glob("*.json"):
            try:
                total_size_bytes += cache_file.stat().st_size

                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                entry = CacheEntry.from_dict(data)
                total_entries += 1
                total_accesses += entry.access_count

                if entry.is_expired():
                    expired_entries += 1

                # Track oldest/newest
                if oldest_entry is None or entry.created_at < oldest_entry:
                    oldest_entry = entry.created_at
                if newest_entry is None or entry.created_at > newest_entry:
                    newest_entry = entry.created_at

            except (json.JSONDecodeError, KeyError, IOError):
                pass

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "total_accesses": total_accesses,
            "avg_accesses_per_entry": round(total_accesses / total_entries, 2) if total_entries > 0 else 0,
            "oldest_entry_age_days": round((time.time() - oldest_entry) / 86400, 1) if oldest_entry else 0,
            "newest_entry_age_days": round((time.time() - newest_entry) / 86400, 1) if newest_entry else 0,
        }


# Global cache instances (keyed by project_id)
_cache_instances: dict[str, LLMCache] = {}


def get_cache(project_id: str, ttl_seconds: Optional[int] = None) -> LLMCache:
    """Get or create cache instance for a project.

    Args:
        project_id: Project UUID
        ttl_seconds: Default TTL in seconds

    Returns:
        LLMCache instance
    """
    if project_id not in _cache_instances:
        _cache_instances[project_id] = LLMCache(project_id, ttl_seconds)
    return _cache_instances[project_id]


def clear_cache_instance(project_id: str) -> None:
    """Remove cache instance from memory.

    Args:
        project_id: Project UUID
    """
    if project_id in _cache_instances:
        del _cache_instances[project_id]
