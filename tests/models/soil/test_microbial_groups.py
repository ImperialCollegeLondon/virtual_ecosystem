"""Test module for soil.microbial_groups.py.

This module tests the functions which generate microbial functional groups.
"""

import numpy as np
import pytest


@pytest.mark.parametrize(
    argnames=["group", "expected_ratio"],
    argvalues=[
        pytest.param(
            "bacteria",
            {"nitrogen": 5.69458, "phosphorus": 15.5048},
            id="bacteria",
        ),
        pytest.param(
            "saprotrophic_fungi",
            {"nitrogen": 5.70632718, "phosphorus": 15.5860039},
            id="fungi",
        ),
    ],
)
def test_calculate_new_biomass_average_nutrient_ratios(
    enzyme_classes, functional_groups, group, expected_ratio
):
    """Check method to calculate average new biomass nutrient ratios works."""
    import numpy as np

    from virtual_ecosystem.models.soil.microbial_groups import (
        calculate_new_biomass_average_nutrient_ratios,
    )

    group_config = functional_groups[group]

    averaged_nutrient_ratios = calculate_new_biomass_average_nutrient_ratios(
        taxonomic_group=group_config.taxonomic_group,
        c_n_ratio=5.7,
        c_p_ratio=15.5,
        enzyme_production=group_config.enzyme_production,
        reproductive_allocation=group_config.reproductive_allocation,
        enzyme_classes=enzyme_classes,
    )

    assert np.isclose(averaged_nutrient_ratios["nitrogen"], expected_ratio["nitrogen"])
    assert np.isclose(
        averaged_nutrient_ratios["phosphorus"], expected_ratio["phosphorus"]
    )


def test_calculate_symbiotic_carbon_supply(
    dummy_carbon_data, fixture_soil_constants, fixture_core_constants
):
    """Test that calculation of splitting of carbon supply between symbiotes works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        calculate_symbiotic_carbon_supply,
    )

    expected_supply = {
        "nitrogen_fixers": [0.012, 0.3, 0.009, 0.00564],
        "ectomycorrhiza": [0.007, 0.175, 0.00525, 0.00329],
        "arbuscular_mycorrhiza": [0.021, 0.525, 0.01575, 0.00987],
    }

    actual_supply = calculate_symbiotic_carbon_supply(
        dummy_carbon_data["plant_symbiote_carbon_supply"]
        / fixture_core_constants.microbial_simulation_depth,
        nitrogen_fixer_fraction=fixture_soil_constants.nitrogen_fixer_supply_fraction,
        ectomycorrhiza_fraction=fixture_soil_constants.ectomycorrhiza_supply_fraction,
    )

    # Check all (non-private) dataclass attributes against the dictionary
    for attr in dir(actual_supply):
        if not attr.startswith("_"):
            assert attr in expected_supply.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_supply, attr), expected_supply[attr])


def test_load_enzymes(fixture_configuration):
    """Test that the function to load all the enzyme classes works."""
    from pathlib import Path

    from virtual_ecosystem.models.soil.microbial_groups import (
        REQUIRED_ENZYMES,
        SoilEnzyme,
        load_enzymes,
    )

    enzyme_classes = load_enzymes(
        path=Path(fixture_configuration.soil.enzyme_class_definition_path)
    )

    expected_enzymes = {
        f"{source}_{substrate}" for source, substrate in REQUIRED_ENZYMES
    }

    assert expected_enzymes == set(enzyme_classes.keys())

    for enzyme_class in enzyme_classes.values():
        assert type(enzyme_class) is SoilEnzyme

    assert enzyme_classes["bacteria_pom"].maximum_rate == 60.0
    assert enzyme_classes["bacteria_maom"].maximum_rate == 24.0
    assert enzyme_classes["fungi_pom"].maximum_rate == 120.0
    assert enzyme_classes["fungi_maom"].maximum_rate == 48.0


def test_load_enzymes_no_file(fixture_root_data_dir_path):
    """Test function to load all the enzyme classes fails for non-existent file."""
    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    path_to_file = fixture_root_data_dir_path / "does_not_exist.csv"

    with pytest.raises(
        ValueError,
        match="Enzyme CSV path not found or a directory:",
    ):
        _ = load_enzymes(path=path_to_file)


def test_load_enzymes_bad_csv_file(tmp_path):
    """Test function to load all the enzyme classes fails for bad csv files."""
    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    path_to_file = tmp_path / "enzyme_definitions.txt"
    path_to_file.write_text('a,b\n1,"unterminated')

    with pytest.raises(ValueError, match="Could not parse enzyme data from:"):
        _ = load_enzymes(path=path_to_file)


def test_load_enzymes_missing_header(
    fixture_configuration,
    tmp_path,
):
    """Test function to load all the enzyme classes fails if a column is missing."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    # Read definitions in and then drop a required header
    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )
    enzyme_definitions = enzyme_definitions.drop(columns=["maximum_rate"])

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in enzyme CSV file: 1 validation error for SoilEnzyme",
    ):
        load_enzymes(output_path)


