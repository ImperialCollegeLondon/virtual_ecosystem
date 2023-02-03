"""The :mod:`~virtual_rainforest.core.logging` module is used to setup the extend the
standard logging setup to provide additional functionality relevant to the virtual
rainforest model.

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

The logging module also defines a function that we should generally make use of to kill
the simulation when something goes wrong. This function
:func:`~virtual_rainforest.core.logger.log_and_raise` raises an exception (of the
developers choice) and adds a developer specified ``CRITICAL`` message to the log. This
function is useful as it ensures that ``CRITICAL`` logging events are accompanied by a
simulation ending exception. As such, this is probably the only means by which you
should log a ``CRITICAL`` message.
"""  # noqa: D205, D415

import logging
from typing import Optional, Type

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(module)s - %(funcName)s(%(lineno)d) - %(message)s",
)

LOGGER = logging.getLogger("virtual_rainforest")


def log_and_raise(
    msg: str, exception: Type[BaseException], extra: Optional[dict] = None
) -> None:
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
