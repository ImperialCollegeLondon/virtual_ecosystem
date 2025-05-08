"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from __future__ import annotations

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.constants import AnimalConsts

# from virtual_ecosystem.models.animal.decay import ExcrementPool
from virtual_ecosystem.models.animal.protocols import Consumer


class PlantResources:
    """A class implementing the Resource protocol for plant data.

    This class acts as the interface between plant model data stored in the core data
    object using the :class:`~virtual_ecosystem.models.animal.protocols.Resource`
    protocol.

    At present, it only exposes a single resource - the total leaf mass of the entire
    plant community in a cell - but this is likely to expand to allow vertical structure
    of plant resources, diversification to fruit and other resources and probably plant
    cohort-specific herbivory.

    Args:
        data: A Data object containing information from the plants model.
        cell_id: The cell id for the plant community to expose.
        constants: Animal-related constants, including plant energy density.
    """

    def __init__(self, data: Data, cell_id: int, constants: AnimalConsts) -> None:
        # Store the data and extract the appropriate plant data
        self.data = data
        """A reference to the core data object."""
        self.cell_id = cell_id
        """The community cell containing the plant resources."""
        self.mass_current: float = 10000.0
        """The mass of the plant leaf mass [kg]."""
        self.constants = constants
        """The animal constants, including energy density."""
        self.vertical_occupancy: VerticalOccupancy = (
            VerticalOccupancy.GROUND | VerticalOccupancy.CANOPY
        )
        """The vertical position of the plant resource pool."""
        self.is_alive = True
        """Indicating whether the plant cohort is alive [True] or dead [False]."""
        self.cnp_proportions: dict[str, float] = {
            "carbon": 0.7,
            "nitrogen": 0.2,
            "phosphorus": 0.1,
        }
        """Toy stoichiometric proportions of plants."""
        self.mass_stoich: dict[str, float] = {}
        """The mass of each stoichiometric element found in the plant resources,
        {"carbon": value, "nitrogen": value, "phosphorus": value}."""

        # Initialize stoichiometric masses
        self.update_stoichiometric_mass()

    def update_stoichiometric_mass(self) -> None:
        """Updates the stoichiometric mass based on the current mass and proportions."""
        self.mass_stoich = {
            element: self.mass_current * proportion
            for element, proportion in self.cnp_proportions.items()
        }

    def set_mass_current(self, new_mass: float) -> None:
        """Sets a new mass for the resource and updates stoichiometric mass."""
        if new_mass < 0:
            raise ValueError("Mass cannot be negative.")
        self.mass_current = new_mass
        self.update_stoichiometric_mass()

    def get_eaten(
        self, consumed_mass: float, herbivore: Consumer
    ) -> tuple[dict[str, float], dict[str, float]]:
        """This function handles herbivory on PlantResources.

        TODO: the plant waste here is specifically leaf litter, alternative functions
        (or classes) will need to be written for consumption of roots and reproductive
        tissues (fruits and flowers).

        Args:
            consumed_mass: The total mass intended to be consumed by the herbivore.
            herbivore: The Consumer (AnimalCohort) consuming the PlantResources.

        Returns:
            A tuple consisting of the stoich mass consumed by the herbivore (adjusted
            for efficiencies), and the mass removed from the plants by herbivory that
            isn't consumed and instead becomes litter.
        """

        # Handle zero or invalid consumption
        if consumed_mass <= 0:
            return (
                {element: 0.0 for element in self.cnp_proportions},
                {element: 0.0 for element in self.cnp_proportions},
            )

        # Check if the requested consumed mass is more than the available mass
        actual_consumed_mass = min(self.mass_current, consumed_mass)

        # Update the plant mass to reflect the mass consumed
        # stoichio mass auto-updates through this call
        self.set_mass_current(self.mass_current - actual_consumed_mass)

        # Calculate the energy value of the consumed plants after mechanical efficiency
        effective_mass_for_herbivore = (
            actual_consumed_mass * herbivore.functional_group.mechanical_efficiency
        )

        # Excess mass goes to the excrement pool, considering only the part not
        # converted by mechanical efficiency
        excess_mass = actual_consumed_mass * (
            1 - herbivore.functional_group.mechanical_efficiency
        )

        # Return the net mass gain of herbivory, considering both mechanical and
        # digestive efficiencies
        net_mass_gain = (
            effective_mass_for_herbivore
            * herbivore.functional_group.conversion_efficiency
        )

        # Transform the net_mass_gain into stoichiometric mass
        herbivore_gain_cnp = {
            element: net_mass_gain * proportion
            for element, proportion in self.cnp_proportions.items()
        }

        # Transform the excess mass into stoichiometric mass
        plant_litter_cnp = {
            element: excess_mass * proportion
            for element, proportion in self.cnp_proportions.items()
        }

        return herbivore_gain_cnp, plant_litter_cnp
