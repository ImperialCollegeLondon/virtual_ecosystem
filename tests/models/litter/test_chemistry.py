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
    updated_pools,
    litter_chemistry,
    litter_losses,
    post_consumption_pools,
):
    """Test that function to calculate updated pool chemistries works correctly."""

    expected_chemistries = {
        "lignin_above_structural": [0.49726272, 0.10113017, 0.67782882, 0.67072519],
        "lignin_woody": [0.49580543, 0.7978783, 0.35224272, 0.35012606],
        "lignin_below_structural": [0.49974338, 0.26270806, 0.74846367, 0.71955592],
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
        updated_pools=updated_pools,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(actual_chemistries.keys()) == set(expected_chemistries.keys())

    for name in actual_chemistries.keys():
        assert np.allclose(actual_chemistries[name], expected_chemistries[name])


def test_calculate_lignin_updates(
    input_lignin, updated_pools, litter_chemistry, litter_inputs
):
    """Test that the function to calculate the lignin updates works as expected."""

    expected_lignin = {
        "above_structural": [-0.0027373, 0.001130172, -0.022171178, -0.029274812],
        "woody": [-0.00419457, -0.0021217, 0.00224272, 0.00012606],
        "below_structural": [-0.00025662, 0.01270806, -0.00153633, -0.03044408],
    }

    actual_lignin = litter_chemistry.calculate_lignin_updates(
        input_lignin=input_lignin,
        litter_inputs=litter_inputs,
        updated_pools=updated_pools,
    )

    assert set(actual_lignin.keys()) == set(expected_lignin.keys())

    for name in actual_lignin.keys():
        assert np.allclose(actual_lignin[name], expected_lignin[name])


def test_calculate_updated_pool_nutrient_ratio(
    dummy_litter_data,
    post_consumption_pools,
    litter_inputs,
    litter_losses,
    input_c_n_ratios,
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
        input_c_nut_ratio=input_c_n_ratios["above_metabolic"],
        nutrient_loss=litter_losses.above_metabolic_nitrogen,
        update_interval=2.0,
    )

    assert np.allclose(actual_ratio, expected_ratio)


def test_calculate_change_in_chemical_concentration(
    dummy_litter_data, post_consumption_pools
):
    """Test that function to calculate chemistry changes works properly."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_change_in_chemical_concentration,
    )

    expected_lignin = [-0.008079787, -0.001949152, 0.0012328767, 0.0012328767]

    input_carbon = np.array([0.0775, 0.05, 0.0225, 0.0225])
    input_lignin = np.array([0.01, 0.34, 0.75, 0.75])

    actual_lignin = calculate_change_in_chemical_concentration(
        input_carbon=input_carbon,
        updated_pool_carbon=post_consumption_pools["woody"],
        input_conc=input_lignin,
        old_pool_conc=dummy_litter_data["lignin_woody"].to_numpy(),
    )

    assert np.allclose(actual_lignin, expected_lignin)


def test_calculate_new_c_n_ratios(
    litter_inputs,
    input_c_n_ratios,
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
        input_c_n_ratios=input_c_n_ratios,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(expected_ratios.keys()) == set(actual_ratios.keys())

    for key in actual_ratios.keys():
        assert np.allclose(actual_ratios[key], expected_ratios[key])


def test_calculate_new_c_p_ratios(
    litter_inputs,
    input_c_p_ratios,
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
        input_c_p_ratios=input_c_p_ratios,
        litter_losses=litter_losses,
        original_pools=post_consumption_pools,
        update_interval=2.0,
    )

    assert set(expected_change.keys()) == set(actual_change.keys())

    for key in actual_change.keys():
        assert np.allclose(actual_change[key], expected_change[key])


def test_calculate_litter_input_lignin_concentrations(litter_inputs):
    """Check calculation of lignin concentrations of each plant flow to litter."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_litter_input_lignin_concentrations,
    )

    expected_woody = [0.233, 0.545, 0.612, 0.378]
    expected_concs_above_struct = [0.25011178, 0.25345463, 0.54339369, 0.61992378]
    expected_concs_below_struct = [0.48590258, 0.56412613, 0.54265483, 0.67810978]

    actual_concs = calculate_litter_input_lignin_concentrations(
        litter_inputs=litter_inputs,
    )

    assert np.allclose(actual_concs["woody"], expected_woody)
    assert np.allclose(actual_concs["above_structural"], expected_concs_above_struct)
    assert np.allclose(actual_concs["below_structural"], expected_concs_below_struct)


