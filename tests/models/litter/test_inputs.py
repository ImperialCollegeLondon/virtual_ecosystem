"""Test module for models.litter.inputs.py."""

from contextlib import nullcontext as does_not_raise
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
        "input_rate_woody": [0.0375, 0.0495, 0.0315, 0.0165],
        "input_rate_above_metabolic": [0.01224823, 0.004026165, 0.0064384, 0.002902665],
        "input_rate_above_structural": [0.00276677, 0.000923835, 0.0067616, 0.01457235],
        "input_rate_below_metabolic": [0.00794333, 0.0039855, 7.5365e-5, 0.005106055],
        "input_rate_below_structural": [0.00555667, 0.0065145, 7.4635e-5, 0.007343945],
        "leaf_mass": [0.02703, 0.0024, 0.02385, 0.0312],
        "root_mass": [0.027, 0.021, 0.0003, 0.0249],
        "deadwood_mass": [0.075, 0.099, 0.063, 0.033],
        "reprod_mass": [0.003, 0.0075, 0.00255, 0.00375],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
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
        data=dummy_litter_data, constants=LitterConsts, update_interval=2.0
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
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
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


def test_partion_plant_inputs_between_pools(
    metabolic_splits, total_litter_input, fixture_core_components
):
    """Check function to partition inputs into litter pools works as expected."""
    from virtual_ecosystem.models.litter.inputs import (
        partion_plant_inputs_between_pools,
    )

    expected_inputs = {
        "input_rate_woody": [0.0375, 0.0495, 0.0315, 0.0165],
        "input_rate_above_metabolic": [0.01224823, 0.004026165, 0.0064384, 0.002902665],
        "input_rate_above_structural": [0.00276677, 0.000923835, 0.0067616, 0.01457235],
        "input_rate_below_metabolic": [0.00794333, 0.0039855, 7.5365e-5, 0.005106055],
        "input_rate_below_structural": [0.00555667, 0.0065145, 7.4635e-5, 0.007343945],
    }

    actual_inputs = partion_plant_inputs_between_pools(
        total_input=total_litter_input,
        metabolic_splits=metabolic_splits,
        update_interval=2.0,
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
        lignin_proportion=dummy_litter_data["senesced_leaf_lignin"],
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


@pytest.mark.parametrize(
    argnames=[
        "raises",
        "turnover_chemical_proportion",
        "herbivory_chemical_proportion",
        "expected_proportions",
        "expected_log",
    ],
    argvalues=[
        pytest.param(
            does_not_raise(),
            np.array([0.05, 0.25, 0.3, 0.57]),
            np.array([0.13, 0.08, 0.27, 0.22]),
            [0.05008879, 0.10125, 0.29641509, 0.53971154],
            (),
            id="fine values",
        ),
        pytest.param(
            pytest.raises(ValueError),
            np.array([0.05, 0.25, np.inf, 0.57]),
            np.array([0.13, 0.08, 0.27, 0.22]),
            [],
            (
                (
                    ERROR,
                    "Litter input from plant turnover contains an infinite chemical "
                    "proportion!",
                ),
            ),
            id="infinite turnover proportion",
        ),
        pytest.param(
            pytest.raises(ValueError),
            np.array([0.05, 0.25, 0.3, 0.57]),
            np.array([np.inf, 0.08, 0.27, 0.22]),
            [],
            (
                (
                    ERROR,
                    "Litter input from animal herbivory waste contains an infinite "
                    "chemical proportion!",
                ),
            ),
            id="infinite herbivory waste proportion",
        ),
    ],
)
def test_merge_input_chemical_proportions(
    dummy_litter_data,
    caplog,
    raises,
    turnover_chemical_proportion,
    herbivory_chemical_proportion,
    expected_proportions,
    expected_log,
):
    """Test that function to merge chemical proportions works as expected."""
    from virtual_ecosystem.models.litter.inputs import merge_input_chemical_proportions

    with raises:
        actual_proportions = merge_input_chemical_proportions(
            turnover_mass=dummy_litter_data["leaf_turnover"],
            herbivory_waste_mass=dummy_litter_data["herbivory_waste_leaf_carbon"],
            total_mass=dummy_litter_data["leaf_turnover"]
            + dummy_litter_data["herbivory_waste_leaf_carbon"],
            turnover_chemical_proportion=turnover_chemical_proportion,
            herbivory_waste_chemical_proportion=herbivory_chemical_proportion,
        )
        assert np.allclose(actual_proportions, expected_proportions)

    # Check the error reports
    log_check(caplog, expected_log)
