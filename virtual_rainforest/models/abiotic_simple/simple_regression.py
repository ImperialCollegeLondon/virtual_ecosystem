r"""The ``models.abiotic_simple.simple_regression`` module uses linear regression
and logarithmic interpolation to calculate atmospheric temperature and humidity profiles
as a function of leaf area index and height. The relationships are derived
from :cite:t:`hardwick_relationship_2015`.

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
from scipy.optimize import curve_fit
from xarray import DataArray

from virtual_rainforest.core.data import Data

MicroclimateGradients: Dict[str, float] = {
    "air_temperature_gradient": -1.27,
    "relative_humidity_gradient": 5.4,
    "vapor_pressure_deficit_gradient": -252.24,
}

MicroclimateParameters: Dict[str, float] = {
    "soil_moisture_capacity": 150,
    "water_interception_factor": 0.1,
    "saturation_vapor_pressure_factor1": 0.61078,
    "saturation_vapor_pressure_factor2": 7.5,
    "saturation_vapor_pressure_factor3": 237.3,
}


def setup_simple_regression(
    layer_roles: List[str],
    data: Data,
    initial_soil_moisture: Union[DataArray, float] = 50,
) -> List[DataArray]:
    r"""Set up abiotic environment variables.

    This function initialises all abiotic variables as DataArrays filled with NaN,
    except for soil moisture which has a homogenous value across all soil layers.

    Args:
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
        data: Data object
        initial_soil_moisture: initial soil moisture

    Returns:
        list of DataArrays for air temperature, relative humidity, vapor pressure
        deficit, soil temperature, atmospheric pressure, atmospheric :math:`\ce{CO2}`,
        soil moisture, and surface runoff
    """

    output = []

    air_temperature = DataArray(
        np.full((len(layer_roles), len(data.grid.cell_id)), np.nan),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        },
        name="air_temperature",
    )
    """Mean air temperature profile, [C]"""
    output.append(air_temperature)

    relative_humidity = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("relative_humidity")
    """Mean relative humidity profile"""
    output.append(relative_humidity)

    vapor_pressure_deficit = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("vapor_pressure_deficit")
    """Mean vapor pressure deficit profile"""
    output.append(vapor_pressure_deficit)

    soil_temperature = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("soil_temperature")
    """Mean soil temperature profile, [C]"""
    output.append(soil_temperature)

    atmospheric_pressure = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("atmospheric_pressure")
    """Atmospheric pressure profile, [kPa]"""
    output.append(atmospheric_pressure)

    atmospheric_CO2 = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("atmospheric_co2")
    r"""Atmospheric :math:`\ce{CO2}` profile, [ppm]"""
    output.append(atmospheric_CO2)

    # initial soil moisture constant in all soil layers, all other layers set to NaN
    soil_moisture = (
        xr.concat(
            [
                DataArray(
                    np.full(
                        (
                            len(layer_roles) - layer_roles.count("soil"),
                            len(data.grid.cell_id),
                        ),
                        np.nan,
                    ),
                    dims=["layers", "cell_id"],
                ),
                DataArray(
                    np.full(
                        (
                            layer_roles.count("soil"),
                            len(data.grid.cell_id),
                        ),
                        initial_soil_moisture,
                    ),
                    dims=["layers", "cell_id"],
                ),
            ],
            dim="layers",
        )
        .rename("soil_moisture")
        .assign_coords(air_temperature.coords)
    )
    output.append(soil_moisture)

    surface_runoff = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("surface_runoff")
    """Surface runoff, [mm]"""
    output.append(surface_runoff)

    return [
        air_temperature,
        relative_humidity,
        vapor_pressure_deficit,
        soil_temperature,
        atmospheric_pressure,
        atmospheric_CO2,
        soil_moisture,
        surface_runoff,
    ]


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
    (see MicroclimateGradients) and :math:`c` is the intersect which we set to the
    external data values. We assume that the gradient remains constant.

    The other atmospheric layers are calculated by logaritmic regression and
    interpolation between the input at the top of the canopy and the 1.5 m values.
    Soil temperature is interpolated between the surface layer and the temperature at
    1 m depth which equals the mean annual temperature.
    The function also provides constant atmospheric pressure and :math:`\ce{CO2}` for
    all atmospheric levels.

    Soil moisture and surface runoff are calculated with a simple bucket model based
    on :cite:t:`davis_simple_2017`: if
    precipitation exceeds soil moisture capacity (see MicroclimateParameters), the
    excess water is added to runoff and soil moisture is set to soil moisture capacity
    value; if the soil is not saturated, precipitation is added to the current soil
    moisture level and runoff is set to zero.

    The `layer_roles` list is composed of the following layers (index 0 above canopy):

    * above canopy
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
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
        time_index: time index, integer
        MicroclimateGradients: gradients for linear regression
        water_interception_factor: Factor that determines how much rainfall is
            intercepted by stem and canopy
        soil_moisture_capacity: soil moisture capacity for water

    Returns:
        list of air temperature, relative humidity, vapor pressure deficit, soil
        temperature, atmospheric pressure, atmospheric :math:`\ce{CO2}`, soil moisture,
        and surface runoff
    """

    output = []

    # air temperature
    air_temperature_lai = lai_regression(
        reference_data=data["air_temperature_ref"].isel(time=time_index),
        leaf_area_index=data["leaf_area_index"],
        gradient=MicroclimateGradients["air_temperature_gradient"],
    )
    air_temperature_log = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time=time_index),
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        value_from_lai_regression=air_temperature_lai,
    )
    air_temperature = air_temperature_log.rename("air_temperature")
    output.append(air_temperature)

    # relative humidity
    relative_humidity_lai = lai_regression(
        reference_data=data["relative_humidity_ref"].isel(time=time_index),
        leaf_area_index=data["leaf_area_index"],
        gradient=MicroclimateGradients["relative_humidity_gradient"],
    )
    relative_humidity_log = log_interpolation(
        data=data,
        reference_data=data["relative_humidity_ref"].isel(time=time_index),
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        value_from_lai_regression=relative_humidity_lai,
    )
    relative_humidity = relative_humidity_log.rename("relative_humidity")
    output.append(relative_humidity)

    # vapor pressure deficit
    # calculate vapor pressure deficit at reference height first
    vapor_pressure_deficit_ref = calculate_vapor_pressure_deficit(
        temperature=data["air_temperature_ref"].isel(time=time_index),
        relative_humidity=data["relative_humidity_ref"].isel(time=time_index),
    )

    vapor_pressure_deficit_lai = lai_regression(
        reference_data=vapor_pressure_deficit_ref,
        leaf_area_index=data["leaf_area_index"],
        gradient=MicroclimateGradients["vapor_pressure_deficit_gradient"],
    )
    vapor_pressure_deficit_log = log_interpolation(
        data=data,
        reference_data=vapor_pressure_deficit_ref,
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        value_from_lai_regression=vapor_pressure_deficit_lai,
    )
    vapor_pressure_deficit = vapor_pressure_deficit_log.rename("vapor_pressure_deficit")
    output.append(vapor_pressure_deficit)

    # soil temperature
    soil_temperature = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        layer_roles=layer_roles,
        surface_temperature=air_temperature.isel(
            layers=len(layer_roles) - layer_roles.count("soil") - 1
        ),
        mean_annual_temperature=data["mean_annual_temperature"],
    )
    output.append(soil_temperature)

    # atmospheric pressure
    atmospheric_pressure_1 = xr.concat(
        [
            data["atmospheric_pressure_ref"]
            .isel(time=time_index)
            .expand_dims(
                dim={"layers": np.arange(len(layer_roles) - layer_roles.count("soil"))},
                axis=0,
            ),  # vertical projection
            DataArray(
                np.full((layer_roles.count("soil"), len(data.grid.cell_id)), np.nan),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(
                        len(layer_roles) - layer_roles.count("soil"), len(layer_roles)
                    ),
                },
            ),
        ],
        dim="layers",
    )
    atmospheric_pressure = atmospheric_pressure_1.assign_coords(
        {
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        },
    )
    output.append(atmospheric_pressure)

    # atmospheric C02
    atmospheric_co2_1 = xr.concat(
        [
            data["atmospheric_co2_ref"]
            .isel(time=time_index)
            .expand_dims(
                dim={"layers": np.arange(len(layer_roles) - layer_roles.count("soil"))},
                axis=0,
            ),  # vertical projection
            DataArray(
                np.full((layer_roles.count("soil"), len(data.grid.cell_id)), np.nan),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(
                        len(layer_roles) - layer_roles.count("soil"), len(layer_roles)
                    ),
                },
            ),
        ],
        dim="layers",
    )
    atmospheric_co2 = atmospheric_co2_1.assign_coords(
        {
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        },
    )
    output.append(atmospheric_co2)

    # precipitation at the surface is reduced as a function of leaf area index
    precipitation_surface = data["precipitation"].isel(time=time_index) * (
        1 - water_interception_factor * data["leaf_area_index"].sum(dim="layers")
    )

    # soil moisture
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
def lai_regression(
    reference_data: DataArray,
    leaf_area_index: DataArray,
    gradient: float,
) -> DataArray:
    """Calculate microclimatic variable at 1.5 m as function of leaf area index.

    Args:
        reference_data: input variable at reference height
        leaf_area_index: leaf area index, [m m-1]
        gradient: gradient of regression from Harwick

    Returns:
        microclimatic variable at 1.5 m
    """

    return DataArray(
        leaf_area_index.sum(dim="layers") * gradient + reference_data, dims="cell_id"
    )


