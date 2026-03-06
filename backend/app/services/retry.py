"""
Retry utility with exponential backoff and API key rotation for Gemini API calls.
Handles 429 RESOURCE_EXHAUSTED errors gracefully by switching to fallback keys.
"""
import asyncio
import functools
import random
from typing import TypeVar, Callable, Any
from google import genai
from google.genai import errors
import httpx
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
            should_retry = False
            is_rate_limit = False
            error_msg = str(exc)
            
            # 1. Check for Rate Limit (429) via Specific SDK API Errors
            if isinstance(exc, errors.APIError):
                if exc.code == 429 or "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                    is_rate_limit = True
                    should_retry = True
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                is_rate_limit = True
                should_retry = True

            # 2. Check for Transient Network Errors (e.g. WinError 10054, ConnectionReset, Timeout)
            if isinstance(exc, (ConnectionResetError, ConnectionError, TimeoutError, httpx.NetworkError, httpx.TimeoutException)):
                should_retry = True
            elif "10054" in error_msg or "ConnectionResetError" in error_msg or "forcibly closed" in error_msg:
                should_retry = True

            if not should_retry or attempt == max_retries:
                raise

            if is_rate_limit:
                # If rate limited, rotate the key
                print(f"[Retry] 429 Rate Limit hit. Attempt {attempt + 1}/{max_retries}.")
                rotate_api_key()
                delay = 1.0 if len(settings.GEMINI_API_KEYS) > 1 else min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            else:
                # Standard exponential backoff for network drops
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                print(f"[Retry] Network error ({type(exc).__name__}). Attempt {attempt + 1}/{max_retries}. Retrying in {delay:.1f}s...")
            
            await asyncio.sleep(delay)

    raise last_exception  # type: ignore[misc]
