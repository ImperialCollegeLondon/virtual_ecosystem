"""The :mod:`~virtual_ecosystem.models.animal.animal_model` module creates a
:class:`~virtual_ecosystem.models.animal.animal_model.AnimalModel` class as a
child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.

At present a lot of the abstract methods of the parent class
(e.g. :func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are
overwritten using placeholder functions that don't do anything. This will
change as the Virtual Ecosystem model develops.

The factory method
:func:`~virtual_ecosystem.models.animal.animal_model.AnimalModel.from_config`
exists in a more complete state, and unpacks a small number of parameters
from our currently pretty minimal configuration dictionary. These parameters
are then used to generate a class instance. If errors emerge when converting
the information from the config dictionary to the required types
(e.g. :class:`~numpy.timedelta64`) they are caught and then logged, and at the
end of the unpacking an error is thrown. This error should be caught and
handled by downstream functions so that all model configuration failures can
be reported as one.
"""  # noqa: D205

from __future__ import annotations

import uuid
from math import ceil, sqrt
from random import choice
from typing import Any, cast

from numpy import array, float32, inf, random, timedelta64, where, zeros
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConfiguration
from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
from virtual_ecosystem.models.animal.animal_traits import (
    DevelopmentType,
    DietType,
    ReproductiveEnvironment,
)
from virtual_ecosystem.models.animal.cnp import CNP, find_microbial_stoichiometries
from virtual_ecosystem.models.animal.decay import (
    CarcassPool,
    ExcrementPool,
    FungalFruitPool,
    HerbivoryWaste,
    LitterPool,
    SoilPool,
)
from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter
from virtual_ecosystem.models.animal.functional_group import (
    FunctionalGroup,
    get_functional_group_by_name,
    import_functional_groups,
)
from virtual_ecosystem.models.animal.model_config import (
    AnimalConfiguration,
    AnimalConstants,
)
from virtual_ecosystem.models.animal.plant_resources import PlantResources
from virtual_ecosystem.models.animal.protocols import Resource
from virtual_ecosystem.models.animal.scaling_functions import (
    damuths_law,
    madingley_individuals_density,
    prey_group_selection,
)


