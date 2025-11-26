from __future__ import annotations
import json
import logging
import os
import time
from pathlib import Path
from datetime import datetime
from functools import wraps

"""
helper_scripts package - lightweight common utilities used by the Hidden Gems Leaderboard Bot.

Keep this file small and dependency-free so it is safe to import in scripts and unit tests.
"""


__all__ = [
    "get_logger",
    "ensure_dir",
    "read_json",
    "write_json",
    "read_text",
    "write_text",
    "chunks",
    "retry",
    "timestamp_iso",
    "safe_cast",
    "is_truthy",
    "__version__",
]

__version__ = "0.1.0"

from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

T = TypeVar("T")


def get_logger(name: Optional[str] = None, level: Optional[int] = logging.INFO) -> logging.Logger:
    """Return a module logger configured with a simple handler if none exists."""
    name = name or __name__
    logger = logging.getLogger(name)
    if logger.handlers:
        # Assume already configured externally
        if level is not None:
            logger.setLevel(level)
        return logger

    logger.setLevel(level or logging.INFO)
    handler = logging.StreamHandler()
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


_log = get_logger(__name__)


def ensure_dir(path: Union[str, Path], exist_ok: bool = True) -> Path:
    """Ensure a directory exists and return a Path to it."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=exist_ok)
    return p


def read_json(path: Union[str, Path], *, default: Any = None) -> Any:
    """Read JSON from a file. Returns default on missing file (no exception)."""
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(obj: Any, path: Union[str, Path], *, indent: int = 2, ensure_dir_exists: bool = True) -> None:
    """Write object as JSON to path. Creates parent directories if necessary."""
    p = Path(path)
    if ensure_dir_exists:
        ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=indent, ensure_ascii=False)


def read_text(path: Union[str, Path], *, default: Optional[str] = None) -> Optional[str]:
    p = Path(path)
    if not p.exists():
        return default
    return p.read_text(encoding="utf-8")


def write_text(data: str, path: Union[str, Path], *, ensure_dir_exists: bool = True) -> None:
    p = Path(path)
    if ensure_dir_exists:
        ensure_dir(p.parent)
    p.write_text(data, encoding="utf-8")


def chunks(seq: Sequence[T], n: int) -> Iterator[List[T]]:
    """Yield successive n-sized chunks from seq (works on sequences)."""
    if n <= 0:
        raise ValueError("n must be > 0")
    for i in range(0, len(seq), n):
        yield list(seq[i : i + n])


def retry(
    retries: int = 3,
    delay: float = 0.5,
    exceptions: Union[Type[BaseException], tuple] = Exception,
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Simple retry decorator. Retries on listed exceptions with a delay."""
    logger = logger or _log

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> T:
            last_exc: Optional[BaseException] = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[arg-type]
                    last_exc = exc
                    if attempt >= retries:
                        logger.debug("Final attempt failed in %s.%s", func.__module__, func.__name__)
                        raise
                    logger.debug("Attempt %d/%d failed for %s: %s — retrying after %.2fs", attempt, retries, func.__name__, exc, delay)
                    time.sleep(delay)
            # type: ignore[unreachable]
            raise last_exc  # pragma: no cover

        return wrapped

    return decorator


def timestamp_iso(utc: bool = True) -> str:
    """Return an ISO formatted timestamp (optionally UTC)."""
    dt = datetime.utcnow() if utc else datetime.now()
    return dt.replace(microsecond=0).isoformat() + ("Z" if utc else "")


def safe_cast(value: Any, type_: Type[T], default: Optional[T] = None) -> Optional[T]:
    """Attempt to cast a value to type_, returning default on failure."""
    try:
        return type_(value)  # type: ignore[call-arg]
    except Exception:
        return default


def is_truthy(value: Any) -> bool:
    """Loose boolean evaluation for environment / config values."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    s = str(value).strip().lower()
    return s not in ("", "0", "false", "no", "none", "null", "off", "f")


# Minimal runtime sanity check
if __name__ == "__main__":
    _log.info("helper_scripts package v%s loaded", __version__)