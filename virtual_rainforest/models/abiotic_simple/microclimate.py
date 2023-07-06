r"""The ``models.abiotic_simple.microclimate`` module uses linear regressions from
:cite:t:`hardwick_relationship_2015` and :cite:t:`jucker_canopy_2018` to predict
atmospheric temperature and relative humidity at ground level (2m) given the above
canopy conditions and leaf area index of intervening canopy. A within canopy profile is
then interpolated using a logarithmic curve between the above canopy observation and
ground level prediction.
Soil temperature is interpolated between the surface layer and the soil temperature at
1 m depth which equals the mean annual temperature.
The module also provides a constant vertical profile of atmospheric pressure and
:math:`\ce{CO2}`.
"""  # noqa: D205, D415

from typing import Dict, List

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
    "soil_temperature_min": -10,
    "soil_temperature_max": 50,
}
"""Upper and lower bounds for abiotic variables. When a values falls outside these
bounds, it is set to the bound value. Note that this approach does not conserve energy
and matter in the system. This will be implemented at a later stage.
"""
# TODO move bounds to core.bound_checking once that is implemented and introduce method
# to conserve energy and matter


def run_microclimate(
    data: Data,
    layer_roles: List[str],
    time_index: int,  # could be datetime?
    MicroclimateGradients: Dict[str, float] = MicroclimateGradients,
    Bounds: Dict[str, float] = Bounds,
) -> Dict[str, DataArray]:
    r"""Calculate simple microclimate.

    This function uses empirical relationships between leaf area index (LAI) and
    atmospheric temperature and relative humidity to derive logarithmic
    profiles of atmospheric temperature and humidity from external climate data such as
    regional climate models or satellite observations. For below canopy values (1.5 m),
    the implementation is based on :cite:t:`hardwick_relationship_2015` as

    :math:`y = m * LAI + c`

    where :math:`y` is the variable of interest, math:`m` is the gradient
    (:data:`~virtual_rainforest.models.abiotic_simple.microclimate.MicroclimateGradients`)
    and :math:`c` is the intersect which we set to the
    external data values. We assume that the gradient remains constant.

    The other atmospheric layers are calculated by logaritmic regression and
    interpolation between the input at the top of the canopy and the 1.5 m values.
    Soil temperature is interpolated between the surface layer and the temperature at
    1 m depth which equals the mean annual temperature.
    The function also provides constant atmospheric pressure and :math:`\ce{CO2}` for
    all atmospheric levels.

    The `layer_roles` list is composed of the following layers (index 0 above canopy):

    * above canopy (canopy height + reference measurement height, typically 2m)
    * canopy layers (maximum of ten layers, minimum one layers)
    * subcanopy (1.5 m)
    * surface layer
    * soil layers (currently one near surface layer and one layer at 1 m below ground)

    The function expects a data object with the following variables:

    * air_temperature_ref [C]
    * relative_humidity_ref []
    * vapour_pressure_deficit_ref [kPa]
    * atmospheric_pressure_ref [Pa]
    * atmospheric_co2_ref [ppm]
    * leaf_area_index [m m-1]
    * layer_heights [m]

    Args:
        data: Data object
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        time_index: time index, integer
        MicroclimateGradients: gradients for linear regression
            :cite:p:`hardwick_relationship_2015`
        Bounds: upper and lower allowed values for vertical profiles, used to constrain
            log interpolation. Note that currently no conservation of water and energy!

    Returns:
        Dict of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa], and
        atmospheric :math:`\ce{CO2}` [ppm]
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
            reference_data=data[var + "_ref"].isel(time_index=time_index),
            leaf_area_index_sum=leaf_area_index_sum,
            layer_roles=layer_roles,
            layer_heights=data["layer_heights"],
            upper_bound=Bounds[var + "_max"],
            lower_bound=Bounds[var + "_min"],
            gradient=MicroclimateGradients[var + "_gradient"],
        ).rename(var)

    # Mean atmospheric pressure profile, [kPa]
    output["atmospheric_pressure"] = (
        (data["atmospheric_pressure_ref"] / 1000)
        .isel(time_index=time_index)
        .where(output["air_temperature"].coords["layer_roles"] != "soil")
        .rename("atmospheric_pressure")
        .T
    )

    # Mean atmospheric C02 profile, [ppm]
    output["atmospheric_co2"] = (
        data["atmospheric_co2_ref"]
        .isel(time_index=0)
        .where(output["air_temperature"].coords["layer_roles"] != "soil")
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
    """LAI regression and logarithmic interpolation of variables above ground.

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
    positive_layer_heights = DataArray(
        np.where(layer_heights > 0, layer_heights, np.nan),
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
    )

    layer_values = np.where(
        np.logical_not(np.isnan(positive_layer_heights)),
        (np.log(positive_layer_heights) * slope + intercept),
        np.nan,
    )

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