class AnimalModel(
    BaseModel,
    model_name="animal",
    model_update_bounds=("1 day", "1 month"),
    vars_required_for_init=("fungal_fruiting_bodies",),
    vars_populated_by_init=("total_animal_respiration", "population_densities"),
    vars_required_for_update=(
        "litter_pool_above_metabolic",
        "litter_pool_above_structural",
        "litter_pool_woody",
        "litter_pool_below_metabolic",
        "litter_pool_below_structural",
        "c_n_ratio_above_metabolic",
        "c_n_ratio_above_structural",
        "c_n_ratio_woody",
        "c_n_ratio_below_metabolic",
        "c_n_ratio_below_structural",
        "c_p_ratio_above_metabolic",
        "c_p_ratio_above_structural",
        "c_p_ratio_woody",
        "c_p_ratio_below_metabolic",
        "c_p_ratio_below_structural",
        "production_of_fungal_fruiting_bodies",
    ),
    vars_populated_by_first_update=(
        "decomposed_excrement_carbon",
        "decomposed_excrement_nitrogen",
        "decomposed_excrement_phosphorus",
        "decomposed_carcasses_carbon",
        "decomposed_carcasses_nitrogen",
        "decomposed_carcasses_phosphorus",
        "herbivory_waste_leaf_carbon",
        "herbivory_waste_leaf_nitrogen",
        "herbivory_waste_leaf_phosphorus",
        "herbivory_waste_leaf_lignin",
        "litter_consumption_above_metabolic",
        "litter_consumption_above_structural",
        "litter_consumption_woody",
        "litter_consumption_below_metabolic",
        "litter_consumption_below_structural",
        "animal_pom_consumption_carbon",
        "animal_pom_consumption_nitrogen",
        "animal_pom_consumption_phosphorus",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
        "decay_of_fungal_fruiting_bodies",
    ),
    vars_updated=(
        "decomposed_excrement_carbon",
        "decomposed_excrement_nitrogen",
        "decomposed_excrement_phosphorus",
        "decomposed_carcasses_carbon",
        "decomposed_carcasses_nitrogen",
        "decomposed_carcasses_phosphorus",
        "herbivory_waste_leaf_carbon",
        "herbivory_waste_leaf_nitrogen",
        "herbivory_waste_leaf_phosphorus",
        "herbivory_waste_leaf_lignin",
        "total_animal_respiration",
        "litter_consumption_above_metabolic",
        "litter_consumption_above_structural",
        "litter_consumption_woody",
        "litter_consumption_below_metabolic",
        "litter_consumption_below_structural",
        "animal_pom_consumption_carbon",
        "animal_pom_consumption_nitrogen",
        "animal_pom_consumption_phosphorus",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
        "fungal_fruiting_bodies",
        "decay_of_fungal_fruiting_bodies",
    ),
):
    """A class describing the animal model.

    Describes the specific functions and attributes that the animal module should
    possess.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        exporter: The export system for animal cohort data.
        static: If True, runs in static mode.
        density_scaling_method: Which density scaling equation to use in initialization.
        **kwargs: Additional arguments for the base model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        exporter: AnimalCohortDataExporter,
        static: bool = False,
        **kwargs: Any,
    ):
        """Animal init function.

        The init function is used only to define class attributes. Any logic should be
        handled in :fun:`~virtual_ecosystem.animal.animal_model._setup`.
        """

        self.exporter: AnimalCohortDataExporter = exporter
        """Exporter for animal cohort data."""

        super().__init__(data, core_components, static, **kwargs)  # runs _setup

        self.model_constants: AnimalConstants
        """Animal constants."""
        self.communities: dict[int, list[AnimalCohort]]
        """Animal communities with grid cell IDs and lists of AnimalCohorts."""
        self.active_cohorts: dict[uuid.UUID, AnimalCohort] = {}
        """A dictionary of all active animal cohorts and their unique ids."""
        self.migrated_cohorts: dict[uuid.UUID, AnimalCohort] = {}
        """A dictionary of all migrated animal cohorts and their unique ids."""
        self.aquatic_cohorts: dict[uuid.UUID, AnimalCohort] = {}
        """A dictionary of all aquatic animal cohorts and their unique ids."""
        self.update_interval_timedelta: timedelta64
        """Convert pint update_interval to timedelta64 once during initialization."""
        self.functional_groups: list[FunctionalGroup]
        """List of functional groups in the model."""
        self.plant_resources: dict[int, list[Resource]]
        """The plant resource pools in the model with associated grid cell ids."""
        self.excrement_pools: dict[int, list[ExcrementPool]]
        """The excrement pools in the model with associated grid cell ids."""
        self.carcass_pools: dict[int, list[CarcassPool]]
        """The carcass pools in the model with associated grid cell ids."""
        self.leaf_waste_pools: dict[int, HerbivoryWaste]
        """A pool for leaves removed by herbivory but not actually consumed."""
        self.microbial_c_n_p_ratios: dict[str, dict[str, float]]
        """The CNP ratios of the different microbial functional groups."""
        self.litter_pools: dict[int, dict[str, Resource]]
        """The litter pools with associated grid cell ids."""
        # TODO: make the following two modifiable
        self.target_cohorts_per_fg: int
        """The target number of cohorts per functional group in each grid cell."""
        self.minimum_cohort_size: int
        """The minimum number of individuals to initialize a cohort at init."""
        self.soil_pools: dict[int, dict[str, SoilPool]]
        """The animal consumable soil pools with associated grid cell ids."""
        self.fungal_fruiting_bodies: dict[int, FungalFruitPool]
        """The pools of fungal fruiting bodies with associated grid cell ids."""

    def _setup_grid_neighbours(self) -> None:
        """Set up grid neighbours for the model.

        Currently, this is redundant with the set_neighbours method of grid.
        This will become a more complex animal specific implementation to manage
        functional group specific adjacency.

        """
        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))

    def _initialize_communities(self, functional_groups: list[FunctionalGroup]) -> None:
        """Initializes the animal communities.

        Args:
            functional_groups: The list of functional groups that will populate the
            model.

        """

        self.communities = {cell_id: [] for cell_id in self.data.grid.cell_id}

        for fg in functional_groups:
            total_individuals = self._estimate_total_individuals(fg)
            cohort_sizes = self._distribute_individuals_to_cohorts(total_individuals)
            cohort_locations = self._assign_cohort_locations(len(cohort_sizes))

            for size, cell_id in zip(cohort_sizes, cohort_locations):
                self.create_new_cohort(
                    functional_group=fg,
                    mass=fg.adult_mass,
                    age=0.0,
                    individuals=size,
                    centroid_key=cell_id,
                )

    def _estimate_total_individuals(self, functional_group: FunctionalGroup) -> int:
        """Estimates the total number of individuals of a functional group.

        Args:
            functional_group: The specific functional group having its individuals
                estimated.

        Returns: The integer number of individuals of the group.

        """

        total_area = self.data.grid.n_cells * self.data.grid.cell_area

        if functional_group.density_individuals_m2 is not None:
            # User-provided empirical density overrides scaling laws
            return int(functional_group.density_individuals_m2 * total_area)

        # No empirical density → use selected scaling method
        if self.density_scaling_method == "damuth":
            density = damuths_law(
                functional_group.adult_mass,
                functional_group.population_density_terms,
            )
        elif self.density_scaling_method == "madingley":
            density = madingley_individuals_density(
                functional_group.adult_mass,
                functional_group.population_density_terms,
            )
        else:
            raise ValueError(
                f"Unsupported density scaling method: {self.density_scaling_method}"
            )

        return ceil(density * total_area)

    def _distribute_individuals_to_cohorts(self, total_individuals: int) -> list[int]:
        """Distribute individuals into cohorts respecting minimum size.

        Args:
            total_individuals: The number of individuals to distribute.

        Returns:
            A list of cohort sizes.
        """
        n_target = self.target_cohorts_per_fg  # ideal number of cohorts
        min_size = self.minimum_cohort_size  # minimum size of cohorts

        if total_individuals < n_target * min_size:
            # if I don't have enough individuals to meet my size and number targets
            # reduce the number of cohorts
            n_target = max(1, total_individuals // min_size)

        base_size = total_individuals // n_target  # the number of indiv in each cohorts
        remainder = total_individuals % n_target  # the leftover number of indiv

        # evenly distribute the remained and return the list of cohort sizes
        return [base_size + 1 if i < remainder else base_size for i in range(n_target)]

    def _assign_cohort_locations(self, n_cohorts: int) -> list[int]:
        """Assign each cohort to a grid cell.

        Args:
            n_cohorts: Number of cohorts to distribute.

        Returns:
            A list of grid cell IDs for each cohort.
        """
        cell_ids = list(self.data.grid.cell_id)  # a list of all the grid cell ids
        n_cells = len(cell_ids)  # the number of grid cells

        if n_cohorts <= n_cells:  # if more cells than cohorts
            # assign one random cell per cohort without replacement
            return random.choice(cell_ids, size=n_cohorts, replace=False).tolist()
        else:  # if more cohorts than cells
            # one cohort per cell, to start
            locations = cell_ids.copy()
            # randomly select grid cell ids equal to number of remaining cohorts
            extra = random.choice(
                cell_ids, size=n_cohorts - n_cells, replace=True
            ).tolist()
            locations.extend(extra)  # assign the extras to the location list
            return locations

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
    ) -> AnimalModel:
        """Factory function to initialise the animal model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
        """

        # Extract the validated model configuration from the complete compiled
        # configuration.
        model_configuration: AnimalConfiguration = configuration.get_subconfiguration(
            "animal", AnimalConfiguration
        )

        core_configuration: CoreConfiguration = configuration.get_subconfiguration(
            "core", CoreConfiguration
        )

        functional_groups = import_functional_groups(
            fg_csv_file=model_configuration.functional_group_definitions_path,
            constants=model_configuration.constants,
        )

        # Find microbial stoichiometries based on the config
        microbial_c_n_p_ratios = find_microbial_stoichiometries(config=configuration)

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=core_configuration.data_output_options.out_path,
            config=model_configuration.cohort_data_export,
        )

        LOGGER.info(
            "Information required to initialise the animal model successfully "
            "extracted."
        )

        return cls(
            data=data,
            core_components=core_components,
            static=model_configuration.static,
            functional_groups=functional_groups,
            model_constants=model_configuration.constants,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
            exporter=exporter,
        )

    def _setup(
        self,
        functional_groups: list[FunctionalGroup],
        microbial_c_n_p_ratios: dict[str, dict[str, float]],
        model_constants: AnimalConstants,
        **kwargs: Any,
    ) -> None:
        """Method to setup the animal model specific data variables.

        This method initializes the data variables required by the animal model.
        Microbial stoichiometries have to be supplied so that the availability of
        nutrients to soil consuming taxa can be found.

        Args:
            functional_groups: The list of animal functional groups present in the
                simulation.
            microbial_c_n_p_ratios: Biomass stoichiometry of each microbial functional
                group.
            model_constants: An
                :class:`~virtual_ecosystem.models.animal.model_config.AnimalConstants`
                instance, providing constants for the model and setting the density
                scaling method to be used in simulation.
            **kwargs: Further arguments to the setup method.
        """

        self.model_constants = model_constants
        """Animal constants."""
        self.density_scaling_method = self.model_constants.density_scaling_method
        """Which density scaling equations are used, "damuth" or "madingley"."""

        days_as_float = self.model_timing.update_interval_quantity.to("days").magnitude
        self.update_interval_in_days = days_as_float
        """Store update interval as a number of days."""
        self.update_interval_timedelta = timedelta64(int(days_as_float), "D")
        """Convert pint update_interval to timedelta64 once during initialization."""

        self._setup_grid_neighbours()
        """Determine grid square adjacency."""
        self.functional_groups = functional_groups
        self.model_constants = self.model_constants
        self.plant_resources = {
            cell_id: [
                PlantResources(
                    data=self.data, cell_id=cell_id, constants=self.model_constants
                )
            ]
            for cell_id in self.data.grid.cell_id
        }

        # TODO - In future, need to take in data on average size of excrement and
        # carcasses pools and their stoichiometries for the initial scavengeable pool
        # parameterisations
        self.excrement_pools = {
            cell_id: [
                ExcrementPool(
                    scavengeable_cnp=CNP(1e-3, 1e-4, 1e-6),
                    decomposed_cnp=CNP(0.0, 0.0, 0.0),
                )
            ]
            for cell_id in self.data.grid.cell_id
        }

        self.carcass_pools = {
            cell_id: [
                CarcassPool(
                    scavengeable_cnp=CNP(1e-3, 1e-4, 1e-6),
                    decomposed_cnp=CNP(0.0, 0.0, 0.0),
                )
            ]
            for cell_id in self.data.grid.cell_id
        }

        self.leaf_waste_pools = {
            cell_id: HerbivoryWaste(plant_matter_type="leaf")
            for cell_id in self.data.grid.cell_id
        }

        self.active_cohorts = {}
        self.communities = {cell_id: list() for cell_id in self.data.grid.cell_id}

        self.target_cohorts_per_fg = len(self.data.grid.cell_id)
        """The target number of cohorts per functional group in each grid cell."""
        self.minimum_cohort_size = 5
        """The minimum number of individuals to initialize a cohort at init."""

        # Microbial C:N:P ratios are then found, and the size of the initial litter and
        # soil pools are populated
        self.microbial_c_n_p_ratios = microbial_c_n_p_ratios
        self.litter_pools = self.populate_litter_pools()
        self.soil_pools = self.populate_soil_pools()
        self.fungal_fruiting_bodies = self.populate_fungal_fruiting_bodies()

        self._initialize_communities(functional_groups)
        """Create the dictionary of animal communities and populate each community with
        animal cohorts."""

        self.exporter.dump(
            communities=self.communities,
            time=self.model_timing.start_time,
        )

        # animal respiration data variable
        # the array should have one value for each animal community
        n_grid_cells = len(self.data.grid.cell_id)

        # Initialize total_animal_respiration as a DataArray with a single dimension:
        # cell_id
        total_animal_respiration = DataArray(
            zeros(
                n_grid_cells
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
        community_ids = self.data.grid.cell_id

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

    def spinup(self) -> None:
        """Placeholder function to spin up the animal model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Function to step the animal model through time.

        This method sets the order of operations for the animal module. In nature, these
        events would be simultaneous. The ordering within the method is less a question
        of the science and more a question of computational logic and stability.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # TODO: merge problems as community looping is not internal to comm methods
        # TODO: These pools are populated but nothing actually gets done with them at
        # the moment, this will have to change when scavenging gets introduced

        # The litter and soil pools have to be populated again to reflect the changes
        # that will have happened in the last time step for those models
        self.litter_pools = self.populate_litter_pools()
        self.soil_pools = self.populate_soil_pools()

        # The fungal fruiting bodies need to be updated based on input from soil fungi
        # and the rate of decay
        fruiting_bodies_decay = self.update_fungal_fruiting_bodies()

        self.forage_community(self.update_interval_timedelta)
        self.migrate_community()
        self.birth_community()
        self.metamorphose_community()
        self.migrate_external_community()
        self.metabolize_community(self.update_interval_timedelta)
        self.inflict_non_predation_mortality_community(self.update_interval_timedelta)
        self.update_community_bookkeeping(self.update_interval_timedelta)
        self.update_cohort_bookkeeping(self.update_interval_timedelta)

        # Now that communities have been updated information required to update the
        # soil and litter models can be extracted
        additions_to_soil = self.calculate_soil_additions()
        litter_consumption = self.calculate_total_litter_consumption(self.litter_pools)
        soil_consumption = self.calculate_total_soil_consumption(self.soil_pools)
        litter_additions = self.calculate_litter_additions_from_herbivory()

        # Now that animal consumption has finished, the data object can be updated to
        # reflect the new size of the fungal fruiting body pools
        self.update_fungal_fruiting_bodies_in_data()

        # Update the data object with the changes to soil and litter pools
        self.data.add_from_dict(
            fruiting_bodies_decay
            | additions_to_soil
            | soil_consumption
            | litter_consumption
            | litter_additions
        )

        # Update population densities
        self.update_population_densities()

        # Dump the cohort data to CSV
        self.exporter.dump(
            communities=self.communities,
            time=(
                self.model_timing.start_time
                + time_index * self.model_timing.update_interval
            ),
        )

    def update_community_bookkeeping(self, dt: timedelta64) -> None:
        """Perform status updates and cleanup at the community level.

        This includes:
        - Updating timers for migrated or aquatic cohorts
        - Reintegration of previously inactive cohorts
        - Removal of dead cohorts

        Args:
            dt: Time step duration [days].
        """

        self.update_migrated_and_aquatic(dt)
        self.reintegrate_community()
        self.remove_dead_cohort_community()

    def update_cohort_bookkeeping(self, dt: timedelta64) -> None:
        """Perform lifecycle-related updates for each cohort.

        This includes:
        - Increasing age
        - Updating largest mass achieved

        Args:
            dt: Time step duration [days].
        """
        self.increase_age_community(dt)
        self.handle_ontogeny()

    def cleanup(self) -> None:
        """Placeholder function for animal model cleanup."""

    def populate_litter_pools(self) -> dict[int, dict[str, Resource]]:
        """Populate the litter pools that animals can consume from.

        Returns:
            dict[str, Resource]: A dictionary where keys represent the pool types and
            values are the corresponding LitterPool objects. The following pools are
            included:

            - "above_metabolic": Litter pool for above-ground metabolic organic matter
            - "above_structural": Litter pool for above-ground structural organic matter
            - "woody": Litter pool for woody biomass
            - "below_metabolic": Litter pool for below-ground metabolic organic matter
            - "below_structural": Litter pool for below-ground structural organic matter

        """

        litter_types = (
            "above_metabolic",
            "above_structural",
            "woody",
            "below_metabolic",
            "below_structural",
        )

        return {
            cell_id: {
                lt: LitterPool(
                    pool_name=lt,
                    cell_id=cell_id,
                    data=self.data,
                    cell_area=self.data.grid.cell_area,  # OK while area is uniform
                )
                for lt in litter_types
            }
            for cell_id in self.data.grid.cell_id
        }

    def populate_soil_pools(self) -> dict[int, dict[str, SoilPool]]:
        """Populate the soil pools that animals can consume from.

        Returns:
            A dictionary where keys represent the pool types and values are the
            corresponding SoilPool objects. The following pools are included:

            - "pom": Particulate organic matter
            - "bacteria": Bacteria
            - "fungi": Fungi (i.e. all fungal functional groups)
        """

        soil_organic_matter_types = ("pom", "bacteria", "fungi")

        return {
            cell_id: {
                som_type: SoilPool(
                    pool_name=som_type,
                    cell_id=cell_id,
                    data=self.data,
                    cell_area=self.data.grid.cell_area,  # OK while area is uniform
                    max_depth_microbial_activity=self.core_constants.max_depth_of_microbial_activity,
                    c_n_p_ratios=self.microbial_c_n_p_ratios,
                )
                for som_type in soil_organic_matter_types
            }
            for cell_id in self.data.grid.cell_id
        }

    def populate_fungal_fruiting_bodies(self) -> dict[int, FungalFruitPool]:
        """Populate the fungal fruiting body pools for animal consumption.

        Returns:
            A dictionary with a fungal fruiting body pool for each cell ID.
        """

        return {
            cell_id: FungalFruitPool(
                cell_id=cell_id,
                data=self.data,
                cell_area=self.data.grid.cell_area,  # OK while area is uniform
                c_n_ratio=self.core_constants.fungal_fruiting_bodies_c_n_ratio,
                c_p_ratio=self.core_constants.fungal_fruiting_bodies_c_p_ratio,
            )
            for cell_id in self.data.grid.cell_id
        }

    def calculate_total_litter_consumption(
        self, litter_pools: dict[int, dict[str, Resource]]
    ) -> dict[str, DataArray]:
        """Compute carbon removed from every litter pool, by cell.

        Args:
            litter_pools: Mapping created at
                model setup.

        Returns:
            Dictionary whose keys are
            ``"litter_consumption_<pool_name>"`` and whose values are 1-D
            :class:`xarray.DataArray` objects (dimension ``cell_id``) containing the
            amount of carbon consumed from each litter pool during the current
            update, expressed in kg C m⁻².
        """
        # List of pool names handled by the model
        litter_types = (
            "above_metabolic",
            "above_structural",
            "woody",
            "below_metabolic",
            "below_structural",
        )

        cell_ids = self.data.grid.cell_id
        area = self.data.grid.cell_area  # Cell area is uniform at present

        results: dict[str, DataArray] = {}

        for pool in litter_types:
            # Original stock at the start of the step (kg C m⁻²)
            start_stock = self.data[f"litter_pool_{pool}"].to_numpy()

            # Current stock after detritivore feeding (kg C m⁻²)
            end_stock = array(
                [litter_pools[cid][pool].mass_current / area for cid in cell_ids]
            )

            # Consumption equals start minus end
            consumption = start_stock - end_stock

            results[f"litter_consumption_{pool}"] = DataArray(
                consumption, dims="cell_id"
            )

        return results

    def calculate_total_soil_consumption(
        self, soil_pools: dict[int, dict[str, SoilPool]]
    ) -> dict[str, DataArray]:
        """Compute carbon and nutrients removed from every soil pool, by cell.

        The soil model treats microbial stoichiometry as fixed so only removal of
        particulate organic nitrogen and phosphorus is calculated explicitly. The soil
        model also subdivides fungi, so this function also calculates how much of the
        fungal removal should come from each group.

        Args:
            soil_pools: Set of soil pools available for animal consumption [kg]

        Returns:
            The rate at which biomass is removed from the relevant soil model pools [kg
            m^-3 day^-1]
        """

        cell_ids = self.data.grid.cell_id
        area = self.data.grid.cell_area  # Cell area is uniform at present

        pom_initial_stock = self.data["soil_c_pool_pom"].to_numpy()

        pom_final_stock = array(
            [
                soil_pools[cid]["pom"].mass_current
                / (area * self.core_constants.max_depth_of_microbial_activity)
                for cid in cell_ids
            ]
        )

        pom_consumption_carbon = pom_initial_stock - pom_final_stock
        # Calculate nutrient consumptions based on carbon consumption and pool
        # stoichiometric ratios
        pom_c_n_ratios = array(
            [soil_pools[cid]["pom"].mass_cnp.get_ratios()["C:N"] for cid in cell_ids]
        )
        pom_c_p_ratios = array(
            [soil_pools[cid]["pom"].mass_cnp.get_ratios()["C:P"] for cid in cell_ids]
        )
        pom_consumption_nitrogen = pom_consumption_carbon / pom_c_n_ratios
        pom_consumption_phosphorus = pom_consumption_carbon / pom_c_p_ratios

        bacteria_initial_stock = self.data["soil_c_pool_bacteria"].to_numpy()

        bacteria_final_stock = array(
            [
                soil_pools[cid]["bacteria"].mass_current
                / (area * self.core_constants.max_depth_of_microbial_activity)
                for cid in cell_ids
            ]
        )

        bacteria_consumption = bacteria_initial_stock - bacteria_final_stock

        # Have to account for the fact that the values in data object for mycorrhizal
        # fungi can be negative, which is treated as zero for animal consumption
        # purposes
        saprotrophic_fungi_initial_stock = self.data[
            "soil_c_pool_saprotrophic_fungi"
        ].to_numpy()
        arbuscular_mycorrhiza_initial_stock = where(
            self.data["soil_c_pool_arbuscular_mycorrhiza"].to_numpy() > 0,
            self.data["soil_c_pool_arbuscular_mycorrhiza"].to_numpy(),
            0,
        )
        ectomycorrhiza_initial_stock = where(
            self.data["soil_c_pool_ectomycorrhiza"].to_numpy() > 0,
            self.data["soil_c_pool_ectomycorrhiza"].to_numpy(),
            0,
        )
        fungi_initial_stock = (
            saprotrophic_fungi_initial_stock
            + arbuscular_mycorrhiza_initial_stock
            + ectomycorrhiza_initial_stock
        )

        fungi_final_stock = array(
            [
                soil_pools[cid]["fungi"].mass_current
                / (area * self.core_constants.max_depth_of_microbial_activity)
                for cid in cell_ids
            ]
        )
        fungi_consumption = fungi_initial_stock - fungi_final_stock

        # Calculate how much of the fungal consumption is applied to each fungal group
        # based on initial pool sizes
        saprotrophic_fungi_consumption = fungi_consumption * (
            saprotrophic_fungi_initial_stock / fungi_initial_stock
        )
        ectomycorrhiza_consumption = fungi_consumption * (
            ectomycorrhiza_initial_stock / fungi_initial_stock
        )
        arbuscular_mycorrhiza_consumption = fungi_consumption * (
            arbuscular_mycorrhiza_initial_stock / fungi_initial_stock
        )

        return {
            "animal_pom_consumption_carbon": self.to_per_day(pom_consumption_carbon),
            "animal_pom_consumption_nitrogen": self.to_per_day(
                pom_consumption_nitrogen
            ),
            "animal_pom_consumption_phosphorus": self.to_per_day(
                pom_consumption_phosphorus
            ),
            "animal_bacteria_consumption": self.to_per_day(bacteria_consumption),
            "animal_saprotrophic_fungi_consumption": self.to_per_day(
                saprotrophic_fungi_consumption
            ),
            "animal_ectomycorrhiza_consumption": self.to_per_day(
                ectomycorrhiza_consumption
            ),
            "animal_arbuscular_mycorrhiza_consumption": self.to_per_day(
                arbuscular_mycorrhiza_consumption
            ),
        }

    def calculate_litter_additions_from_herbivory(self) -> dict[str, DataArray]:
        """Calculate additions to litter due to herbivory mechanical inefficiencies.

        TODO - At present the only type of herbivory this works for is leaf herbivory,
        that should be changed once herbivory as a whole is fleshed out.

        Returns:
            A dictionary containing details of the leaf litter addition due to herbivory
            this comprises of the mass added in carbon terms [kg C m^-2], ratio of
            carbon to nitrogen [unitless], ratio of carbon to phosphorus [unitless], and
            the proportion of input carbon that is lignin [unitless].
        """

        # Find the size of the leaf waste pool (in carbon terms)
        leaf_addition = [
            self.leaf_waste_pools[cell_id].mass_cnp["carbon"] / self.data.grid.cell_area
            for cell_id in self.data.grid.cell_id
        ]

        # Find the chemistry of the pools, handling different cases properly
        leaf_c_n = [
            self.leaf_waste_pools[cell_id].mass_cnp["carbon"]
            / self.leaf_waste_pools[cell_id].mass_cnp["nitrogen"]
            if self.leaf_waste_pools[cell_id].mass_cnp["nitrogen"] > 0
            else inf
            for cell_id in self.data.grid.cell_id
        ]

        leaf_c_p = [
            self.leaf_waste_pools[cell_id].mass_cnp["carbon"]
            / self.leaf_waste_pools[cell_id].mass_cnp["phosphorus"]
            if self.leaf_waste_pools[cell_id].mass_cnp["phosphorus"] > 0
            else inf
            for cell_id in self.data.grid.cell_id
        ]

        leaf_lignin = [
            self.leaf_waste_pools[cell_id].lignin_proportion
            for cell_id in self.data.grid.cell_id
        ]

        # Reset all of the herbivory waste pools to zero
        for waste in self.leaf_waste_pools.values():
            waste.mass_cnp["carbon"] = 0.0
            waste.mass_cnp["nitrogen"] = 0.0
            waste.mass_cnp["phosphorus"] = 0.0

        return {
            "herbivory_waste_leaf_carbon": DataArray(
                array(leaf_addition), dims="cell_id"
            ),
            "herbivory_waste_leaf_nitrogen": DataArray(array(leaf_c_n), dims="cell_id"),
            "herbivory_waste_leaf_phosphorus": DataArray(
                array(leaf_c_p), dims="cell_id"
            ),
            "herbivory_waste_leaf_lignin": DataArray(
                array(leaf_lignin), dims="cell_id"
            ),
        }

    def update_fungal_fruiting_bodies(self) -> dict[str, DataArray]:
        """Update fungal fruiting bodies pools due to fungal production and decay.

        This method first updates the fungal fruiting body pools with the new biomass
        supplied from the soil model. The total decay of the fungal fruiting bodies is
        then calculated and subtracted from the pools. This ordering means that we are
        prioritising decay over before animal consumption, which is consistent with the
        assumptions we made for excrement and carcass decay.

        Returns:
            The rate at which fungal fruiting bodies decay back into the soil [kg m^-2
            day^-1].
        """

        for cell_id, fungal_fruiting_bodies_pool in self.fungal_fruiting_bodies.items():
            production = (
                self.data["production_of_fungal_fruiting_bodies"]
                .isel(cell_id=cell_id)
                .item()
                * self.grid.cell_area
                * self.update_interval_in_days
            )
            fungal_fruiting_bodies_pool.mass_cnp.update(
                carbon=+production,
                nitrogen=+production / fungal_fruiting_bodies_pool.c_n_ratio,
                phosphorus=+production / fungal_fruiting_bodies_pool.c_p_ratio,
            )

        total_decay = [
            fungal_fruiting_bodies_pool.apply_decay(
                decay_constant=self.core_constants.fungal_fruiting_bodies_decay_rate,
                time_period=self.update_interval_in_days,
            )
            for fungal_fruiting_bodies_pool in self.fungal_fruiting_bodies.values()
        ]

        return {
            "decay_of_fungal_fruiting_bodies": DataArray(
                array(total_decay)
                / (self.grid.cell_area * self.update_interval_in_days),
                dims="cell_id",
            )
        }

    def calculate_soil_additions(self) -> dict[str, DataArray]:
        """Calculate how much animal matter should be transferred to the soil."""

        nutrients = ["carbon", "nitrogen", "phosphorus"]

        # Find the size of all decomposed excrement and carcass pools, by cell_id
        decomposed_excrement = {
            nutrient: [
                pool.decomposed_nutrient_per_area(
                    nutrient=nutrient, grid_cell_area=self.data.grid.cell_area
                )
                for cell_id, pools in self.excrement_pools.items()
                for pool in pools
            ]
            for nutrient in nutrients
        }

        decomposed_carcasses = {
            nutrient: [
                pool.decomposed_nutrient_per_area(
                    nutrient=nutrient, grid_cell_area=self.data.grid.cell_area
                )
                for cell_id, pools in self.carcass_pools.items()
                for pool in pools
            ]
            for nutrient in nutrients
        }

        # Reset all decomposed excrement pools to zero
        for excrement_pools in self.excrement_pools.values():
            for excrement_pool in excrement_pools:
                excrement_pool.reset()

        for carcass_pools in self.carcass_pools.values():
            for carcass_pool in carcass_pools:
                carcass_pool.reset()

        # Create the output DataArray for each nutrient
        return {
            "decomposed_excrement_carbon": self.to_per_day(
                array(decomposed_excrement["carbon"])
            ),
            "decomposed_excrement_nitrogen": self.to_per_day(
                array(decomposed_excrement["nitrogen"])
            ),
            "decomposed_excrement_phosphorus": self.to_per_day(
                array(decomposed_excrement["phosphorus"])
            ),
            "decomposed_carcasses_carbon": self.to_per_day(
                array(decomposed_carcasses["carbon"])
            ),
            "decomposed_carcasses_nitrogen": self.to_per_day(
                array(decomposed_carcasses["nitrogen"])
            ),
            "decomposed_carcasses_phosphorus": self.to_per_day(
                array(decomposed_carcasses["phosphorus"])
            ),
        }

    def update_fungal_fruiting_bodies_in_data(self) -> None:
        """Method to update the fungal fruiting bodies in the data object.

        This update is based on the current state of the animal model FungalFruitPools.
        This method is run after the additions due to new fungal fruiting body
        production and removals due to decay and animal consumption have been made.
        """

        for cell_id, fungal_fruiting_bodies_pool in self.fungal_fruiting_bodies.items():
            self.data["fungal_fruiting_bodies"].loc[{"cell_id": cell_id}] = (
                fungal_fruiting_bodies_pool.mass_cnp["carbon"]
                / self.data.grid.cell_area
            )

    def to_per_day(self, change: NDArray[float32]) -> DataArray:
        """Method to convert a change caused by the animal model into a per day rate.

        Args:
            change: Change in pool caused by the animal model [kg m^-3].

        Returns:
            Change converted to a per day rate (which are the units the soil model needs
            it in) units [kg m^-3 day^-1].
        """

        return DataArray(change / self.update_interval_in_days, dims="cell_id")

    def update_population_densities(self) -> None:
        """Updates the densities for each functional group in each community."""

        for community_id, community in self.communities.items():
            # Create a dictionary to accumulate densities by functional group
            fg_density_dict = {}

            for cohort in community:
                fg_name = cohort.functional_group.name
                fg_density = self.calculate_density_for_cohort(cohort)

                # Sum the density for the functional group
                if fg_name not in fg_density_dict:
                    fg_density_dict[fg_name] = 0.0
                fg_density_dict[fg_name] += fg_density

            # Update the corresponding entries in the data variable for each
            # functional group
            for fg_name, fg_density in fg_density_dict.items():
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

    def abandon_communities(self, cohort: AnimalCohort) -> None:
        """Removes the cohort from the occupancy of every community.

        This method is for use in death or re-initializing territories.

        Args:
            cohort: The cohort to be removed from the occupancy lists.
        """
        for cell_id in cohort.territory:
            self.communities[cell_id] = [
                c for c in self.communities[cell_id] if c.id != cohort.id
            ]

    def update_community_occupancy(
        self, cohort: AnimalCohort, centroid_key: int
    ) -> None:
        """This updates the community lists for animal cohort occupancy.

        Args:
            cohort: The animal cohort being updates.
            centroid_key: The grid cell key of the anchoring grid cell.
        """

        territory_cells = cohort.get_territory_cells(centroid_key)
        cohort.update_territory(territory_cells)

        for cell_id in territory_cells:
            self.communities[cell_id].append(cohort)

    def migrate(self, migrant: AnimalCohort, destination_centroid: int) -> None:
        """Function to move an AnimalCohort between grid cells.

        This function takes a cohort and a destination grid cell, changes the
        centroid of the cohort's territory to be the new cell, and then
        reinitializes the territory around the new centroid.

        TODO: travel distance should be a function of body-size or locomotion once
            multi-grid occupancy is integrated.

        Args:
            migrant: The AnimalCohort moving between AnimalCommunities.
            destination_centroid: The grid cell the cohort is moving to.

        """

        # Remove the cohort from its current community
        current_centroid = migrant.centroid_key
        self.communities[current_centroid].remove(migrant)

        # Update the cohort's cell ID to the destination cell ID
        migrant.centroid_key = destination_centroid

        # Add the cohort to the destination community
        self.communities[destination_centroid].append(migrant)

        # Regenerate a territory for the cohort at the destination community
        self.abandon_communities(migrant)
        self.update_community_occupancy(migrant, destination_centroid)

    def migrate_community(self) -> None:
        """This handles migrating all cohorts with a centroid in the community.

        This migration method initiates migration for two reasons:
        1) The cohort is starving and needs to move for a chance at resource access
        2) An initial migration event immediately after birth.

        TODO: MGO - migrate distance mod for larger territories?


        """
        for cohort in self.active_cohorts.values():
            is_starving = cohort.is_below_mass_threshold(
                self.model_constants.dispersal_mass_threshold
            )
            is_juvenile_and_migrate = (
                cohort.age == 0.0
                and random.random() <= cohort.migrate_juvenile_probability()
            )
            migrate = is_starving or is_juvenile_and_migrate

            if not migrate:
                continue

            # Get the list of neighbors for the current cohort's cell
            neighbour_keys = self.data.grid.neighbours[cohort.centroid_key]

            destination_key = choice(neighbour_keys)
            self.migrate(cohort, destination_key)

    def remove_dead_cohort(self, cohort: AnimalCohort) -> None:
        """Removes an AnimalCohort from the model's cohorts and relevant communities.

        This method removes the cohort from every community listed in its territory's
        grid cell keys, and then removes it from the model's main cohort dictionary.

        Args:
            cohort: The AnimalCohort to be removed.

        Raises:
            KeyError: If the cohort ID does not exist in the model's cohorts.
        """
        # Check if the cohort exists in self.active_cohorts
        if cohort.id in self.active_cohorts:
            # Iterate over all grid cell keys in the cohort's territory
            for cell_id in cohort.territory:
                if cell_id in self.communities and cohort in self.communities[cell_id]:
                    self.communities[cell_id].remove(cohort)

            # Remove the cohort from the model's cohorts dictionary
            del self.active_cohorts[cohort.id]
        else:
            raise KeyError(f"Cohort with ID {cohort.id} does not exist.")

    def remove_dead_cohort_community(self) -> None:
        """This handles remove_dead_cohort for all cohorts in a community."""
        # Collect cohorts to remove (to avoid modifying the dictionary during iteration)
        cohorts_to_remove = [
            cohort for cohort in self.active_cohorts.values() if cohort.individuals == 0
        ]

        # Remove each cohort
        for cohort in cohorts_to_remove:
            cohort.is_alive = False
            self.remove_dead_cohort(cohort)

    def birth(self, parent_cohort: AnimalCohort) -> None:
        """Produce offspring for a parent cohort using helper methods.

        This orchestrates the reproduction process, including:
        - Calculating total available reproductive mass.
        - Determining number of offspring.
        - Creating offspring and adding them to the population.
        - Updating parent mass after reproduction.
        - Removing semelparous parents if applicable.

        Args:
            parent_cohort: The parent cohort giving birth.
        """
        reproductive_mass = self.calculate_total_reproductive_mass(parent_cohort)
        number_offspring = self.calculate_offspring_count(
            parent_cohort, reproductive_mass
        )

        if number_offspring == 0:
            return  # Insufficient mass for offspring

        self.create_offspring(parent_cohort, number_offspring)
        self.handle_post_birth_parent_updates(parent_cohort, number_offspring)

    def calculate_total_reproductive_mass(
        self, parent: AnimalCohort
    ) -> dict[str, float]:
        """Calculate total reproductive mass available for offspring.

        For semelparous species, part of the parent's non-reproductive mass
        is also transferred to reproduction as they die after reproducing.

        Args:
            parent: The parent cohort.

        Returns:
            Reproductive mass for carbon, nitrogen, phosphorus (kg).
        """
        semelparous_loss = self.calculate_semelparous_mass_loss(parent)

        return {
            "carbon": parent.reproductive_mass_cnp.carbon + semelparous_loss["carbon"],
            "nitrogen": parent.reproductive_mass_cnp.nitrogen
            + semelparous_loss["nitrogen"],
            "phosphorus": parent.reproductive_mass_cnp.phosphorus
            + semelparous_loss["phosphorus"],
        }

    def calculate_offspring_count(
        self, parent: AnimalCohort, reproductive_mass: dict[str, float]
    ) -> int:
        """Calculate the maximum number of total offspring based on available mass.

        Each offspring has a defined birth mass, which must be split into C, N, and P.
        The limiting nutrient determines how many offspring can be made.

        Args:
            parent: The parent cohort.
            reproductive_mass: Available reproductive mass (C, N, P).

        Returns:
            Number of offspring.
        """
        birth_mass = parent.functional_group.birth_mass
        birth_c, birth_n, birth_p = self.calculate_birth_mass_cnp(birth_mass, parent)

        # Find the limiting element — how many offspring can be made from each element?
        max_per_parent = min(
            reproductive_mass["carbon"] / birth_c,
            reproductive_mass["nitrogen"] / birth_n,
            reproductive_mass["phosphorus"] / birth_p,
        )
        # Total offspring is limited offspring per parent times the number of parents
        return int(max_per_parent * parent.individuals)

    def handle_post_birth_parent_updates(
        self,
        parent: AnimalCohort,
        offspring_count: int,
    ) -> None:
        """Update parent's reproductive mass and handle semelparous death if needed.

        Reduces the parent's reproductive mass based on offspring produced.
        Removes semelparous parents after reproduction.

        Args:
            parent: The parent cohort.
            offspring_count: Number of offspring produced.
        """
        birth_mass = parent.functional_group.birth_mass
        birth_c, birth_n, birth_p = self.calculate_birth_mass_cnp(birth_mass, parent)

        total_c = offspring_count * birth_c
        total_n = offspring_count * birth_n
        total_p = offspring_count * birth_p

        # TODO: double check that total_c can't be more than available mass
        parent.reproductive_mass_cnp.update(
            carbon=-min(total_c, parent.reproductive_mass_cnp.carbon),
            nitrogen=-min(total_n, parent.reproductive_mass_cnp.nitrogen),
            phosphorus=-min(total_p, parent.reproductive_mass_cnp.phosphorus),
        )

        if parent.functional_group.reproductive_type == "semelparous":
            self.handle_semelparous_parent_death(parent)

    def handle_semelparous_parent_death(self, parent: AnimalCohort) -> None:
        """Apply mass loss and remove parent cohort for semelparous species.

        Semelparous parents die after reproducing, so we:
        - Apply a mass loss to the parent.
        - Set parent to `is_alive = False`.
        - Remove the parent from the population.

        Args:
            parent: The parent cohort.
        """
        # TODO: avoid recalculating this mass loss
        loss = self.calculate_semelparous_mass_loss(parent)

        parent.mass_cnp.update(
            carbon=-loss["carbon"],
            nitrogen=-loss["nitrogen"],
            phosphorus=-loss["phosphorus"],
        )
        parent.is_alive = False
        self.remove_dead_cohort(parent)

    def calculate_semelparous_mass_loss(self, parent: AnimalCohort) -> dict[str, float]:
        """Calculate the mass lost by a semelparous parent after reproduction.

        If the species is not semelparous, returns zero loss.

        Args:
            parent: The parent cohort.

        Returns:
            Dictionary of mass loss (C, N, P).
        """
        if parent.functional_group.reproductive_type != "semelparous":
            return {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}

        loss_fraction = parent.constants.semelparity_mass_loss

        return {
            "carbon": parent.mass_cnp.carbon * loss_fraction,
            "nitrogen": parent.mass_cnp.nitrogen * loss_fraction,
            "phosphorus": parent.mass_cnp.phosphorus * loss_fraction,
        }

    def calculate_birth_mass_cnp(
        self, birth_mass: float, parent: AnimalCohort
    ) -> tuple[float, float, float]:
        """Convert total birth mass into carbon, nitrogen, and phosphorus components.

        Args:
            birth_mass: Total birth mass per offspring.
            parent: Parent cohort providing stoichiometry.

        Returns:
            Tuple of (birth_carbon, birth_nitrogen, birth_phosphorus).
        """
        proportions = parent.cnp_proportions
        return (
            birth_mass * proportions["carbon"],
            birth_mass * proportions["nitrogen"],
            birth_mass * proportions["phosphorus"],
        )

    def create_offspring(
        self, parent: AnimalCohort, number_offspring: int
    ) -> AnimalCohort:
        """Create a new offspring cohort using the parent's offspring group definition.

        Args:
            parent: The parent cohort.
            number_offspring: Number of offspring to create.

        Returns:
            The newly created AnimalCohort.
        """
        offspring_functional_group = get_functional_group_by_name(
            self.functional_groups,
            parent.functional_group.offspring_functional_group,
        )

        offspring = self.create_new_cohort(
            functional_group=offspring_functional_group,
            mass=offspring_functional_group.birth_mass,
            age=0.0,
            individuals=number_offspring,
            centroid_key=parent.centroid_key,
            is_birth=True,
        )

        return offspring

    def birth_community(self) -> None:
        """This handles birth for all cohorts in a community."""

        # reproduction occurs for cohorts with sufficient reproductive mass
        for cohort in self.active_cohorts.values():
            if (
                not cohort.is_below_mass_threshold(
                    self.model_constants.birth_mass_threshold
                )
                and cohort.functional_group.reproductive_type != "nonreproductive"
            ):
                self.birth(cohort)

    def forage_community(self, dt: timedelta64) -> None:
        """Loop through each active cohort and trigger resource consumption.

        Diet flags on a cohort determine which resource lists are assembled and
        forwarded to ``cohort.forage_cohort``:

        * ``DietType.HERBIVORE``      → live plant resources
        * ``DietType.CARNIVORE``      → live prey cohorts
        * ``DietType.DETRITUS``       → plant-litter pools (detritivory)
        * ``DietType.CARCASSES``      → carcass pools (scavenging)
        * ``DietType.WASTE``          → excrement pools (coprophagy)
        * ``DietType.MUSHROOMS``      → fungal fruiting bodies
        * ``DietType.FUNGI``          → soil fungi (SoilPool['fungi'])
        * ``DietType.POM``            → soil POM (SoilPool['pom'])
        * ``DietType.BACTERIA``       → soil bacteria (SoilPool['bacteria'])

        Deposition targets (``excrement_pools`` for faeces and ``carcass_pool_map``
        for uneaten prey remains) are always supplied so trophic functions can
        update them regardless of whether the cohort actively scavenges in the
        same step.

        Args:
            dt: Time step duration.
        """

        for cohort in list(self.active_cohorts.values()):
            # Safety check territory must be defined
            if cohort.territory is None:
                raise ValueError("The cohort's territory hasn't been defined.")

            diet: DietType = cohort.functional_group.diet

            # Build resource collections based on diet flags
            plant_list: list[Resource] = []
            prey_list: list[AnimalCohort] = []
            fungal_fruit_list: list[Resource] = []
            soil_fungi_list: list[Resource] = []
            pom_list: list[Resource] = []
            bacteria_list: list[Resource] = []
            litter_list: list[Resource] = []
            scavenge_carcass_pools: list[Resource] = []
            scavenge_waste_pools: list[Resource] = []

            # Deposition targets (always passed)
            excrement_pools = cohort.get_excrement_pools(self.excrement_pools)
            carcass_pool_map = self.carcass_pools

            # Live plant resources
            if diet & (
                DietType.ALGAE
                | DietType.FLOWERS
                | DietType.FOLIAGE
                | DietType.FRUIT
                | DietType.SEEDS
                | DietType.NECTAR
                | DietType.WOOD
            ):
                plant_list = cohort.get_plant_resources(self.plant_resources)

            # Live prey
            if diet & (
                DietType.BLOOD
                | DietType.INVERTEBRATES
                | DietType.FISH
                | DietType.VERTEBRATES
            ):
                prey_list = cohort.get_prey(self.communities)

            # Fruiting-body fungivory
            if diet & DietType.MUSHROOMS:
                fungal_fruit_list = cohort.get_fungal_fruit_pools(
                    self.fungal_fruiting_bodies
                )

            # Soil fungi
            if diet & DietType.FUNGI:
                soil_fungi_list = cohort.get_soil_fungi_pools(self.soil_pools)

            # Soil POM
            if diet & DietType.POM:
                pom_list = cohort.get_pom_pools(self.soil_pools)

            # Soil bacteria
            if diet & DietType.BACTERIA:
                bacteria_list = cohort.get_bacteria_pools(self.soil_pools)

            # Plant litter detritivory
            if diet & DietType.DETRITUS:
                litter_list = cohort.get_litter_pools(self.litter_pools)

            # Carcass scavenging
            if diet & DietType.CARCASSES:
                scavenge_carcass_pools = cast(
                    list[Resource], cohort.get_carcass_pools(self.carcass_pools)
                )

            # Coprophagy
            if diet & DietType.WASTE:
                scavenge_waste_pools = cast(list[Resource], excrement_pools)

            # Delegate to cohort-level foraging
            cohort.forage_cohort(
                plant_list=plant_list,
                animal_list=prey_list,
                fungal_fruit_list=fungal_fruit_list,
                soil_fungi_list=soil_fungi_list,
                pom_list=pom_list,
                bacteria_list=bacteria_list,
                litter_pools=litter_list,
                excrement_pools=excrement_pools,  # for defecation
                carcass_pool_map=carcass_pool_map,  # for prey remains
                scavenge_carcass_pools=scavenge_carcass_pools,
                scavenge_excrement_pools=scavenge_waste_pools,
                herbivory_waste_pools=self.leaf_waste_pools,
                dt=dt,
            )

        # Remove cohorts that died during foraging
        self.remove_dead_cohort_community()

    def metabolize_community(self, dt: timedelta64) -> None:
        """This handles metabolize for all cohorts in a community.

        This method generates a total amount of metabolic waste per cohort and passes
        that waste to handler methods for distinguishing between nitrogenous and
        carbonaceous wastes as they need depositing in different pools. This will not
        be fully implemented until the stoichiometric rework.

        Respiration wastes are totaled because they are CO2 and not tracked spatially.
        Excretion wastes are handled cohort by cohort because they will need to be
        spatially explicit with multi-grid occupancy.

        Args:
            air_temperature_data: The full air temperature data (as a DataArray) for
                all communities.
            dt: Number of days over which the metabolic costs should be calculated.

        """
        for cell_id, community in self.communities.items():
            # Check for empty community and skip processing if empty
            if not community:
                continue

            total_carbonaceous_waste = 0.0

            # Extract the temperature for this specific community (cell_id)
            surface_temperature = self.data["air_temperature"][
                self.layer_structure.index_surface_scalar
            ].to_numpy()

            grid_temperature = surface_temperature[cell_id]

            for cohort in community:
                # Calculate metabolic waste based on cohort properties
                metabolic_waste_mass = cohort.metabolize(grid_temperature, dt)

                # Carbonaceous waste from respiration
                total_carbonaceous_waste += cohort.respire(metabolic_waste_mass)

                # Excretion of waste into the excrement pool
                cohort.excrete(metabolic_waste_mass, self.excrement_pools[cell_id])

            # Update the total_animal_respiration for the specific cell_id
            self.data["total_animal_respiration"].loc[{"cell_id": cell_id}] += (
                total_carbonaceous_waste
            )

    def increase_age_community(self, dt: timedelta64) -> None:
        """This handles age for all cohorts in a community.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        for cohort in self.active_cohorts.values():
            cohort.increase_age(dt)

    def handle_ontogeny(self) -> None:
        """Update largest body mass achieved for immature cohorts.

        This is used to support ontogeny-aware starvation calculations.
        """

        for cohort in self.active_cohorts.values():
            if not cohort.is_mature:
                cohort.update_largest_mass()

    def inflict_non_predation_mortality_community(self, dt: timedelta64) -> None:
        """This handles natural mortality for all cohorts in a community.

        This includes background mortality, starvation, and, for mature cohorts,
        senescence.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        number_of_days = float(dt / timedelta64(1, "D"))
        for cohort in list(self.active_cohorts.values()):
            cohort.inflict_non_predation_mortality(
                number_of_days, cohort.get_carcass_pools(self.carcass_pools)
            )
            if cohort.individuals <= 0:
                cohort.is_alive = False
                self.remove_dead_cohort(cohort)

    def metamorphose(self, larval_cohort: AnimalCohort) -> None:
        """This transforms a larval status cohort into an adult status cohort.

        This method takes an indirect developing cohort in its larval form,
        inflicts a mortality rate, and creates an adult cohort of the correct type.

        TODO: Build in a relationship between larval_cohort mass and adult cohort mass.
        TODO: Is adult_mass the correct mass threshold?
        TODO: If the time step drops below a month, this needs an intermediary stage.

        Args:
            larval_cohort: The cohort in its larval stage to be transformed.
        """

        # inflict a mortality
        number_dead = ceil(
            larval_cohort.individuals * larval_cohort.constants.metamorph_mortality
        )
        larval_cohort.die_individual(
            number_dead, larval_cohort.get_carcass_pools(self.carcass_pools)
        )
        # collect the adult functional group
        adult_functional_group = get_functional_group_by_name(
            self.functional_groups,
            larval_cohort.functional_group.offspring_functional_group,
        )

        # create the new adult cohort and update its presence in the simulation
        self.create_new_cohort(
            adult_functional_group,
            adult_functional_group.birth_mass,
            0.0,
            larval_cohort.individuals,
            larval_cohort.centroid_key,
        )

        # remove the larval cohort
        larval_cohort.is_alive = False
        self.remove_dead_cohort(larval_cohort)

    def metamorphose_community(self) -> None:
        """Handle metamorphosis for all applicable cohorts in the community."""

        # Iterate over a static list of cohort values
        for cohort in list(self.active_cohorts.values()):
            if (
                cohort.functional_group.development_type == DevelopmentType.INDIRECT
                and (cohort.mass_current >= cohort.functional_group.adult_mass)
            ):
                self.metamorphose(cohort)

    def update_migrated_and_aquatic(self, dt: timedelta64) -> None:
        """Handles updating timing on frozen migrated and aquatic cohorts.

        Args:
            dt: The amount of time passed in the update (days).

        """

        dt_float = float(dt / timedelta64(1, "D"))

        for cohort in list(self.migrated_cohorts.values()):
            cohort.remaining_time_away -= dt_float
            if cohort.remaining_time_away <= 0:
                self.reintegrate_cohort(cohort, source="migrated")

        for cohort in list(self.aquatic_cohorts.values()):
            cohort.remaining_time_away -= dt_float
            if cohort.remaining_time_away <= 0:
                self.reintegrate_cohort(cohort, source="aquatic")

    def reintegrate_cohort(self, cohort: AnimalCohort, source: str) -> None:
        """Handles integration of cohorts from migrated/aquatic to active status.

        Args:
            cohort: The animal cohort changing to active status.
            source: Whether the cohort was migrated or aquatic.

        """
        if source == "migrated":
            mortality_rate = cohort.constants.migration_mortality
            self.migrated_cohorts.pop(cohort.id)
        elif source == "aquatic":
            mortality_rate = cohort.constants.aquatic_mortality
            self.aquatic_cohorts.pop(cohort.id)

        deaths = int(cohort.individuals * mortality_rate)
        cohort.individuals -= deaths

        if cohort.individuals > 0:
            cohort.location_status = "active"
            self.active_cohorts[cohort.id] = cohort

            # Reintroduce cohort to its communities
            self.update_community_occupancy(cohort, cohort.centroid_key)

        else:
            cohort.is_alive = False

    def migrate_external(self, cohort: AnimalCohort) -> None:
        """Handles the initiation of external migration events.

        Args:
            cohort: The migrating cohort.
        """
        # Remove cohort from community occupancy
        self.abandon_communities(cohort)

        # Move cohort to migration pool
        cohort.location_status = "migrated"
        cohort.remaining_time_away = cohort.constants.migration_residence_time
        self.migrated_cohorts[cohort.id] = cohort
        self.active_cohorts.pop(cohort.id)

    def migrate_external_community(self) -> None:
        """Cycles through all active cohorts and checks for external migration.

        Only calls `trigger_external_migration` for cohorts that are seasonal migrators.
        """
        for cohort in list(self.active_cohorts.values()):
            if (
                cohort.functional_group.migration_type == "seasonal"
                and cohort.is_migration_season()
            ):
                self.migrate_external(cohort)

    def reintegrate_community(self) -> None:
        """Cycles through all migrated and aquatic cohorts, checking for reintegration.

        Only calls `reintegrate_cohort` when `remaining_time_away` is 0 or less.
        """
        for cohort in list(self.migrated_cohorts.values()):
            if cohort.remaining_time_away <= 0:
                self.reintegrate_cohort(cohort, source="migrated")

        for cohort in list(self.aquatic_cohorts.values()):
            if cohort.remaining_time_away <= 0:
                self.reintegrate_cohort(cohort, source="aquatic")

    def assign_prey_groups(self, cohort: AnimalCohort) -> None:
        """Assign the available prey groups to a given animal cohort.

        This method filters the functional groups present in the model based on the
        diet of the cohort and stores the resulting prey/resource groups on the cohort.
        It should be called whenever a cohort is created or changes functional group.

        Args:
            cohort: The AnimalCohort instance for which to assign prey groups.
        """

        cohort.prey_groups = prey_group_selection(
            cohort.functional_group.diet,
            cohort.functional_group.adult_mass,
            cohort.functional_group.prey_scaling,
            self.functional_groups,
        )

    def create_new_cohort(
        self,
        functional_group: FunctionalGroup,
        mass: float,
        age: float,
        individuals: int,
        centroid_key: int,
        is_birth: bool = False,
    ) -> AnimalCohort:
        """Create a new AnimalCohort and register it in the model.

        Args:
            functional_group: Functional group defining cohort traits.
            mass: Body mass (kg) at creation.
            age: Age (days) at creation.
            individuals: Number of individuals in the cohort.
            centroid_key: Grid cell for territorial location.
            is_birth: Whether the cohort is a new offspring (affects aquatic routing).

        Returns:
            A registered AnimalCohort.
        """

        cohort = AnimalCohort(
            functional_group=functional_group,
            mass=mass,
            age=age,
            individuals=individuals,
            centroid_key=centroid_key,
            grid=self.data.grid,
            constants=self.model_constants,
            core_constants=self.core_constants,
        )

        self.assign_prey_groups(cohort)

        # Register based on birth & aquatic logic
        if (
            is_birth
            and functional_group.reproductive_environment
            is ReproductiveEnvironment.AQUATIC
        ):
            cohort.remaining_time_away = cohort.constants.aquatic_residence_time
            self.aquatic_cohorts[cohort.id] = cohort
        else:
            self.active_cohorts[cohort.id] = cohort
            self.update_community_occupancy(cohort, centroid_key)

        return cohort