def logarithmic(x: DataArray, gradient: float, intercept: float) -> DataArray:
    """Logarithmic function.

    Args:
        x: x values
        gradient: gradient
        intercept: intercept

    Returns:
        y values
    """
    return DataArray(gradient * np.log(x) + intercept)


def log_interpolation(
    data: Data,
    reference_data: DataArray,
    layer_roles: List[str],
    layer_heights: DataArray,
    value_from_lai_regression: DataArray,
) -> DataArray:
    """Logarithmic interpolation of variables for vertical profile.

    Args:
        data: Data object
        reference_data: input variable at reference height
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
        layer_heights: vertical layer heights, [m]
        value_from_lai_regression: variable value from linear regression with LAI

    Returns:
        vertical profile of provided variable
    """

    # Fit logarithmic function to interpolate between temperature top and 1.5m
    x_values = np.array(
        [
            layer_heights.isel(layers=0),
            np.repeat(1.5, len(data.grid.cell_id)),
        ]
    ).flatten()
    y_values = np.array([reference_data, value_from_lai_regression]).flatten()

    popt, pcov = curve_fit(logarithmic, x_values, y_values)
    a, b = popt  # the function coefficients

    output = a * np.log(layer_heights) + b
    return DataArray(
        np.where(output < 0, 0, output),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        },
    )


