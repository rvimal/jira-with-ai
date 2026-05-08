from __future__ import annotations

from collections.abc import Callable
import time
from typing import TypeVar


T = TypeVar("T")


def retry_call(
    func: Callable[[], T],
    *,
    attempts: int,
    delay_seconds: float,
    retriable_exceptions: tuple[type[Exception], ...],
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except retriable_exceptions as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error