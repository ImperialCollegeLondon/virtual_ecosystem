"""Test module for models.litter.input_partition.py."""

from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_ecosystem.models.litter.constants import LitterConsts


def test_calculate_metabolic_proportions_of_input(dummy_litter_data):
    """Test that function to calculate metabolic input proportions works as expected."""

    from virtual_ecosystem.models.litter.input_partition import (
        calculate_metabolic_proportions_of_input,
    )

    expected_proportions = {
        "leaves": [0.812403025, 0.640197595, 0.424077745, 0.0089426731],
        "reproductive": [0.8462925685, 0.833489905, 0.83196046, 0.8390536408],
        "roots": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
    }

    actual_proportions = calculate_metabolic_proportions_of_input(
        leaf_turnover_lignin_proportion=dummy_litter_data["leaf_turnover_lignin"],
        reproduct_turnover_lignin_proportion=dummy_litter_data[
            "plant_reproductive_tissue_turnover_lignin"
        ],
        root_turnover_lignin_proportion=dummy_litter_data["root_turnover_lignin"],
        leaf_turnover_c_n_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"],
        reproduct_turnover_c_n_ratio=dummy_litter_data[
            "plant_reproductive_tissue_turnover_c_n_ratio"
        ],
        root_turnover_c_n_ratio=dummy_litter_data["root_turnover_c_n_ratio"],
        leaf_turnover_c_p_ratio=dummy_litter_data["leaf_turnover_c_p_ratio"],
        reproduct_turnover_c_p_ratio=dummy_litter_data[
            "plant_reproductive_tissue_turnover_c_p_ratio"
        ],
        root_turnover_c_p_ratio=dummy_litter_data["root_turnover_c_p_ratio"],
        constants=LitterConsts,
    )

    assert set(expected_proportions.keys()) == set(actual_proportions.keys())

    for key in actual_proportions.keys():
        assert np.allclose(actual_proportions[key], expected_proportions[key])


def test_partion_plant_inputs_between_pools(dummy_litter_data, metabolic_splits):
    """Check function to partition inputs into litter pools works as expected."""

    from virtual_ecosystem.models.litter.input_partition import (
        partion_plant_inputs_between_pools,
    )

    expected_woody = [0.075, 0.099, 0.063, 0.033]
    expected_above_meta = [0.02447376, 0.00644323, 0.01102713, 0.00340132]
    expected_above_struct = [0.00552624, 0.00135677, 0.01252287, 0.02884868]
    expected_below_meta = [0.01588666, 0.00797100, 0.00015073, 0.01021211]
    expected_below_struct = [0.01111334, 0.013029, 0.00014927, 0.01468789]

    actual_splits = partion_plant_inputs_between_pools(
        deadwood_production=dummy_litter_data["deadwood_production"],
        leaf_turnover=dummy_litter_data["leaf_turnover"],
        reproduct_turnover=dummy_litter_data["plant_reproductive_tissue_turnover"],
        root_turnover=dummy_litter_data["root_turnover"],
        metabolic_splits=metabolic_splits,
    )

    assert np.allclose(actual_splits["woody"], expected_woody)
    assert np.allclose(actual_splits["above_ground_metabolic"], expected_above_meta)
    assert np.allclose(actual_splits["above_ground_structural"], expected_above_struct)
    assert np.allclose(actual_splits["below_ground_metabolic"], expected_below_meta)
    assert np.allclose(actual_splits["below_ground_structural"], expected_below_struct)


def test_split_pool_into_metabolic_and_structural_litter(dummy_litter_data):
    """Check function to split input biomass between litter pools works as expected."""

    from virtual_ecosystem.models.litter.input_partition import (
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

    from virtual_ecosystem.models.litter.input_partition import (
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
