"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_model` module
creates a
:class:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel.from_config`
exists in a
more complete state, and unpacks a small number of parameters from our currently pretty
minimal configuration dictionary. These parameters are then used to generate a class
instance. If errors crop here when converting the information from the config dictionary
to the required types they are caught and then logged, and at the end of the unpacking
an error is thrown. This error should be caught and handled by downstream functions so
that all model configuration failures can be reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any, Union

import numpy as np
import xarray as xr
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.hydrology.hydrology_constants import HydrologyParameters


class HydrologyModel(BaseModel):
    """A class describing the hydrology model.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        initial_soil_moisture: The initial soil moisture for all layers.

    Raises:
        InitialisationError: when initial soil moisture is out of bounds.
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
    )
    # TODO add time dimension
    # TODO at the momement, the reference height is at 2m. This will change to a higher
    # atmospheric level, likely 10m. Then this first step will return faulty values.
    """The required variables and axes for the hydrology model"""
    vars_updated = [
        "soil_moisture",
        "surface_runoff",
        "vertical_flow",
        "soil_evaporation",
    ]
    """Variables updated by the hydrology model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: int,
        canopy_layers: int,
        initial_soil_moisture: float,
        **kwargs: Any,
    ):
        # sanity checks for initial soil moisture
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

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.update_interval
        """The time interval between model updates."""
        self.initial_soil_moisture = initial_soil_moisture
        """Initial soil moisture for all layers and grill cells identical."""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> HydrologyModel:
        """Factory function to initialise the hydrology model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]
        initial_soil_moisture = config["hydrology"]["initial_soil_moisture"]

        LOGGER.info(
            "Information required to initialise the hydrology model successfully "
            "extracted."
        )
        return cls(
            data, update_interval, soil_layers, canopy_layers, initial_soil_moisture
        )

    def setup(self) -> None:
        """Function to set up the hydrology model.

        At the moment, this function initializes soil moisture homogenously for all
        soil layers and initializes air temperature and relative humidity to calculate
        soil evaporation and soil moisture for the first update().
        """

        # Create 1-dimensional numpy array filled with initial soil moisture values for
        # all soil layers and np.nan for atmosphere layers
        soil_moisture_values = np.repeat(
            a=[np.nan, self.initial_soil_moisture],
            repeats=[
                len(self.layer_roles) - self.layer_roles.count("soil"),
                self.layer_roles.count("soil"),
            ],
        )
        # Broadcast 1-dimensional array to grid and assign dimensions and coordinates
        self.data["soil_moisture"] = DataArray(
            np.broadcast_to(
                soil_moisture_values,
                (len(self.data.grid.cell_id), len(self.layer_roles)),
            ).T,
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(len(self.layer_roles)),
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": self.data.grid.cell_id,
            },
            name="soil_moisture",
        )

        # create initial air temperature with reference temperature below the canopy
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

        # create initial relative humidity  with reference humidity below the canopy
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

    def spinup(self) -> None:
        """Placeholder function to spin up the hydrology model."""

    def update(self, time_index: int) -> None:
        """Function to update the hydrology model.

        At the moment, this step calculates soil moisture, vertical flow, soil
        evaporation, and surface runoff. The processes are described in detail in the
        :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_soil_moisture`
        and
        :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_vertical_flow`
        and
        :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_soil_evaporation`
        functions.

        The water extracted by plant roots (= evapotranspiration) is not included. In
        the Virtual Rainforest simulation, the reduction of soil moisture due to
        evapotranspiration will be considered after running the plant model.

        TODO make it less nested so the number of inputs are sensible?
        TODO Implement horizontal sub-surface flow and stream flow
        """

        # Interception: precipitation at the surface is reduced as a function of leaf
        # area index
        precipitation_surface = self.data["precipitation"].isel(
            time_index=time_index
        ) * (
            1
            - HydrologyParameters["water_interception_factor"]
            * self.data["leaf_area_index"].sum(dim="layers")
        )

        # Calculate soil moisture, [relative water content], vertical flow, [m3/time
        # step], soil evaporation, [mm], and surface runoff, [mm]
        soil_hydrology = calculate_soil_moisture(
            layer_roles=self.layer_roles,
            layer_heights=self.data["layer_heights"],
            precipitation_surface=precipitation_surface,
            current_soil_moisture=self.data["soil_moisture"],
            temperature=self.data["air_temperature"]
            .isel(layers=self.layer_roles.index("subcanopy"))
            .drop_vars(["layer_roles", "layers"]),
            relative_humidity=self.data["relative_humidity"]
            .isel(layers=self.layer_roles.index("subcanopy"))
            .drop_vars(["layer_roles", "layers"]),
            atmospheric_pressure=(
                (self.data["atmospheric_pressure_ref"]).isel(time_index=time_index)
            ),
            wind_speed=0.1,  # TODO include wind in data set?
            soil_moisture_capacity=HydrologyParameters["soil_moisture_capacity"],
        )

        # update data object
        self.data.add_from_dict(output_dict=soil_hydrology)

    def cleanup(self) -> None:
        """Placeholder function for hydrology model cleanup."""


def calculate_soil_moisture(
    layer_roles: list,
    layer_heights: DataArray,
    precipitation_surface: DataArray,
    current_soil_moisture: DataArray,
    temperature: DataArray,
    relative_humidity: DataArray,
    atmospheric_pressure: DataArray,
    wind_speed: Union[DataArray, float] = 0.1,
    soil_moisture_capacity: Union[DataArray, float] = HydrologyParameters[
        "soil_moisture_capacity"
    ],
    meters_to_millimeters: float = HydrologyParameters["meters_to_millimeters"],
) -> dict[str, DataArray]:
    """Calculate soil moisture, surface runoff, soil evaporation, and vertical flow.

    Soil moisture and surface runoff are calculated with a simple bucket model based on
    :cite:t:`davis_simple_2017`: if precipitation exceeds soil moisture capacity, the
    excess water is added to runoff and soil moisture is set to soil moisture capacity
    value; if the soil is not saturated, precipitation is added to the current soil
    moisture level and runoff is set to zero.

    Soil evaporation is calculated with classical bulk aerodynamic formulation,
    following the so-called alpha method, see
    :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_soil_evaporation`
    .

    Vertical flow is calculated using the Richards equation, see
    :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_vertical_flow`
    .

    Args:
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        layer_heights: heights of all layers, [m]
        precipitation_surface: precipitation that reaches surface, [mm]
        current_soil_moisture: current soil moisture at top soil layer, [mm]
        temperature: air temperature at reference height, [C]
        relative_humidity: relative humidity at reference height, []
        atmospheric_pressure: atmospheric pressure at reference height, [kPa]
        wind_speed: wind speed at reference height, [m s-1]
        soil_moisture_capacity: soil moisture capacity (optional), [relative water
            content]
        meters_to_millimeters: conversion factor from meters to millimeters

    Returns:
        soil moisture, [relative water content], vertical flow, [m3/timestep], surface
            runoff, [mm], soil evaporation, [mm]
    """

    output = {}

    # calculate soil depth in mm
    soil_depth = (
        layer_heights.isel(
            layers=np.arange(
                len(layer_roles) - layer_roles.count("soil"), len(layer_roles)
            )
        ).sum(dim="layers")
    ) * (-meters_to_millimeters)

    # Calculate how much water can be added to soil before capacity is reached.
    # To find out how much rain can be taken up by the topsoil before rain goes to
    # runoff, the relative water content (between 0 and 1) is converted to mm with this
    # equation:
    # water content in mm = relative water content / 100 * depth in mm
    # Example: for 20% water at 40 cm this would be: 20/100 * 400mm = 80 mm
    available_capacity_mm = (
        soil_moisture_capacity - current_soil_moisture.mean(dim="layers")
    ) * soil_depth

    # Find grid cells where precipitation exceeds available capacity
    surface_runoff_cells = precipitation_surface.where(
        precipitation_surface > available_capacity_mm
    )

    # Calculate runoff in mm
    output["surface_runoff"] = (
        DataArray(surface_runoff_cells.data - available_capacity_mm.data)
        .fillna(0)
        .rename("surface_runoff")
        .rename({"dim_0": "cell_id"})
        .assign_coords({"cell_id": current_soil_moisture.cell_id})
    )

    # Calculate total water in mm in each grid cell
    total_water_mm = (
        current_soil_moisture.mean(dim="layers") * soil_depth + precipitation_surface
    )

    # Calculate relative soil moisture incl infiltration and cap to capacity
    soil_moisture_infiltrated = DataArray(
        np.clip(total_water_mm / soil_depth, 0, soil_moisture_capacity)
    )

    # Calculate soil (surface) evaporation
    output["soil_evaporation"] = calculate_soil_evaporation(
        temperature=temperature,
        relative_humidity=relative_humidity,
        atmospheric_pressure=atmospheric_pressure,
        soil_moisture=soil_moisture_infiltrated,
        wind_speed=wind_speed,
    )

    # Calculate soil mositure after evaporation
    soil_moisture_residual = (
        soil_moisture_infiltrated - output["soil_evaporation"] / soil_depth
    )

    # Calculate vertical flow in mm per time step for mean soil moisture
    output["vertical_flow"] = calculate_vertical_flow(
        soil_moisture_residual=soil_moisture_residual,
        soil_depth=soil_depth,
        soil_moisture_capacity=soil_moisture_capacity,
    )

    # Reduce mean soil moisture by vertical flow - this shouldn't get negative
    soil_moisture_reduced = DataArray(
        np.clip(
            soil_moisture_infiltrated - (output["vertical_flow"] / soil_depth),
            0,
            soil_moisture_capacity,
        ),
    )

    # Expand to all soil layers and add atmospheric layers (nan)
    output["soil_moisture"] = xr.concat(
        [
            DataArray(
                np.full(
                    (
                        len(layer_roles) - layer_roles.count("soil"),
                        len(layer_heights.cell_id),
                    ),
                    np.nan,
                ),
                dims=["layers", "cell_id"],
            ),
            soil_moisture_reduced.expand_dims(
                dim={"layers": layer_roles.count("soil")},
            ),
        ],
        dim="layers",
    ).assign_coords(
        coords={
            "layers": np.arange(len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
            "cell_id": layer_heights.cell_id,
        }
    )

    return output


def calculate_vertical_flow(
    soil_moisture_residual: DataArray,
    soil_depth: DataArray,
    soil_moisture_capacity: Union[float, DataArray] = (
        HydrologyParameters["soil_moisture_capacity"]
    ),
    hydraulic_conductivity: Union[float, DataArray] = (
        HydrologyParameters["hydraulic_conductivity"]
    ),
    hydraulic_gradient: Union[float, DataArray] = (
        HydrologyParameters["hydraulic_gradient"]
    ),
    timestep_conversion_factor: float = (HydrologyParameters["seconds_to_month"]),
    steepness_water_retention_curve: Union[float, DataArray] = (
        HydrologyParameters["steepness_water_retention_curve"]
    ),
    nonlinearily_parameter: Union[float, DataArray] = (
        HydrologyParameters["nonlinearily_parameter"]
    ),
    meters_to_millimeters: float = HydrologyParameters["meters_to_millimeters"],
) -> DataArray:
    """Calculate vertical water flow through soil column.

    To calculate the flow of water through unsaturated soil, this function uses the
    Richards equation which considers both the hydraulic conductivity and the soil water
    retention curve to account for the varying moisture content.

    First, the function calculates the effective hydraulic conductivity based on the
    moisture content using the van Genuchten equation. Then, it applies Darcy's law to
    calculate the water flow rate considering the effective hydraulic conductivity.

    Args:
        soil_moisture_residual: residual soil moisture, [relative water content]
        soil_depths: soil depths = length of the flow path, [m]
        soil_moisture_capacity: soil moisture capacity, [relative water content]
        hydraulic_conductivity: hydraulic conductivity of soil, [m/s]
        hydraulic_gradient: hydraulic gradient (change in hydraulic head) along the flow
            path, positive values indicate downward flow, [m/m]
        timestep_conversion_factor: factor to convert flow from m3/s to model time step
        steepness_water_retention_curve: dimensionless parameter in van Genuchten model
            that describes the steepness of the water retention curve. Smaller values
            correspond to steeper curves, indicating that the soil retains water at a
            higher matric potential. Larger values result in flatter curves, indicating
            that the soil retains water at a lower matric potential.
        nonlinearily_parameter: dimensionless parameter in van Genuchten model that
            describes the degree of nonlinearity of the relationship between the
            volumetric water content and the soil matric potential.

    Returns:
        volumetric flow rate of water, [m3/timestep]
    """
    # Define the soil water retention curve parameters (van Genuchten model)
    # TODO abs(hydraulic) gradient support for datatype to allow negative values
    theta = soil_moisture_capacity - (
        soil_moisture_capacity - soil_moisture_residual
    ) / (
        1
        + (steepness_water_retention_curve * hydraulic_gradient)
        ** nonlinearily_parameter
    ) ** (
        1 - 1 / nonlinearily_parameter
    )

    # Calculate the effective hydraulic conductivity
    m = 1 - 1 / nonlinearily_parameter
    effective_conductivity = (
        hydraulic_conductivity
        * (theta / soil_moisture_capacity) ** (0.5)
        * (1 - (1 - (theta / soil_moisture_capacity) ** (1 / m)) ** m) ** 2
    )

    # Calculate the water flow rate in m3 per seconds and convert to mm per timestep
    return (
        effective_conductivity
        * hydraulic_gradient
        / soil_depth
        * meters_to_millimeters
        * timestep_conversion_factor
    )


def calculate_soil_evaporation(
    temperature: DataArray,
    relative_humidity: DataArray,
    atmospheric_pressure: DataArray,
    soil_moisture: DataArray,
    wind_speed: Union[float, DataArray] = 0.5,
    celsius_to_kelvin: float = HydrologyParameters["celsius_to_kelvin"],  # TODO move
    density_air: float = HydrologyParameters["density_air"],
    latent_heat_vapourisation: float = HydrologyParameters["latent_heat_vapourisation"],
    gas_constant_water_vapour: float = HydrologyParameters["gas_constant_water_vapour"],
    heat_transfer_coefficient: float = HydrologyParameters["heat_transfer_coefficient"],
    flux_to_mm_conversion: float = HydrologyParameters["flux_to_mm_conversion"],
    timestep_conversion_factor: float = HydrologyParameters["seconds_to_month"],
) -> DataArray:
    """Calculate soil evaporation based classical bulk aerodynamic formulation.

    TODO write description and add references
    TODO move constants to HydrologyParameters or CoreConstants and check values

    Args:
        temperature: air temperature at reference height, [C]
        relative_humidity: relative humidity at reference height, []
        atmospheric_pressure: atmospheric pressure at reference height, [kPa]
        soil_moisture: top soil moisture, [relative water content]
        wind_speed: wind speed at reference height, [m s-1]
        celsius_to_kelvin: factor to convert teperature from Celsius to Kelvin
        density_air: density if air, [kg m-3]
        latent_heat_vapourisation: latent heat of vapourisation, [J kg-1]
        gas_constant_water_vapour: gas constant for water vapour, [J kg-1 K-1]
        heat_transfer_coefficient: heat transfer coefficient of air
        flux_to_mm_conversion: flux to mm conversion factor

    Returns:
        soil evaporation, [mm]
    """

    # Convert temperature to Kelvin
    temperature_k = temperature + celsius_to_kelvin

    # Estimate alpha using the Barton (1979) equation
    barton_ratio = (1.8 * soil_moisture) / (soil_moisture + 0.3)
    alpha = np.where(barton_ratio > 1, 1, barton_ratio)

    saturation_vapour_pressure = DataArray(
        0.6112 * np.exp((17.67 * (temperature_k)) / (temperature_k + 243.5))
    )

    saturated_specific_humidity = DataArray(
        (gas_constant_water_vapour / latent_heat_vapourisation)
        * (
            saturation_vapour_pressure
            / (atmospheric_pressure - saturation_vapour_pressure)
        ),
        dims=temperature.dims,
    )

    specific_humidity_air = DataArray(
        (relative_humidity * saturated_specific_humidity) / 100,
        dims=relative_humidity.dims,
        name="specific_humidity",
    )

    aerodynamic_resistance = heat_transfer_coefficient / np.sqrt(wind_speed)

    evaporative_flux = (density_air / aerodynamic_resistance) * (
        alpha * saturation_vapour_pressure - specific_humidity_air
    )

    return DataArray(  # TODO check this
        (evaporative_flux / flux_to_mm_conversion) / timestep_conversion_factor
    )
