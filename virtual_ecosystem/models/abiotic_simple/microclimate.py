r"""The ``models.abiotic_simple.microclimate`` module uses linear regressions from
:cite:t:`hardwick_relationship_2015` and :cite:t:`jucker_canopy_2018` to predict
atmospheric temperature, relative humidity, and vapour pressure deficit at ground level
(1.5 m) given the above canopy conditions and leaf area index of intervening canopy. A
within canopy profile is then interpolated using a logarithmic curve between the above
canopy observation and ground level prediction.
Soil temperature is interpolated between the surface layer and the soil temperature at
1 m depth which equals the mean annual temperature.
The module also provides a constant vertical profile of atmospheric pressure and
:math:`\ce{CO2}`.

TODO change tenperatures to Kelvin
"""  # noqa: D205

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)


def run_microclimate(
    data: Data,
    layer_structure: LayerStructure,
    time_index: int,  # could be datetime?
    constants: AbioticSimpleConsts,
    bounds: AbioticSimpleBounds,
) -> dict[str, DataArray]:
    r"""Calculate simple microclimate.

    This function uses empirical relationships between leaf area index (LAI) and
    atmospheric temperature, relative humidity, and vapour pressure deficit to derive
    logarithmic profiles of these variables from external climate data such as
    regional climate models or satellite observations. Note that these sources provide
    data at different heights and with different underlying assumptions which lead to
    different biases in the model output. For below canopy values (1.5 m),
    the implementation is based on :cite:t:`hardwick_relationship_2015` as

    :math:`y = m * LAI + c`

    where :math:`y` is the variable of interest, :math:`m` is the gradient
    (:data:`~virtual_ecosystem.models.abiotic_simple.constants.AbioticSimpleConsts`)
    and :math:`c` is the intersect which we set to the external data values. We assume
    that the gradient remains constant.

    The other atmospheric layers are calculated by logarithmic regression and
    interpolation between the input at the top of the canopy and the 1.5 m values.
    Soil temperature is interpolated between the surface layer and the temperature at
    1 m depth which equals the mean annual temperature.
    The function also provides constant atmospheric pressure and :math:`\ce{CO2}` for
    all atmospheric levels.

    The `layer_roles` list is composed of the following layers (index 0 above canopy):

    * above canopy (canopy height)
    * canopy layers (maximum of ten layers, minimum one layers)
    * subcanopy (1.5 m)
    * surface layer
    * soil layers (currently one near surface layer and one layer at 1 m below ground)

    The function expects a data object with the following variables:

    * air_temperature_ref [C]
    * relative_humidity_ref []
    * vapour_pressure_deficit_ref [kPa]
    * atmospheric_pressure_ref [kPa]
    * atmospheric_co2_ref [ppm]
    * leaf_area_index [m m-1]
    * layer_heights [m]

    Args:
        data: Data object
        layer_structure: The LayerStructure instance for the simulation.
        time_index: time index, integer
        constants: Set of constants for the abiotic simple model
        bounds: upper and lower allowed values for vertical profiles, used to constrain
            log interpolation. Note that currently no conservation of water and energy!

    Returns:
        Dict of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa], and
        atmospheric :math:`\ce{CO2}` [ppm]
    """

    # TODO make sure variables are representing correct time interval, e.g. mm per day
    output = {}

    # sum leaf area index over all canopy layers
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # interpolate atmospheric profiles
    for var in ["air_temperature", "relative_humidity", "vapour_pressure_deficit"]:
        lower, upper, gradient = getattr(bounds, var)

        output[var] = log_interpolation(
            data=data,
            reference_data=data[var + "_ref"].isel(time_index=time_index),
            leaf_area_index_sum=leaf_area_index_sum,
            layer_structure=layer_structure,
            layer_heights=data["layer_heights"],
            upper_bound=upper,
            lower_bound=lower,
            gradient=gradient,
        ).rename(var)

    # Mean atmospheric pressure profile, [kPa]
    # TODO: this should only be filled for filled/true above ground layers
    output["atmospheric_pressure"] = layer_structure.from_template()
    output["atmospheric_pressure"][layer_structure.index_atmosphere] = data[
        "atmospheric_pressure_ref"
    ].isel(time_index=time_index)

    # Mean atmospheric C02 profile, [ppm]
    # TODO: this should only be filled for filled/true above ground layers
    output["atmospheric_co2"] = layer_structure.from_template()
    output["atmospheric_co2"][layer_structure.index_atmosphere] = data[
        "atmospheric_co2_ref"
    ].isel(time_index=time_index)

    # Calculate soil temperatures
    lower, upper = getattr(bounds, "soil_temperature")
    output["soil_temperature"] = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=output["air_temperature"].isel(
            layers=layer_structure.index_surface
        ),
        mean_annual_temperature=data["mean_annual_temperature"],
        layer_structure=layer_structure,
        upper_bound=upper,
        lower_bound=lower,
    )

    return output


