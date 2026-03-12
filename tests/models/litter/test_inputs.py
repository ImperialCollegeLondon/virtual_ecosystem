"""Test module for models.litter.inputs.py."""

from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check


def test_determine_all_plant_to_litter_flows(
    dummy_litter_data, fixture_litter_constants
):
    """Test that function to determine plant to litter flows works correctly."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.inputs import LitterInputs

    expected_inputs = {
        "leaves_meta_split": [0.8123565, 0.75097557, 0.46460743, 0.14485736],
        "roots_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
        "woody": [0.0375, 0.0495, 0.0315, 0.0165],
        "above_metabolic": [0.010979, 0.00090117, 0.00554044, 0.00225977],
        "above_structural": [0.002536, 0.00029883, 0.00638456, 0.01334023],
        "below_metabolic": [0.00794333, 0.0039855, 7.5365e-5, 0.005106055],
        "below_structural": [0.00555667, 0.0065145, 7.4635e-5, 0.007343945],
        "leaf_mass": [0.013515, 0.0012, 0.011925, 0.0156],
        "root_mass": [0.0135, 0.0105, 0.00015, 0.01245],
        "deadwood_mass": [0.0375, 0.0495, 0.0315, 0.0165],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "leaf_nitrogen": [0.00090064935, 3.72256365e-5, 0.00030530780, 0.00032629252],
        "root_nitrogen": [0.000445545, 0.000230263, 3.464203e-6, 0.000335580],
        "deadwood_nitrogen": [0.00061779, 0.00085492, 0.00043092, 0.00029946],
        "leaf_phosphorus": [3.260071e-5, 3.503399e-6, 2.319225e-5, 4.062491e-5],
        "root_phosphorus": [2.0557332e-5, 2.3302264e-5, 3.4301395e-7, 3.3476741e-5],
        "deadwood_phosphorus": [4.3782837e-5, 7.3289902e-5, 3.3754822e-5, 1.8564356e-5],
    }

    litter_inputs = LitterInputs.create_from_data(
        data=dummy_litter_data, constants=fixture_litter_constants, update_interval=2.0
    )
    # Check that the right sort of object has been created
    assert isinstance(litter_inputs, LitterInputs)

    # Then convert to a dict to check the values
    litter_inputs = asdict(litter_inputs)

    # Check that all keys match and have correct values for both dictionaries
    assert set(expected_inputs.keys()) == set(litter_inputs.keys())

    for key in litter_inputs.keys():
        assert np.allclose(litter_inputs[key], expected_inputs[key])


def test_convert_to_input_masses_to_rates_per_area(
    fixture_litter_model, dummy_litter_data
):
    """Test function to convert input masses to rates per area."""
    from virtual_ecosystem.models.litter.inputs import (
        convert_to_input_masses_to_rates_per_area,
    )

    expected_input_rate = [0.0375, 0.0495, 0.0315, 0.0165]

    actual_input_rate = convert_to_input_masses_to_rates_per_area(
        input_mass=dummy_litter_data["stem_turnover_cnp"].loc[:, "C"],
        cell_area=fixture_litter_model.grid.cell_area,
        update_interval=2.0,
    )

    assert np.allclose(actual_input_rate, expected_input_rate)


def test_combine_input_sources(dummy_litter_data):
    """Test that function to combine input sources works as expected."""
    from virtual_ecosystem.models.litter.inputs import combine_input_sources

    expected_combined = {
        "leaf_mass": [0.013515, 0.0012, 0.011925, 0.0156],
        "root_mass": [0.0135, 0.0105, 0.00015, 0.01245],
        "deadwood_mass": [0.0375, 0.0495, 0.0315, 0.0165],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "leaf_nitrogen": [0.00090064935, 3.72256365e-5, 0.00030530780, 0.00032629252],
        "root_nitrogen": [0.000445545, 0.000230263, 3.464203e-6, 0.000335580],
        "deadwood_nitrogen": [0.00061779, 0.00085492, 0.00043092, 0.00029946],
        "leaf_phosphorus": [3.260071e-5, 3.503399e-6, 2.319225e-5, 4.062491e-5],
        "root_phosphorus": [2.0557332e-5, 2.3302264e-5, 3.4301395e-7, 3.3476741e-5],
        "deadwood_phosphorus": [4.3782837e-5, 7.3289902e-5, 3.3754822e-5, 1.8564356e-5],
    }

    actual_combined = combine_input_sources(dummy_litter_data, update_interval=2.0)

    assert set(expected_combined.keys()) == set(actual_combined.keys())

    for key in actual_combined.keys():
        assert np.allclose(actual_combined[key], expected_combined[key])


def test_calculate_metabolic_proportions_of_input(
    total_litter_input, fixture_litter_constants
):
    """Test that function to calculate metabolic input proportions works as expected."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_metabolic_proportions_of_input,
    )

    expected_proportions = {
        "leaves_meta_split": [0.8123565, 0.75097557, 0.46460743, 0.14485736],
        "roots_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
    }

    actual_proportions = calculate_metabolic_proportions_of_input(
        total_input=total_litter_input, constants=fixture_litter_constants
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
        "woody": [0.0375, 0.0495, 0.0315, 0.0165],
        "above_metabolic": [0.010979, 0.00090117, 0.00554044, 0.00225977],
        "above_structural": [0.002536, 0.00029883, 0.00638456, 0.01334023],
        "below_metabolic": [0.00794333, 0.0039855, 7.5365e-5, 0.005106055],
        "below_structural": [0.00555667, 0.0065145, 7.4635e-5, 0.007343945],
    }

    actual_inputs = partion_plant_inputs_between_pools(
        total_input=total_litter_input,
        metabolic_splits=metabolic_splits,
    )

    assert set(expected_inputs.keys()) == set(actual_inputs.keys())

    for key in actual_inputs.keys():
        assert np.allclose(actual_inputs[key], expected_inputs[key])


