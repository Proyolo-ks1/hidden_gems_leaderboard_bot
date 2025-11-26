from __future__ import annotations
import importlib
import inspect
import logging
import pkgutil
from types import ModuleType
from typing import Iterable, List

"""
commands package initializer.

Provides utilities to auto-discover and register command modules.

Expected module API (preferred):
- setup(bot) -> None | coroutine

If a module exposes a setup function it will be called with the bot
instance so modules can register their commands/cogs.
"""



logger = logging.getLogger(__name__)


def iter_command_modules() -> Iterable[ModuleType]:
    """
    Yield imported modules that live inside this package.
    Modules are lazily imported; modules that raise during import will be logged and skipped.
    """
    for finder, name, ispkg in pkgutil.iter_modules(path=__path__, prefix=__name__ + "."):
        # skip packages and this package itself if encountered
        if ispkg:
            continue
        try:
            module = importlib.import_module(name)
            yield module
        except Exception:
            logger.exception("Failed to import command module %r, skipping", name)


async def register_all(bot) -> List[str]:
    """
    Call `setup(bot)` (or await it) for each discovered command module that provides it.
    Returns a list of module names successfully registered.
    """
    registered = []
    for module in iter_command_modules():
        setup_fn = getattr(module, "setup", None)
        if setup_fn is None:
            logger.debug("module %s has no setup(), skipping", module.__name__)
            continue

        try:
            if inspect.iscoroutinefunction(setup_fn):
                await setup_fn(bot)
            else:
                setup_fn(bot)
            registered.append(module.__name__)
            logger.info("registered commands from %s", module.__name__)
        except Exception:
            logger.exception("Error while registering commands from %s", module.__name__)
    return registered


__all__ = ["iter_command_modules", "register_all"]