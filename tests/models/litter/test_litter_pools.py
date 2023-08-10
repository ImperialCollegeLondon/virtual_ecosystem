"""Test module for litter.litter_pools.py.

This module tests the functionality of the litter pools module
"""

import numpy as np
import pytest
import xarray as xr

from virtual_rainforest.models.litter.constants import LitterConsts


@pytest.fixture
def temp_and_water_factors(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Temperature and water factors for the various litter layers."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_temperature_effect_on_litter_decomp,
    )

    temp_above = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["air_temperature"][surface_layer_index],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    temp_below = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["soil_temperature"][top_soil_layer_index],
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


def test_calculate_moisture_effect_on_litter_decomp(top_soil_layer_index):
    """Test that soil moisture effects on decomposition are calculated correctly."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_moisture_effect_on_litter_decomp,
    )

    water_potentials = [-10.0, -25.0, -100.0, -400.0]

    expected_factor = [1.0, 0.88496823, 0.71093190, 0.53689556]

    actual_factor = calculate_moisture_effect_on_litter_decomp(
        water_potentials,
        water_potential_halt=LitterConsts.litter_decay_water_potential_halt,
        water_potential_opt=LitterConsts.litter_decay_water_potential_optimum,
        moisture_response_curvature=LitterConsts.moisture_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_litter_pool_updates(dummy_litter_data, surface_layer_index):
    """Test that litter pool update calculation is correct."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_pool_updates,
    )

    expected_pools = {
        "litter_pool_above_metabolic": [0.29577179, 0.14802621, 0.06922856],
        "litter_pool_above_structural": [0.50055126, 0.25063497, 0.09068855],
        "litter_pool_woody": [4.702103, 11.801373, 7.301836],
        "litter_C_mineralisation_rate": [0.00238682, 0.00172775, 0.00090278],
    }

    result = calculate_litter_pool_updates(
        surface_temp=dummy_litter_data["air_temperature"][
            surface_layer_index
        ].to_numpy(),
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        update_interval=1.0,
        constants=LitterConsts,
    )

    for name in expected_pools.keys():
        xr.testing.assert_allclose(
            result[name], xr.DataArray(expected_pools[name], dims=["cell_id"])
        )


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


def test_calculate_litter_decay_woody(dummy_litter_data, temp_and_water_factors):
    """Test calculation of woody litter decay."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_woody,
    )

    expected_decay = [0.0004831961, 0.0012131307, 0.0007504961]

    actual_decay = calculate_litter_decay_woody(
        temperature_factor=temp_and_water_factors["temp_above"],
        litter_pool_woody=dummy_litter_data["litter_pool_woody"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_woody,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_carbon_mineralised():
    """Test that the calculation of litter decay mineralisation works as expected."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_carbon_mineralised,
    )

    litter_decay = np.array([0.000167429, 8.371483356e-5, 3.013734008e-5])

    expected_mineral = [7.534305e-5, 3.767167e-5, 1.356180e-5]

    actual_mineral = calculate_carbon_mineralised(
        litter_decay, LitterConsts.cue_metabolic
    )

    assert np.allclose(actual_mineral, expected_mineral)
