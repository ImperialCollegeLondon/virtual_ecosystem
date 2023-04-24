"""The ``models.abiotic.simple_regression`` module uses simple linear regression
and logarithmic interpolation to calculate atmospheric temperature and humidity and soil
temperature as a function of leaf area index and height. The relationships are derived
from HARDWICK.
"""  # noqa: D205, D415

from dataclasses import dataclass
from typing import List

import numpy as np
from scipy.optimize import curve_fit
from xarray import DataArray

from virtual_rainforest.core.data import Data


@dataclass
class MicroclimateGradients:
    """Regression parameters for 1.5 m microclimate calculations."""

    air_temperature_max_gradient: float = -2.45
    """Maximum air temperature gradient from linear regression """
    air_temperature_min_gradient: float = -0.08
    """Maximum air temperature gradient from linear regression """

    relative_humidity_max_gradient: float = -0.02
    """Maximum relative humidity gradient from linear regression """
    relative_humidity_min_gradient: float = 9.05
    """Maximum relative humidity gradient from linear regression """

    vapor_pressure_deficit_max_gradient: float = -504
    """Maximum vapor pressure deficit gradient from linear regression """
    vapor_pressure_deficit_min_gradient: float = -0.47
    """Maximum vapor pressure deficit gradient from linear regression """

    soil_temperature_max_gradient: float = -1.28
    """Maximum soil temperature gradient from linear regression """
    soil_temperature_min_gradient: float = -0.37
    """Maximum soil temperature gradient from linear regression """
    soil_temperature_diurnal_range_gradient: float = -0.92
    """Maximum soil temperature gradient from linear regression """


layer_roles: List[str] = [
    "above",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "subcanopy",
    "surface",
    "soil",
    "soil",
]


def setup_simple_regression(
    layer_roles: List[str],
    data: Data,
) -> List[DataArray]:
    """Set up abiotic environment."""

    air_temperature_min = DataArray(
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
        name="air_temperature_min",
    )
    """Minimum air temperature profile, [C]"""
    air_temperature_max = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("air_temperature_max")
    """Maximum air temperature profile, [C]"""
    air_temperature_mean = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("air_temperature_mean")
    """Mean air temperature profile, [C]"""
    air_temperature_diurnal_range = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("air_temperature_diurnal_range")
    """Diurnal range of air temperature profile, [C]"""

    atmospheric_humidity_min = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("atmospheric_humidity_min")
    """Minimum atmospheric humidity profile"""
    atmospheric_humidity_max = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("atmospheric_humidity_max")
    """Maximum atmospheric humidity profile"""
    atmospheric_humidity_mean = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("atmospheric_humidity_mean")
    """Mean atmospheric humidity profile"""
    atmospheric_humidity_diurnal_range = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("atmospheric_humidity_diurnal_range")
    """Diurnal range of atmospheric humidity profile"""

    vapor_pressure_deficit_min = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("vapor_pressure_deficit_min")
    """Minimum vapor pressure deficit profile"""
    vapor_pressure_deficit_max = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("vapor_pressure_deficit_max")
    """Maximum vapor pressure deficit profile"""
    vapor_pressure_deficit_mean = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("vapor_pressure_deficit_mean")
    """Mean vapor pressure deficit profile"""
    vapor_pressure_deficit_diurnal_range = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("vapor_pressure_deficit_diurnal_range")
    """Diurnal range of vapor pressure deficit profile"""

    soil_temperature_min = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("soil_temperature_min")
    """Minimum soil temperature profile, [C]"""
    soil_temperature_max = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("soil_temperature_max")
    """Maximum soil temperature profile, [C]"""
    soil_temperature_mean = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("soil_temperature_mean")
    """Mean soil temperature profile, [C]"""
    soil_temperature_diurnal_range = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("soil_temperature_diurnal_range")
    """Diurnal range of soil temperature profile, [C]"""

    return [
        air_temperature_min,
        air_temperature_max,
        air_temperature_mean,
        air_temperature_diurnal_range,
        atmospheric_humidity_min,
        atmospheric_humidity_max,
        atmospheric_humidity_mean,
        atmospheric_humidity_diurnal_range,
        vapor_pressure_deficit_min,
        vapor_pressure_deficit_max,
        vapor_pressure_deficit_mean,
        vapor_pressure_deficit_diurnal_range,
        soil_temperature_min,
        soil_temperature_max,
        soil_temperature_mean,
        soil_temperature_diurnal_range,
    ]


def run_simple_regression(
    data: Data,
    layer_roles: List[str],
    canopy_node_heights: DataArray,
    leaf_area_index: DataArray,
    MicroclimateGradients: MicroclimateGradients = MicroclimateGradients(),
) -> List[DataArray]:
    """Calculate simple microclimate.

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
    the input at the top of the canopy and the 1.5 m values. The `layer_roles` list is
    composed of the following layers (index 0 above canopy):

    * above canopy
    * canopy layers (maximum of ten layers, minimum one layers)
    * subcanopy (1.5 m)
    * surface layer
    * soil layers (currently one near surface layer and one layer at 1 m below ground)

    The function expects a data object with the following variables:

    * air_temperature_ref
    * relative_humidity_ref

    Args:
        data: Data object
        canopy_node_heights: heights of canopy layers, the first entry equals the canopy
            height, [m]
        leaf_area_index: leaf area index, [m m-1]

    Returns:
        list of min/max for air temperature, relative humidity, vapor pressure deficit,
        and soil temperature
    """

    output = []

    gradient = MicroclimateGradients
    # TODO find a clever way to loop over min max mean diurnal_range of all vars

    # calculate temperature at 1.5 m as a function of LAI based on Hardwick (2015)
    air_temperature_min_lai = DataArray(
        gradient.air_temperature_min_gradient * leaf_area_index.sum(dim="layers")
        + data["air_temperature_ref"].isel(layers=0)
    )

    # Fit logarithmic function to interpolate between temperature top and 1.5m
    x_values = np.array(
        [canopy_node_heights.isel(layers=1), np.repeat(1.5, len(data.grid.cell_id))]
    ).flatten()
    y_values = np.array(
        [data["air_temperature_ref"].isel(layers=0), air_temperature_min_lai]
    ).flatten()

    popt, pcov = curve_fit(logarithmic, x_values, y_values)
    a, b = popt  # the function coefficients

    air_temperature_min = DataArray(
        a * np.log(canopy_node_heights) + b,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        },
        name="air_temperature_min",
    )
    output.append(air_temperature_min)

    return output


def logarithmic(x: DataArray, a: float, b: float) -> DataArray:
    """Logarithmic function."""
    return DataArray(a * np.log(x) + b)
