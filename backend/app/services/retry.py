"""
Retry utility with exponential backoff for Gemini API calls.
Handles 429 RESOURCE_EXHAUSTED errors gracefully.
"""
import asyncio
import functools
import random
from typing import TypeVar, Callable, Any

T = TypeVar("T")


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
    Works for both sync and async callables.
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

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            print(f"[Retry] Rate limited. Attempt {attempt + 1}/{max_retries}. "
                  f"Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)

    raise last_exception  # type: ignore[misc]
