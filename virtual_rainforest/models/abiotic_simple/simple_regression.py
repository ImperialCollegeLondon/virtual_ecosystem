r"""The ``models.abiotic_simple.simple_regression`` module uses simple linear regression
and logarithmic interpolation to calculate atmospheric temperature and humidity and soil
temperature as a function of leaf area index and height. The relationships are derived
from HARDWICK. The module also provides a constant vertical profile of atmospheric
pressure and :math:`\ce{CO2}`. Soil moisture and surface runoff are calculated with a
simple bucket model.
"""  # noqa: D205, D415

from typing import Dict, List  # , Union, Tuple

import numpy as np
import xarray as xr
from scipy.optimize import curve_fit
from xarray import DataArray

from virtual_rainforest.core.data import Data

MicroclimateGradients: Dict[str, float] = {
    "air_temperature_gradient": -1.27,
    "relative_humidity_gradient": 5.4,
    "vapor_pressure_deficit_gradient": -252.24,
    "soil_temperature_gradient": -0.61,
    "soil_temperature_diurnal_range_gradient": -0.92,
}

MicroclimateParameters: Dict[str, float] = {
    "soil_moisture_capacity": 150,
    "soil_temperature_adjustment": 5,
    "water_interception_factor": 0.1,
}


def setup_simple_regression(
    layer_roles: List[str],
    data: Data,
) -> List[DataArray]:
    r"""Set up abiotic environment variables.

    Args:
        layer_roles: list of layer roles (soil, surface, subcanopy, canopy, above)
        data: Data object

    Returns:
        list of DataArrays for air temperature, relative humidity, vapor pressure
        deficit, soil temperature, atmospheric pressure, atmospheric :math:`\ce{CO2}`,
        soil moisture, and surface runoff
    """

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

    relative_humidity = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("relative_humidity")
    """Mean relative humidity profile"""

    vapor_pressure_deficit = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("vapor_pressure_deficit")
    """Mean vapor pressure deficit profile"""

    soil_temperature = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("soil_temperature")
    """Mean soil temperature profile, [C]"""

    atmospheric_pressure = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("atmospheric_pressure")
    """Atmospheric pressure profile, [kPa]"""

    atmospheric_CO2 = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("atmospheric_co2")
    r"""Atmospheric :math:`\ce{CO2}` profile, [ppm]"""

    soil_moisture = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("soil_moisture")
    """Soil moisture"""

    surface_runoff = DataArray(
        np.full_like(air_temperature, np.nan),
        dims=air_temperature.dims,
        coords=air_temperature.coords,
    ).rename("surface_runoff")
    """Surface runoff, [mm]"""

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
    time_index: int,  # could be datetime
    MicroclimateGradients: Dict[str, float] = MicroclimateGradients,
    MicroclimateParameters: Dict[str, float] = MicroclimateParameters,
) -> List[DataArray]:
    r"""Calculate simple microclimate.

    This function uses empirical relationships between leaf area index (LAI) and
    atmospheric temperature, humidity and soil temperature to derive logarithmic
    profiles of atmospheric temperature and humidity as well as soil temperatures
    from external climate data such as regional climate models or satellite
    observations. For below canopy values (1.5 m), the implementation is based on
    HARDWICK as

    :math:`y = m * LAI + c`

    where :math:`y` is the variable of interest, math:`m` is the gradient
    (see MicroclimateGradients) and :math:`c` is the intersect which we set to the
    external data values. We assume that the gradient remains constant.

    The other layers are calculated by logaritmic regression and interpolation between
    the input at the top of the canopy and the 1.5 m values (except for atmospheric
    pressure and :math:`\ce{CO2}` which are constant). The `layer_roles` list is
    composed of the following layers (index 0 above canopy):

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
        layer_roles: roles of vertical layers
        time_index: time index, integer
        MicroclimateGradients: gradients for linear regression
        MicroclimateParameters: dictionnary of microclimate parameters

    Returns:
        list of air temperature, relative humidity, vapor pressure deficit, soil
        temperature, atmospheric pressure, atmospheric :math:`\ce{CO2}`, soil moisture,
        and surface runoff
    """
    # set limits for humidity

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
    # calculate vapor pressure deficit at reference height
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

    # TODO soil temperature; interpolation from surface to 1m depth (annual mean)?

    # highest_soil_layer = (
    #     (
    #         air_temperature.isel(layers=12)
    #         + data["mean_annual_temperature"].isel(layers=14)
    #     )
    #     / 2
    # ).expand_dims("layers")
    # soil_temperature = xr.concat(
    #     [
    #         DataArray(
    #             np.full((len(layer_roles), len(data.grid.cell_id)), np.nan),
    #             dims=["layers", "cell_id"],
    #             coords={
    #                 "layers": np.arange(0, len(layer_roles)),
    #                 "layer_roles": (
    #                     "layers",
    #                     layer_roles[0 : len(layer_roles)],
    #                 ),
    #                 "cell_id": data.grid.cell_id,
    #             },
    #         ),
    #         highest_soil_layer,
    #         data["mean_annual_temperature"].isel(layer=14),
    #     ],
    #     dim="layers",
    # )
    # output.append(soil_temperature)

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

    # soil moisture

    # precipitation_surface = (
    #    data["precipitation"] * MicroclimateParameters['water_interception_factor']
    #  * data["leaf_area_index"].sum(dim="layers")
    # ) TODO check dimensions (write in surface layer)

    # soil_moisture, surface_run_off = calculate_soil_moisture(
    #       precipitation_surface,
    #       current_soil_moisture,
    #       soil_moisture_capacity= MicroclimateParameters['soil_moisture_capacity'],
    # )

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
        leaf_area_index: leaf area index
        gradient: gradient of regression from Harwick

    Returns:
        microclimatic variable at 1.5 m
    """

    return DataArray(
        leaf_area_index.sum(dim="layers") * gradient + reference_data, dims="cell_id"
    )


def logarithmic(x: DataArray, a: float, b: float) -> DataArray:
    """Logarithmic function."""
    return DataArray(a * np.log(x) + b)


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
        layer_roles: list of layer roles
        layer_heights: vertical layer heights
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

    return DataArray(
        a * np.log(layer_heights) + b,
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
) -> DataArray:
    r"""Calculate saturation vapor pressure.

    Saturation vapor pressure :math:`e_{s} (T)` is here calculated as
    :math:`e_{s}(T) = 0.61078 exp(\frac{7.5 T}{T + 237.3})`
    where :math:`T` is temperature in degree C .

    Args:
        temperature: air temperature, [C]

    Returns:
        saturation vapor pressure, kPa
    """
    return DataArray(
        (0.61078 * np.exp((7.5 * (temperature)) / (temperature + 237.3))),
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


# TODO HYDROLOGY grid based not ready

# def calculate_surface_runoff(
#     precipitation_surface: DataArray,
#     current_soil_moisture: DataArray,
#     soil_moisture_capacity: Union[DataArray,float],
# ) -> Tuple[DataArray, DataArray]:
#     """Calculate surface runoff and update soil mositure content.
#     Args:
#         precipitation_surface: precipitation that reaches surface, [mm],
#         current_soil_moisture: current soil moisture at upper layer, [mm],
#         soil_moisture_capacity: soil moisture capacity
#     Returns:
#         current soil moisture, [mm], surface runoff, [mm]
#     """
#     # TODO apply to DataArray with where() or any() !
#     if precipitation_surface > soil_moisture_capacity:
#         surface_runoff = current_soil_moisture - soil_moisture_capacity
#         soil_moisture_updated = soil_moisture_capacity

#     elif current_soil_moisture < 0:
#         soil_moisture_updated = DataArray(
#             np.zeros(len(current_soil_moisture)), dims="cell_id"
#         )
#       surface_runoff = DataArray(np.zeros(len(current_soil_moisture)), dims="cell_id")
#     else:
#       surface_runoff = DataArray(np.zeros(len(current_soil_moisture)), dims="cell_id")

#     return (soil_moisture_updated, surface_runoff)
