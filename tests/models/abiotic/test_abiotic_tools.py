"""Test abiotic_tools.py."""

import numpy as np
import pytest


def test_calculate_molar_density_air(
    dummy_climate_data_varying_canopy, fixture_core_components, fixture_core_constants
):
    """Test calculate temperature-dependent molar desity of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_molar_density_air,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_molar_density_air(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        standard_mole=fixture_core_constants.standard_mole,
        standard_pressure=fixture_core_constants.standard_pressure,
        celsius_to_kelvin=fixture_core_constants.zero_Celsius,
    )

    exp_result = np.array(
        [
            [38.110259, 38.110259, 38.110259, 38.110259],
            [38.129755, 38.129755, 38.129755, np.nan],
            [38.252699, 38.252699, np.nan, np.nan],
            [38.46472, np.nan, np.nan, np.nan],
            [39.256827, 39.256827, 39.256827, 39.256827],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-5, atol=1e-5)


def test_calculate_air_density(
    dummy_climate_data_varying_canopy, fixture_core_components, fixture_core_constants
):
    """Test calculate the density of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import calculate_air_density

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_air_density(
        air_temperature=data["air_temperature"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        specific_gas_constant_dry_air=fixture_core_constants.specific_gas_constant_dry_air,
        celsius_to_kelvin=fixture_core_constants.zero_Celsius,
    )

    exp_result = np.array(
        [
            [1.103205, 1.103205, 1.103205, 1.103205],
            [1.103769, 1.103769, 1.103769, np.nan],
            [1.107328, 1.107328, np.nan, np.nan],
            [1.113466, np.nan, np.nan, np.nan],
            [1.136395, 1.136395, 1.136395, 1.136395],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-5, atol=1e-5)


def test_calculate_latent_heat_vapourisation(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test calculation of latent heat of vapourization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_latent_heat_vapourisation,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere
    constants = fixture_abiotic_constants

    result = calculate_latent_heat_vapourisation(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        celsius_to_kelvin=fixture_core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=constants.latent_heat_vap_equ_factors,
    )
    exp_result = np.array(
        [
            [2432.140894, 2432.140894, 2432.140894, 2432.140894],
            [2432.454337, 2432.454337, 2432.454337, np.nan],
            [2434.432314, 2434.432314, np.nan, np.nan],
            [2437.849066, np.nan, np.nan, np.nan],
            [2450.677865, 2450.677865, 2450.677865, 2450.677865],
        ]
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize(
    "input_array, expected",
    [
        (np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]), np.array([4.0, 5.0, 6.0])),
        (
            np.array([[1.0, np.nan, 3.0], [4.0, 5.0, np.nan], [np.nan, 8.0, 9.0]]),
            np.array([4.0, 8.0, 9.0]),
        ),
        (
            np.array([[np.nan, 2.0, np.nan], [np.nan, 5.0, np.nan]]),
            np.array([np.nan, 5.0, np.nan]),
        ),
        (np.array([[np.nan, 2.0, 3.0]]), np.array([np.nan, 2.0, 3.0])),
        (
            np.array([[np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan]]),
            np.array([np.nan, np.nan, np.nan]),
        ),
    ],
)
def test_find_last_valid_row(input_array, expected):
    """Test that last true value is selected for each column."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import find_last_valid_row

    result = find_last_valid_row(input_array)
    np.testing.assert_allclose(result, expected)


def test_calculate_slope_of_saturated_pressure_curve(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
):
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_slope_of_saturated_pressure_curve,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_slope_of_saturated_pressure_curve(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        saturated_pressure_slope_parameters=fixture_abiotic_constants.saturated_pressure_slope_parameters,
    )

    exp_result = np.array(
        [
            [0.243363, 0.243363, 0.243363, 0.243363],
            [0.241487, 0.241487, 0.241487, np.nan],
            [0.229981, 0.229981, np.nan, np.nan],
            [0.211376, np.nan, np.nan, np.nan],
            [0.153957, 0.153957, 0.153957, 0.153957],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_actual_vapour_pressure(
    dummy_climate_data_varying_canopy, fixture_core_components, fixture_pyrealm_config
):
    """Test calculate effective vapour pressure."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_actual_vapour_pressure,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_actual_vapour_pressure(
        air_temperature=data["air_temperature"][atm_index],
        relative_humidity=data["relative_humidity"][atm_index],
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    exp_result = np.array(
        [
            [3.810352, 3.810352, 3.810352, 3.810352],
            [3.790901, 3.790901, 3.790901, np.nan],
            [3.668916, 3.668916, np.nan, np.nan],
            [3.461875, np.nan, np.nan, np.nan],
            [2.503226, 2.503226, 2.503226, 2.503226],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


@pytest.mark.parametrize(
    "input_array, input_nan_mask, expected",
    [
        # Test case 1: Some NaNs, one intended
        (
            np.array([[1.0, np.nan], [3.0, np.nan]]),
            np.array([[False, True], [False, False]]),
            np.array([[1.0, np.nan], [3.0, 0.0]]),
        ),
        # Test case 2: All valid
        (
            np.array([[1.0, 2.0], [3.0, 4.0]]),
            np.array([[False, False], [False, False]]),
            np.array([[1.0, 2.0], [3.0, 4.0]]),
        ),
        # Test case 3: All intended NaNs
        (
            np.array([[np.nan, np.nan], [np.nan, np.nan]]),
            np.array([[True, True], [True, True]]),
            np.array([[np.nan, np.nan], [np.nan, np.nan]]),
        ),
        # Test case 4: One unintended NaN
        (
            np.array([[np.nan, 5.0], [6.0, 7.0]]),
            np.array([[False, False], [False, False]]),
            np.array([[0.0, 5.0], [6.0, 7.0]]),
        ),
    ],
)
def test_set_unintended_nan_to_zero(input_array, input_nan_mask, expected):
    """Test 2D arrays: unintended NaNs are zeroed, intended preserved."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        set_unintended_nan_to_zero,
    )

    result = set_unintended_nan_to_zero(input_array, input_nan_mask)
    np.testing.assert_allclose(result, expected, equal_nan=True)


def test_compute_layer_thickness_for_varying_canopy(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test layer thickness for varying canopy."""
    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        compute_layer_thickness_for_varying_canopy,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    exp_result = np.array(
        [
            [2.0, 2.0, 2.0, 31.9],
            [10.0, 10.0, 29.9, np.nan],
            [10.0, 19.9, np.nan, np.nan],
            [9.9, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )

    result = compute_layer_thickness_for_varying_canopy(
        heights=data["layer_heights"][atm_index].to_numpy()
    )

    np.testing.assert_allclose(result, exp_result)


def test_calculate_specific_humidity(
    dummy_climate_data_varying_canopy, fixture_core_components, fixture_pyrealm_config
):
    """Test specific humidity."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_specific_humidity,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_specific_humidity(
        air_temperature=data["air_temperature"][atm_index].to_numpy(),
        relative_humidity=data["relative_humidity"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        molecular_weight_ratio_water_to_dry_air=0.622,
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    exp_result = np.array(
        [
            [0.025064, 0.025064, 0.025064, 0.025064],
            [0.024934, 0.024934, 0.024934, np.nan],
            [0.02412, 0.02412, np.nan, np.nan],
            [0.02274, np.nan, np.nan, np.nan],
            [0.01638, 0.01638, 0.01638, 0.01638],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-4, atol=1e-4)
