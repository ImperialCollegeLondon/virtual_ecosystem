"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import xarray as xr
from xarray import DataArray


def test_log_interpolation(
    dummy_climate_data, fixture_core_components, fixture_empty_array
):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import log_interpolation

    data = dummy_climate_data
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_mean_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_air_temp = fixture_empty_array.copy()
    t_vals = [30.0, 29.844995, 28.87117, 27.206405, 22.65, 16.145945]
    exp_air_temp.T[..., [0, 1, 2, 3, 11, 12]] = t_vals
    xr.testing.assert_allclose(result, exp_air_temp)

    # relative humidity
    result_hum = log_interpolation(
        data=data,
        reference_data=data["relative_humidity_mean_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=100,
        lower_bound=0,
        gradient=5.4,
    )

    exp_humidity = fixture_empty_array.copy()
    humidity_vals = [90.0, 90.341644, 92.488034, 96.157312, 100.0, 100.0]
    exp_humidity.T[..., [0, 1, 2, 3, 11, 12]] = humidity_vals
    xr.testing.assert_allclose(result_hum, exp_humidity)


def test_ragged_log_interpolation(
    dummy_climate_data_ragged, fixture_core_components, fixture_empty_array
):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import log_interpolation

    data = dummy_climate_data_ragged
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_mean_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_air_temp = fixture_empty_array.copy()
    exp_air_temp[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.844995, 29.896663, 29.948332],
        [28.87117, 29.247446, np.nan],
        [27.206405, np.nan, np.nan],
        [22.65, 25.1, 27.55],
        [16.145945, 20.763963, 25.381982],
    ]
    xr.testing.assert_allclose(result, exp_air_temp)


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
        data["air_temperature_mean_ref"].isel(time_index=0),
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )

    exp_output = DataArray(
        [1.41727, 1.41727, 1.41727],
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2]},
    )
    xr.testing.assert_allclose(result, exp_output)


def test_calculate_vapour_pressure_deficit(fixture_empty_array):
    """Test calculation of VPD."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_vapour_pressure_deficit,
    )

    temperature = fixture_empty_array.copy()
    t_vals = [30.0, 29.844995, 28.87117, 27.206405, 22.65, 16.145945]
    temperature.T[..., [0, 1, 2, 3, 11, 12]] = t_vals
    rel_humidity = fixture_empty_array.copy()
    humidity_vals = [90.0, 90.341644, 92.488034, 96.157312, 100.0, 100.0]
    rel_humidity.T[..., [0, 1, 2, 3, 11, 12]] = humidity_vals

    constants = AbioticSimpleConsts()
    result = calculate_vapour_pressure_deficit(
        temperature=temperature,
        relative_humidity=rel_humidity,
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )
    exp_output = fixture_empty_array.copy()
    vpd_vals = [0.141727, 0.136357, 0.103501, 0.050763, 0.0, 0.0]
    exp_output.T[..., [0, 1, 2, 3, 11, 12]] = vpd_vals

    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_ragged_calculate_vapour_pressure_deficit(
    fixture_empty_array, dummy_climate_data_ragged
):
    """Test calculation of VPD with different number of canopy layers."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_vapour_pressure_deficit,
    )

    data = dummy_climate_data_ragged
    constants = AbioticSimpleConsts()
    result = calculate_vapour_pressure_deficit(
        temperature=data["air_temperature"],
        relative_humidity=data["relative_humidity"],
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )
    exp_output = fixture_empty_array.copy()
    exp_output[[0, 1, 2, 3, 11, 12], :] = [
        [0.141727, 0.141727, 0.141727],
        [0.136357, 0.136357, 0.136357],
        [0.103501, 0.103501, np.nan],
        [0.050763, np.nan, np.nan],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_run_microclimate(
    dummy_climate_data, fixture_core_components, fixture_empty_array
):
    """Test interpolation of all variables."""

    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )
    from virtual_ecosystem.models.abiotic_simple.microclimate import run_microclimate

    data = dummy_climate_data

    result = run_microclimate(
        data=data,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        time_index=0,
        constants=AbioticSimpleConsts(),
        bounds=AbioticSimpleBounds(),
    )

    exp_air_temp = fixture_empty_array.copy()
    exp_air_temp[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.91965, 29.91965, 29.91965],
        [29.414851, 29.414851, 29.414851],
        [28.551891, 28.551891, 28.551891],
        [26.19, 26.19, 26.19],
        [22.81851, 22.81851, 22.81851],
    ]
    xr.testing.assert_allclose(result["air_temperature_mean"], exp_air_temp)

    soil_values = DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"])
    pressure_values = DataArray(np.full((13, 3), 96.0), dims=["layers", "cell_id"])
    exp_pressure = xr.concat(
        [pressure_values, soil_values], dim="layers"
    ).assign_coords(data["layer_heights"].coords)
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_pressure)


def test_run_microclimate_ragged(
    dummy_climate_data_ragged, fixture_core_components, fixture_empty_array
):
    """Test interpolation of all variables with ragged arrays."""

    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )
    from virtual_ecosystem.models.abiotic_simple.microclimate import run_microclimate

    data = dummy_climate_data_ragged

    result = run_microclimate(
        data=data,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        time_index=0,
        constants=AbioticSimpleConsts(),
        bounds=AbioticSimpleBounds(),
    )

    exp_air_temp = fixture_empty_array.copy()
    exp_air_temp[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.91965, 29.946434, 29.973217],
        [29.414851, 29.609901, np.nan],
        [28.551891, np.nan, np.nan],
        [26.19, 27.46, 28.73],
        [22.81851, 25.21234, 27.60617],
    ]
    xr.testing.assert_allclose(result["air_temperature_mean"], exp_air_temp)

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

    surface_temperature = DataArray([22.0, 22.0, 22.0], dims="cell_id")
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"].isel(time_index=0),
        upper_bound=50.0,
        lower_bound=-10.0,
    )

    exp_output = DataArray(
        [
            [20.505557, 20.505557, 20.505557],
            [20.0, 20.0, 20.0],
        ],
        dims=["layers", "cell_id"],
        coords={
            "layers": [13, 14],
            "layer_roles": ("layers", ["soil", "soil"]),
            "cell_id": [0, 1, 2],
        },
    )

    xr.testing.assert_allclose(result, exp_output)
