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
    dummy_litter_data, plant_inputs, input_lignin, input_c_n_ratios
):
    """Test that function to calculate updated pool chemistries works correctly."""
    from virtual_ecosystem.models.litter.chemistry import LitterChemistry

    litter_chemistry = LitterChemistry(dummy_litter_data)

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
        input_lignin=input_lignin,
        input_c_n_ratios=input_c_n_ratios,
        updated_pools=updated_pools,
    )

    assert set(actual_chemistries.keys()) == set(expected_chemistries.keys())

    for name in actual_chemistries.keys():
        assert np.allclose(actual_chemistries[name], expected_chemistries[name])


def test_calculate_lignin_updates(dummy_litter_data, plant_inputs, input_lignin):
    """Test that the function to calculate the lignin updates works as expected."""
    from virtual_ecosystem.models.litter.chemistry import LitterChemistry

    litter_chemistry = LitterChemistry(dummy_litter_data)

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


def test_calculate_c_n_ratio_updates(dummy_litter_data, plant_inputs, input_c_n_ratios):
    """Test that calculation of C:N ratio updates works properly."""
    from virtual_ecosystem.models.litter.chemistry import LitterChemistry

    litter_chemistry = LitterChemistry(dummy_litter_data)

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


def test_calculate_N_mineralisation(dummy_litter_data, decay_rates):
    """Test that function to calculate nitrogen mineralisation rate works properly."""
    from virtual_ecosystem.models.litter.chemistry import calculate_N_mineralisation

    expected_n_mineral = [0.0066373295, 0.0043192466, 0.0009099071, 0.0009765675]

    actual_n_mineral = calculate_N_mineralisation(
        decay_rates=decay_rates,
        c_n_ratio_above_metabolic=dummy_litter_data["c_n_ratio_above_metabolic"],
        c_n_ratio_above_structural=dummy_litter_data["c_n_ratio_above_structural"],
        c_n_ratio_woody=dummy_litter_data["c_n_ratio_woody"],
        c_n_ratio_below_metabolic=dummy_litter_data["c_n_ratio_below_metabolic"],
        c_n_ratio_below_structural=dummy_litter_data["c_n_ratio_below_structural"],
        active_microbe_depth=CoreConsts.max_depth_of_microbial_activity,
    )

    assert np.allclose(actual_n_mineral, expected_n_mineral)
