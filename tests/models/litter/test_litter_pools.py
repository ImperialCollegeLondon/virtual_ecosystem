"""Test module for litter.litter_pools.py.

This module tests the functionality of the litter pools module
"""

import numpy as np

from virtual_rainforest.models.litter.constants import LitterConsts


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
