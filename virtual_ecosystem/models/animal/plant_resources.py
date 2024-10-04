"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from __future__ import annotations

from collections.abc import Sequence

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.decay import ExcrementPool
from virtual_ecosystem.models.animal.protocols import Consumer


class PlantResources:
    """A class implementing the Resource protocol for plant data.

    This class acts as the interface between plant model data stored in the core data
    object using the :class:`~virtual_ecosystem.models.animal.protocols.Resource`
    protocol.

    At present, it only exposes a single resource - the total leaf mass of the entire
    plant community in a cell - but this is likely to expand to allow vertical structure
    of plant resources, diversification to fruit and other resources and probably plant
    cohort specific herbivory.

    TODO: fix mass_current after resolving example data questions

    Args:
        data: A Data object containing information from the plants model.
        cell_id: The cell id for the plant community to expose.
    """

    def __init__(self, data: Data, cell_id: int, constants: AnimalConsts) -> None:
        # Store the data and extract the appropriate plant data
        self.data = data
        """A reference to the core data object."""
        self.cell_id = cell_id
        """The community cell containing the plant resources."""
        # self.mass_current: float = (
        #    data["layer_leaf_mass"].sel(cell_id=cell_id).sum(dim="layers").item()
        # )
        self.mass_current = 100000.0
        """The mass of the plant leaf mass [kg]."""
        self.constants = constants
        """The animals constants."""
        # Calculate energy availability
        # TODO - this needs to be handed back to the plants model, which will define PFT
        #        specific conversions to different resources.
        self.energy_density: float = self.constants.energy_density["plant"]
        """The energy (J) in a kg of plant [currently set to toy value of Alfalfa]."""
        self.energy_max: float = self.mass_current * self.energy_density
        """The maximum amount of energy that the cohort can have [J] [Alfalfa]."""
        self.stored_energy = self.energy_max
        """The amount of energy in the plant cohort [J] [toy]."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""

    def get_eaten(
        self,
        consumed_mass: float,
        herbivore: Consumer,
        excrement_pools: Sequence[ExcrementPool],
    ) -> float:
        """This function handles herbivory on PlantResources."""

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

        # Calculate the energy to be added to each excrement pool
        excreta_energy_per_pool = (
            excess_mass * self.constants.energy_density["plant"]
        ) / len(excrement_pools)

        # Distribute the excreta energy across the excrement pools
        for excrement_pool in excrement_pools:
            excrement_pool.decomposed_carbon += excreta_energy_per_pool

        # Return the net mass gain of herbivory, considering both mechanical and
        # digestive efficiencies
        net_mass_gain = (
            effective_mass_for_herbivore
            * herbivore.functional_group.conversion_efficiency
        )

        return net_mass_gain
