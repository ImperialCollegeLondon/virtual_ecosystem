"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import pytest
import xarray as xr


@pytest.mark.parametrize(
    "measurement_height",
    [
        0.5,  # below typical understorey
        1.5,  # standard met height
        2.0,  # slightly above standard
        10.0,  # mid canopy
    ],
)
def test_varying_canopy_log_interpolation(
    dummy_climate_data, fixture_core_components, measurement_height
):
    """Test log interpolation for wind speed at different measurement heights."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        log_interpolation,
    )

    layer_structure = fixture_core_components.layer_structure
    data = dummy_climate_data

    reference_data = data["wind_speed_ref"].isel(time_index=0).to_numpy()
    layer_heights = data["layer_heights"].to_numpy()
    leaf_area_index_sum = np.nansum(data["leaf_area_index"], axis=0)

    result = log_interpolation(
        reference_data=reference_data,
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=layer_structure,
        layer_heights=layer_heights,
        measurement_height=measurement_height,
        upper_bound=10,
        lower_bound=0.001,
        gradient=-0.1,
    )

    # Top layer should equal reference data regardless of measurement height
    np.testing.assert_allclose(result[0].values, reference_data)

    # Profile should decrease with depth regardless of measurement height
    profile = result[layer_structure.index_filled_atmosphere, 0].values
    assert np.all(np.diff(profile) <= 0)

    # Bounds should be respected at all measurement heights
    assert result.max() <= 20
    assert result.min() >= 0.001

    # No invalid values
    assert np.all(np.isfinite(result.values) | np.isnan(result.values))


@pytest.mark.parametrize(
    "measurement_height",
    [
        0.5,  # below typical understorey
        1.5,  # standard met height
        2.0,  # slightly above standard
        10.0,  # mid canopy
    ],
)
def test_exp_interpolation(
    fixture_core_components,
    dummy_climate_data,
    measurement_height,
):
    """Test exponential temperature interpolation at different measurement heights."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        exp_interpolation,
    )

    layer_structure = fixture_core_components.layer_structure
    data = dummy_climate_data

    reference_data = data["air_temperature_ref"].isel(time_index=0).to_numpy()
    layer_heights = data["layer_heights"].to_numpy()
    leaf_area_index_sum = np.nansum(data["leaf_area_index"], axis=0)

    result = exp_interpolation(
        reference_data=reference_data,
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=layer_structure,
        layer_heights=layer_heights,
        measurement_height=measurement_height,
        upper_bound=80.0,
        lower_bound=-20.0,
        gradient=-1.27,
    )

    # Top layer should equal reference data regardless of measurement height
    np.testing.assert_allclose(result[0].values, reference_data)

    # Profile should decrease with depth regardless of measurement height
    profile = result[layer_structure.index_filled_atmosphere, 0].values
    assert np.all(np.diff(profile) <= 0)

    # Bounds should be respected at all measurement heights
    assert result.max() <= 80
    assert result.min() >= -20

    # No invalid values
    assert np.all(np.isfinite(result.values) | np.isnan(result.values))


def test_varying_canopy_calculate_vapour_pressure_deficit(
    fixture_core_components, dummy_climate_data, fixture_pyrealm_config
):
    """Test calculation of VPD with different number of canopy layers."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        calculate_vapour_pressure_deficit,
    )

    lyr_strct = fixture_core_components.layer_structure

    data = dummy_climate_data
    result = calculate_vapour_pressure_deficit(
        temperature=data["air_temperature"],
        relative_humidity=data["relative_humidity"],
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )
    exp_output = lyr_strct.from_template()
    exp_output[lyr_strct.index_filled_atmosphere] = [
        [0.263742, 0.504452, 0.833445, 1.341337],
        [0.208435, 0.40536, 0.676682, np.nan],
        [0.145237, 0.301385, np.nan, np.nan],
        [0.088784, np.nan, np.nan, np.nan],
        [0.021247, 0.087685, 0.139956, 0.31649],
    ]
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_run_microclimate_varying_canopy(
    dummy_climate_data,
    fixture_core_components,
    fixture_core_constants,
    fixture_abiotic_simple_configuration,
    fixture_pyrealm_config,
):
    """Test interpolation of all variables with varying canopy arrays."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        run_simple_microclimate,
    )

    data = dummy_climate_data
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
        [23.0, 24.0, 25.0, 26.0],
        [22.737281, 23.786638, 24.87785, np.nan],
        [21.039147, 22.270679, np.nan, np.nan],
        [18.463956, np.nan, np.nan, np.nan],
        [14.606371, 18.905246, 23.563744, 26.0],
    ]
    xr.testing.assert_allclose(result["air_temperature"], exp_air_temp)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.131051, 21.591324, 23.142502, 24.505557],
        [22.0, 22.5, 23.0, 24.0],
    ]
    xr.testing.assert_allclose(result["soil_temperature"], exp_soil_temp)

    exp_wind = lyr_strct.from_template()
    exp_wind[lyr_strct.index_filled_atmosphere] = [
        [0.5, 0.8, 1.2, 1.8],
        [0.4871356, 0.7887022, 1.192109, np.nan],
        [0.4063148, 0.71, np.nan, np.nan],
        [0.2681506, np.nan, np.nan, np.nan],
        [0.001, 0.08837985, 0.9927933, 1.8],
    ]
    xr.testing.assert_allclose(result["wind_speed"], exp_wind)

    exp_pressure = lyr_strct.from_template()
    exp_pressure[lyr_strct.index_filled_atmosphere] = [
        [96.0, 95.8, 95.5, 95.2],
        [96.0, 95.8, 95.5, np.nan],
        [96.0, 95.8, np.nan, np.nan],
        [96, np.nan, np.nan, np.nan],
        [96.0, 95.8, 95.5, 95.2],
    ]
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_pressure)

    exp_co2 = lyr_strct.from_template()
    exp_co2[lyr_strct.index_filled_atmosphere] = [
        [400, 401, 402, 403],
        [400, 401, 402, np.nan],
        [400, 401, np.nan, np.nan],
        [400, np.nan, np.nan, np.nan],
        [400, 401, 402, 403],
    ]
    xr.testing.assert_allclose(result["atmospheric_co2"], exp_co2)


def test_interpolate_soil_temperature(dummy_climate_data, fixture_core_components):
    """Test soil temperature interpolation."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        interpolate_soil_temperature,
    )

    lyr_strct = fixture_core_components.layer_structure
    data = dummy_climate_data

    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=data["air_temperature"][11],
        mean_annual_temperature=data["mean_annual_temperature"].isel(time_index=0),
        layer_structure=lyr_strct,
        upper_bound=50.0,
        lower_bound=-10.0,
    )

    exp_output = lyr_strct.from_template()
    exp_output[lyr_strct.index_all_soil] = np.array(
        [[21.115276, 21.615276, 22.241665, 23.494443], [22.0, 22.5, 23.0, 24.0]]
    )

    xr.testing.assert_allclose(result, exp_output)