def test_split_pool_into_metabolic_and_structural_litter(
    dummy_litter_data, fixture_litter_constants
):
    """Check function to split input biomass between litter pools works as expected."""

    from virtual_ecosystem.models.litter.inputs import (
        split_pool_into_metabolic_and_structural_litter,
    )

    expected_split = [0.812403025, 0.640197595, 0.424077745, 0.0089426731]

    actual_split = split_pool_into_metabolic_and_structural_litter(
        input_carbon=dummy_litter_data["foliage_turnover_cnp"].loc[:, "C"],
        lignin_proportion=dummy_litter_data["senesced_leaf_lignin"],
        input_nitrogen=dummy_litter_data["foliage_turnover_cnp"].loc[:, "N"],
        input_phosphorus=dummy_litter_data["foliage_turnover_cnp"].loc[:, "P"],
        max_metabolic_fraction=fixture_litter_constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=fixture_litter_constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=fixture_litter_constants.metabolic_split_phosphorus_sensitivity,
    )

    assert np.allclose(actual_split, expected_split)


@pytest.mark.parametrize(
    "lignin_proportions",
    [
        pytest.param(
            np.array([-0.5, 0.4, 0.35, 0.23]),
            id="negative_lignin",
        ),
        pytest.param(
            np.array([0.5, 1.4, 0.35, 0.23]),
            id="lignin_above_one",
        ),
    ],
)
def test_split_pool_into_metabolic_and_structural_litter_bad_data(
    caplog, fixture_litter_constants, lignin_proportions, dummy_litter_data
):
    """Check that pool split functions raises an error if out of bounds data is used."""

    from virtual_ecosystem.models.litter.inputs import (
        split_pool_into_metabolic_and_structural_litter,
    )

    with pytest.raises(ValueError):
        split_pool_into_metabolic_and_structural_litter(
            input_carbon=dummy_litter_data["foliage_turnover_cnp"].loc[:, "C"],
            lignin_proportion=lignin_proportions,
            input_nitrogen=dummy_litter_data["foliage_turnover_cnp"].loc[:, "N"],
            input_phosphorus=dummy_litter_data["foliage_turnover_cnp"].loc[:, "P"],
            max_metabolic_fraction=fixture_litter_constants.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=fixture_litter_constants.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=fixture_litter_constants.metabolic_split_phosphorus_sensitivity,
        )

    expected_log = ((ERROR, "Lignin proportion not between 0 and 1 (inclusive)!"),)

    # Check the error reports
    log_check(caplog, expected_log)


