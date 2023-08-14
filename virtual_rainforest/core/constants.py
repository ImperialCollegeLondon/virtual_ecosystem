"""The :mod:`~virtual_rainforest.core.constants` module is used to store constants that
are used across the Virtual Rainforest. This includes universal constants, such as the
strength of gravity, but also constants that are shared between multiple models, such as
the depth of the biogeochemically active soil layer.

At the moment, no constants are actually stored in this module. It currently only
contains the :attr:`CONSTANTS_REGISTRY`, which all constants classes should be
registered in across models. This allows for all constants to be documented neatly.
"""  # noqa: D205, D415

from typing import Any

CONSTANTS_REGISTRY: dict[str, Any] = {}
"""A registry for all the constants data classes.

:meta hide-value:
"""
