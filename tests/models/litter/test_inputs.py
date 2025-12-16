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
        "reproduct_meta_split": [0.8462925685, 0.833489905, 0.83196046, 0.8390536408],
        "roots_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
        "woody": [0.0375, 0.0495, 0.0315, 0.0165],
        "above_metabolic": [0.01224844, 0.00402676, 0.00660119, 0.00383300],
        "above_structural": [0.00276656, 0.00092324, 0.00659881, 0.01364200],
        "below_metabolic": [0.00794333, 0.0039855, 7.5365e-5, 0.005106055],
        "below_structural": [0.00555667, 0.0065145, 7.4635e-5, 0.007343945],
        "leaf_mass": [0.013515, 0.0012, 0.011925, 0.0156],
        "root_mass": [0.0135, 0.0105, 0.00015, 0.01245],
        "deadwood_mass": [0.0375, 0.0495, 0.0315, 0.0165],
        "reprod_mass": [0.0015, 0.00375, 0.001275, 0.001875],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "reprod_lignin": [0.01, 0.03, 0.04, 0.02],
        "leaf_nitrogen": [15.00583994, 32.23584906, 39.05894298, 47.80986065],
        "root_nitrogen": [30.3, 45.6, 43.3, 37.1],
        "deadwood_nitrogen": [60.7, 57.9, 73.1, 55.1],
        "reprod_nitrogen": [12.5, 23.8, 15.7, 18.2],
        "leaf_phosphorus": [414.56154, 342.52452, 514.18037, 384.00081],
        "root_phosphorus": [656.7, 450.6, 437.3, 371.9],
        "deadwood_phosphorus": [856.5, 675.4, 933.2, 888.8],
        "reprod_phosphorus": [125.5, 105.0, 145.0, 189.2],
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


def test_convert_to_input_masses_to_rates_per_area(fixture_litter_model):
    """Test function to convert input masses to rates per area."""
    from virtual_ecosystem.models.litter.inputs import (
        convert_to_input_masses_to_rates_per_area,
    )

    expected_input_rate = [0.0375, 0.0495, 0.0315, 0.0165]

    print(fixture_litter_model.data["stem_turnover_cnp"].loc[:, "C"])
    print(fixture_litter_model.grid.cell_area)

    actual_input_rate = convert_to_input_masses_to_rates_per_area(
        input_mass=fixture_litter_model.data["stem_turnover_cnp"].loc[:, "C"],
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
        "reprod_mass": [0.0015, 0.00375, 0.001275, 0.001875],
        "leaf_lignin": [0.05008879, 0.10125, 0.29641509, 0.53971154],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "reprod_lignin": [0.01, 0.03, 0.04, 0.02],
        "leaf_nitrogen": [15.00583994, 32.23584906, 39.05894298, 47.80986065],
        "root_nitrogen": [30.3, 45.6, 43.3, 37.1],
        "deadwood_nitrogen": [60.7, 57.9, 73.1, 55.1],
        "reprod_nitrogen": [12.5, 23.8, 15.7, 18.2],
        "leaf_phosphorus": [414.56154, 342.52452, 514.18037, 384.00081],
        "root_phosphorus": [656.7, 450.6, 437.3, 371.9],
        "deadwood_phosphorus": [856.5, 675.4, 933.2, 888.8],
        "reprod_phosphorus": [125.5, 105.0, 145.0, 189.2],
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
        "reproduct_meta_split": [0.8462925685, 0.833489905, 0.83196046, 0.8390536408],
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
        "above_metabolic": [0.01224844, 0.00402676, 0.00660119, 0.00383300],
        "above_structural": [0.00276656, 0.00092324, 0.00659881, 0.01364200],
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
        lignin_proportion=dummy_litter_data["senesced_leaf_lignin"],
        carbon_nitrogen_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"],
        carbon_phosphorus_ratio=dummy_litter_data["leaf_turnover_c_p_ratio"],
        max_metabolic_fraction=fixture_litter_constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=fixture_litter_constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=fixture_litter_constants.metabolic_split_phosphorus_sensitivity,
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
    caplog, fixture_litter_constants, c_n_ratios, expected_log, request
):
    """Check that pool split functions raises an error if out of bounds data is used."""

    if request.node.callspec.id == "negative_metabolic_flow":
        pytest.skip(
            "Current implementation does not raise an error here. This will be"
            " fixed in Issue #1010."
        )

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
            max_metabolic_fraction=fixture_litter_constants.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=fixture_litter_constants.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=fixture_litter_constants.metabolic_split_phosphorus_sensitivity,
        )

    # Check the error reports
    log_check(caplog, expected_log)