def calculate_saturation_vapor_pressure(
    temperature: DataArray,
    factor1: float = MicroclimateParameters["saturation_vapor_pressure_factor1"],
    factor2: float = MicroclimateParameters["saturation_vapor_pressure_factor2"],
    factor3: float = MicroclimateParameters["saturation_vapor_pressure_factor3"],
) -> DataArray:
    r"""Calculate saturation vapor pressure.

    Saturation vapor pressure :math:`e_{s} (T)` is here calculated as
    :math:`e_{s}(T) = 0.61078 exp(\frac{7.5 T}{T + 237.3})`
    where :math:`T` is temperature in degree C .

    Args:
        temperature: air temperature, [C]
        factor1: factor 1 in saturation vapor pressure calculation
        factor2: factor 2 in saturation vapor pressure calculation
        factor3: factor 3 in saturation vapor pressure calculation

    Returns:
        saturation vapor pressure, kPa
    """
    return DataArray(
        (factor1 * np.exp((factor2 * (temperature)) / (temperature + factor3))),
        dims=temperature.dims,
        name="saturation_vapor_pressure",
    )


def calculate_vapor_pressure_deficit(
    temperature: DataArray,
    relative_humidity: DataArray,
) -> DataArray:
    """Calculate vapor pressure deficit.

    Vapor pressure deficit is defined as the difference between saturated vapor pressure
    and actual vapor pressure.

    Args:
        temperature: temperature, [C]
        relative_humidity: relative humidity, []

    Return:
        vapor pressure deficit, [kPa]
    """
    saturation_vapor_pressure = calculate_saturation_vapor_pressure(temperature)
    actual_vapor_pressure = saturation_vapor_pressure * (relative_humidity / 100)

    return (saturation_vapor_pressure - actual_vapor_pressure).rename(
        "vapor_pressure_deficit_ref"
    )


