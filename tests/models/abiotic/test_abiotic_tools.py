"""Test abiotic_tools.py."""

import numpy as np
import pytest
from pyrealm.constants import CoreConst as PyrealmConst

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_calculate_molar_density_air(
    dummy_climate_data_varying_canopy, fixture_core_components
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
        standard_mole=CoreConsts.standard_mole,
        standard_pressure=CoreConsts.standard_pressure,
        celsius_to_kelvin=CoreConsts.zero_Celsius,
    )

    exp_result = np.array(
        [
            [38.110259, 38.110259, 38.110259, 38.110259],
            [38.129755, 38.129755, 38.129755, 38.129755],
            [38.252699, 38.252699, np.nan, np.nan],
            [38.46472, np.nan, np.nan, np.nan],
            [39.256827, 39.256827, 39.256827, 39.256827],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-5, atol=1e-5)


def test_calculate_air_density(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculate the density of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import calculate_air_density

    consts = CoreConsts()
    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_air_density(
        air_temperature=data["air_temperature"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        specific_gas_constant_dry_air=consts.specific_gas_constant_dry_air,
        celsius_to_kelvin=consts.zero_Celsius,
    )

    exp_result = np.array(
        [
            [1.103205, 1.103205, 1.103205, 1.103205],
            [1.103769, 1.103769, 1.103769, 1.103769],
            [1.107328, 1.107328, np.nan, np.nan],
            [1.113466, np.nan, np.nan, np.nan],
            [1.136395, 1.136395, 1.136395, 1.136395],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-5, atol=1e-5)


def test_calculate_latent_heat_vapourisation(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of latent heat of vapourization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_latent_heat_vapourisation,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere
    constants = AbioticConsts()

    result = calculate_latent_heat_vapourisation(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        celsius_to_kelvin=CoreConsts.zero_Celsius,
        latent_heat_vap_equ_factors=constants.latent_heat_vap_equ_factors,
    )
    exp_result = np.array(
        [
            [2432.140894, 2432.140894, 2432.140894, 2432.140894],
            [2432.454337, 2432.454337, 2432.454337, 2432.454337],
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
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_slope_of_saturated_pressure_curve,
    )

    data = dummy_climate_data_varying_canopy
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere
    const = AbioticConsts()

    result = calculate_slope_of_saturated_pressure_curve(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        saturated_pressure_slope_parameters=const.saturated_pressure_slope_parameters,
    )

    exp_result = np.array(
        [
            [0.243363, 0.243363, 0.243363, 0.243363],
            [0.241487, 0.241487, 0.241487, 0.241487],
            [0.229981, 0.229981, np.nan, np.nan],
            [0.211376, np.nan, np.nan, np.nan],
            [0.153957, 0.153957, 0.153957, 0.153957],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_actual_vapour_pressure(dummy_climate_data, fixture_core_components):
    """Test calculate effective vapour pressure."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_actual_vapour_pressure,
    )

    lyr_str = fixture_core_components.layer_structure

    result = calculate_actual_vapour_pressure(
        air_temperature=dummy_climate_data["air_temperature"],
        relative_humidity=dummy_climate_data["relative_humidity"],
        pyrealm_const=PyrealmConst,
    )

    exp_result = lyr_str.from_template()
    exp_result[lyr_str.index_filled_atmosphere] = np.array(
        [3.810352, 3.790901, 3.668916, 3.461875, 2.503226]
    )[:, None]
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)
