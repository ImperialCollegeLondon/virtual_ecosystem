"""Test module for models.litter.input_partition.py."""

from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_ecosystem.models.litter.constants import LitterConsts


def test_partion_plant_inputs_between_pools(dummy_litter_data):
    """Check function to partition inputs into litter pools works as expected."""

    from virtual_ecosystem.models.litter.input_partition import (
        partion_plant_inputs_between_pools,
    )

    expected_woody = [0.075, 0.099, 0.063, 0.033]
    expected_above_meta = [0.02512875, 0.006499185, 0.01510113, 0.0106036]
    expected_above_struct = [0.00487125, 0.001300815, 0.00844887, 0.0216464]
    expected_below_meta = [0.02000484, 0.01181712, 0.00019187, 0.01451371]
    expected_below_struct = [0.00699516, 0.00918288, 0.00010813, 0.01038629]

    actual_splits = partion_plant_inputs_between_pools(
        deadwood_production=dummy_litter_data["deadwood_production"],
        leaf_turnover=dummy_litter_data["leaf_turnover"],
        reproduct_turnover=dummy_litter_data["plant_reproductive_tissue_turnover"],
        root_turnover=dummy_litter_data["root_turnover"],
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
        constants=LitterConsts,
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

    expected_split = [0.8365, 0.73525, 0.61726, 0.261076]

    actual_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=dummy_litter_data["leaf_turnover_lignin"],
        carbon_nitrogen_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"],
        max_metabolic_fraction=LitterConsts.max_metabolic_fraction_of_input,
        split_sensitivity=LitterConsts.structural_metabolic_split_sensitivity,
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

    with pytest.raises(ValueError):
        split_pool_into_metabolic_and_structural_litter(
            lignin_proportion=lignin_proportions,
            carbon_nitrogen_ratio=c_n_ratios,
            max_metabolic_fraction=LitterConsts.max_metabolic_fraction_of_input,
            split_sensitivity=LitterConsts.structural_metabolic_split_sensitivity,
        )

    # Check the error reports
    log_check(caplog, expected_log)


def test_calculate_litter_input_lignin_concentrations(dummy_litter_data):
    """Check calculation of lignin concentrations of each plant flow to litter."""

    from virtual_ecosystem.models.litter.input_partition import (
        calculate_litter_input_lignin_concentrations,
    )

    below_struct_input = [0.00699516, 0.00918288, 0.00010813, 0.01038629]
    above_struct_input = [0.00487125, 0.001300815, 0.00844887, 0.0216464]

    expected_woody = [0.233, 0.545, 0.612, 0.378]
    expected_concs_above_struct = [0.28329484, 0.23062465, 0.75773447, 0.75393599]
    expected_concs_below_struct = [0.7719623, 0.8004025, 0.7490983, 0.9589565]

    actual_concs = calculate_litter_input_lignin_concentrations(
        deadwood_lignin_proportion=dummy_litter_data["deadwood_lignin"],
        root_turnover_lignin_proportion=dummy_litter_data["root_turnover_lignin"],
        leaf_turnover_lignin_proportion=dummy_litter_data["leaf_turnover_lignin"],
        reproduct_turnover_lignin_proportion=dummy_litter_data[
            "plant_reproductive_tissue_turnover_lignin"
        ],
        root_turnover=dummy_litter_data["root_turnover"],
        leaf_turnover=dummy_litter_data["leaf_turnover"],
        reproduct_turnover=dummy_litter_data["plant_reproductive_tissue_turnover"],
        plant_input_below_struct=below_struct_input,
        plant_input_above_struct=above_struct_input,
    )

    assert np.allclose(actual_concs["woody"], expected_woody)
    assert np.allclose(actual_concs["above_structural"], expected_concs_above_struct)
    assert np.allclose(actual_concs["below_structural"], expected_concs_below_struct)
