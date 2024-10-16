"""Test module for models.litter.inputs.py."""

from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_ecosystem.models.litter.constants import LitterConsts


def test_determine_all_plant_to_litter_flows(dummy_litter_data):
    """Test that function to determine plant to litter flows works correctly."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.inputs import LitterInputs

    expected_inputs = {
        "leaves_meta_split": [0.8123412282, 0.7504823457, 0.4509559749, 0.0852205423],
        "reproduct_meta_split": [0.8462925685, 0.833489905, 0.83196046, 0.8390536408],
        "roots_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
        "input_woody": [0.075, 0.099, 0.063, 0.033],
        "input_above_metabolic": [0.02449646, 0.00805233, 0.0128768, 0.00580533],
        "input_above_structural": [0.00553354, 0.00184767, 0.0135232, 0.0291447],
        "input_below_metabolic": [0.01588666, 0.007971, 0.00015073, 0.01021211],
        "input_below_structural": [0.01111334, 0.013029, 0.00014927, 0.01468789],
        "leaf_mass": [0.02703, 0.0024, 0.02385, 0.0312],
        "root_mass": [0.027, 0.021, 0.0003, 0.0249],
        "deadwood_mass": [0.075, 0.099, 0.063, 0.033],
        "reprod_mass": [0.003, 0.0075, 0.00255, 0.00375],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "deadwood_lignin": [0.233, 0.545, 0.612, 0.378],
        "reprod_lignin": [0.01, 0.03, 0.04, 0.02],
        "leaf_nitrogen": [15.00899, 32.5, 40.710063, 53.929808],
        "root_nitrogen": [30.3, 45.6, 43.3, 37.1],
        "deadwood_nitrogen": [60.7, 57.9, 73.1, 55.1],
        "reprod_nitrogen": [12.5, 23.8, 15.7, 18.2],
        "leaf_phosphorus": [414.77525, 342.625, 528.24654, 384.29231],
        "root_phosphorus": [656.7, 450.6, 437.3, 371.9],
        "deadwood_phosphorus": [856.5, 675.4, 933.2, 888.8],
        "reprod_phosphorus": [125.5, 105.0, 145.0, 189.2],
    }

    litter_inputs = LitterInputs.create_from_data(
        data=dummy_litter_data, constants=LitterConsts
    )
    # Check that the right sort of object has been created
    assert isinstance(litter_inputs, LitterInputs)

    # Then convert to a dict to check the values
    litter_inputs = asdict(litter_inputs)

    # Check that all keys match and have correct values for both dictionaries
    assert set(expected_inputs.keys()) == set(litter_inputs.keys())

    for key in litter_inputs.keys():
        assert np.allclose(litter_inputs[key], expected_inputs[key])


def test_combine_input_sources(dummy_litter_data):
    """Test that function to combine input sources works as expected."""
    from virtual_ecosystem.models.litter.inputs import combine_input_sources

    expected_combined = {
        "leaf_mass": [0.02703, 0.0024, 0.02385, 0.0312],
        "root_mass": [0.027, 0.021, 0.0003, 0.0249],
        "deadwood_mass": [0.075, 0.099, 0.063, 0.033],
        "reprod_mass": [0.003, 0.0075, 0.00255, 0.00375],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "deadwood_lignin": [0.233, 0.545, 0.612, 0.378],
        "reprod_lignin": [0.01, 0.03, 0.04, 0.02],
        "leaf_nitrogen": [15.00899, 32.5, 40.710063, 53.929808],
        "root_nitrogen": [30.3, 45.6, 43.3, 37.1],
        "deadwood_nitrogen": [60.7, 57.9, 73.1, 55.1],
        "reprod_nitrogen": [12.5, 23.8, 15.7, 18.2],
        "leaf_phosphorus": [414.77525, 342.625, 528.24654, 384.29231],
        "root_phosphorus": [656.7, 450.6, 437.3, 371.9],
        "deadwood_phosphorus": [856.5, 675.4, 933.2, 888.8],
        "reprod_phosphorus": [125.5, 105.0, 145.0, 189.2],
    }

    actual_combined = combine_input_sources(dummy_litter_data)

    assert set(expected_combined.keys()) == set(actual_combined.keys())

    for key in actual_combined.keys():
        assert np.allclose(actual_combined[key], expected_combined[key])


def test_calculate_metabolic_proportions_of_input(total_litter_input):
    """Test that function to calculate metabolic input proportions works as expected."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_metabolic_proportions_of_input,
    )

    expected_proportions = {
        "leaves_meta_split": [0.8123412282, 0.7504823457, 0.4509559749, 0.0852205423],
        "reproduct_meta_split": [0.8462925685, 0.833489905, 0.83196046, 0.8390536408],
        "roots_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
    }

    actual_proportions = calculate_metabolic_proportions_of_input(
        total_input=total_litter_input, constants=LitterConsts
    )

    assert set(expected_proportions.keys()) == set(actual_proportions.keys())

    for key in actual_proportions.keys():
        assert np.allclose(actual_proportions[key], expected_proportions[key])


