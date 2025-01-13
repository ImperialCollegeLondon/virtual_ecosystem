"""The :mod:`~virtual_ecosystem.models.animal.animal_model` module creates a
:class:`~virtual_ecosystem.models.animal.animal_model.AnimalModel` class as a
child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
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

import uuid
from math import ceil, sqrt
from random import choice, random
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
from virtual_ecosystem.models.animal.animal_traits import DevelopmentType, DietType
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.decay import (
    CarcassPool,
    ExcrementPool,
    HerbivoryWaste,
    LitterPool,
)
from virtual_ecosystem.models.animal.functional_group import (
    FunctionalGroup,
    get_functional_group_by_name,
)
from virtual_ecosystem.models.animal.plant_resources import PlantResources
from virtual_ecosystem.models.animal.protocols import Resource
from virtual_ecosystem.models.animal.scaling_functions import damuths_law


class AnimalModel(
    BaseModel,
    model_name="animal",
    model_update_bounds=("1 day", "1 month"),
    vars_required_for_init=(),
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

    communities: dict[int, list[AnimalCohort]]
    """Animal communities with grid cell IDs and lists of AnimalCohorts."""

    cohorts: dict[uuid.UUID, AnimalCohort]
    """A dictionary of all animal cohorts and their unique ids."""

    def _setup_grid_neighbours(self) -> None:
        """Set up grid neighbours for the model.

        Currently, this is redundant with the set_neighbours method of grid.
        This will become a more complex animal specific implementation to manage
        functional group specific adjacency.

        """
        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))

    def _initialize_communities(self, functional_groups: list[FunctionalGroup]) -> None:
        """Initialize the animal communities by creating and populating animal cohorts.

        Args:
            functional_groups: The list of functional groups that will populate the
            model.
        """
        # Initialize communities dictionary with cell IDs as keys and empty lists for
        # cohorts
        self.communities = {cell_id: list() for cell_id in self.data.grid.cell_id}

        # Iterate over each cell and functional group to create and populate cohorts
        for cell_id in self.data.grid.cell_id:
            for functional_group in functional_groups:
                # Calculate the number of individuals using Damuth's Law
                individuals = damuths_law(
                    functional_group.adult_mass, functional_group.damuths_law_terms
                )

                # Create a cohort of the functional group
                cohort = AnimalCohort(
                    functional_group=functional_group,
                    mass=functional_group.adult_mass,
                    age=0.0,
                    individuals=individuals,
                    centroid_key=cell_id,
                    grid=self.data.grid,
                    constants=self.model_constants,
                )
                self.cohorts[cohort.id] = cohort
                self.communities[cell_id].append(cohort)

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
        static = config["animal"]["static"]

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
            static=static,
            functional_groups=functional_groups,
            model_constants=model_constants,
        )

    def _setup(
        self,
        functional_groups: list[FunctionalGroup],
        model_constants: AnimalConsts = AnimalConsts(),
        **kwargs: Any,
    ) -> None:
        """Method to setup the animal model specific data variables.

        This method initializes the data variables required by the animal model.

        Args:
            functional_groups: The list of animal functional groups present in the
                simulation.
            model_constants: Set of constants for the animal model.
            **kwargs: Further arguments to the setup method.
        """
        days_as_float = self.model_timing.update_interval_quantity.to("days").magnitude
        self.update_interval_timedelta = timedelta64(int(days_as_float), "D")
        """Convert pint update_interval to timedelta64 once during initialization."""

        self._setup_grid_neighbours()
        """Determine grid square adjacency."""
        self.functional_groups = functional_groups
        """List of functional groups in the model."""
        self.model_constants = model_constants
        """Animal constants."""
        self.plant_resources: dict[int, list[Resource]] = {
            cell_id: [
                PlantResources(
                    data=self.data, cell_id=cell_id, constants=self.model_constants
                )
            ]
            for cell_id in self.data.grid.cell_id
        }
        """The plant resource pools in the model with associated grid cell ids."""
        # TODO - In future, need to take in data on average size of excrement and
        # carcasses pools and their stoichiometries for the initial scavengeable pool
        # parameterisations
        self.excrement_pools: dict[int, list[ExcrementPool]] = {
            cell_id: [
                ExcrementPool(
                    scavengeable_carbon=1e-3,
                    scavengeable_nitrogen=1e-4,
                    scavengeable_phosphorus=1e-6,
                    decomposed_carbon=0.0,
                    decomposed_nitrogen=0.0,
                    decomposed_phosphorus=0.0,
                )
            ]
            for cell_id in self.data.grid.cell_id
        }
        """The excrement pools in the model with associated grid cell ids."""
        self.carcass_pools: dict[int, list[CarcassPool]] = {
            cell_id: [
                CarcassPool(
                    scavengeable_carbon=1e-3,
                    scavengeable_nitrogen=1e-4,
                    scavengeable_phosphorus=1e-6,
                    decomposed_carbon=0.0,
                    decomposed_nitrogen=0.0,
                    decomposed_phosphorus=0.0,
                )
            ]
            for cell_id in self.data.grid.cell_id
        }
        """The carcass pools in the model with associated grid cell ids."""
        self.leaf_waste_pools: dict[int, HerbivoryWaste] = {
            cell_id: HerbivoryWaste(plant_matter_type="leaf")
            for cell_id in self.data.grid.cell_id
        }
        """A pool for leaves removed by herbivory but not actually consumed."""
        self.cohorts: dict[uuid.UUID, AnimalCohort] = {}
        """A dictionary of all animal cohorts and their unique ids."""
        self.communities: dict[int, list[AnimalCohort]] = {
            cell_id: list() for cell_id in self.data.grid.cell_id
        }

        self._initialize_communities(functional_groups)
        """Create the dictionary of animal communities and populate each community with
        animal cohorts."""

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

        TODO: update so that it just cycles through the community methods, each of those
        will cycle through all cohorts in the model

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # TODO: merge problems as community looping is not internal to comm methods
        # TODO: These pools are populated but nothing actually gets done with them at
        # the moment, this will have to change when scavenging gets introduced
        litter_pools = self.populate_litter_pools()

        self.forage_community()
        self.migrate_community()
        self.birth_community()
        self.metamorphose_community()
        self.metabolize_community(
            self.update_interval_timedelta,
        )
        self.inflict_non_predation_mortality_community(self.update_interval_timedelta)
        self.remove_dead_cohort_community()
        self.increase_age_community(self.update_interval_timedelta)

        # Now that communities have been updated information required to update the
        # soil and litter models can be extracted
        additions_to_soil = self.calculate_soil_additions()
        litter_consumption = self.calculate_total_litter_consumption(litter_pools)
        litter_additions = self.calculate_litter_additions_from_herbivory()

        # Update the data object with the changes to soil and litter pools
        self.data.add_from_dict(
            additions_to_soil | litter_consumption | litter_additions
        )  # TODO - TEST THIS!

        # Update population densities
        self.update_population_densities()

    def cleanup(self) -> None:
        """Placeholder function for animal model cleanup."""

    def populate_litter_pools(self) -> dict[str, LitterPool]:
        """Populate the litter pools that animals can consume from.

        Returns:
            dict[str, LitterPool]: A dictionary where keys represent the pool types and
            values are the corresponding `LitterPool` objects. The following pools are
            included:

            - "above_metabolic": Litter pool for above-ground metabolic organic matter
            - "above_structural": Litter pool for above-ground structural organic matter
            - "woody": Litter pool for woody biomass
            - "below_metabolic": Litter pool for below-ground metabolic organic matter
            - "below_structural": Litter pool for below-ground structural organic matter

        """

        return {
            "above_metabolic": LitterPool(
                pool_name="above_metabolic",
                data=self.data,
                cell_area=self.grid.cell_area,
            ),
            "above_structural": LitterPool(
                pool_name="above_structural",
                data=self.data,
                cell_area=self.grid.cell_area,
            ),
            "woody": LitterPool(
                pool_name="woody",
                data=self.data,
                cell_area=self.grid.cell_area,
            ),
            "below_metabolic": LitterPool(
                pool_name="below_metabolic",
                data=self.data,
                cell_area=self.grid.cell_area,
            ),
            "below_structural": LitterPool(
                pool_name="below_structural",
                data=self.data,
                cell_area=self.grid.cell_area,
            ),
        }

    def calculate_total_litter_consumption(
        self, litter_pools: dict[str, LitterPool]
    ) -> dict[str, DataArray]:
        """Calculate total animal consumption of each litter pool.

        TODO: rework for merge

        Args:
            litter_pools: The full set of animal accessible litter pools.

        Returns:
            The total consumption of litter from each pool [kg C m^-2]
        """

        # Find total animal consumption from each pool
        total_consumption = {
            pool_name: self.data[f"litter_pool_{pool_name}"]
            - (litter_pools[pool_name].mass_current / self.data.grid.cell_area)
            for pool_name in litter_pools.keys()
        }

        return {
            f"litter_consumption_{pool_name}": DataArray(
                array(total_consumption[pool_name]), dims="cell_id"
            )
            for pool_name in litter_pools.keys()
        }

    def calculate_litter_additions_from_herbivory(self) -> dict[str, DataArray]:
        """Calculate additions to litter due to herbivory mechanical inefficiencies.

        TODO - At present the only type of herbivory this works for is leaf herbivory,
        that should be changed once herbivory as a whole is fleshed out.
        TODO: rework for merge

        Returns:
            A dictionary containing details of the leaf litter addition due to herbivory
            this comprises of the mass added in carbon terms [kg C m^-2], ratio of
            carbon to nitrogen [unitless], ratio of carbon to phosphorus [unitless], and
            the proportion of input carbon that is lignin [unitless].
        """

        # Find the size of the leaf waste pool (in carbon terms)
        leaf_addition = [
            self.leaf_waste_pools[cell_id].mass_current / self.data.grid.cell_area
            for cell_id in self.data.grid.cell_id
        ]
        # Find the chemistry of the pools as well
        leaf_c_n = [
            self.leaf_waste_pools[cell_id].c_n_ratio
            for cell_id in self.data.grid.cell_id
        ]
        leaf_c_p = [
            self.leaf_waste_pools[cell_id].c_p_ratio
            for cell_id in self.data.grid.cell_id
        ]
        leaf_lignin = [
            self.leaf_waste_pools[cell_id].lignin_proportion
            for cell_id in self.data.grid.cell_id
        ]

        # Reset all of the herbivory waste pools to zero
        for waste in self.leaf_waste_pools.values():
            waste.mass_current = 0.0

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
            "decomposed_excrement_carbon": DataArray(
                array(decomposed_excrement["carbon"])
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
            "decomposed_excrement_nitrogen": DataArray(
                array(decomposed_excrement["nitrogen"])
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
            "decomposed_excrement_phosphorus": DataArray(
                array(decomposed_excrement["phosphorus"])
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
            "decomposed_carcasses_carbon": DataArray(
                array(decomposed_carcasses["carbon"])
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
            "decomposed_carcasses_nitrogen": DataArray(
                array(decomposed_carcasses["nitrogen"])
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
            "decomposed_carcasses_phosphorus": DataArray(
                array(decomposed_carcasses["phosphorus"])
                / self.model_timing.update_interval_quantity.to("days").magnitude,
                dims="cell_id",
            ),
        }

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
        for cohort in self.cohorts.values():
            is_starving = cohort.is_below_mass_threshold(
                self.model_constants.dispersal_mass_threshold
            )
            is_juvenile_and_migrate = (
                cohort.age == 0.0 and random() <= cohort.migrate_juvenile_probability()
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
        # Check if the cohort exists in self.cohorts
        if cohort.id in self.cohorts:
            # Iterate over all grid cell keys in the cohort's territory
            for cell_id in cohort.territory:
                if cell_id in self.communities and cohort in self.communities[cell_id]:
                    self.communities[cell_id].remove(cohort)

            # Remove the cohort from the model's cohorts dictionary
            del self.cohorts[cohort.id]
        else:
            raise KeyError(f"Cohort with ID {cohort.id} does not exist.")

    def remove_dead_cohort_community(self) -> None:
        """This handles remove_dead_cohort for all cohorts in a community."""
        # Collect cohorts to remove (to avoid modifying the dictionary during iteration)
        cohorts_to_remove = [
            cohort for cohort in self.cohorts.values() if cohort.individuals <= 0
        ]

        # Remove each cohort
        for cohort in cohorts_to_remove:
            cohort.is_alive = False
            self.remove_dead_cohort(cohort)

    def birth(self, parent_cohort: AnimalCohort) -> None:
        """Produce a new AnimalCohort through reproduction.

        A cohort can only reproduce if it has an excess of reproductive mass above a
        certain threshold. The offspring will be an identical cohort of adults
        with age 0 and mass=birth_mass. A new territory, likely smaller b/c allometry,
        is generated for the newborn cohort.

        The science here follows Madingley.

        TODO: Check whether Madingley discards excess reproductive mass.
        TODO: Rework birth mass for indirect developers.

        Args:
            parent_cohort: The AnimalCohort instance which is producing a new cohort.
        """
        # semelparous organisms use a portion of their non-reproductive mass to make
        # offspring and then they die
        non_reproductive_mass_loss = 0.0
        if parent_cohort.functional_group.reproductive_type == "semelparous":
            non_reproductive_mass_loss = (
                parent_cohort.mass_current
                * parent_cohort.constants.semelparity_mass_loss
            )
            parent_cohort.mass_current -= non_reproductive_mass_loss
            # kill the semelparous parent cohort
            parent_cohort.is_alive = False

        number_offspring = (
            int(
                (parent_cohort.reproductive_mass + non_reproductive_mass_loss)
                / parent_cohort.functional_group.birth_mass
            )
            * parent_cohort.individuals
        )

        # reduce reproductive mass by amount used to generate offspring
        parent_cohort.reproductive_mass = 0.0

        if number_offspring <= 0:
            print("No offspring created, exiting birth method.")
            return

        offspring_functional_group = get_functional_group_by_name(
            self.functional_groups,
            parent_cohort.functional_group.offspring_functional_group,
        )

        offspring_cohort = AnimalCohort(
            offspring_functional_group,
            parent_cohort.functional_group.birth_mass,
            0.0,
            number_offspring,
            parent_cohort.centroid_key,
            parent_cohort.grid,
            parent_cohort.constants,
        )

        # add a new cohort of the parental type to the community
        self.cohorts[offspring_cohort.id] = offspring_cohort

        # Debug: Print cohorts after adding offspring
        print(f"Total cohorts after adding offspring: {len(self.cohorts)}")

        # add the new cohort to the community lists it occupies
        self.update_community_occupancy(offspring_cohort, offspring_cohort.centroid_key)

        if parent_cohort.functional_group.reproductive_type == "semelparous":
            self.remove_dead_cohort(parent_cohort)

    def birth_community(self) -> None:
        """This handles birth for all cohorts in a community."""

        # reproduction occurs for cohorts with sufficient reproductive mass
        for cohort in self.cohorts.values():
            if (
                not cohort.is_below_mass_threshold(
                    self.model_constants.birth_mass_threshold
                )
                and cohort.functional_group.reproductive_type != "nonreproductive"
            ):
                self.birth(cohort)

    def forage_community(self) -> None:
        """This function organizes the foraging of animal cohorts.

        Herbivores will only forage plant resources, while carnivores will forage for
        prey (other animal cohorts).

        It loops over every animal cohort in the community and calls the
        forage_cohort function with a list of suitable trophic resources. This action
        initiates foraging for those resources, with mass transfer details handled
        internally by forage_cohort and its helper functions. Future expansions may
        include functions for handling scavenging and soil consumption behaviors.

        Cohorts with no remaining individuals post-foraging are marked for death.
        """

        for consumer_cohort in self.cohorts.values():
            # Check that the cohort has a valid territory defined
            if consumer_cohort.territory is None:
                raise ValueError("The cohort's territory hasn't been defined.")

            # Initialize empty resource lists
            plant_list = []
            prey_list = []
            excrement_list = consumer_cohort.get_excrement_pools(self.excrement_pools)
            """plant_waste_list = consumer_cohort.get_plant_waste_pools(
                self.leaf_waste_pools
            )"""

            # Check the diet of the cohort and get appropriate resources
            if consumer_cohort.functional_group.diet == DietType.HERBIVORE:
                plant_list = consumer_cohort.get_plant_resources(self.plant_resources)

            elif consumer_cohort.functional_group.diet == DietType.CARNIVORE:
                prey_list = consumer_cohort.get_prey(self.communities)

            # Initiate foraging for the consumer cohort with the available resources
            consumer_cohort.forage_cohort(
                plant_list=plant_list,
                animal_list=prey_list,
                excrement_pools=excrement_list,
                carcass_pools=self.carcass_pools,  # the full list of carcass pools
                herbivory_waste_pools=self.leaf_waste_pools,  # full list of leaf waste
            )

            # Temporary solution to remove dead cohorts
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
        for cohort in self.cohorts.values():
            cohort.increase_age(dt)

    def inflict_non_predation_mortality_community(self, dt: timedelta64) -> None:
        """This handles natural mortality for all cohorts in a community.

        This includes background mortality, starvation, and, for mature cohorts,
        senescence.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        number_of_days = float(dt / timedelta64(1, "D"))
        for cohort in list(self.cohorts.values()):
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
        # create the adult cohort
        adult_cohort = AnimalCohort(
            adult_functional_group,
            adult_functional_group.birth_mass,
            0.0,
            larval_cohort.individuals,
            larval_cohort.centroid_key,
            self.grid,
            self.model_constants,
        )

        # add a new cohort of the parental type to the community
        self.cohorts[adult_cohort.id] = adult_cohort

        # add the new cohort to the community lists it occupies
        self.update_community_occupancy(adult_cohort, adult_cohort.centroid_key)

        # remove the larval cohort
        larval_cohort.is_alive = False
        self.remove_dead_cohort(larval_cohort)

    def metamorphose_community(self) -> None:
        """Handle metamorphosis for all applicable cohorts in the community."""

        # Iterate over a static list of cohort values
        for cohort in list(self.cohorts.values()):
            if (
                cohort.functional_group.development_type == DevelopmentType.INDIRECT
                and (cohort.mass_current >= cohort.functional_group.adult_mass)
            ):
                self.metamorphose(cohort)
