"""Test module for litter.chemistry.py.

This module tests the functionality of the litter chemistry module
"""

import numpy as np

from virtual_ecosystem.models.litter.constants import LitterConsts


def test_calculate_litter_chemistry_factor():
    """Test that litter chemistry effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_litter_chemistry_factor,
    )

    lignin_proportions = np.array([0.01, 0.1, 0.5, 0.8])

    expected_factor = [0.95122942, 0.60653065, 0.08208499, 0.01831563]

    actual_factor = calculate_litter_chemistry_factor(
        lignin_proportions, LitterConsts.lignin_inhibition_factor
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
        "lignin_above_structural": [0.49726312, 0.10113065, 0.67996749, 0.68136766],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974337, 0.26270880, 0.74846363, 0.71955458],
        "c_n_ratio_above_metabolic": [7.5450184, 8.9814418, 10.998779, 10.175958],
        "c_n_ratio_above_structural": [37.6666294, 43.3945275, 49.4785666, 54.4562879],
        "c_n_ratio_woody": [55.57479, 63.250918, 47.44333, 59.08069],
        "c_n_ratio_below_metabolic": [10.90629, 11.42741, 15.21408, 13.02765],
        "c_n_ratio_below_structural": [50.96669, 56.78504, 73.33861, 72.76419],
        "c_p_ratio_above_metabolic": [61.099543, 70.015298, 110.68070, 98.767703],
        "c_p_ratio_above_structural": [340.38278, 473.84604, 456.99901, 579.00396],
        "c_p_ratio_woody": [558.58393, 762.474347, 847.96815, 599.98045],
        "c_p_ratio_below_metabolic": [314.40006, 404.09534, 315.06196, 360.38398],
        "c_p_ratio_below_structural": [558.1202, 607.2732, 775.4709, 759.5603],
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
        "above_structural": [0.4972631215, 0.1011306546, 0.6799674901, 0.6813676608],
        "woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "below_structural": [0.49974337, 0.26270880, 0.74846363, 0.71955458],
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


def test_calculate_updated_pool_nutrient_ratio(
    dummy_litter_data,
    post_consumption_pools,
    litter_inputs,
    litter_losses,
    input_chemistries,
):
    """Test that calculation of updated pool nutrient ratios works as expected."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_updated_pool_nutrient_ratio,
    )

    expected_ratio = [7.5450184, 8.9814418, 10.998779, 10.175958]

    actual_ratio = calculate_updated_pool_nutrient_ratio(
        initial_carbon=post_consumption_pools["above_metabolic"],
        input_carbon_rate=litter_inputs.above_metabolic,
        carbon_loss=litter_losses.above_metabolic_carbon,
        initial_c_nut_ratio=dummy_litter_data["c_n_ratio_above_metabolic"].to_numpy(),
        input_c_nut_ratio=input_chemistries.above_metabolic_nitrogen,
        nutrient_loss=litter_losses.above_metabolic_nitrogen,
        update_interval=2.0,
    )

    assert np.allclose(actual_ratio, expected_ratio)


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

    expected_lignin = [0.4972631215, 0.1011306546, 0.6799674901, 0.6813676608]

    actual_lignin = calculate_updated_pool_lignin_proportion(
        initial_carbon=post_consumption_pools["above_structural"],
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


def test_calculate_new_c_n_ratios(
    litter_inputs,
    input_chemistries,
    litter_chemistry,
    litter_losses,
    post_consumption_pools,
):
    """Test that calculation of C:N ratio updates works properly."""

    expected_ratios = {
        "above_metabolic": [7.5450184, 8.9814418, 10.998779, 10.175958],
        "above_structural": [37.6666294, 43.3945275, 49.4785666, 54.4562879],
        "woody": [55.57479, 63.250918, 47.44333, 59.08069],
        "below_metabolic": [10.90629, 11.42741, 15.21408, 13.02765],
        "below_structural": [50.96669, 56.78504, 73.33861, 72.76419],
    }

    actual_ratios = litter_chemistry.calculate_new_c_n_ratios(
        litter_inputs=litter_inputs,
        input_chemistries=input_chemistries,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(expected_ratios.keys()) == set(actual_ratios.keys())

    for key in actual_ratios.keys():
        assert np.allclose(actual_ratios[key], expected_ratios[key])


def test_calculate_new_c_p_ratios(
    litter_inputs,
    input_chemistries,
    litter_chemistry,
    litter_losses,
    post_consumption_pools,
):
    """Test that calculation of C:P ratio updates works properly."""

    expected_change = {
        "above_metabolic": [61.099543, 70.015298, 110.68070, 98.767703],
        "above_structural": [340.38278, 473.84604, 456.99901, 579.00396],
        "woody": [558.58393, 762.474347, 847.96815, 599.98045],
        "below_metabolic": [314.40006, 404.09534, 315.06196, 360.38398],
        "below_structural": [558.1202, 607.2732, 775.4709, 759.5603],
    }

    actual_change = litter_chemistry.calculate_new_c_p_ratios(
        litter_inputs=litter_inputs,
        input_chemistries=input_chemistries,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(expected_change.keys()) == set(actual_change.keys())

    for key in actual_change.keys():
        assert np.allclose(actual_change[key], expected_change[key])
