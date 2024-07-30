"""Test module for litter.litter_pools.py.

This module tests the functionality of the litter pools module
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


@pytest.fixture
def decay_rates():
    """Decay rates for the various litter pools."""

    return {
        "metabolic_above": np.array(
            [0.00450883464, 0.00225441732, 0.00105206141, 0.00105206141]
        ),
        "structural_above": np.array(
            [0.000167429, 8.371483356e-5, 3.013734008e-5, 3.013734008e-5]
        ),
        "woody": np.array([0.0004831961, 0.0012131307, 0.0007504961, 0.0007504961]),
        "metabolic_below": np.array([0.00627503, 0.01118989, 0.00141417, 0.00141417]),
        "structural_below": np.array(
            [2.08818455e-04, 2.07992589e-04, 8.96385948e-06, 8.96385948e-06]
        ),
    }


def test_calculate_litter_chemistry_factor():
    """Test that litter chemistry effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_litter_chemistry_factor,
    )

    lignin_proportions = np.array([0.01, 0.1, 0.5, 0.8])

    expected_factor = [0.95122942, 0.60653065, 0.08208499, 0.01831563]

    actual_factor = calculate_litter_chemistry_factor(
        lignin_proportions, LitterConsts.lignin_inhibition_factor
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_decay_rates(dummy_litter_data, fixture_core_components):
    """Test that calculation of the decay rates works as expected."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_decay_rates

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
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=LitterConsts,
    )

    for name in expected_decay.keys():
        assert np.allclose(actual_decay[name], expected_decay[name])


def test_calculate_total_C_mineralised(decay_rates):
    """Test that calculation of total C mineralised is as expected."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_total_C_mineralised,
    )

    expected_mineralisation = [0.0212182, 0.0274272, 0.00617274, 0.00617274]

    actual_mineralisation = calculate_total_C_mineralised(
        decay_rates=decay_rates, model_constants=LitterConsts, core_constants=CoreConsts
    )

    assert np.allclose(actual_mineralisation, expected_mineralisation)


def test_calculate_updated_pools(dummy_litter_data, decay_rates):
    """Test that the function to calculate the pool values after the update works."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_updated_pools

    expected_pools = {
        "above_metabolic": [0.31632696, 0.152963456, 0.0868965658, 0.092546626],
        "above_structural": [0.504536392, 0.251133385, 0.0968690302, 0.09991897],
        "woody": [4.7740336, 11.896573, 7.361499, 7.331499],
        "below_metabolic": [0.40842678, 0.35943734, 0.0673781086, 0.083478172],
        "below_structural": [0.60560552, 0.31876689, 0.0200756214, 0.028575558],
    }

    plant_inputs = {
        "woody": [0.075, 0.099, 0.063, 0.033],
        "above_ground_metabolic": [0.02512875, 0.006499185, 0.0166206948, 0.022270755],
        "above_ground_structural": [0.00487125, 0.001300815, 0.0069293052, 0.009979245],
        "below_ground_metabolic": [0.02097684, 0.01181712, 0.0002064486, 0.016306512],
        "below_ground_structural": [0.00602316, 0.00918288, 9.35514e-5, 0.008593488],
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


def test_calculate_lignin_updates(dummy_litter_data):
    """Test that the function to calculate the lignin updates works as expected."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_lignin_updates

    updated_pools = {
        "above_structural": np.array([0.5047038, 0.25068224, 0.09843778, 0.11163532]),
        "woody": np.array([4.774517, 11.898729, 7.361411, 7.331411]),
        "below_structural": np.array([0.6066315, 0.31860251, 0.02010566, 0.03038382]),
    }
    input_lignin = {
        "woody": np.array([0.233, 0.545, 0.612, 0.378]),
        "above_structural": np.array([0.28329484, 0.23062465, 0.75773447, 0.75393599]),
        "below_structural": np.array([0.7719623, 0.8004025, 0.7490983, 0.9589565]),
    }
    plant_inputs = {
        "woody": np.array([0.075, 0.099, 0.063, 0.033]),
        "above_ground_structural": np.array(
            [0.00487125, 0.001300815, 0.0069293052, 0.009979245]
        ),
        "below_ground_structural": np.array(
            [0.00602316, 0.00918288, 9.35514e-5, 0.008593488]
        ),
    }

    expected_lignin = {
        "above_structural": [-0.00209157, 0.00067782, 0.00406409, 0.00482142],
        "woody": [-0.00419414, -0.00212166, 0.00224223, 0.00012603],
        "below_structural": [2.70027594e-3, 1.58639055e-2, -4.1955995e-6, 5.9099388e-2],
    }

    actual_lignin = calculate_lignin_updates(
        lignin_above_structural=dummy_litter_data["lignin_above_structural"],
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        input_lignin=input_lignin,
        plant_inputs=plant_inputs,
        updated_pools=updated_pools,
    )

    for name in actual_lignin.keys():
        assert np.allclose(actual_lignin[name], expected_lignin[name])


def test_calculate_litter_decay_metabolic_above(
    dummy_litter_data, temp_and_water_factors
):
    """Test calculation of above ground metabolic litter decay."""
    from virtual_ecosystem.models.litter.litter_pools import (
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
    from virtual_ecosystem.models.litter.litter_pools import (
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
    from virtual_ecosystem.models.litter.litter_pools import (
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
    from virtual_ecosystem.models.litter.litter_pools import (
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
    from virtual_ecosystem.models.litter.litter_pools import (
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
    from virtual_ecosystem.models.litter.litter_pools import (
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


def test_calculate_change_in_lignin(dummy_litter_data):
    """Test that function to calculate lignin changes works properly."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_change_in_lignin

    expected_lignin = [-0.008079787, -0.001949152, 0.0012328767, 0.0012328767]

    input_carbon = np.array([0.0775, 0.05, 0.0225, 0.0225])
    input_lignin = np.array([0.01, 0.34, 0.75, 0.75])

    actual_lignin = calculate_change_in_lignin(
        input_carbon=input_carbon,
        updated_pool_carbon=dummy_litter_data["litter_pool_woody"].to_numpy(),
        input_lignin=input_lignin,
        old_pool_lignin=dummy_litter_data["lignin_woody"].to_numpy(),
    )

    assert np.allclose(actual_lignin, expected_lignin)