def test_calculate_litter_input_nitrogen_ratios(litter_inputs):
    """Check function to calculate the C:N ratios of input to each litter pool works."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_litter_input_nitrogen_ratios,
    )

    expected_c_n_ratios = {
        "woody": [60.7, 57.9, 73.1, 55.1],
        "below_metabolic": [20.32269136, 22.96676383, 26.06473456, 19.59251036],
        "below_structural": [101.61345679, 114.83381916, 130.32367278, 97.96255178],
        "above_metabolic": [12.540983, 21.600478, 20.237902, 15.403147],
        "above_structural": [62.91002, 110.3194, 109.3635, 75.59183],
    }

    actual_c_n_ratios = calculate_litter_input_nitrogen_ratios(
        litter_inputs=litter_inputs,
        struct_to_meta_nitrogen_ratio=LitterConsts.structural_to_metabolic_n_ratio,
    )

    assert set(expected_c_n_ratios.keys()) == set(actual_c_n_ratios.keys())

    for key in actual_c_n_ratios.keys():
        assert np.allclose(actual_c_n_ratios[key], expected_c_n_ratios[key])


def test_calculate_litter_input_phosphorus_ratios(litter_inputs):
    """Check function to calculate the C:P ratios of input to each litter pool works."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_litter_input_phosphorus_ratios,
    )

    expected_c_p_ratios = {
        "woody": [856.5, 675.4, 933.2, 888.8],
        "below_metabolic": [440.4591226, 226.94788998, 263.23576031, 196.40039357],
        "below_structural": [2202.29561299, 1134.7394499, 1316.17880156, 982.00196785],
        "above_metabolic": [286.886303, 107.015923, 241.802298, 136.049497],
        "above_structural": [1488.595406, 580.6433876, 1408.378272, 610.0666667],
    }

    actual_c_p_ratios = calculate_litter_input_phosphorus_ratios(
        litter_inputs=litter_inputs,
        struct_to_meta_phosphorus_ratio=LitterConsts.structural_to_metabolic_p_ratio,
    )

    assert set(expected_c_p_ratios.keys()) == set(actual_c_p_ratios.keys())

    for key in actual_c_p_ratios.keys():
        assert np.allclose(actual_c_p_ratios[key], expected_c_p_ratios[key])


def test_calculate_nutrient_split_between_litter_pools(
    dummy_litter_data, litter_inputs
):
    """Check the function to calculate the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_nutrient_split_between_litter_pools,
    )

    expected_meta_c_n = np.array([20.32269136, 22.96676383, 26.06473456, 19.59251036])
    expected_struct_c_n = np.array([101.6134568, 114.83381915, 130.3236728, 97.9625518])

    actual_meta_c_n, actual_struct_c_n = calculate_nutrient_split_between_litter_pools(
        input_c_nut_ratio=dummy_litter_data["root_turnover_c_n_ratio"],
        metabolic_split=litter_inputs.roots_meta_split,
        struct_to_meta_nutrient_ratio=LitterConsts.structural_to_metabolic_n_ratio,
    )

    # Standard checks of the produced values
    assert np.allclose(actual_meta_c_n, expected_meta_c_n)
    assert np.allclose(actual_struct_c_n, expected_struct_c_n)
    # Check that expected ratio is actually preserved by the function
    assert np.allclose(
        expected_struct_c_n,
        expected_meta_c_n * LitterConsts.structural_to_metabolic_n_ratio,
    )
    # Check that weighted sum of the two new C:N ratios is compatible with the original
    # C:N ratio
    assert np.allclose(
        dummy_litter_data["root_turnover_c_n_ratio"],
        1
        / (
            (litter_inputs.roots_meta_split / actual_meta_c_n)
            + ((1 - litter_inputs.roots_meta_split) / actual_struct_c_n)
        ),
    )
