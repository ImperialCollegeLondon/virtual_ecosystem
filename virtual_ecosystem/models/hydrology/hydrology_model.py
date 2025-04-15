"""The :mod:`~virtual_ecosystem.models.hydrology.hydrology_model` module
creates a
:class:`~virtual_ecosystem.models.hydrology.hydrology_model.HydrologyModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.

There are still a number of open TODOs related to process implementation and improvement
, time step and model structure, and units and module coordination.

.. TODO:: processes

    * spin up soil moisture and accumulated runoff
    * set boundaries for river discharge
    * update infiltration process
    * net radiation needs to be initialised here and included in hydro_input

.. TODO:: time step and model structure

    * find a way to load daily (precipitation) data and loop over daily time_index
    * allow for different time steps (currently only 30 days)
    * potentially move `calculate_drainage_map` to core
    * add abiotic constants from config

.. TODO:: units and module coordination

    * change temperature to Kelvin
    * plants need to return transpiration only

"""  # noqa: D205

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pint import Quantity
from pyrealm.constants import CoreConst as PyrealmConst
from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.hydrology import (
    above_ground,
    below_ground,
    hydrology_tools,
)
from virtual_ecosystem.models.hydrology.constants import HydroConsts


class HydrologyModel(
    BaseModel,
    model_name="hydrology",
    model_update_bounds=("1 day", "1 month"),
    vars_required_for_init=(
        "layer_heights",
        "elevation",
    ),
    vars_updated=(
        "canopy_evaporation",
        "precipitation_surface",
        "soil_moisture",
        "surface_runoff",
        "vertical_flow",
        "soil_evaporation",
        "surface_runoff_accumulated",
        "subsurface_flow_accumulated",
        "matric_potential",
        "groundwater_storage",
        "river_discharge_rate",
        "total_river_discharge",
        "subsurface_flow",
        "baseflow",
        "bypass_flow",
        "aerodynamic_resistance_surface",
    ),
    vars_required_for_update=(
        "air_temperature",
        "relative_humidity",
        "atmospheric_pressure",
        "vapour_pressure_deficit",
        "precipitation",
        "wind_speed",
        "leaf_area_index",
        "layer_heights",
        "soil_moisture",
        "evapotranspiration",  # TODO this needs to be transpiration
        "surface_runoff_accumulated",
        "subsurface_flow_accumulated",
        "density_air",
        "aerodynamic_resistance_canopy",
        "specific_heat_air",
        "stomatal_conductance",
    ),
    vars_populated_by_init=(
        "soil_moisture",
        "groundwater_storage",
        "surface_runoff_accumulated",
        "subsurface_flow_accumulated",
        "aerodynamic_resistance_surface",
        "aerodynamic_resistance_canopy",
        "specific_heat_air",
        "stomatal_conductance",
        "latent_heat_vapourisation",
        "density_air",
    ),
    vars_populated_by_first_update=(
        "precipitation_surface",
        "surface_runoff",
        "bypass_flow",
        "soil_evaporation",
        "vertical_flow",
        "matric_potential",
        "subsurface_flow",
        "baseflow",
        "total_river_discharge",
        "river_discharge_rate",
        "canopy_evaporation",
    ),
):
    """A class describing the hydrology model.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        initial_soil_moisture: The initial volumetric relative water content [unitless]
            for all layers. This will be converted to soil moisture in mm.
        initial_groundwater_saturation: Initial level of groundwater saturation (between
            0 and 1) for all layers and grid cells identical. This will be converted to
            groundwater storage in mm.
        model_constants: Set of constants for the hydrology model.

    Raises:
        InitialisationError: when soil moisture or saturation parameters are not numeric
            or out of [0, 1] bounds.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        static: bool = False,
        **kwargs: Any,
    ):
        """Hydrology init function.

        The init function is used only to define class attributes. Any logic should be
        handeled in :fun:`~virtual_ecosystem.hydrology.hydrology_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.initial_soil_moisture: float
        """Initial volumetric relative water content [unitless] for all layers and grid
        cells identical."""
        self.initial_groundwater_saturation: float
        """Initial level of groundwater saturation for all layers identical."""
        self.model_constants: HydroConsts
        """Set of constants for the hydrology model"""
        self.drainage_map: dict
        """Upstream neighbours for the calculation of accumulated horizontal flow."""
        self.soil_layer_thickness_mm: np.ndarray
        """Soil layer thickness in mm."""
        self.surface_layer_index: int
        """Surface layer index."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> HydrologyModel:
        """Factory function to initialise the hydrology model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load model parameters
        initial_soil_moisture = config["hydrology"]["initial_soil_moisture"]
        initial_groundwater_saturation = config["hydrology"][
            "initial_groundwater_saturation"
        ]

        # Load in the relevant constants
        model_constants = load_constants(config, "hydrology", "HydroConsts")
        static = config["hydrology"]["static"]

        LOGGER.info(
            "Information required to initialise the hydrology model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            static=static,
            initial_soil_moisture=initial_soil_moisture,
            initial_groundwater_saturation=initial_groundwater_saturation,
            model_constants=model_constants,
        )

    def _setup(
        self,
        initial_soil_moisture: float,
        initial_groundwater_saturation: float,
        model_constants: HydroConsts = HydroConsts(),
        **kwargs: Any,
    ) -> None:
        """Function to set up the hydrology model.

        This function initializes variables that are required to run the
        first update().

        For the within grid cell hydrology, soil moisture is initialised homogenously
        for all soil layers and groundwater storage is set to the percentage of it's
        capacity that was defined in the model configuration. Soil and canopy
        aerodynamic resistances are set to an initial constant value. Some additional
        atmospheric variables are initialised to ensure they are available for update
        when the Virtual Ecosystem is run with the `abiotic_simple` model.

        For the hydrology across the grid, this function initialises the accumulated
        surface runoff variable and the subsurface accumulated flow variable. Both
        require a spinup which is currently not implemented.

        Args:
            initial_soil_moisture: The initial volumetric relative water content
                [unitless] for all layers. This will be converted to soil moisture in
                mm.
            initial_groundwater_saturation: Initial level of groundwater saturation
                (between 0 and 1) for all layers and grid cells identical. This will be
                converted to groundwater storage in mm.
            model_constants: Set of constants for the hydrology model.
            **kwargs: Further arguments to the setup method.
        """

        # Sanity checks for initial soil moisture and initial_groundwater_saturation
        for attr, value in (
            ("initial_soil_moisture", initial_soil_moisture),
            ("initial_groundwater_saturation", initial_groundwater_saturation),
        ):
            if not isinstance(value, float | int):
                to_raise = InitialisationError(f"The {attr} must be numeric!")
                LOGGER.error(to_raise)
                raise to_raise

            if value < 0 or value > 1:
                to_raise = InitialisationError(f"The {attr} has to be between 0 and 1!")
                LOGGER.error(to_raise)
                raise to_raise

        self.initial_soil_moisture = initial_soil_moisture
        self.initial_groundwater_saturation = initial_groundwater_saturation
        self.model_constants = model_constants
        self.abiotic_constants = AbioticConsts()
        self.grid.set_neighbours(distance=sqrt(self.grid.cell_area))
        """Set neighbours."""
        self.drainage_map = above_ground.calculate_drainage_map(
            grid=self.data.grid,
            elevation=np.array(self.data["elevation"]),
        )

        # Calculate layer thickness for soil moisture unit conversion and set structures
        # and tile across grid cells
        self.soil_layer_thickness_mm = np.tile(
            (
                self.layer_structure.soil_layer_thickness
                * self.core_constants.meters_to_mm
            )[:, None],
            self.grid.n_cells,
        )

        # Select aboveground layer for surface evaporation calculation
        # TODO this needs to be replaced with 2m above ground value
        self.surface_layer_index = self.layer_structure.index_surface_scalar

        # Calculate initial soil moisture, [mm]
        self.data["soil_moisture"] = hydrology_tools.initialise_soil_moisture_mm(
            soil_layer_thickness=self.soil_layer_thickness_mm,
            layer_structure=self.layer_structure,
            initial_soil_moisture=self.initial_soil_moisture,
        )

        # Create initial groundwater storage variable with two layers, [mm]
        # TODO think about including this in config, but we don't want to carry those
        # layers around with all variables in the data object
        initial_groundwater_storage = (
            self.initial_groundwater_saturation
            * self.model_constants.groundwater_capacity
        )
        self.data["groundwater_storage"] = DataArray(
            np.full((2, self.grid.n_cells), initial_groundwater_storage),
            dims=("groundwater_layers", "cell_id"),
            name="groundwater_storage",
        )

        # Set initial above-ground accumulated runoff and sub-surface flow to zero
        for var in ["surface_runoff_accumulated", "subsurface_flow_accumulated"]:
            self.data[var] = DataArray(
                np.zeros_like(self.data["elevation"]),
                dims="cell_id",
                name=var,
                coords={"cell_id": self.grid.cell_id},
            )

        # Initialise atmospheric variables required for update
        atmosphere_setup = hydrology_tools.initialise_atmosphere_for_hydrology(
            data=self.data,
            model_constants=self.model_constants,
            abiotic_constants=self.abiotic_constants,
            core_constants=self.core_constants,
            layer_structure=self.layer_structure,
        )
        self.data.add_from_dict(output_dict=atmosphere_setup)

    def spinup(self) -> None:
        """Placeholder function to spin up the hydrology model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        r"""Function to update the hydrology model.

        This function calculates the main hydrological components of the Virtual
        Ecosystem and updates the following variables in the `data` object:

        * canopy_evaporation, [mm]
        * precipitation_surface, [mm]
        * soil_moisture, [mm]
        * matric_potential, [kPa]
        * surface_runoff, [mm]
        * surface_runoff_accumulated, [mm]
        * subsurface_flow, [mm]
        * subsurface_flow_accumulated, [mm]
        * soil_evaporation, [mm]
        * vertical_flow, [mm d-1]
        * groundwater_storage, [mm]
        * subsurface_flow, [mm]
        * baseflow, [mm]
        * total_river_discharge, [mm]
        * river_discharge_rate, [m3 s-1]
        * bypass flow, [mm]
        * aerodynamic_resistance_surface, [s m-1]

        Many of the underlying processes are problematic at a monthly timestep, which is
        currently the only supported update interval. As a short-term work around, the
        input precipitation is randomly distributed over 30 days and input
        evapotranspiration is divided by 30, and the return variables are monthly means
        or monthly accumulated values.

        Precipitation that reaches the surface is defined as incoming precipitation
        minus canopy interception, which is estimated using a stroage-based approach,
        see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.calculate_interception`
        . The water from the canopy interception pool either evaporated back to the
        atmosphere or drips through the canopy reaching the surface with a delay.

        Surface runoff is calculated with a simple bucket model based on
        :cite:t:`davis_simple_2017`, see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.calculate_surface_runoff`
        : if precipitation exceeds top soil moisture capacity
        , the excess water is added to runoff and top soil moisture is set to soil
        moisture capacity value; if the top soil is not saturated, precipitation is
        added to the current topsoil moisture level and runoff is set to zero.
        The accumulated surface runoff is calculated as the sum of current runoff and
        the runoff from upstream cells at the previous time step, see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.accumulate_horizontal_flow`
        .

        Potential soil evaporation is calculated with classical bulk aerodynamic
        formulation, following the so-called ':math:`\alpha` method', see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.calculate_soil_evaporation`
        , and reduced to actual evaporation as a function of leaf area index.

        Vertical flow between soil layers is calculated combining Richards' equation and
        Darcy's law for unsaturated flow
        :func:`~virtual_ecosystem.models.hydrology.below_ground.calculate_vertical_flow`
        . Here, the mean vertical flow in mm per day that goes though the top soil layer
        is returned to the data object. Note that there are
        severe limitations to this approach on the temporal and spatial scale of this
        model and this can only be treated as a very rough approximation!

        Soil moisture is updated by iteratively updating the soil moisture of individual
        layers under consideration of the vertical flow in and out of each layer, see
        :func:`~virtual_ecosystem.models.hydrology.below_ground.update_soil_moisture`

        Groundwater storage and flows are modelled using two parallel linear
        reservoirs, see
        :func:`~virtual_ecosystem.models.hydrology.below_ground.update_groundwater_storage`
        . The horizontal flow between grid cells currently uses the same function as the
        above ground runoff.

        Total river discharge is calculated as the sum of above- and below ground
        horizontal flow and converted to river discharge rate in m3/s.

        The function requires the following input variables from the data object:

        * air temperature, [C]
        * relative humidity, []
        * atmospheric pressure, [kPa]
        * vapour pressure deficit, [kPa]
        * precipitation, [mm]
        * wind speed, [m s-1]
        * leaf area index, [m m-1]
        * layer heights, [m]
        * Soil moisture (previous time step), [mm]
        * evapotranspiration (current time step), [mm]
        * accumulated surface runoff (previous time step), [mm]
        * accumulated subsurface flow (previous time step), [mm]
        * aerodynamic_resistance_canopy, [s m-1]

        and a number of parameters that as described in detail in
        :class:`~virtual_ecosystem.models.hydrology.constants.HydroConsts`.
        """
        # Determine number of days, currently only 30 days (=1 month)
        if self.model_timing.update_interval_quantity != Quantity("1 month"):
            to_raise = NotImplementedError("This time step is currently not supported.")
            LOGGER.error(to_raise)
            raise to_raise

        days: int = 30

        # Set seed for random rainfall generator
        seed: None | int = kwargs.pop("seed", None)

        # Select variables at relevant heights for current time step
        hydro_input = hydrology_tools.setup_hydrology_input_current_timestep(
            data=self.data,
            time_index=time_index,
            days=days,
            seed=seed,
            layer_structure=self.layer_structure,
            soil_layer_thickness_mm=self.soil_layer_thickness_mm,
            soil_moisture_capacity=self.core_constants.soil_moisture_capacity,
            soil_moisture_residual=self.model_constants.soil_moisture_residual,
        )

        # Calculate psychrometric constant
        psychrometric_constant = hydrology_tools.calculate_psychrometric_constant(
            atmospheric_pressure=self.data["atmospheric_pressure"].to_numpy(),
            latent_heat_vapourization=self.data["latent_heat_vapourisation"].to_numpy(),
            specific_heat_air=self.data["specific_heat_air"].to_numpy(),
            molecular_weight_ratio_water_to_dry_air=(
                self.core_constants.molecular_weight_ratio_water_to_dry_air
            ),
        )

        # Create lists for output variables to store daily data
        daily_lists: dict = {name: [] for name in self.vars_updated}

        for day in np.arange(days):
            # Interception of water in canopy, [mm]
            interception = above_ground.calculate_interception(
                leaf_area_index=hydro_input["leaf_area_index_sum"],
                precipitation=hydro_input["current_precipitation"][:, day],
                intercept_parameters=self.model_constants.intercept_parameters,
                veg_density_param=self.model_constants.veg_density_param,
            )

            # Calculate canopy evaporation and leaf drainage
            # TODO net radiation is part of energy balance, check which inputs are
            # required, in which order this is calculated, discuss also with plant model
            # needs to move out of loop and split in 30 days if sum input
            net_radiation_canopy = self.layer_structure.from_template()
            net_radiation_canopy[self.layer_structure.index_filled_canopy] = 20.0

            canopy_water_balance = above_ground.calculate_canopy_evaporation(
                leaf_area_index=self.data["leaf_area_index"].to_numpy(),
                interception=interception,
                net_radiation=net_radiation_canopy.to_numpy(),
                vapour_pressure_deficit=self.data["vapour_pressure_deficit"].to_numpy(),
                air_temperature=self.data["air_temperature"].to_numpy(),
                density_air_kg=self.data["density_air"].to_numpy(),
                specific_heat_air=self.data["specific_heat_air"].to_numpy(),
                aerodynamic_resistance=self.data[
                    "aerodynamic_resistance_canopy"
                ].to_numpy(),
                stomatal_resistance=(
                    self.core_constants.conductance_to_resistance_conversion_factor
                    / self.data["stomatal_conductance"].to_numpy()
                ),
                latent_heat_vapourisation=self.data[
                    "latent_heat_vapourisation"
                ].to_numpy(),
                psychrometric_constant=psychrometric_constant,
                saturated_pressure_slope_parameters=(
                    self.abiotic_constants.saturated_pressure_slope_parameters
                ),
                time_interval=self.core_constants.seconds_to_day,
                intercept_residence_time=self.model_constants.intercept_residence_time,
                extinction_coefficient_global_radiation=(
                    self.model_constants.extinction_coefficient_global_radiation
                ),
            )
            daily_lists["canopy_evaporation"].append(
                canopy_water_balance["canopy_evaporation"]
            )
            # Precipitation that reaches the surface per day, [mm]
            precipitation_surface = (
                hydro_input["current_precipitation"][:, day]
                - interception
                + np.nansum(canopy_water_balance["leaf_drainage"], axis=0)
            )
            daily_lists["precipitation_surface"].append(precipitation_surface)

            # Calculate daily surface runoff of each grid cell, [mm]
            surface_runoff = above_ground.calculate_surface_runoff(
                precipitation_surface=precipitation_surface,
                top_soil_moisture=hydro_input["current_soil_moisture"][0],
                top_soil_moisture_capacity=hydro_input["top_soil_moisture_capacity"],
            )
            daily_lists["surface_runoff"].append(surface_runoff)

            # Calculate preferential bypass flow, [mm]
            bypass_flow = above_ground.calculate_bypass_flow(
                top_soil_moisture=hydro_input["current_soil_moisture"][0],
                sat_top_soil_moisture=hydro_input["top_soil_moisture_capacity"],
                available_water=precipitation_surface - surface_runoff,
                bypass_flow_coefficient=(self.model_constants.bypass_flow_coefficient),
            )
            daily_lists["bypass_flow"].append(bypass_flow)

            # Calculate top soil moisture after infiltration, [mm]
            soil_moisture_infiltrated = np.clip(
                (
                    hydro_input["current_soil_moisture"][0]
                    + precipitation_surface
                    - surface_runoff
                    - bypass_flow,
                ),
                0,
                hydro_input["top_soil_moisture_capacity"],
            ).squeeze()

            # Prepare inputs for soil evaporation function
            # TODO currently surface layer, needs to be replaced with 2m above ground
            top_soil_moisture_vol = (
                soil_moisture_infiltrated / self.soil_layer_thickness_mm[0]
            )

            soil_evaporation = above_ground.calculate_soil_evaporation(
                temperature=hydro_input["surface_temperature"],
                relative_humidity=hydro_input["surface_humidity"],
                atmospheric_pressure=hydro_input["surface_pressure"],
                soil_moisture=top_soil_moisture_vol,
                soil_moisture_residual=self.model_constants.soil_moisture_residual,
                soil_moisture_capacity=self.core_constants.soil_moisture_capacity,
                leaf_area_index=hydro_input["leaf_area_index_sum"],
                wind_speed_surface=hydro_input["surface_wind_speed"],
                density_air=self.data["density_air"][
                    self.surface_layer_index
                ].to_numpy(),
                latent_heat_vapourisation=self.data["latent_heat_vapourisation"][
                    self.surface_layer_index
                ].to_numpy(),
                gas_constant_water_vapour=self.core_constants.gas_constant_water_vapour
                / 1000.0,
                drag_coefficient_evaporation=(
                    self.model_constants.drag_coefficient_evaporation
                ),
                extinction_coefficient_global_radiation=(
                    self.model_constants.extinction_coefficient_global_radiation
                ),
                time_interval=self.core_constants.seconds_to_day,
                pyrealm_const=PyrealmConst,
            )
            daily_lists["soil_evaporation"].append(soil_evaporation["soil_evaporation"])
            daily_lists["aerodynamic_resistance_surface"].append(
                soil_evaporation["aerodynamic_resistance_surface"]
            )

            # Calculate top soil moisture after evap and combine with lower layers, [mm]
            soil_moisture_evap_mm: NDArray[np.float32] = np.concatenate(
                (
                    np.expand_dims(
                        np.clip(
                            (
                                soil_moisture_infiltrated
                                - soil_evaporation["soil_evaporation"]
                            ),
                            hydro_input["top_soil_moisture_residual"],
                            hydro_input["top_soil_moisture_capacity"],
                        ),
                        axis=0,
                    ),
                    hydro_input["current_soil_moisture"][1:],
                )
            )

            # Calculate vertical flow between soil layers in mm per day and soil matric
            # potential in m (later converted to kPa for data object).
            # Note that there are severe limitations to this approach on the temporal
            # spatial scale of this model and this can only be treated as a very rough
            # approximation to discuss nutrient leaching.
            vertical_flow = below_ground.calculate_vertical_flow(
                soil_moisture=soil_moisture_evap_mm
                / self.soil_layer_thickness_mm,  # vol
                soil_layer_thickness=self.soil_layer_thickness_mm / 1000.0,  # m
                soil_layer_depth=np.abs(self.layer_structure.soil_layer_depths),  # m
                soil_moisture_saturation=(
                    self.model_constants.soil_moisture_saturation
                ),  # vol
                soil_moisture_residual=(
                    self.model_constants.soil_moisture_residual
                ),  # vol
                saturated_hydraulic_conductivity=(
                    self.model_constants.saturated_hydraulic_conductivity
                ),  # m/s
                air_entry_potential_inverse=(
                    self.model_constants.air_entry_potential_inverse
                ),  # m/m
                van_genuchten_nonlinearily_parameter=(
                    self.model_constants.van_genuchten_nonlinearily_parameter
                ),
                pore_connectivity_parameter=(
                    self.model_constants.pore_connectivity_parameter
                ),
                groundwater_capacity=self.model_constants.groundwater_capacity / 1000.0,
                seconds_to_day=self.core_constants.seconds_to_day,
            )
            daily_lists["matric_potential"].append(
                vertical_flow["matric_potential"] * self.model_constants.m_to_kpa
            )
            daily_lists["vertical_flow"].append(vertical_flow["vertical_flow"])

            # Update soil moisture by +/- vertical flow to each layer and remove root
            # water uptake by plants (transpiration), [mm]
            # TODO combined input from evaporation and transpiration
            soil_moisture_updated = below_ground.update_soil_moisture(
                soil_moisture=soil_moisture_evap_mm,  # mm
                vertical_flow=vertical_flow["vertical_flow"],  # mm day-1
                evapotranspiration=hydro_input["current_evapotranspiration"],  # mm
                soil_moisture_capacity=(  # mm
                    self.core_constants.soil_moisture_capacity
                    * self.soil_layer_thickness_mm
                ),
                soil_moisture_residual=(  # mm
                    self.model_constants.soil_moisture_residual
                    * self.soil_layer_thickness_mm
                ),
            )
            daily_lists["soil_moisture"].append(soil_moisture_updated)

            # calculate below ground horizontal flow and update ground water
            below_ground_flow = below_ground.update_groundwater_storage(
                groundwater_storage=hydro_input["groundwater_storage"],
                vertical_flow_to_groundwater=vertical_flow["vertical_flow"][-1],
                bypass_flow=bypass_flow,
                max_percolation_rate_uzlz=(
                    self.model_constants.max_percolation_rate_uzlz
                ),
                groundwater_loss=self.model_constants.groundwater_loss,
                reservoir_const_upper_groundwater=(
                    self.model_constants.reservoir_const_upper_groundwater
                ),
                reservoir_const_lower_groundwater=(
                    self.model_constants.reservoir_const_lower_groundwater
                ),
            )

            for var in ["groundwater_storage", "subsurface_flow", "baseflow"]:
                daily_lists[var].append(below_ground_flow[var])

            # Calculate horizontal flow
            # Calculate accumulated runoff for each cell (me+sum of upstream neighbours)
            new_accumulated_runoff = above_ground.accumulate_horizontal_flow(
                drainage_map=self.drainage_map,
                current_flow=surface_runoff,
                previous_accumulated_flow=hydro_input["previous_accumulated_runoff"],
            )
            daily_lists["surface_runoff_accumulated"].append(new_accumulated_runoff)

            # Calculate subsurface accumulated flow, [mm]
            new_subsurface_flow_accumulated = above_ground.accumulate_horizontal_flow(
                drainage_map=self.drainage_map,
                current_flow=np.array(
                    below_ground_flow["subsurface_flow"] + below_ground_flow["baseflow"]
                ),
                previous_accumulated_flow=(
                    hydro_input["previous_subsurface_flow_accumulated"]
                ),
            )
            daily_lists["subsurface_flow_accumulated"].append(
                new_subsurface_flow_accumulated
            )

            # Calculate total river discharge as sum of above- and below-ground flow
            total_river_discharge = (
                new_accumulated_runoff + new_subsurface_flow_accumulated
            )
            daily_lists["total_river_discharge"].append(total_river_discharge)

            # Convert total discharge to river discharge rate, [m3 s-1]
            river_discharge_rate = above_ground.convert_mm_flow_to_m3_per_second(
                river_discharge_mm=total_river_discharge,
                area=self.grid.cell_area,
                days=days,
                seconds_to_day=self.core_constants.seconds_to_day,
                meters_to_millimeters=self.core_constants.meters_to_mm,
            )
            daily_lists["river_discharge_rate"].append(river_discharge_rate)

            # update inputs for next day
            hydro_input["current_soil_moisture"] = soil_moisture_updated
            hydro_input["groundwater_storage"] = below_ground_flow[
                "groundwater_storage"
            ]
            hydro_input["previous_accumulated_runoff"] = new_accumulated_runoff
            hydro_input["subsurface_flow_accumulated"] = new_subsurface_flow_accumulated

        # create output dict as intermediate step to not overwrite data directly
        soil_hydrology = {}

        # Calculate monthly accumulated/mean values for hydrology variables
        for var in [
            "precipitation_surface",
            "surface_runoff",
            "soil_evaporation",
            "subsurface_flow",
            "baseflow",
            "bypass_flow",
            "surface_runoff_accumulated",
            "subsurface_flow_accumulated",
            "total_river_discharge",
        ]:
            soil_hydrology[var] = DataArray(
                np.sum(np.stack(daily_lists[var], axis=1), axis=1),
                dims="cell_id",
                coords={"cell_id": self.grid.cell_id},
            )

        soil_hydrology["canopy_evaporation"] = self.layer_structure.from_template()
        soil_hydrology["canopy_evaporation"][
            self.layer_structure.index_filled_canopy
        ] = np.array(daily_lists["canopy_evaporation"]).sum(axis=(0, 1))

        soil_hydrology["vertical_flow"] = DataArray(  # vertical flow through top soil
            np.mean(np.stack(daily_lists["vertical_flow"][0], axis=1), axis=1),
            dims="cell_id",
            coords={"cell_id": self.grid.cell_id},
        )

        for var in ["river_discharge_rate", "aerodynamic_resistance_surface"]:
            soil_hydrology[var] = DataArray(
                np.mean(np.stack(daily_lists[var], axis=1), axis=1),
                dims="cell_id",
                coords={"cell_id": self.grid.cell_id},
            )

        # Return mean soil moisture, [mm], and soil matric potential, [kPa], and add
        # atmospheric layers (nan)
        for var in ["soil_moisture", "matric_potential"]:
            soil_hydrology[var] = self.layer_structure.from_template()
            soil_hydrology[var][self.layer_structure.index_all_soil] = np.mean(
                np.stack(daily_lists[var], axis=0), axis=0
            )

        # Save last state of groundwater stoage, [mm]
        soil_hydrology["groundwater_storage"] = DataArray(
            daily_lists["groundwater_storage"][day],
            dims=self.data["groundwater_storage"].dims,
        )

        # Update data object
        self.data.add_from_dict(output_dict=soil_hydrology)

    def cleanup(self) -> None:
        """Placeholder function for hydrology model cleanup."""
