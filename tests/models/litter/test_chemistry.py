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


def test_calculate_lignin_updates(dummy_litter_data):
    """Test that the function to calculate the lignin updates works as expected."""
    from virtual_ecosystem.models.litter.chemistry import calculate_lignin_updates

    updated_pools = {
        "above_structural": np.array([0.5047038, 0.25068224, 0.09843778, 0.11163532]),
        "woody": np.array([4.774517, 11.898729, 7.361411, 7.331411]),
        "below_structural": np.array([0.6066315, 0.31860251, 0.02010566, 0.03038382]),
    }
    input_lignin = {
        "woody": np.array([0.233, 0.545, 0.612, 0.378]),
        "above_structural": np.array([0.28329484, 0.23062465, 0.75773447, 0.75393599]),
        "below_structural": np.array([0.7719623, 0.8004025, 0.7490983, 0.9589565]),
    }
    plant_inputs = {
        "woody": np.array([0.075, 0.099, 0.063, 0.033]),
        "above_ground_structural": np.array(
            [0.00487125, 0.001300815, 0.0069293052, 0.009979245]
        ),
        "below_ground_structural": np.array(
            [0.00602316, 0.00918288, 9.35514e-5, 0.008593488]
        ),
    }

    expected_lignin = {
        "above_structural": [-0.00209157, 0.00067782, 0.00406409, 0.00482142],
        "woody": [-0.00419414, -0.00212166, 0.00224223, 0.00012603],
        "below_structural": [2.70027594e-3, 1.58639055e-2, -4.1955995e-6, 5.9099388e-2],
    }

    actual_lignin = calculate_lignin_updates(
        lignin_above_structural=dummy_litter_data["lignin_above_structural"],
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        input_lignin=input_lignin,
        plant_inputs=plant_inputs,
        updated_pools=updated_pools,
    )

    for name in actual_lignin.keys():
        assert np.allclose(actual_lignin[name], expected_lignin[name])


def test_calculate_change_in_lignin(dummy_litter_data):
    """Test that function to calculate lignin changes works properly."""
    from virtual_ecosystem.models.litter.chemistry import calculate_change_in_lignin

    expected_lignin = [-0.008079787, -0.001949152, 0.0012328767, 0.0012328767]

    input_carbon = np.array([0.0775, 0.05, 0.0225, 0.0225])
    input_lignin = np.array([0.01, 0.34, 0.75, 0.75])

    actual_lignin = calculate_change_in_lignin(
        input_carbon=input_carbon,
        updated_pool_carbon=dummy_litter_data["litter_pool_woody"].to_numpy(),
        input_lignin=input_lignin,
        old_pool_lignin=dummy_litter_data["lignin_woody"].to_numpy(),
    )

    assert np.allclose(actual_lignin, expected_lignin)


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
