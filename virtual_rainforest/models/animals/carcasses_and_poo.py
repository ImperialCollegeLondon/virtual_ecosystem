"""The :mod:`~virtual_rainforest.models.animals.carcasses_and_poo` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. And the moment this consists of animal carcasses and excrement.
"""  # noqa: #D205, D415


from dataclasses import dataclass


@dataclass
class CarcassPool:
    """This is a class of carcass pools."""

    stored_energy: float
    """The amount of energy in the carcass pool [J]."""
    position: int
    """The grid position of the carcass pool."""


@dataclass
class ExcrementPool:
    """This class store information about the amount of excrement in each grid cell."""

    scavengeable_energy: float
    """The amount of animal accessible energy in the excrement pool [J]."""

    decomposed_energy: float
    """The amount of decomposed energy in the excrement pool [J]."""

    def decomposed_carbon(self, grid_cell_area: float) -> float:
        """Calculate carbon stored in full decomposed excrement based on the energy.

        TODO - At the moment this literally just assumes that a kilogram of carbon
        contains 10^6 J, in future this needs to be properly parametrised.

        Args:
            grid_cell_area: The size of the grid cell [m^2]

        Returns:
            The amount of decomposed excrement in carbon terms [kg C m^-2]
        """

        joules_per_kilo_carbon = 1e6

        return self.decomposed_energy / (joules_per_kilo_carbon * grid_cell_area)
