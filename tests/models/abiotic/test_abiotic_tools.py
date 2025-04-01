"""Test abiotic_tools.py."""

import numpy as np
import pytest
from pyrealm.constants import CoreConst as pyrealm_const

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_calculate_molar_density_air():
    """Test calculate temperature-dependent molar desity of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_molar_density_air,
    )

    result = calculate_molar_density_air(
        temperature=np.array([[25.0] * 3, [20.0] * 3, [18.0] * 3]),
        atmospheric_pressure=np.full((3, 3), 96.0),
        standard_mole=CoreConsts.standard_mole,
        standard_pressure=CoreConsts.standard_pressure,
        celsius_to_kelvin=CoreConsts.zero_Celsius,
    )
    np.testing.assert_allclose(
        result,
        np.array([[38.749371] * 3, [39.410285] * 3, [39.681006] * 3]),
        rtol=1e-5,
        atol=1e-5,
    )


def test_calculate_air_density(dummy_climate_data):
    """Test calculate the density of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import calculate_air_density

    consts = CoreConsts()
    result = calculate_air_density(
        air_temperature=dummy_climate_data["air_temperature_ref"]
        .isel(time_index=0)
        .to_numpy(),
        atmospheric_pressure=dummy_climate_data["atmospheric_pressure_ref"]
        .isel(time_index=0)
        .to_numpy(),
        specific_gas_constant_dry_air=consts.specific_gas_constant_dry_air,
        celsius_to_kelvin=consts.zero_Celsius,
    )
    np.testing.assert_allclose(
        result,
        np.repeat(1.103205, 4),
        rtol=1e-5,
        atol=1e-5,
    )


def test_calculate_latent_heat_vapourisation():
    """Test calculation of latent heat of vapourization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_latent_heat_vapourisation,
    )

    constants = AbioticConsts()
    result = calculate_latent_heat_vapourisation(
        temperature=np.array([[25.0] * 3, [20.0] * 3, [18.0] * 3]),
        celsius_to_kelvin=CoreConsts.zero_Celsius,
        latent_heat_vap_equ_factors=constants.latent_heat_vap_equ_factors,
    )
    exp_result = np.array([[2442.447596] * 3, [2453.174942] * 3, [2457.589459] * 3])

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


def test_calculate_slope_of_saturated_pressure_curve():
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_slope_of_saturated_pressure_curve,
    )

    const = AbioticConsts()
    result = calculate_slope_of_saturated_pressure_curve(
        temperature=np.full((4, 3), 20.0),
        saturated_pressure_slope_parameters=const.saturated_pressure_slope_parameters,
    )
    exp_result = np.full((4, 3), 0.14474)
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_actual_vapour_pressure(dummy_climate_data, fixture_core_components):
    """Calculate effective vapour pressure, [kPa]."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_actual_vapour_pressure,
    )

    lyr_str = fixture_core_components.layer_structure

    result = calculate_actual_vapour_pressure(
        air_temperature=dummy_climate_data["air_temperature"],
        relative_humidity=dummy_climate_data["relative_humidity"],
        pyrealm_const=pyrealm_const,
    )

    exp_result = lyr_str.from_template()
    exp_result[lyr_str.index_filled_atmosphere] = np.array(
        [3.810352, 3.790901, 3.668916, 3.461875, 2.503226]
    )[:, None]
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)
