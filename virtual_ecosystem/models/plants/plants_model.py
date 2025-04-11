"""The :mod:`~virtual_ecosystem.models.plants.plants_model` module creates
:class:`~virtual_ecosystem.models.plants.plants_model.PlantsModel` class as a child of
the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
"""  # noqa: D205

from __future__ import annotations

from typing import Any

import numpy as np
import xarray as xr
from numpy.typing import NDArray
from pyrealm.constants import CoreConst, PModelConst
from pyrealm.demography.canopy import Canopy
from pyrealm.demography.flora import Flora
from pyrealm.demography.tmodel import StemAllocation, StemAllometry
from pyrealm.pmodel import PModel, PModelEnvironment

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.canopy import (
    calculate_canopies,
    initialise_canopy_layers,
)
from virtual_ecosystem.models.plants.communities import PlantCommunities
from virtual_ecosystem.models.plants.constants import PlantsConsts
from virtual_ecosystem.models.plants.functional_types import get_flora_from_config


class PlantsModel(
    BaseModel,
    model_name="plants",
    model_update_bounds=("1 day", "1 year"),
    vars_required_for_init=(
        "plant_cohorts_cell_id",
        "plant_cohorts_pft",
        "plant_cohorts_n",
        "plant_cohorts_dbh",
        "downward_shortwave_radiation",
    ),
    vars_populated_by_init=(
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_fapar",
        "layer_leaf_mass",  # NOTE - placeholder resource for herbivory
        "shortwave_absorption",
    ),
    vars_required_for_update=(
        "plant_cohorts_cell_id",
        "plant_cohorts_pft",
        "plant_cohorts_n",
        "plant_cohorts_dbh",
        "downward_shortwave_radiation",
        "air_temperature",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
        "dissolved_nitrate",
        "dissolved_ammonium",
        "dissolved_phosphorus",
        "ecto_supply_limit_n",
        "ecto_supply_limit_p",
        "arbuscular_supply_limit_n",
        "arbuscular_supply_limit_p",
    ),
    vars_updated=(
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_fapar",
        "layer_leaf_mass",  # NOTE - placeholder resource for herbivory
        "shortwave_absorption",
        "evapotranspiration",
        "deadwood_production",
        "leaf_turnover",
        "plant_reproductive_tissue_turnover",
        "root_turnover",
        "stem_lignin",
        "senesced_leaf_lignin",
        "plant_reproductive_tissue_lignin",
        "root_lignin",
        "deadwood_c_n_ratio",
        "leaf_turnover_c_n_ratio",
        "plant_reproductive_tissue_turnover_c_n_ratio",
        "root_turnover_c_n_ratio",
        "deadwood_c_p_ratio",
        "leaf_turnover_c_p_ratio",
        "plant_reproductive_tissue_turnover_c_p_ratio",
        "root_turnover_c_p_ratio",
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "plant_n_uptake_arbuscular",
        "plant_n_uptake_ecto",
        "plant_p_uptake_arbuscular",
        "plant_p_uptake_ecto",
    ),
    vars_populated_by_first_update=(
        "evapotranspiration",
        "deadwood_production",
        "leaf_turnover",
        "plant_reproductive_tissue_turnover",
        "root_turnover",
        "stem_lignin",
        "senesced_leaf_lignin",
        "plant_reproductive_tissue_lignin",
        "root_lignin",
        "deadwood_c_n_ratio",
        "leaf_turnover_c_n_ratio",
        "plant_reproductive_tissue_turnover_c_n_ratio",
        "root_turnover_c_n_ratio",
        "deadwood_c_p_ratio",
        "leaf_turnover_c_p_ratio",
        "plant_reproductive_tissue_turnover_c_p_ratio",
        "root_turnover_c_p_ratio",
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "plant_n_uptake_arbuscular",
        "plant_n_uptake_ecto",
        "plant_p_uptake_arbuscular",
        "plant_p_uptake_ecto",
    ),
):
    """Representation of plants in the Virtual Ecosystem.

    The plants model is initialised from data describing inventories for each grid cell
    in the simulation of size-structured cohorts. Each cohort belongs to a plant
    functional type, from a set of functional types defined in the model configuration.
    The inventory data is provided within the data configuration of the simulation and
    requires the following variables:

    * ``plant_cohorts_cell_id``: The grid cell id containing the cohort
    * ``plant_cohorts_pft``: The plant functional type of the cohort
    * ``plant_cohorts_n``: The number of individuals in the cohort
    * ``plant_cohorts_dbh``: The diameter at breast height of the individuals in metres.

    These data are used to setup the plant communities within each grid cell, using the
    :class:`~virtual_ecosystem.models.plants.communities.PlantCommunities` class to
    maintain a lookup dictionary of communities by grid cell.

    The model setup then initialises the canopy layer data within the
    :class:`virtual_ecosystem.core.data.Data` instance for the simulation and populates
    these data layers with the calculated community canopy structure for each grid cell.
    The community canopy representation is calculated using the perfect plasticticy
    approximation, implemented in the `pyrealm` package. The canopy variables populated
    at this stage are:

    * the canopy layer closure heights (``layer_heights``),
    * the canopy layer leaf area indices (``leaf_area_index``),
    * the fraction of absorbed photosynthetically active radation in each canopy layer
        (``layer_fapar``), and
    * the whole canopy leaf mass within the layers (``layer_leaf_mass``)

    The model update process filters the photosynthetic photon flux density at the top
    of canopy through the community canopy representation. This allows the gross primary
    productivity (GPP) within canopy layers to be estimated, giving the total expected
    GPP for individual stems within cohorts. The predicted GPP is then allocated between
    plant respiration, turnover and growth and the resulting allocation to growth is
    used to predict the change in stem diameter expected during the update interval.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        flora: A Flora instance of the plant functional types to be used in the model.
        model_constants: Set of constants for the plants model.
    """

    # TODO - think about a shared "plant cohort" core axis that defines the cohort
    #        initialisation  data, but the issue here is that the length of this is
    #        variable.

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        static: bool = False,
        **kwargs: Any,
    ):
        """Plants init function.

        The init function is used only to define class attributes. Any logic should be
        handeled in :fun:`~virtual_ecosystem.plants.plants_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.flora: Flora
        """A flora containing the plant functional types used in the plants model."""
        self.model_constant: PlantsConsts
        """Set of constants for the plants model"""
        self.communities: PlantCommunities
        """An instance of PlantCommunities providing dictionary access keyed by cell id
        to PlantCommunity instances for each cell."""
        self._canopy_layer_indices: NDArray[np.bool_]
        """The indices of the canopy layers within wider vertical profile. This is 
        a shorter reference to self.layer_structure.index_canopy."""
        self.canopies: dict[int, Canopy]
        """A dictionary giving the canopy structure of each grid cell."""
        self.filled_canopy_mask: NDArray[np.bool_]
        """A boolean array showing which layers contain canopy by cell."""
        self.per_stem_gpp: dict[int, NDArray[np.float32]]
        """A dictionary keyed by cell id giving an array of per stem GPP values for each
        cohort in the community."""
        self.per_stem_transpiration: dict[int, NDArray[np.float32]]
        """A dictionary keyed by cell id giving an array of per stem transpiration
        values for each cohort in the cell community"""
        self.pmodel_consts: PModelConst
        """PModel constants used by pyrealm."""
        self.pmodel_core_consts: CoreConst
        """Core constants used by pyrealm."""
        self.per_update_interval_stem_mortality_probability: np.float64
        """The rate of stem mortality per update interval."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> PlantsModel:
        """Factory function to initialise a plants model from configuration.

        This function returns a PlantsModel instance based on the provided configuration
        and data, raising an exception if the configuration is invalid.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(config, "plants", "PlantsConsts")
        static = config["plants"]["static"]

        # Generate the flora
        flora = get_flora_from_config(config=config)

        # Try and create the instance - safeguard against exceptions from __init__
        try:
            inst = cls(
                data=data,
                core_components=core_components,
                static=static,
                flora=flora,
                model_constants=model_constants,
            )
        except Exception as excep:
            LOGGER.critical(
                f"Error creating plants model from configuration: {excep!s}"
            )
            raise excep

        LOGGER.info("Plants model instance generated from configuration.")
        return inst

    def _setup(
        self,
        flora: Flora,
        model_constants: PlantsConsts = PlantsConsts(),
        **kwargs: Any,
    ) -> None:
        """Setup implementation for the Plants Model.

        Args:
            flora: A flora containing the plant functional types used in the plants
                model.
            model_constants: Set of constants for the plants model.
            **kwargs: Further arguments to the setup method.
        """

        # Set the instance attributes from the __init__ arguments
        self.flora = flora
        self.model_constants = model_constants
        self.communities = PlantCommunities(
            data=self.data, flora=self.flora, grid=self.grid
        )
        # This is widely used internally so store it as an attribute.
        self._canopy_layer_indices = self.layer_structure.index_canopy

        # Calculate PPFD from DSR
        self.data["photosynthetic_photon_flux_density"] = (
            self.data["downward_shortwave_radiation"] / model_constants.ppfd_to_dsr
        )

        # Initialise the canopy layer arrays.
        # TODO - this initialisation step may move somewhere else at some point see #442
        self.data.add_from_dict(
            initialise_canopy_layers(
                data=self.data,
                layer_structure=self.layer_structure,
            )
        )

        # Calculate the community canopy representations.
        self.canopies = calculate_canopies(
            communities=self.communities,
            max_canopy_layers=self.layer_structure.n_canopy_layers,
        )

        # TODO - #697 these need to be configurable
        self.pmodel_consts = PModelConst()
        self.pmodel_core_consts = CoreConst()

        # Create and populate the canopy data layers and set the absorption from the
        # first time index
        self.update_canopy_layers()
        self.set_shortwave_absorption(time_index=0)

        # Initialise other attributes
        self.per_stem_gpp = {}
        self.per_stem_transpiration = {}
        self.filled_canopy_mask = np.full(
            (self.layer_structure.n_layers, self.grid.n_cells), False
        )

        # Calculate the per update interval stem mortality rate
        self.per_update_interval_stem_mortality_probability = 1 - (
            1 - model_constants.per_stem_annual_mortality_probability
        ) ** (1 / self.model_timing.updates_per_year)

    def spinup(self) -> None:
        """Placeholder function to spin up the plants model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Update the plants model.

        This method first updates the canopy layers, so that growth in any previous
        update is reflected in the canopy structure. It then estimates the absorbed
        irradiance through the canopy and calculates the per cohort gross primary
        productivity, given the position in the canopy and canopy area of each
        individual in the cohort. This then increments the diameter of breast height
        within the cohort.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # Update the canopy layers
        self.update_canopy_layers()
        self.set_shortwave_absorption(time_index=time_index)

        # Estimate the GPP and growth with the updated this update
        self.estimate_gpp(time_index=time_index)
        self.allocate_gpp()

        # Calculate the turnover of each plant biomass pool
        self.calculate_turnover()

        # Calculate uptake from each inorganic soil nutrient pool
        self.calculate_nutrient_uptake()

        # Calculate the rate at which plants take nutrients from mycorrhizal fungi
        self.calculate_mycorrhizal_uptakes()

        # Apply mortality to plant cohorts
        self.apply_mortality()

    def cleanup(self) -> None:
        """Placeholder function for plants model cleanup."""

    def update_canopy_layers(self) -> None:
        """Update the canopy structure for the plant communities.

        This method updates the following canopy layer variables in the data object from
        the current state of the canopies attribute:

        * the layer closure heights (``layer_heights``),
        * the layer leaf area indices (``leaf_area_index``),
        * the fraction of absorbed photosynthetically active radation in each layer
          (``layer_fapar``), and
        * the whole canopy leaf mass within the layers (``layer_leaf_mass``), and
        * the proportion of shortwave radiation absorbed, including both by leaves in
          canopy layers and by light reaching the topsoil  (``shortwave_absorption``).
        """

        canopy_array_shape = (self.layer_structure.n_canopy_layers, self.grid.n_cells)
        heights = np.full(canopy_array_shape, fill_value=np.nan)
        fapar = np.full(canopy_array_shape, fill_value=np.nan)
        lai = np.full(canopy_array_shape, fill_value=np.nan)
        mass = np.full(canopy_array_shape, fill_value=np.nan)

        for cell_id, canopy, community in zip(
            self.canopies, self.canopies.values(), self.communities.values()
        ):
            # Get the indices of the array to be filled in
            fill_idx = (slice(0, canopy.heights.size), (cell_id,))

            # Insert canopy layer heights
            # TODO - #695 At present, pyrealm returns a column array which _I think_
            #        always has zero as the last entry. We don't want that value, so it
            #        is being clipped out here but keep an eye on this definition and
            #        update if pyrealm changes. In the meantime, keep this guard check
            #        to raise if the issue arises.

            if canopy.heights[-1, :].item() > 0:
                raise ValueError("Last canopy.height is non-zero")

            heights[fill_idx] = np.concatenate(
                [[[canopy.max_stem_height]], canopy.heights[0:-1, :]]
            )

            # Insert canopy fapar:
            # TODO - #695 currently 1D, not 2D - consistency in pyrealm? keepdims?
            fapar[fill_idx] = canopy.community_data.fapar.reshape((-1, 1))

            # Partition the total stem foliage masses across cohorts vertically
            # following the leaf area within each layer.
            # TODO - need to expose the per cohort data to allow selective herbivory. Do
            #        we need the total leaf mass per layer for anything?
            leaf_mass_per_cohort_per_layer = (
                community.stem_allometry.foliage_mass
                * community.cohorts.n_individuals
                * (canopy.cohort_data.lai / canopy.cohort_data.lai.sum(axis=0))
            )
            mass[fill_idx] = leaf_mass_per_cohort_per_layer.sum(axis=1, keepdims=True)

            # LAI - add up LAI across cohorts within layers
            lai[fill_idx] = canopy.cohort_data.lai.sum(axis=1, keepdims=True)

        # Insert the canopy layers into the data objects
        self.data["layer_heights"][self._canopy_layer_indices, :] = heights
        self.data["leaf_area_index"][self._canopy_layer_indices, :] = lai
        self.data["layer_fapar"][self._canopy_layer_indices, :] = fapar
        self.data["layer_leaf_mass"][self._canopy_layer_indices, :] = mass

        # Add the above canopy reference height
        self.data["layer_heights"][self.layer_structure.index_above, :] = (
            heights[0, :] + self.layer_structure.above_canopy_height_offset
        )

        # Update the filled canopy layers
        self.layer_structure.set_filled_canopy(canopy_heights=heights)

        # Update the internal canopy layer mask
        self.filled_canopy_mask = np.logical_not(np.isnan(self.data["layer_leaf_mass"]))

        LOGGER.info(
            f"Updated canopy data on {self.layer_structure.index_filled_canopy.sum()}"
        )

    def set_shortwave_absorption(self, time_index: int) -> None:
        """Set the shortwave radiation absorption across the vertical layers.

        This method takes the shortwave radiation at the top of the canopy for a
        particular time index and uses the ``layer_fapar`` data calculated by the canopy
        model to estimate the amount of radiation absorbed by each canopy layer and the
        remaining radiation absorbed by the top soil layer.

        TODO:
          - With the full canopy model, this could be partitioned into sunspots
            and shade.
          - At the moment, we're only looking at PPFD and need to switch to SWDown
            `#721 <https://github.com/ImperialCollegeLondon/virtual_ecosystem/issues/721>`_
        """  # noqa: D405 temporary section

        # Extract a PPFD time slice
        canopy_top_ppfd = (
            self.data["photosynthetic_photon_flux_density"]
            .isel(time_index=time_index)
            .to_numpy()
        )

        # Calculate the fate of PPFD through the layers
        absorbed_irradiance = self.data["layer_fapar"] * canopy_top_ppfd
        # Add the remaining irradiance at the surface layer level
        absorbed_irradiance[self.layer_structure.index_topsoil] = (
            canopy_top_ppfd - np.nansum(absorbed_irradiance, axis=0)
        )

        self.data["shortwave_absorption"] = absorbed_irradiance

    def estimate_gpp(self, time_index: int) -> None:
        """Estimate the gross primary productivity within plant cohorts.

        This method uses the P Model to estimate the light use efficiency of leaves in
        gC mol-1, given the environment (temperate, atmospheric pressure, vapour
        pressure deficit and atmospheric CO2 concentration) within each canopy layer.
        This is multiplied by the absorbed irradiance within each canopy layer to
        predict the gross primary productivity (GPP, µg C m-2 s-1) for each canopy
        layer.

        The GPP for each cohort is then estimated by mutiplying the cohort canopy area
        within each layer by GPP and the time elapsed in seconds since the last update.

        .. TODO:

            * This function populates evapotranspiration but the calculation is
              currently only estimating _transpiration_
              `#704 <https://github.com/ImperialCollegeLondon/virtual_ecosystem/issues/704>`_
            * Conversion of transpiration from `µmol m-2` to `mm m-2` currently ignores
              density changes with conditions:
              `#723 <https://github.com/ImperialCollegeLondon/virtual_ecosystem/issues/723>`_

        Args:
            time_index: The index along the time axis of the forcing data giving the
                time step to be used to estimate GPP.

        Raises:
            ValueError: if any of the P Model forcing variables are not defined.


        """

        # Estimate the light use efficiency of leaves within each canopy layer within
        # each grid cell. The LUE is set purely by the environmental conditions, which
        # are shared across cohorts so we can calculate all layers in all cells.
        pmodel_env = PModelEnvironment(
            tc=self.data["air_temperature"].to_numpy(),
            vpd=self.data["vapour_pressure_deficit"].to_numpy(),
            patm=self.data["atmospheric_pressure"].to_numpy(),
            co2=self.data["atmospheric_co2"].to_numpy(),
            core_const=self.pmodel_core_consts,
            pmodel_const=self.pmodel_consts,
        )
        pmodel = PModel(pmodel_env)

        # Get the canopy top PPFD per grid cell for this time index
        canopy_top_ppfd = (
            self.data["photosynthetic_photon_flux_density"]
            .isel(time_index=time_index)
            .to_numpy()
        )

        # Get a floating point representation of the numner of seconds since last update
        # TODO - move this attribute to model_timing.
        n_seconds = self.model_timing.update_interval / np.timedelta64(1, "s")

        # Initialise transpiration array to collect per grid cell values
        # NOTE - #704, this is _not_ evapotranspiration, but we'll pretend it is for
        #        the moment.
        transpiration = self.layer_structure.from_template("evapotranspiration")

        # Now calculate the gross primary productivity and transpiration across cohorts
        # and canopy layers over the time period.
        # NOTE - Because the number of cohorts differ between grid cells, this is
        #        calculation is done within a loop over grid cells, but it is possible
        #        that this could be unwrapped into a single calculation, which might be
        #        much faster.

        for cell_id in self.canopies.keys():
            # Get the canopy and community for the cell
            canopy = self.canopies[cell_id]
            community = self.communities[cell_id]

            # Generate subsetting to match the layer structure to the cohort canopy
            # layers, whose dimensions vary between grid cells
            active_layers = np.where(self.filled_canopy_mask[:, cell_id])[0]

            # GPP is estimated as:
            #    LUE * per stem per layer fAPAR * the canopy top PPFD.
            # Dimensions:
            #    (n_active_layers, 1) * (n_active_layers, n_cohorts) * scalar
            #    = (n_active_layers, n_cohorts)
            # Units:
            #    gC mol-1  * µmol m-2 s-1 * (-) = µg m-2 s-1
            per_stem_gpp_rate = (
                pmodel.lue[active_layers, :][:, [cell_id]]
                * canopy.cohort_data.stem_fapar
                * canopy_top_ppfd[cell_id]
            )

            # The transpiration associated with that GPP is then:
            #    (GPP / (Mc * 1e6)) * iwue
            # Dimensions:
            #    ((n_layer, n_cohorts) / scalar) * (n_layer, 1)
            # Units:
            #    ((µgC m-2 s-1) / (µg mol-1)) * µmol mol -1 = µmol m2 s-1
            per_stem_transpiration_rate = (
                per_stem_gpp_rate / (self.pmodel_core_consts.k_CtoK * 1e6)
            ) * pmodel.iwue[active_layers, :][:, [cell_id]]

            # Now scale up and aggregate those values

            # Per stem GPP since last update: sum GPP *  whole stem leaf area
            # and scale by elapsed time in seconds
            self.per_stem_gpp[cell_id] = (
                per_stem_gpp_rate * canopy.cohort_data.stem_leaf_area * n_seconds
            ).sum(axis=0)

            # Calculate total stem transpiration in µmol per stem and total grid cell
            # transpiration in mm m-2 since last update
            self.per_stem_transpiration[cell_id] = (
                per_stem_transpiration_rate
                * canopy.cohort_data.stem_leaf_area
                * n_seconds
            ).sum(axis=0)

            # Calculate the total transpiration per layer in mm m2 in mm, converted from
            # an initial value is in µmol m2 s1.abs
            transpiration[active_layers, cell_id] = (
                community.cohorts.n_individuals
                * per_stem_transpiration_rate
                * n_seconds
                * 1.8e-8
            ).sum(axis=1)

        # Pass values to data object
        #
        # - #704, this is _not_ evapotranspiration, but we'll pretend it is for
        #        the moment.
        #
        self.data["evapotranspiration"] = transpiration

    def allocate_gpp(self) -> None:
        """Calculate the allocation of GPP to growth and respiration.

        This method uses the T Model to estimate the allocation of plant gross
        primary productivity to respiration, growth, maintenance and turnover costs.
        The method then simulates growth by increasing dbh and calculates leaf and root
        turnover values.
        """

        # Reset turnover to 0 as turnover from previous steps should have been allocated
        self.data["leaf_turnover"] = xr.full_like(self.data["elevation"], 0)
        self.data["root_turnover"] = xr.full_like(self.data["elevation"], 0)

        # Loop over each grid cell
        for cell_id in self.communities.keys():
            community = self.communities[cell_id]
            cohorts = community.cohorts

            # Calculate the allocation of GPP
            cohort_allocation = StemAllocation(
                stem_traits=community.stem_traits,
                stem_allometry=community.stem_allometry,
                at_potential_gpp=self.per_stem_gpp[cell_id],
            )

            # Grow the plants by increasing cohort dbh
            # TODO: dimension mismatch (1d vs 2d array) - check in pyrealm
            cohorts.dbh_values = cohorts.dbh_values + cohort_allocation.delta_dbh
            # TODO: move leaf/root turnover calculation to pyrealm & call here
            leaf_turnover = (
                community.stem_allometry.foliage_mass / community.stem_traits.tau_f
            )
            # Calculate total turnover from all cohorts in a grid cell
            self.data["leaf_turnover"][cell_id] = np.sum(leaf_turnover)
            self.data["root_turnover"][cell_id] = np.sum(
                cohort_allocation.turnover - leaf_turnover
            )
            # Update community allometry with new dbh values
            community.stem_allometry = StemAllometry(
                stem_traits=community.stem_traits, at_dbh=cohorts.dbh_values
            )

    def apply_mortality(self) -> None:
        """Apply mortality to plant cohorts.

        This function applies the basic annual mortality rate to plant cohorts. The
        mortality rate is currently a constant value for all cohorts. The function
        calculates the number of individuals that have died in each cohort and updates
        the cohort data accordingly. The function then updates deadwood production.

        """

        self.data["deadwood_production"] = xr.full_like(self.data["elevation"], 0)

        # Loop over each grid cell
        for cell_id in self.communities.keys():
            community = self.communities[cell_id]
            cohorts = community.cohorts

            # Calculate the number of individuals that have died in each cohort
            mortality = np.random.binomial(
                cohorts.n_individuals,
                self.per_update_interval_stem_mortality_probability,
            )

            # Decrease size of cohorts based on mortality
            cohorts.n_individuals = cohorts.n_individuals - mortality

            # Update deadwood production
            self.data["deadwood_production"][cell_id] = np.sum(
                mortality * community.stem_allometry.stem_mass
            )

    def calculate_turnover(self) -> None:
        """Calculate turnover of each plant biomass pool.

        This function calculates the turnover rate for each plant biomass pool (wood,
        leaves, roots, and reproductive tissues). As well as this the lignin
        concentration, carbon nitrogen ratio and carbon phosphorus ratio of each
        turnover flow is calculated. It also returns the rate at which plants supply
        carbon to their nitrogen fixing symbionts in the soil and the rate at which they
        exude carbohydrates into the soil more generally.

        Warning:
            At present, this function literally just returns constant values for each of
            the variables it returns.
        """

        self.data["plant_reproductive_tissue_turnover"] = xr.full_like(
            self.data["elevation"], 0.003
        )

        # Lignin concentrations
        self.data["stem_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.stem_lignin
        )
        self.data["senesced_leaf_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.senesced_leaf_lignin
        )
        self.data["leaf_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.leaf_lignin
        )
        self.data["plant_reproductive_tissue_lignin"] = xr.full_like(
            self.data["elevation"],
            self.model_constants.plant_reproductive_tissue_lignin,
        )
        self.data["root_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.root_lignin
        )

        # C:N and C:P ratios
        self.data["deadwood_c_n_ratio"] = xr.full_like(
            self.data["elevation"], self.model_constants.deadwood_c_n_ratio
        )
        self.data["leaf_turnover_c_n_ratio"] = xr.full_like(
            self.data["elevation"], self.model_constants.leaf_turnover_c_n_ratio
        )
        self.data["plant_reproductive_tissue_turnover_c_n_ratio"] = xr.full_like(
            self.data["elevation"],
            self.model_constants.plant_reproductive_tissue_turnover_c_n_ratio,
        )
        self.data["root_turnover_c_n_ratio"] = xr.full_like(
            self.data["elevation"], self.model_constants.root_turnover_c_n_ratio
        )
        self.data["deadwood_c_p_ratio"] = xr.full_like(
            self.data["elevation"], self.model_constants.deadwood_c_p_ratio
        )
        self.data["leaf_turnover_c_p_ratio"] = xr.full_like(
            self.data["elevation"], self.model_constants.leaf_turnover_c_p_ratio
        )
        self.data["plant_reproductive_tissue_turnover_c_p_ratio"] = xr.full_like(
            self.data["elevation"],
            self.model_constants.plant_reproductive_tissue_turnover_c_p_ratio,
        )
        self.data["root_turnover_c_p_ratio"] = xr.full_like(
            self.data["elevation"], self.model_constants.root_turnover_c_p_ratio
        )
        self.data["plant_symbiote_carbon_supply"] = xr.full_like(
            self.data["elevation"], 0.01
        )
        self.data["root_carbohydrate_exudation"] = xr.full_like(
            self.data["elevation"], 0.025
        )

    def calculate_nutrient_uptake(self) -> None:
        """Calculate uptake of soil nutrients by the plant community.

        This function calculates the rate a which plants take up inorganic nutrients
        (ammonium, nitrate, and labile phosphorus) from the soil.

        Warning:
            At present, this function just calculates uptake based on an entirely made
            up function, and does not link to plant dynamics in any way.
        """

        # Assume plants can take 0.1% of the available nutrient per day
        self.data["plant_ammonium_uptake"] = self.data["dissolved_ammonium"] * 0.01
        self.data["plant_nitrate_uptake"] = self.data["dissolved_nitrate"] * 0.01
        self.data["plant_phosphorus_uptake"] = self.data["dissolved_phosphorus"] * 0.01

    def calculate_mycorrhizal_uptakes(self) -> None:
        """Calculate the rate at which plants take nutrients from mycorrhizal fungi.

        Warning:
            At present, this function just calculates uptake based on an entirely made
            up function, and does not link to plant dynamics in any way.
        """

        # TODO - This should use the limits in some way
        self.data["plant_n_uptake_arbuscular"] = xr.full_like(
            self.data["elevation"], 0.0
        )
        self.data["plant_n_uptake_ecto"] = xr.full_like(self.data["elevation"], 0.0)
        self.data["plant_p_uptake_arbuscular"] = xr.full_like(
            self.data["elevation"], 0.0
        )
        self.data["plant_p_uptake_ecto"] = xr.full_like(self.data["elevation"], 0.0)
