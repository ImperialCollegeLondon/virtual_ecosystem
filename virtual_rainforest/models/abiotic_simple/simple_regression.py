r"""The ``models.abiotic_simple.simple_regression`` module uses linear regression
and logarithmic interpolation to calculate atmospheric temperature and humidity profiles
as a function of leaf area index and canopy layer height. The relationships are derived
from :cite:t:`hardwick_relationship_2015` and :cite:t:`jucker_canopy_2018`.
Soil temperature is interpolated between the surface layer and the air
temperature at 1 m depth which equals the mean annual temperature.
The module also provides a constant vertical profile of atmospheric pressure and
:math:`\ce{CO2}`.
Soil moisture and surface runoff are calculated with a simple bucket model based on
:cite:t:`davis_simple_2017`.
"""  # noqa: D205, D415

from typing import Dict, List, Tuple, Union

import numpy as np
import xarray as xr
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER

MicroclimateGradients: Dict[str, float] = {
    "air_temperature_gradient": -1.27,
    "relative_humidity_gradient": 5.4,
    "vapour_pressure_deficit_gradient": -252.24,
}
"""Gradients for linear regression to calculate air temperature, relative humidity, and
vapour pressure deficit as a function of leaf area index from
:cite:t:`hardwick_relationship_2015`.
"""

MicroclimateParameters: Dict[str, float] = {
    "soil_moisture_capacity": 150,
    "water_interception_factor": 0.1,
    "saturation_vapour_pressure_factor1": 0.61078,
    "saturation_vapour_pressure_factor2": 7.5,
    "saturation_vapour_pressure_factor3": 237.3,
}
"""Parameters for simple abiotic regression model."""


def setup_simple_regression(
    layer_roles: List[str],
    data: Data,
    initial_soil_moisture: float = 50,
) -> List[DataArray]:
    r"""Set up abiotic environment variables.

    This function initialises all abiotic variables as DataArrays filled with NaN,
    except for soil moisture which has a homogenous value across all soil layers.

    Args:
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        data: Data object
        initial_soil_moisture: initial soil moisture

    Returns:
        list of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa],
        atmospheric :math:`\ce{CO2}` [ppm], soil moisture [-], and surface runoff [mm]
    """

    output = []

    # Initialise DataArrays filled with NaN
    air_temperature = DataArray(
        np.full((len(layer_roles), len(data.grid.cell_id)), np.nan),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
        name="air_temperature",
    )
    output.append(air_temperature)

    # copy and assign new variable names
    for name in (
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
        "surface_runoff",
    ):
        output.append(air_temperature.copy().rename(name))

    # The initial soil moisture constant in all soil layers, all other layers set to NaN
    soil_moisture = air_temperature.copy().rename("soil_moisture")
    soil_moisture = soil_moisture.where(
        soil_moisture.coords["layer_roles"] != "soil",
        initial_soil_moisture,
    )
    output.append(soil_moisture)

    return output


