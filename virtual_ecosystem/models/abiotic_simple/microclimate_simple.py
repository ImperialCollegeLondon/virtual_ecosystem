r"""The ``models.abiotic_simple.microclimate_simple`` module uses linear regressions
from :cite:t:`hardwick_relationship_2015` and :cite:t:`jucker_canopy_2018` to predict
atmospheric temperature, relative humidity, and vapour pressure deficit at measurement
height (default 1.5 m) given the above canopy conditions and leaf area index of
intervening canopy. A
within canopy profile is then interpolated using an exponential curve between the above
canopy observation and ground level prediction. The same method is applied to derive a
vertical wind profile within the canopy, except that we use a logarithmic interpolation.
Soil temperature is interpolated between the surface layer and the soil temperature at
1 m depth which equals the mean annual temperature.
The module also provides a constant vertical profile of atmospheric pressure and
:math:`\ce{CO2}` as well as a profile of net radiation.

TODO change temperatures to Kelvin
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calculate_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic import abiotic_tools, energy_balance
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants
from virtual_ecosystem.models.abiotic_simple.model_config import (
    AbioticSimpleBounds,
    AbioticSimpleConstants,
)


def run_simple_microclimate(
    data: Data,
    layer_structure: LayerStructure,
    time_index: int,  # could be datetime?
    constants: AbioticSimpleConstants | AbioticConstants,
    core_constants: CoreConstants,
    pyrealm_core_constants: PyrealmCoreConst,
    bounds: AbioticSimpleBounds,
) -> dict[str, DataArray]:
    r"""Calculate simple microclimate.

    This function uses empirical relationships between leaf area index (LAI) and
    atmospheric temperature, relative humidity, vapour pressure deficit, and wind speed
    to derive vertical profiles of these variables from external climate data such as
    regional climate models or satellite observations. Note that these sources provide
    data at different heights and with different underlying assumptions which lead to
    different biases in the model output. For below canopy values (default is 1.5 m),
    the implementation is based on :cite:t:`hardwick_relationship_2015` as

    :math:`y = m * LAI + c`

    where :math:`y` is the variable of interest, :math:`m` is the gradient
    (:data:`~virtual_ecosystem.models.abiotic_simple.model_config.AbioticSimpleConstants`)
    and :math:`c` is the intersect which we set to the external data values. We assume
    that the gradient remains constant.

    The values for all atmospheric layers as defined by 'layer_heights' in the Virtual
    Ecosystem (including canopy layers and surface layer) are calculated by exponential
    (for atmospheric temperature, relative humidity, vapour pressure deficit) or
    logarithmic (for wind speed) regression and interpolation between the input at the
    top of the canopy and the measurement height values.

    Soil temperature is interpolated between the surface layer and the temperature at
    1 m depth which which approximately equals the mean annual temperature, i.e. can
    assumed to be constant over the year.

    The function also broadcasts the reference values for atmospheric pressure and
    :math:`\ce{CO2}` to all atmospheric levels as they are currently assumed to remain
    constant during one time step. Net radiation for canopy and topsoil layer is also
    returned.

    The `layer_roles` list is composed of the following layers (index 0 above canopy):

    * above canopy (canopy height + 2 m)
    * canopy layers
    * surface layer
    * soil layers

    The function expects a data object with the following variables:

    * air_temperature_ref [C]
    * relative_humidity_ref []
    * vapour_pressure_deficit_ref [kPa]
    * atmospheric_pressure_ref [kPa]
    * atmospheric_co2_ref [ppm]
    * wind_speed_ref [m s-1]
    * leaf_area_index [m m-1]
    * layer_heights [m]

    Args:
        data: Data object
        layer_structure: The LayerStructure instance for the simulation.
        time_index: Time index, integer
        constants: Set of constants for the abiotic simple model
        core_constants: Set of constants shared across all models
        pyrealm_core_constants: Set of constants from pyrealm package
        bounds: Upper and lower allowed values for vertical profiles, used to constrain
            log/exp interpolation. Note that currently no conservation of water and
            energy!

    Returns:
        Dict of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa],
        atmospheric :math:`\ce{CO2}` [ppm], wind speed [m s-1]
    """

    output = {}

    # Sum leaf area index over all canopy layers, [m m-1]
    # This step excludes the understorey vegetation, assuming that the relationship
    # between LAI and the variables is purely based on the vegetation above the
    # measurement height of 1m :cite:p:`hardwick_relationship_2015`.
    leaf_area_index_sum = np.nansum(
        data["leaf_area_index"][layer_structure.index_filled_canopy], axis=0
    )

    # Interpolate atmospheric profiles
    for var in [
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
    ]:
        lower, upper, gradient = getattr(bounds, var)

        output[var] = exp_interpolation(
            reference_data=data[var + "_ref"].isel(time_index=time_index).to_numpy(),
            leaf_area_index_sum=leaf_area_index_sum,
            layer_structure=layer_structure,
            layer_heights=data["layer_heights"].to_numpy(),
            measurement_height=constants.measurement_height,
            upper_bound=upper,
            lower_bound=lower,
            gradient=gradient,
        ).rename(var)

    # Interpolate wind profiles
    lower_wind, upper_wind, gradient_wind = getattr(bounds, "wind_speed")
    output["wind_speed"] = log_interpolation(
        reference_data=data["wind_speed_ref"].isel(time_index=time_index).to_numpy(),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=layer_structure,
        layer_heights=data["layer_heights"].to_numpy(),
        measurement_height=constants.measurement_height,
        upper_bound=upper_wind,
        lower_bound=lower_wind,
        gradient=gradient_wind,
    ).rename(var)

    # Vapour pressure, [kPa]
    vapour_pressure = abiotic_tools.calculate_actual_vapour_pressure(
        air_temperature=output["air_temperature"],
        relative_humidity=output["relative_humidity"],
        pyrealm_core_constants=pyrealm_core_constants,
    )
    output["vapour_pressure"] = layer_structure.from_template()
    output["vapour_pressure"] = vapour_pressure

    # Mean atmospheric pressure profile, [kPa]
    output["atmospheric_pressure"] = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=output["air_temperature"],
        variable_name=data["atmospheric_pressure_ref"],
        time_index=time_index,
    )

    # Mean atmospheric C02 profile, [ppm]
    output["atmospheric_co2"] = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=output["air_temperature"],
        variable_name=data["atmospheric_co2_ref"],
        time_index=time_index,
    )

    # Calculate soil temperatures, [C]
    lower, upper = getattr(bounds, "soil_temperature")
    output["soil_temperature"] = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=output["air_temperature"].isel(
            layers=layer_structure.index_surface
        ),
        mean_annual_temperature=data["mean_annual_temperature"].isel(
            time_index=time_index
        ),
        layer_structure=layer_structure,
        upper_bound=upper,
        lower_bound=lower,
    )

    # Initialise canopy and understorey temperature, [C]
    output["canopy_temperature"] = output["air_temperature"].copy()

    # Initialise diurnal temperature range, [C]
    diurnal_temperature_range = layer_structure.from_template()
    layer_values = (
        data["diurnal_temperature_range_ref"].isel(time_index=time_index).values
    )
    output["diurnal_temperature_range"] = diurnal_temperature_range.where(
        diurnal_temperature_range.isnull(),
        other=layer_values,
    )

    # Calculate net radiation, [W m-2].
    canopy_longwave_emission = energy_balance.calculate_longwave_emission(
        temperature=output["canopy_temperature"].to_numpy(),
        emissivity=constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    soil_longwave_emission = energy_balance.calculate_longwave_emission(
        temperature=output["soil_temperature"][
            layer_structure.index_topsoil_scalar
        ].to_numpy(),
        emissivity=constants.soil_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    net_radiation_canopy = (
        data["shortwave_absorption"][layer_structure.index_filled_canopy].to_numpy()
        - canopy_longwave_emission[layer_structure.index_filled_canopy]
    )
    net_radiation_understorey = (
        data["shortwave_absorption"][layer_structure.index_surface_scalar].to_numpy()
        - canopy_longwave_emission[layer_structure.index_surface_scalar]
    )
    net_radiation_soil = (
        data["shortwave_absorption"][layer_structure.index_topsoil_scalar].to_numpy()
        - soil_longwave_emission
    )

    net_radiation = layer_structure.from_template()
    net_radiation[layer_structure.index_filled_canopy] = net_radiation_canopy
    net_radiation[layer_structure.index_surface_scalar] = net_radiation_understorey
    net_radiation[layer_structure.index_topsoil_scalar] = net_radiation_soil
    output["net_radiation"] = net_radiation

    return output


def log_interpolation(
    reference_data: NDArray[np.floating],
    leaf_area_index_sum: NDArray[np.floating],
    layer_structure: LayerStructure,
    layer_heights: NDArray[np.floating],
    measurement_height: float,
    upper_bound: float,
    lower_bound: float,
    gradient: float,
) -> DataArray:
    """LAI regression and logarithmic interpolation of variables above ground.

    Args:
        reference_data: Input variable at reference height
        leaf_area_index_sum: Leaf area index summed over all canopy layers, [m m-1]
        layer_structure: The LayerStructure instance for the simulation.
        layer_heights: Vertical layer heights, [m]
        measurement_height: Height at which to interpolate the variable, [m]
        lower_bound: Minimum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        upper_bound: Maximum allowed value, used to constrain log interpolation.
        gradient: Gradient of regression from :cite:t:`hardwick_relationship_2015`

    Returns:
        vertical logarithmic profile of provided variable
    """

    # Calculate microclimatic variable at measurement height as function of LAI
    lai_regression = leaf_area_index_sum * gradient + reference_data

    # Avoid invalid heights
    positive_layer_heights = np.where(layer_heights > 0, layer_heights, np.nan)

    # Top height
    reference_height = positive_layer_heights[layer_structure.index_above]

    # Calculate per cell slope and intercept for logarithmic within-canopy profile
    slope = (reference_data - lai_regression) / (
        np.log(reference_height) - np.log(measurement_height)
    )
    intercept = lai_regression - slope * np.log(measurement_height)

    # Calculate the values within cells by layer
    layer_values = np.log(positive_layer_heights) * slope + intercept

    # set upper and lower bounds
    return_array = layer_structure.from_template()
    return_array[:] = np.clip(layer_values, lower_bound, upper_bound)

    return return_array


def exp_interpolation(
    reference_data: NDArray[np.floating],
    leaf_area_index_sum: NDArray[np.floating],
    layer_structure: LayerStructure,
    layer_heights: NDArray[np.floating],
    measurement_height: float,
    upper_bound: float,
    lower_bound: float,
    gradient: float,
) -> DataArray:
    """LAI regression and exponential interpolation of variables above ground.

    Args:
        reference_data: Input variable at reference height
        leaf_area_index_sum: Leaf area index summed over all canopy layers, [m m-1]
        layer_structure: The LayerStructure instance for the simulation.
        layer_heights: Vertical layer heights, [m]
        measurement_height: Height at which to interpolate the variable, [m]
        lower_bound: Minimum allowed value, used to constrain exp interpolation. Note
            that currently no conservation of water and energy!
        upper_bound: Maximum allowed value, used to constrain exp interpolation.
        gradient: Gradient of regression from :cite:t:`hardwick_relationship_2015`

    Returns:
        vertical exponential profile of provided variable
    """

    # Value at measurement height from LAI regression
    lai_regression = leaf_area_index_sum * gradient + reference_data

    # Avoid invalid heights
    positive_layer_heights = np.where(layer_heights > 0, layer_heights, np.nan)

    # Top height
    reference_height = positive_layer_heights[layer_structure.index_above]

    # Normalized vertical coordinate: 0 at canopy top, 1 at measurement height
    relative_canopy_depth = (reference_height - positive_layer_heights) / (
        reference_height - measurement_height
    )

    # Normalized exponential profile
    exp_profile = (1 - np.exp(-gradient * relative_canopy_depth)) / (
        1 - np.exp(-gradient)
    )

    # Interpolate between top and bottom
    layer_values = (lai_regression - reference_data) * exp_profile + reference_data

    # Apply bounds
    return_array = layer_structure.from_template()
    return_array[:] = np.clip(layer_values, lower_bound, upper_bound)

    return return_array


def calculate_vapour_pressure_deficit(
    temperature: DataArray,
    relative_humidity: DataArray,
    pyrealm_core_constants: PyrealmCoreConst,
) -> dict[str, DataArray]:
    """Calculate vapour pressure and vapour pressure deficit, kPa.

    Vapor pressure deficit is defined as the difference between saturated vapour
    pressure and actual vapour pressure.

    Args:
        temperature: temperature, [C]
        relative_humidity: relative humidity, []
        pyrealm_core_constants: Set of core constants from pyrealm which include factors
            for saturation vapour pressure calculation

    Return:
        vapour pressure, [kPa], vapour pressure deficit, [kPa]
    """

    output = {}
    saturation_vapour_pressure_numpy = calculate_vp_sat(
        tc=temperature.to_numpy(),
        core_const=pyrealm_core_constants,
    )
    saturation_vapour_pressure = saturation_vapour_pressure_numpy
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
        layer_heights: Vertical layer heights, [m]
        layer_roles: List of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        surface_temperature: Surface temperature, [C]
        mean_annual_temperature: Mean annual temperature, [C]
        layer_structure: The LayerStructure instance for the simulation.
        upper_bound: Maximum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        lower_bound: Minimum allowed value, used to constrain log interpolation.

    Returns:
        soil temperature profile, [C]
    """

    # Select surface layer (atmosphere) and generate interpolation heights
    surface_layer = layer_heights[layer_structure.index_surface].to_numpy()
    soil_depths = layer_heights[layer_structure.index_all_soil].to_numpy()
    interpolation_heights = np.concatenate(
        [
            surface_layer,
            -1 * soil_depths + surface_layer,
        ]
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