def test_partion_plant_inputs_between_pools(metabolic_splits, total_litter_input):
    """Check function to partition inputs into litter pools works as expected."""
    from virtual_ecosystem.models.litter.inputs import (
        partion_plant_inputs_between_pools,
    )

    expected_inputs = {
        "input_woody": [0.075, 0.099, 0.063, 0.033],
        "input_above_metabolic": [0.02449646, 0.00805233, 0.0128768, 0.00580533],
        "input_above_structural": [0.00553354, 0.00184767, 0.0135232, 0.02914467],
        "input_below_metabolic": [0.01588666, 0.007971, 0.00015073, 0.01021211],
        "input_below_structural": [0.01111334, 0.013029, 0.00014927, 0.01468789],
    }

    actual_inputs = partion_plant_inputs_between_pools(
        total_input=total_litter_input, metabolic_splits=metabolic_splits
    )

    assert set(expected_inputs.keys()) == set(actual_inputs.keys())

    for key in actual_inputs.keys():
        assert np.allclose(actual_inputs[key], expected_inputs[key])


def test_split_pool_into_metabolic_and_structural_litter(dummy_litter_data):
    """Check function to split input biomass between litter pools works as expected."""

    from virtual_ecosystem.models.litter.inputs import (
        split_pool_into_metabolic_and_structural_litter,
    )

    expected_split = [0.812403025, 0.640197595, 0.424077745, 0.0089426731]

    actual_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=dummy_litter_data["leaf_turnover_lignin"],
        carbon_nitrogen_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"],
        carbon_phosphorus_ratio=dummy_litter_data["leaf_turnover_c_p_ratio"],
        max_metabolic_fraction=LitterConsts.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=LitterConsts.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=LitterConsts.metabolic_split_phosphorus_sensitivity,
    )

    assert np.allclose(actual_split, expected_split)


@pytest.mark.parametrize(
    "c_n_ratios,expected_log",
    [
        pytest.param(
            np.array([34.2, 55.5, 37.1, 400.7]),
            (
                (
                    ERROR,
                    "Fraction of input biomass going to metabolic pool has dropped "
                    "below zero!",
                ),
            ),
            id="negative_metabolic_flow",
        ),
        pytest.param(
            np.array([34.2, 55.5, 37.1, 3.7]),
            (
                (
                    ERROR,
                    "Fraction of input biomass going to structural biomass is less than"
                    " the lignin fraction!",
                ),
            ),
            id="less_than_lignin",
        ),
    ],
)
def test_split_pool_into_metabolic_and_structural_litter_bad_data(
    caplog, c_n_ratios, expected_log
):
    """Check that pool split functions raises an error if out of bounds data is used."""

    from virtual_ecosystem.models.litter.inputs import (
        split_pool_into_metabolic_and_structural_litter,
    )

    # C:N ratio of >400 is far too high for the function to behave sensibly
    lignin_proportions = np.array([0.5, 0.4, 0.35, 0.23])
    c_p_ratios = np.array([[415.0, 327.4, 554.5, 145.0]])

    with pytest.raises(ValueError):
        split_pool_into_metabolic_and_structural_litter(
            lignin_proportion=lignin_proportions,
            carbon_nitrogen_ratio=c_n_ratios,
            carbon_phosphorus_ratio=c_p_ratios,
            max_metabolic_fraction=LitterConsts.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=LitterConsts.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=LitterConsts.metabolic_split_phosphorus_sensitivity,
        )

    # Check the error reports
    log_check(caplog, expected_log)