def run_simple_regression(
    data: Data,
    layer_roles: List[str],
    time_index: int,  # could be datetime?
    MicroclimateGradients: Dict[str, float] = MicroclimateGradients,
    water_interception_factor: Union[DataArray, float] = MicroclimateParameters[
        "water_interception_factor"
    ],
    soil_moisture_capacity: Union[DataArray, float] = MicroclimateParameters[
        "soil_moisture_capacity"
    ],
) -> List[DataArray]:
    r"""Calculate simple microclimate.

    This function uses empirical relationships between leaf area index (LAI) and
    atmospheric temperature and relative humidity to derive logarithmic
    profiles of atmospheric temperature and humidity from external climate data such as
    regional climate models or satellite observations. For below canopy values (1.5 m),
    the implementation is based on :cite:t:`hardwick_relationship_2015` as

    :math:`y = m * LAI + c`

    where :math:`y` is the variable of interest, math:`m` is the gradient
    (:data:`~virtual_rainforest.models.abiotic_simple.simple_regression.MicroclimateGradients`)
    and :math:`c` is the intersect which we set to the
    external data values. We assume that the gradient remains constant.

    The other atmospheric layers are calculated by logaritmic regression and
    interpolation between the input at the top of the canopy and the 1.5 m values.
    Soil temperature is interpolated between the surface layer and the temperature at
    1 m depth which equals the mean annual temperature.
    The function also provides constant atmospheric pressure and :math:`\ce{CO2}` for
    all atmospheric levels.

    Soil moisture and surface runoff are calculated with a simple bucket model based
    on :cite:t:`davis_simple_2017`: if
    precipitation exceeds soil moisture capacity (see
    :data:`~virtual_rainforest.models.abiotic_simple.simple_regression.MicroclimateParameters`)
    , the excess water is added to runoff and soil moisture is set to soil moisture
    capacity value; if the soil is not saturated, precipitation is added to the current
    soil moisture level and runoff is set to zero.

    The `layer_roles` list is composed of the following layers (index 0 above canopy):

    * above canopy (canopy height + reference measurement height, typically 2m)
    * canopy layers (maximum of ten layers, minimum one layers)
    * subcanopy (1.5 m)
    * surface layer
    * soil layers (currently one near surface layer and one layer at 1 m below ground)

    The function expects a data object with the following variables:

    * air_temperature_ref
    * relative_humidity_ref
    * atmospheric_pressure_ref
    * atmospheric_co2_ref
    * leaf_area_index
    * layer_heights
    * precipitation
    * soil_moisture

    Args:
        data: Data object
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        time_index: time index, integer
        MicroclimateGradients: gradients for linear regression
            :cite:p:`hardwick_relationship_2015`
        water_interception_factor: Factor that determines how much rainfall is
            intercepted by stem and canopy
        soil_moisture_capacity: soil moisture capacity for water

    Returns:
        list of air temperature, relative humidity, vapour pressure deficit, soil
        temperature, atmospheric pressure, atmospheric :math:`\ce{CO2}`, soil moisture,
        and surface runoff
    """

    # TODO correct gap between 1.5 m and 2m reference height for LAI = 0
    output = []

    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # Mean air temperature profile, [C]
    air_temperature = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time=time_index),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=MicroclimateGradients["air_temperature_gradient"],
    ).rename("air_temperature")
    output.append(air_temperature)

    # Mean relative humidity profile, []
    relative_humidity = log_interpolation(
        data=data,
        reference_data=data["relative_humidity_ref"].isel(time=time_index),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=100,
        lower_bound=0,
        gradient=MicroclimateGradients["relative_humidity_gradient"],
    ).rename("relative_humidity")
    output.append(relative_humidity)

    # Mean vapour pressure deficit, [kPa]
    # calculate vapour pressure deficit at reference height first
    vapour_pressure_deficit_ref = calculate_vapour_pressure_deficit(
        temperature=data["air_temperature_ref"].isel(time=time_index),
        relative_humidity=data["relative_humidity_ref"].isel(time=time_index),
    )

    vapour_pressure_deficit = log_interpolation(
        data=data,
        reference_data=vapour_pressure_deficit_ref,
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=10,
        lower_bound=0,
        gradient=MicroclimateGradients["vapour_pressure_deficit_gradient"],
    ).rename("vapour_pressure_deficit")
    output.append(vapour_pressure_deficit)

    # Mean soil temperature profile, [C]
    soil_temperature = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        layer_roles=layer_roles,
        surface_temperature=air_temperature.isel(
            layers=len(layer_roles) - layer_roles.count("soil") - 1
        ),
        mean_annual_temperature=data["mean_annual_temperature"],
    )
    output.append(soil_temperature)

    # Mean atmospheric pressure profile, [kPa]
    atmospheric_pressure = data["atmospheric_pressure"].where(
        data["atmospheric_pressure"].coords["layer_roles"] == "soil",
        (data["atmospheric_pressure_ref"].isel(time=time_index)),
    )
    output.append(atmospheric_pressure)

    # Mean atmospheric C02 profile, [ppm]
    atmospheric_co2 = data["atmospheric_co2"].where(
        data["atmospheric_co2"].coords["layer_roles"] == "soil",
        (data["atmospheric_co2_ref"].isel(time=time_index)),
    )
    output.append(atmospheric_co2)

    # Precipitation at the surface is reduced as a function of leaf area index
    precipitation_surface = data["precipitation"].isel(time=time_index) * (
        1 - water_interception_factor * data["leaf_area_index"].sum(dim="layers")
    )

    # Mean soil moisture profile, [] and Runoff, [mm]
    soil_moisture, surface_run_off = calculate_soil_moisture(
        layer_roles=layer_roles,
        precipitation_surface=precipitation_surface,
        current_soil_moisture=data["soil_moisture"],
        soil_moisture_capacity=soil_moisture_capacity,
    )

    output.append(soil_moisture)
    output.append(surface_run_off)
    return output


