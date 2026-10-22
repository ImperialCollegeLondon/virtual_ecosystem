"""Test soil.model_config."""

from contextlib import nullcontext as does_not_raise
from itertools import permutations

import pytest
from pydantic import ValidationError


def test_SoilConstants_pH():
    """Test the custom validation on SoilConstants model.

    This tests all possible orderings of the four microbe pH variables.
    """
    from virtual_ecosystem.models.soil.model_config import SoilConstants

    defaults = (2.5, 4.5, 7.5, 11.0)
    keys = [
        "min_pH_microbes",
        "lowest_optimal_pH_microbes",
        "highest_optimal_pH_microbes",
        "max_pH_microbes",
    ]

    for perm in permutations(defaults):
        if perm == defaults:
            # If the ordering is the same as the defaults, all is good
            outcome = does_not_raise()
        else:
            # Otherwise not.
            outcome = pytest.raises(ValidationError)

        with outcome:
            _ = SoilConstants(**dict(zip(keys, perm)))


@pytest.mark.parametrize(
    argnames="data, outcome",
    argvalues=(
        pytest.param({}, does_not_raise(), id="default provides required"),
        pytest.param(
            {
                "microbial_group_definition": [
                    {"name": "saprotrophic_fungi"},
                    {"name": "ectomycorrhiza"},
                    {"name": "arbuscular_mycorrhiza"},
                    {"name": "bacteria"},
                ]
            },
            does_not_raise(),
            id="user data provides required",
        ),
        pytest.param(
            {"microbial_group_definition": [{"name": "saprotrophic_fungi"}]},
            pytest.raises(ValidationError),
            id="user data only provides one",
        ),
    ),
)
def test_SoilConfiguration_microbial_group_definition(data, outcome):
    """Test the custom validation on SoilConfiguration.enzyme_class_definition."""
    from virtual_ecosystem.models.soil.model_config import SoilConfiguration

    with outcome:
        _ = SoilConfiguration(**data)


@pytest.mark.parametrize(
    argnames="data, outcome",
    argvalues=(
        pytest.param({}, does_not_raise(), id="default ok"),
        pytest.param(
            {"taxonomic_group": "fungi", "reproductive_allocation": 0.3},
            does_not_raise(),
            id="user provided ok",
        ),
        pytest.param(
            {"taxonomic_group": "bacteria", "reproductive_allocation": 0.3},
            pytest.raises(ValidationError),
            id="user provided fruiting bacteria",
        ),
        pytest.param(
            {"taxonomic_group": "archaea", "reproductive_allocation": 0.3},
            pytest.raises(ValidationError),
            id="user provided archaea",
        ),
    ),
)
def test_SoilMicrobialGroup(data, outcome):
    """Test the custom validation on SoilMicrobialGroup."""
    from virtual_ecosystem.models.soil.model_config import SoilMicrobialGroup

    with outcome:
        _ = SoilMicrobialGroup(**data)


def test_load_enzymes(fixture_configuration):
    """Test that the function to load all the enzyme classes works."""
    from pathlib import Path

    from virtual_ecosystem.models.soil.model_config import (
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
    from virtual_ecosystem.models.soil.model_config import load_enzymes

    path_to_file = fixture_root_data_dir_path / "does_not_exist.csv"

    with pytest.raises(
        ValueError,
        match="Enzyme CSV path not found or a directory:",
    ):
        _ = load_enzymes(path=path_to_file)


def test_load_enzymes_bad_csv_file(tmp_path):
    """Test function to load all the enzyme classes fails for bad csv files."""
    from virtual_ecosystem.models.soil.model_config import load_enzymes

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

    from virtual_ecosystem.models.soil.model_config import load_enzymes

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

    from virtual_ecosystem.models.soil.model_config import load_enzymes

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

    from virtual_ecosystem.models.soil.model_config import (
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

    from virtual_ecosystem.models.soil.model_config import load_enzymes

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

    from virtual_ecosystem.models.soil.model_config import load_enzymes

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

    from virtual_ecosystem.models.soil.model_config import load_enzymes

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
