"""Test module for models.litter.inputs.py."""

from logging import ERROR

import numpy as np
import pytest
from xarray import DataArray

from tests.conftest import log_check


def test_determine_all_plant_to_litter_flows(
    dummy_litter_data, fixture_litter_constants
):
    """Test that function to determine plant to litter flows works correctly."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.inputs import LitterInputs

    expected_inputs = {
        "leaf_meta_split": [0.81240302, 0.64019755, 0.42407771, 0.00894268],
        "root_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
        "subcanopy_meta_split": [0.82815, 0.57, 0.0, 0.827026],
        "herbivore_waste_above_meta_split": [
            0.7638626,
            0.7697267,
            0.6327571,
            0.6741623,
        ],
        "herbivore_waste_below_meta_split": [0.211658, 0.488244, 0.181836, 0.0],
        "woody": [0.0375, 0.0495, 0.0315, 0.0165],
        "above_metabolic": [0.01106943, 0.00109058, 0.00535450, 0.00163240],
        "above_structural": [0.002554888, 0.000436330, 0.006572925, 0.014686861],
        "below_metabolic": [0.00794558, 0.00425741, 0.00027294, 0.00510606],
        "below_structural": [0.005565040, 0.006799504, 0.000963604, 0.007501166],
        "leaf_lignin": [0.05, 0.25, 0.3, 0.57],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "subcanopy_lignin": [0.05, 0.43, 0.84, 0.01],
        "herbivore_waste_above_lignin": [0.13, 0.08, 0.27, 0.22],
        "herbivore_waste_below_lignin": [0.33, 0.089, 0.46, 0.35],
    }
    # Some expected inputs are triplets so need to be stored as such
    expected_inputs["leaf_mass"] = DataArray(
        data=np.stack(
            [
                [0.0135, 0.00015, 0.0105, 0.01425],
                [0.0009, 5.882353e-6, 0.0002436195, 0.000248258],
                [3.253012e-5, 4.581549e-7, 1.893598e-5, 3.741140e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_inputs["root_mass"] = DataArray(
        data=np.stack(
            [
                [0.0135, 0.0105, 0.00015, 0.01245],
                [0.000445545, 0.000230263, 3.464203e-6, 0.000335580],
                [2.0557332e-5, 2.3302264e-5, 3.4301395e-7, 3.3476741e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_inputs["deadwood_mass"] = DataArray(
        data=np.stack(
            [
                [0.0375, 0.0495, 0.0315, 0.0165],
                [0.00061779, 0.00085492, 0.00043092, 0.00029946],
                [4.3782837e-5, 7.3289902e-5, 3.3754822e-5, 1.8564356e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_inputs["subcanopy_mass"] = DataArray(
        data=np.stack(
            [
                [0.000109321, 0.000326914, 2.419753e-6, 0.000719259],
                [4.0691358e-5, 2.1271605e-5, 8.4629630e-8, 7.3580247e-6],
                [3.2666667e-7, 1.3919753e-6, 1.7549383e-9, 1.5530864e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_inputs["herbivore_waste_above_mass"] = DataArray(
        data=np.stack(
            [
                [1.5e-5, 0.00105, 0.001425, 0.00135],
                [6.493210e-7, 3.134327e-5, 6.168833e-5, 7.803469e-5],
                [7.058827e-8, 3.045241e-6, 4.256272e-6, 3.213519e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_inputs["herbivore_waste_below_mass"] = DataArray(
        data=np.stack(
            [
                [1.0617284e-5, 0.0005569136, 0.0010865432, 0.0001572222],
                [3.64197531e-7, 2.79876543e-6, 1.77043210e-5, 3.28395062e-7],
                [8.74691358e-9, 1.33919753e-6, 3.62753086e-6, 1.94327160e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )

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
        input_mass=dummy_litter_data["stem_turnover_cnp"].sel(element="C"),
        cell_area=fixture_litter_model.grid.cell_area,
        update_interval=2.0,
    )

    assert np.allclose(actual_input_rate, expected_input_rate)


def test_combine_input_sources(dummy_litter_data):
    """Test that function to combine input sources works as expected."""
    from virtual_ecosystem.models.litter.inputs import combine_input_sources

    expected_combined = {
        "leaf_lignin": [0.05, 0.25, 0.3, 0.57],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "subcanopy_lignin": [0.05, 0.43, 0.84, 0.01],
        "herbivore_waste_above_lignin": [0.13, 0.08, 0.27, 0.22],
        "herbivore_waste_below_lignin": [0.33, 0.089, 0.46, 0.35],
    }
    # Some expected inputs are triplets so need to be stored as such
    expected_combined["leaf_mass"] = DataArray(
        data=np.stack(
            [
                [0.0135, 0.00015, 0.0105, 0.01425],
                [0.0009, 5.882353e-6, 0.0002436195, 0.000248258],
                [3.253012e-5, 4.581549e-7, 1.893598e-5, 3.741140e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_combined["root_mass"] = DataArray(
        data=np.stack(
            [
                [0.0135, 0.0105, 0.00015, 0.01245],
                [0.000445545, 0.000230263, 3.464203e-6, 0.000335580],
                [2.0557332e-5, 2.3302264e-5, 3.4301395e-7, 3.3476741e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_combined["deadwood_mass"] = DataArray(
        data=np.stack(
            [
                [0.0375, 0.0495, 0.0315, 0.0165],
                [0.00061779, 0.00085492, 0.00043092, 0.00029946],
                [4.3782837e-5, 7.3289902e-5, 3.3754822e-5, 1.8564356e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_combined["subcanopy_mass"] = DataArray(
        data=np.stack(
            [
                [0.000109321, 0.000326914, 2.419753e-6, 0.000719259],
                [4.0691358e-5, 2.1271605e-5, 8.4629630e-8, 7.3580247e-6],
                [3.2666667e-7, 1.3919753e-6, 1.7549383e-9, 1.5530864e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_combined["herbivore_waste_above_mass"] = DataArray(
        data=np.stack(
            [
                [1.5e-5, 0.00105, 0.001425, 0.00135],
                [6.493210e-7, 3.134327e-5, 6.168833e-5, 7.803469e-5],
                [7.058827e-8, 3.045241e-6, 4.256272e-6, 3.213519e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )
    expected_combined["herbivore_waste_below_mass"] = DataArray(
        data=np.stack(
            [
                [1.0617284e-5, 0.0005569136, 0.0010865432, 0.0001572222],
                [3.64197531e-7, 2.79876543e-6, 1.77043210e-5, 3.28395062e-7],
                [8.74691358e-9, 1.33919753e-6, 3.62753086e-6, 1.94327160e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_litter_data["cell_id"], "element": ["C", "N", "P"]},
    )

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
        "leaf_meta_split": [0.81240302, 0.64019755, 0.42407771, 0.00894268],
        "root_meta_split": [0.588394858, 0.379571377, 0.5024461477, 0.410125012],
        "subcanopy_meta_split": [0.82815, 0.57, 0.0, 0.827026],
        "herbivore_waste_above_meta_split": [
            0.7638626,
            0.7697267,
            0.6327571,
            0.6741623,
        ],
        "herbivore_waste_below_meta_split": [0.211658, 0.488244, 0.181836, 0.0],
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
        "above_metabolic": [0.01106943, 0.00109058, 0.00535450, 0.00163240],
        "above_structural": [0.002554888, 0.000436330, 0.006572925, 0.014686861],
        "below_metabolic": [0.00794558, 0.00425741, 0.00027294, 0.00510606],
        "below_structural": [0.005565040, 0.006799504, 0.000963604, 0.007501166],
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

    # Merge foliage turnover across PFTs
    collapsed_foliage = dummy_litter_data["foliage_turnover_cnp"].sum(dim="pft")

    actual_split = split_pool_into_metabolic_and_structural_litter(
        input_masses=collapsed_foliage,
        lignin_proportion=dummy_litter_data["senesced_leaf_lignin"],
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
            input_masses=dummy_litter_data["foliage_turnover_cnp"],
            lignin_proportion=lignin_proportions,
            max_metabolic_fraction=fixture_litter_constants.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=fixture_litter_constants.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=fixture_litter_constants.metabolic_split_phosphorus_sensitivity,
        )

    expected_log = ((ERROR, "Lignin proportion not between 0 and 1 (inclusive)!"),)

    # Check the error reports
    log_check(caplog, expected_log)


def test_calculate_input_chemistries(fixture_litter_constants, litter_inputs):
    """Check that calculation of input chemistries is correct."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.inputs import calculate_input_chemistries

    expected_chemistries = {
        "woody_lignin": [0.233, 0.545, 0.612, 0.378],
        "above_structural_lignin": [0.26710212, 0.60062982, 0.53808352, 0.57375723],
        "below_structural_lignin": [0.48580135, 0.54777011, 0.56071798, 0.67123270],
        "woody_nitrogen": [0.00061779, 0.00085492, 0.00043092, 0.00029946],
        "below_metabolic_nitrogen": [
            0.00039106928,
            0.00017584697,
            1.22101206e-5,
            0.00026061304,
        ],
        "below_structural_nitrogen": [
            5.48399188e-5,
            5.72148004e-5,
            8.95840338e-6,
            7.52953501e-5,
        ],
        "above_metabolic_nitrogen": [
            0.00089995134,
            5.33447125e-5,
            0.00024685572,
            8.89360896e-5,
        ],
        "above_structural_nitrogen": [
            4.1389337e-5,
            5.1525155e-6,
            5.8536743e-5,
            0.0002447146,
        ],
        "woody_phosphorus": [4.3782837e-5, 7.3289902e-5, 3.3754822e-5, 1.8564356e-5],
        "below_metabolic_phosphorus": [
            1.80392188e-5,
            1.86684102e-5,
            2.19564468e-6,
            2.59981984e-5,
        ],
        "below_structural_phosphorus": [
            2.526860157e-6,
            5.973051351e-6,
            1.774900134e-6,
            9.421814238e-6,
        ],
        "above_metabolic_phosphorus": [
            3.14742219e-5,
            4.49467401e-6,
            1.87049233e-5,
            6.03601548e-6,
        ],
        "above_structural_phosphorus": [
            1.45315301e-6,
            4.00697185e-7,
            4.48908362e-6,
            3.61419899e-5,
        ],
    }

    actual_chemistries = calculate_input_chemistries(
        litter_inputs=litter_inputs,
        meta_to_struct_nitrogen_ratio=fixture_litter_constants.metabolic_to_structural_n_ratio,
        meta_to_struct_phosphorus_ratio=fixture_litter_constants.metabolic_to_structural_p_ratio,
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
    expected_concs_above_struct = [0.26710212, 0.60062982, 0.53808352, 0.57375723]
    expected_concs_below_struct = [0.48580135, 0.54777011, 0.56071798, 0.67123270]

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
            0.00039106928,
            0.00017584697,
            1.22101206e-5,
            0.00026061304,
        ],
        "below_structural_nitrogen": [
            5.48399188e-5,
            5.72148004e-5,
            8.95840338e-6,
            7.52953501e-5,
        ],
        "above_metabolic_nitrogen": [
            0.00089995134,
            5.33447125e-5,
            0.00024685572,
            8.89360896e-5,
        ],
        "above_structural_nitrogen": [
            4.1389337e-5,
            5.1525155e-6,
            5.8536743e-5,
            0.0002447146,
        ],
    }

    actual_nutrient_masses = calculate_litter_input_nutrient_masses(
        litter_inputs=litter_inputs,
        meta_to_struct_nutrient_ratio=fixture_litter_constants.metabolic_to_structural_n_ratio,
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
            meta_to_struct_nutrient_ratio=fixture_litter_constants.metabolic_to_structural_n_ratio,
            nutrient="oxygen",
        )

    expected_log = ((ERROR, "oxygen is not an element we currently track!"),)

    # Check the error reports
    log_check(caplog, expected_log)


