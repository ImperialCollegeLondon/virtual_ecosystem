"""Test module for litter.carbon.py.

This module tests the functionality of the litter carbon module
"""

import numpy as np
import pytest


@pytest.fixture
def temp_and_water_factors(
    dummy_litter_data, fixture_core_components, fixture_litter_constants
):
    """Temperature and water factors for the various litter layers."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_environmental_factors,
    )

    return calculate_environmental_factors(
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=fixture_litter_constants,
    )


def test_calculate_post_consumption_pools(dummy_litter_data):
    """Test that the calculation of post consumption pool sizes is correct."""
    from virtual_ecosystem.models.litter.carbon import calculate_post_consumption_pools

    expected_pools = {
        "above_metabolic": [0.3, 0.15, 0.07, 0.07],
        "above_structural": [0.5, 0.25, 0.09, 0.09],
        "woody": [4.7, 11.8, 7.3, 7.3],
        "below_metabolic": [0.4, 0.37, 0.07, 0.07],
        "below_structural": [0.6, 0.31, 0.02, 0.02],
    }

    actual_pools = calculate_post_consumption_pools(
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic_cnp"]
        .loc[:, "C"]
        .to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural_cnp"]
        .loc[:, "C"]
        .to_numpy(),
        woody=dummy_litter_data["litter_pool_woody_cnp"].loc[:, "C"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic_cnp"]
        .loc[:, "C"]
        .to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural_cnp"]
        .loc[:, "C"]
        .to_numpy(),
        consumption_above_metabolic=dummy_litter_data[
            "litter_consumption_above_metabolic"
        ].to_numpy(),
        consumption_above_structural=dummy_litter_data[
            "litter_consumption_above_structural"
        ].to_numpy(),
        consumption_woody=dummy_litter_data["litter_consumption_woody"].to_numpy(),
        consumption_below_metabolic=dummy_litter_data[
            "litter_consumption_below_metabolic"
        ].to_numpy(),
        consumption_below_structural=dummy_litter_data[
            "litter_consumption_below_structural"
        ].to_numpy(),
    )

    assert set(expected_pools.keys()) == set(actual_pools.keys())

    for key in actual_pools.keys():
        assert np.allclose(actual_pools[key], expected_pools[key])


def test_calculate_decay_rates(
    dummy_litter_data, fixture_core_components, fixture_litter_constants
):
    """Test that calculation of the decay rates works as expected."""
    from virtual_ecosystem.models.litter.carbon import calculate_decay_rates

    expected_decay = {
        "metabolic_above": [0.0150294488, 0.0150294488, 0.0150294488, 0.0150294488],
        "structural_above": [0.000334859, 0.002474294, 0.000123188, 0.000123188],
        "woody": [0.000102808, 2.293950e-5, 0.000217644, 0.000217644],
        "metabolic_below": [0.02281971, 0.02019472, 0.01622326, 0.01622326],
        "structural_below": [
            0.00050625835,
            0.00156375238,
            0.00010311745,
            0.00010311745,
        ],
    }

    actual_decay = calculate_decay_rates(
        lignin_above_structural=dummy_litter_data["lignin_above_structural"].to_numpy(),
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=fixture_litter_constants,
    )

    assert set(expected_decay.keys()) == set(actual_decay.keys())

    for name in expected_decay.keys():
        assert np.allclose(actual_decay[name], expected_decay[name])


def test_calculate_total_C_mineralised(
    litter_losses, fixture_litter_constants, fixture_core_constants
):
    """Test that calculation of total C mineralised is as expected."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_total_C_mineralised,
    )

    expected_mineralisation = [0.0266645, 0.02019299, 0.00756695, 0.00762047]

    actual_mineralisation = calculate_total_C_mineralised(
        litter_losses=litter_losses,
        model_constants=fixture_litter_constants,
        core_constants=fixture_core_constants,
        update_interval=2.0,
    )

    assert np.allclose(actual_mineralisation, expected_mineralisation)


def test_calculate_updated_pools(decay_rates, post_consumption_pools, litter_inputs):
    """Test that the function to calculate the pool values after the update works."""
    from virtual_ecosystem.models.litter.carbon import calculate_updated_pools

    expected_pools = {
        "above_metabolic": [0.312747774, 0.147333779, 0.078843190, 0.072379485],
        "above_structural": [0.50473556, 0.24936209, 0.10274537, 0.11665499],
        "woody": [4.774026, 11.89845637, 7.35980938, 7.32981591],
        "below_metabolic": [0.39768414, 0.36316585, 0.06791351, 0.07781341],
        "below_structural": [0.61050051, 0.32204064, 0.02014513, 0.03468225],
    }

    actual_pools = calculate_updated_pools(
        post_consumption_pools=post_consumption_pools,
        decay_rates=decay_rates,
        litter_inputs=litter_inputs,
        update_interval=2.0,
    )

    assert set(expected_pools.keys()) == set(actual_pools.keys())

    for name in expected_pools.keys():
        assert np.allclose(actual_pools[name], expected_pools[name])


