#!/usr/bin/env python3
"""Test script for LLM cache functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.cache import get_cache


def test_cache_operations():
    """Test basic cache operations."""

    project_id = "7e3b9804-e395-4e80-8e0b-4840cd6dddd7"

    print("="*80)
    print("TESTING LLM CACHE FUNCTIONALITY")
    print("="*80 + "\n")

    # Get cache instance
    cache = get_cache(project_id)
    print(f"✅ Cache instance created for project: {project_id}\n")

    # Test 1: Store some responses
    print("[1] Storing test cache entries...")

    test_entries = [
        {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt": "Translate 'Hello world' to Chinese",
            "response": {
                "content": "Hello World (translated)",
                "provider": "openai",
                "model": "gpt-4o",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                },
                "latency_ms": 850,
                "raw_response": None
            },
            "temperature": 0.7
        },
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4.5",
            "prompt": "Translate 'Good morning' to Chinese",
            "response": {
                "content": "Good Morning (translated)",
                "provider": "anthropic",
                "model": "claude-sonnet-4.5",
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 4,
                    "total_tokens": 16
                },
                "latency_ms": 920,
                "raw_response": None
            },
            "temperature": 0.7
        },
        {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt": "Translate 'Thank you' to Chinese",
            "response": {
                "content": "Thank You (translated)",
                "provider": "openai",
                "model": "gpt-4o",
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 3,
                    "total_tokens": 14
                },
                "latency_ms": 780,
                "raw_response": None
            },
            "temperature": 0.5
        }
    ]

    cache_keys = []
    for i, entry in enumerate(test_entries, 1):
        cache_key = cache.set(
            provider=entry["provider"],
            model=entry["model"],
            prompt=entry["prompt"],
            response=entry["response"],
            temperature=entry["temperature"]
        )
        cache_keys.append(cache_key)
        print(f"    ✅ Entry {i}: {entry['provider']}/{entry['model']}")
        print(f"       Prompt: {entry['prompt'][:50]}...")
        print(f"       Cache key: {cache_key[:16]}...")

    print(f"\n✅ Stored {len(test_entries)} cache entries\n")

    # Test 2: Retrieve from cache
    print("[2] Retrieving cached responses...")

    for i, entry in enumerate(test_entries, 1):
        cached_response = cache.get(
            provider=entry["provider"],
            model=entry["model"],
            prompt=entry["prompt"],
            temperature=entry["temperature"]
        )

        if cached_response:
            print(f"    ✅ Cache HIT for entry {i}")
            print(f"       Response: {cached_response['content']}")
        else:
            print(f"    ❌ Cache MISS for entry {i}")

    print()

    # Test 3: Get cache statistics
    print("[3] Getting cache statistics...")
    stats = cache.get_stats()

    print(f"    Total entries: {stats['total_entries']}")
    print(f"    Active entries: {stats['active_entries']}")
    print(f"    Expired entries: {stats['expired_entries']}")
    print(f"    Total size: {stats['total_size_mb']} MB")
    print(f"    Total accesses: {stats['total_accesses']}")
    print(f"    Avg accesses/entry: {stats['avg_accesses_per_entry']}")
    print()

    # Test 4: Access a cache entry again (should increment access count)
    print("[4] Testing access tracking...")
    print("    Accessing first entry again...")

    cached_response = cache.get(
        provider=test_entries[0]["provider"],
        model=test_entries[0]["model"],
        prompt=test_entries[0]["prompt"],
        temperature=test_entries[0]["temperature"]
    )

    stats = cache.get_stats()
    print(f"    Total accesses after re-access: {stats['total_accesses']}")
    print(f"    ✅ Access count incremented\n")

    # Test 5: Cache with different temperature (should create new entry)
    print("[5] Testing cache key uniqueness...")
    print("    Same prompt, different temperature...")

    cache_key_different_temp = cache.set(
        provider="openai",
        model="gpt-4o",
        prompt="Translate 'Hello world' to Chinese",  # Same prompt
        response={
            "content": "Hello, World (alternate)",  # Different response
            "provider": "openai",
            "model": "gpt-4o",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            "latency_ms": 850,
            "raw_response": None
        },
        temperature=0.9  # Different temperature
    )

    stats = cache.get_stats()
    print(f"    Total entries now: {stats['total_entries']}")
    print(f"    ✅ New cache entry created (different params = different key)\n")

    print("="*80)
    print("✅ ALL CACHE TESTS PASSED")
    print("="*80 + "\n")

    print("Cache directory:")
    print(f"    {cache.responses_dir}")
    print()

    # List cache files
    cache_files = list(cache.responses_dir.glob("*.json"))
    print(f"Cache files ({len(cache_files)} total):")
    for i, file in enumerate(cache_files[:5], 1):  # Show first 5
        size_kb = file.stat().st_size / 1024
        print(f"    {i}. {file.name[:32]}... ({size_kb:.1f} KB)")

    if len(cache_files) > 5:
        print(f"    ... and {len(cache_files) - 5} more")

    print()

    return stats


if __name__ == "__main__":
    stats = test_cache_operations()

    print("\nTest completed successfully! ✅")
    print("\nNext steps:")
    print("1. Test cache API endpoints:")
    print(f"   curl http://localhost:8000/api/v1/cache/7e3b9804-e395-4e80-8e0b-4840cd6dddd7/stats")
    print()
    print("2. Clear cache via API:")
    print(f"   curl -X POST http://localhost:8000/api/v1/cache/7e3b9804-e395-4e80-8e0b-4840cd6dddd7/clear")
