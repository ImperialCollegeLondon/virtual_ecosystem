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
from pyrealm.core.water import convert_water_moles_to_mm
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
from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
from virtual_ecosystem.models.plants.functional_types import (
    ExtraTraitsPFT,
    get_flora_from_config,
)
from virtual_ecosystem.models.plants.stochiometry import (
    StemStochiometry,
)


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
        "subcanopy_vegetation_biomass",
        "subcanopy_seedbank_biomass",
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
        "subcanopy_vegetation_biomass",
        "subcanopy_seedbank_biomass",
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
        "transpiration",
        "deadwood_production",
        "leaf_turnover",
        "fallen_non_propagule_c_mass",
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
        "subcanopy_vegetation_biomass",
        "subcanopy_seedbank_biomass",
    ),
    vars_populated_by_first_update=(
        "transpiration",
        "deadwood_production",
        "leaf_turnover",
        "fallen_non_propagule_c_mass",
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
    * the fraction of absorbed photosynthetically active radiation in each canopy layer
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
        exporter: CommunityDataExporter,
        static: bool = False,
        **kwargs: Any,
    ):
        """Plants init function.

        The init function is used only to define class attributes. Any logic should be
        handled in :fun:`~virtual_ecosystem.plants.plants_model._setup`.
        """

        self.flora: Flora
        """A flora containing the plant functional types used in the plants model."""
        self.extra_pft_traits: ExtraTraitsPFT
        """The extra traits for each plant functional type, keyed by PFT name."""
        self.model_constant: PlantsConsts
        """Set of constants for the plants model"""
        self.communities: PlantCommunities
        """An instance of PlantCommunities providing dictionary access keyed by cell id
        to PlantCommunity instances for each cell."""
        self.stochiometries: dict[int, dict[str, StemStochiometry]]
        """A dictionary keyed by cell id giving the stochiometry of each community."""
        self.allocations: dict[int, StemAllocation]
        """A dictionary keyed by cell id giving the allocation of each community."""
        self._canopy_layer_indices: NDArray[np.bool_]
        """The indices of the canopy layers within wider vertical profile. This is 
        a shorter reference to self.layer_structure.index_canopy."""
        self.canopies: dict[int, Canopy]
        """A dictionary giving the canopy structure of each grid cell."""
        self.stem_allocations: dict[int, StemAllocation]
        """A dictionary giving the stem allocation of GPP for the community in each grid
       cell. The dictionary is only populated by the update method - before that the
       dictionary will be empty."""
        self.below_canopy_light_fraction: NDArray[np.floating]
        """The fraction of light transmitted through the canopy."""
        self.ground_incident_light_fraction: NDArray[np.floating]
        """The fraction of light reaching the ground through the canopy and subcanopy
        vegetation."""
        self.filled_canopy_mask: NDArray[np.bool_]
        """A boolean array showing which layers contain canopy by cell."""
        self.per_stem_gpp: dict[int, NDArray[np.floating]]
        """A dictionary keyed by cell id giving the GPP values over the course of a 
        model update for each stem within the cohorts in the community (µg C)."""
        self.per_stem_transpiration: dict[int, NDArray[np.floating]]
        """A dictionary keyed by cell id giving an array of per stem transpiration
        values in for each cohort in the cell community (mm H2O)"""
        self.pmodel: PModel
        """A P Model instance providing estimates of light use efficiency through the
        canopy and across cells."""
        self.pmodel_consts: PModelConst
        """PModel constants used by pyrealm."""
        self.pmodel_core_consts: CoreConst
        """Core constants used by pyrealm."""
        self.per_update_interval_stem_mortality_probability: np.float64
        """The rate of stem mortality per update interval."""

        # Define and populate model specific attributes
        self.exporter: CommunityDataExporter = exporter
        """A CommunityDataExporter instance providing configuration and methods for
        export of community data."""

        # Run the base model __init__
        super().__init__(data, core_components, static, **kwargs)

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
        flora, extra_traits = get_flora_from_config(config=config)

        # Create a CommunityDataExporter instance from config
        exporter = CommunityDataExporter.from_config(config=config)

        # Try and create the instance - safeguard against exceptions from __init__
        try:
            inst = cls(
                data=data,
                core_components=core_components,
                static=static,
                flora=flora,
                extra_pft_traits=extra_traits,
                model_constants=model_constants,
                exporter=exporter,
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
        extra_pft_traits: ExtraTraitsPFT,
        model_constants: PlantsConsts = PlantsConsts(),
        **kwargs: Any,
    ) -> None:
        """Setup implementation for the Plants Model.

        Args:
            flora: A flora containing the plant functional types used in the plants
                model.
            extra_pft_traits: Additional traits for each plant functional type, keyed by
                PFT name.
            model_constants: Set of constants for the plants model.
            **kwargs: Further arguments to the setup method.
        """

        # Set the instance attributes from the __init__ arguments
        self.flora = flora
        self.extra_pft_traits = extra_pft_traits
        self.model_constants = model_constants

        # Adjust flora rates to timestep
        # TODO: This is kinda hacky because the Flora instances is a frozen dataclass,
        #       but we only bring the model timing and flora object together at this
        #       point. We would have to pass the model timing in to the flora creation.
        #       Potentially create a Flora.adjust_rate_timing() method, but we'd need to
        #       be sure that the approach is sane first.

        # Respiration rates are expressed as proportions of masses per year so need to
        # be reduced proportionately to the number of updates per year
        updates_per_year = self.model_timing.updates_per_year
        object.__setattr__(self.flora, "resp_f", self.flora.resp_f / updates_per_year)
        object.__setattr__(self.flora, "resp_r", self.flora.resp_r / updates_per_year)
        object.__setattr__(self.flora, "resp_s", self.flora.resp_s / updates_per_year)
        object.__setattr__(self.flora, "resp_rt", self.flora.resp_rt / updates_per_year)

        # Turnover rates are implemented as the number of years required to completely
        # turnover foliage/roots etc and are included in equations as the reciprocal of
        # the values. So rescaling them to shorter timescales requires that we
        # _increase_ the values proportionally to the reduced time between updates.
        object.__setattr__(self.flora, "tau_f", self.flora.tau_f * updates_per_year)
        object.__setattr__(self.flora, "tau_r", self.flora.tau_r * updates_per_year)
        object.__setattr__(self.flora, "tau_rt", self.flora.tau_rt * updates_per_year)

        # Now build the communities with the updated rates
        self.communities = PlantCommunities(
            data=self.data, flora=self.flora, grid=self.grid
        )

        # Initialize the stochiometries of each cohort. Each StemStochiometry object
        # contains a list of StemTissue objects, which are the tissues that make up the
        # stochiometry of the stem. The initial values for N and P are based on the
        # ideal stochiometric ratios defined in the PlantsConsts class.
        # TODO: #697 - these need to be configurable
        self.stochiometries = {}

        for cell_id in self.communities.keys():
            self.stochiometries[cell_id] = {}
            self.stochiometries[cell_id]["N"] = StemStochiometry.default_init(
                self.communities[cell_id],
                extra_pft_traits=self.extra_pft_traits,
                element="N",
            )
            self.stochiometries[cell_id]["P"] = StemStochiometry.default_init(
                self.communities[cell_id],
                extra_pft_traits=self.extra_pft_traits,
                element="P",
            )

        # This is widely used internally so store it as an attribute.
        self._canopy_layer_indices = self.layer_structure.index_canopy

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

        # Set the stem allocations to be an empty dictionary - this attribute is
        # populated by the update method but not at setup.
        self.stem_allocations = {}

        # TODO - #697 these need to be configurable
        self.pmodel_consts = PModelConst()
        self.pmodel_core_consts = CoreConst()

        # Create and populate the canopy data layers and the subcanopy vegetation and
        # then set the shortwave absorption from the first time index
        self.update_canopy_layers()
        self.set_subcanopy_light_capture()
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

        # Run the community data exporter
        self.exporter.dump(
            communities=self.communities,
            canopies=self.canopies,
            stem_allocations=self.stem_allocations,
            time=self.model_timing.start_time,
        )

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
        self.canopies = calculate_canopies(
            communities=self.communities,
            max_canopy_layers=self.layer_structure.n_canopy_layers,
        )
        self.update_canopy_layers()
        self.set_subcanopy_light_capture()
        self.set_shortwave_absorption(time_index=time_index)

        # Estimate the canopy GPP and growth with the updated this update
        self.calculate_light_use_efficiency()
        self.estimate_gpp(time_index=time_index)

        # Calculate uptake from each inorganic soil nutrient pool
        self.calculate_nutrient_uptake()

        self.allocate_gpp()

        # Calculate the turnover of each plant biomass pool
        self.calculate_turnover()

        # Calculate the rate at which plants take nutrients from mycorrhizal fungi
        self.calculate_mycorrhizal_uptakes()

        # Apply mortality to plant cohorts
        self.apply_mortality()

        # Calculate the subcanopy vegetation
        self.calculate_subcanopy_dynamics()

        # Run the community data exporter
        self.exporter.dump(
            communities=self.communities,
            canopies=self.canopies,
            stem_allocations=self.stem_allocations,
            time=self.model_timing.start_time
            + time_index * self.model_timing.update_interval,
        )

    def cleanup(self) -> None:
        """Placeholder function for plants model cleanup."""

    def update_canopy_layers(self) -> None:
        """Update the canopy structure for the plant communities.

        This method updates the following canopy layer variables in the data object from
        the current state of the canopies attribute:

        * the layer closure heights (``layer_heights``),
        * the layer leaf area indices (``leaf_area_index``),
        * the fraction of absorbed photosynthetically active radiation in each layer
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
            fapar[fill_idx] = canopy.community_data.average_layer_fapar[:, None]

            # Calculate the per stem leaf mass  as (stem leaf area * (1/sigma) * L) and
            # then scale up to the number of individuals and sum across cohorts to give
            # a total mass per layer within the cell.
            # TODO - need to expose the per cohort data to allow selective herbivory.
            # BUG  - The calculation here needs to be robust to no plants being present
            #        in a cell. At the moment, even with plants present, the scaling of
            #        the model is resulting in cohort total LAI of zero, which gives
            #        zero division and hence np.nan in the expected leaf mass per cohort
            #        per layer, which then breaks the setting of the filled layer mask.
            #        But with actually no plants present, the code still needs to work.

            cohort_leaf_mass_per_layer = (
                canopy.cohort_data.stem_leaf_area
                * (1 / community.stem_traits.sla)
                * community.stem_traits.lai
            ) * community.cohorts.n_individuals

            mass[fill_idx] = cohort_leaf_mass_per_layer.sum(axis=1, keepdims=True)

            # LAI - insert community average LAI values from light capture model
            lai[fill_idx] = canopy.community_data.average_layer_lai[:, None]

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

        # Update the below canopy light fraction
        self.below_canopy_light_fraction = np.array(
            [
                cnpy.community_data.transmission_to_ground
                for cnpy in self.canopies.values()
            ]
        )

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
        """  # noqa: D405

        # Get the canopy top shortwave downwelling radiation for the current time slice
        canopy_top_swd = (
            self.data["downward_shortwave_radiation"]
            .isel(time_index=time_index)
            .to_numpy()
        )

        # Calculate the fate of shortwave radiation through the layers assuming that the
        # vegetation fAPAR applies to all light wavelengths
        absorbed_irradiance = self.data["layer_fapar"] * canopy_top_swd

        # Add the remaining irradiance at the surface layer level
        absorbed_irradiance[self.layer_structure.index_topsoil] = (
            canopy_top_swd * self.ground_incident_light_fraction
        )

        self.data["shortwave_absorption"] = absorbed_irradiance

    def calculate_light_use_efficiency(self) -> None:
        """Calculate the light use efficiency across vertical layers.

        This method uses the P Model to estimate the light use efficiency within
        vertical layers, given the environmental conditions through the canopy
        structure.
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

        self.pmodel = PModel(pmodel_env)

    def estimate_gpp(self, time_index: int) -> None:
        """Estimate the gross primary productivity within plant cohorts.

        This method uses estimated light use efficiency from the P Model to estimate the
        light use efficiency of leaves in gC mol-1, given the environment (temperature,
        atmospheric pressure, vapour pressure deficit and atmospheric CO2 concentration)
        within each canopy layer. This is multiplied by the absorbed irradiance within
        each canopy layer to predict the gross primary productivity (GPP, µg C m-2 s-1)
        for each canopy layer.

        This method requires that the calculate_light_use_efficiency method has been run
        to populate the
        :attr:`~virtual_ecosystem.models.plants.plants_model.PlantsModel.pmodel`
        attribute.

        The GPP for each cohort is then estimated by multiplying the cohort canopy area
        within each layer by GPP and the time elapsed in seconds since the last update.

        .. TODO:

            * Conversion of transpiration from `µmol m-2` to `mm m-2` currently ignores
              density changes with conditions:
              `#723 <https://github.com/ImperialCollegeLondon/virtual_ecosystem/issues/723>`_

        Args:
            time_index: The index along the time axis of the forcing data giving the
                time step to be used to estimate GPP.

        Raises:
            ValueError: if any of the P Model forcing variables are not defined.
        """

        # Get the canopy top PPFD per grid cell for this time index
        canopy_top_ppfd = (
            self.data["downward_shortwave_radiation"]
            .isel(time_index=time_index)
            .to_numpy()
            * self.model_constants.dsr_to_ppfd
        )

        # Initialise transpiration array to collect per grid cell values
        transpiration = self.layer_structure.from_template("transpiration")

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

            # HACK? Need to consider empty cells - not done systematically at the moment
            #       and there is an issue with identifying cells with a single canopy
            #       layer. I think this line might be right to handle the empty cell,
            #       but is currently a sticking plaster for wider problems.
            if active_layers.size == 0:
                continue

            # GPP for each later is estimated as (value, dimensions, units):
            #    LUE                (n_active_layers, 1)          [gC mol-1]
            #    * cohort fAPAR     (n_active_layers, n_cohorts)  [-]
            #    * canopy top PPFD  scalar                        [µmol m-2 s-1]
            #    * stem leaf area   (n_active_layers, n_cohorts)  [m2]
            #    * time elapsed     scalar                        [s]
            # Units:
            #    g C mol-1 * (-) * µmol m-2 s-1 * m2 * s = µg C

            per_layer_gpp = (
                self.pmodel.lue[active_layers, :][:, [cell_id]]  # gC mol-1
                * canopy.cohort_data.fapar  # unitless
                * canopy_top_ppfd[cell_id]  # µmol m-1 s-1
                * canopy.cohort_data.stem_leaf_area  # m2
                * self.model_timing.update_interval_seconds  # second
            )

            # Calculate and store whole stem GPP in kg C
            self.per_stem_gpp[cell_id] = per_layer_gpp.sum(axis=0) * 1e-9

            # The per layer transpiration associated with that GPP then needs GPP in
            # moles of Carbon  (GPP in µg C / (Molar mass carbon * 1e6))):
            #   GPP in mols   (n_layer, n_cohorts)  [mol C]
            #   * IWUE        (n_layer, 1)          [µmol mol -1]
            # Units:
            #    mol C  * µmol H2O mol C -1 = µmol H2O
            per_layer_transpiration_micromolar = (
                per_layer_gpp / (self.pmodel_core_consts.k_c_molmass * 1e6)
            ) * self.pmodel.iwue[active_layers, :][:, [cell_id]]

            # Convert to mm
            per_layer_transpiration_mm = convert_water_moles_to_mm(
                water_moles=per_layer_transpiration_micromolar * 1e-6,
                tc=np.repeat(
                    self.pmodel.env.tc[active_layers, :][:, [cell_id]],
                    canopy.n_cohorts,
                    axis=1,
                ),
                patm=np.repeat(
                    self.pmodel.env.patm[active_layers, :][:, [cell_id]],
                    canopy.n_cohorts,
                    axis=1,
                ),
                core_const=self.pmodel_core_consts,
            )

            # Calculate and store total stem transpiration in mm  per stem and total
            # grid cell transpiration in mm m-2 since last update
            self.per_stem_transpiration[cell_id] = per_layer_transpiration_mm.sum(
                axis=0
            )

            # Calculate the total transpiration per layer in m2 in mm
            transpiration[active_layers, cell_id] = (
                community.cohorts.n_individuals * per_layer_transpiration_mm
            ).sum(axis=1)

        # Pass values to data object
        self.data["transpiration"] = transpiration

    def allocate_gpp(self) -> None:
        """Calculate the allocation of GPP to growth and respiration.

        This method uses the T Model to estimate the allocation of plant gross
        primary productivity to respiration, growth, maintenance and turnover costs.
        The method then simulates growth by increasing dbh and calculates leaf and root
        turnover values.
        """

        # Initialize all turnover variables to 0 with the proper dimensions.
        # Most variables are merged across PFTs and cohorts - one pool per cell.
        self.data["leaf_turnover"] = xr.full_like(self.data["elevation"], 0)
        self.data["root_turnover"] = xr.full_like(self.data["elevation"], 0)
        self.data["root_carbohydrate_exudation"] = xr.full_like(
            self.data["elevation"], 0
        )
        self.data["plant_symbiote_carbon_supply"] = xr.full_like(
            self.data["elevation"], 0
        )
        self.data["fallen_non_propagule_c_mass"] = xr.full_like(
            self.data["elevation"], 0
        )

        # Fallen propagules and canopy RT are stored per cell and per PFT.
        # Canopy RT mass is deliberately not partitioned across canopy vertical layers.
        pft_cell_template = xr.DataArray(
            data=np.zeros((self.grid.n_cells, self.flora.n_pfts)),
            coords={"cell_id": self.data["cell_id"], "pft": self.flora.name},
        )
        self.data["fallen_n_propagules"] = pft_cell_template.copy()
        self.data["canopy_n_propagules"] = pft_cell_template.copy()
        self.data["canopy_non_propagule_c_mass"] = pft_cell_template.copy()

        for cell_id in self.communities.keys():
            community = self.communities[cell_id]
            cohorts = community.cohorts
            stochiometries = self.stochiometries[cell_id]

            # Calculate the allocation of GPP per stem and store it in the attribute
            stem_allocation = StemAllocation(
                stem_traits=community.stem_traits,
                stem_allometry=community.stem_allometry,
                whole_crown_gpp=self.per_stem_gpp[cell_id],
            )
            self.stem_allocations[cell_id] = stem_allocation

            # ALLOCATE TO TURNOVER:
            # Grow the plants by increasing the stem dbh
            # TODO: dimension mismatch (1d vs 2d array) - check in pyrealm
            # HACK: The current code prevents stems shrinking to zero and below. This is
            #       temporary until we fix what happens with stem shrinkage and carbon
            #       starvation to something biological.
            #
            #       We could kill stems where the new D <=0 but adds loads of code and
            #       for the moment we just want to avoid passing pyrealm negative sizes.
            #       If the np.where is removed and this is set directly, then pyrealm
            #       will detect D <= 0 and raise an exception.

            new_dbh = cohorts.dbh_values + stem_allocation.delta_dbh
            cohorts.dbh_values = np.where(new_dbh <= 0, cohorts.dbh_values, new_dbh)

            # Sum of turnover from all cohorts in a grid cell
            self.data["leaf_turnover"][cell_id] = self.convert_to_litter_units(
                input_mass=np.sum(
                    stem_allocation.foliage_turnover * cohorts.n_individuals
                ),
            )
            self.data["root_turnover"][cell_id] = self.convert_to_litter_units(
                input_mass=np.sum(
                    stem_allocation.fine_root_turnover * cohorts.n_individuals
                ),
            )

            # Partition reproductive tissue into propagule and non-propagule masses and
            # convert the propagule mass to number of propagules
            # 1. Turnover reproductive tissue mass leaving the canopy to the ground
            stem_fallen_n_propagules, stem_fallen_non_propagule_c_mass = (
                self.partition_reproductive_tissue(
                    # TODO: dimension issue in pyrealm, returns 2D array.
                    stem_allocation.reproductive_tissue_turnover.squeeze()
                )
            )

            # 2. Canopy reproductive tissue mass: partition into propagules and
            # non-propagules.
            # TODO - This is wrong. Reproductive tissue mass can't simply move backwards
            #        and forwards between these two classes.
            stem_canopy_n_propagules, stem_canopy_non_propagule_c_mass = (
                self.partition_reproductive_tissue(
                    community.stem_allometry.reproductive_tissue_mass
                )
            )

            # Add those partitions to pools
            #  - Merge fallen non-propagule mass into a single pool
            self.data["fallen_non_propagule_c_mass"][cell_id] = (
                self.convert_to_litter_units(
                    input_mass=(
                        stem_fallen_non_propagule_c_mass * cohorts.n_individuals
                    ).sum(),
                )
            )

            # Allocate fallen propagules, and canopy propagules and non-propagule mass
            # into PFT specific pools by iterating over cohort PFTs.
            # TODO: not sure how performant this is, there might be a better solution.

            for (
                cohort_pft,
                fallen_n_propagules,
                canopy_n_propagules,
                canopy_non_propagule_mass,
                cohort_n_stems,
            ) in zip(
                cohorts.pft_names,
                stem_fallen_n_propagules.squeeze(),
                stem_canopy_n_propagules.squeeze(),
                stem_canopy_non_propagule_c_mass.squeeze(),
                cohorts.n_individuals,
            ):
                self.data["fallen_n_propagules"].loc[cell_id, cohort_pft] += (
                    fallen_n_propagules * cohort_n_stems
                )
                self.data["canopy_n_propagules"].loc[cell_id, cohort_pft] += (
                    canopy_n_propagules * cohort_n_stems
                )
                self.data["canopy_non_propagule_c_mass"].loc[cell_id, cohort_pft] += (
                    canopy_non_propagule_mass * cohort_n_stems
                )

            # ALLOCATE N TO REGROW WHAT WAS LOST TO TURNOVER
            for stochiometry in stochiometries.values():
                stochiometry.account_for_element_loss_turnover(stem_allocation)

            # ALLOCATE GPP TO ACTIVE NUTRIENT PATHWAYS:
            # Allocate the topsliced GPP to root exudates with remainder as active
            # nutrient pathways
            self.data["root_carbohydrate_exudation"][cell_id] = (
                self.convert_to_soil_units(
                    input_mass=np.sum(
                        stem_allocation.gpp_topslice
                        * self.model_constants.root_exudates
                        * cohorts.n_individuals
                    )
                )
            )

            self.data["plant_symbiote_carbon_supply"][cell_id] = (
                self.convert_to_soil_units(
                    input_mass=np.sum(
                        stem_allocation.gpp_topslice
                        * (1 - self.model_constants.root_exudates)
                        * cohorts.n_individuals
                    )
                )
            )

            # Subtract the N/P required from growth from the element store, and
            # redistribute it to the individual tissues.
            for stochiometry in stochiometries.values():
                stochiometry.account_for_growth(stem_allocation)

            # Balance the N & P surplus/deficit with the symbiote carbon supply
            for element in ["N", "P"]:
                element_weighted_avg = np.dot(
                    self.data["ecto_supply_limit_" + element.lower()][cell_id]
                    + self.data["arbuscular_supply_limit_" + element.lower()][cell_id],
                    cohorts.n_individuals,
                )
                element_available_per_cohort = element_weighted_avg / sum(
                    element_weighted_avg
                )
                element_available_per_stem = np.divide(
                    element_available_per_cohort, cohorts.n_individuals
                )
                stochiometries[element].element_surplus += element_available_per_stem

            # Cohort by cohort, distribute the surplus/deficit across the tissue types
            for cohort in range(len(cohorts.n_individuals)):
                for stochiometry in stochiometries.values():
                    if stochiometry.element_surplus[cohort] < 0:
                        # Distribute deficit across the tissue types
                        stochiometry.distribute_deficit(cohort)

                    elif (
                        stochiometry.element_surplus[cohort] > 0
                        and stochiometry.tissue_deficit[cohort] > 0
                    ):
                        # Distribute the surplus across the tissue types
                        stochiometry.distribute_surplus(cohort)

                    else:
                        # NO ADJUSTMENT REQUIRED - there is a surplus in the store, but
                        # there is no deficit in the tissue types.
                        pass

            # Update community allometry with new dbh values
            community.stem_allometry = StemAllometry(
                stem_traits=community.stem_traits, at_dbh=cohorts.dbh_values
            )

            self.update_cn_ratios()

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
            self.data["deadwood_production"][cell_id] = self.convert_to_litter_units(
                input_mass=np.sum(mortality * community.stem_allometry.stem_mass),
            )

    def update_cn_ratios(self) -> None:
        """Update the C:N and C:P ratios of plant tissues.

        This function updates the C:N and C:P ratios of various plant tissues, including
        deadwood, leaf turnover, plant reproductive tissue turnover, and root turnover.

        # TODO: Update this to use the Stochiometry class values.

        Warning:
            At present, this function just sets values to original constants.
        """

        # C:N and C:P ratios
        self.data["deadwood_c_n_ratio"] = xr.full_like(self.data["elevation"], 56.5)
        self.data["leaf_turnover_c_n_ratio"] = xr.full_like(
            self.data["elevation"], 25.5
        )
        self.data["plant_reproductive_tissue_turnover_c_n_ratio"] = xr.full_like(
            self.data["elevation"], 12.5
        )
        self.data["root_turnover_c_n_ratio"] = xr.full_like(
            self.data["elevation"], 45.6
        )
        self.data["deadwood_c_p_ratio"] = xr.full_like(self.data["elevation"], 856.5)
        self.data["leaf_turnover_c_p_ratio"] = xr.full_like(
            self.data["elevation"], 415.0
        )
        self.data["plant_reproductive_tissue_turnover_c_p_ratio"] = xr.full_like(
            self.data["elevation"], 125.5
        )
        self.data["root_turnover_c_p_ratio"] = xr.full_like(
            self.data["elevation"], 656.7
        )

        for cell_id in self.communities.keys():
            pass
            # TODO: ask Jacob what he wants from these values
            # self.data["deadwood_c_n_ratio"][cell_id] = (
            # self.stochiometries[cell_id]["N"]...

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

        self.data["nitrogen_fixation_carbon_supply"] = xr.full_like(
            self.data["elevation"], 0.01
        )

    def calculate_nutrient_uptake(self) -> None:
        """Calculate uptake of soil nutrients by the plant community.

        This function calculates the rate a which plants take up inorganic nutrients
        (ammonium, nitrate, and labile phosphorus) from the soil. The function then
        assigns the N/P uptake values to the respective community through the
        stochiometry class.

        Warning:
            At present, this function just calculates uptake based on an entirely made
            up function, and does not link to plant dynamics in any way.
        """

        # Assume plants can take 0.1% of the available nutrient per day
        self.data["plant_ammonium_uptake"] = self.data["dissolved_ammonium"] * 0.01
        self.data["plant_nitrate_uptake"] = self.data["dissolved_nitrate"] * 0.01
        self.data["plant_phosphorus_uptake"] = self.data["dissolved_phosphorus"] * 0.01

        # Calculate N/P uptake (g N/P per stem) due to transpiration. Multiply:
        # - Per stem transpiration (µmol H2O per stem)
        # - Conversion factor from µmol H2O to m^3 (1.08015*10^-11)
        # - Concentration of N/P uptake (kg m^-3)
        # - Kg to g (1000)
        # TODO: scale by atmospheric pressure and temperature (#927)

        for cell_id in self.communities.keys():
            self.stochiometries[cell_id]["N"].element_surplus += (
                self.per_stem_transpiration[cell_id]
                * 1.8015e-11
                * (
                    self.data["plant_ammonium_uptake"][cell_id]
                    + self.data["plant_nitrate_uptake"][cell_id]
                ).item()
                * 1000
            )
            self.stochiometries[cell_id]["P"].element_surplus += (
                self.per_stem_transpiration[cell_id]
                * (1.8015 * pow(10.0, -11))
                * (self.data["plant_phosphorus_uptake"][cell_id]).item()
                * 1000
            )

    def calculate_mycorrhizal_uptakes(self) -> None:
        """Calculate the rate at which plants take nutrients from mycorrhizal fungi.

        Warning:
            At present, this function just calculates uptake based on an entirely made
            up function, and does not link to plant dynamics in any way.
        """

        # Making arbitrary assumption that the plants take exactly half the maximum
        # supply amount, this should be replaced by something more sensible
        self.data["plant_n_uptake_arbuscular"] = (
            0.5 * self.data["arbuscular_supply_limit_n"]
        )
        self.data["plant_n_uptake_ecto"] = 0.5 * self.data["ecto_supply_limit_n"]
        self.data["plant_p_uptake_arbuscular"] = (
            0.5 * self.data["arbuscular_supply_limit_p"]
        )
        self.data["plant_p_uptake_ecto"] = 0.5 * self.data["ecto_supply_limit_p"]

    def set_subcanopy_light_capture(self) -> None:
        r"""Calculate the leaf area index and absorption of subcanopy vegetation.

        The subcanopy vegetation is represented as pure leaf biomass (:math:`M_{SC}`, kg
        m-2), with an associated extinction coefficient (:math:`k`) and specific leaf
        area (:math:`\sigma`, kg m-2) set in the model constants. These can be used to
        calculate the   leaf area index (:math:`L`) and hence the absorption fraction
        (:math:`f_{a}`) of  the subcanopy vegetation layer via the Beer-Lambert law: 

        .. math ::
            :nowrap:

            \[
                \begin{align*}
                    L &= M_{SC} \sigma \\
                    f_a = e^{-kL}
                \end{align*}
            \]
        """

        # Calculate the leaf area index - values are already in kg m-2 so no need to
        # account for the area occupied by the biomass - and set the leaf area
        subcanopy_lai = (
            self.data["subcanopy_vegetation_biomass"]
            * self.model_constants.subcanopy_specific_leaf_area
        )

        # Beer-Lambert transmission - note that this is 1 when there is no biomass and
        # so no light is absorbed by the vegetation and all of the subcanopy light
        # reaches the ground.
        subcanopy_light_transmission = np.exp(
            -self.model_constants.subcanopy_extinction_coef * subcanopy_lai
        )

        # Absorb a fraction of the below canopy light and pass the rest on to the ground
        # incident light fraction
        sub_canopy_fapar = self.below_canopy_light_fraction * (
            1 - subcanopy_light_transmission
        )

        self.ground_incident_light_fraction = (
            self.below_canopy_light_fraction * subcanopy_light_transmission
        )

        # Store those values
        self.data["leaf_area_index"][self.layer_structure.index_surface_scalar] = (
            subcanopy_lai
        )
        self.data["layer_fapar"][self.layer_structure.index_surface_scalar] = (
            sub_canopy_fapar
        )

    def calculate_subcanopy_dynamics(self) -> None:
        r"""Estimate the dynamics of subcanopy vegetation.

        The fraction of the PPFD reaching the topsoil layer is extracted, given the leaf
        area index and fAPAR calculated from the biomass of subcanopy vegetation. That
        is then used to estimate GPP, given the LUE from the P Model in the surface
        layer.

        The GPP allocation then follows the parameterisation of the T Model but where
        the subcanopy vegetation biomass is represented purely as leaf tissue.

        At each update:

        * The ``subcanopy_vegetation_biomass`` increases with the new growth from light
          capture and the addition of a sprouting biomass from the
          ``subcanopy_seedbank_biomass``.

        * The ``subcanopy_seedbank_biomass`` loses mass due to resprouting but gains a
          proportion of the net primary productivity from the subcanopy vegetation.
        """

        # Calculate the gross primary productivity since the last update.
        #    LUE                     1 layer          [gC mol-1]
        #    * shortwave absorption  1 layer          [µmol m-2 s-1]
        #    * DST to PPFD           scalar           [-]
        #    * time elapsed     scalar                [s]
        # Units:
        #    gC mol-1 * µmol m-2 s-1  * (-) * s = µg C m-2
        subcanopy_gpp = (
            self.pmodel.lue[self.layer_structure.index_surface_scalar, :]
            * self.data["shortwave_absorption"][
                self.layer_structure.index_surface_scalar, :
            ]
            * self.model_constants.dsr_to_ppfd
            * self.model_timing.update_interval_seconds
        )

        # Calculate the transpiration associated with that GPP in moles
        subcanopy_transpiration = (
            subcanopy_gpp / (self.pmodel_core_consts.k_c_molmass * 1e6)
        ) * self.pmodel.iwue[self.layer_structure.index_surface_scalar, :]

        # Calculate NPP, converting µg C m-2 to  kg C m-2
        subcanopy_npp = (
            self.model_constants.subcanopy_yield
            * (subcanopy_gpp * 1e-9)
            * (1 - self.model_constants.subcanopy_respiration_fraction)
        )

        subcanopy_growth = subcanopy_npp * (
            1 - self.model_constants.subcanopy_reproductive_allocation
        )

        new_seedbank = subcanopy_npp - subcanopy_growth

        subcanopy_sprouting_mass = self.data["subcanopy_seedbank_biomass"] * (
            1
            - np.exp(
                -self.model_constants.subcanopy_sprout_rate
                * (1 / self.model_timing.updates_per_year)
            )
        )

        # Update the biomasses
        self.data["subcanopy_vegetation_biomass"] += subcanopy_growth + (
            self.model_constants.subcanopy_sprout_yield * subcanopy_sprouting_mass
        )

        self.data["subcanopy_seedbank_biomass"] += (
            new_seedbank - subcanopy_sprouting_mass
        )

        self.data["transpiration"] += subcanopy_transpiration

    def partition_reproductive_tissue(
        self, reproductive_tissue_mass: NDArray[np.floating]
    ) -> tuple[NDArray[np.int_], NDArray[np.floating]]:
        """Partition reproductive tissue into propagules and non-propagules.

        This function partitions the reproductive tissue of each cohort into
        propagules and non-propagules. The number of propagules is calculated based on
        the mass of reproductive tissue and the mass of each propagule. The remaining
        mass is considered as non-propagule reproductive tissue.
        """

        n_propagules = np.floor(
            reproductive_tissue_mass
            * self.model_constants.propagule_mass_portion
            / self.model_constants.carbon_mass_per_propagule
        )

        non_propagule_mass = reproductive_tissue_mass - (
            n_propagules * self.model_constants.carbon_mass_per_propagule
        )

        return n_propagules, non_propagule_mass

    def convert_to_litter_units(
        self, input_mass: NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Helper function to convert plant quantities into litter model units.

        The plant model records the plant biomass in units of mass (kg) per grid square,
        whereas the litter model expects litter inputs as kg per m^2.

        Args:
            input_mass: The mass (of carbon) being passed from the plant model to the
                litter model [kg/g]

        Returns:
            The input mass converted to the density units that the litter model uses [kg
            m^-2]
        """

        return input_mass / self.grid.cell_area

    def convert_to_soil_units(
        self, input_mass: NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Helper function to convert plant quantities into soil model units.

        The plant model records the GPP allocations (summed over stems) in units of mass
        (g), whereas the soil model expects inputs into the soil to be expressed as rate
        per area units (i.e. kg m^-2 day^-1). As well as converting to per area and rate
        units this function also converts from g to kg.

        Args:
            input_mass: The mass (of carbon) being passed from the plant model to the
                soil model [g]

        Returns:
            The input mass converted to the density rate units that the soil model uses
            [kg m^-2 day^-1]
        """

        time_interval_in_days = self.model_timing.update_interval_seconds / 86400

        return input_mass / (1000.0 * time_interval_in_days * self.grid.cell_area)
