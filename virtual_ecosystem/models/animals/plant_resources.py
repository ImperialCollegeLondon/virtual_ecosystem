"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: #D205, D415

from __future__ import annotations

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animals.constants import AnimalConsts
from virtual_ecosystem.models.animals.protocols import Consumer, DecayPool


class PlantResources:
    """A class implementing the Resource protocol for plant data.

    This class acts as the interface between plant model data stored in the core data
    object using the :class:`~virtual_ecosystem.models.animals.protocols.Resource`
    protocol.

    At present, it only exposes a single resource - the total leaf mass of the entire
    plant community in a cell - but this is likely to expand to allow vertical structure
    of plant resources, diversification to fruit and other resources and probably plant
    cohort specific herbivory.

    Args:
        data: A Data object containing information from the plants model.
        cell_id: The cell id for the plant community to expose.
    """

    def __init__(self, data: Data, cell_id: int, constants: AnimalConsts) -> None:
        # Store the data and extract the appropriate plant data
        self.data = data
        """A reference to the core data object."""
        self.mass_current: float = (
            data["layer_leaf_mass"].sel(cell_id=cell_id).sum(dim="layers").item()
        )
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

    def get_eaten(self, herbivore: Consumer, excrement_pool: DecayPool) -> float:
        """This function removes energy from a PlantResources and through herbivory.

        Args:
            herbivore: The AnimalCohort preying on the PlantResources
            excrement_pool: The resident pool of detritus to which the remains of excess
                plant material is lost.

        Returns:
            A float of the energy value of the consumed plants after mechanical and
            digestive efficiencies are accounted for.

        """

        # Minimum of the energy available and amount that can be consumed in an 8 hour
        # foraging window .
        mass_consumed = min(
            self.mass_current,
            herbivore.intake_rate * herbivore.individuals,
        )

        # TODO - this needs to feedback herbivory to into the data object and hence back
        # into the plant model, but for now, the energy is consumed and not lost from
        # plants.
        self.mass_current -= mass_consumed

        # TODO - All plant matter that animals fail to eat currently goes into the
        # excrement pool. This isn't ideal, but will do for now. This herbivore
        # contribution to litter fall should be handled by the plant model in future.
        excrement_pool.decomposed_energy += mass_consumed * (
            1 - herbivore.functional_group.mechanical_efficiency
        )

        # Return the net mass gain of herbivory
        return (
            mass_consumed
            * herbivore.functional_group.conversion_efficiency
            * herbivore.functional_group.mechanical_efficiency
        )