# supporting functions
def logarithmic(x: DataArray, gradient: float, intercept: float) -> DataArray:
    """Logarithmic function.

    Args:
        x: x values
        gradient: gradient
        intercept: intercept

    Returns:
        y values
    """
    for number in x:
        if number < 0:
            to_raise = ValueError("x values must be positive!")
            LOGGER.error(to_raise)
            raise to_raise

    return DataArray(gradient * np.log(x) + intercept)


def log_interpolation(
    data: Data,
    reference_data: DataArray,
    leaf_area_index_sum: DataArray,
    layer_roles: List,
    layer_heights: DataArray,
    upper_bound: float,
    lower_bound: float,
    gradient: float,
) -> DataArray:
    """LAI regression and logarithmic interpolation of variables for vertical profile.

    Args:
        data: Data object
        reference_data: input variable at reference height
        leaf_area_index_sum: leaf area index summed over all layers, [m m-1]
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
        layer_heights: vertical layer heights, [m]
        lower_bound: minimum allowed value
        upper_bound: maximum allowed value
        gradient: gradient of regression from :cite:t:`hardwick_relationship_2015`

    Returns:
        vertical profile of provided variable
    """

    # Calculate microclimatic variable at 1.5 m as function of leaf area index
    lai_regression = DataArray(
        leaf_area_index_sum * gradient + reference_data, dims="cell_id"
    )

    # Calculate per cell slope and intercept for logarithmic within-canopy profile
    slope = (reference_data - lai_regression) / (
        np.log(layer_heights.isel(layers=0)) - np.log(1.5)
    )
    intercept = lai_regression - slope * np.log(1.5)

    # Calculate the values within cells by layer
    layer_values = np.log(layer_heights) * slope + intercept

    # set upper and lower bounds
    return DataArray(
        np.clip(layer_values, lower_bound, upper_bound),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
    )


def calculate_saturation_vapour_pressure(
    temperature: DataArray,
    factor1: float = MicroclimateParameters["saturation_vapour_pressure_factor1"],
    factor2: float = MicroclimateParameters["saturation_vapour_pressure_factor2"],
    factor3: float = MicroclimateParameters["saturation_vapour_pressure_factor3"],
) -> DataArray:
    r"""Calculate saturation vapour pressure.

    Saturation vapour pressure :math:`e_{s} (T)` is here calculated as

    :math:`e_{s}(T) = 0.61078 exp(\frac{7.5 T}{T + 237.3})`

    where :math:`T` is temperature in degree C .

    Args:
        temperature: air temperature, [C]
        factor1: factor 1 in saturation vapour pressure calculation
        factor2: factor 2 in saturation vapour pressure calculation
        factor3: factor 3 in saturation vapour pressure calculation

    Returns:
        saturation vapour pressure, kPa
    """

    return DataArray(
        factor1 * np.exp((factor2 * temperature) / (temperature + factor3))
    ).rename("saturation_vapour_pressure")


def calculate_vapour_pressure_deficit(
    temperature: DataArray,
    relative_humidity: DataArray,
) -> DataArray:
    """Calculate vapour pressure deficit.

    Vapor pressure deficit is defined as the difference between saturated vapour
    pressure and actual vapour pressure.

    Args:
        temperature: temperature, [C]
        relative_humidity: relative humidity, []

    Return:
        vapour pressure deficit, [kPa]
    """
    saturation_vapour_pressure = calculate_saturation_vapour_pressure(temperature)
    actual_vapour_pressure = saturation_vapour_pressure * (relative_humidity / 100)

    return saturation_vapour_pressure - actual_vapour_pressure