def log_interpolation(
    data: Data,
    reference_data: DataArray,
    leaf_area_index_sum: DataArray,
    layer_structure: LayerStructure,
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
        layer_structure: The LayerStructure instance for the simulation.
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
    positive_layer_heights = np.where(layer_heights > 0, layer_heights, np.nan)
    layer_values = (
        np.log(positive_layer_heights) * slope.to_numpy() + intercept.to_numpy()
    )

    # set upper and lower bounds
    return_array = layer_structure.from_template()
    return_array[:] = np.clip(layer_values, lower_bound, upper_bound)

    return return_array


def calculate_saturation_vapour_pressure(
    temperature: DataArray,
    saturation_vapour_pressure_factors: list[float],
) -> DataArray:
    r"""Calculate saturation vapour pressure.

    Saturation vapour pressure :math:`e_{s} (T)` is here calculated as

    :math:`e_{s}(T) = 0.61078 exp(\frac{7.5 T}{T + 237.3})`

    where :math:`T` is temperature in degree C .

    Args:
        temperature: Air temperature, [C]
        saturation_vapour_pressure_factors: Factors in saturation vapour pressure
            calculation

    Returns:
        saturation vapour pressure, [kPa]
    """
    factor1, factor2, factor3 = saturation_vapour_pressure_factors
    return DataArray(
        factor1 * np.exp((factor2 * temperature) / (temperature + factor3))
    ).rename("saturation_vapour_pressure")


def calculate_vapour_pressure_deficit(
    temperature: DataArray,
    relative_humidity: DataArray,
    saturation_vapour_pressure_factors: list[float],
) -> dict[str, DataArray]:
    """Calculate vapour pressure and vapour pressure deficit.

    Vapor pressure deficit is defined as the difference between saturated vapour
    pressure and actual vapour pressure.

    Args:
        temperature: temperature, [C]
        relative_humidity: relative humidity, []
        saturation_vapour_pressure_factors: Factors in saturation vapour pressure
            calculation

    Return:
        vapour pressure, [kPa], vapour pressure deficit, [kPa]
    """

    output = {}
    saturation_vapour_pressure = calculate_saturation_vapour_pressure(
        temperature,
        saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
    )
    actual_vapour_pressure = saturation_vapour_pressure * (relative_humidity / 100)
    output["vapour_pressure"] = actual_vapour_pressure
    output["vapour_pressure_deficit"] = (
        saturation_vapour_pressure - actual_vapour_pressure
    )
    return output


def interpolate_soil_temperature(
    layer_heights: DataArray,
    surface_temperature: DataArray,
    mean_annual_temperature: DataArray,
    layer_structure: LayerStructure,
    upper_bound: float,
    lower_bound: float,
) -> DataArray:
    """Interpolate soil temperature using logarithmic function.

    Args:
        layer_heights: vertical layer heights, [m]
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        surface_temperature: surface temperature, [C]
        mean_annual_temperature: mean annual temperature, [C]
        layer_structure: The LayerStructure instance for the simulation.
        upper_bound: maximum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        lower_bound: minimum allowed value, used to constrain log interpolation.

    Returns:
        soil temperature profile, [C]
    """

    # select surface layer (atmosphere) and generate interpolation heights
    surface_layer = layer_heights[layer_structure.index_surface].to_numpy()
    soil_depths = layer_heights[layer_structure.index_all_soil].to_numpy()
    interpolation_heights = np.concatenate(
        [surface_layer, -1 * soil_depths + surface_layer]
    )

    # Calculate per cell slope and intercept for logarithmic soil temperature profile
    slope = (surface_temperature.to_numpy() - mean_annual_temperature.to_numpy()) / (
        np.log(interpolation_heights[0]) - np.log(interpolation_heights[-1])
    )
    intercept = surface_temperature.to_numpy() - slope * np.log(
        interpolation_heights[0]
    )

    # Calculate the values within cells by layer and clip by the bounds
    layer_values = np.clip(
        np.log(interpolation_heights) * slope + intercept, lower_bound, upper_bound
    )

    # return
    return_xarray = layer_structure.from_template()
    return_xarray[layer_structure.index_all_soil] = layer_values[1:]

    return return_xarray
