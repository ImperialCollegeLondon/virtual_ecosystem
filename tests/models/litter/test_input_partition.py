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
    expected_above_meta = [0.02512875, 0.006499185, 0.0166206948, 0.022270755]
    expected_above_struct = [0.00487125, 0.001300815, 0.0069293052, 0.009979245]
    expected_below_meta = [0.02097684, 0.01181712, 0.0002064486, 0.016306512]
    expected_below_struct = [0.00602316, 0.00918288, 9.35514e-5, 0.008593488]

    actual_splits = partion_plant_inputs_between_pools(
        deadwood_production_rate=dummy_litter_data["deadwood_production"],
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

    expected_split = [0.8365, 0.73525, 0.68962, 0.67045]

    actual_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=dummy_litter_data["leaf_turnover_lignin"],
        carbon_nitrogen_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"],
        max_metabolic_fraction=LitterConsts.max_metabolic_fraction_of_input,
        split_sensitivity=LitterConsts.structural_metabolic_split_sensitivity,
    )

    assert np.allclose(actual_split, expected_split)


def test_split_pool_into_metabolic_and_structural_litter_bad_data(caplog):
    """Check that pool split functions raises an error if out of bounds data is used."""

    from virtual_ecosystem.models.litter.input_partition import (
        split_pool_into_metabolic_and_structural_litter,
    )

    # C:N ratio of >400 is far too high for the function to behave sensibly
    lignin_proportions = np.array([0.5, 0.4, 0.35, 0.23])
    c_n_ratios = np.array([34.2, 55.5, 37.1, 400.7])

    with pytest.raises(ValueError):
        split_pool_into_metabolic_and_structural_litter(
            lignin_proportion=lignin_proportions,
            carbon_nitrogen_ratio=c_n_ratios,
            max_metabolic_fraction=LitterConsts.max_metabolic_fraction_of_input,
            split_sensitivity=LitterConsts.structural_metabolic_split_sensitivity,
        )

    # Check the error reports
    expected_log = (
        (
            ERROR,
            "Fraction of input biomass going to metabolic pool has dropped below zero!",
        ),
    )

    log_check(caplog, expected_log)
