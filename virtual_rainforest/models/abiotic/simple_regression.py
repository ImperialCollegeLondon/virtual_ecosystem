"""The ``models.abiotic.simple_regression`` module uses simple linear regression
and logarithmic interpolation to calculate atmospheric temperature and humidity and soil
temperature as a function of leaf area index and height. The relationships are derived
from HARDWICK.
"""  # noqa: D205, D415

from typing import Dict, List

import numpy as np
from scipy.optimize import curve_fit
from xarray import DataArray

from virtual_rainforest.core.data import Data

MicroclimateGradients: Dict[str, float] = {
    "air_temperature_max_gradient": -2.45,
    "air_temperature_min_gradient": -0.08,
    "relative_humidity_max_gradient": -0.02,
    "relative_humidity_min_gradient": 9.05,
    "vapor_pressure_deficit_max_gradient": -504,
    "vapor_pressure_deficit_min_gradient": -0.47,
    "soil_temperature_max_gradient": -1.28,
    "soil_temperature_min_gradient": -0.37,
    "soil_temperature_diurnal_range_gradient": -0.92,
}


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

    relative_humidity_min = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("relative_humidity_min")
    """Minimum atmospheric humidity profile"""
    relative_humidity_max = DataArray(
        np.full_like(air_temperature_min, np.nan),
        dims=air_temperature_min.dims,
        coords=air_temperature_min.coords,
    ).rename("relative_humidity_max")
    """Maximum atmospheric humidity profile"""

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

    return [
        air_temperature_min,
        air_temperature_max,
        relative_humidity_min,
        relative_humidity_max,
        vapor_pressure_deficit_min,
        vapor_pressure_deficit_max,
        soil_temperature_min,
        soil_temperature_max,
    ]


def run_simple_regression(
    data: Data,
    layer_roles: List[str],
    input_list: List[str],
    canopy_node_heights: DataArray,
    atmosphere_node_heights: DataArray,
    soil_node_depths: DataArray,
    leaf_area_index: DataArray,
    MicroclimateGradients: Dict[str, float] = MicroclimateGradients,
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
        layer_roles: roles of vertical layers
        input_list: list of output variables to be calculated
        canopy_node_heights: heights of canopy layers, the first canopy layer equals the
            canopy height, [m]
        atmosphere_node_heights
        soil_node_depths
        leaf_area_index: leaf area index, [m m-1]

    Returns:
        list of min/max for air temperature, relative humidity, vapor pressure deficit,
        and soil temperature
    """
    # set limits for humidity

    output = []

    for i in range(0, len(input_list)):
        if "air_temperature" in input_list[i]:
            reference_data = data["air_temperature_ref"].isel(layers=0)
        elif "relative_humidity" in input_list[i]:
            reference_data = data["relative_humidity_ref"].isel(layers=0)
        elif "vapor_pressure" in input_list[i]:
            reference_data = data["vapor_pressure_deficit_ref"].isel(layers=0)
        elif "soil_temperature" in input_list[i]:
            reference_data = data["air_temperature_ref"].isel(layers=0) + 5.0
        else:
            "This variable is not implemented"

        gradient = input_list[i] + "_gradient"
        value_from_lai = DataArray(
            MicroclimateGradients[gradient] * leaf_area_index.sum(dim="layers")
            + reference_data
        )

        # Fit logarithmic function to interpolate between temperature top and 1.5m
        x_values = np.array(
            [
                canopy_node_heights.isel(layers=1) + 2,
                np.repeat(1.5, len(data.grid.cell_id)),
            ]
        ).flatten()
        y_values = np.array([reference_data, value_from_lai]).flatten()

        popt, pcov = curve_fit(logarithmic, x_values, y_values)
        a, b = popt  # the function coefficients

        if "soil" not in input_list[i]:
            output_heights = atmosphere_node_heights
        else:
            output_heights = soil_node_depths

        output_variable = DataArray(
            a * np.log(output_heights) + b,
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, len(layer_roles)),
                "layer_roles": (
                    "layers",
                    layer_roles[0 : len(layer_roles)],
                ),
                "cell_id": data.grid.cell_id,
            },
            name=input_list[i],
        )

        output.append(output_variable)

    return output


def logarithmic(x: DataArray, a: float, b: float) -> DataArray:
    """Logarithmic function."""
    return DataArray(a * np.log(x) + b)
