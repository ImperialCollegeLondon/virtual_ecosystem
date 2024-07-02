"""Test module for litter.env_factors.py."""

import numpy as np

from virtual_ecosystem.models.litter.constants import LitterConsts


def test_calculate_environmental_factors(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Test that the calculation of the environmental factors works as expected."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_environmental_factors,
    )

    expected_water_factors = [1.0, 0.88496823, 0.71093190, 0.71093190]
    expected_temp_above_factors = [0.1878681, 0.1878681, 0.1878681, 0.1878681]
    expected_temp_below_factors = [0.2732009, 0.2732009, 0.2732009, 0.2732009]

    environmental_factors = calculate_environmental_factors(
        surface_temp=dummy_litter_data["air_temperature"][surface_layer_index],
        topsoil_temp=dummy_litter_data["soil_temperature"][top_soil_layer_index],
        water_potential=dummy_litter_data["matric_potential"][top_soil_layer_index],
        constants=LitterConsts,
    )

    assert np.allclose(environmental_factors["water"], expected_water_factors)
    assert np.allclose(environmental_factors["temp_above"], expected_temp_above_factors)
    assert np.allclose(environmental_factors["temp_below"], expected_temp_below_factors)


def test_calculate_temperature_effect_on_litter_decomp(
    dummy_litter_data, top_soil_layer_index
):
    """Test that temperature effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_temperature_effect_on_litter_decomp,
    )

    expected_factor = [0.2732009, 0.2732009, 0.2732009, 0.2732009]

    actual_factor = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["soil_temperature"][top_soil_layer_index],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_soil_water_effect_on_litter_decomp(top_soil_layer_index):
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
