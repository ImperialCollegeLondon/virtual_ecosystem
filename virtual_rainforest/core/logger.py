"""The `core.logging` module.

The `core.logging` module is used to setup the extend the standard logging setup to
provide additional functionality relevant to the virtual rainforest model.

At the moment the module simply sets up the logger so that other modules can access it.
It is very likely to be further extended in future.
"""

import logging

LOGGER = logging.getLogger("virtual_rainforest")