def interpolate_soil_temperature(
    layer_heights: DataArray,
    layer_roles: List,
    surface_temperature: DataArray,
    mean_annual_temperature: DataArray,
) -> DataArray:
    """Interpolate soil temperature.

    Args:
        layer_heights: vertical layer heights, [m]
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
        surface_temperature: surface temperature, [C]
        mean_annual_temperature: mean annual temperature, [C]

    Returns:
        soil temperature profile, [C]
    """

    # select surface layer (atmosphere)
    surface_layer = layer_heights[layer_heights.coords["layer_roles"] == "surface"]

    # calculate relative depth of lowest layer with respect to surface layer
    lowest_soil_depth_relative = (
        layer_heights.isel(layers=-1).expand_dims("layers") * -1 + surface_layer.values
    )

    # create array of interpolation heights including surface layer and soil layers
    interpolation_heights = xr.concat(
        [
            surface_layer,
            layer_heights[layer_heights.coords["layer_roles"] == "soil"] * -1
            + surface_layer.values,
        ],
        dim="layers",
    )

    # x values include surface and lowest soil layer
    x_values = np.array(
        xr.concat(
            [
                layer_heights[
                    layer_heights.coords["layer_roles"] == "surface"
                ],  # surface layer
                lowest_soil_depth_relative,
            ],
            dim="layers",
        )
    ).flatten()

    y_values = np.array([surface_temperature, mean_annual_temperature]).flatten()

    popt, pcov = curve_fit(logarithmic, x_values, y_values)
    a, b = popt  # the function coefficients

    interpolation = DataArray(
        a * np.log(interpolation_heights) + b,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(
                len(layer_roles) - layer_roles.count("soil") - 1, len(layer_roles)
            ),
            "layer_roles": (
                "layers",
                layer_roles[
                    len(layer_roles) - layer_roles.count("soil") - 1 : len(layer_roles)
                ],
            ),
            "cell_id": mean_annual_temperature.coords["cell_id"],
        },
    )

    soil_temperature = xr.concat(
        [
            DataArray(
                np.full(
                    (
                        len(layer_roles) - layer_roles.count("soil"),
                        len(mean_annual_temperature.coords["cell_id"]),
                    ),
                    np.nan,
                ),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(
                        0, len(layer_roles) - layer_roles.count("soil")
                    ),
                    "layer_roles": (
                        "layers",
                        layer_roles[0 : len(layer_roles) - layer_roles.count("soil")],
                    ),
                    "cell_id": mean_annual_temperature.coords["cell_id"],
                },
            ),
            interpolation[interpolation.coords["layer_roles"] == "soil"],
        ],
        dim="layers",  # select bottom two
    )
    return soil_temperature.rename("soil_temperature")


# TODO HYDROLOGY grid based not ready


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
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
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
        DataArray(surface_runoff_cells.data - available_capacity.data, dims="cell_id")
        .fillna(0)
        .rename("surface_runoff")
        .assign_coords(
            {
                "cell_id": current_soil_moisture.cell_id,
            },
        )
    )

    total_water = current_soil_moisture.mean(dim="layers") + precipitation_surface
    soil_moisture_mean = total_water.where(total_water < soil_moisture_capacity).fillna(
        soil_moisture_capacity
    )
    soil_moisture = (
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
        .assign_coords(current_soil_moisture.coords)
    )
    return (soil_moisture, surface_runoff)
