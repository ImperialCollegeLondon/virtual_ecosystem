"""The :mod:`~virtual_ecosystem.models.animal.decay` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. And the moment this consists of animal carcasses and excrement.
"""  # noqa: D205

from dataclasses import dataclass


@dataclass
class CarcassPool:
    """This class store information about the carcass biomass in each grid cell."""

    scavengeable_carbon: float
    """The amount of animal accessible carbon in the carcass pool [kg C]."""

    decomposed_carbon: float
    """The amount of decomposed carbon in the carcass pool [kg C]."""

    scavengeable_nitrogen: float
    """The amount of animal accessible nitrogen in the carcass pool [kg N]."""

    decomposed_nitrogen: float
    """The amount of decomposed nitrogen in the carcass pool [kg N]."""

    scavengeable_phosphorus: float
    """The amount of animal accessible phosphorus in the carcass pool [kg P]."""

    decomposed_phosphorus: float
    """The amount of decomposed phosphorus in the carcass pool [kg P]."""

    def decomposed_nutrient_per_area(
        self, nutrient: str, grid_cell_area: float
    ) -> float:
        """Convert decomposed carcass nutrient content to mass per area units.

        Args:
            nutrient: The name of the nutrient to calculate for
            grid_cell_area: The size of the grid cell [m^2]

        Raises:
            AttributeError: If a nutrient other than carbon, nitrogen, or phosphorus is
                chosen

        Returns:
            The nutrient content of the decomposed carcasses on a per area basis [kg
            m^-2]
        """

        decomposed_nutrient = getattr(self, f"decomposed_{nutrient}")

        return decomposed_nutrient / grid_cell_area


@dataclass
class ExcrementPool:
    """This class store information about the amount of excrement in each grid cell."""

    scavengeable_carbon: float
    """The amount of animal accessible carbon in the excrement pool [kg C]."""

    decomposed_carbon: float
    """The amount of decomposed carbon in the excrement pool [kg C]."""

    scavengeable_nitrogen: float
    """The amount of animal accessible nitrogen in the excrement pool [kg N]."""

    decomposed_nitrogen: float
    """The amount of decomposed nitrogen in the excrement pool [kg N]."""

    scavengeable_phosphorus: float
    """The amount of animal accessible phosphorus in the excrement pool [kg P]."""

    decomposed_phosphorus: float
    """The amount of decomposed phosphorus in the excrement pool [kg P]."""

    def decomposed_nutrient_per_area(
        self, nutrient: str, grid_cell_area: float
    ) -> float:
        """Convert decomposed excrement nutrient content to mass per area units.

        Args:
            nutrient: The name of the nutrient to calculate for
            grid_cell_area: The size of the grid cell [m^2]

        Raises:
            AttributeError: If a nutrient other than carbon, nitrogen, or phosphorus is
                chosen

        Returns:
            The nutrient content of the decomposed excrement on a per area basis [kg
            m^-2]
        """

        decomposed_nutrient = getattr(self, f"decomposed_{nutrient}")

        return decomposed_nutrient / grid_cell_area


def find_decay_consumed_split(
    microbial_decay_rate: float, animal_scavenging_rate: float
):
    """Find fraction of biomass that is assumed to decay rather than being scavenged.

    This should be calculated separately for each relevant biomass type (excrement and
    carcasses). This function should could be replaced in future by something that
    incorporates more of the factors determining this split (e.g. temperature).

    Args:
        microbial_decay_rate: Rate at which biomass type decays due to microbes [day^-1]
        animal_scavenging_rate: Rate at which biomass type is scavenged due to animals
            [day^-1]
    """

    return microbial_decay_rate / (animal_scavenging_rate + microbial_decay_rate)
