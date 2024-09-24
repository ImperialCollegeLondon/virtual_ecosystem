"""Test module for litter.chemistry.py.

This module tests the functionality of the litter chemistry module
"""

import numpy as np

from virtual_ecosystem.core.constants import CoreConsts
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
    dummy_litter_data, plant_inputs, metabolic_splits, updated_pools, litter_chemistry
):
    """Test that function to calculate updated pool chemistries works correctly."""

    expected_chemistries = {
        "lignin_above_structural": [0.49726219, 0.10065698, 0.67693666, 0.6673972],
        "lignin_woody": [0.49580543, 0.7978783, 0.35224272, 0.35012606],
        "lignin_below_structural": [0.49974338, 0.26270806, 0.74846367, 0.71955592],
        "c_n_ratio_above_metabolic": [7.3918226, 8.9320212, 10.413317, 9.8624367],
        "c_n_ratio_above_structural": [37.5547150, 43.3448492, 48.0974058, 52.0359678],
        "c_n_ratio_woody": [55.5816919, 63.2550698, 47.5208477, 59.0819914],
        "c_n_ratio_below_metabolic": [10.7299421, 11.3394567, 15.1984024, 12.2222413],
        "c_n_ratio_below_structural": [50.6228215, 55.9998994, 73.0948342, 58.6661277],
        "c_p_ratio_above_metabolic": [69.965838, 68.549282, 107.38423, 96.583573],
        "c_p_ratio_above_structural": [346.048307, 472.496124, 465.834123, 525.882608],
        "c_p_ratio_woody": [560.22870571, 762.56863636, 848.03530307, 600.40427444],
        "c_p_ratio_below_metabolic": [308.200782, 405.110726, 314.824814, 372.870229],
        "c_p_ratio_below_structural": [563.06464, 597.68324, 772.78968, 609.82810],
    }

    actual_chemistries = litter_chemistry.calculate_new_pool_chemistries(
        plant_inputs=plant_inputs,
        metabolic_splits=metabolic_splits,
        updated_pools=updated_pools,
    )

    assert set(actual_chemistries.keys()) == set(expected_chemistries.keys())

    for name in actual_chemistries.keys():
        assert np.allclose(actual_chemistries[name], expected_chemistries[name])


def test_calculate_lignin_updates(
    dummy_litter_data, plant_inputs, input_lignin, updated_pools, litter_chemistry
):
    """Test that the function to calculate the lignin updates works as expected."""

    expected_lignin = {
        "above_structural": [-0.00273781, 0.00065698, -0.02306334, -0.03260280],
        "woody": [-0.00419457, -0.0021217, 0.00224272, 0.00012606],
        "below_structural": [-0.00025662, 0.01270806, -0.00153633, -0.03044408],
    }

    actual_lignin = litter_chemistry.calculate_lignin_updates(
        input_lignin=input_lignin,
        plant_inputs=plant_inputs,
        updated_pools=updated_pools,
    )

    assert set(actual_lignin.keys()) == set(expected_lignin.keys())

    for name in actual_lignin.keys():
        assert np.allclose(actual_lignin[name], expected_lignin[name])


