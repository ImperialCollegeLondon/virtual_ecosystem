"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import xarray as xr
from xarray import DataArray


def test_varying_canopy_log_interpolation(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test log interpolation for wind speed."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        log_interpolation,
    )

    data = dummy_climate_data_varying_canopy
    lyr_strct = fixture_core_components.layer_structure

    # temperature
    result = log_interpolation(
        reference_data=data["wind_speed_ref"].isel(time_index=0).to_numpy(),
        leaf_area_index_sum=np.nansum(data["leaf_area_index"], axis=0),
        layer_structure=lyr_strct,
        layer_heights=data["layer_heights"].to_numpy(),
        upper_bound=10,
        lower_bound=0.001,
        gradient=-0.1,
    )

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [1.0, 1.0, 1.0, 1.0],
        [0.991564, 0.993673, 0.995782, np.nan],
        [0.938567, 0.953925, np.nan, np.nan],
        [0.847968, np.nan, np.nan, np.nan],
        [0.246038, 0.434528, 0.623019, 0.811509],
    ]
    xr.testing.assert_allclose(result, exp_air_temp)


def test_exp_interpolation(fixture_core_components, dummy_climate_data_varying_canopy):
    """Test exponential temperature interpolation."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        exp_interpolation,
    )

    layer_structure = fixture_core_components.layer_structure
    data = dummy_climate_data_varying_canopy

    reference_data = data["air_temperature_ref"].isel(time_index=0).to_numpy()
    layer_heights = data["layer_heights"].to_numpy()
    leaf_area_index_sum = np.nansum(data["leaf_area_index"], axis=0)
    gradient = -1.27

    result = exp_interpolation(
        reference_data=reference_data,
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=layer_structure,
        layer_heights=layer_heights,
        upper_bound=80.0,
        lower_bound=-20.0,
        gradient=gradient,
    )

    # Top layer should equal reference_data
    np.testing.assert_allclose(result[0].values, reference_data)

    # Profile should decrease
    profile = result[layer_structure.index_filled_atmosphere, 0].values
    assert np.all(np.diff(profile) <= 0)

    # Assert bounds are respected
    assert result.max() <= 80
    assert result.min() >= -20

    # handle invalid values
    assert np.all(np.isfinite(result.values) | np.isnan(result.values))


def test_varying_canopy_calculate_vapour_pressure_deficit(
    fixture_core_components, dummy_climate_data_varying_canopy, fixture_pyrealm_config
):
    """Test calculation of VPD with different number of canopy layers."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        calculate_vapour_pressure_deficit,
    )

    lyr_strct = fixture_core_components.layer_structure

    data = dummy_climate_data_varying_canopy
    result = calculate_vapour_pressure_deficit(
        temperature=data["air_temperature"],
        relative_humidity=data["relative_humidity"],
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )
    exp_output = lyr_strct.from_template()
    exp_output[lyr_strct.index_filled_atmosphere] = [
        [0.423372, 0.423372, 0.423372, 0.423372],
        [0.376681, 0.376681, 0.376681, np.nan],
        [0.278148, 0.278148, np.nan, np.nan],
        [0.143955, np.nan, np.nan, np.nan],
        [0.052748, 0.052748, 0.052748, 0.052748],
    ]
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_run_microclimate_varying_canopy(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_core_constants,
    fixture_abiotic_simple_configuration,
    fixture_pyrealm_config,
):
    """Test interpolation of all variables with varying canopy arrays."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        run_simple_microclimate,
    )

    data = dummy_climate_data_varying_canopy
    lyr_strct = fixture_core_components.layer_structure

    result = run_simple_microclimate(
        data=data,
        layer_structure=lyr_strct,
        time_index=0,
        constants=fixture_abiotic_simple_configuration.constants,
        core_constants=fixture_core_constants,
        pyrealm_core_constants=fixture_pyrealm_config.core,
        bounds=fixture_abiotic_simple_configuration.bounds,
    )

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.870794, 29.913863, 29.956931, np.nan],
        [29.035646, 29.357097, np.nan, np.nan],
        [27.769159, np.nan, np.nan, np.nan],
        [25.871986, 27.247991, 28.623995, 30.0],
    ]
    xr.testing.assert_allclose(result["air_temperature"], exp_air_temp)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [21.48431, 21.832134, 22.179959, 22.527783],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(result["soil_temperature"], exp_soil_temp)

    exp_wind = lyr_strct.from_template()
    exp_wind[lyr_strct.index_filled_atmosphere] = [
        [1.0, 1.0, 1.0, 1.0],
        [0.993673, 0.995782, 0.997891, np.nan],
        [0.953925, 0.969284, np.nan, np.nan],
        [0.885976, np.nan, np.nan, np.nan],
        [0.434528, 0.623019, 0.811509, 1.0],
    ]
    xr.testing.assert_allclose(result["wind_speed"], exp_wind)

    exp_pressure = lyr_strct.from_template()
    exp_pressure[lyr_strct.index_filled_atmosphere] = [
        [96, 96, 96, 96],
        [96, 96, 96, np.nan],
        [96, 96, np.nan, np.nan],
        [96, np.nan, np.nan, np.nan],
        [96, 96, 96, 96],
    ]
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_pressure)

    exp_co2 = lyr_strct.from_template()
    exp_co2[lyr_strct.index_filled_atmosphere] = [
        [400, 400, 400, 400],
        [400, 400, 400, np.nan],
        [400, 400, np.nan, np.nan],
        [400, np.nan, np.nan, np.nan],
        [400, 400, 400, 400],
    ]
    xr.testing.assert_allclose(result["atmospheric_co2"], exp_co2)


def test_interpolate_soil_temperature(dummy_climate_data, fixture_core_components):
    """Test soil temperature interpolation."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        interpolate_soil_temperature,
    )

    lyr_strct = fixture_core_components.layer_structure
    data = dummy_climate_data

    surface_temperature = DataArray([22.0, 22.0, 22.0, 22.0], dims="cell_id")
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"],
        layer_structure=lyr_strct,
        upper_bound=50.0,
        lower_bound=-10.0,
    )

    exp_output = lyr_strct.from_template()
    exp_output[lyr_strct.index_all_soil] = np.array([20.505557, 20.0])[:, None]

    xr.testing.assert_allclose(result, exp_output)
