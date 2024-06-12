"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import xarray as xr
from xarray import DataArray


def test_varying_canopy_log_interpolation(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_empty_2d_array,
):
    """Test log interpolation method for air temperature profile."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import log_interpolation

    data = dummy_climate_data_varying_canopy
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=np.repeat(-2.45, 3),
    )

    air_temp1 = fixture_empty_2d_array.copy()
    air_temp1[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.844995, 29.844995, 29.844995],
        [28.87117, 28.87117, np.nan],
        [27.206405, np.nan, np.nan],
        [22.65, 22.65, 22.65],
        [16.145945, 16.145945, 16.145945],
    ]
    air_temp2 = fixture_empty_2d_array.copy()
    air_temp2[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.896663, 29.896663, 29.896663],
        [29.247446, 29.247446, np.nan],
        [28.137603, np.nan, np.nan],
        [25.1, 25.1, 25.1],
        [20.763963, 20.763963, 20.763963],
    ]
    air_temp3 = fixture_empty_2d_array.copy()
    air_temp3[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.948332, 29.948332, 29.948332],
        [29.623723, 29.623723, np.nan],
        [29.068802, np.nan, np.nan],
        [27.55, 27.55, 27.55],
        [25.381982, 25.381982, 25.381982],
    ]
    exp_air_temp = xr.concat(
        [air_temp1, air_temp2, air_temp3],
        dim=xr.DataArray(["mean", "min", "max"], dims="climate_stats"),
    )
    np.testing.assert_allclose(result, exp_air_temp, rtol=1e-4, atol=1e-4)


def test_calculate_saturation_vapour_pressure(dummy_climate_data):
    """Test calculation of saturation vapour pressure."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_saturation_vapour_pressure,
    )

    data = dummy_climate_data
    constants = AbioticSimpleConsts()
    # Extract saturation factors from constants
    result = calculate_saturation_vapour_pressure(
        data["air_temperature_ref"].isel(time_index=0),
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )

    exp_output = DataArray(
        [1.41727, 1.41727, 1.41727],
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2]},
    )
    np.testing.assert_allclose(result, exp_output, rtol=1e-4, atol=1e-4)


def test_varying_canopy_calculate_vapour_pressure_deficit(
    fixture_empty_2d_array, dummy_climate_data_varying_canopy
):
    """Test calculation of VPD with different number of canopy layers."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_vapour_pressure_deficit,
    )

    data = dummy_climate_data_varying_canopy
    constants = AbioticSimpleConsts()
    result = calculate_vapour_pressure_deficit(
        temperature=data["air_temperature"],
        relative_humidity=data["relative_humidity"],
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )
    vpd = fixture_empty_2d_array.copy()
    vpd[[0, 1, 2, 3, 11, 12], :] = [
        [0.141727, 0.141727, 0.141727],
        [0.136357, 0.136357, 0.136357],
        [0.103501, 0.103501, np.nan],
        [0.050763, np.nan, np.nan],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    exp_vpd = xr.concat(
        [vpd] * 3,
        dim=xr.DataArray(
            ["mean", "min", "max"], dims="climate_stats", name="climate_stats"
        ),
    )
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_vpd)


def test_run_microclimate_varying_canopy(
    dummy_climate_data_varying_canopy, fixture_core_components, fixture_empty_2d_array
):
    """Test interpolation of all variables with varying canopy arrays."""

    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )
    from virtual_ecosystem.models.abiotic_simple.microclimate import run_microclimate

    data = dummy_climate_data_varying_canopy
    result = run_microclimate(
        data=data,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        time_index=0,
        constants=AbioticSimpleConsts(),
        bounds=AbioticSimpleBounds(),
    )

    air_temp1 = fixture_empty_2d_array.copy()
    air_temp1[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.91965, 29.91965, 29.91965],
        [29.414851, 29.414851, np.nan],
        [28.551891, np.nan, np.nan],
        [26.19, 26.19, 26.19],
        [22.81851, 22.81851, 22.81851],
    ]
    air_temp2 = fixture_empty_2d_array.copy()
    air_temp2[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.996626, 29.996626, 29.996626],
        [29.975427, 29.975427, np.nan],
        [29.939187, np.nan, np.nan],
        [29.84, 29.84, 29.84],
        [29.698415, 29.698415, 29.698415],
    ]
    air_temp3 = fixture_empty_2d_array.copy()
    air_temp3[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.948332, 29.948332, 29.948332],
        [29.623723, 29.623723, np.nan],
        [29.068802, np.nan, np.nan],
        [27.55, 27.55, 27.55],
        [25.381982, 25.381982, 25.381982],
    ]
    exp_air_temp = xr.concat(
        [air_temp1, air_temp2, air_temp3],
        dim=xr.DataArray(["mean", "min", "max"], dims="climate_stats"),
    )
    np.testing.assert_allclose(
        result["air_temperature"], exp_air_temp, rtol=1e-4, atol=1e-4
    )

    soil_temp = fixture_empty_2d_array.copy()
    soil_temp[[13, 14], :] = [[20.712458, 22.451549, 21.360448], [20.0, 20.0, 20.0]]
    exp_soil_temp = xr.concat(
        [soil_temp] * 3,
        dim=xr.DataArray(
            ["mean", "min", "max"], dims="climate_stats", name="climate_stats"
        ),
    )
    xr.testing.assert_allclose(result["soil_temperature"], exp_soil_temp)

    soil_values = DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"])
    pressure_values = DataArray(np.full((13, 3), 96.0), dims=["layers", "cell_id"])
    exp_pressure = xr.concat(
        [pressure_values, soil_values], dim="layers"
    ).assign_coords(data["layer_heights"].coords)
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_pressure)


def test_interpolate_soil_temperature(dummy_climate_data):
    """Test soil temperature interpolation."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        interpolate_soil_temperature,
    )

    data = dummy_climate_data

    surface_temperature = DataArray(
        np.full((3, 3), 22.0),
        dims=["cell_id", "climate_stats"],
        coords={
            "cell_id": [0, 1, 2],
            "climate_stats": ["mean", "min", "max"],
        },
    )
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"],
        upper_bound=50.0,
        lower_bound=-10.0,
    )

    exp_output = DataArray(
        [
            [
                [20.505557, 20.505557, 20.505557],
                [20.505557, 20.505557, 20.505557],
                [20.505557, 20.505557, 20.505557],
            ],
            [
                [20.0, 20.0, 20.0],
                [20.0, 20.0, 20.0],
                [20.0, 20.0, 20.0],
            ],
        ],
        dims=["layers", "cell_id", "climate_stats"],
        coords={
            "layers": [13, 14],
            "layer_roles": ("layers", ["soil", "soil"]),
            "cell_id": [0, 1, 2],
            "climate_stats": ["mean", "min", "max"],
        },
    )
    xr.testing.assert_allclose(result, exp_output)
