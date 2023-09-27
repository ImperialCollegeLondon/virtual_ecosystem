"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_model` module
creates a
:class:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel.from_config`
exists in a more complete state, and unpacks a small number of parameters from our
currently pretty minimal configuration dictionary. These parameters are then used to
generate a class instance. If errors crop here when converting the information from the
config dictionary to the required types they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled by
downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.config import Config
from virtual_rainforest.core.constants import load_constants
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.hydrology import above_ground, below_ground
from virtual_rainforest.models.hydrology.constants import HydroConsts


class HydrologyModel(BaseModel):
    """A class describing the hydrology model.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: A list giving the number and depth of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        initial_soil_moisture: The initial volumetric relative water content [unitless]
            for all layers.
        constants: Set of constants for the hydrology model.

    Raises:
        InitialisationError: when initial soil moisture is out of bounds.

    TODOs:

    * find a way to load daily (precipitation) data and loop over daily time_index
    * add time dimension to required_init_vars
    * allow for different time steps (currently only 30 days)
    * implement below-ground horizontal flow and update stream flow
    * potentially move `calculate_drainage_map` to core
    * Convert soil moisture to matric potential
    """

    model_name = "hydrology"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that hydrology model can sensibly capture."""
    upper_bound_on_time_scale = "1 month"
    """Longest time scale that hydrology model can sensibly capture."""
    required_init_vars = (
        ("precipitation", ("spatial",)),
        ("leaf_area_index", ("spatial",)),
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
        ("atmospheric_pressure_ref", ("spatial",)),
        ("evapotranspiration", ("spatial",)),
        ("elevation", ("spatial",)),
        ("surface_runoff", ("spatial",)),
        # TODO this requires the plant model to run before the hydrology; this works as
        # long as the p-model does not require soil moisture as an input. If it does, we
        # have to discuss where we move the calculation of stream flow.
    )
    """The required variables and axes for the hydrology model"""

    vars_updated = (
        "precipitation_surface",  # precipitation-interception loss, input to `plants`
        "soil_moisture",
        "surface_runoff",  # equivalent to SPLASH runoff
        "vertical_flow",
        "soil_evaporation",
        "stream_flow",  # P-ET; later surface_runoff_acc + below_ground_acc
        "surface_runoff_accumulated",
    )
    """Variables updated by the hydrology model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: list[float],
        canopy_layers: int,
        initial_soil_moisture: float,
        constants: HydroConsts,
        **kwargs: Any,
    ):
        # Sanity checks for initial soil moisture
        if type(initial_soil_moisture) is not float:
            to_raise = InitialisationError("The initial soil moisture must be a float!")
            LOGGER.error(to_raise)
            raise to_raise

        if initial_soil_moisture < 0 or initial_soil_moisture > 1:
            to_raise = InitialisationError(
                "The initial soil moisture has to be between 0 and 1!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        super().__init__(data, update_interval, **kwargs)

        # Create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.soil_layers = soil_layers
        """The number of soil layers."""
        self.update_interval
        """The time interval between model updates."""
        self.initial_soil_moisture = initial_soil_moisture
        """Initial volumetric relative water content [unitless] for all layers and grid
        cells identical."""
        self.constants = constants
        """Set of constants for the hydrology model"""
        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))
        """Set neighbours."""
        self.drainage_map = above_ground.calculate_drainage_map(
            grid=self.data.grid,
            elevation=np.array(self.data["elevation"]),
        )
        """Upstream neighbours for the calculation of accumulated runoff."""

    @classmethod
    def from_config(
        cls, data: Data, config: Config, update_interval: Quantity
    ) -> HydrologyModel:
        """Factory function to initialise the hydrology model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: A validated Virtual Rainforest model configuration object.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]
        initial_soil_moisture = config["hydrology"]["initial_soil_moisture"]

        # Load in the relevant constants
        constants = load_constants(config, "hydrology", "HydroConsts")

        LOGGER.info(
            "Information required to initialise the hydrology model successfully "
            "extracted."
        )
        return cls(
            data,
            update_interval,
            soil_layers,
            canopy_layers,
            initial_soil_moisture,
            constants,
        )

    def setup(self) -> None:
        """Function to set up the hydrology model.

        At the moment, this function initializes variables that are required to run the
        first update(). For the within grid cell hydrology, soil moisture is initialised
        homogenously for all soil layers. This design might change with the
        implementation of the SPLASH model in the plant module which will take care of
        the above-ground hydrology. Air temperature and relative humidity below the
        canopy are set to the 2 m reference values.

        For the hydrology across the grid (above-/below-ground and accumulated runoff),
        this function uses the upstream neighbours of each grid cell (see
        :func:`~virtual_rainforest.models.hydrology.above_ground.calculate_drainage_map`
        ).
        """

        # Create 1-dimensional numpy array filled with initial soil moisture values for
        # all soil layers and np.nan for atmosphere layers
        soil_moisture_values = np.repeat(
            a=[np.nan, self.initial_soil_moisture],
            repeats=[
                len(self.layer_roles) - len(self.soil_layers),
                len(self.soil_layers),
            ],
        )
        # Broadcast 1-dimensional array to grid and assign dimensions and coordinates
        self.data["soil_moisture"] = DataArray(
            np.broadcast_to(
                soil_moisture_values,
                (self.data.grid.n_cells, len(self.layer_roles)),
            ).T,
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(len(self.layer_roles)),
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": self.data.grid.cell_id,
            },
            name="soil_moisture",
        )

        # Create initial air temperature with reference temperature below the canopy
        # for first soil evaporation update.
        self.data["air_temperature"] = (
            DataArray(self.data["air_temperature_ref"].isel(time_index=0))
            .expand_dims("layers")
            .rename("air_temperature")
            .assign_coords(
                coords={
                    "layers": [self.layer_roles.index("subcanopy")],
                    "layer_roles": ("layers", ["subcanopy"]),
                    "cell_id": self.data.grid.cell_id,
                },
            )
        )

        # Create initial relative humidity with reference humidity below the canopy
        # for first soil evaporation update.
        self.data["relative_humidity"] = (
            DataArray(self.data["relative_humidity_ref"].isel(time_index=0))
            .expand_dims("layers")
            .rename("relative_humidity")
            .assign_coords(
                coords={
                    "layers": [self.layer_roles.index("subcanopy")],
                    "layer_roles": ("layers", ["subcanopy"]),
                    "cell_id": self.data.grid.cell_id,
                },
            )
        )

        # Get the runoff created by SPLASH or initial data set as the initial state:
        initial_runoff = np.array(self.data["surface_runoff"])

        # Set initial accumulated runoff to zero
        accumulated_runoff = np.zeros_like(self.data["elevation"])

        # Calculate accumulated surface runoff for each cell
        new_accumulated_runoff = above_ground.accumulate_surface_runoff(
            drainage_map=self.drainage_map,
            surface_runoff=initial_runoff,
            accumulated_runoff=accumulated_runoff,
        )

        self.data["surface_runoff_accumulated"] = DataArray(
            new_accumulated_runoff,
            dims="cell_id",
            name="surface_runoff_accumulated",
            coords={"cell_id": self.data.grid.cell_id},
        )

    def spinup(self) -> None:
        """Placeholder function to spin up the hydrology model."""

    def update(self, time_index: int) -> None:
        r"""Function to update the hydrology model.

        At the moment, this step calculates surface precipitation, soil moisture,
        vertical flow, soil evaporation, and surface runoff (per grid cell and
        accumulated), and estimates mean stream flow. These processes are problematic
        at a monthly timestep, which is why - as an intermediate step - the input
        precipitation is divided by 30 days, the same day is run 30 times, and the
        return variables are means or accumulated values.

        Surface runoff is calculated with a simple bucket model based on
        :cite:t:`davis_simple_2017`: if precipitation exceeds top soil moisture capacity
        , the excess water is added to runoff and top soil moisture is set to soil
        moisture capacity value; if the top soil is not saturated, precipitation is
        added to the current soil moisture level and runoff is set to zero. Note that
        this function will likely change with the implementation of the SPLASH model
        :cite:p:`davis_simple_2017` in the plant module which will take care of the grid
        cell based above-ground hydrology. The accumulated surface runoff is calculated
        as the sum of current runoff and the runoff from upstream cells at the previous
        time step.

        Soil evaporation is calculated with classical bulk aerodynamic formulation,
        following the so-called ':math:`\alpha` method', see
        :func:`~virtual_rainforest.models.hydrology.above_ground.calculate_soil_evaporation`
        .

        Vertical flow between soil layers is calculated using the Richards equation, see
        :func:`~virtual_rainforest.models.hydrology.below_ground.calculate_vertical_flow`
        . That function returns total vertical flow in mm. Note that there are
        severe limitations to this approach on the temporal and spatial scale of this
        model and this can only be treated as a very rough approximation!

        Soil moisture is updated by iteratively updating the soil moisture of individual
        layers under consideration of the vertical flow in and out of each layer, see
        :func:`~virtual_rainforest.models.hydrology.below_ground.update_soil_moisture`
        .

        Mean stream flow :math:`Q` is currently estimated with a simple catchment water
        balance as

        :math:`Q = P - ET - \Delta S`

        where :math:`P` is mean precipitation, :math:`ET` is evapotranspiration, and
        :math:`\Delta S` is the change in soil moisture. Note that this has to be called
        after evapotranspiration is calculated by the plant model which works as long as
        the P-model does not require moisture as an input. In the future, this
        might move to a different model or the order of models might change.

        The function requires the following input variables from the data object:

        * air temperature, [C]
        * relative humidity, []
        * atmospheric pressure, [kPa]
        * precipitation, [mm]
        * wind speed (currently not implemented, default = 0.1 m s-1)
        * leaf area index, [m m-2]
        * layer heights, [m]
        * Volumetric relative water content (previous time step), [unitless]
        * evapotranspiration (current time step), [mm]
        * accumulated surface runoff (previous time step), [mm]

        and the following soil parameters (defaults in
        :class:`~virtual_rainforest.models.hydrology.constants.HydroConsts`):

        * soil moisture capacity, [unitless]
        * soil moisture residual, [unitless]
        * soil hydraulic conductivity, [m s-1]
        * soil hydraulic gradient, [m m-1]
        * van Genuchten non-linearity parameter, dimensionless

        and a number of additional parameters that as described in detail in
        :class:`~virtual_rainforest.models.hydrology.constants.HydroConsts`.

        The function updates the following variables in the `data` object:

        * precipitation_surface, [mm]
        * soil_moisture, [-]
        * surface_runoff, [mm], equivalent to SPLASH runoff
        * vertical_flow, [mm/timestep]
        * soil_evaporation, [mm]
        * stream_flow, [mm/timestep], currently simply P-ET
        * surface_runoff_accumulated, [mm]
        """
        # Determine number of days, currently only 30 days (=1 month)
        if self.update_interval != Quantity("1 month"):
            to_raise = NotImplementedError("This time step is currently not supported.")
            LOGGER.error(to_raise)
            raise to_raise

        days: int = 30

        # Select variables at relevant heights for current time step
        current_precipitation = (
            self.data["precipitation"].isel(time_index=time_index) / days
        ).to_numpy()
        leaf_area_index_sum = self.data["leaf_area_index"].sum(dim="layers").to_numpy()
        evapotranspiration = (
            self.data["evapotranspiration"].sum(dim="layers") / days
        ).to_numpy()
        subcanopy_temperature = (
            self.data["air_temperature"]
            .isel(layers=self.layer_roles.index("subcanopy"))
            .to_numpy()
        )
        subcanopy_humidity = (
            self.data["relative_humidity"]
            .isel(layers=self.layer_roles.index("subcanopy"))
            .to_numpy()
        )
        subcanopy_pressure = (
            self.data["atmospheric_pressure_ref"].isel(time_index=time_index).to_numpy()
        )
        soil_layer_heights = (
            self.data["layer_heights"]
            .where(self.data["layer_heights"].layer_roles == "soil")
            .dropna(dim="layers")
        ).to_numpy()

        # Calculate thickness of each layer, [mm]
        soil_layer_thickness = calculate_layer_thickness(
            soil_layer_heights=soil_layer_heights,
            meters_to_mm=self.constants.meters_to_mm,
        )

        # Convert soil moisture (volumetric relative water content) to mm as follows:
        # water content in mm = relative water content / 100 * depth in mm
        # Example: for 20% water at 40 cm this would be: 20/100 * 400mm = 80 mm
        soil_moisture_mm = (
            self.data["soil_moisture"]
            .where(self.data["soil_moisture"].layer_roles == "soil")
            .dropna(dim="layers")
            * soil_layer_thickness
        ).to_numpy()

        top_soil_moisture_capacity_mm = (
            self.constants.soil_moisture_capacity * soil_layer_thickness[0]
        )
        top_soil_moisture_residual_mm = (
            self.constants.soil_moisture_residual * soil_layer_thickness[0]
        )

        # Create lists for output variables to store daily data
        daily_lists: dict = {name: [] for name in self.vars_updated}

        for day in np.arange(days):
            # Interception of water in canopy, [mm]
            interception = above_ground.estimate_interception(
                leaf_area_index=leaf_area_index_sum,
                precipitation=current_precipitation,
                intercept_param_1=self.constants.intercept_param_1,
                intercept_param_2=self.constants.intercept_param_2,
                intercept_param_3=self.constants.intercept_param_3,
                veg_density_param=self.constants.veg_density_param,
            )

            # Precipitation that reaches the surface per day, [mm]
            precipitation_surface = current_precipitation - interception
            daily_lists["precipitation_surface"].append(precipitation_surface)

            # Calculate how much water can be added to soil before capacity is reached,
            # [mm]
            free_capacity_mm = (
                self.constants.soil_moisture_capacity * soil_layer_thickness
                - soil_moisture_mm
            )

            # Calculate daily surface runoff of each grid cell, [mm]; replace by SPLASH
            surface_runoff = np.where(
                precipitation_surface > free_capacity_mm[0],
                precipitation_surface - free_capacity_mm[0],
                0,
            )
            daily_lists["surface_runoff"].append(surface_runoff)

            # Calculate top soil moisture after infiltration, [mm]
            soil_moisture_infiltrated = np.clip(
                soil_moisture_mm[0] + precipitation_surface,
                0,
                top_soil_moisture_capacity_mm,
            )

            # Calculate daily soil evaporation, [mm]
            top_soil_moisture_vol = soil_moisture_infiltrated / soil_layer_thickness[0]

            soil_evaporation = above_ground.calculate_soil_evaporation(
                temperature=subcanopy_temperature,
                relative_humidity=subcanopy_humidity,
                atmospheric_pressure=subcanopy_pressure,
                soil_moisture=top_soil_moisture_vol,
                soil_moisture_residual=self.constants.soil_moisture_residual,
                wind_speed=0.1,  # m/s TODO wind_speed in data object
                celsius_to_kelvin=self.constants.celsius_to_kelvin,
                density_air=self.constants.density_air,
                latent_heat_vapourisation=self.constants.latent_heat_vapourisation,
                gas_constant_water_vapour=self.constants.gas_constant_water_vapour,
                heat_transfer_coefficient=self.constants.heat_transfer_coefficient,
            )
            daily_lists["soil_evaporation"].append(soil_evaporation)

            # Calculate top soil moisture after evap and combine with lower layers, [mm]
            soil_moisture_evap: NDArray[np.float32] = np.concatenate(
                (
                    np.expand_dims(
                        np.clip(
                            (soil_moisture_infiltrated - soil_evaporation),
                            top_soil_moisture_residual_mm,
                            top_soil_moisture_capacity_mm,
                        ),
                        axis=0,
                    ),
                    soil_moisture_mm[1:],
                )
            )

            # Calculate vertical flow between soil layers in mm per time step
            # Note that there are severe limitations to this approach on the temporal
            # spatial scale of this model and this can only be treated as a very rough
            # approximation to discuss nutrient leaching.
            vertical_flow = below_ground.calculate_vertical_flow(
                soil_moisture=soil_moisture_evap / soil_layer_thickness,  # vol
                soil_layer_thickness=soil_layer_thickness,  # mm
                soil_moisture_capacity=self.constants.soil_moisture_capacity,  # vol
                soil_moisture_residual=self.constants.soil_moisture_residual,  # vol
                hydraulic_conductivity=self.constants.hydraulic_conductivity,  # m/s
                hydraulic_gradient=self.constants.hydraulic_gradient,  # m/m
                nonlinearily_parameter=self.constants.nonlinearily_parameter,
                groundwater_capacity=self.constants.groundwater_capacity,
                seconds_to_day=self.constants.seconds_to_day,
            )
            daily_lists["vertical_flow"].append(vertical_flow)

            # Update soil moisture by +/- vertical flow to each layer and remove root
            # water uptake by plants (transpiration), [mm]
            soil_moisture_updated = below_ground.update_soil_moisture(
                soil_moisture=soil_moisture_evap,
                vertical_flow=vertical_flow,
                evapotranspiration=evapotranspiration,
                soil_moisture_capacity=(
                    self.constants.soil_moisture_capacity * soil_layer_thickness
                ),
                soil_moisture_residual=(
                    self.constants.soil_moisture_residual * soil_layer_thickness
                ),
            )

            daily_lists["soil_moisture"].append(
                soil_moisture_updated / soil_layer_thickness
            )

            # update soil_moisture_mm for next day
            soil_moisture_mm = soil_moisture_updated

        # create output dict as intermediate step to not overwrite data directly
        soil_hydrology = {}

        # Calculate monthly accumulated values
        for var in ["precipitation_surface", "surface_runoff", "soil_evaporation"]:
            soil_hydrology[var] = DataArray(
                np.sum(np.stack(daily_lists[var], axis=1), axis=1),
                dims="cell_id",
                coords={"cell_id": self.data.grid.cell_id},
            )

        soil_hydrology["vertical_flow"] = DataArray(
            np.sum(daily_lists["vertical_flow"], axis=(0, 1)),
            dims="cell_id",
            coords={"cell_id": self.data.grid.cell_id},
        )

        # Return mean soil moisture, [-], and add atmospheric layers (nan)
        soil_hydrology["soil_moisture"] = DataArray(
            np.concatenate(
                (
                    np.full(
                        (
                            len(self.layer_roles) - self.layer_roles.count("soil"),
                            self.data.grid.n_cells,
                        ),
                        np.nan,
                    ),
                    np.mean(
                        np.stack(daily_lists["soil_moisture"], axis=0),
                        axis=0,
                    ),
                ),
            ),
            dims=self.data["soil_moisture"].dims,
            coords=self.data["soil_moisture"].coords,
        )

        # TODO Convert to matric potential

        # Calculate accumulated surface runoff for model time step
        # Get the runoff created by SPLASH or initial data set
        single_cell_runoff = np.array(soil_hydrology["surface_runoff"])

        # Get accumulated runoff from previous time step
        accumulated_runoff = np.array(self.data["surface_runoff_accumulated"])

        # Calculate accumulated runoff for each cell (me + sum of upstream neighbours)
        new_accumulated_runoff = above_ground.accumulate_surface_runoff(
            drainage_map=self.drainage_map,
            surface_runoff=single_cell_runoff,
            accumulated_runoff=accumulated_runoff,
        )

        soil_hydrology["surface_runoff_accumulated"] = DataArray(
            new_accumulated_runoff, dims="cell_id"
        )

        # Calculate stream flow as Q= P-ET-dS ; vertical flow is not considered
        # TODO add vertical and below-ground horizontal flow
        # The maximum stream flow capacity is set to an arbitray value, could be used to
        # flag flood events

        soil_moisture_change = np.sum(
            np.array(
                daily_lists["soil_moisture"][-1] - daily_lists["soil_moisture"][0]
            ),
            axis=0,
        )

        soil_hydrology["stream_flow"] = DataArray(
            np.clip(
                (
                    soil_hydrology["precipitation_surface"]
                    - evapotranspiration * days
                    - soil_moisture_change
                ),
                0,
                HydroConsts.stream_flow_capacity,
            ).squeeze(),
            dims="cell_id",
        )

        # Update data object
        self.data.add_from_dict(output_dict=soil_hydrology)

    def cleanup(self) -> None:
        """Placeholder function for hydrology model cleanup."""


def calculate_layer_thickness(
    soil_layer_heights: NDArray[np.float32],
    meters_to_mm: float,
) -> NDArray[np.float32]:
    """Calculate layer thickness from soil layer depth profile.

    Args:
        soil_layer_heights: soil layer heights, [m]
        meters_to_mm: meter to millimeter conversion factor

    Returns:
        soil layer thickness, mm
    """
    return np.array(
        [
            (soil_layer_heights[i] - soil_layer_heights[i - 1]) * (-meters_to_mm)
            if i > 0
            else soil_layer_heights[0] * (-meters_to_mm)
            for i in range(len(soil_layer_heights))
        ],
    )