def test_load_enzymes_surplus_header(
    fixture_configuration,
    tmp_path,
):
    """Test function to load all the enzyme classes fails for extra headers."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )
    enzyme_definitions["unused_column"] = "ignored"

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in enzyme CSV file: 1 validation error for SoilEnzyme",
    ):
        load_enzymes(output_path)


def test_load_enzymes_missing_required_enzyme(
    fixture_configuration,
    tmp_path,
):
    """Test function to load the enzyme classes fails if required enzyme is missing."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import (
        REQUIRED_ENZYMES,
        load_enzymes,
    )

    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )

    # Remove one enzyme definition from the dataframe
    source, substrate = next(iter(REQUIRED_ENZYMES))

    mask = ~(
        (enzyme_definitions["source"] == source)
        & (enzyme_definitions["substrate"] == substrate)
    )
    enzyme_definitions = enzyme_definitions.loc[mask]

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="The source/substrate pairs provided in enzyme class definitions",
    ):
        load_enzymes(output_path)


def test_load_enzymes_unexpected_enzyme(fixture_configuration, tmp_path):
    """Test function to load enzyme classes fails if unexpected enzyme is included."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )

    # Copy a valid row but change its source/substrate combination.
    unexpected_row = enzyme_definitions.iloc[[0]].copy()
    unexpected_row.loc[:, "source"] = "unexpected_source"
    unexpected_row.loc[:, "substrate"] = "unexpected_substrate"

    enzyme_definitions = pd.concat(
        [enzyme_definitions, unexpected_row],
        ignore_index=True,
    )

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in enzyme CSV file: 2 validation errors for SoilEnzyme",
    ):
        load_enzymes(output_path)


def test_load_enzymes_duplicate_enzyme(fixture_configuration, tmp_path):
    """Test function to load the enzyme classes fails an enzyme is duplicated."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )

    # Duplicate one of the rows so that there are two copies of the same enzyme in the
    # input data
    enzyme_definitions = pd.concat(
        [enzyme_definitions, enzyme_definitions.loc[[2]]], ignore_index=True
    )

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Duplicated enzyme source/substrate combinations in enzyme data",
    ):
        load_enzymes(output_path)