def test_merge_input_lignin_proportions(dummy_litter_data):
    """Test that function to merge lignin proportions works as expected."""
    from virtual_ecosystem.models.litter.inputs import merge_input_lignin_proportions

    expected_proportions = [0.05008879, 0.10125, 0.29641509, 0.53971154]

    actual_proportions = merge_input_lignin_proportions(
        turnover_mass=dummy_litter_data["leaf_turnover"],
        herbivory_waste_mass=dummy_litter_data["herbivory_waste_leaf_carbon"],
        total_mass=dummy_litter_data["leaf_turnover"]
        + dummy_litter_data["herbivory_waste_leaf_carbon"],
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
        mass_1=dummy_litter_data["leaf_turnover"],
        mass_2=dummy_litter_data["herbivory_waste_leaf_carbon"],
        nutrient_ratio_1=dummy_litter_data["leaf_turnover_c_n_ratio"],
        nutrient_ratio_2=dummy_litter_data["herbivory_waste_leaf_nitrogen"],
    )
    assert np.allclose(actual_proportions, expected_proportions)


def test_calculate_input_chemistries(fixture_litter_constants, litter_inputs):
    """Check that calculation of input chemistries is correct."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.inputs import calculate_input_chemistries

    expected_chemistries = {
        "woody_lignin": [0.233, 0.545, 0.612, 0.378],
        "above_structural_lignin": [0.25011178, 0.25345463, 0.54339369, 0.61992378],
        "below_structural_lignin": [0.48590258, 0.56412613, 0.54265483, 0.67810978],
        "woody_nitrogen": [60.7, 57.9, 73.1, 55.1],
        "below_metabolic_nitrogen": [
            20.32269136,
            22.96676383,
            26.06473456,
            19.59251036,
        ],
        "below_structural_nitrogen": [
            101.61345679,
            114.83381916,
            130.32367278,
            97.96255178,
        ],
        "above_metabolic_nitrogen": [12.540983, 21.600478, 20.237902, 15.403147],
        "above_structural_nitrogen": [62.91002, 110.3194, 109.3635, 75.59183],
        "woody_phosphorus": [856.5, 675.4, 933.2, 888.8],
        "below_metabolic_phosphorus": [
            440.4591226,
            226.94788998,
            263.23576031,
            196.40039357,
        ],
        "below_structural_phosphorus": [
            2202.29561299,
            1134.7394499,
            1316.17880156,
            982.00196785,
        ],
        "above_metabolic_phosphorus": [286.886303, 107.015923, 241.802298, 136.049497],
        "above_structural_phosphorus": [
            1488.595406,
            580.6433876,
            1408.378272,
            610.0666667,
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
    expected_concs_above_struct = [0.25011178, 0.25345463, 0.54339369, 0.61992378]
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


def test_calculate_litter_input_nitrogen_ratios(
    fixture_litter_constants, litter_inputs
):
    """Check function to calculate the C:N ratios of input to each litter pool works."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_litter_input_nitrogen_ratios,
    )

    expected_c_n_ratios = {
        "woody_nitrogen": [60.7, 57.9, 73.1, 55.1],
        "below_metabolic_nitrogen": [
            20.32269136,
            22.96676383,
            26.06473456,
            19.59251036,
        ],
        "below_structural_nitrogen": [
            101.61345679,
            114.83381916,
            130.32367278,
            97.96255178,
        ],
        "above_metabolic_nitrogen": [12.540983, 21.600478, 20.237902, 15.403147],
        "above_structural_nitrogen": [62.91002, 110.3194, 109.3635, 75.59183],
    }

    actual_c_n_ratios = calculate_litter_input_nitrogen_ratios(
        litter_inputs=litter_inputs,
        struct_to_meta_nitrogen_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
    )

    assert set(expected_c_n_ratios.keys()) == set(actual_c_n_ratios.keys())

    for key in actual_c_n_ratios.keys():
        assert np.allclose(actual_c_n_ratios[key], expected_c_n_ratios[key])


