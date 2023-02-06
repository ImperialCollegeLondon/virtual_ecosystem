"""The 'carcass_module.

This file provides toy carcass module functionality for developing the animal and soil
modules.
"""

from dataclasses import dataclass


@dataclass
class CarcassPool:
    """This is a class of carcass pools."""

    energy: float
    """The amount of energy in the carcass pool [J]."""
    position: int
    """The grid position of the carcass pool."""
