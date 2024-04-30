"""The :mod:`~virtual_ecosystem.models.hydrology.hydrology_model` module
creates a
:class:`~virtual_ecosystem.models.hydrology.hydrology_model.HydrologyModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Ecosystem
model develops. The factory method
:func:`~virtual_ecosystem.models.hydrology.hydrology_model.HydrologyModel.from_config`
exists in a more complete state, and unpacks a small number of parameters from our
currently pretty minimal configuration dictionary. These parameters are then used to
generate a class instance. If errors crop here when converting the information from the
config dictionary to the required types they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled by
downstream functions so that all model configuration failures can be reported as one.

TODOs

    * find a way to load daily (precipitation) data and loop over daily time_index
    * add time dimension to required_init_vars
    * allow for different time steps (currently only 30 days)
    * potentially move `calculate_drainage_map` to core
    * change temperature to Kelvin
    * change soil moisture to mm
    * add abiotic constants from config
"""  # noqa: D205, D415

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pint import Quantity
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
    required_init_vars=(
        ("layer_heights", ("spatial",)),
        ("elevation", ("spatial",)),
    ),
    vars_updated=(
        "precipitation_surface",  # precipitation-interception loss, input to `plants`
        "soil_moisture",
        "surface_runoff",  # equivalent to SPLASH runoff
        "vertical_flow",
        "latent_heat_vapourisation",
        "molar_density_air",
        "soil_evaporation",
        "aerodynamic_resistance_surface",
        "surface_runoff_accumulated",
        "subsurface_flow_accumulated",
        "matric_potential",
        "groundwater_storage",
        "river_discharge_rate",
        "total_river_discharge",
        "subsurface_flow",
        "baseflow",
    ),
):
    """A class describing the hydrology model.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        initial_soil_moisture: The initial volumetric relative water content [unitless]
            for all layers.
        initial_groundwater_saturation: Initial level of groundwater saturation (between
            0 and 1) for all layers and grid cells identical.
        model_constants: Set of constants for the hydrology model.

    Raises:
        InitialisationError: when soil moisture or saturation parameters are not numeric
            or out of [0, 1] bounds.

    TODOs:

    * find a way to load daily (precipitation) data and loop over daily time_index
    * add time dimension to required_init_vars
    * allow for different time steps (currently only 30 days)
    * potentially move `calculate_drainage_map` to core
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        initial_soil_moisture: float,
        initial_groundwater_saturation: float,
        model_constants: HydroConsts = HydroConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        # Sanity checks for initial soil moisture and initial_groundwater_saturation
        for attr, value in (
            ("initial_soil_moisture", initial_soil_moisture),
            ("initial_groundwater_saturation", initial_groundwater_saturation),
        ):
            if not isinstance(value, (float, int)):
                to_raise = InitialisationError(f"The {attr} must be numeric!")
                LOGGER.error(to_raise)
                raise to_raise

            if value < 0 or value > 1:
                to_raise = InitialisationError(f"The {attr} has to be between 0 and 1!")
                LOGGER.error(to_raise)
                raise to_raise

        self.initial_soil_moisture: float = initial_soil_moisture
        """Initial volumetric relative water content [unitless] for all layers and grid
        cells identical."""
        self.initial_groundwater_saturation: float = initial_groundwater_saturation
        """Initial level of groundwater saturation for all layers identical."""
        self.model_constants: HydroConsts = model_constants
        """Set of constants for the hydrology model"""
        self.core_constants = core_components.core_constants
        """Set of core constants for the hydrology model"""
        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))
        """Set neighbours."""
        self.drainage_map = above_ground.calculate_drainage_map(
            grid=self.data.grid,
            elevation=np.array(self.data["elevation"]),
        )
        """Upstream neighbours for the calculation of accumulated horizontal flow."""

        self.soil_layer_thickness = hydrology_tools.calculate_layer_thickness(
            soil_layer_heights=(
                self.data["layer_heights"]
                .where(self.data["layer_heights"].layer_roles == "soil")
                .dropna(dim="layers")
            ).to_numpy(),
            meters_to_mm=self.core_constants.meters_to_mm,
        )
        """Soil layer thickness in mm."""

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

        LOGGER.info(
            "Information required to initialise the hydrology model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            initial_soil_moisture=initial_soil_moisture,
            initial_groundwater_saturation=initial_groundwater_saturation,
            model_constants=model_constants,
        )

    def setup(self) -> None:
        """Function to set up the hydrology model.

        At the moment, this function initializes variables that are required to run the
        first update(). Air temperature and relative humidity below the canopy are set
        to the 2 m reference values.

        For the within grid cell hydrology, soil moisture is initialised homogenously
        for all soil layers and groundwater storage is set to the percentage of it's
        capacity that was defined in the model configuration. This design might change
        with the implementation of the SPLASH model :cite:p:`davis_simple_2017` which
        will take care of part of the above-ground hydrology.

        For the hydrology across the grid, this function initialises the accumulated
        surface runoff variable and the subsurface accumulated flow variable. Both
        require a spinup which is currently not implemented.
        """

        # Calculate initial soil moisture, [mm]
        soil_moisture_ini = hydrology_tools.initialise_soil_moisture_mm(
            soil_layer_thickness=self.soil_layer_thickness,
            layer_structure=self.layer_structure,
            n_cells=self.data.grid.n_cells,
            initial_soil_moisture=self.initial_soil_moisture,
        )

        self.data["soil_moisture"] = DataArray(
            soil_moisture_ini,
            dims=self.data["layer_heights"].dims,
            coords=self.data["layer_heights"].coords,
            name="soil_moisture",
        )

        # Create initial groundwater storage variable with two layers, [mm]
        # TODO think about including this in config, but we don't want to carry those
        # layers around with all variables in the data object
        initial_groundwater_storage = (
            self.initial_groundwater_saturation
            * self.model_constants.groundwater_capacity
        )
        self.data["groundwater_storage"] = DataArray(
            np.full((2, self.data.grid.n_cells), initial_groundwater_storage),
            dims=("groundwater_layers", "cell_id"),
            name="groundwater_storage",
        )

        # Create subcanopy microclimate from reference height
        for var in [
            "air_temperature",
            "relative_humidity",
            "wind_speed",
            "atmospheric_pressure",
        ]:
            self.data[var] = (
                DataArray(self.data[var + "_ref"].isel(time_index=0))
                .expand_dims("layers")
                .rename(var)
                .assign_coords(
                    coords={
                        "layers": [self.layer_structure.layer_roles.index("subcanopy")],
                        "layer_roles": ("layers", ["subcanopy"]),
                        "cell_id": self.data.grid.cell_id,
                    },
                )
            )

        # Set initial above-ground accumulated runoff and sub-surface flow to zero
        for var in ["surface_runoff_accumulated", "subsurface_flow_accumulated"]:
            self.data[var] = DataArray(
                np.zeros_like(self.data["elevation"]),
                dims="cell_id",
                name=var,
                coords={"cell_id": self.data.grid.cell_id},
            )

    def spinup(self) -> None:
        """Placeholder function to spin up the hydrology model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        r"""Function to update the hydrology model.

        This function calculates the main hydrological components of the Virtual
        Ecosystem and updates the following variables in the `data` object:

        * precipitation_surface, [mm]
        * soil_moisture, [mm]
        * matric_potential, [kPa]
        * surface_runoff, [mm], equivalent to SPLASH runoff
        * surface_runoff_accumulated, [mm]
        * subsurface_flow_accumulated, [mm]
        * soil_evaporation, [mm]
        * aerodynamic_resistance_surface
        * vertical_flow, [mm d-1]
        * latent_heat_vapourisation, [J kg-1]
        * molar_density_air, [mol m-3]
        * groundwater_storage, [mm]
        * subsurface_flow, [mm]
        * baseflow, [mm]
        * total_river_discharge, [mm]
        * river_discharge_rate, [m3 s-1]

        Many of the underlying processes are problematic at a monthly timestep, which is
        currently the only supported update interval. As a short-term work around, the
        input precipitation is randomly distributed over 30 days and input
        evapotranspiration is divided by 30, and the return variables are monthly means
        or monthly accumulated values.

        Precipitation that reaches the surface is defined as incoming precipitation
        minus canopy interception, which is estimated using a stroage-based approach,
        see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.calculate_interception`
        .

        Surface runoff is calculated with a simple bucket model based on
        :cite:t:`davis_simple_2017`, see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.calculate_surface_runoff`
        : if precipitation exceeds top soil moisture capacity
        , the excess water is added to runoff and top soil moisture is set to soil
        moisture capacity value; if the top soil is not saturated, precipitation is
        added to the current soil moisture level and runoff is set to zero. Note that
        this function will likely change with the implementation of the SPLASH model
        :cite:p:`davis_simple_2017` in the plant module which will take care of the grid
        cell based above-ground hydrology. The accumulated surface runoff is calculated
        as the sum of current runoff and the runoff from upstream cells at the previous
        time step, see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.accumulate_horizontal_flow`
        .

        Potential soil evaporation is calculated with classical bulk aerodynamic
        formulation, following the so-called ':math:`\alpha` method', see
        :func:`~virtual_ecosystem.models.hydrology.above_ground.calculate_soil_evaporation`
        , and reduced to actual evaporation as a function of leaf area index.

        Vertical flow between soil layers is calculated using the Richards equation, see
        :func:`~virtual_ecosystem.models.hydrology.below_ground.calculate_vertical_flow`
        . Here, the mean vertical flow in mm per day that goes though the top soil layer
        is returned to the data object. Note that there are
        severe limitations to this approach on the temporal and spatial scale of this
        model and this can only be treated as a very rough approximation!

        Soil moisture is updated by iteratively updating the soil moisture of individual
        layers under consideration of the vertical flow in and out of each layer, see
        :func:`~virtual_ecosystem.models.hydrology.below_ground.update_soil_moisture`
        . The conversion to matric potential is based on :cite:t:`campbell_simple_1974`,
        see
        :func:`~virtual_ecosystem.models.hydrology.below_ground.convert_soil_moisture_to_water_potential`
        .

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
        * precipitation, [mm]
        * wind speed, [m s-1]
        * leaf area index, [m m-2]
        * layer heights, [m]
        * Soil moisture (previous time step), [mm]
        * evapotranspiration (current time step), [mm]
        * accumulated surface runoff (previous time step), [mm]
        * accumulated subsurface flow (previous time step), [mm]

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

        subcanopy_layer_index = self.layer_structure.layer_roles.index("subcanopy")

        # Select variables at relevant heights for current time step
        abiotic_constants = AbioticConsts()
        hydro_input = hydrology_tools.setup_hydrology_input_current_timestep(
            data=self.data,
            time_index=time_index,
            days=days,
            seed=seed,
            layer_roles=self.layer_structure.layer_roles,
            soil_layer_thickness=self.soil_layer_thickness,
            soil_moisture_capacity=self.model_constants.soil_moisture_capacity,
            soil_moisture_residual=self.model_constants.soil_moisture_residual,
            core_constants=self.core_constants,
            latent_heat_vap_equ_factors=(abiotic_constants.latent_heat_vap_equ_factors),
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

            # Precipitation that reaches the surface per day, [mm]
            precipitation_surface = (
                hydro_input["current_precipitation"][:, day] - interception
            )
            daily_lists["precipitation_surface"].append(precipitation_surface)

            # Calculate daily surface runoff of each grid cell, [mm]; replace by SPLASH
            surface_runoff = above_ground.calculate_surface_runoff(
                precipitation_surface=precipitation_surface,
                top_soil_moisture=hydro_input["soil_moisture_true"][0],
                top_soil_moisture_capacity=hydro_input["top_soil_moisture_capacity_mm"],
            )

            daily_lists["surface_runoff"].append(surface_runoff)

            # Calculate preferential bypass flow, [mm]
            bypass_flow = above_ground.calculate_bypass_flow(
                top_soil_moisture=hydro_input["soil_moisture_true"][0],
                sat_top_soil_moisture=hydro_input["top_soil_moisture_capacity_mm"],
                available_water=precipitation_surface - surface_runoff,
                infiltration_shape_parameter=(
                    self.model_constants.infiltration_shape_parameter
                ),
            )

            # Calculate top soil moisture after infiltration, [mm]
            soil_moisture_infiltrated = np.clip(
                (
                    hydro_input["soil_moisture_true"][0]
                    + precipitation_surface
                    - surface_runoff
                    - bypass_flow,
                ),
                0,
                hydro_input["top_soil_moisture_capacity_mm"],
            ).squeeze()

            # Prepare inputs for soil evaporation function
            top_soil_moisture_vol = (
                soil_moisture_infiltrated / self.soil_layer_thickness[0]
            )

            latent_heat_vapourisation = (
                hydro_input["latent_heat_vapourisation"][subcanopy_layer_index] / 1000.0
            )
            density_air_kg = (
                hydro_input["molar_density_air"][subcanopy_layer_index]
                * self.core_constants.molecular_weight_air
                / 1000.0
            )

            soil_evaporation = above_ground.calculate_soil_evaporation(
                temperature=hydro_input["subcanopy_temperature"],
                relative_humidity=hydro_input["subcanopy_humidity"],
                atmospheric_pressure=hydro_input["subcanopy_pressure"],
                soil_moisture=top_soil_moisture_vol,
                soil_moisture_residual=self.model_constants.soil_moisture_residual,
                soil_moisture_capacity=self.model_constants.soil_moisture_capacity,
                leaf_area_index=hydro_input["leaf_area_index_sum"],
                wind_speed_surface=hydro_input["subcanopy_wind_speed"],
                celsius_to_kelvin=self.core_constants.zero_Celsius,
                density_air=density_air_kg,
                latent_heat_vapourisation=latent_heat_vapourisation,
                gas_constant_water_vapour=self.core_constants.gas_constant_water_vapour,
                soil_surface_heat_transfer_coefficient=(
                    self.model_constants.soil_surface_heat_transfer_coefficient
                ),
                extinction_coefficient_global_radiation=(
                    self.model_constants.extinction_coefficient_global_radiation
                ),
            )
            daily_lists["soil_evaporation"].append(soil_evaporation["soil_evaporation"])
            daily_lists["aerodynamic_resistance_surface"].append(
                soil_evaporation["aerodynamic_resistance_surface"]
            )

            # Calculate top soil moisture after evap and combine with lower layers, [mm]
            soil_moisture_evap: NDArray[np.float32] = np.concatenate(
                (
                    np.expand_dims(
                        np.clip(
                            (
                                soil_moisture_infiltrated
                                - soil_evaporation["soil_evaporation"]
                            ),
                            hydro_input["top_soil_moisture_residual_mm"],
                            hydro_input["top_soil_moisture_capacity_mm"],
                        ),
                        axis=0,
                    ),
                    hydro_input["soil_moisture_true"][1:],
                )
            )

            # Calculate vertical flow between soil layers in mm per day
            # Note that there are severe limitations to this approach on the temporal
            # spatial scale of this model and this can only be treated as a very rough
            # approximation to discuss nutrient leaching.
            vertical_flow = below_ground.calculate_vertical_flow(
                soil_moisture=soil_moisture_evap / self.soil_layer_thickness,  # vol
                soil_layer_thickness=self.soil_layer_thickness,  # mm
                soil_moisture_capacity=(
                    self.model_constants.soil_moisture_capacity
                ),  # vol
                soil_moisture_residual=(
                    self.model_constants.soil_moisture_residual
                ),  # vol
                hydraulic_conductivity=(
                    self.model_constants.hydraulic_conductivity
                ),  # m/s
                hydraulic_gradient=self.model_constants.hydraulic_gradient,  # m/m
                nonlinearily_parameter=self.model_constants.nonlinearily_parameter,
                groundwater_capacity=self.model_constants.groundwater_capacity,
                seconds_to_day=self.core_constants.seconds_to_day,
            )
            daily_lists["vertical_flow"].append(vertical_flow)

            # Update soil moisture by +/- vertical flow to each layer and remove root
            # water uptake by plants (transpiration), [mm]
            soil_moisture_updated = below_ground.update_soil_moisture(
                soil_moisture=soil_moisture_evap,  # mm
                vertical_flow=vertical_flow,  # mm
                evapotranspiration=hydro_input["current_evapotranspiration"],  # mm
                soil_moisture_capacity=(  # mm
                    self.model_constants.soil_moisture_capacity
                    * self.soil_layer_thickness
                ),
                soil_moisture_residual=(  # mm
                    self.model_constants.soil_moisture_residual
                    * self.soil_layer_thickness
                ),
            )

            daily_lists["soil_moisture"].append(soil_moisture_updated)

            # Convert soil moisture to matric potential
            matric_potential = below_ground.convert_soil_moisture_to_water_potential(
                soil_moisture=(  # vol
                    soil_moisture_updated / self.soil_layer_thickness
                ),
                air_entry_water_potential=(
                    self.model_constants.air_entry_water_potential
                ),
                water_retention_curvature=(
                    self.model_constants.water_retention_curvature
                ),
                soil_moisture_capacity=self.model_constants.soil_moisture_capacity,
            )
            daily_lists["matric_potential"].append(matric_potential)

            # calculate below ground horizontal flow and update ground water
            below_ground_flow = below_ground.update_groundwater_storage(
                groundwater_storage=hydro_input["groundwater_storage"],
                vertical_flow_to_groundwater=vertical_flow[-1],
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
                area=self.data.grid.cell_area,
                days=days,
                seconds_to_day=self.core_constants.seconds_to_day,
                meters_to_millimeters=self.core_constants.meters_to_mm,
            )
            daily_lists["river_discharge_rate"].append(river_discharge_rate)

            # update inputs for next day
            hydro_input["soil_moisture_true"] = soil_moisture_updated  # mm
            hydro_input["groundwater_storage"] = below_ground_flow[
                "groundwater_storage"
            ]
            hydro_input["previous_accumulated_runoff"] = new_accumulated_runoff
            hydro_input["subsurface_flow_accumulated"] = new_subsurface_flow_accumulated

        # create output dict as intermediate step to not overwrite data directly
        soil_hydrology = {}

        # Return monthly latent heat of vapourisation and molar density of air
        # (currently only one value per month, will be average with daily input)
        for var in ["latent_heat_vapourisation", "molar_density_air"]:
            soil_hydrology[var] = DataArray(
                hydro_input[var],
                dims=self.data["layer_heights"].dims,
                coords=self.data["layer_heights"].coords,
            )

        # Calculate monthly accumulated/mean values for hydrology variables
        for var in [
            "precipitation_surface",
            "surface_runoff",
            "soil_evaporation",
            "subsurface_flow",
            "baseflow",
            "surface_runoff_accumulated",
            "subsurface_flow_accumulated",
            "total_river_discharge",
        ]:
            soil_hydrology[var] = DataArray(
                np.sum(np.stack(daily_lists[var], axis=1), axis=1),
                dims="cell_id",
                coords={"cell_id": self.data.grid.cell_id},
            )

        soil_hydrology["vertical_flow"] = DataArray(  # vertical flow through top soil
            np.mean(np.stack(daily_lists["vertical_flow"][0], axis=1), axis=1),
            dims="cell_id",
            coords={"cell_id": self.data.grid.cell_id},
        )

        for var in ["river_discharge_rate", "aerodynamic_resistance_surface"]:
            soil_hydrology[var] = DataArray(
                np.mean(np.stack(daily_lists[var], axis=1), axis=1),
                dims="cell_id",
                coords={"cell_id": self.data.grid.cell_id},
            )

        # Return mean soil moisture, [-], and matric potential, [kPa], and add
        # atmospheric layers (nan)
        for var in ["soil_moisture", "matric_potential"]:
            soil_hydrology[var] = DataArray(
                np.concatenate(
                    (
                        np.full(
                            (
                                self.layer_structure.n_layers
                                - self.layer_structure.layer_roles.count("soil"),
                                self.data.grid.n_cells,
                            ),
                            np.nan,
                        ),
                        np.mean(
                            np.stack(daily_lists[var], axis=0),
                            axis=0,
                        ),
                    ),
                ),
                dims=self.data["layer_heights"].dims,
                coords=self.data["layer_heights"].coords,
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
