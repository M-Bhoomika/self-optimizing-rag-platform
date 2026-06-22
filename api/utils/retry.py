"""Retry helpers for transient failures."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_call(
    func: Callable[[], T],
    attempts: int = 3,
    delay_seconds: float = 0.05,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last_error: BaseException | None = None
    for attempt in range(attempts):
        try:
            return func()
        except exceptions as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(delay_seconds * (attempt + 1))
    assert last_error is not None
    raise last_error