def test_load_enzymes_bad_enzyme_data(fixture_configuration, tmp_path):
    """Test function to load enzyme classes fails if csv data is non-numeric."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_enzymes

    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )

    # Replace a parameter value with a string
    enzyme_definitions["maximum_rate"] = enzyme_definitions["maximum_rate"].astype(
        object
    )
    enzyme_definitions.loc[0, "maximum_rate"] = "this_is_nonsense"

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in enzyme CSV file: 1 validation error for SoilEnzyme",
    ):
        load_enzymes(output_path)


def test_load_microbes(fixture_configuration, enzyme_classes):
    """Test that the function to load all the microbial groups works."""
    from pathlib import Path
    from typing import get_args

    from virtual_ecosystem.models.soil.microbial_groups import (
        REQUIRED_MICROBIAL_GROUPS,
        SoilMicrobe,
        load_microbes,
    )

    microbial_groups = load_microbes(
        path=Path(fixture_configuration.soil.microbial_group_definition_path),
        enzyme_classes=enzyme_classes,
    )

    assert set(get_args(REQUIRED_MICROBIAL_GROUPS)) == set(microbial_groups.keys())

    for microbial_group in microbial_groups.values():
        assert type(microbial_group) is SoilMicrobe

    assert microbial_groups["bacteria"].c_n_ratio == 5.2
    assert microbial_groups["saprotrophic_fungi"].c_n_ratio == 6.5
    assert microbial_groups["arbuscular_mycorrhiza"].c_n_ratio == 18.0
    assert microbial_groups["ectomycorrhiza"].c_n_ratio == 18.0

    # Check that enzyme productions have populated
    assert microbial_groups["bacteria"].enzyme_production == {
        "maom": 0.005,
        "pom": 0.005,
    }
    assert microbial_groups["saprotrophic_fungi"].enzyme_production == {
        "maom": 0.005,
        "pom": 0.005,
    }
    assert microbial_groups["arbuscular_mycorrhiza"].enzyme_production == {
        "maom": 0.0,
        "pom": 0.0,
    }
    assert microbial_groups["ectomycorrhiza"].enzyme_production == {
        "maom": 0.02,
        "pom": 0.02,
    }

    # Check that enzyme substrates have all populated
    assert set(microbial_groups["bacteria"].enzyme_substrates) == set(["maom", "pom"])
    assert set(microbial_groups["saprotrophic_fungi"].enzyme_substrates) == set(
        ["maom", "pom"]
    )
    assert set(microbial_groups["arbuscular_mycorrhiza"].enzyme_substrates) == set()
    assert set(microbial_groups["ectomycorrhiza"].enzyme_substrates) == set(
        ["maom", "pom"]
    )

    # Check that the synthesis nutrient ratios are as expected
    expected_ratios = {
        "bacteria": {
            "nitrogen": 5.2,
            "phosphorus": 16.0,
        },
        "saprotrophic_fungi": {
            "nitrogen": 6.5,
            "phosphorus": 40.0,
        },
        "arbuscular_mycorrhiza": {
            "nitrogen": 18.0,
            "phosphorus": 120.0,
        },
        "ectomycorrhiza": {
            "nitrogen": 16.947903430749683,
            "phosphorus": 112.1311475409836,
        },
    }

    for group, expected in expected_ratios.items():
        actual = microbial_groups[group].synthesis_nutrient_ratios

        assert actual.keys() == expected.keys()
        for nutrient, value in expected.items():
            assert np.isclose(actual[nutrient], value)


def test_load_microbes_no_file(fixture_root_data_dir_path, enzyme_classes):
    """Test function to load all the microbial groups fails for non-existent file."""
    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    path_to_file = fixture_root_data_dir_path / "does_not_exist.csv"

    with pytest.raises(
        ValueError,
        match="Microbial group CSV path not found or a directory:",
    ):
        _ = load_microbes(path=path_to_file, enzyme_classes=enzyme_classes)


def test_load_microbes_bad_csv_file(tmp_path, enzyme_classes):
    """Test function to load all the microbial groups fails for bad csv files."""
    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    path_to_file = tmp_path / "enzyme_definitions.txt"
    path_to_file.write_text('a,b\n1,"unterminated')

    with pytest.raises(ValueError, match="Could not parse microbe data from:"):
        _ = load_microbes(path=path_to_file, enzyme_classes=enzyme_classes)


def test_load_microbes_missing_header(fixture_configuration, tmp_path, enzyme_classes):
    """Test function to load all the microbial groups fails if a column is missing."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    # Read definitions in and then drop a required header
    microbe_definitions = pd.read_csv(
        fixture_configuration.soil.microbial_group_definition_path
    )
    microbe_definitions = microbe_definitions.drop(columns=["turnover_rate"])

    # Write file out to temporary location
    output_path = tmp_path / "microbe_definitions.csv"
    microbe_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in microbe parametrisation CSV file: 1 validation error for"
        " SoilMicrobe",
    ):
        load_microbes(output_path, enzyme_classes=enzyme_classes)


