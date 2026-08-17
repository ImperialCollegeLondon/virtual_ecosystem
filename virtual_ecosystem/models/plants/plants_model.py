"""The :mod:`~virtual_ecosystem.models.plants.plants_model` module creates
:class:`~virtual_ecosystem.models.plants.plants_model.PlantsModel` class as a child of
the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
"""  # noqa: D205

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pandas
import xarray as xr
from numpy.typing import NDArray
from pyrealm.constants import CoreConst, PModelConst
from pyrealm.core.water import convert_water_moles_to_mm
from pyrealm.demography.canopy import Canopy
from pyrealm.demography.cohorts import cohort_id_generator, create_cohorts
from pyrealm.demography.flora import Flora
from pyrealm.demography.tmodel import GrowthIncrements, StemAllocation, StemAllometry
from pyrealm.pmodel import PModel, PModelEnvironment

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConfiguration, PyrealmConfig
from virtual_ecosystem.models.hydrology.model_config import (
    HydrologyConfiguration,
    HydrologyConstants,
)
from virtual_ecosystem.models.plants.biomasses import (
    Biomasses,
    BiomassTissueABC,
    FoliageBiomass,
    FruitBiomass,
    RootBiomass,
    SeedBiomass,
    StemBiomass,
    partition_reproductive_tissue_mass,
)
from virtual_ecosystem.models.plants.canopy import (
    calculate_canopies,
    initialise_canopy_layers,
)
from virtual_ecosystem.models.plants.communities import Community, PlantCommunities
from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
from virtual_ecosystem.models.plants.functional_types import get_flora_from_config
from virtual_ecosystem.models.plants.model_config import (
    PlantsConfiguration,
    PlantsConstants,
)
from virtual_ecosystem.models.plants.subcanopy import Subcanopy


