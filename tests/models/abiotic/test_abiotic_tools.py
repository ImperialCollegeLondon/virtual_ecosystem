"""Test abiotic_tools.py."""

import numpy as np
import pytest

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


def test_calculate_specific_heat_air():
    """Test calculate specific heat of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_specific_heat_air,
    )

    constants = AbioticConsts()
    result = calculate_specific_heat_air(
        temperature=np.array([[25.0] * 3, [20.0] * 3, [18.0] * 3]),
        molar_heat_capacity_air=CoreConsts.molar_heat_capacity_air,
        specific_heat_equ_factors=constants.specific_heat_equ_factors,
    )

    exp_result = np.array([[29.2075] * 3, [29.202] * 3, [29.2] * 3])

    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


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


@pytest.mark.parametrize(
    "air_temperature, effective_vapour_pressure_air, expected_dewpoint_temperature",
    [
        (np.repeat(20.0, 3), np.repeat(2.5, 3), np.repeat(21.304722, 3)),
        (np.repeat(-10.0, 3), np.repeat(0.8, 3), np.repeat(3.32904, 3)),
        (np.repeat(0.0, 3), np.repeat(1.0, 3), np.repeat(6.950734, 3)),
    ],
)
def test_calculate_dewpoint_temperature(
    air_temperature,
    effective_vapour_pressure_air,
    expected_dewpoint_temperature,
):
    """Test calculation of dewpoint temperature."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_dewpoint_temperature,
    )

    result = calculate_dewpoint_temperature(
        air_temperature=air_temperature,
        effective_vapour_pressure_air=effective_vapour_pressure_air,
    )

    np.testing.assert_allclose(result, expected_dewpoint_temperature, atol=1e-2)