def test_load_microbes_surplus_header(fixture_configuration, tmp_path, enzyme_classes):
    """Test function to load all the microbial groups fails for extra headers."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    microbe_definitions = pd.read_csv(
        fixture_configuration.soil.microbial_group_definition_path
    )
    microbe_definitions["unused_column"] = "ignored"

    # Write file out to temporary location
    output_path = tmp_path / "microbe_definitions.csv"
    microbe_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in microbe parametrisation CSV file: 1 validation error for"
        " SoilMicrobe",
    ):
        load_microbes(output_path, enzyme_classes=enzyme_classes)


def test_load_microbes_missing_required_microbe(
    fixture_configuration, tmp_path, enzyme_classes
):
    """Test function to load the microbial groups fails if required group is missing."""
    from typing import get_args

    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import (
        REQUIRED_MICROBIAL_GROUPS,
        load_microbes,
    )

    microbe_definitions = pd.read_csv(
        fixture_configuration.soil.microbial_group_definition_path
    )

    # Remove one microbial group definition from the dataframe
    name = next(iter(get_args(REQUIRED_MICROBIAL_GROUPS)))

    mask = ~(microbe_definitions["name"] == name)
    microbe_definitions = microbe_definitions.loc[mask]

    # Write file out to temporary location
    output_path = tmp_path / "microbe_definitions.csv"
    microbe_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="The microbial groups provided in the microbial groups definition file",
    ):
        load_microbes(output_path, enzyme_classes=enzyme_classes)


def test_load_microbes_unexpected_microbe(
    fixture_configuration, tmp_path, enzyme_classes
):
    """Test function to load microbial groups fails if unexpected group is included."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    microbe_definitions = pd.read_csv(
        fixture_configuration.soil.microbial_group_definition_path
    )

    # Copy a valid row but change its name
    unexpected_row = microbe_definitions.iloc[[0]].copy()
    unexpected_row.loc[:, "name"] = "bacteria_2"

    microbe_definitions = pd.concat(
        [microbe_definitions, unexpected_row],
        ignore_index=True,
    )

    # Write file out to temporary location
    output_path = tmp_path / "microbe_definitions.csv"
    microbe_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in microbe parametrisation CSV file: 1 validation error for"
        " SoilMicrobe",
    ):
        load_microbes(output_path, enzyme_classes=enzyme_classes)


def test_load_microbes_duplicate_microbe(
    fixture_configuration, tmp_path, enzyme_classes
):
    """Test function to load the microbial groups fails an group is duplicated."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    microbe_definitions = pd.read_csv(
        fixture_configuration.soil.microbial_group_definition_path
    )

    # Duplicate one of the rows so that there are two copies of the same microbe in the
    # input data
    microbe_definitions = pd.concat(
        [microbe_definitions, microbe_definitions.loc[[2]]], ignore_index=True
    )

    # Write file out to temporary location
    output_path = tmp_path / "microbe_definitions.csv"
    microbe_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Duplicated microbial groups in microbial parametrisation data",
    ):
        load_microbes(output_path, enzyme_classes=enzyme_classes)


def test_load_microbes_bad_microbe_data(
    fixture_configuration, tmp_path, enzyme_classes
):
    """Test function to load microbial groups fails if csv data is non-numeric."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import load_microbes

    microbe_definitions = pd.read_csv(
        fixture_configuration.soil.microbial_group_definition_path
    )

    # Replace a parameter value with a string
    microbe_definitions["turnover_rate"] = microbe_definitions["turnover_rate"].astype(
        object
    )
    microbe_definitions.loc[0, "turnover_rate"] = "this_is_nonsense"

    # Write file out to temporary location
    output_path = tmp_path / "microbe_definitions.csv"
    microbe_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        ValueError,
        match="Invalid data in microbe parametrisation CSV file: 1 validation error for"
        " SoilMicrobe",
    ):
        load_microbes(output_path, enzyme_classes=enzyme_classes)
