"""Test module for litter.litter_pools.py.

This module tests the functionality of the litter pools module
"""

import numpy as np
import pytest

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
        calculate_environmental_factors,
    )

    water_potentials = convert_soil_moisture_to_water_potential(
        dummy_litter_data["soil_moisture"][top_soil_layer_index],
        air_entry_water_potential=LitterConsts.air_entry_water_potential,
        water_retention_curvature=LitterConsts.water_retention_curvature,
        saturated_water_content=LitterConsts.saturated_water_content,
    )

    environmental_factors = calculate_environmental_factors(
        surface_temp=dummy_litter_data["air_temperature"][surface_layer_index],
        topsoil_temp=dummy_litter_data["soil_temperature"][top_soil_layer_index],
        water_potential=water_potentials,
        constants=LitterConsts,
    )

    return environmental_factors


def test_calculate_environmental_factors(
    dummy_litter_data, surface_layer_index, top_soil_layer_index
):
    """Test that the calculation of the environmental factors works as expected."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_environmental_factors,
    )

    # TODO - hardcoding this in, but eventually this should be added to the data object.
    water_potentials = [-10.0, -25.0, -100.0]

    expected_water_factors = [1.0, 0.88496823, 0.71093190]
    expected_temp_above_factors = [0.1878681, 0.1878681, 0.1878681]
    expected_temp_below_factors = [0.2732009, 0.2732009, 0.2732009]

    environmental_factors = calculate_environmental_factors(
        surface_temp=dummy_litter_data["air_temperature"][surface_layer_index],
        topsoil_temp=dummy_litter_data["soil_temperature"][top_soil_layer_index],
        water_potential=water_potentials,
        constants=LitterConsts,
    )

    assert np.allclose(environmental_factors["water"], expected_water_factors)
    assert np.allclose(environmental_factors["temp_above"], expected_temp_above_factors)
    assert np.allclose(environmental_factors["temp_below"], expected_temp_below_factors)


def test_calculate_temperature_effect_on_litter_decomp(
    dummy_litter_data, top_soil_layer_index
):
    """Test that temperature effects on decomposition are calculated correctly."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_temperature_effect_on_litter_decomp,
    )

    expected_factor = [0.2732009, 0.2732009, 0.2732009]

    actual_factor = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["soil_temperature"][top_soil_layer_index],
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


def test_calculate_litter_chemistry_factor():
    """Test that litter chemistry effects on decomposition are calculated correctly."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_chemistry_factor,
    )

    lignin_proportions = np.array([0.01, 0.1, 0.5, 0.8])

    expected_factor = [0.95122942, 0.60653065, 0.08208499, 0.01831563]

    actual_factor = calculate_litter_chemistry_factor(
        lignin_proportions, LitterConsts.lignin_inhibition_factor
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
        "litter_pool_above_metabolic": [0.295826, 0.14827, 0.06984],
        "litter_pool_above_structural": [0.500605, 0.250343, 0.091286],
        "litter_pool_woody": [4.702103, 11.802315, 7.300997],
        "litter_pool_below_metabolic": [0.394145, 0.35923, 0.069006],
        "litter_pool_below_structural": [0.60027118, 0.30975403, 0.02047743],
        "litter_C_mineralisation_rate": [0.0212182, 0.02746286, 0.00796359],
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
        lignin_above_structural=dummy_litter_data["lignin_above_structural"].to_numpy(),
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        decomposed_excrement=dummy_litter_data["decomposed_excrement"].to_numpy(),
        decomposed_carcasses=dummy_litter_data["decomposed_carcasses"].to_numpy(),
        update_interval=1.0,
        constants=LitterConsts,
    )

    for name in expected_pools.keys():
        np.allclose(result[name], expected_pools[name])


def test_calculate_decay_rates(dummy_litter_data, temp_and_water_factors):
    """Test that calculation of the decay rates works as expected."""
    from virtual_rainforest.models.litter.litter_pools import calculate_decay_rates

    expected_decay = {
        "metabolic_above": [0.00450883, 0.00225442, 0.00105206],
        "structural_above": [1.67429665e-4, 6.18573593e-4, 1.10869077e-5],
        "woody": [0.0004832, 0.00027069, 0.0015888],
        "metabolic_below": [0.00627503, 0.01118989, 0.00141417],
        "structural_below": [2.08818451e-4, 7.25965456e-4, 2.56818870e-6],
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

    for name in actual_decay.keys():
        np.allclose(actual_decay[name], expected_decay[name])


def test_calculate_total_C_mineralised():
    """Test that calculation of total C mineralised is as expected."""
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_total_C_mineralised,
    )

    expected_mineralisation = [0.0212182, 0.0274272, 0.00617274]

    decay_rates = {
        "metabolic_above": np.array([0.00450883464, 0.00225441732, 0.00105206141]),
        "structural_above": np.array([0.000167429, 8.371483356e-5, 3.013734008e-5]),
        "woody": np.array([0.0004831961, 0.0012131307, 0.0007504961]),
        "metabolic_below": np.array([0.00627503, 0.01118989, 0.00141417]),
        "structural_below": np.array([2.08818455e-04, 2.07992589e-04, 8.96385948e-06]),
    }

    actual_mineralisation = calculate_total_C_mineralised(
        decay_rates=decay_rates,
        constants=LitterConsts,
    )

    assert np.allclose(actual_mineralisation, expected_mineralisation)


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
    from virtual_rainforest.models.litter.litter_pools import (
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
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_metabolic_below,
    )

    expected_decay = [0.00627503, 0.01118989, 0.00141417]

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
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_litter_decay_structural_below,
    )

    expected_decay = [2.08818451e-04, 7.25965456e-04, 2.56818870e-06]

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
    from virtual_rainforest.models.litter.litter_pools import (
        calculate_carbon_mineralised,
    )

    litter_decay = np.array([0.000167429, 8.371483356e-5, 3.013734008e-5])

    expected_mineral = [7.534305e-5, 3.767167e-5, 1.356180e-5]

    actual_mineral = calculate_carbon_mineralised(
        litter_decay, LitterConsts.cue_metabolic
    )

    assert np.allclose(actual_mineral, expected_mineral)


@pytest.mark.parametrize(
    "metabolic_fraction,expected_metabolic,expected_structural",
    [
        (
            0.2,
            [2.1428e-5, 9.7142e-5, 2.31428e-04, 4.85714e-04],
            [8.5712e-5, 0.000388568, 0.000925712, 0.001942856],
        ),
        (
            0.5,
            [5.357e-5, 0.000242855, 0.00057857, 0.001214285],
            [5.357e-5, 0.000242855, 0.00057857, 0.001214285],
        ),
        (
            0.9,
            [9.6426e-5, 0.000437139, 0.001041426, 0.002185713],
            [1.0714e-5, 4.8571e-5, 1.15714e-4, 2.42857e-4],
        ),
    ],
)
def test_calculate_carcass_split(
    metabolic_fraction, expected_metabolic, expected_structural
):
    """Test that the carcass split function works as intended."""
    from virtual_rainforest.models.litter.litter_pools import calculate_carcass_split

    decomposed_carcass_C = np.array([1.0714e-4, 4.8571e-4, 1.15714e-3, 2.42857e-3])

    actual_metabolic, actual_structural = calculate_carcass_split(
        decomposed_carcass_C, metabolic_fraction
    )

    assert np.allclose(actual_metabolic, expected_metabolic)
    assert np.allclose(actual_structural, expected_structural)
