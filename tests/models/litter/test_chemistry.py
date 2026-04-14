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
        "lignin_above_structural": [0.49765798, 0.10073481, 0.68181057, 0.68425001],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974337, 0.26270880, 0.74846363, 0.71955458],
        "above_metabolic_nitrogen": [0.04155601, 0.01679779, 0.00720536, 0.00722372],
        "above_structural_nitrogen": [0.01340387, 0.00576308, 0.00207896, 0.00214561],
        "woody_nitrogen": [
            0.08590272675794186,
            0.18811515700056716,
            0.15512843175215565,
            0.12406449399964693,
        ],
        "below_metabolic_nitrogen": [
            0.03646374156564698,
            0.031780241542046714,
            0.004463859135747939,
            0.0059729429329157605,
        ],
        "below_structural_nitrogen": [0.01197838, 0.00567122, 0.00027473, 0.00047664],
        "above_metabolic_phosphorus": [
            0.005137187527623923,
            0.0021249325400981077,
            0.0007146426225135252,
            0.0007456091915781818,
        ],
        "above_structural_phosphorus": [
            0.0014833637342951769,
            0.0005261425345003986,
            0.00022508107092281037,
            0.000201785392779848,
        ],
        "woody_phosphorus": [
            0.00854665833297424,
            0.015605057949575844,
            0.008679346482530033,
            0.012216757912695322,
        ],
        "below_metabolic_phosphorus": [
            0.0012648984227293088,
            0.0008987132838502913,
            0.0002155560449125626,
            0.00021591806050868297,
        ],
        "below_structural_phosphorus": [
            0.0010938513065823457,
            0.000530306030300695,
            2.5977931602591404e-5,
            4.566095674036676e-5,
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
        "lignin_above_structural": [0.49765798, 0.10073481, 0.68181057, 0.68425001],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974337, 0.26270880, 0.74846363, 0.71955458],
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

    expected_lignin = [0.49765798, 0.10073481, 0.68181057, 0.68425001]

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
        "above_metabolic_nitrogen": [0.04155601, 0.01679779, 0.00720536, 0.00722372],
        "above_structural_nitrogen": [0.01340387, 0.00576308, 0.00207896, 0.00214561],
        "woody_nitrogen": [
            0.08590272675794186,
            0.18811515700056716,
            0.15512843175215565,
            0.12406449399964693,
        ],
        "below_metabolic_nitrogen": [
            0.03646374156564698,
            0.031780241542046714,
            0.004463859135747939,
            0.0059729429329157605,
        ],
        "below_structural_nitrogen": [0.01197838, 0.00567122, 0.00027473, 0.00047664],
        "above_metabolic_phosphorus": [
            0.005137187527623923,
            0.0021249325400981077,
            0.0007146426225135252,
            0.0007456091915781818,
        ],
        "above_structural_phosphorus": [
            0.0014833637342951769,
            0.0005261425345003986,
            0.00022508107092281037,
            0.000201785392779848,
        ],
        "woody_phosphorus": [
            0.00854665833297424,
            0.015605057949575844,
            0.008679346482530033,
            0.012216757912695322,
        ],
        "below_metabolic_phosphorus": [
            0.0012648984227293088,
            0.0008987132838502913,
            0.0002155560449125626,
            0.00021591806050868297,
        ],
        "below_structural_phosphorus": [
            0.0010938513065823457,
            0.000530306030300695,
            2.5977931602591404e-5,
            4.566095674036676e-5,
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
