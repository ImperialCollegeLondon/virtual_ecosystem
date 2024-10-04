"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from __future__ import annotations

from collections.abc import Sequence

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.constants import AnimalConsts

# from virtual_ecosystem.models.animal.decay import ExcrementPool
from virtual_ecosystem.models.animal.protocols import Consumer, DecayPool


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
        self.mass_current = 100000.0
        """The mass of the plant leaf mass [kg]."""
        self.constants = constants
        """The animal constants, including energy density."""
        self.is_alive = True
        """Indicating whether the plant cohort is alive [True] or dead [False]."""

    def get_eaten(
        self,
        consumed_mass: float,
        herbivore: Consumer,
        excrement_pools: Sequence[DecayPool],
    ) -> float:
        """Handles herbivory on PlantResources, transfers excess to excrement pools.

        Args:
            consumed_mass: The amount of mass consumed by the herbivore [kg].
            herbivore: The herbivore consuming the plant resource, used to access its
                functional group properties such as mechanical efficiency and
                conversion efficiency.
            excrement_pools: A sequence of excrement pools to which excess mass (carbon)
            will be added.

        Returns:
            The net mass gain of the herbivore after considering mechanical and
            digestive efficiencies [kg].
        """
        # Check if the requested consumed mass is more than the available mass
        actual_consumed_mass = min(self.mass_current, consumed_mass)

        # Update the plant mass to reflect the mass consumed
        self.mass_current -= actual_consumed_mass

        # Calculate the mass value of the consumed plants after mechanical efficiency
        effective_mass_for_herbivore = (
            actual_consumed_mass * herbivore.functional_group.mechanical_efficiency
        )

        # Excess mass goes to the excrement pool
        excess_mass = actual_consumed_mass * (
            1 - herbivore.functional_group.mechanical_efficiency
        )

        # Distribute the excess mass as carbon across the excrement pools
        excreta_mass_per_pool = excess_mass / len(excrement_pools)
        for excrement_pool in excrement_pools:
            excrement_pool.decomposed_carbon += excreta_mass_per_pool

        # Return the net mass gain of herbivory, considering both mechanical and
        #  digestive efficiencies
        net_mass_gain = (
            effective_mass_for_herbivore
            * herbivore.functional_group.conversion_efficiency
        )

        return net_mass_gain