def test_calculate_final_pool_size(post_consumption_pools, litter_inputs, decay_rates):
    """Test that the function to find pool size after input and decay works."""
    from virtual_ecosystem.models.litter.carbon import calculate_final_pool_size

    expected_pool_size = [0.312747774, 0.147333779, 0.078843190, 0.072379485]

    actual_pool_size = calculate_final_pool_size(
        input_rate=litter_inputs.above_metabolic,
        decay_rate=decay_rates["metabolic_above"],
        initial_pool=post_consumption_pools["above_metabolic"],
        update_interval=2.0,
    )

    assert np.allclose(actual_pool_size, expected_pool_size)


def test_calculate_litter_decay_metabolic_above(
    temp_and_water_factors, fixture_litter_constants
):
    """Test calculation of above ground metabolic litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_metabolic_above,
    )

    expected_decay = [0.0150294488, 0.0150294488, 0.0150294488, 0.0150294488]

    actual_decay = calculate_litter_decay_metabolic_above(
        temperature_factor=temp_and_water_factors["temp_above"],
        litter_decay_coefficient=fixture_litter_constants.litter_decay_constant_metabolic_above,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_structural_above(
    dummy_litter_data, fixture_litter_constants, temp_and_water_factors
):
    """Test calculation of above ground structural litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_structural_above,
    )

    expected_decay = [0.000334859, 0.002474294, 0.000123188, 0.000123188]

    actual_decay = calculate_litter_decay_structural_above(
        temperature_factor=temp_and_water_factors["temp_above"],
        lignin_proportion=dummy_litter_data["lignin_above_structural"],
        litter_decay_coefficient=fixture_litter_constants.litter_decay_constant_structural_above,
        lignin_inhibition_factor=fixture_litter_constants.lignin_inhibition_factor,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_woody(
    dummy_litter_data, fixture_litter_constants, temp_and_water_factors
):
    """Test calculation of woody litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_woody,
    )

    expected_decay = [0.000102808, 2.293950e-5, 0.000217644, 0.000217644]

    actual_decay = calculate_litter_decay_woody(
        temperature_factor=temp_and_water_factors["temp_above"],
        lignin_proportion=dummy_litter_data["lignin_woody"],
        litter_decay_coefficient=fixture_litter_constants.litter_decay_constant_woody,
        lignin_inhibition_factor=fixture_litter_constants.lignin_inhibition_factor,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_metabolic_below(
    fixture_litter_constants, temp_and_water_factors
):
    """Test calculation of below ground metabolic litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_metabolic_below,
    )

    expected_decay = [0.02281971, 0.02019472, 0.01622326, 0.01622326]

    actual_decay = calculate_litter_decay_metabolic_below(
        temperature_factor=temp_and_water_factors["temp_below"],
        moisture_factor=temp_and_water_factors["water"],
        litter_decay_coefficient=fixture_litter_constants.litter_decay_constant_metabolic_below,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_litter_decay_structural_below(
    dummy_litter_data, fixture_litter_constants, temp_and_water_factors
):
    """Test calculation of below ground structural litter decay."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_litter_decay_structural_below,
    )

    expected_decay = [0.00050625835, 0.00156375238, 0.00010311745, 0.00010311745]

    actual_decay = calculate_litter_decay_structural_below(
        temperature_factor=temp_and_water_factors["temp_below"],
        moisture_factor=temp_and_water_factors["water"],
        lignin_proportion=dummy_litter_data["lignin_below_structural"],
        litter_decay_coefficient=fixture_litter_constants.litter_decay_constant_structural_below,
        lignin_inhibition_factor=fixture_litter_constants.lignin_inhibition_factor,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_carbon_mineralised(fixture_litter_constants):
    """Test that the calculation of litter decay mineralisation works as expected."""
    from virtual_ecosystem.models.litter.carbon import (
        calculate_carbon_mineralised,
    )

    carbon_loss = np.array(
        [0.000167429, 8.371483356e-5, 3.013734008e-5, 3.013734008e-5]
    )

    expected_mineral = [7.534305e-5, 3.767167e-5, 1.356180e-5, 1.356180e-5]

    actual_mineral = calculate_carbon_mineralised(
        carbon_loss=carbon_loss,
        carbon_use_efficiency=fixture_litter_constants.cue_metabolic,
    )

    assert np.allclose(actual_mineral, expected_mineral)