def test_merge_input_lignin_proportions(dummy_litter_data):
    """Test that function to merge lignin proportions works as expected."""
    from virtual_ecosystem.models.litter.inputs import merge_input_lignin_proportions

    expected_proportions = [0.05008879, 0.10125, 0.29641509, 0.53971154]

    actual_proportions = merge_input_lignin_proportions(
        turnover_mass=dummy_litter_data["foliage_turnover_cnp"].loc[:, "C"],
        herbivory_waste_mass=dummy_litter_data["herbivory_waste_leaf_cnp"].loc[:, "C"],
        total_mass=dummy_litter_data["foliage_turnover_cnp"].loc[:, "C"]
        + dummy_litter_data["herbivory_waste_leaf_cnp"].loc[:, "C"],
        turnover_lignin_proportion=dummy_litter_data["senesced_leaf_lignin"],
        herbivory_waste_lignin_proportion=dummy_litter_data[
            "herbivory_waste_leaf_lignin"
        ],
    )
    assert np.allclose(actual_proportions, expected_proportions)


def test_average_nutrient_ratios(dummy_litter_data):
    """Test that function to average nutrient ratios works as expected."""
    from virtual_ecosystem.models.litter.inputs import average_nutrient_ratios

    expected_proportions = [15.00583994, 32.23584906, 39.05894298, 47.80986065]

    actual_proportions = average_nutrient_ratios(
        mass_1=dummy_litter_data["foliage_turnover_cnp"].loc[:, "C"].to_numpy(),
        mass_2=dummy_litter_data["herbivory_waste_leaf_cnp"].loc[:, "C"].to_numpy(),
        nutrient_ratio_1=(
            dummy_litter_data["foliage_turnover_cnp"].loc[:, "C"]
            / dummy_litter_data["foliage_turnover_cnp"].loc[:, "N"]
        ),
        nutrient_ratio_2=(
            dummy_litter_data["herbivory_waste_leaf_cnp"].loc[:, "C"]
            / dummy_litter_data["herbivory_waste_leaf_cnp"].loc[:, "N"]
        ),
    )
    assert np.allclose(actual_proportions, expected_proportions)


def test_calculate_input_chemistries(fixture_litter_constants, litter_inputs):
    """Check that calculation of input chemistries is correct."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.inputs import calculate_input_chemistries

    expected_chemistries = {
        "woody_lignin": [0.233, 0.545, 0.612, 0.378],
        "above_structural_lignin": [0.26693592, 0.40658661, 0.55364065, 0.63113627],
        "below_structural_lignin": [0.48590258, 0.56412613, 0.54265483, 0.67810978],
        "woody_nitrogen": [0.00061779, 0.00085492, 0.00043092, 0.00029946],
        "below_metabolic_nitrogen": [
            0.000390860,
            0.000173533,
            2.891455e-6,
            0.000260613,
        ],
        "below_structural_nitrogen": [
            5.4684391e-5,
            5.6729804e-5,
            5.7268951e-7,
            7.4966861e-5,
        ],
        "above_metabolic_nitrogen": [
            0.00086087927,
            3.49103455e-5,
            0.00024812256,
            0.00014962926,
        ],
        "above_structural_nitrogen": [
            3.977028208e-5,
            2.315269818e-6,
            5.718511268e-5,
            0.000176663005,
        ],
        "woody_phosphorus": [4.3782837e-5, 7.3289902e-5, 3.3754822e-5, 1.8564356e-5],
        "below_metabolic_phosphorus": [
            1.80342047e-5,
            1.75613001e-5,
            2.86302286e-7,
            2.59981913e-5,
        ],
        "below_structural_phosphorus": [
            2.5231263e-6,
            5.7409655e-6,
            5.6705821e-8,
            7.4785442e-6,
        ],
        "above_metabolic_phosphorus": [
            3.11611524e-5,
            3.28550094e-6,
            1.88482594e-5,
            1.86295285e-5,
        ],
        "above_structural_phosphorus": [
            1.4395607e-6,
            2.1789590e-7,
            4.3439814e-6,
            2.1995354e-5,
        ],
    }

    actual_chemistries = calculate_input_chemistries(
        litter_inputs=litter_inputs,
        struct_to_meta_nitrogen_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
        struct_to_meta_phosphorus_ratio=fixture_litter_constants.structural_to_metabolic_p_ratio,
    )

    # Convert to a dict to check the values
    actual_chemistries = asdict(actual_chemistries)

    # Check that all keys match and have correct values for both dictionaries
    assert set(expected_chemistries.keys()) == set(actual_chemistries.keys())

    for key in actual_chemistries.keys():
        assert np.allclose(actual_chemistries[key], expected_chemistries[key])


def test_calculate_litter_input_lignin_concentrations(litter_inputs):
    """Check calculation of lignin concentrations of each plant flow to litter."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_litter_input_lignin_concentrations,
    )

    expected_woody = [0.233, 0.545, 0.612, 0.378]
    expected_concs_above_struct = [0.26693592, 0.40658661, 0.55364065, 0.63113627]
    expected_concs_below_struct = [0.48590258, 0.56412613, 0.54265483, 0.67810978]

    actual_concs = calculate_litter_input_lignin_concentrations(
        litter_inputs=litter_inputs,
    )

    assert np.allclose(actual_concs["woody_lignin"], expected_woody)
    assert np.allclose(
        actual_concs["above_structural_lignin"], expected_concs_above_struct
    )
    assert np.allclose(
        actual_concs["below_structural_lignin"], expected_concs_below_struct
    )


