"""The ''carcass'' module provides toy carcass module functionality for developing
the animal and soil modules.
"""  # noqa: #D205, D415


from dataclasses import dataclass


@dataclass
class CarcassPool:
    """This is a class of carcass pools."""

    energy: float
    """The amount of energy in the carcass pool [J]."""
    position: int
    """The grid position of the carcass pool."""
