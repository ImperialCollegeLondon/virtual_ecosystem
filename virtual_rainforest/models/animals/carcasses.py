"""The ''carcasses'' module provides toy carcass module functionality for developing
the animal and soil modules.
"""  # noqa: #D205, D415


from dataclasses import dataclass


@dataclass
class CarcassPool:
    """This is a class of carcass pools."""

    stored_energy: float
    """The amount of energy in the carcass pool [J]."""