def interpolate_soil_temperature(
    layer_heights: DataArray,
    layer_roles: List,
    surface_temperature: DataArray,
    mean_annual_temperature: DataArray,
    lower_bound: float = -10,
    upper_bound: float = 50,
) -> DataArray:
    """Interpolate soil temperature using logarithmic function.

    Args:
        layer_heights: vertical layer heights, [m]
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        surface_temperature: surface temperature, [C]
        mean_annual_temperature: mean annual temperature, [C]
        lower_bound: minimum allowed values
        upper_bound: maximum allowed value

    Returns:
        soil temperature profile, [C]
    """

    # select surface layer (atmosphere)
    surface_layer = layer_heights[layer_heights.coords["layer_roles"] == "surface"]

    # create array of interpolation heights including surface layer and soil layers
    interpolation_heights = xr.concat(
        [
            surface_layer,
            layer_heights[layer_heights.coords["layer_roles"] == "soil"] * -1
            + surface_layer.values,
        ],
        dim="layers",
    )

    # Calculate per cell slope and intercept for logarithmic soil temperature profile
    slope = (surface_temperature - mean_annual_temperature) / (
        np.log(interpolation_heights.isel(layers=0))
        - np.log(interpolation_heights.isel(layers=-1))
    )
    intercept = surface_temperature - slope * np.log(
        interpolation_heights.isel(layers=0)
    )

    # Calculate the values within cells by layer
    layer_values = np.log(interpolation_heights) * slope + intercept

    # set upper and lower bounds
    layer_values_low = np.where(layer_values < lower_bound, lower_bound, layer_values)
    layer_values_bound = DataArray(
        np.where(layer_values_low > upper_bound, upper_bound, layer_values_low),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(interpolation_heights)),
            "layer_roles": ("layers", layer_roles[0 : len(interpolation_heights)]),
            "cell_id": mean_annual_temperature.cell_id,
        },
    )

    return xr.concat(
        [
            DataArray(
                np.full(
                    (
                        len(layer_roles) - len(interpolation_heights),
                        len(mean_annual_temperature.coords["cell_id"]),
                    ),
                    np.nan,
                ),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(len(interpolation_heights), len(layer_roles)),
                    "layer_roles": (
                        "layers",
                        layer_roles[len(interpolation_heights) : len(layer_roles)],
                    ),
                    "cell_id": mean_annual_temperature.coords["cell_id"],
                },
            ),
            layer_values_bound,
        ],
        dim="layers",
    ).rename("soil_temperature")


# TODO HYDROLOGY grid based in simple model?
# Stream flow could be estimated as P-ET


def calculate_soil_moisture(
    layer_roles: List,
    precipitation_surface: DataArray,
    current_soil_moisture: DataArray,
    soil_moisture_capacity: Union[DataArray, float] = MicroclimateParameters[
        "soil_moisture_capacity"
    ],
) -> Tuple[DataArray, DataArray]:
    """Calculate surface runoff and update soil mositure content.

    Soil moisture and surface runoff are calculated with a simple bucket model: if
    precipitation exceeds soil moisture capacity (see MicroclimateParameters), the
    excess water is added to runoff and soil moisture is set to soil moisture capacity
    value; if the soil is not saturated, precipitation is added to the current soil
    moisture level and runoff is set to zero.

    Args:
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        precipitation_surface: precipitation that reaches surface, [mm],
        current_soil_moisture: current soil moisture at upper layer, [mm],
        soil_moisture_capacity: soil moisture capacity (optional)

    Returns:
        current soil moisture, [mm], surface runoff, [mm]
    """

    available_capacity = soil_moisture_capacity - current_soil_moisture.mean(
        dim="layers"
    )

    surface_runoff_cells = precipitation_surface.where(
        precipitation_surface > available_capacity
    )
    surface_runoff = (
        DataArray(surface_runoff_cells.data - available_capacity.data)
        .fillna(0)
        .rename("surface_runoff")
        .rename({"dim_0": "cell_id"})
        .assign_coords({"cell_id": current_soil_moisture.cell_id})
    )

    total_water = current_soil_moisture.mean(dim="layers") + precipitation_surface
    soil_moisture_mean = total_water.where(total_water < soil_moisture_capacity).fillna(
        soil_moisture_capacity
    )
    soil_moisture = (  # TODO set bounds 0-100
        xr.concat(
            [
                DataArray(
                    np.full(
                        (
                            len(layer_roles) - layer_roles.count("soil"),
                            len(current_soil_moisture.cell_id),
                        ),
                        np.nan,
                    ),
                    dims=["layers", "cell_id"],
                ),
                DataArray(
                    np.full(
                        (
                            layer_roles.count("soil"),
                            len(current_soil_moisture.cell_id),
                        ),
                        soil_moisture_mean,
                    ),
                    dims=["layers", "cell_id"],
                ),
            ],
            dim="layers",
        )
        .rename("soil_moisture")
        .assign_coords(
            {
                "layers": np.arange(0, len(layer_roles)),
                "layer_roles": ("layers", layer_roles),
                "cell_id": current_soil_moisture.coords["cell_id"],
            },
        )
    )
    return soil_moisture, surface_runoff
