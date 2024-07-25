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
        "leaves": [0.8365, 0.73525, 0.61726, 0.261076],
        "reproductive": [0.84775, 0.837148, 0.838696, 0.843448],
        "roots": [0.74092, 0.56272, 0.639562, 0.58288],
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
    expected_above_meta = [0.02512875, 0.006499185, 0.01510113, 0.0106036]
    expected_above_struct = [0.00487125, 0.001300815, 0.00844887, 0.0216464]
    expected_below_meta = [0.02000484, 0.01181712, 0.00019187, 0.01451371]
    expected_below_struct = [0.00699516, 0.00918288, 0.00010813, 0.01038629]

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


def test_calculate_litter_input_lignin_concentrations(dummy_litter_data, plant_inputs):
    """Check calculation of lignin concentrations of each plant flow to litter."""

    from virtual_ecosystem.models.litter.input_partition import (
        calculate_litter_input_lignin_concentrations,
    )

    expected_woody = [0.233, 0.545, 0.612, 0.378]
    expected_concs_above_struct = [0.28329484, 0.23062465, 0.75773447, 0.75393599]
    expected_concs_below_struct = [0.77196233, 0.80040249, 0.74908861, 0.95895666]

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
        plant_input_below_struct=plant_inputs["below_ground_structural"],
        plant_input_above_struct=plant_inputs["above_ground_structural"],
    )

    assert np.allclose(actual_concs["woody"], expected_woody)
    assert np.allclose(actual_concs["above_structural"], expected_concs_above_struct)
    assert np.allclose(actual_concs["below_structural"], expected_concs_below_struct)


def test_calculate_litter_input_nitrogen_ratios(dummy_litter_data, metabolic_splits):
    """Check function to calculate the C:N ratios of input to each litter pool works."""
    from virtual_ecosystem.models.litter.input_partition import (
        calculate_litter_input_nitrogen_ratios,
    )

    expected_c_n_ratios = {
        "woody": [60.7, 57.9, 73.1, 55.1],
        "below_metabolic": [14.879783, 16.587126, 17.733169, 13.903046],
        "below_structural": [74.398916, 82.935630, 88.665843, 69.515230],
        "above_metabolic": [8.9373399, 14.343140, 15.968877, 13.520689],
        "above_structural": [44.735092, 71.440811, 83.323241, 72.103527],
    }

    actual_c_n_ratios = calculate_litter_input_nitrogen_ratios(
        deadwood_c_n_ratio=dummy_litter_data["deadwood_c_n_ratio"],
        root_turnover_c_n_ratio=dummy_litter_data["root_turnover_c_n_ratio"],
        leaf_turnover_c_n_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"],
        reproduct_turnover_c_n_ratio=dummy_litter_data[
            "plant_reproductive_tissue_turnover_c_n_ratio"
        ],
        leaf_turnover=dummy_litter_data["leaf_turnover"],
        reproduct_turnover=dummy_litter_data["plant_reproductive_tissue_turnover"],
        metabolic_splits=metabolic_splits,
        struct_to_meta_nitrogen_ratio=LitterConsts.structural_to_metabolic_n_ratio,
    )

    assert set(expected_c_n_ratios.keys()) == set(actual_c_n_ratios.keys())

    for key in actual_c_n_ratios.keys():
        assert np.allclose(actual_c_n_ratios[key], expected_c_n_ratios[key])


def test_calculate_nutrient_split_between_litter_pools(
    dummy_litter_data, metabolic_splits
):
    """Check the function to calculate the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.input_partition import (
        calculate_nutrient_split_between_litter_pools,
    )

    expected_meta_c_n = np.array([14.879783, 16.587126, 17.733169, 13.903046])
    expected_struct_c_n = np.array([74.398916, 82.935630, 88.665843, 69.515230])

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
