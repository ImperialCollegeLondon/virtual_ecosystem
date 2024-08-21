"""The :mod:`~virtual_ecosystem.core.logger` module is used to setup the extend the
standard logging setup to provide additional functionality relevant to the Virtual
Ecosystem model.

At the moment the module simply sets up the logger so that other modules can access it.
It is very likely to be further extended in future.

All logging messages are emitted with a specified logging level, which essentially
indicates the importance of the logging message. At the moment we use the 5 standard
logging levels, though we might extend this by using custom logging levels at some
point. The five logging levels we use are as follows:

=============  =========================================================================
Logging level  Use case
=============  =========================================================================
``CRITICAL``   Something has gone so wrong that the model run has to stop immediately.
``ERROR``      | Something has definitely gone wrong, but there is still a value in
                 continuing the execution
               | of the model. This is mainly to check if other errors crop
                 up, so that all relevant errors
               | can be reported at once.
``WARNING``    | Something seems a bit off, so the user should be warned, but the model
                 might actually be
               | fine.
``INFO``       | Something expected has happened, and it's useful to give the user
                 information about it,
               | e.g. configuration has been validated, or an output
                 file is being saved to a specific
               | location.
``DEBUG``      | Something has happened that is generally of minimal interest, but might
                 be relevant when
               | attempting to debug issues.
=============  =========================================================================

These logging levels can then be used to filter the messages the user receives, by
setting the logging level such that only messages above a certain level (of importance)
are displayed. In practice, we are likely to generally set the logging level to ``INFO``
so that ``DEBUG`` messages are suppressed, except when we are actively trying to debug
the model.

Logging and exceptions
----------------------

When an exception is allowed to halt the code, it is important for the reason to be
written to the log, as well as producing any traceback to the console. So, exception
handling should always include a LOGGER call, using one of the following patterns.

#. A test in the code indicates that we should raise an exception:

  .. code-block:: python

    if thing_has_gone_wrong:
        to_raise = ValueError("It went wrong!")
        LOGGER.critical(to_raise)
        raise to_raise

#. A ``try`` block results in an exception:

  .. code-block:: python

    try:
        doing_something_that_raises()
    except ValueError as excep:
        LOGGER.critical(excep)
        raise

#. A ``try`` block results in an exception and we want to change the exception type:

  .. code-block:: python

    try:
        doing_something_that_raises()
    except ValueError as excep:
        LOGGER.critical(excep)
        raise ValueError("Bad input") from excep
"""  # noqa: D205

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(module)s - %(funcName)s(%(lineno)d) - %(message)s",
)

LOGGER = logging.getLogger("virtual_ecosystem")
""":class:`logging.Logger`: The core logger instance used in the Virtual Ecosystem."""


def add_file_logger(logfile: Path) -> None:
    """Redirect logging to a provided file path.

    This function adds a FileHandler with the name ``vr_logfile`` to
    :data:`~virtual_ecosystem.core.logger.LOGGER` using the provided ``logfile`` path.
    It also turns off record propagation so that logging messages are only sent to that
    file and not to the parent StreamHandler.

    Args:
        logfile: The path to a file to use for logging.

    Raises:
        RuntimeError: If the file handler already exists. If the logging is to move to a
            new file, the existing handler needs to be explicitly removed first.
    """

    for handler in LOGGER.handlers:
        if isinstance(handler, logging.FileHandler) and handler.name == "vr_logfile":
            raise RuntimeError(f"Already logging to file: {handler.baseFilename}")

    # Do not propogate errors up to parent handler - this avoids mirroring the log
    # output through the StreamHandler associated with the root logger
    LOGGER.propagate = False

    # Add a specific file handler for this log.
    format = "[%(levelname)s] - %(module)s - %(funcName)s(%(lineno)d) - %(message)s"
    formatter = logging.Formatter(fmt=format)
    handler = logging.FileHandler(logfile)
    handler.setFormatter(formatter)
    handler.name = "vr_logfile"
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.DEBUG)


def remove_file_logger() -> None:
    """Remove the file logger and return to stream logging.

    This function attempts to remove the ``vr_logfile`` FileHandler that is added by
    :func:`~virtual_ecosystem.core.logger.add_file_logger`. If that file handler is
    not found it simple exits, otherwise it removes the file handler and restores
    message propagation.
    """

    try:
        # Find the file logger by name and remove it
        vr_logfile = next(
            handler for handler in LOGGER.handlers if handler.name == "vr_logfile"
        )
    except StopIteration:
        return

    vr_logfile.close()
    LOGGER.removeHandler(vr_logfile)

    # Allow logger messages to propogate back down to the root StreamHandler
    LOGGER.propagate = True
