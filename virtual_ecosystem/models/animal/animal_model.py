"""The :mod:`~virtual_ecosystem.models.animal.animal_model` module creates a
:class:`~virtual_ecosystem.models.animal.animal_model.AnimalModel` class as a
child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_ecosystem.core.base_model.BaseModel.setup` and
:func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the
Virtual Ecosystem model develops. The factory method
:func:`~virtual_ecosystem.models.animal.animal_model.AnimalModel.from_config`
exists in a more complete state, and unpacks a small number of parameters
from our currently pretty minimal configuration dictionary. These parameters are
then used to generate a class instance. If errors crop up here when converting the
information from the config dictionary to the required types
(e.g. :class:`~numpy.timedelta64`) they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled
by downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205

from __future__ import annotations

from math import sqrt
from typing import Any

from numpy import array, timedelta64, zeros
from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
from virtual_ecosystem.models.animal.animal_communities import AnimalCommunity
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup


class AnimalModel(
    BaseModel,
    model_name="animal",
    model_update_bounds=("1 day", "1 month"),
    required_init_vars=(),
    vars_updated=(
        "decomposed_excrement",
        "decomposed_carcasses",
        "total_animal_respiration",
    ),
):
    """A class describing the animal model.

    Describes the specific functions and attributes that the animal module should
    possess.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        functional_groups: The list of animal functional groups present in the
            simulation.
        model_constants: Set of constants for the animal model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        functional_groups: list[FunctionalGroup],
        model_constants: AnimalConsts = AnimalConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        days_as_float = self.model_timing.update_interval_quantity.to("days").magnitude
        self.update_interval_timedelta = timedelta64(int(days_as_float), "D")
        """Convert pint update_interval to timedelta64 once during initialization."""

        self._setup_grid_neighbors()
        """Determine grid square adjacency."""

        self.functional_groups = functional_groups
        """List of functional groups in the model."""
        self.communities: dict[int, AnimalCommunity] = {}
        """Set empty dict for populating with communities."""
        self.model_constants = model_constants
        """Animal constants."""
        self._initialize_communities(functional_groups)
        """Create the dictionary of animal communities and populate each community with
        animal cohorts."""
        self.setup()
        """Initialize the data variables used by the animal model."""

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
                functional_groups=functional_groups,
                data=self.data,
                community_key=k,
                neighbouring_keys=list(self.data.grid.neighbours[k]),
                get_destination=self.get_community_by_key,
                constants=self.model_constants,
            )
            for k in self.data.grid.cell_id
        }

        # Create animal cohorts in each grid square's animal community according to the
        # populate_community method.
        for community in self.communities.values():
            community.populate_community()

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> AnimalModel:
        """Factory function to initialise the animal model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(config, "animal", "AnimalConsts")

        # Load functional groups
        functional_groups = [
            FunctionalGroup(**k, constants=model_constants)
            for k in config["animal"]["functional_groups"]
        ]

        LOGGER.info(
            "Information required to initialise the animal model successfully "
            "extracted."
        )

        return cls(
            data=data,
            core_components=core_components,
            functional_groups=functional_groups,
            model_constants=model_constants,
        )

    def setup(self) -> None:
        """Method to setup the animal model specific data variables.

        TODO: rename this as something else because you've used it crazy

        """

        # animal respiration data variable
        # the array should have one value for each animal community
        n_communities = len(self.data.grid.cell_id)

        # Initialize total_animal_respiration as a DataArray with a single dimension:
        # cell_id
        total_animal_respiration = DataArray(
            zeros(
                n_communities
            ),  # Filled with zeros to start with no carbon production.
            dims=["cell_id"],
            coords={"cell_id": self.data.grid.cell_id},
            name="total_animal_respiration",
        )

        # Add total_animal_respiration to the Data object.
        self.data["total_animal_respiration"] = total_animal_respiration

        # Population density data variable
        functional_group_names = [fg.name for fg in self.functional_groups]

        # Assuming self.communities is a dict with community_id as keys
        community_ids = list(self.communities.keys())

        # Create a multi-dimensional array for population densities
        population_densities = DataArray(
            zeros((len(community_ids), len(functional_group_names)), dtype=float),
            dims=["community_id", "functional_group_id"],
            coords={
                "community_id": community_ids,
                "functional_group_id": functional_group_names,
            },
            name="population_densities",
        )

        # Add to Data object
        self.data["population_densities"] = population_densities

        # initialize values
        self.update_population_densities()

        # Debugging output
        # print("Data variables after setup:", list(self.data.data.data_vars))

    def spinup(self) -> None:
        """Placeholder function to spin up the animal model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to step the animal model through time.

        Temporary solution.

        This method sets the order of operations for the animal module. In nature, these
        events would be simultaneous. The ordering within the method is less a question
        of the science and more a question of computational logic and stability.



        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        for community in self.communities.values():
            community.forage_community()
            community.migrate_community()
            community.birth_community()
            community.metamorphose_community()
            community.metabolize_community(
                float(self.data["air_temperature"][0][community.community_key].values),
                self.update_interval_timedelta,
            )
            community.inflict_non_predation_mortality_community(
                self.update_interval_timedelta
            )
            community.remove_dead_cohort_community()
            community.increase_age_community(self.update_interval_timedelta)

        # Now that communities have been updated information required to update the
        # litter model can be extracted
        additions_to_litter = self.calculate_litter_additions()

        # Update the litter pools
        self.data.add_from_dict(additions_to_litter)

        # Update population densities
        self.update_population_densities()

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
                array(decomposed_excrement)
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
            "decomposed_carcasses": DataArray(
                array(decomposed_carcasses)
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
        }

    def update_population_densities(self) -> None:
        """Updates the densities for each functional group in each community."""

        for community_id, community in self.communities.items():
            for fg_name, cohorts in community.animal_cohorts.items():
                # Initialize the population density of the functional group
                fg_density = 0.0
                for cohort in cohorts:
                    # Calculate the population density for the cohort
                    fg_density += self.calculate_density_for_cohort(cohort)

                # Update the corresponding entry in the data variable
                # This update should happen once per functional group after summing
                # all cohort densities
                self.data["population_densities"].loc[
                    {"community_id": community_id, "functional_group_id": fg_name}
                ] = fg_density

    def calculate_density_for_cohort(self, cohort: AnimalCohort) -> float:
        """Calculate the population density for a cohort within a specific community.

        TODO: This will need to be modified for multi-grid occupancy.

        Args:
            cohort: The AnimalCohort object for which to calculate the density.
            community_id: The identifier for the community where the cohort resides.

        Returns:
            The population density of the cohort within the community (individuals/m2).
        """
        # Retrieve the area of the community where the cohort resides
        community_area = self.data.grid.cell_area

        # Calculate the population density
        population_density = cohort.individuals / community_area

        return population_density
