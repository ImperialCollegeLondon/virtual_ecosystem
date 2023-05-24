r"""The ``models.abiotic_simple.simple_regression`` module uses linear regressions from
:cite:t:`hardwick_relationship_2015` and :cite:t:`jucker_canopy_2018` to predict
atmospheric temperature and relative humidity at ground level (2m) given the above
canopy conditions and leaf area index of intervening canopy. A within canopy profile is
then interpolated using a logarithmic curve between the above canopy observation and
ground level prediction.
Soil temperature is interpolated between the surface layer and the air temperature at
1 m depth which equals the mean annual temperature.
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
    "soil_moisture_capacity": 90,
    "water_interception_factor": 0.1,
    "saturation_vapour_pressure_factor1": 0.61078,
    "saturation_vapour_pressure_factor2": 7.5,
    "saturation_vapour_pressure_factor3": 237.3,
}
"""Parameters for simple abiotic regression model."""

Bounds: Dict[str, float] = {
    "air_temperature_min": -20,
    "air_temperature_max": 80,
    "relative_humidity_min": 0,
    "relative_humidity_max": 100,
    "vapour_pressure_deficit_min": 0,
    "vapour_pressure_deficit_max": 10,
    "soil_moisture_min": 0,
    "soil_moisture_max": 100,
    "soil_temperature_min": -10,
    "soil_temperature_max": 50,
}
"""Upper and lower bounds for abiotic variables. When a values falls outside these
bounds, it is set to the bound value. Note that this approach does not conserve energy
and matter in the system. This will be implemented at a later stage.
"""
# TODO move bounds to core.bound_checking once that is implemented and introduce method
# to conserve energy and matter


def setup_simple_regression(
    layer_roles: List[str],
    data: Data,
    initial_soil_moisture: float = 50,
) -> Dict[str, DataArray]:
    r"""Set up abiotic environment variables.

    This function initialises all abiotic variables as DataArrays filled with NaN,
    except for soil moisture which has a homogenous value across all soil layers.

    Args:
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        data: Data object
        initial_soil_moisture: initial soil moisture

    Returns:
        Dict of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa],
        atmospheric :math:`\ce{CO2}` [ppm], soil moisture [-], and surface runoff [mm]
    """

    # TODO: make sure variables are representing correct time interval, see #222
    output = {}

    # Initialise DataArrays filled with NaN
    output["air_temperature"] = DataArray(
        np.full((len(layer_roles), len(data.grid.cell_id)), np.nan),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
        name="air_temperature",
    )

    # copy and assign new variable names
    for name in (
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
        "surface_runoff",
    ):
        output[name] = output["air_temperature"].copy().rename(name)

    # The initial soil moisture constant in all soil layers, all other layers set to NaN
    soil_moisture = output["air_temperature"].copy().rename("soil_moisture")
    output["soil_moisture"] = soil_moisture.where(
        soil_moisture.coords["layer_roles"] != "soil",
        initial_soil_moisture,
    )

    # TODO until the plant model is ready, these variables are initialised here
    layer_heights = np.repeat(
        a=[32.0, 30.0, 20.0, 10.0, np.nan, 1.5, 0.1, -0.1, -1.0],
        repeats=[1, 1, 1, 1, 7, 1, 1, 1, 1],
    )
    output["layer_heights"] = DataArray(
        np.broadcast_to(layer_heights, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
        name="layer_heights",
    )

    leaf_area_index = np.repeat(a=[np.nan, 1.0, np.nan], repeats=[1, 3, 11])
    output["leaf_area_index"] = DataArray(
        np.broadcast_to(leaf_area_index, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
        name="leaf_area_index",
    )

    # calculate vapour pressure deficit time series at reference height first
    output["vapour_pressure_deficit_ref"] = calculate_vapour_pressure_deficit(
        temperature=data["air_temperature_ref"],
        relative_humidity=data["relative_humidity_ref"],
    ).rename("vapour_pressure_deficit_ref")

    return output


def run_simple_regression(
    data: Data,
    layer_roles: List[str],
    time_index: int,  # could be datetime?
    MicroclimateGradients: Dict[str, float] = MicroclimateGradients,
    Bounds: Dict[str, float] = Bounds,
    water_interception_factor: Union[DataArray, float] = MicroclimateParameters[
        "water_interception_factor"
    ],
    soil_moisture_capacity: Union[DataArray, float] = MicroclimateParameters[
        "soil_moisture_capacity"
    ],
) -> Dict[str, DataArray]:
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
    * vapour_pressure_deficit_ref
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
        Bounds: upper and lower allowed values for vertical profiles, used to constrain
            log interpolation. Note that currently no conservation of water and energy!
        water_interception_factor: Factor that determines how much rainfall is
            intercepted by stem and canopy
        soil_moisture_capacity: soil moisture capacity for water

    Returns:
        Dict of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa],
        atmospheric :math:`\ce{CO2}` [ppm], soil moisture [-], and surface runoff [mm]
    """

    # TODO correct gap between 1.5 m and 2m reference height for LAI = 0
    # TODO make sure variables are representing correct time interval, e.g. mm per day
    output = {}

    # sum leaf area index over all canopy layers
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # interpolate atmospheric profiles
    for var in ["air_temperature", "relative_humidity", "vapour_pressure_deficit"]:
        output[var] = log_interpolation(
            data=data,
            reference_data=data[var + "_ref"].isel(time=time_index),
            leaf_area_index_sum=leaf_area_index_sum,
            layer_roles=layer_roles,
            layer_heights=data["layer_heights"],
            upper_bound=Bounds[var + "_max"],
            lower_bound=Bounds[var + "_min"],
            gradient=MicroclimateGradients[var + "_gradient"],
        ).rename(var)

    # Mean atmospheric pressure profile, [kPa]
    output["atmospheric_pressure"] = (
        data["atmospheric_pressure_ref"]
        .isel(time=time_index)
        .where(data["atmospheric_pressure"].coords["layer_roles"] != "soil")
        .rename("atmospheric_pressure")
        .T
    )

    # Mean atmospheric C02 profile, [ppm]
    output["atmospheric_co2"] = (
        data["atmospheric_co2_ref"]
        .isel(time=0)
        .where(data["atmospheric_co2"].coords["layer_roles"] != "soil")
        .rename("atmospheric_co2")
        .T
    )

    # Calculate soil temperatures
    soil_temperature_only = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=output["air_temperature"].isel(
            layers=len(layer_roles) - layer_roles.count("soil") - 1
        ),
        mean_annual_temperature=data["mean_annual_temperature"],
        upper_bound=Bounds["soil_temperature_max"],
        lower_bound=Bounds["soil_temperature_min"],
    )

    # add above-ground vertical layers back
    output["soil_temperature"] = xr.concat(
        [
            data["soil_temperature"].isel(
                layers=np.arange(0, len(layer_roles) - layer_roles.count("soil"))
            ),
            soil_temperature_only,
        ],
        dim="layers",
    )

    # Precipitation at the surface is reduced as a function of leaf area index
    precipitation_surface = data["precipitation"].isel(time=time_index) * (
        1 - water_interception_factor * data["leaf_area_index"].sum(dim="layers")
    )

    # Mean soil moisture profile, [] and Runoff, [mm]
    soil_moisture_only, surface_run_off = calculate_soil_moisture(
        layer_roles=layer_roles,
        precipitation_surface=precipitation_surface,
        current_soil_moisture=data["soil_moisture"],
        soil_moisture_capacity=soil_moisture_capacity,
    )
    output["soil_moisture"] = xr.concat(
        [
            data["soil_moisture"].isel(
                layers=np.arange(0, len(layer_roles) - layer_roles.count("soil"))
            ),
            soil_moisture_only,
        ],
        dim="layers",
    )
    output["surface_run_off"] = surface_run_off

    return output


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
        lower_bound: minimum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        upper_bound: maximum allowed value, used to constrain log interpolation.
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
    surface_temperature: DataArray,
    mean_annual_temperature: DataArray,
    upper_bound: float = Bounds["soil_temperature_max"],
    lower_bound: float = Bounds["soil_temperature_min"],
) -> DataArray:
    """Interpolate soil temperature using logarithmic function.

    Args:
        layer_heights: vertical layer heights, [m]
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        surface_temperature: surface temperature, [C]
        mean_annual_temperature: mean annual temperature, [C]
        upper_bound: maximum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        lower_bound: minimum allowed value, used to constrain log interpolation.

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

    # set upper and lower bounds and return soil and surface layers, further layers are
    # added in the 'run' function
    return DataArray(
        np.clip(layer_values, lower_bound, upper_bound),
        coords=interpolation_heights.coords,
    ).drop_isel(layers=0)


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
        current soil moisture for one layer, [mm], surface runoff, [mm]
    """
    # calculate how much water can be added to soil before capacity is reached
    available_capacity = soil_moisture_capacity - current_soil_moisture.mean(
        dim="layers"
    )

    # calculate where precipitation exceeds available capacity
    surface_runoff_cells = precipitation_surface.where(
        precipitation_surface > available_capacity
    )
    # calculate runoff
    surface_runoff = (
        DataArray(surface_runoff_cells.data - available_capacity.data)
        .fillna(0)
        .rename("surface_runoff")
        .rename({"dim_0": "cell_id"})
        .assign_coords({"cell_id": current_soil_moisture.cell_id})
    )

    # calculate total water in each grid cell
    total_water = current_soil_moisture.mean(dim="layers") + precipitation_surface

    # calculate soil moisture for one layer and copy to all layers
    soil_moisture = (
        DataArray(np.clip(total_water, 0, soil_moisture_capacity))
        .expand_dims(dim={"layers": np.arange(layer_roles.count("soil"))}, axis=0)
        .assign_coords(
            {
                "cell_id": current_soil_moisture.cell_id,
                "layers": [
                    len(layer_roles) - layer_roles.count("soil"),
                    len(layer_roles) - 1,
                ],
                "layer_roles": ("layers", layer_roles.count("soil") * ["soil"]),
            }
        )
    )

    return soil_moisture, surface_runoff
