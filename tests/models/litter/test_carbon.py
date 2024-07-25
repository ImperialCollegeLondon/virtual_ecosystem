"""Test module for litter.carbon.py.

This module tests the functionality of the litter carbon module
"""

import numpy as np
import pytest

from virtual_ecosystem.models.litter.constants import LitterConsts


@pytest.fixture
def temp_and_water_factors(dummy_litter_data, fixture_core_components):
    """Temperature and water factors for the various litter layers."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_soil_water_effect_on_litter_decomp,
        calculate_temperature_effect_on_litter_decomp,
    )

    # Calculate temperature factor for the above ground litter layers
    temperature_factor_above = calculate_temperature_effect_on_litter_decomp(
        temperature=dummy_litter_data["air_temperature"][
            fixture_core_components.layer_structure.index_surface_scalar
        ],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )
    # Calculate temperature factor for the below ground litter layers
    temperature_factor_below = calculate_temperature_effect_on_litter_decomp(
        temperature=dummy_litter_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )
    # Calculate the water factor (relevant for below ground layers)
    water_factor = calculate_soil_water_effect_on_litter_decomp(
        water_potential=dummy_litter_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        water_potential_halt=LitterConsts.litter_decay_water_potential_halt,
        water_potential_opt=LitterConsts.litter_decay_water_potential_optimum,
        moisture_response_curvature=LitterConsts.moisture_response_curvature,
    )

    return {
        "temp_above": temperature_factor_above,
        "temp_below": temperature_factor_below,
        "water": water_factor,
    }


def test_calculate_decay_rates(dummy_litter_data, fixture_core_components):
    """Test that calculation of the decay rates works as expected."""
    from virtual_ecosystem.models.litter.carbon import calculate_decay_rates

    expected_decay = {
        "metabolic_above": [0.00450883, 0.00225442, 0.00105206, 0.00105206],
        "structural_above": [1.6742967e-4, 6.1857359e-4, 1.1086908e-5, 1.1086908e-5],
        "woody": [0.0004832, 0.00027069, 0.0015888, 0.0015888],
        "metabolic_below": [0.01092804, 0.00894564, 0.00135959, 0.00135959],
        "structural_below": [3.6365995e-04, 5.803657e-04, 2.469074e-06, 2.469074e-06],
    }

    actual_decay = calculate_decay_rates(
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        lignin_above_structural=dummy_litter_data["lignin_above_structural"].to_numpy(),
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        surface_temp=dummy_litter_data["air_temperature"][
            fixture_core_components.layer_structure.index_surface_scalar
        ].to_numpy(),
        topsoil_temp=dummy_litter_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        water_potential=dummy_litter_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        constants=LitterConsts,
    )

    for name in expected_decay.keys():
        assert np.allclose(actual_decay[name], expected_decay[name])


def test_calculate_total_C_mineralised(decay_rates):
    """Test that calculation of total C mineralised is as expected."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.litter.carbon import (
        calculate_total_C_mineralised,
    )

    expected_mineralisation = [0.02987233, 0.02316114, 0.00786517, 0.00786517]

    actual_mineralisation = calculate_total_C_mineralised(
        decay_rates=decay_rates, model_constants=LitterConsts, core_constants=CoreConsts
    )

    assert np.allclose(actual_mineralisation, expected_mineralisation)


def test_calculate_updated_pools(dummy_litter_data, decay_rates, plant_inputs):
    """Test that the function to calculate the pool values after the update works."""
    from virtual_ecosystem.models.litter.carbon import calculate_updated_pools

    expected_pools = {
        "above_metabolic": [0.31632696, 0.15296346, 0.08537701, 0.08087947],
        "above_structural": [0.50453639, 0.25006367, 0.09842669, 0.11162423],
        "woody": [4.77403361, 11.89845863, 7.3598224, 7.3298224],
        "below_metabolic": [0.39814877, 0.36392583, 0.06747269, 0.08179453],
        "below_structural": [0.60626784, 0.31802215, 0.02010319, 0.03038135],
    }

    actual_pools = calculate_updated_pools(
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        decomposed_excrement=dummy_litter_data["decomposed_excrement"].to_numpy(),
        decomposed_carcasses=dummy_litter_data["decomposed_carcasses"].to_numpy(),
        decay_rates=decay_rates,
        plant_inputs=plant_inputs,
        update_interval=2.0,
    )

    for name in expected_pools.keys():
        assert np.allclose(actual_pools[name], expected_pools[name])


def test_calculate_litter_decay_metabolic_above(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of above ground metabolic litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_metabolic_above,
    )

    expected_decay = [0.00450883464, 0.00225441732, 0.00105206141, 0.00105206141]

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
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_structural_above,
    )

    expected_decay = [1.67429665e-4, 6.18573593e-4, 1.10869077e-5, 1.10869077e-5]

    actual_decay = calculate_litter_decay_structural_above(
        temperature_factor=temp_and_water_factors["temp_above"],
        litter_pool_above_structural=dummy_litter_data["litter_pool_above_structural"],
        lignin_proportion=dummy_litter_data["lignin_above_structural"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_structural_above,
        lignin_inhibition_factor=LitterConsts.lignin_inhibition_factor,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_woody(dummy_litter_data, temp_and_water_factors):
    """Test calculation of woody litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_woody,
    )

    expected_decay = [0.0004832, 0.00027069, 0.0015888, 0.0015888]

    actual_decay = calculate_litter_decay_woody(
        temperature_factor=temp_and_water_factors["temp_above"],
        litter_pool_woody=dummy_litter_data["litter_pool_woody"],
        lignin_proportion=dummy_litter_data["lignin_woody"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_woody,
        lignin_inhibition_factor=LitterConsts.lignin_inhibition_factor,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_metabolic_below(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of below ground metabolic litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_metabolic_below,
    )

    expected_decay = [0.01092804, 0.00894564, 0.00135959, 0.00135959]

    actual_decay = calculate_litter_decay_metabolic_below(
        temperature_factor=temp_and_water_factors["temp_below"],
        moisture_factor=temp_and_water_factors["water"],
        litter_pool_below_metabolic=dummy_litter_data["litter_pool_below_metabolic"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_metabolic_below,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_structural_below(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of below ground structural litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_structural_below,
    )

    expected_decay = [3.63659952e-04, 5.80365659e-04, 2.46907410e-06, 2.46907410e-06]

    actual_decay = calculate_litter_decay_structural_below(
        temperature_factor=temp_and_water_factors["temp_below"],
        moisture_factor=temp_and_water_factors["water"],
        litter_pool_below_structural=dummy_litter_data["litter_pool_below_structural"],
        lignin_proportion=dummy_litter_data["lignin_below_structural"],
        litter_decay_coefficient=LitterConsts.litter_decay_constant_structural_below,
        lignin_inhibition_factor=LitterConsts.lignin_inhibition_factor,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_carbon_mineralised():
    """Test that the calculation of litter decay mineralisation works as expected."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_carbon_mineralised,
    )

    litter_decay = np.array(
        [0.000167429, 8.371483356e-5, 3.013734008e-5, 3.013734008e-5]
    )

    expected_mineral = [7.534305e-5, 3.767167e-5, 1.356180e-5, 1.356180e-5]

    actual_mineral = calculate_carbon_mineralised(
        litter_decay, LitterConsts.cue_metabolic
    )

    assert np.allclose(actual_mineral, expected_mineral)
