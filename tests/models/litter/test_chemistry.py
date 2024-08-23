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
    dummy_litter_data, plant_inputs, metabolic_splits, litter_chemistry
):
    """Test that function to calculate updated pool chemistries works correctly."""

    updated_pools = {
        "above_metabolic": np.array([0.32072786, 0.15473132, 0.08523907, 0.08074153]),
        "above_structural": np.array([0.5047038, 0.25068224, 0.09843778, 0.11163532]),
        "woody": np.array([4.774517, 11.898729, 7.361411, 7.331411]),
        "below_metabolic": np.array([0.4090768, 0.37287148, 0.06883228, 0.08315412]),
        "below_structural": np.array([0.6066315, 0.31860251, 0.02010566, 0.03038382]),
    }

    expected_chemistries = {
        "lignin_above_structural": [0.49790843, 0.10067782, 0.70495536, 0.71045831],
        "lignin_woody": [0.49580586, 0.79787834, 0.35224223, 0.35012603],
        "lignin_below_structural": [0.50313604, 0.26586391, 0.7499951, 0.82142894],
        "c_n_ratio_above_metabolic": [7.42828417, 8.93702902, 11.13974273, 10.28862942],
        "c_n_ratio_above_structural": [37.5698310, 43.3465444, 49.0206010, 54.4471558],
        "c_n_ratio_woody": [55.58168366, 63.25507083, 47.52080006, 59.08199528],
        "c_n_ratio_below_metabolic": [10.9044015, 11.4675610, 15.2070612, 12.6623415],
        "c_n_ratio_below_structural": [50.7755820, 56.387878, 73.1837156, 64.0424461],
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
    dummy_litter_data, plant_inputs, input_lignin, litter_chemistry
):
    """Test that the function to calculate the lignin updates works as expected."""

    updated_pools = {
        "above_structural": np.array([0.5047038, 0.25068224, 0.09843778, 0.11163532]),
        "woody": np.array([4.774517, 11.898729, 7.361411, 7.331411]),
        "below_structural": np.array([0.6066315, 0.31860251, 0.02010566, 0.03038382]),
    }

    expected_lignin = {
        "above_structural": [-0.00209157, 0.00067782, 0.00495532, 0.01045834],
        "woody": [-0.00419414, -0.00212166, 0.00224223, 0.00012603],
        "below_structural": [3.1360386e-3, 1.5863906e-2, -4.90160482e-6, 7.1428885e-2],
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
    dummy_litter_data, plant_inputs, input_c_n_ratios, litter_chemistry
):
    """Test that calculation of C:N ratio updates works properly."""

    updated_pools = {
        "above_metabolic": np.array([0.32072786, 0.15473132, 0.08523907, 0.08074153]),
        "above_structural": np.array([0.5047038, 0.25068224, 0.09843778, 0.11163532]),
        "woody": np.array([4.774517, 11.898729, 7.361411, 7.331411]),
        "below_metabolic": np.array([0.4090768, 0.37287148, 0.06883228, 0.08315412]),
        "below_structural": np.array([0.6066315, 0.31860251, 0.02010566, 0.03038382]),
    }

    expected_change = {
        "above_metabolic": [0.12828416, 0.23702901, 1.03974239, 0.48862956],
        "above_structural": [0.06983094, 0.14654437, 3.22060275, 4.24715499],
        "woody": [0.081683655, -0.04492917, 0.220800061, -0.01800472],
        "below_metabolic": [0.20440145, 0.16756069, 0.00706121, 0.26234147],
        "below_structural": [0.27558203, 0.78787769, 0.08371555, 2.8424462],
    }

    actual_change = litter_chemistry.calculate_c_n_ratio_updates(
        plant_inputs=plant_inputs,
        input_c_n_ratios=input_c_n_ratios,
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