def test_calculate_litter_input_phosphorus_ratios(
    fixture_litter_constants, litter_inputs
):
    """Check function to calculate the C:P ratios of input to each litter pool works."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_litter_input_phosphorus_ratios,
    )

    expected_c_p_ratios = {
        "woody_phosphorus": [856.5, 675.4, 933.2, 888.8],
        "below_metabolic_phosphorus": [
            440.4591226,
            226.94788998,
            263.23576031,
            196.40039357,
        ],
        "below_structural_phosphorus": [
            2202.29561299,
            1134.7394499,
            1316.17880156,
            982.00196785,
        ],
        "above_metabolic_phosphorus": [286.886303, 107.015923, 241.802298, 136.049497],
        "above_structural_phosphorus": [
            1488.595406,
            580.6433876,
            1408.378272,
            610.0666667,
        ],
    }

    actual_c_p_ratios = calculate_litter_input_phosphorus_ratios(
        litter_inputs=litter_inputs,
        struct_to_meta_phosphorus_ratio=fixture_litter_constants.structural_to_metabolic_p_ratio,
    )

    assert set(expected_c_p_ratios.keys()) == set(actual_c_p_ratios.keys())

    for key in actual_c_p_ratios.keys():
        assert np.allclose(actual_c_p_ratios[key], expected_c_p_ratios[key])


def test_calculate_nutrient_split_between_litter_pools(
    dummy_litter_data, fixture_litter_constants, litter_inputs
):
    """Check the function to calculate the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_nutrient_split_between_litter_pools,
    )

    expected_meta_c_n = np.array([20.32269136, 22.96676383, 26.06473456, 19.59251036])
    expected_struct_c_n = np.array([101.6134568, 114.83381915, 130.3236728, 97.9625518])

    actual_meta_c_n, actual_struct_c_n = calculate_nutrient_split_between_litter_pools(
        input_c_nut_ratio=dummy_litter_data["root_turnover_cnp"].loc[:, "C"]
        / dummy_litter_data["root_turnover_cnp"].loc[:, "N"],
        metabolic_split=litter_inputs.roots_meta_split,
        struct_to_meta_nutrient_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
    )

    # Standard checks of the produced values
    assert np.allclose(actual_meta_c_n, expected_meta_c_n)
    assert np.allclose(actual_struct_c_n, expected_struct_c_n)
    # Check that expected ratio is actually preserved by the function
    assert np.allclose(
        expected_struct_c_n,
        expected_meta_c_n * fixture_litter_constants.structural_to_metabolic_n_ratio,
    )
    # Check that weighted sum of the two new C:N ratios is compatible with the original
    # C:N ratio
    assert np.allclose(
        dummy_litter_data["root_turnover_cnp"].loc[:, "C"]
        / dummy_litter_data["root_turnover_cnp"].loc[:, "N"],
        1
        / (
            (litter_inputs.roots_meta_split / actual_meta_c_n)
            + ((1 - litter_inputs.roots_meta_split) / actual_struct_c_n)
        ),
    )
