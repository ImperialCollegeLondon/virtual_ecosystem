"""Test module for litter.litter_pools.py.

This module tests the functionality of the litter pools module
"""

import numpy as np
import pytest

from virtual_ecosystem.models.litter.constants import LitterConsts


@pytest.fixture
def temp_and_water_factors(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Temperature and water factors for the various litter layers."""
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_environmental_factors,
    )

    environmental_factors = calculate_environmental_factors(
        surface_temp=dummy_litter_data["air_temperature_mean"][surface_layer_index],
        topsoil_temp=dummy_litter_data["soil_temperature_mean"][top_soil_layer_index],
        water_potential=dummy_litter_data["matric_potential"][top_soil_layer_index],
        constants=LitterConsts,
    )

    return environmental_factors


# TODO - Compare the below
# [-297.1410435034187, -4.264765510307134, -79.66618999943468]
# [-10.0, -25.0, -100.0]


@pytest.fixture
def decay_rates(dummy_litter_data, temp_and_water_factors):
    """Decay rates for the various litter pools."""

    return {
        "metabolic_above": np.array([0.00450883464, 0.00225441732, 0.00105206141]),
        "structural_above": np.array([0.000167429, 8.371483356e-5, 3.013734008e-5]),
        "woody": np.array([0.0004831961, 0.0012131307, 0.0007504961]),
        "metabolic_below": np.array([0.00627503, 0.01118989, 0.00141417]),
        "structural_below": np.array([2.08818455e-04, 2.07992589e-04, 8.96385948e-06]),
    }


def test_calculate_environmental_factors(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Test that the calculation of the environmental factors works as expected."""
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_environmental_factors,
    )

    expected_water_factors = [1.0, 0.88496823, 0.71093190]
    expected_temp_above_factors = [0.1878681, 0.1878681, 0.1878681]
    expected_temp_below_factors = [0.2732009, 0.2732009, 0.2732009]

    environmental_factors = calculate_environmental_factors(
        surface_temp=dummy_litter_data["air_temperature_mean"][surface_layer_index],
        topsoil_temp=dummy_litter_data["soil_temperature_mean"][top_soil_layer_index],
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
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_temperature_effect_on_litter_decomp,
    )

    expected_factor = [0.2732009, 0.2732009, 0.2732009]

    actual_factor = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["soil_temperature_mean"][top_soil_layer_index],
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_moisture_effect_on_litter_decomp(top_soil_layer_index):
    """Test that soil moisture effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_moisture_effect_on_litter_decomp,
    )

    water_potentials = np.array([-10.0, -25.0, -100.0, -400.0])

    expected_factor = [1.0, 0.88496823, 0.71093190, 0.53689556]

    actual_factor = calculate_moisture_effect_on_litter_decomp(
        water_potentials,
        water_potential_halt=LitterConsts.litter_decay_water_potential_halt,
        water_potential_opt=LitterConsts.litter_decay_water_potential_optimum,
        moisture_response_curvature=LitterConsts.moisture_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)


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


def test_calculate_change_in_litter_variables(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Test that litter pool update calculation is correct."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_change_in_litter_variables,
    )

    expected_pools = {
        "litter_pool_above_metabolic": [0.29587973, 0.14851276, 0.07041856],
        "litter_pool_above_structural": [0.50055126, 0.25010012, 0.0907076],
        "litter_pool_woody": [4.702103, 11.802315, 7.300997],
        "litter_pool_below_metabolic": [0.38949196, 0.36147436, 0.06906041],
        "litter_pool_below_structural": [0.60011634, 0.30989963, 0.02047753],
        "lignin_above_structural": [0.4996410, 0.1004310, 0.6964345],
        "lignin_woody": [0.49989001, 0.79989045, 0.34998229],
        "lignin_below_structural": [0.499760108, 0.249922519, 0.737107757],
        "litter_C_mineralisation_rate": [0.02987233, 0.02316114, 0.00786517],
    }

    result = calculate_change_in_litter_variables(
        surface_temp=dummy_litter_data["air_temperature_mean"][
            surface_layer_index
        ].to_numpy(),
        topsoil_temp=dummy_litter_data["soil_temperature_mean"][
            top_soil_layer_index
        ].to_numpy(),
        water_potential=dummy_litter_data["matric_potential"][
            top_soil_layer_index
        ].to_numpy(),
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        lignin_above_structural=dummy_litter_data["lignin_above_structural"].to_numpy(),
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        decomposed_excrement=dummy_litter_data["decomposed_excrement"].to_numpy(),
        decomposed_carcasses=dummy_litter_data["decomposed_carcasses"].to_numpy(),
        update_interval=1.0,
        model_constants=LitterConsts,
        core_constants=CoreConsts,
    )

    for name in expected_pools.keys():
        assert np.allclose(result[name], expected_pools[name])


def test_calculate_decay_rates(dummy_litter_data, temp_and_water_factors):
    """Test that calculation of the decay rates works as expected."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_decay_rates

    expected_decay = {
        "metabolic_above": [0.00450883, 0.00225442, 0.00105206],
        "structural_above": [1.67429665e-4, 6.18573593e-4, 1.10869077e-5],
        "woody": [0.0004832, 0.00027069, 0.0015888],
        "metabolic_below": [0.01092804, 0.00894564, 0.00135959],
        "structural_below": [3.63659952e-04, 5.80365659e-04, 2.46907410e-06],
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
        environmental_factors=temp_and_water_factors,
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

    expected_mineralisation = [0.0212182, 0.0274272, 0.00617274]

    actual_mineralisation = calculate_total_C_mineralised(
        decay_rates=decay_rates, model_constants=LitterConsts, core_constants=CoreConsts
    )

    assert np.allclose(actual_mineralisation, expected_mineralisation)


def test_calculate_updated_pools(dummy_litter_data, decay_rates):
    """Test that the function to calculate the pool values after the update works."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_updated_pools

    expected_pools = {
        "above_metabolic": [0.291759466, 0.147025527, 0.070837127],
        "above_structural": [0.501102522, 0.251269950, 0.091377105],
        "woody": [4.7042056, 11.802745, 7.3036710],
        "below_metabolic": [0.38828994, 0.34846022, 0.06801166],
        "below_structural": [0.60054236, 0.31054401, 0.02094207],
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
        update_interval=2.0,
        constants=LitterConsts,
    )

    for name in expected_pools.keys():
        assert np.allclose(actual_pools[name], expected_pools[name])


def test_calculate_lignin_updates(dummy_litter_data):
    """Test that the function to calculate the lignin updates works as expected."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_lignin_updates

    updated_pools = {
        "above_structural": np.array([0.501102522, 0.251269950, 0.091377105]),
        "woody": np.array([4.7042056, 11.802745, 7.3036710]),
        "below_structural": np.array([0.60054236, 0.31054401, 0.02094207]),
    }

    expected_lignin = {
        "above_structural": [-0.000717108, 0.0008580691, -0.007078589],
        "woody": [-0.0002198883, -0.0002191015, -3.5406852e-5],
        "below_structural": [-0.000479566, -0.000154567, -0.025212407],
    }

    actual_lignin = calculate_lignin_updates(
        lignin_above_structural=dummy_litter_data["lignin_above_structural"],
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        updated_pools=updated_pools,
        update_interval=2.0,
        constants=LitterConsts,
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
    from virtual_ecosystem.models.litter.litter_pools import (
        calculate_litter_decay_structural_above,
    )

    expected_decay = [1.67429665e-4, 6.18573593e-4, 1.10869077e-5]

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

    expected_decay = [0.0004832, 0.00027069, 0.0015888]

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

    expected_decay = [0.01092804, 0.00894564, 0.00135959]

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

    expected_decay = [3.63659952e-04, 5.80365659e-04, 2.46907410e-06]

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

    litter_decay = np.array([0.000167429, 8.371483356e-5, 3.013734008e-5])

    expected_mineral = [7.534305e-5, 3.767167e-5, 1.356180e-5]

    actual_mineral = calculate_carbon_mineralised(
        litter_decay, LitterConsts.cue_metabolic
    )

    assert np.allclose(actual_mineral, expected_mineral)


def test_calculate_change_in_lignin(dummy_litter_data):
    """Test that function to calculate lignin changes works properly."""
    from virtual_ecosystem.models.litter.litter_pools import calculate_change_in_lignin

    expected_lignin = [-0.008079787, -0.001949152, 0.0012328767]

    input_carbon = np.array([0.0775, 0.05, 0.0225])
    input_lignin = np.array([0.01, 0.34, 0.75])

    actual_lignin = calculate_change_in_lignin(
        input_carbon=input_carbon,
        updated_pool_carbon=dummy_litter_data["litter_pool_woody"].to_numpy(),
        input_lignin=input_lignin,
        old_pool_lignin=dummy_litter_data["lignin_woody"].to_numpy(),
    )

    assert np.allclose(actual_lignin, expected_lignin)
