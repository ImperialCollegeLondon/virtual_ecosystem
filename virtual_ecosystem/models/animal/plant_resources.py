"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from __future__ import annotations

from virtual_ecosystem.core.data import Data
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
        self.is_alive = True
        """Indicating whether the plant cohort is alive [True] or dead [False]."""

    def get_eaten(
        self, consumed_mass: float, herbivore: Consumer
    ) -> tuple[float, float]:
        """This function handles herbivory on PlantResources.

        TODO: the plant waste here is specifically leaf litter, alternative functions
        (or classes) will need to be written for consumption of roots and reproductive
        tissues (fruits and flowers).

        Args:
            consumed_mass: The mass intended to be consumed by the herbivore.
            herbivore: The Consumer (AnimalCohort) consuming the PlantResources.

        Returns:
            A tuple consisting of the actual mass consumed by the herbivore (adjusted
            for efficiencies), and the mass removed from the plants by herbivory that
            isn't consumed and instead becomes litter.
        """
        # Check if the requested consumed mass is more than the available mass
        actual_consumed_mass = min(self.mass_current, consumed_mass)

        # Update the plant mass to reflect the mass consumed
        self.mass_current -= actual_consumed_mass

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

        return net_mass_gain, excess_mass
