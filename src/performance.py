import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def log_performance(func: Callable) -> Callable:
    """Decorator to log function execution time."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.debug(
                f"{func.__module__}.{func.__name__} completed in {elapsed:.4f}s"
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.debug(
                f"{func.__module__}.{func.__name__} failed after {elapsed:.4f}s: {e}"
            )
            raise

    return wrapper
