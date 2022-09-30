"""The `core.logging` module.

The `core.logging` module is used to setup the extend the standard logging setup to
provide additional functionality relevant to the virtual rainforest model.

At the moment the module simply sets up the logger so that other modules can access it.
It is very likely to be further extended in future.
"""

import logging
from typing import Type

LOGGER = logging.getLogger("virtual_rainforest")


def log_and_raise(msg: str, exception: Type[Exception], extra: dict = None) -> None:
    """Emit a critical error message and raise an Exception.

    This convenience function adds a critical level message to the logger and
    then raises an exception with the same message. This is intended only for
    use in loading resources: the package cannot run properly with misconfigured
    resources but errors with the data checking should log and carry on.

    Args:
        msg: A message to add to the log
        exception: An exception type to be raised
        extra: A dictionary of extra information to be passed to the logger
    """

    LOGGER.critical(msg, extra=extra)
    raise exception(msg)