class PlantsModel(
    BaseModel,
    model_name="plants",
    model_update_bounds=("1 day", "1 year"),
    vars_required_for_init=(
        "downward_shortwave_radiation",
        "plant_pft_propagules",
        "subcanopy_seedbank_biomass",
        "subcanopy_vegetation_biomass",
    ),
    vars_populated_by_init=(
        "layer_fapar",
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_leaf_mass",  # NOTE - placeholder resource for herbivory
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "shortwave_absorption",
        "subcanopy_seedbank_litter_cnp",
        "subcanopy_vegetation_litter_cnp",
        "subcanopy_vegetation_cnp",
        "subcanopy_seedbank_cnp",
        "fallen_seeds_cnp",
        "fallen_fruit_cnp",
        "canopy_seed_cnp",
        "canopy_fruit_cnp",
        "canopy_foliage_cnp",
        "stem_turnover_cnp",
        "foliage_turnover_cnp",
        "root_turnover_cnp",
        "seed_turnover_cnp",
        "fruit_turnover_cnp",
        "subcanopy_vegetation_cnp_consumed",
        "subcanopy_seedbank_cnp_consumed",
        "canopy_foliage_cnp_consumed",
        "canopy_seed_cnp_consumed",
        "canopy_fruit_cnp_consumed",
        "fallen_seeds_cnp_consumed",
        "fallen_fruit_cnp_consumed",
        "root_lignin",
        "senesced_leaf_lignin",
        "stem_lignin",
        "subcanopy_seedbank_litter_lignin",
        "subcanopy_vegetation_litter_lignin",
    ),
    vars_required_for_update=(
        "air_temperature",
        "atmospheric_co2",
        "atmospheric_pressure",
        "dissolved_ammonium",
        "dissolved_nitrate",
        "dissolved_phosphorus",
        "downward_shortwave_radiation",
        "plant_pft_propagules",
        "subcanopy_seedbank_biomass",
        "subcanopy_vegetation_biomass",
        "vapour_pressure_deficit",
        "arbuscular_mycorrhizal_n_supply",
        "arbuscular_mycorrhizal_p_supply",
        "ectomycorrhizal_n_supply",
        "ectomycorrhizal_p_supply",
        "soil_moisture",
    ),
    vars_updated=(
        "stem_turnover_cnp",  # i.e. deadwood
        "foliage_turnover_cnp",
        "root_turnover_cnp",
        "seed_turnover_cnp",
        "fruit_turnover_cnp",
        "canopy_fruit_cnp",
        "canopy_seed_cnp",
        "fallen_fruit_cnp",
        "fallen_seeds_cnp",
        "canopy_foliage_cnp",
        "subcanopy_seedbank_litter_cnp",
        "subcanopy_vegetation_litter_cnp",
        "subcanopy_vegetation_cnp",
        "subcanopy_seedbank_cnp",
        "layer_fapar",
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_leaf_mass",  # NOTE - placeholder resource for herbivory
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "shortwave_absorption",
        "subcanopy_seedbank_biomass",
        "subcanopy_vegetation_biomass",
        "transpiration",
        "subcanopy_ammonium_uptake",
        "subcanopy_nitrate_uptake",
        "subcanopy_phosphorus_uptake",
        "fallen_fruit_decay_cnp",
    ),
    vars_populated_by_first_update=(
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "transpiration",
        "subcanopy_ammonium_uptake",
        "subcanopy_nitrate_uptake",
        "subcanopy_phosphorus_uptake",
        "fallen_fruit_decay_cnp",
    ),
):
    """Representation of plants in the Virtual Ecosystem.

    The plants model is initialised using data from three sources:

    1. The ``flora`` object contains a set of plant functional types, associating unique
       PFT names with sets of required traits for each PFT.
    2. A data frame defining the initial cohort inventories for each grid cell. Each row
       in the data frame defines a cohort in one of the grid cells and the fields set:

        * ``plant_cohorts_pft``: The PFT of the cohort, matching an entry in the
          ``flora``
        * ``plant_cohorts_cell_id``: The grid cell id containing the cohort
        * ``plant_cohorts_n``: The number of individuals in the cohort
        * ``plant_cohorts_dbh``: The diameter at breast height of the individuals in
          metres.

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
        exporter: An instance of the ``CommunityDataExporter`` class used to export
            plant community data for each time step.
        flora: A flora containing the plant functional types used in the plants
            model.
        cohort_data: A data frame containing the initial cohort data.
        extra_pft_traits: Additional traits for each plant functional type, keyed by
            PFT name.
        model_constants: Set of constants for the plants model.
        pyrealm_config: Configuration options to the pyrealm package.
        hydrology_constants: Constants from the hydrology model.
        static: Boolean flag indicating if the model should run in static mode.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        exporter: CommunityDataExporter,
        flora: Flora,
        cohort_data: pandas.DataFrame,
        model_constants: PlantsConstants = PlantsConstants(),
        pyrealm_config: PyrealmConfig = PyrealmConfig(),
        hydrology_constants: HydrologyConstants = HydrologyConstants(),
        static: bool = False,
    ):
        """Plants init function.

        The init function is used only to define class attributes. Any logic should be
        handled in :fun:`~virtual_ecosystem.plants.plants_model._setup`.
        """

        # Run the base model __init__
        super().__init__(data, core_components, static)

        # Define and populate model specific attributes
        self.flora: Flora
        """A flora containing the plant functional types used in the plants model."""
        self.initial_cohort_data: pandas.DataFrame
        """A dataframe providing the initial cohort data."""
        self.cohort_id_generator: Iterator
        """Set of constants for the plants model"""
        self.model_constants: PlantsConstants
        """Set of constants for the plants model"""
        self.communities: PlantCommunities
        """An instance of PlantCommunities providing dictionary access keyed by cell id
        to PlantCommunity instances for each cell."""
        self.biomasses: dict[int, Biomasses]
        """A dictionary keyed by cell id of the carbon and nutrient biomass of each
        community."""
        self.biomass_tissues: list[type[BiomassTissueABC]]
        """A list of types of biomass subclasses that sets the tissues to be
        modelled within the simulation."""
        self.allocations: dict[int, StemAllocation]
        """A dictionary keyed by cell id giving the allocation of each community."""
        self._canopy_layer_indices: NDArray[np.bool_]
        """The indices of the canopy layers within wider vertical profile. This is 
        a shorter reference to self.layer_structure.index_canopy."""
        self.canopies: dict[int, Canopy | None]
        """A dictionary giving the canopy structure of each grid cell."""
        self.stem_allocations: dict[int, StemAllocation]
        """A dictionary giving the stem allocation of GPP for the community in each grid
        cell. The dictionary is only populated by the update method - before that the
        dictionary will be empty."""
        self.growth_increments: dict[int, GrowthIncrements]
        """A dictionary giving the growth increments for the community in each grid
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
        self.pyrealm_pmodel_consts: PModelConst
        """PModel constants used by pyrealm."""
        self.pyrealm_core_consts: CoreConst
        """Core constants used by pyrealm."""

        self.per_update_interval_stem_mortality_probability: np.float64
        """The rate of stem mortality per update interval."""
        self.canopy_top_radiation: NDArray[np.floating]
        """The downwelling radiation at the canopy top for the current time step."""
        self.subcanopy: Subcanopy
        """Representation of the subcanopy vegetation."""
        self.hydrology_constants: HydrologyConstants
        """Constants used by the Hydrology model."""
        self.soil_water_residual: float
        """Residual soil water limit for transpiration."""
        self.total_daily_water_demand: NDArray[np.floating]
        """The total daily water demand from transpiration when not water limited."""
        self.water_limitation_factor: NDArray[np.floating]
        """The limitation factor to GPP and transpiration when water demand cannot be
        met from soil moisture."""
        self.data_object_templates: dict[str, xr.DataArray]
        """DataArray templates for the data object."""

        # Set the exporter - this is always set _regardless_ of the static mode.
        self.exporter: CommunityDataExporter = exporter
        """A CommunityDataExporter instance providing configuration and methods for
        export of community data."""

        self.cohort_id_generator = cohort_id_generator(mode="str")
        # Initialise the cohort generator.

        # Run the setup if the model is not in deep static mode
        if self._run_setup:
            self._setup(
                flora=flora,
                cohort_data=cohort_data,
                model_constants=model_constants,
                pyrealm_config=pyrealm_config,
                hydrology_constants=hydrology_constants,
            )

    def _setup(
        self,
        flora: Flora,
        cohort_data: pandas.DataFrame,
        model_constants: PlantsConstants = PlantsConstants(),
        pyrealm_config: PyrealmConfig = PyrealmConfig(),
        hydrology_constants: HydrologyConstants = HydrologyConstants(),
    ) -> None:
        """Setup implementation for the Plants Model.

        See __init__ for argument descriptions.
        """

        # Set the instance attributes from the __init__ arguments
        self.flora = flora
        self.model_constants = model_constants
        self.hydrology_constants = hydrology_constants

        # Adjust flora rates to timestep
        # TODO: This is kinda hacky because the Flora instances is a frozen dataclass,
        #       but we only bring the model timing and flora object together at this
        #       point. We would have to pass the model timing in to the flora creation.
        #       Potentially create a Flora.adjust_rate_timing() method, but we'd need to
        #       be sure that the approach is sane first.

        # Respiration rates are expressed as proportions of masses per year so need to
        # be reduced proportionately to the number of updates per year
        updates_per_year = self.model_timing.updates_per_year
        for resp_rate in ["resp_f", "resp_r", "resp_s", "resp_rt"]:
            setattr(
                self.flora,
                resp_rate,
                [v / updates_per_year for v in getattr(self.flora, resp_rate)],
            )

        # Turnover rates are implemented as the number of years required to completely
        # turnover foliage/roots etc and are included in equations as the reciprocal of
        # the values. So rescaling them to shorter timescales requires that we
        # _increase_ the values proportionally to the reduced time between updates.
        for turnover_rate in ["tau_f", "tau_r", "tau_rt", "tau_f_base"]:
            setattr(
                self.flora,
                turnover_rate,
                [v * updates_per_year for v in getattr(self.flora, turnover_rate)],
            )

        # Now build the communities with the updated rates
        self.communities = PlantCommunities(
            cohort_data=cohort_data,
            flora=self.flora,
            grid=self.grid,
            cohort_id_generator=self.cohort_id_generator,
        )

        # HACK pyrealm3: Initialise the non-pyrealm biomasses by setting additional
        #      attributes on the community allometries.
        for cmty in self.communities.values():
            # Partition reproductive tissue allocation into fruit and seed masses
            cmty.stem_allometry.fruit_mass, cmty.stem_allometry.seed_mass = (
                partition_reproductive_tissue_mass(
                    cohorts=cmty.cohorts,
                    mass=cmty.stem_allometry.foliage_mass
                    * cmty.cohorts["p_foliage_for_reproductive_tissue"].to_numpy(),
                )
            )

        # Define the set of tissues to be tracked for each stem.
        self.biomass_tissues = [
            FoliageBiomass,  # foliage mass
            StemBiomass,  # stem mass
            RootBiomass,  # fine root mass
            FruitBiomass,  # fruit tissue mass
            SeedBiomass,  # seed tissue mass
        ]

        # Record the per stem biomasses of stochiometric tissues for each cohort.
        # The initial values for N and P are based on the ideal stoichiometric ratios
        # defined in the plant traits.
        self.biomasses = {
            cell_id: Biomasses.from_cohorts(
                cohorts=community.cohorts,
                allometry=community.stem_allometry,
                tissues=self.biomass_tissues,
            )
            for cell_id, community in self.communities.items()
        }

        # Check the pft propagules data Some development notes:
        # - This _could_ be an optional __init__ variable that defaults to zero, but we
        #   don't currently have optional __init__ variables.
        # - The axis name checking here is something that the axis validation in data
        #   loading should do, but the information (PFT names) needed to validate it
        #   there is not part of the core configuration, so even when we pass
        #   CoreComponents to the axis validation it won't be available (unless we
        #   duplicate that information as part of the core, which might not be the
        #   maddest thing ever).

        # Does the propagule data have PFT coordinates
        if "pft" not in self.data["plant_pft_propagules"].coords:
            raise InitialisationError(
                "The plant_pft_propagules data is missing 'pft' coordinates."
            )

        # Do the PFT coordinate values match the flora?
        if not set(self.data["plant_pft_propagules"]["pft"].data) == set(
            flora.pft_name
        ):
            raise InitialisationError(
                "The 'pft' coordinates in the plant_pft_propagules data do not match "
                "the PFT names configured in the PlantsModel flora"
            )

        # Define xarray templates
        self.data_object_templates = {
            "cnp_pft": xr.DataArray(
                data=np.zeros((self.grid.n_cells, len(self.flora.pft_name), 3)),
                coords={
                    "cell_id": self.data["cell_id"],
                    "pft": list(self.flora.pft_name),
                    "element": ["C", "N", "P"],
                },
            ),
            "cnp": xr.DataArray(
                data=np.zeros((self.grid.n_cells, 3)),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
            "cell": xr.zeros_like(self.data["elevation"]),
            "pft": xr.DataArray(
                data=np.zeros((self.grid.n_cells, len(self.flora.pft_name))),
                coords={
                    "cell_id": self.data["cell_id"],
                    "pft": list(self.flora.pft_name),
                },
            ),
        }

        # Initialize the various tissue arrays structured by PFT. These are used to pass
        # aggregate biomass summaries per PFT out to other other models
        vars_to_initialize = [
            # Canopy biomasses
            "canopy_foliage_cnp",
            "canopy_seed_cnp",
            "canopy_fruit_cnp",
            # Turnover biomasses
            "fallen_fruit_cnp",
            "fallen_seeds_cnp",
            "foliage_turnover_cnp",
            "seed_turnover_cnp",
            "fruit_turnover_cnp",
            "root_turnover_cnp",
            "stem_turnover_cnp",
            # Biomass consumption pools
            "canopy_foliage_cnp_consumed",
            "canopy_seed_cnp_consumed",
            "canopy_fruit_cnp_consumed",
            "fallen_seeds_cnp_consumed",
            "fallen_fruit_cnp_consumed",
        ]
        for var_name in vars_to_initialize:
            self.data[var_name] = self.data_object_templates["cnp_pft"].copy()

        # Initialise tissue arrays that do not have PFT structure.
        vars_to_initialize = [
            "subcanopy_vegetation_cnp_consumed",
            "subcanopy_seedbank_cnp_consumed",
        ]
        for var_name in vars_to_initialize:
            self.data[var_name] = self.data_object_templates["cnp"].copy()

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
        self.growth_increments = {}

        # Set pyrealm configuration
        self.pyrealm_pmodel_consts = pyrealm_config.pmodel
        self.pyrealm_core_consts = pyrealm_config.core

        # Create and populate the canopy data layers
        self.update_canopy_layers()

        # Initialise the subcanopy vegetation class and then set the light capture of
        # the subcanopy vegetation
        self.subcanopy = Subcanopy(
            data=self.data,
            pyrealm_core_constants=self.pyrealm_core_consts,
            model_constants=self.model_constants,
            layer_index=self.layer_structure.index_surface_scalar,
            model_timing=self.model_timing,
            data_object_template=self.data_object_templates["cnp"],
        )

        # The (constant) lignin proportions of each plant biomass pool are now populated
        # (based on the plant constants)
        self.populate_lignin_proportions()

        # Get the canopy top shortwave downwelling radiation for the first time slice
        self.set_canopy_top_radiation(time_index=0)

        # This updates the data fapar and lai values of the surface layer using the
        # subcanopy vegetation
        self.subcanopy.set_light_capture(
            below_canopy_light_fraction=self.below_canopy_light_fraction
        )

        # Set the shortwave absorption profile down to the ground
        self.set_shortwave_absorption()

        # Initialise other attributes
        self.per_stem_gpp = {}
        self.per_stem_transpiration = {}
        self.filled_canopy_mask = np.full(
            (self.layer_structure.n_layers, self.grid.n_cells), False
        )

        # Calculate the per update interval stem mortality and recruitment rates from
        # the annual values
        self.per_update_interval_stem_mortality_probability = 1 - (
            1 - model_constants.per_stem_annual_mortality_probability
        ) ** (1 / self.model_timing.updates_per_year)

        self.per_update_interval_propagule_recruitment_probability = 1 - (
            1 - model_constants.per_propagule_annual_recruitment_probability
        ) ** (1 / self.model_timing.updates_per_year)

        # Calculate the residual soil water limit in mm (currently a global value) as
        # the product of the depth of the first subsoil layer in mm and the hydrology
        # soil moisture residual constant.
        #
        # NOTE: The current bucket hydrology model expects all uptake to be from the
        # second soil layer (first below surface soil) but this could change in future
        # to include deeper layers (see #1771)
        self.soil_water_residual = (
            self.layer_structure.soil_layer_thickness[1]
            * 1000
            * self.hydrology_constants.soil_moisture_residual
        ).item()

        # Run the community data exporter
        # - the stem allocations and growth increments are empty dictionaries.
        self.exporter.dump(
            communities=self.communities,
            biomasses=self.biomasses,
            canopies=self.canopies,
            stem_allocations=self.stem_allocations,
            growth_increments=self.growth_increments,
            time=self.model_timing.start_time,
            time_index=0,
        )

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
    ) -> PlantsModel:
        """Factory function to initialise a plants model from configuration.

        This function returns a PlantsModel instance based on the provided configuration
        and data, raising an exception if the configuration is invalid.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
        """

        # Extract subconfigurations from the complete compiled configuration.
        model_configuration: PlantsConfiguration = configuration.get_subconfiguration(
            "plants", PlantsConfiguration
        )
        core_configuration: CoreConfiguration = configuration.get_subconfiguration(
            "core", CoreConfiguration
        )
        hydrology_configuration: HydrologyConfiguration = (
            configuration.get_subconfiguration("hydrology", HydrologyConfiguration)
        )

        # Generate the flora
        flora = get_flora_from_config(config=model_configuration)

        # Load the initial cohort data - use of FILEPATH_PLACEHOLDER guarantees that
        # this path has been set and exists.
        try:
            with open(model_configuration.cohort_data_path) as csv_data:
                cohort_data = pandas.read_csv(csv_data)
        except pandas.errors.ParserError as excep:
            msg = "Plant configuration error: cannot parse cohort data " + str(excep)
            LOGGER.error(msg)
            raise InitialisationError(msg)

        # Create a CommunityDataExporter instance from config
        exporter = CommunityDataExporter.from_config(
            output_directory=core_configuration.data_output_options.out_path,
            config=model_configuration.community_data_export,
        )

        # Try and create the instance - safeguard against exceptions from __init__
        try:
            inst = cls(
                data=data,
                core_components=core_components,
                static=model_configuration.static,
                flora=flora,
                cohort_data=cohort_data,
                model_constants=model_configuration.constants,
                exporter=exporter,
                pyrealm_config=core_configuration.pyrealm,
                hydrology_constants=hydrology_configuration.constants,
            )
        except Exception as excep:
            LOGGER.critical(
                f"Error creating plants model from configuration: {excep!s}"
            )
            raise excep

        LOGGER.info("Plants model instance generated from configuration.")
        return inst

    def spinup(self) -> None:
        """Placeholder function to spin up the plants model."""

    def reset_update_vars(self) -> None:
        """Resets specified variables in the data object before each update."""

        # Initialize variables that hold one value per cell
        by_cell_vars = [
            "root_carbohydrate_exudation",
            "plant_symbiote_carbon_supply",
        ]
        for var in by_cell_vars:
            self.data[var] = self.data_object_templates["cell"].copy()

        # Initialize variables that are stored per cell and per element
        cnp_vars = [
            "stem_turnover_cnp",
            "root_turnover_cnp",
            "subcanopy_vegetation_litter_cnp",
            "subcanopy_vegetation_cnp",
            "subcanopy_seedbank_litter_cnp",
            "subcanopy_seedbank_cnp",
        ]
        for var in cnp_vars:
            self.data[var] = self.data_object_templates["cnp"].copy()

        # Initialize variables that are stored by cell x PFT x CNP
        pft_cnp_vars = [
            "canopy_foliage_cnp",
            "canopy_seed_cnp",
            "canopy_fruit_cnp",
            "foliage_turnover_cnp",
            "seed_turnover_cnp",
            "fruit_turnover_cnp",
        ]
        for var in pft_cnp_vars:
            self.data[var] = self.data_object_templates["cnp_pft"].copy()

        # Initialise transpiration array to collect per grid cell values
        self.data["transpiration"] = self.layer_structure.from_template("transpiration")

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

        self.reset_update_vars()

        # Apply mortality and recruitment to plant cohorts
        self.apply_mortality()
        self.apply_recruitment()

        # Update the stem allometry to reflect applied changes to stem diameter from the
        # previous time step and to add new cohorts
        self.update_allometry()

        # Get the canopy top shortwave downwelling radiation for the current time slice
        self.set_canopy_top_radiation(time_index=time_index)

        # Apply herbivory effects - this modifies the stem LAI and tau_f parameters, and
        # care needs to be taken about the sequencing of using the modified values - see
        # comments on downstream methods.
        self.apply_herbivory()

        # Update the canopy layer heights and set the canopy fAPAR values:
        # * The layer heights use the PPA model based on the crown area, so layer
        #   heights are not affected by decreased LAI from herbivory, which is what we
        #   want.
        # * However, the fAPAR is affected by reduced LAI by herbivory, which is again
        #   what we want since more light penetrates down though the canopy.
        self.canopies = calculate_canopies(
            communities=self.communities,
            max_canopy_layers=self.layer_structure.n_canopy_layers,
        )

        # Calculate the canopy light capture - this does use LAI to calculate the FAPAR
        # and so incorporates foliage loss due to herbivory.
        self.update_canopy_layers()

        # Calculate the light capture by the subcanopy
        self.subcanopy.set_light_capture(
            below_canopy_light_fraction=self.below_canopy_light_fraction
        )

        # Use the FAPAR across the canopy and subcanopy to calculate an absorption
        # profile
        self.set_shortwave_absorption()

        # Estimate the canopy light use efficiency given the current abiotic conditions.
        self.calculate_light_use_efficiency()

        # Calculate the GPP across the canopy layers for each cohort and combine to give
        # a single aggregate estimate of GPP and resulting transpiration per stem
        self.estimate_gpp(time_index=time_index)

        # Similarly estimate GPP and transpiration for the subcanopy
        self.subcanopy.estimate_gpp(pmodel=self.pmodel, swd=self.canopy_top_radiation)

        # Apply water limitation
        self.calculate_daily_water_demand()
        self.apply_water_limitation()

        # Calculate uptake from each inorganic soil nutrient pool
        self.calculate_nutrient_uptake()

        # Allocate GPP, calculating changes in biomass and turnover and applying changes
        # to stem diameter to capture growth. This function uses the foliage turnover
        # trait (tau_f), modified by apply_herbivory above, to account for carbon costs
        # of folivory.
        self.allocate_gpp()

        # Update the fallen fruits and seeds pools
        self.update_fallen_pools()

        # Calculate the subcanopy vegetation dynamics
        self.subcanopy.calculate_dynamics()

        # Run the community data exporter
        self.exporter.dump(
            communities=self.communities,
            biomasses=self.biomasses,
            canopies=self.canopies,
            stem_allocations=self.stem_allocations,
            growth_increments=self.growth_increments,
            time=self.model_timing.update_datestamps[time_index],
            time_index=time_index,
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
            # Handle empty canopies
            # - At the moment pyrealm does not handle canopies from no cohorts in the
            #   cell (represented as None) and handles canopies from cohorts with no
            #   individuals by reporting zero layer heights. These two pathways should
            #   be synchronised in a future pyrealm release.
            # - Of note, empty pyrealm canopies from cohorts with no
            #   individuals. The canopy max height is defined by the hypothetical
            #   maximum size of the trees of which there no individuals - which is
            #   misleading to say the least.

            # If canopy height data is present then fill in the appropriate layers,
            # otherwise leave the cell with NA data.
            if canopy is not None and canopy.heights.size > 0:
                # Array indices of filled layers in this cell
                fill_idx = (slice(0, canopy.heights.size), (cell_id,))

                # Create a column array to insert layer heights, including
                # - the top of the canopy (maximum stem height)
                # - the layer closure heights (if any), rotated into a column array,
                #   omitting the final layer, which is the ground.
                heights[fill_idx] = np.concatenate(
                    [
                        [[canopy.max_stem_height]],
                        canopy.heights[0:-1, None],
                    ]
                )

                # Similarly, insert canopy fapar:
                fapar[fill_idx] = canopy.community_data.average_layer_fapar[:, None]

                # Calculate the per stem leaf mass:
                # * (stem leaf area * (1/sigma) * L) * n_indviduals to give total cohort
                #   mass per layer within the cell.
                # * Cohort traits need to be converted from pandas.Series to row array
                #   to broadcast across columns of stem leaf area
                cohort_leaf_mass_per_layer = (
                    canopy.cohort_data.stem_leaf_area
                    * (1 / community.cohorts["sla"].to_numpy())
                    * community.cohorts["lai"].to_numpy()
                ) * community.cohorts["n_individuals"].to_numpy()

                mass[fill_idx] = cohort_leaf_mass_per_layer.sum(axis=1, keepdims=True)

                # LAI - insert community average LAI values from light capture model
                lai[fill_idx] = canopy.community_data.average_layer_lai[:, None]

        # Insert the canopy layers into the data objects
        self.data["layer_heights"][self._canopy_layer_indices, :] = heights
        self.data["leaf_area_index"][self._canopy_layer_indices, :] = lai
        self.data["layer_fapar"][self._canopy_layer_indices, :] = fapar
        self.data["layer_leaf_mass"][self._canopy_layer_indices, :] = mass

        # Add the above canopy reference height, handling np.nan in first row when
        # the canopy is empty.
        self.data["layer_heights"][self.layer_structure.index_above, :] = np.where(
            np.isnan(heights[0, :]),
            self.layer_structure.above_canopy_height_offset,
            heights[0, :] + self.layer_structure.above_canopy_height_offset,
        )

        # Update the filled canopy layers
        self.layer_structure.set_filled_canopy(canopy_heights=heights)

        # Update the below canopy light fraction, handling cells with no canopy
        # Note - dual path here: no cohorts = None, extinct cohorts have defined
        # transmission of 1.
        self.below_canopy_light_fraction = np.array(
            [
                1 if cnpy is None else cnpy.community_data.transmission_to_ground
                for cnpy in self.canopies.values()
            ]
        )

        # Update the internal canopy layer mask
        self.filled_canopy_mask = np.logical_not(np.isnan(self.data["layer_leaf_mass"]))

        LOGGER.info(
            f"Updated canopy data on {self.layer_structure.index_filled_canopy.sum()}"
        )

    def set_canopy_top_radiation(self, time_index: int) -> None:
        """Set the current canopy top shortwave downwelling radiation."""

        self.canopy_top_radiation = (
            self.data["downward_shortwave_radiation"]
            .isel(time_index=time_index)
            .to_numpy()
        )

    def apply_herbivory(self) -> None:
        r"""Applies herbivory effects on the plants model.

        Herbivory removes biomass from the biomass tissues. In the case of foliage
        herbivory, this also impacts the light gathering of the canopy and effects the
        allocation of carbon to replacing lost leaves, assuming the plant prioritises
        the maintenance of canopy area during allocation of GPP.

        The impacts on light gathering are modelled by decreasing the LAI of the cohort
        to reflect the decrease in expected foliage mass (:math:`W_f`) given the mass of
        foliage removed by herbivory (:math:`H_f`). The model assumes a constant rate of
        herbivory, such that the average realised leaf mass over a time step is:

        .. math::

            \tilde{W_f} = W_f - H_f / 2

        The original expected foliage mass is calculated, given the crown area
        (:math:`A_c`), LAI (:math:`L`) and specific leaf area (:math:`\sigma`) as:

        .. math::

            W_f = (A_c L) / \sigma

        Hence the realised LAI given herbivory can be calculated as:

        .. math::

            \tilde{L} = (\tilde{W_f}  \sigma) / A_c

        The increased carbon cost of leaf replacement can be rolled into the standard
        foliage turnover costs by increasing the foliage turnover rate (:math:`\tau_f`).
        This increases turnover costs and hence reduces the amount of carbon available
        for stem growth.

        .. math::

            \tilde{\tau_f} = \frac{W_f \tau_f}{H_f \tau_f + W_f}


        .. todo::

            There is a timing issue here - the effects of herbivory in the last time
            step are being used to modify the light gathering and leaf turnover costs
            for the current plants timestep.

        """

        for cell_id in self.grid.cell_id:
            community: Community = self.communities[cell_id]
            biomasses: Biomasses = self.biomasses[cell_id]

            # 1. Reduce biomasses following herbivory - need to distribute the aggregate
            #    herbivory per PFT within each cell across the cohorts within the cell.

            for herbivory_tissue in ("fruit", "seed", "foliage"):
                # Get the tissue
                tissue = biomasses.get_tissue(herbivory_tissue)
                # Get the relative carbon biomass of each cohort within its PFT
                relative_herbivory = tissue.get_relative_carbon_biomass_by_pft(
                    cohorts=community.cohorts
                )

                # Extract the herbivory for this cell, broadcasts the total PFT
                # herbivory out to each cohort and then scale by the relative per PFT
                # biomass of cohorts to distribute the herbivory between cohorts.
                herbivory_by_cohort = (
                    self.data[f"canopy_{herbivory_tissue}_cnp_consumed"].sel(
                        cell_id=cell_id, pft=community.cohorts["pft_name"].to_numpy()
                    )
                    * relative_herbivory[:, np.newaxis]
                )

                # Apply the per cohort herbivory to the tissue
                tissue.apply_herbivory(herbivory_by_cohort)

            # 2. Decrease LAI to account for herbivory effects on light gathering. This
            #    assumes that the herbivory is at a constant rate through the time step
            #    so that the canopy is _on average_ missing half of the consumed mass.

            #    NOTE: The foliage mass here should be the expected foliage mass without
            #          herbivory, which is calculated as part of the stem allometry from
            #          the LAI, crown area and SLA. The code here modifies the LAI for
            #          use in calculating light penetration, but the LAI must be
            #          restored before the allometry is recalculated for the next step.
            foliage_carbon_loss = herbivory_by_cohort.sel(element="C").to_numpy()
            average_foliage_mass = (
                community.stem_allometry.foliage_mass - foliage_carbon_loss / 2
            )

            # Note here that LAI is calculated reset to the PFT standard before the
            # stem allocation is next calculated
            community.cohorts["lai"] = (
                (average_foliage_mass * community.cohorts["sla"])
                / community.stem_allometry.crown_area
            ).squeeze()

            # 3. Increase leaf turnover to account for herbivory replacement costs
            #    within T model
            community.cohorts["tau_f"] = (
                (community.stem_allometry.foliage_mass * community.cohorts["tau_f"])
                / (
                    foliage_carbon_loss * community.cohorts["tau_f"]
                    + community.stem_allometry.foliage_mass
                )
            ).squeeze()

    def set_shortwave_absorption(self) -> None:
        """Set the shortwave radiation absorption across the vertical layers.

        This method takes the shortwave radiation at the top of the canopy for a
        particular time index and uses the ``layer_fapar`` data calculated by the canopy
        and subcanopy models to estimate the amount of radiation absorbed by each canopy
        layer and the remaining radiation absorbed by the top soil layer.

        The method requires that the ``canopy_top_radiation`` attribute has been set
        with the SWD values for the current time step.

        TODO:
          - With the full canopy model, this could be partitioned into sunspots
            and shade.
        """  # noqa: D405

        # Set the ground_incident light
        self.ground_incident_light_fraction = (
            self.below_canopy_light_fraction * self.subcanopy.light_transmission
        )

        # Calculate the fate of shortwave radiation through the layers assuming that the
        # vegetation fAPAR applies to all light wavelengths
        absorbed_irradiance = self.data["layer_fapar"] * self.canopy_top_radiation

        # Add the remaining irradiance at the surface layer level
        absorbed_irradiance[self.layer_structure.index_topsoil] = (
            self.canopy_top_radiation * self.ground_incident_light_fraction
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
        #
        # The pressure and VPD variables are saved as kPa and so need to be scaled here
        # for use with pyrealm.
        pmodel_env = PModelEnvironment(
            tc=self.data["air_temperature"].to_numpy(),
            vpd=self.data["vapour_pressure_deficit"].to_numpy() * 1000,
            patm=self.data["atmospheric_pressure"].to_numpy() * 1000,
            co2=self.data["atmospheric_co2"].to_numpy(),
            core_const=self.pyrealm_core_consts,
            pmodel_const=self.pyrealm_pmodel_consts,
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
        canopy_top_ppfd = self.canopy_top_radiation * self.model_constants.dsr_to_ppfd

        # Reset the transpiration data
        self.data["transpiration"][:] = np.nan

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

            # Handle cells with no canopy. Using continue here leaves the transpiration
            # values for the cell as np.nan
            if canopy is None:
                # The .per_stem_gpp and .per_stem_transpiration dictionaries for the
                # cell is filled with an empty array. Once we have a better handle on
                # empty community structure this needs to be resolved.
                self.per_stem_gpp[cell_id] = np.array([])
                self.per_stem_transpiration[cell_id] = np.array([])
                continue

            # Get cohort data into vertical structure - the cohort canopy data only
            # contains occupied layers - so for example a block of 3 canopy layers by 4
            # cohorts. For the multiplication by the cell_id column array, we need it to
            #  match the vertical array structure. So we zero pad the array along the
            #  vertical axis with one above for the above canopy layer and then
            #  n_layers_below_canopy gives the remaining number of layers below.
            n_layers_below_canopy = (
                self.layer_structure.n_layers - len(canopy.heights) - 1
            )
            padding = ((1, n_layers_below_canopy), (0, 0))
            # Pad fapar and stem leaf area along vertical (first) axis.
            fapar = np.pad(canopy.cohort_data.fapar, padding)
            stem_leaf_area = np.pad(canopy.cohort_data.stem_leaf_area, padding)

            # GPP for each layer is estimated as (value, dimensions, units):
            #    LUE                (n_layers, 1)           [gC mol-1]
            #    * cohort fAPAR     (n_layers, n_cohorts)   [-]
            #    * canopy top PPFD  scalar                  [µmol m-2 s-1]
            #    * stem leaf area   (n__layers, n_cohorts)  [m2]
            #    * time elapsed     scalar                  [s]
            # Units:
            #    g C mol-1 * (-) * µmol m-2 s-1 * m2 * s = µg C

            per_layer_gpp = (
                self.pmodel.lue[:, [cell_id]]
                * fapar
                * canopy_top_ppfd[cell_id]
                * stem_leaf_area
                * self.model_timing.update_interval_seconds
            )

            # Mask all nans with zero. This includes all unoccupied canopy layers, but
            # also patches canopy conditions where GPP is not estimable using the P
            # Model (where m <= c*, see
            # https://pyrealm.readthedocs.io/en/stable/api/pmodel_api.html#pyrealm.pmodel.jmax_limitation.JmaxLimitationWang17)
            per_layer_gpp = np.nan_to_num(per_layer_gpp)

            # Calculate and store whole stem GPP in kg C
            self.per_stem_gpp[cell_id] = per_layer_gpp.sum(axis=0) * 1e-9

            # The per layer transpiration associated with that GPP then needs GPP in
            # moles of Carbon  (GPP in µg C / (Molar mass carbon * 1e6))):
            #   GPP in mols   (n_layer, n_cohorts)  [mol C]
            #   * IWUE        (n_layer, 1)          [µmol mol -1]
            # Units:
            #    mol C  * µmol H2O mol C -1 = µmol H2O
            per_layer_transpiration_micromolar = (
                per_layer_gpp / (self.pyrealm_core_consts.k_c_molmass * 1e6)
            ) * self.pmodel.iwue[:, [cell_id]]

            # Convert to mm
            per_layer_transpiration_mm = convert_water_moles_to_mm(
                water_moles=per_layer_transpiration_micromolar * 1e-6,
                tc=self.pmodel.env.tc[:, [cell_id]],
                patm=self.pmodel.env.patm[:, [cell_id]],
                core_const=self.pyrealm_core_consts,
            )

            # Calculate and store total stem transpiration in mm per stem
            self.per_stem_transpiration[cell_id] = np.nansum(
                per_layer_transpiration_mm, axis=0
            )

            # Calculate the total transpiration per layer in m2 in mm, replacing
            # unfilled canopy cells with np.nan. Note that this does not replace
            # non-estimable GPP with np.nan: those stay as zero.
            self.data["transpiration"][:, cell_id] = np.where(
                self.filled_canopy_mask[:, cell_id],
                (
                    community.cohorts["n_individuals"].to_numpy()
                    * per_layer_transpiration_mm
                ).sum(axis=1),
                np.nan,
            )

    def calculate_daily_water_demand(self) -> None:
        """Calculates the water demand from transpiration.

        The method calculates the total daily water demand in mm from transpiration in
        both the canopy and subcanopy.
        """

        total_canopy_demand = np.zeros(self.grid.n_cells)

        for cell_id, cmty in self.communities.items():
            total_canopy_demand[cell_id] = (
                self.per_stem_transpiration[cell_id]
                * cmty.cohorts["n_individuals"].to_numpy()
            ).sum()

        # Calculate per cell limitation factor as available water over total daily
        # demand, capping at 1. Note that that this uses an explicit integer number of
        # days to match the definition of the `days` parameter scaling
        self.total_daily_water_demand = (
            total_canopy_demand + self.subcanopy.subcanopy_transpiration
        ) / np.floor(
            self.model_timing.update_interval_seconds
            / self.core_constants.seconds_to_day
        )

    def apply_water_limitation(self) -> None:
        """Apply water limitation to canopy and subcanopy growth.

        This method compares the total water demand in cells to the plant accessible
        soil moisture. If the total water demand exceeds the available water, it
        calculates a soil moisture limitation factor as the simple ratio of
        available water over total demand. This factor is then applied to per stem
        GPP and transpiration estimates and to subcanopy GPP and transpiration.
        """

        # NOTE: The current bucket hydrology model expects all uptake to be from the
        # first subsoil layer (below surface soil) but this could change in future
        # to include deeper layers (see #1771)

        water_limitation_factor = np.minimum(
            1,
            (
                self.data["soil_moisture"]
                .sel(
                    layers=np.argmax(self.layer_structure.index_subsoil)
                )  # 1st subsoil layer
                .to_numpy()
                - self.soil_water_residual
            )
            / self.total_daily_water_demand,
        )

        # Apply limitation
        # - Reduce subcanopy transpiration and productivity
        self.subcanopy.subcanopy_transpiration *= water_limitation_factor
        self.subcanopy.subcanopy_gpp *= water_limitation_factor

        # - Reduce canopy transpiration and productivity
        for cell_id in self.communities.keys():
            self.per_stem_transpiration[cell_id] *= water_limitation_factor[cell_id]
            self.per_stem_gpp[cell_id] *= water_limitation_factor[cell_id]

        # - Reduce resulting transpiration demands in data
        self.data["transpiration"] *= water_limitation_factor

        # Store attribute
        self.water_limitation_factor = water_limitation_factor

    def allocate_gpp(self) -> None:
        """Calculate the allocation of GPP to growth and respiration.

        This method uses the T Model to estimate the allocation of plant gross
        primary productivity to respiration, growth, maintenance and turnover costs.
        The method then simulates growth by increasing dbh and calculates leaf and root
        turnover values.
        """

        for cell_id in self.communities.keys():
            community = self.communities[cell_id]
            cohorts = community.cohorts
            biomasses = self.biomasses[cell_id]

            # Calculate the allocation of GPP in kgC m2 per stem, since the T Model is
            # calibrated using per kg values.
            stem_allocation = StemAllocation(
                cohorts=community.cohorts,
                allometry=community.stem_allometry,
                whole_crown_gpp=self.per_stem_gpp[cell_id],
            )

            # Calculate carbon available for growth increment and other uses.
            unallocated_carbon = stem_allocation.npp - (
                stem_allocation.branch_turnover
                + stem_allocation.fine_root_turnover
                + stem_allocation.foliage_turnover
            )

            # Calculate carbon costs of fruit
            reproductive_tissue_mass = (
                community.stem_allometry.foliage_mass
                * cohorts["p_foliage_for_reproductive_tissue"].to_numpy()
            )
            reproductive_tissue_respiration = (
                reproductive_tissue_mass * cohorts["resp_rt"].to_numpy()
            )
            reproductive_tissue_turnover = reproductive_tissue_mass * (
                1 / cohorts["tau_rt"].to_numpy()
            )

            # HACK pyrealm3 - again, passing in reproductive tissue mass as a extra
            #      attribute on the increment object
            stem_allocation.fruit_turnover, stem_allocation.seed_turnover = (
                partition_reproductive_tissue_mass(
                    cohorts=cohorts, mass=reproductive_tissue_turnover
                )
            )

            self.stem_allocations[cell_id] = stem_allocation

            # Per stem carbon costs of root exudates
            symbiote_allocation = (
                unallocated_carbon * cohorts["gpp_topslice"].to_numpy()
            )

            # Calculate carbon available for growth
            growth_carbon = unallocated_carbon - (
                reproductive_tissue_turnover
                + reproductive_tissue_respiration
                + symbiote_allocation
            )

            # Calculate growth increments
            growth_increments = GrowthIncrements(
                cohorts=cohorts,
                allometry=community.stem_allometry,
                stem_allocation=stem_allocation,
                biomass_production=growth_carbon,
            )

            self.growth_increments[cell_id] = growth_increments

            # Assign change in fruit production with growth increment. Currently not
            # allocating new fruit production with growth, placeholder for when we do.
            growth_increments.delta_fruit_mass = np.zeros_like(
                growth_increments.delta_foliage_mass
            )
            growth_increments.delta_seed_mass = np.zeros_like(
                growth_increments.delta_foliage_mass
            )

            # GROW THE PLANTS by increasing the stem dbh
            #
            # HACK: The code below prevents stems shrinking to zero and below. This is
            #       temporary until we fix what happens with stem shrinkage and carbon
            #       starvation to something biological.
            #
            #       We could kill stems where the new D <=0 but adds loads of code and
            #       for the moment we just want to avoid passing pyrealm negative sizes.
            #       If the np.where is removed and this is set directly, then pyrealm
            #       will detect D <= 0 and raise an exception.
            #
            #       The problem with this hack is that it currently only
            #       targets the DBH, not the rest of the allocation so these turnover
            #       etc may still be based on shrinking tree values.

            new_dbh = (
                cohorts["dbh_value"].to_numpy() + growth_increments.delta_dbh.squeeze()
            )
            cohorts["dbh_value"] = np.where(
                new_dbh <= 0, cohorts["dbh_value"].to_numpy(), new_dbh
            )

            # HANDLE ALLOCATION TO TURNOVER:
            tissue_turnovers = biomasses.apply_turnover(allocation=stem_allocation)

            # Store turnover quantities for tissues aggregated across cohorts in the
            # data object:
            # * scale per stem quantities up to the number of individuals,
            # * sum across cohorts
            for aggregated_tissue in ("stem", "foliage", "root"):
                self.data[f"{aggregated_tissue}_turnover_cnp"][cell_id] += (
                    tissue_turnovers[aggregated_tissue]
                    * cohorts["n_individuals"].to_numpy()[:, None]
                ).sum(axis=0)

            # Expose biomasses that are affected by herbivory and which are currently
            # structured by PFT: foliage, seed and fruit
            #
            # Get boolean indices for each pft giving the columns of the cohort biomass
            # data that belong to the PFT.
            #
            # * The order of the PFTs in this list of indices matches the order of the
            #   PFT axis in self.data, so enumerate() over the sequence iterates over
            #   the PFT axis correctly.
            # * This also works when a PFT is not present - the resulting boolean column
            #   index just contains False, but using the index gives a (0, 3) array of
            #   cohorts by elements - and a sum can be taken across the 0 length
            #   dimension to give a total zero.
            cohort_pft_bool_idx = [
                cohorts["pft_name"] == pft for pft in self.flora.pft_name
            ]

            for by_pft_tissue in ("fruit", "seed", "foliage"):
                # Calculate the total turnover and standing biomass in each cohort
                total_turnover_biomass = (
                    tissue_turnovers[by_pft_tissue]
                    * cohorts["n_individuals"].to_numpy()[:, None]
                )
                total_standing_biomass = (
                    self.biomasses[cell_id].get_tissue(by_pft_tissue).elemental_masses
                    * cohorts["n_individuals"].to_numpy()[:, None]
                )

                for pft_idx, row_idx in enumerate(cohort_pft_bool_idx):
                    # Extract the cohorts for this PFT and sum across them and insert
                    # into xxx_turnover_cnp arrays
                    self.data[f"{by_pft_tissue}_turnover_cnp"][cell_id][pft_idx] = (
                        total_turnover_biomass[row_idx, :].sum(axis=0)
                    )

                    # Same but for the standing canopy biomass inserted into
                    # canopy_xxx_cnp arrays
                    self.data[f"canopy_{by_pft_tissue}_cnp"][cell_id][pft_idx] = (
                        total_standing_biomass[row_idx, :].sum(axis=0)
                    )

            # HANDLE ALLOCATION TO GROWTH

            biomasses.apply_growth(growth_increments=growth_increments)

            # TODO: capture propagules in canopy seedbank.

            # ALLOCATE GPP TO ACTIVE NUTRIENT PATHWAYS:
            # Allocate the symbiote carbon allocation to root exudates and active
            # nutrient pathways
            self.data["root_carbohydrate_exudation"][cell_id] = (
                self.convert_to_soil_units(
                    input_mass=np.sum(
                        symbiote_allocation
                        * cohorts["n_individuals"].to_numpy()
                        * self.model_constants.root_exudates
                    )
                )
            )

            self.data["plant_symbiote_carbon_supply"][cell_id] = (
                self.convert_to_soil_units(
                    input_mass=np.sum(
                        symbiote_allocation
                        * cohorts["n_individuals"].to_numpy()
                        * (1 - self.model_constants.root_exudates)
                    )
                )
            )

            # ASSIGN INCOMING NUTRIENTS FROM SYMBIOTES TO INDIVIDUALS
            # TODO - At the moment, the incoming nutrients from transpiration are added
            #        to the biomass surplus pools by the calculate_nutrient_uptake()
            #        step that precedes allocate_gpp in _update(). Might be clearer to
            #        bring it in here.
            # TODO - need to think here about the allocation model. The supplies should
            #        probably be proportional to relative contributions to the carbon
            #        supply rather than just distributed equally amongst all
            #        individuals.

            total_individuals = cohorts["n_individuals"].sum()
            cohort_not_empty = cohorts["n_individuals"] > 0
            symbiote_nutrients = np.zeros_like(biomasses.element_surpluses)

            for col_idx, element in ((1, "n"), (2, "p")):
                total_supply = float(
                    self.data["ectomycorrhizal_" + element + "_supply"][cell_id]
                    + self.data["arbuscular_mycorrhizal_" + element + "_supply"][
                        cell_id
                    ]
                )
                symbiote_nutrients[cohort_not_empty, col_idx] = (
                    total_supply / total_individuals
                )

            biomasses._adjust_surpluses(symbiote_nutrients)

            # BALANCE THE NUTRIENTS WITHIN BIOMASSES
            biomasses.balance_elements()

    def update_allometry(self) -> None:
        """Update the T model allometry of cohorts.

        This method is used to update the theoretical expectation of the stem
        allometry under the T model given any changes to the DBH of cohorts from
        growth. It also handles resetting LAI and foliage turnover rates - which may
        have been altered in the apply_herbivory method - to the default values for
        the PFT for each cohort.
        """

        for community in self.communities.values():
            # Reset LAI
            community.cohorts["lai"] = community.cohorts["lai_base"]

            # Reset tau_f
            community.cohorts["tau_f"] = community.cohorts["tau_f_base"]

            # Update community allometry with new dbh values
            community.stem_allometry = StemAllometry(cohorts=community.cohorts)

    def apply_mortality(self) -> None:
        """Apply mortality to plant cohorts.

        This function applies the basic annual mortality rate to plant cohorts. The
        mortality rate is currently a constant value for all cohorts. The function
        calculates the number of individuals that have died in each cohort and updates
        the cohort data accordingly.

        The function then transfers the biomasses of dead stems into tissue turnover
        pools.
        """

        # Loop over each grid cell
        for cell_id in self.communities.keys():
            community = self.communities[cell_id]
            cohorts = community.cohorts

            # Calculate the number of individuals that have died in each cohort
            mortality = np.random.binomial(
                cohorts["n_individuals"],
                self.per_update_interval_stem_mortality_probability,
            )

            if mortality.sum() > 0:
                # Decrease size of cohorts based on mortality
                cohorts["n_individuals"] = cohorts["n_individuals"] - mortality

                # Get the biomasses of the tissues in the dead stems
                biomasses_of_dead_stems = self.biomasses[cell_id]

                # Iterate over the tissues moving biomass into the turnover CNP arrays:
                # 1. For stem and root biomass multiply stem biomasses by the
                #    number of dead individuals and then sum across cohorts to give
                #    total aggregated elemental contributions:
                for aggregated_tissue in ("stem", "root"):
                    self.data[f"{aggregated_tissue}_turnover_cnp"][cell_id] += (
                        biomasses_of_dead_stems.get_tissue(
                            aggregated_tissue
                        ).elemental_masses
                        * mortality[:, None]
                    ).sum(axis=0)

                # 2. Fruit and seed biomasses are stored by PFT so need pooling by PFT.
                #    TODO - Some structural overlap here with allocate turnover in GPP.
                #           Can we share code here? Need a collapse_by_pft method?
                cohort_pft_bool_idx = [
                    cohorts["pft_name"] == pft for pft in self.flora.pft_name
                ]

                for by_pft_tissue in ("fruit", "foliage", "seed"):
                    # Calculate the total turnover and standing biomass in each cohort
                    total_turnover_biomass = (
                        biomasses_of_dead_stems.get_tissue(
                            by_pft_tissue
                        ).elemental_masses
                        * mortality[:, None]
                    )

                    for pft_idx, col_idx in enumerate(cohort_pft_bool_idx):
                        # Extract the cohorts for this PFT and sum across them and
                        # insert into xxx_turnover_cnp arrays
                        self.data[f"{by_pft_tissue}_turnover_cnp"][cell_id][pft_idx] = (
                            total_turnover_biomass[col_idx, :].sum(axis=0)
                        )

    def apply_recruitment(self) -> None:
        """Apply recruitment to plant cohorts.

        This function applies recruitment to plant cohorts, currently using a single
        recruitment rate across all plant functional types.
        """

        # Get the sequence of PFT names in the data array
        pft_sequence = self.data["plant_pft_propagules"]["pft"].to_numpy()

        # Get recruitment across all cells
        # TODO - swap out p with a per PFT trait array.
        recruitment = np.random.binomial(
            n=self.data["plant_pft_propagules"],
            p=self.per_update_interval_propagule_recruitment_probability,
        )

        # Remove recruitment from propagule pool.
        self.data["plant_pft_propagules"] -= recruitment

        # Loop over each grid cell
        for cell_id, community in self.communities.items():
            # Which PFTs have any recruitment in this community
            recruiting_pfts = recruitment[cell_id, :] > 0

            # If there is any recruitment, create a new set of Cohorts with a rubbish
            # guess at initial DBH values.
            #
            # TODO - We need to allocate the seed mass to growing a tiny tree.
            #        Probably that would be by using StemAllocation with an initial
            #        value of zero and a potential GPP equal to the seed mass, but
            #        the equations aren't defined for DBH=0. Not sure how to self
            #        start these, so using a 2mm DBH. Need a DBH given mass solver.
            n_recruiting = recruiting_pfts.sum()
            if n_recruiting:
                new_cohorts = create_cohorts(
                    flora=self.flora,
                    cid_generator=self.cohort_id_generator,
                    pft_name=pft_sequence[recruiting_pfts],
                    dbh_value=np.repeat(0.002, n_recruiting),
                    n_individuals=recruitment[cell_id, recruiting_pfts],
                )

                # Add recruited cohorts
                community.cohorts = pandas.concat([community.cohorts, new_cohorts])

                # NOTE - The step above implicitly keeps the community reference within
                #        the Biomasses objects up to date with recruitment and hence
                #        maintains the link between the number of cohorts in the
                #        community and the number of columns in the biomass arrays.
                #        This is terribly convenient but was utterly unplanned and is
                #        all sorts of fugly. If / when this code is updated, something
                #        needs to maintain this linkage.

                # Extend biomasses.
                # TODO - This currently uses initialisation from default ratios, but  it
                #        should use nutrients from the reproductive mass. One step at a
                #        time.
                new_community = Community(
                    cell_id=cell_id,
                    cell_area=community.cell_area,
                    flora=self.flora,
                    cohorts=new_cohorts,
                )

                # Set the reproductive tissue masses
                new_community.stem_allometry.fruit_mass = np.zeros(len(new_cohorts))
                new_community.stem_allometry.seed_mass = np.zeros(len(new_cohorts))

                new_biomasses = Biomasses.from_cohorts(
                    cohorts=new_community.cohorts,
                    allometry=new_community.stem_allometry,
                    tissues=self.biomass_tissues,
                )

                self.biomasses[cell_id].append(new_biomasses)

    def populate_lignin_proportions(self) -> None:
        """Populate lignin proportions of all the plant biomass pools.

        This function populates the lignin concentrations of each plant biomass pool.

        Warning:
            At present, this function literally just populates constant values for
            lignin, so this function is just called once during model initialise to
            create an array of constant values, which are then used for the rest of the
            model run.
        """

        # Lignin concentrations
        self.data["stem_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.stem_lignin
        )
        self.data["senesced_leaf_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.senesced_leaf_lignin
        )
        self.data["root_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.root_lignin
        )
        self.data["subcanopy_vegetation_litter_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.subcanopy_vegetation_lignin
        )
        self.data["subcanopy_seedbank_litter_lignin"] = xr.full_like(
            self.data["elevation"], self.model_constants.subcanopy_seedbank_lignin
        )

    def calculate_nutrient_uptake(self) -> None:
        """Calculate uptake of soil nutrients by the plant community.

        This function calculates the amount of inorganic nutrients(ammonium, nitrate,
        and labile phosphorus) taken up by plants from the soil, through transpiration.
        The function then assigns the N/P uptake values to the respective community
        through the Biomass class.
        """

        self.data["plant_ammonium_uptake"] = xr.full_like(
            self.data["dissolved_ammonium"], 0
        )
        self.data["plant_nitrate_uptake"] = xr.full_like(
            self.data["dissolved_nitrate"], 0
        )
        self.data["plant_phosphorus_uptake"] = xr.full_like(
            self.data["dissolved_phosphorus"], 0
        )

        for cell_id in self.communities.keys():
            # Calculate N/P uptake (g N/P per stem) due to transpiration. Multiply:
            # - Per stem transpiration (µmol H2O per stem)
            # - Conversion factor from µmol H2O to m^3 (1.08015*10^-11)
            # - Concentration of N/P uptake (kg m^-3)
            # - Kg to g (1000)
            # TODO: scale by atmospheric pressure and temperature (#927)
            ammonium_uptake = (
                self.data["dissolved_ammonium"][cell_id].item()
                * self.per_stem_transpiration[cell_id]
                * 1.8015e-11
                * 1000
            )
            nitrate_uptake = (
                self.data["dissolved_nitrate"][cell_id].item()
                * self.per_stem_transpiration[cell_id]
                * 1.8015e-11
                * 1000
            )
            phosphorous_uptake = (
                self.data["dissolved_phosphorus"][cell_id].item()
                * self.per_stem_transpiration[cell_id]
                * 1.8015e-11
                * 1000
            )

            # Add per-cell, per-plant uptake to the data object
            self.data["plant_ammonium_uptake"][cell_id] = sum(ammonium_uptake)
            self.data["plant_nitrate_uptake"][cell_id] = sum(nitrate_uptake)
            self.data["plant_phosphorus_uptake"][cell_id] = sum(phosphorous_uptake)

            # Add per-stem uptake to the biomass surplus pools
            self.biomasses[cell_id]._adjust_surpluses(
                np.stack(
                    [
                        np.zeros_like(phosphorous_uptake),  # No carbon
                        ammonium_uptake + nitrate_uptake,
                        phosphorous_uptake,
                    ],
                    axis=1,
                )
            )

    def update_fallen_pools(self) -> None:
        """Update the fallen seeds and fruit pools.

        This method calculates the new values for the pools based on the turnover of the
        input biomass (from the canopy plants) and the consumption of the pools by
        animals.

        Seeds are assumed not to decay if left unconsumed by animals. Fruit, however, do
        decay if left uneaten. This decay is applied to the fruit left after animal
        consumption has occurred, and the size of the depends on both the length of
        simulation time step and the average (soil surface) temperature across the
        previous timestep. The carbon, nitrogen and phosphorus from the decayed fruit is
        then added directly into the soil (bypassing the litter model).
        """

        # Seeds do not decay, so if they aren't eaten by animals they accumulate
        self.data["fallen_seeds_cnp"] += (
            self.data["seed_turnover_cnp"] - self.data["fallen_seeds_cnp_consumed"]
        )

        # Find the amount of fruit left after animal consumption
        post_consumption_fruit = (
            self.data["fallen_fruit_cnp"] - self.data["fallen_fruit_cnp_consumed"]
        )

        # Estimate the fraction of this remaining fruit that decays
        fraction_decayed = self.calculate_fallen_fruit_decay_fraction(
            decay_rate=self.model_constants.fallen_fruit_decay_rate,
            surface_temperature=self.data["air_temperature"][
                self.layer_structure.index_surface_scalar
            ],
        )
        fruit_decay = fraction_decayed * post_consumption_fruit

        # Find the pool size for the next time stop by adding new biomass and
        # subtracting decay
        self.data["fallen_fruit_cnp"] = (
            post_consumption_fruit + self.data["fruit_turnover_cnp"] - fruit_decay
        )

        # Update data object with total (summed across PFTs) decay into the soil model
        # (expressed as a rate per area)
        self.data["fallen_fruit_decay_cnp"] = fruit_decay.sum(dim="pft") / (
            self.grid.cell_area
            * self.model_timing.update_interval_quantity.to("days").magnitude
        )

    def calculate_fallen_fruit_decay_fraction(
        self, decay_rate: float, surface_temperature: xr.DataArray
    ) -> xr.DataArray:
        """Calculate fraction of fallen fruit that decays in a given timestep.

        The fraction of fruit (flesh) that has decayed is effected by two things: the
        length of the simulation time step, and the average (soil surface) temperature
        for this time step. We combine these into a single measure, degree days, which
        uses 0 Celsius as a basis, i.e. if temperatures are zero or below no decay will
        occur.

        Args:
            decay_rate: Rate at which fruit decays [Celsius^-1 day^-1]
            surface_temperature: Temperature of the forest floor [Celsius]

        Returns:
            The fraction of the fallen fruit that has decayed into the soil.
        """

        # Calculate the degree days (subzero temperatures are treated as zero)
        degree_days = np.where(
            surface_temperature >= 0.0,
            surface_temperature
            * (self.model_timing.update_interval_quantity.to("days").magnitude),
            0.0,
        )

        return xr.DataArray(1 - np.exp(-decay_rate * degree_days), dims="cell_id")

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
