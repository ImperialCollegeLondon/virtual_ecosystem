"""The :mod:`~virtual_ecosystem.models.plants.plants_model` module creates
:class:`~virtual_ecosystem.models.plants.plants_model.PlantsModel` class as a child of
the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
"""  # noqa: D205

from __future__ import annotations

from typing import Any

import numpy as np
import xarray as xr

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.canopy import (
    build_canopy_arrays,
    initialise_canopy_layers,
)
from virtual_ecosystem.models.plants.community import PlantCommunities
from virtual_ecosystem.models.plants.constants import PlantsConsts
from virtual_ecosystem.models.plants.functional_types import Flora


class PlantsModel(
    BaseModel,
    model_name="plants",
    model_update_bounds=("1 day", "1 year"),
    vars_required_for_init=(
        "plant_cohorts_cell_id",
        "plant_cohorts_pft",
        "plant_cohorts_n",
        "plant_cohorts_dbh",
        "photosynthetic_photon_flux_density",
    ),
    vars_populated_by_init=(
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_fapar",
        "layer_leaf_mass",  # NOTE - placeholder resource for herbivory
        "canopy_absorption",
    ),
    vars_required_for_update=(
        "plant_cohorts_cell_id",
        "plant_cohorts_pft",
        "plant_cohorts_n",
        "plant_cohorts_dbh",
        "photosynthetic_photon_flux_density",
    ),
    vars_updated=(
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_fapar",
        "layer_leaf_mass",  # NOTE - placeholder resource for herbivory
        "canopy_absorption",
        "evapotranspiration",
        "deadwood_production",
        "leaf_turnover",
        "plant_reproductive_tissue_turnover",
        "root_turnover",
        "deadwood_lignin",
        "leaf_turnover_lignin",
        "plant_reproductive_tissue_turnover_lignin",
        "root_turnover_lignin",
        "deadwood_c_n_ratio",
        "leaf_turnover_c_n_ratio",
        "plant_reproductive_tissue_turnover_c_n_ratio",
        "root_turnover_c_n_ratio",
        "deadwood_c_p_ratio",
        "leaf_turnover_c_p_ratio",
        "plant_reproductive_tissue_turnover_c_p_ratio",
        "root_turnover_c_p_ratio",
    ),
    vars_populated_by_first_update=(
        "evapotranspiration",
        "deadwood_production",
        "leaf_turnover",
        "plant_reproductive_tissue_turnover",
        "root_turnover",
        "deadwood_lignin",
        "leaf_turnover_lignin",
        "plant_reproductive_tissue_turnover_lignin",
        "root_turnover_lignin",
        "deadwood_c_n_ratio",
        "leaf_turnover_c_n_ratio",
        "plant_reproductive_tissue_turnover_c_n_ratio",
        "root_turnover_c_n_ratio",
        "deadwood_c_p_ratio",
        "leaf_turnover_c_p_ratio",
        "plant_reproductive_tissue_turnover_c_p_ratio",
        "root_turnover_c_p_ratio",
    ),
):
    """A class defining the plants model.

    This is currently a basic placeholder to define the main interfaces between the
    plants model and other models.

    When a model instance is created, the model attributes are validated and set.
    The initial canopy structure for each grid cell is then generated from provided
    plant cohort data using the
    :meth:`~virtual_ecosystem.models.plants.plants_model.PlantsModel.update_canopy_layers`
    method. This includes the irradiance absorbed within each canopy layer and reaching
    ground level, which at present is estimated using the first time step of the
    provided photosynthetic photon flux density (PPFD).

    When the model is updated, the P Model **will be** used to calculate the light use
    efficiency given the conditions within canopy layers, and the PPFD at the top of the
    canopy and the canopy layer extinction profile is used to estimate gross primary
    productivity across plant cohorts. An allocation model is then used to estimate
    growth and then update the canopy model.

    Required Variables:

        The following variables must be provided in the ``data`` instance to initialise
        an instance of this model:

        * ``plant_cohorts_cell_id``: The grid cell id containing the cohort
        * ``plant_cohorts_pft``: The plant functional type of the cohort
        * ``plant_cohorts_n``: The number of individuals in the cohort
        * ``plant_cohorts_dbh``: The diameter at breast height of the individuals in
          metres.
        * ``photosynthetic_photon_flux_density``: The above canopy photosynthetic photon
          flux density in µmol m-2 s-1.

    Warning:
        The current implementation defines the main interfaces between the plants model
        and other models and accesses and updates the expected data to be used in the
        full model. The actual predictions of the model are placeholder values.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        flora: A Flora instance of the plant functional types to be used in the model.
        model_constants: Set of constants for the plants model.
    """

    # TODO - think about a shared "plant cohort" core axis that defines the cohort
    #        initialisation  data, but the issue here is that the length of this is
    #        variable.

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
        flora = Flora.from_config(config=config)

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
        """Placeholder function to set up the plants model.

        Args:
            flora: A flora containing the plant functional types used in the plants
                model.
            model_constants: Set of constants for the plants model.
            **kwargs: Further arguments to the setup method.
        """

        # Save the class attributes
        self.flora = flora
        """A flora containing the plant functional types used in the plants model."""
        self.model_constants = model_constants
        """Set of constants for the plants model"""
        self.communities = PlantCommunities(self.data, self.flora)
        """Initialise the plant communities from the data object."""

        # Initialise and then update the canopy layers.
        # TODO - this initialisation step may move somewhere else at some point.
        self.data = initialise_canopy_layers(
            data=self.data,
            layer_structure=self.layer_structure,
        )
        """A reference to the global data object."""

        # This is widely used internally so store it as an attribute.
        self._canopy_layer_indices = self.layer_structure.index_canopy
        """The indices of the canopy layers within wider vertical profile"""

        # Run the canopy initialisation - update the canopy structure from the initial
        # cohort data and then initialise the irradiance using the first observation for
        # PPFD.
        self.update_canopy_layers()
        self.set_canopy_absorption(time_index=0)

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
        self.set_canopy_absorption(time_index=time_index)

        # Estimate the GPP and growth with the updated this update
        self.estimate_gpp(time_index=time_index)
        self.allocate_gpp()

        # Calculate the turnover of each plant biomass pool
        self.calculate_turnover()

    def cleanup(self) -> None:
        """Placeholder function for plants model cleanup."""

    def update_canopy_layers(self) -> None:
        """Update the canopy structure for the plant communities.

        This method calculates the canopy structure from the current state of the plant
        cohorts across grid cells and then updates four canopy layer variables in the
        the data object:

        * the layer closure heights (``layer_heights``),
        * the layer leaf area indices (``leaf_area_index``),
        * the fraction of absorbed photosynthetically active radation in each layer
          (``layer_fapar``), and
        * the whole canopy leaf mass within the layers (``layer_leaf_mass``), and

        * the absorbed irradiance in each layer, including the remaining incident
          radation at ground level (``canopy_absorption``).
        """
        # Retrive the canopy model arrays and insert into the data object.
        canopy_data = build_canopy_arrays(
            self.communities,
            n_canopy_layers=self.layer_structure.n_canopy_layers,
        )

        # Insert the canopy layers into the data objects
        self.data["layer_heights"][self._canopy_layer_indices, :] = canopy_data[0]
        self.data["leaf_area_index"][self._canopy_layer_indices, :] = canopy_data[1]
        self.data["layer_fapar"][self._canopy_layer_indices, :] = canopy_data[2]
        self.data["layer_leaf_mass"][self._canopy_layer_indices, :] = canopy_data[3]

        # Update the above canopy heights
        self.data["layer_heights"][0, :] = (
            self.data["layer_heights"][1, :]
            + self.layer_structure.above_canopy_height_offset
        )

    def set_canopy_absorption(self, time_index: int) -> None:
        """Set the absorbed irradiance across the canopy.

        This method takes the photosynthetic photon flux density at the top of the
        canopy for a particular time index and uses the ``layer_fapar`` data calculated
        by the canopy model to estimate the irradiance absorbed by each layer and the
        remaining irradiance at ground level.
        """

        # TODO: With the full canopy model, this could be partitioned into sunspots and
        #       shade.

        # Extract a PPFD time slice
        canopy_top_ppfd = (
            self.data["photosynthetic_photon_flux_density"]
            .isel(time_index=time_index)
            .data
        )

        # Calculate the fate of PPFD through the layers
        absorbed_irradiance = canopy_top_ppfd * self.data["layer_fapar"].data
        ground_irradiance = canopy_top_ppfd - np.nansum(absorbed_irradiance, axis=0)

        # Store the absorbed irradiance in the data object and add the remaining
        # irradiance at the surface layer level
        # NOTE - this is only the _PPFD_ at ground level not the SWDown.
        self.data["canopy_absorption"][:] = absorbed_irradiance
        ground = np.where(self.data["layer_roles"].data == "surface")[0]
        self.data["canopy_absorption"][ground] = ground_irradiance

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

        Warning:
            At present this method checks that the required forcing variables exist, but
            asserts a constant fixed light use efficiency rather than using the P Model.

        Args:
            time_index: The index along the time axis of the forcing data giving the
                time step to be used to estimate GPP.

        Raises:
            ValueError: if any of the P Model forcing variables are not defined.
        """

        # For the moment check the data presence and dimensionality
        # 1 ) PModelEnvironment vars
        forcing_vars = (
            "air_temperature",
            "vapour_pressure_deficit",
            "atmospheric_pressure",
            "atmospheric_co2",
        )

        # Loop over the P Model environment forcing variables, checking they are found
        for var in forcing_vars:
            if var not in self.data:
                msg = f"Variable missing from estimate_gpp: {var}"
                LOGGER.critical(msg)
                raise ValueError(msg)

        # # Next step will to calculate the PModelEnvironment and fit the PModel
        # pmodel_env = PModelEnvironment(
        #     tc = self.data["air_temperature"].isel(time=time_index).data
        #     vpd = self.data["vapour_pressure_deficit"].isel(time=time_index).data
        #     patm = self.data["atmospheric_pressure"].isel(time=time_index).data
        #     co2 = self.data["atmospheric_co2"].isel(time=time_index).data
        #     const = self.pmodel_consts
        # )
        # pmodel = PModel(pmodel_env)
        #
        # This will give an array of the light use efficiency per layer per cell,

        # Get an array where populated canopy layers are one otherwise nan
        filled_canopy = xr.where(
            (self.data["layer_heights"] * self._canopy_layer_indices[:, None]) > 0,
            1,
            np.nan,
        )

        # Set a representative place holder LUE in gC mol-1 for now
        self.data["layer_light_use_efficiency"] = filled_canopy * 0.3

        # The LUE can then be scaled by the calculated absorbed irradiance, which is
        # the product of the layer specific fapar and the downwelling PPFD. In practice,
        # this will use something like:
        #
        # pmodel.estimate_productivity(
        #     fapar=1, ppfd=self.data["canopy_absorption"]
        # )
        # but for now:

        self.data["layer_gpp_per_m2"] = (
            self.data["layer_light_use_efficiency"] * self.data["canopy_absorption"]
        )

        # We then have the gross primary productivity in µg C m-2 s-1 within each
        # canopy layer for each cell. This needs to be converted into the per stem GPP
        # for each cohort across the layers and scaled up from per second to the time
        # step.

        # TODO - this implementation isn't great. Need to think about whether Cohorts
        # are objects or whether Communities are a dataclass of arrays. Also need to
        # think about where the split between the virtual_ecosystem layer definition
        # (with above canopy/subcanopy/surface/soil) and the pyrealm canopy layer
        # definition occurs.

        # TODO - calculate time covered in update properly
        seconds_since_last_update = 30 * 24 * 60 * 60

        for cell_id, community in self.communities.items():
            # Extract the vertical slice for this cell and reduce to the canopy layers
            cell_gpp_per_m2 = (
                self.data["layer_gpp_per_m2"]
                .isel(cell_id=cell_id)
                .data[self._canopy_layer_indices]
            )
            for cohort in community:
                cohort.gpp = np.nansum(
                    cohort.canopy_area * cell_gpp_per_m2 * seconds_since_last_update
                )

        # Estimate evapotranspiration
        #  - currently just a placeholder for something more involved
        self.data["evapotranspiration"] = filled_canopy * 20

    def allocate_gpp(self) -> None:
        """Calculate the allocation of GPP to growth and respiration.

        This method will use the T Model to estimate the allocation of plant gross
        primary productivity to respiration, growth, maintenance and turnover costs.

        Warning:
            At present, this asserts a constant fixed increment in diameter at breast
            height, rather than calculating the actual predictions of the T Model.
        """

        for community in self.communities.values():
            for cohort in community:
                # arbitrarily use the ceiling of the gpp in kilos as a cm increase in
                # dbh to provide an annual increment that relates to GPP.
                cohort.dbh += np.ceil(cohort.gpp / (1e6 * 1e3)) / 1e2

    def calculate_turnover(self) -> None:
        """Calculate turnover of each plant biomass pool.

        This function calculates the turnover rate for each plant biomass pool (wood,
        leaves, roots, and reproductive tissues). As well as this the lignin
        concentration, carbon nitrogen ratio and carbon phosphorus ratio of each
        turnover flow is calculated.

        Warning:
            At present, this function literally just returns constant values for each of
            the variables it returns.
        """

        # All outputs are just constants at the moment
        self.data["deadwood_production"] = xr.full_like(self.data["elevation"], 0.075)
        self.data["leaf_turnover"] = xr.full_like(self.data["elevation"], 0.027)
        self.data["plant_reproductive_tissue_turnover"] = xr.full_like(
            self.data["elevation"], 0.003
        )
        self.data["root_turnover"] = xr.full_like(self.data["elevation"], 0.027)
        self.data["deadwood_lignin"] = xr.full_like(self.data["elevation"], 0.545)
        self.data["leaf_turnover_lignin"] = xr.full_like(self.data["elevation"], 0.05)
        self.data["plant_reproductive_tissue_turnover_lignin"] = xr.full_like(
            self.data["elevation"], 0.01
        )
        self.data["root_turnover_lignin"] = xr.full_like(self.data["elevation"], 0.2)
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
