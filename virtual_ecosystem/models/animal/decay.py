"""The :mod:`~virtual_ecosystem.models.animal.decay` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. This includes excrement and carcasses that are tracked solely
in the animal module. This also includes plant litter which is mainly tracked in the
`litter` module, but is made available for animal consumption.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.protocols import Consumer


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


class LitterPool:
    """A class that makes litter available for animal consumption.

    This class acts as the interface between litter model data stored in the core data
    object and the animal model.

    This class is designed to be reused for all five of the litter pools used in the
    litter model, as all of these pools are consumable by animals.

    Args:
        pool_name: The name of the litter pool being accessed.
        data: A Data object containing information from the litter model.
        cell_area: The size of the cell, used to convert from density to mass units
            [m^2]
    """

    def __init__(self, pool_name: str, data: Data, cell_area: float) -> None:
        self.mass_current = (data[f"litter_pool_{pool_name}"].to_numpy()) * cell_area
        """Mass of the litter pool in carbon terms [kg C]."""

        self.c_n_ratio = data[f"c_n_ratio_{pool_name}"].to_numpy()
        """Carbon nitrogen ratio of the litter pool [unitless]."""

        self.c_p_ratio = data[f"c_p_ratio_{pool_name}"].to_numpy()
        """Carbon phosphorus ratio of the litter pool [unitless]."""

    def get_eaten(
        self, consumed_mass: float, detritivore: Consumer, grid_cell_id: int
    ) -> float:
        """This function handles litter detritivory.

        Args:
            consumed_mass: The mass intended to be consumed by the herbivore [kg].
            detritivore: The Consumer (AnimalCohort) consuming the Litter.
            grid_cell_id: The cell id of the cell the animal cohort is in.

        Returns:
            The actual mass consumed by the detritivore, adjusted for efficiencies [kg].
        """

        # Check if the requested consumed mass is more than the available mass
        actually_available_mass = min(self.mass_current[grid_cell_id], consumed_mass)

        # Calculate the mass of the consumed litter after mechanical efficiency
        actual_consumed_mass = (
            actually_available_mass * detritivore.functional_group.mechanical_efficiency
        )

        # Update the litter pool mass to reflect the mass consumed
        self.mass_current[grid_cell_id] -= actual_consumed_mass

        # Return the net mass gain of detritivory, after considering
        # digestive efficiencies
        net_mass_gain = (
            actual_consumed_mass * detritivore.functional_group.conversion_efficiency
        )

        return net_mass_gain
