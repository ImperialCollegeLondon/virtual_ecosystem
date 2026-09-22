"""Test module for litter.chemistry.py.

This module tests the functionality of the litter chemistry module
"""

import numpy as np


def test_calculate_litter_chemistry_factor(fixture_litter_constants):
    """Test that litter chemistry effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_litter_chemistry_factor,
    )

    lignin_proportions = np.array([0.01, 0.1, 0.5, 0.8])

    expected_factor = [0.95122942, 0.60653065, 0.08208499, 0.01831563]

    actual_factor = calculate_litter_chemistry_factor(
        lignin_proportions, fixture_litter_constants.lignin_inhibition_factor
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_new_pool_chemistries(
    litter_inputs,
    litter_chemistry,
    litter_losses,
    post_consumption_pools,
    input_chemistries,
):
    """Test that function to calculate updated pool chemistries works correctly."""

    expected_chemistries = {
        "lignin_above_structural": [0.4976432, 0.10184581, 0.6793591, 0.668817],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974109, 0.26255952, 0.73335986, 0.71623308],
        "above_metabolic_nitrogen": [0.04164068, 0.01683533, 0.00720338, 0.00710534],
        "above_structural_nitrogen": [0.01340754, 0.0057693, 0.00208167, 0.00228176],
        "woody_nitrogen": [
            0.08590272675794186,
            0.18811515700056716,
            0.15512843175215565,
            0.12406449399964693,
        ],
        "below_metabolic_nitrogen": [0.03613763, 0.0315315, 0.00445357, 0.00593552],
        "below_structural_nitrogen": [0.0119763, 0.00566867, 0.00029149, 0.00047728],
        "above_metabolic_phosphorus": [0.00513782, 0.00212742, 0.00071441, 0.00072071],
        "above_structural_phosphorus": [0.00148339, 0.00052657, 0.00022537, 0.00023009],
        "woody_phosphorus": [
            0.00854665833297424,
            0.015605057949575844,
            0.008679346482530033,
            0.012216757912695322,
        ],
        "below_metabolic_phosphorus": [0.00125366, 0.00089397, 0.00021798, 0.00021479],
        "below_structural_phosphorus": [
            1.09364254e-03,
            5.30437838e-04,
            2.94129841e-05,
            4.95457779e-05,
        ],
    }

    actual_chemistries = litter_chemistry.calculate_new_pool_chemistries(
        litter_inputs=litter_inputs,
        litter_losses=litter_losses,
        input_chemistries=input_chemistries,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(actual_chemistries.keys()) == set(expected_chemistries.keys())

    for name in actual_chemistries.keys():
        assert np.allclose(actual_chemistries[name], expected_chemistries[name])


def test_calculate_new_lignin_proportions(
    input_chemistries,
    post_consumption_pools,
    litter_chemistry,
    litter_losses,
    litter_inputs,
):
    """Test that the function to calculate the lignin updates works as expected."""

    expected_lignin = {
        "lignin_above_structural": [0.4976432, 0.10184581, 0.6793591, 0.668817],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974109, 0.26255952, 0.73335986, 0.71623308],
    }

    actual_lignin = litter_chemistry.calculate_new_lignin_proportions(
        litter_inputs=litter_inputs,
        input_chemistries=input_chemistries,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(actual_lignin.keys()) == set(expected_lignin.keys())

    for name in actual_lignin.keys():
        assert np.allclose(actual_lignin[name], expected_lignin[name])


def test_calculate_updated_pool_lignin_proportion(
    dummy_litter_data,
    post_consumption_pools,
    litter_inputs,
    litter_losses,
    input_chemistries,
):
    """Test that function to calculate chemistry changes works properly."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_updated_pool_lignin_proportion,
    )

    expected_lignin = [0.4976432, 0.10184581, 0.6793591, 0.668817]

    actual_lignin = calculate_updated_pool_lignin_proportion(
        initial_carbon=post_consumption_pools["above_structural"]
        .sel(element="C")
        .to_numpy(),
        input_carbon_rate=litter_inputs.above_structural,
        carbon_loss=litter_losses.above_structural_carbon,
        initial_lignin_proportion=dummy_litter_data[
            "lignin_above_structural"
        ].to_numpy(),
        input_lignin_proportion=input_chemistries.above_structural_lignin,
        lignin_loss=litter_losses.above_structural_lignin,
        update_interval=2.0,
    )

    assert np.allclose(actual_lignin, expected_lignin)


def test_calculate_updated_nutrient_pools(
    input_chemistries,
    litter_losses,
    post_consumption_pools,
):
    """Test that calculation of C:N ratio updates works properly."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_updated_nutrient_pools,
    )

    expected_pools = {
        "above_metabolic_nitrogen": [0.04164068, 0.01683533, 0.00720338, 0.00710534],
        "above_structural_nitrogen": [0.01340754, 0.0057693, 0.00208167, 0.00228176],
        "woody_nitrogen": [
            0.08590272675794186,
            0.18811515700056716,
            0.15512843175215565,
            0.12406449399964693,
        ],
        "below_metabolic_nitrogen": [0.03613763, 0.0315315, 0.00445357, 0.00593552],
        "below_structural_nitrogen": [0.0119763, 0.00566867, 0.00029149, 0.00047728],
        "above_metabolic_phosphorus": [0.00513782, 0.00212742, 0.00071441, 0.00072071],
        "above_structural_phosphorus": [0.00148339, 0.00052657, 0.00022537, 0.00023009],
        "woody_phosphorus": [
            0.00854665833297424,
            0.015605057949575844,
            0.008679346482530033,
            0.012216757912695322,
        ],
        "below_metabolic_phosphorus": [0.00125366, 0.00089397, 0.00021798, 0.00021479],
        "below_structural_phosphorus": [
            1.09364254e-03,
            5.30437838e-04,
            2.94129841e-05,
            4.95457779e-05,
        ],
    }

    actual_pools = calculate_updated_nutrient_pools(
        input_chemistries=input_chemistries,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(expected_pools.keys()) == set(actual_pools.keys())

    for key in actual_pools.keys():
        assert np.allclose(actual_pools[key], expected_pools[key])
