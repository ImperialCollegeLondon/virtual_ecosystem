"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import xarray as xr
from xarray import DataArray


def test_log_interpolation(dummy_climate_data, fixture_core_components):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import log_interpolation

    data = dummy_climate_data
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=fixture_core_components.layer_structure,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_air_temp = fixture_core_components.layer_structure.from_template()
    t_vals = [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    exp_air_temp.T[..., [0, 1, 2, 3, 11]] = t_vals
    xr.testing.assert_allclose(result, exp_air_temp)

    # relative humidity
    result_hum = log_interpolation(
        data=data,
        reference_data=data["relative_humidity_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=fixture_core_components.layer_structure,
        layer_heights=data["layer_heights"],
        upper_bound=100,
        lower_bound=0,
        gradient=5.4,
    )

    exp_humidity = fixture_core_components.layer_structure.from_template()
    humidity_vals = [90.0, 90.341644, 92.488034, 96.157312, 100.0]
    exp_humidity.T[..., [0, 1, 2, 3, 11]] = humidity_vals
    xr.testing.assert_allclose(result_hum, exp_humidity)


def test_varying_canopy_log_interpolation(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import log_interpolation

    data = dummy_climate_data_varying_canopy
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=fixture_core_components.layer_structure,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_air_temp = fixture_core_components.layer_structure.from_template()
    exp_air_temp[[0, 1, 2, 3, 11], :] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.844995, 29.896663, 29.948332, 29.948332],
        [28.87117, 29.247446, np.nan, np.nan],
        [27.206405, np.nan, np.nan, np.nan],
        [16.145945, 20.763963, 25.381982, 25.381982],
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
        data["air_temperature_ref"].isel(time_index=0),
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )

    exp_output = DataArray(
        np.repeat(1.41727, 4),
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2, 3]},
    )
    xr.testing.assert_allclose(result, exp_output)


def test_calculate_vapour_pressure_deficit(fixture_core_components):
    """Test calculation of VPD."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_vapour_pressure_deficit,
    )

    temperature = fixture_core_components.layer_structure.from_template()
    t_vals = [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    temperature.T[..., [0, 1, 2, 3, 11]] = t_vals

    rel_humidity = fixture_core_components.layer_structure.from_template()
    humidity_vals = [90.0, 90.341644, 92.488034, 96.157312, 100.0]
    rel_humidity.T[..., [0, 1, 2, 3, 11]] = humidity_vals

    constants = AbioticSimpleConsts()
    result = calculate_vapour_pressure_deficit(
        temperature=temperature,
        relative_humidity=rel_humidity,
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )
    exp_output = fixture_core_components.layer_structure.from_template()
    vpd_vals = [0.141727, 0.136357, 0.103501, 0.050763, 0.0]
    exp_output.T[..., [0, 1, 2, 3, 11]] = vpd_vals

    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_varying_canopy_calculate_vapour_pressure_deficit(
    fixture_core_components, dummy_climate_data_varying_canopy
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
    exp_output = fixture_core_components.layer_structure.from_template()
    exp_output[[0, 1, 2, 3, 11], :] = [
        [0.141727, 0.141727, 0.141727, 0.141727],
        [0.136357, 0.136357, 0.136357, 0.136357],
        [0.103501, 0.103501, np.nan, np.nan],
        [0.050763, np.nan, np.nan, np.nan],
        [0.0, 0.0, 0.0, 0.0],
    ]
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_run_microclimate(dummy_climate_data, fixture_core_components):
    """Test interpolation of all variables."""

    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )
    from virtual_ecosystem.models.abiotic_simple.microclimate import run_microclimate

    data = dummy_climate_data

    result = run_microclimate(
        data=data,
        layer_structure=fixture_core_components.layer_structure,
        time_index=0,
        constants=AbioticSimpleConsts(),
        bounds=AbioticSimpleBounds(),
    )

    exp_air_temp = fixture_core_components.layer_structure.from_template()
    exp_air_temp[[0, 1, 2, 3, 11]] = np.array(
        [30.0, 29.91965, 29.414851, 28.551891, 22.81851]
    )[:, None]
    xr.testing.assert_allclose(result["air_temperature"], exp_air_temp)

    exp_soil_temp = fixture_core_components.layer_structure.from_template()
    exp_soil_temp[[12, 13]] = np.array([20.712458, 20.0])[:, None]
    xr.testing.assert_allclose(result["soil_temperature"], exp_soil_temp)

    exp_pressure = fixture_core_components.layer_structure.from_template()
    exp_pressure[np.arange(0, 12)] = 96
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_pressure)


def test_run_microclimate_varying_canopy(
    dummy_climate_data_varying_canopy, fixture_core_components
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
        layer_structure=fixture_core_components.layer_structure,
        time_index=0,
        constants=AbioticSimpleConsts(),
        bounds=AbioticSimpleBounds(),
    )

    exp_air_temp = fixture_core_components.layer_structure.from_template()
    exp_air_temp[[0, 1, 2, 3, 11], :] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.91965, 29.946434, 29.973217, 29.973217],
        [29.414851, 29.609901, np.nan, np.nan],
        [28.551891, np.nan, np.nan, np.nan],
        [22.81851, 25.21234, 27.60617, 27.60617],
    ]
    xr.testing.assert_allclose(result["air_temperature"], exp_air_temp)

    exp_soil_temp = fixture_core_components.layer_structure.from_template()
    exp_soil_temp[[12, 13], :] = [
        [20.712458, 21.317566, 21.922674, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(result["soil_temperature"], exp_soil_temp)

    exp_pressure = fixture_core_components.layer_structure.from_template()
    exp_pressure[np.arange(0, 12)] = 96
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_pressure)


def test_interpolate_soil_temperature(dummy_climate_data, fixture_core_components):
    """Test soil temperature interpolation."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        interpolate_soil_temperature,
    )

    data = dummy_climate_data

    surface_temperature = DataArray([22.0, 22.0, 22.0, 22.0], dims="cell_id")
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"],
        layer_structure=fixture_core_components.layer_structure,
        upper_bound=50.0,
        lower_bound=-10.0,
    )

    exp_output = fixture_core_components.layer_structure.from_template()
    exp_output[[12, 13]] = np.array([20.505557, 20.0])[:, None]

    xr.testing.assert_allclose(result, exp_output)
