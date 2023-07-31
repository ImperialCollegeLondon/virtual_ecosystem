"""Test module for litter.litter_pools.py.

This module tests the functionality of the litter pools module
"""

import numpy as np
import pytest

from virtual_rainforest.models.litter.constants import LitterConsts


@pytest.fixture
def temp_and_water_factors(
    dummy_climate_data, surface_layer_index, top_soil_layer_index
):
    """Temperature and water factors for the various litter layers."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_temperature_effect_on_litter_decomp,
    )

    temp_above = calculate_temperature_effect_on_litter_decomp(
        dummy_climate_data["air_temperature"][surface_layer_index],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    temp_below = calculate_temperature_effect_on_litter_decomp(
        dummy_climate_data["soil_temperature"][top_soil_layer_index],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    # TODO - Add water_below in here when it becomes relevant

    return {"temp_above": temp_above, "temp_below": temp_below}


def test_calculate_temperature_effect_on_litter_decomp(
    dummy_carbon_data, top_soil_layer_index
):
    """Test that temperature effects on decomposition are calculated correctly."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_temperature_effect_on_litter_decomp,
    )

    expected_factor = [0.77760650, 0.88583053, 1.0, 0.41169183]

    actual_factor = calculate_temperature_effect_on_litter_decomp(
        dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_litter_decay_metabolic_above(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of above ground metabolic litter decay."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_metabolic_above,
    )

    expected_decay = [0.00450883464, 0.00225441732, 0.00105206141]

    actual_decay = calculate_litter_decay_metabolic_above(
        temperature_factor=temp_and_water_factors["temp_above"],
        litter_pool_above_metabolic=dummy_litter_data["litter_pool_above_metabolic"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_metabolic_above,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_structural_above(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of above ground metabolic litter decay."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_structural_above,
    )

    expected_decay = [0.000167429, 8.371483356e-5, 3.013734008e-5]

    actual_decay = calculate_litter_decay_structural_above(
        temperature_factor=temp_and_water_factors["temp_above"],
        litter_pool_above_structural=dummy_litter_data["litter_pool_above_structural"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_structural_above,
    )

    assert np.allclose(actual_decay, expected_decay)
