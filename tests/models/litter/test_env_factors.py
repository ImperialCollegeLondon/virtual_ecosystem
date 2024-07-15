"""Test module for litter.env_factors.py."""

import numpy as np

from virtual_ecosystem.models.litter.constants import LitterConsts


def test_calculate_temperature_effect_on_litter_decomp(
    dummy_litter_data, fixture_core_components
):
    """Test that temperature effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_temperature_effect_on_litter_decomp,
    )

    expected_factor = [0.2732009, 0.2732009, 0.2732009, 0.2732009]

    actual_factor = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_soil_water_effect_on_litter_decomp():
    """Test that soil moisture effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_soil_water_effect_on_litter_decomp,
    )

    water_potentials = np.array([-10.0, -25.0, -100.0, -400.0])

    expected_factor = [1.0, 0.88496823, 0.71093190, 0.53689556]

    actual_factor = calculate_soil_water_effect_on_litter_decomp(
        water_potentials,
        water_potential_halt=LitterConsts.litter_decay_water_potential_halt,
        water_potential_opt=LitterConsts.litter_decay_water_potential_optimum,
        moisture_response_curvature=LitterConsts.moisture_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)