def test_calculate_litter_input_nutrient_masses(
    fixture_litter_constants, litter_inputs
):
    """Check calculation of the input nutrients masses to each litter pool."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_litter_input_nutrient_masses,
    )

    expected_nutrient_masses = {
        "woody_nitrogen": [0.00061779, 0.00085492, 0.00043092, 0.00029946],
        "below_metabolic_nitrogen": [
            0.000390860,
            0.000173533,
            2.891455e-6,
            0.000260613,
        ],
        "below_structural_nitrogen": [
            5.4684391e-5,
            5.6729804e-5,
            5.7268951e-7,
            7.4966861e-5,
        ],
        "above_metabolic_nitrogen": [
            0.00086087927,
            3.49103455e-5,
            0.00024812256,
            0.00014962926,
        ],
        "above_structural_nitrogen": [
            3.977028208e-5,
            2.315269818e-6,
            5.718511268e-5,
            0.000176663005,
        ],
    }

    actual_nutrient_masses = calculate_litter_input_nutrient_masses(
        litter_inputs=litter_inputs,
        struct_to_meta_nutrient_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
        nutrient="nitrogen",
    )

    assert set(expected_nutrient_masses.keys()) == set(actual_nutrient_masses.keys())

    for key in actual_nutrient_masses.keys():
        assert np.allclose(actual_nutrient_masses[key], expected_nutrient_masses[key])


def test_calculate_litter_input_nutrient_masses_bad_input(
    caplog, fixture_litter_constants, litter_inputs
):
    """Check input nutrient calculation fails gracefully for incorrect nutrients."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_litter_input_nutrient_masses,
    )

    with pytest.raises(ValueError):
        _ = calculate_litter_input_nutrient_masses(
            litter_inputs=litter_inputs,
            struct_to_meta_nutrient_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
            nutrient="oxygen",
        )

    expected_log = ((ERROR, "oxygen is not an element we currently track!"),)

    # Check the error reports
    log_check(caplog, expected_log)


def test_calculate_nutrient_split_between_litter_pools(
    dummy_litter_data, fixture_litter_constants, litter_inputs
):
    """Check the function to calculate the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_nutrient_split_between_litter_pools,
    )

    expected_n_meta = np.array([6.331932287, 2.81123962, 0.0468426692, 4.22192613])
    expected_n_struct = np.array([0.8858875316, 0.91902302, 0.009277350, 1.214462735])

    actual_n_meta, actual_n_struct = calculate_nutrient_split_between_litter_pools(
        input_carbon_mass=dummy_litter_data["root_turnover_cnp"].loc[:, "C"],
        input_nutrient_mass=dummy_litter_data["root_turnover_cnp"].loc[:, "N"],
        metabolic_split=litter_inputs.roots_meta_split,
        struct_to_meta_nutrient_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
    )

    # Standard checks of the produced values
    assert np.allclose(actual_n_meta, expected_n_meta)
    assert np.allclose(actual_n_struct, expected_n_struct)
