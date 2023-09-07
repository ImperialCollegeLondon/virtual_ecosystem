"""The :mod:`~virtual_rainforest.models.animals.animal_model` module creates a
:class:`~virtual_rainforest.models.animals.animal_model.AnimalModel` class as a
child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.setup` and
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the
Virtual Rainforest model develops. The factory method
:func:`~virtual_rainforest.models.animals.animal_model.AnimalModel.from_config`
exists in a more complete state, and unpacks a small number of parameters
from our currently pretty minimal configuration dictionary. These parameters are
then used to generate a class instance. If errors crop up here when converting the
information from the config dictionary to the required types
(e.g. :class:`~numpy.timedelta64`) they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled
by downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205, D415


from __future__ import annotations

from math import sqrt
from typing import Any

from numpy import timedelta64
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_communities import AnimalCommunity
from virtual_rainforest.models.animals.functional_group import FunctionalGroup


class AnimalModel(BaseModel):
    """A class describing the animal model.

    Describes the specific functions and attributes that the animal module should
    possess.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        functional_groups: The list of animal functional groups present in the
            simulation
    """

    model_name = "animals"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that animal model can sensibly capture."""
    upper_bound_on_time_scale = "1 month"
    """Longest time scale that animal model can sensibly capture."""
    required_init_vars = ()
    """Required initialisation variables for the animal model."""
    vars_updated = (
        "decomposed_excrement",
        "decomposed_carcasses",
    )
    """Variables updated by the animal model.

    At the moment these are only inputs to the litter model.
    """

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        functional_groups: list[FunctionalGroup],
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        days_as_float = self.update_interval.to("days").magnitude
        self.update_interval_timedelta = timedelta64(int(days_as_float), "D")
        """Convert pint update_interval to timedelta64 once during initialization."""

        self._setup_grid_neighbors()
        """Determine grid square adjacency."""

        self.communities: dict[int, AnimalCommunity] = {}
        """Set empty dict for populating with communities."""
        self._initialize_communities(functional_groups)
        """Create the dictionary of animal communities and populate each community with
        animal cohorts."""

    def _setup_grid_neighbors(self) -> None:
        """Set up grid neighbors for the model.

        Currently, this is redundant with the set_neighbours method of grid.
        This will become a more complex animal specific implementation to manage
        functional group specific adjacency.

        """
        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))

    def get_community_by_key(self, key: int) -> AnimalCommunity:
        """Function to return the AnimalCommunity present in a given grid square.

        This function exists principally to provide a callable for AnimalCommunity.

        Args:
            key: The specific grid square integer key associated with the community.

        Returns:
            The AnimalCommunity object in that grid square.

        """
        return self.communities[key]

    def _initialize_communities(self, functional_groups: list[FunctionalGroup]) -> None:
        """Initialize the animal communities.

        Args:
            functional_groups: The list of functional groups that will populate the
            model.
        """

        # Generate a dictionary of AnimalCommunity objects, one per grid cell.
        self.communities = {
            k: AnimalCommunity(
                functional_groups,
                k,
                list(self.data.grid.neighbours[k]),
                self.get_community_by_key,
            )
            for k in self.data.grid.cell_id
        }

        # Create animal cohorts in each grid square's animal community according to the
        # populate_community method.
        for community in self.communities.values():
            community.populate_community()

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> AnimalModel:
        """Factory function to initialise the animal model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) virtual rainforest configuration.
            update_interval: Frequency with which all models are updated
        """

        # Find timing details

        functional_groups_raw = config["animals"]["functional_groups"]

        animal_functional_groups = []
        for k in functional_groups_raw:
            animal_functional_groups.append(FunctionalGroup(*k))
        """create list of functional group objects to initialize  communities with."""

        LOGGER.info(
            "Information required to initialise the animal model successfully "
            "extracted."
        )
        return cls(data, update_interval, animal_functional_groups)

    def setup(self) -> None:
        """Function to set up the animal model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the animal model."""

    def update(self, time_index: int) -> None:
        """Function to step the animal model through time.

        Currently this is a toy implementation.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        for community in self.communities.values():
            community.forage_community()
            community.migrate_community()
            community.birth_community()
            community.metabolize_community(self.update_interval_timedelta)
            community.inflict_natural_mortality_community(
                self.update_interval_timedelta
            )
            community.increase_age_community(self.update_interval_timedelta)

        # Now that communities have been updated information required to update the
        # litter model can be extracted
        additions_to_litter = self.calculate_litter_additions()

        # Update the litter pools
        self.data.add_from_dict(additions_to_litter)

    def cleanup(self) -> None:
        """Placeholder function for animal model cleanup."""

    def calculate_litter_additions(self) -> dict[str, DataArray]:
        """Calculate the how much animal matter should be transferred to the litter."""

        # Find the size of all decomposed excrement and carcass pools
        decomposed_excrement = [
            community.excrement_pool.decomposed_carbon(self.data.grid.cell_area)
            for community in self.communities.values()
        ]
        decomposed_carcasses = [
            community.carcass_pool.decomposed_carbon(self.data.grid.cell_area)
            for community in self.communities.values()
        ]

        # All excrement and carcasses in their respective decomposed subpools are moved
        # to the litter model, so stored energy of each subpool is reset to zero
        for community in self.communities.values():
            community.excrement_pool.decomposed_energy = 0.0
            community.carcass_pool.decomposed_energy = 0.0

        return {
            "decomposed_excrement": DataArray(
                decomposed_excrement / self.update_interval.to("days"), dims="cell_id"
            ),
            "decomposed_carcasses": DataArray(
                decomposed_carcasses / self.update_interval.to("days"), dims="cell_id"
            ),
        }
