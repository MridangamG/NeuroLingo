"""
Retry utility with exponential backoff and API key rotation for Gemini API calls.
Handles 429 RESOURCE_EXHAUSTED errors gracefully by switching to fallback keys.
"""
import asyncio
import functools
import random
from typing import TypeVar, Callable, Any
from google import genai
from app.core.config import settings

T = TypeVar("T")

# Global state for key rotation
_current_key_idx = 0
_shared_client = genai.Client(api_key=settings.GEMINI_API_KEYS[_current_key_idx])

def get_gemini_client() -> genai.Client:
    """Returns the currently active Gemini client."""
    global _shared_client
    return _shared_client

def rotate_api_key():
    """Rotates to the next available API key in the configured list."""
    global _current_key_idx, _shared_client
    keys = settings.GEMINI_API_KEYS
    if len(keys) <= 1:
        return # No fallback keys available
        
    _current_key_idx = (_current_key_idx + 1) % len(keys)
    new_key = keys[_current_key_idx]
    
    # Re-initialize the shared client with the new key
    _shared_client = genai.Client(api_key=new_key)
    print(f"[Key Rotation] Switched to fallback API key #{_current_key_idx + 1} / {len(keys)}")


async def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    **kwargs: Any,
) -> T:
    """
    Call `func(*args, **kwargs)` with exponential backoff on failure.
    If a 429 rate limit is hit, it immediately attempts to rotate the API key.
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            # If it's a coroutine, await it
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as exc:
            last_exception = exc
            error_msg = str(exc)
            is_rate_limit = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg

            if not is_rate_limit or attempt == max_retries:
                raise

            # If rate limited, rotate the key
            print(f"[Retry] 429 Rate Limit hit. Attempt {attempt + 1}/{max_retries}.")
            rotate_api_key()
            
            # Shorter backoff if we have a fallback key rotated
            delay = 1.0 if len(settings.GEMINI_API_KEYS) > 1 else min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            print(f"[Retry] Retrying with new key in {delay:.1f}s...")
            await asyncio.sleep(delay)

    raise last_exception  # type: ignore[misc]