def test_calculate_change_in_chemical_concentration(dummy_litter_data):
    """Test that function to calculate chemistry changes works properly."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_change_in_chemical_concentration,
    )

    expected_lignin = [-0.008079787, -0.001949152, 0.0012328767, 0.0012328767]

    input_carbon = np.array([0.0775, 0.05, 0.0225, 0.0225])
    input_lignin = np.array([0.01, 0.34, 0.75, 0.75])

    actual_lignin = calculate_change_in_chemical_concentration(
        input_carbon=input_carbon,
        updated_pool_carbon=dummy_litter_data["litter_pool_woody"].to_numpy(),
        input_conc=input_lignin,
        old_pool_conc=dummy_litter_data["lignin_woody"].to_numpy(),
    )

    assert np.allclose(actual_lignin, expected_lignin)


def test_calculate_c_n_ratio_updates(
    dummy_litter_data, plant_inputs, input_c_n_ratios, updated_pools, litter_chemistry
):
    """Test that calculation of C:N ratio updates works properly."""

    expected_change = {
        "above_metabolic": [0.091822576, 0.232021211, 0.313317200, 0.062436702],
        "above_structural": [0.05471499, 0.14484922, 2.29740576, 1.835967773],
        "woody": [0.0816919, -0.0449302, 0.2208477, -0.0180086],
        "below_metabolic": [0.02994209, 0.03945672, -0.00159759, -0.17775875],
        "below_structural": [0.12282146, 0.39989943, -0.00516585, -2.53387232],
    }

    actual_change = litter_chemistry.calculate_c_n_ratio_updates(
        plant_inputs=plant_inputs,
        input_c_n_ratios=input_c_n_ratios,
        updated_pools=updated_pools,
    )

    assert set(expected_change.keys()) == set(actual_change.keys())

    for key in actual_change.keys():
        assert np.allclose(actual_change[key], expected_change[key])


def test_calculate_c_p_ratio_updates(
    dummy_litter_data, plant_inputs, input_c_p_ratios, updated_pools, litter_chemistry
):
    """Test that calculation of C:P ratio updates works properly."""

    expected_change = {
        "above_metabolic": [12.665838, -0.15071757, 7.28423174, 0.78357281],
        "above_structural": [8.5483073, -0.7038764, 50.034123, -44.317392],
        "woody": [4.72870571, -0.73136364, 0.73530307, 1.30427444],
        "below_metabolic": [-2.49921796, -6.18927446, -0.37518617, -39.52977135],
        "below_structural": [12.56464272, 2.08324337, -0.31032454, -41.37190224],
    }

    actual_change = litter_chemistry.calculate_c_p_ratio_updates(
        plant_inputs=plant_inputs,
        input_c_p_ratios=input_c_p_ratios,
        updated_pools=updated_pools,
    )

    assert set(expected_change.keys()) == set(actual_change.keys())

    for key in actual_change.keys():
        assert np.allclose(actual_change[key], expected_change[key])


def test_calculate_N_mineralisation(dummy_litter_data, decay_rates, litter_chemistry):
    """Test that function to calculate nitrogen mineralisation rate works properly."""

    expected_n_mineral = [0.00595963, 0.00379074, 0.00085095, 0.0009043]

    actual_n_mineral = litter_chemistry.calculate_N_mineralisation(
        decay_rates=decay_rates,
        active_microbe_depth=CoreConsts.max_depth_of_microbial_activity,
    )

    assert np.allclose(actual_n_mineral, expected_n_mineral)


def test_calculate_P_mineralisation(dummy_litter_data, decay_rates, litter_chemistry):
    """Test that function to calculate phosphorus mineralisation rate works properly."""

    expected_p_mineral = [4.39937479e-4, 2.13832149e-4, 6.40698004e-5, 6.56405873e-5]

    actual_p_mineral = litter_chemistry.calculate_P_mineralisation(
        decay_rates=decay_rates,
        active_microbe_depth=CoreConsts.max_depth_of_microbial_activity,
    )

    assert np.allclose(actual_p_mineral, expected_p_mineral)


def test_calculate_litter_input_lignin_concentrations(
    dummy_litter_data, plant_inputs, litter_chemistry
):
    """Check calculation of lignin concentrations of each plant flow to litter."""

    expected_woody = [0.233, 0.545, 0.612, 0.378]
    expected_concs_above_struct = [0.24971768, 0.22111396, 0.51122474, 0.56571041]
    expected_concs_below_struct = [0.48590258, 0.56412613, 0.54265483, 0.67810978]

    actual_concs = litter_chemistry.calculate_litter_input_lignin_concentrations(
        plant_input_below_struct=plant_inputs["below_ground_structural"],
        plant_input_above_struct=plant_inputs["above_ground_structural"],
    )

    assert np.allclose(actual_concs["woody"], expected_woody)
    assert np.allclose(actual_concs["above_structural"], expected_concs_above_struct)
    assert np.allclose(actual_concs["below_structural"], expected_concs_below_struct)


def test_calculate_litter_input_nitrogen_ratios(
    dummy_litter_data, metabolic_splits, litter_chemistry
):
    """Check function to calculate the C:N ratios of input to each litter pool works."""

    expected_c_n_ratios = {
        "woody": [60.7, 57.9, 73.1, 55.1],
        "below_metabolic": [11.449427, 13.09700, 14.48056, 11.04331],
        "below_structural": [57.24714, 65.48498, 72.40281, 55.21655],
        "above_metabolic": [8.48355299, 14.17116914, 12.3424635, 11.10877484],
        "above_structural": [42.5018709, 69.9028550, 64.6044513, 57.7622747],
    }

    actual_c_n_ratios = litter_chemistry.calculate_litter_input_nitrogen_ratios(
        metabolic_splits=metabolic_splits,
        struct_to_meta_nitrogen_ratio=LitterConsts.structural_to_metabolic_n_ratio,
    )

    assert set(expected_c_n_ratios.keys()) == set(actual_c_n_ratios.keys())

    for key in actual_c_n_ratios.keys():
        assert np.allclose(actual_c_n_ratios[key], expected_c_n_ratios[key])


def test_calculate_litter_input_phosphorus_ratios(
    dummy_litter_data, metabolic_splits, litter_chemistry
):
    """Check function to calculate the C:P ratios of input to each litter pool works."""

    expected_c_p_ratios = {
        "woody": [856.5, 675.4, 933.2, 888.8],
        "below_metabolic": [248.1465, 129.418998, 146.243645, 110.700999],
        "below_structural": [1240.73249721, 647.09498874, 731.2182237, 553.50499377],
        "above_metabolic": [220.55713162, 65.14600889, 152.23446238, 112.22496062],
        "above_structural": [1118.95921, 343.440873, 825.333331, 387.658509],
    }

    actual_c_p_ratios = litter_chemistry.calculate_litter_input_phosphorus_ratios(
        metabolic_splits=metabolic_splits,
        struct_to_meta_phosphorus_ratio=LitterConsts.structural_to_metabolic_p_ratio,
    )

    assert set(expected_c_p_ratios.keys()) == set(actual_c_p_ratios.keys())

    for key in actual_c_p_ratios.keys():
        assert np.allclose(actual_c_p_ratios[key], expected_c_p_ratios[key])


def test_calculate_nutrient_split_between_litter_pools(
    dummy_litter_data, metabolic_splits
):
    """Check the function to calculate the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.chemistry import (
        calculate_nutrient_split_between_litter_pools,
    )

    expected_meta_c_n = np.array([11.449427, 13.09700, 14.48056, 11.04331])
    expected_struct_c_n = np.array([57.24714, 65.48498, 72.40281, 55.21655])

    actual_meta_c_n, actual_struct_c_n = calculate_nutrient_split_between_litter_pools(
        input_c_nut_ratio=dummy_litter_data["root_turnover_c_n_ratio"],
        metabolic_split=metabolic_splits["roots"],
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
        (
            actual_meta_c_n * metabolic_splits["roots"]
            + actual_struct_c_n * (1 - metabolic_splits["roots"])
        ),
    )
