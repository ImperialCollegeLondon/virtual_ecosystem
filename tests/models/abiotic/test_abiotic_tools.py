"""Test abiotic_tools.py."""

import numpy as np

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_calculate_molar_density_air():
    """Test calculate temperature-dependent molar desity of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_molar_density_air,
    )

    result = calculate_molar_density_air(
        temperature=np.array([[25, 25, 25], [20, 20, 20], [18, 18, 18]]),
        atmospheric_pressure=np.full((3, 3), 96),
        standard_mole=CoreConsts.standard_mole,
        standard_pressure=CoreConsts.standard_pressure,
        celsius_to_kelvin=CoreConsts.zero_Celsius,
    )
    np.testing.assert_allclose(
        result,
        np.array(
            [
                [38.749371, 38.749371, 38.749371],
                [39.410285, 39.410285, 39.410285],
                [39.681006, 39.681006, 39.681006],
            ]
        ),
        rtol=1e-5,
        atol=1e-5,
    )


def test_calculate_specific_heat_air():
    """Test calculate specific heat of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_specific_heat_air,
    )

    result = calculate_specific_heat_air(
        temperature=np.array([[25, 25, 25], [20, 20, 20], [18, 18, 18]]),
        molar_heat_capacity_air=CoreConsts.molar_heat_capacity_air,
        specific_heat_equ_factor_1=AbioticConsts.specific_heat_equ_factor_1,
        specific_heat_equ_factor_2=AbioticConsts.specific_heat_equ_factor_2,
    )

    exp_result = np.array(
        [[29.2075, 29.207, 29.207], [29.202, 29.202, 29.202], [29.2, 29.2, 29.2]],
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_latent_heat_vaporisation():
    """Test calculation of latent heat of vaporization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_latent_heat_vaporisation,
    )

    result = calculate_latent_heat_vaporisation(
        temperature=np.array([[25, 25, 25], [20, 20, 20], [18, 18, 18]]),
        celsius_to_kelvin=CoreConsts.zero_Celsius,
        latent_heat_vap_equ_factor_1=AbioticConsts.latent_heat_vap_equ_factor_1,
        latent_heat_vap_equ_factor_2=AbioticConsts.latent_heat_vap_equ_factor_2,
    )
    exp_result = np.array(
        [
            [2442.4475964, 2442.44759649, 2442.44759649],
            [2453.174942646, 2453.174942646, 2453.174942646],
            [2457.589459197, 2457.589459197, 2457.589459197],
        ]
    )

    np.testing.assert_allclose(
        result,
        exp_result,
        rtol=1e-5,
        atol=1e-5,
    )
