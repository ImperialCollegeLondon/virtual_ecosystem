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
    from virtual_rainforest.models.litter.litter_model import (
        convert_soil_moisture_to_water_potential,
    )
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_moisture_effect_on_litter_decomp,
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

    water_potentials = convert_soil_moisture_to_water_potential(
        dummy_litter_data["soil_moisture"][top_soil_layer_index],
        air_entry_water_potential=LitterConsts.air_entry_water_potential,
        water_retention_curvature=LitterConsts.water_retention_curvature,
        saturated_water_content=LitterConsts.saturated_water_content,
    )

    water_below = calculate_moisture_effect_on_litter_decomp(
        water_potentials,
        water_potential_halt=LitterConsts.litter_decay_water_potential_halt,
        water_potential_opt=LitterConsts.litter_decay_water_potential_optimum,
        moisture_response_curvature=LitterConsts.moisture_response_curvature,
    )

    return {
        "temp_above": temp_above,
        "temp_below": temp_below,
        "water_below": water_below,
    }


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


def test_calculate_litter_pool_updates(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Test that litter pool update calculation is correct."""
    from virtual_rainforest.models.litter.litter_model import (
        convert_soil_moisture_to_water_potential,
    )
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_pool_updates,
    )

    expected_pools = {
        "litter_pool_above_metabolic": [0.295773, 0.148027, 0.069261],
        "litter_pool_above_structural": [0.50055126, 0.25063497, 0.09068855],
        "litter_pool_woody": [4.702103, 11.801373, 7.301836],
        "litter_pool_below_metabolic": [0.394145, 0.35923, 0.069006],
        "litter_pool_below_structural": [0.600271, 0.310272, 0.020471],
        "litter_C_mineralisation_rate": [0.0212182, 0.0274272, 0.00617274],
    }

    # Calculate water potential
    water_potential = convert_soil_moisture_to_water_potential(
        dummy_litter_data["soil_moisture"][top_soil_layer_index].to_numpy(),
        air_entry_water_potential=LitterConsts.air_entry_water_potential,
        water_retention_curvature=LitterConsts.water_retention_curvature,
        saturated_water_content=LitterConsts.saturated_water_content,
    )

    result = calculate_litter_pool_updates(
        surface_temp=dummy_litter_data["air_temperature"][
            surface_layer_index
        ].to_numpy(),
        topsoil_temp=dummy_litter_data["soil_temperature"][
            top_soil_layer_index
        ].to_numpy(),
        water_potential=water_potential,
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        excess_excrement=dummy_litter_data["excess_excrement"].to_numpy(),
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
    """Test calculation of above ground structural litter decay."""
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


def test_calculate_litter_decay_metabolic_below(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of below ground metabolic litter decay."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_metabolic_below,
    )

    expected_decay = [0.00627503, 0.01118989, 0.00141417]

    actual_decay = calculate_litter_decay_metabolic_below(
        temperature_factor=temp_and_water_factors["temp_below"],
        moisture_factor=temp_and_water_factors["water_below"],
        litter_pool_below_metabolic=dummy_litter_data["litter_pool_below_metabolic"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_metabolic_below,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_structural_below(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of below ground structural litter decay."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_structural_below,
    )

    expected_decay = [2.08818455e-04, 2.07992589e-04, 8.96385948e-06]

    actual_decay = calculate_litter_decay_structural_below(
        temperature_factor=temp_and_water_factors["temp_below"],
        moisture_factor=temp_and_water_factors["water_below"],
        litter_pool_below_structural=dummy_litter_data["litter_pool_below_structural"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_structural_below,
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