def test_find_nutrient_split_between_litter_pools(
    dummy_litter_data, fixture_litter_constants, litter_inputs
):
    """Check the function to find the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.inputs import (
        find_nutrient_split_between_litter_pools,
    )

    expected_n_meta = np.array([6.331932287, 2.81123962, 0.0468426692, 4.22192613])
    expected_n_struct = np.array([0.8858875316, 0.91902302, 0.009277350, 1.214462735])

    actual_n_meta, actual_n_struct = find_nutrient_split_between_litter_pools(
        input_carbon_rate=dummy_litter_data["root_turnover_cnp"].sel(element="C"),
        input_nutrient_rate=dummy_litter_data["root_turnover_cnp"].sel(element="N"),
        metabolic_split=litter_inputs.root_meta_split,
        meta_to_struct_nutrient_ratio=fixture_litter_constants.metabolic_to_structural_n_ratio,
    )

    # Standard checks of the produced values
    assert np.allclose(actual_n_meta, expected_n_meta)
    assert np.allclose(actual_n_struct, expected_n_struct)


def test_find_nutrient_split_between_litter_pools_bad_input(
    dummy_litter_data, fixture_litter_constants, litter_inputs
):
    """Check the function to find the nutrient split handles bad input correctly."""
    from virtual_ecosystem.models.litter.inputs import (
        find_nutrient_split_between_litter_pools,
    )

    # One carbon input is missing
    input_carbon_rate = DataArray([218.7, 0.0, 2.43, 201.69], dims="cell_id")
    # In one case all flow is to metabolic
    metabolic_split = DataArray(
        [0.588394858, 0.379571377, 1.0, 0.410125012], dims="cell_id"
    )

    expected_n_meta = DataArray(
        [6.331932287, 0.0, 0.0561200192, 4.22192613], dims="cell_id"
    )
    expected_n_struct = DataArray([0.8858875316, 0.0, 0.0, 1.214462735], dims="cell_id")

    actual_n_meta, actual_n_struct = find_nutrient_split_between_litter_pools(
        input_carbon_rate=input_carbon_rate,
        input_nutrient_rate=dummy_litter_data["root_turnover_cnp"].loc[:, "N"],
        metabolic_split=metabolic_split,
        meta_to_struct_nutrient_ratio=fixture_litter_constants.metabolic_to_structural_n_ratio,
    )

    # Standard checks of the produced values
    assert np.allclose(actual_n_meta, expected_n_meta)
    assert np.allclose(actual_n_struct, expected_n_struct)


def test_calculate_nutrient_split(
    dummy_litter_data, fixture_litter_constants, litter_inputs
):
    """Check the function to calculate the nutrient split between litter pools."""
    from virtual_ecosystem.models.litter.inputs import calculate_nutrient_split

    expected_n_meta = np.array([6.331932287, 2.81123962, 0.0468426692, 4.22192613])
    expected_n_struct = np.array([0.8858875316, 0.91902302, 0.009277350, 1.214462735])

    actual_n_meta, actual_n_struct = calculate_nutrient_split(
        carbon_input_meta=dummy_litter_data["root_turnover_cnp"].loc[:, "C"]
        * litter_inputs.root_meta_split,
        carbon_input_struct=dummy_litter_data["root_turnover_cnp"].loc[:, "C"]
        * (1 - litter_inputs.root_meta_split),
        input_nutrient_rate=dummy_litter_data["root_turnover_cnp"].loc[:, "N"],
        meta_to_struct_nutrient_ratio=fixture_litter_constants.metabolic_to_structural_n_ratio,
    )

    # Standard checks of the produced values
    assert np.allclose(actual_n_meta, expected_n_meta)
    assert np.allclose(actual_n_struct, expected_n_struct)
