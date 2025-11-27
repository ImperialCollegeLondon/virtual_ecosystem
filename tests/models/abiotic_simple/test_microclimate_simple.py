"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import xarray as xr
from xarray import DataArray


def test_varying_canopy_log_interpolation(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
        log_interpolation,
    )

    data = dummy_climate_data_varying_canopy
    lyr_strct = fixture_core_components.layer_structure
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        reference_data=data["air_temperature_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=lyr_strct,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.793326, 29.844995, 29.896663, np.nan],
        [28.494893, 28.87117, np.nan, np.nan],
        [26.275206, np.nan, np.nan, np.nan],
        [11.527927, 16.145945, 20.763963, 25.381982],
    ]
    xr.testing.assert_allclose(result, exp_air_temp)


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
        [0.405282, 0.405282, 0.405282, np.nan],
        [0.297993, 0.297993, np.nan, np.nan],
        [0.138345, np.nan, np.nan, np.nan],
        [0.0, 0.0, 0.0, 0.0],
    ]
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_run_microclimate_varying_canopy(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_core_constants,
    fixture_abiotic_simple_configuration,
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
        bounds=fixture_abiotic_simple_configuration.bounds,
    )

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.892867, 29.91965, 29.946434, np.nan],
        [29.219802, 29.414851, np.nan, np.nan],
        [28.069188, np.nan, np.nan, np.nan],
        [20.42468, 22.81851, 25.21234, 27.60617],
    ]
    xr.testing.assert_allclose(result["air_temperature"], exp_air_temp)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.10735, 20.712458, 21.317566, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(result["soil_temperature"], exp_soil_temp)

    exp_wind = lyr_strct.from_template()
    exp_wind[lyr_strct.index_filled_atmosphere] = [
        [1, 1, 1, 1],
        [0.991564, 0.993673, 0.995782, np.nan],
        [0.938567, 0.953925, np.nan, np.nan],
        [0.847968, np.nan, np.nan, np.nan],
        [0.246038, 0.434528, 0.623019, 0.811509],
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
