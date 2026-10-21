"""Test module for soil.microbial_groups.py.

This module tests the functions which generate microbial functional groups.
"""

from logging import WARNING
from typing import get_args

import numpy as np
import pytest

from tests.conftest import log_check


def test_make_full_set_of_enzyme_classes(fixture_configuration):
    """Test that the function to make all the enzyme classes works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        REQUIRED_ENZYMES,
        SoilEnzymeClass,
        make_full_set_of_enzyme_classes,
    )

    enzyme_classes = make_full_set_of_enzyme_classes(
        path_to_csv=fixture_configuration.soil.enzyme_class_definition_path
    )

    expected_enzymes = {
        f"{source}_{substrate}" for source, substrate in REQUIRED_ENZYMES
    }

    assert expected_enzymes == set(enzyme_classes.keys())

    for group in enzyme_classes:
        assert type(enzyme_classes[group]) is SoilEnzymeClass

    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert enzyme_classes["bacteria_pom"].maximum_rate == 60.0
    assert enzyme_classes["bacteria_maom"].maximum_rate == 24.0
    assert enzyme_classes["fungi_pom"].maximum_rate == 120.0
    assert enzyme_classes["fungi_maom"].maximum_rate == 48.0


def test_make_full_set_of_enzyme_classes_no_file(fixture_root_data_dir_path):
    """Test function to make all the enzyme classes fails for non-existent file."""
    from virtual_ecosystem.core.exceptions import ConfigurationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

    path_to_file = fixture_root_data_dir_path / "does_not_exist.csv"

    with pytest.raises(
        ConfigurationError,
        match="enzyme class definition file doesn't point to a csv file",
    ):
        _ = make_full_set_of_enzyme_classes(path_to_csv=path_to_file)


def test_make_full_set_of_enzyme_classes_non_csv_file(tmp_path):
    """Test function to make all the enzyme classes fails for non-csv file."""
    from virtual_ecosystem.core.exceptions import ConfigurationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

    path_to_file = tmp_path / "enzyme_definitions.txt"
    path_to_file.write_text("garbage text")

    with pytest.raises(
        ConfigurationError,
        match="enzyme class definition file doesn't point to a csv file",
    ):
        _ = make_full_set_of_enzyme_classes(path_to_csv=path_to_file)


def test_make_full_set_of_enzyme_classes_missing_header(
    fixture_configuration,
    tmp_path,
):
    """Test function to make all the enzyme classes fails if a column is missing."""
    import pandas as pd

    from virtual_ecosystem.core.exceptions import InitialisationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

    # Read definitions in and then drop a required header
    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )
    enzyme_definitions = enzyme_definitions.drop(columns=["maximum_rate"])

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    with pytest.raises(
        InitialisationError,
        match="expected headers are missing from the enzyme class",
    ):
        make_full_set_of_enzyme_classes(output_path)


def test_make_full_set_of_enzyme_classes_surplus_header(
    fixture_configuration,
    tmp_path,
    caplog,
):
    """Test function to make all the enzyme classes warms about extra headers."""
    import pandas as pd

    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

    enzyme_definitions = pd.read_csv(
        fixture_configuration.soil.enzyme_class_definition_path
    )
    enzyme_definitions["unused_column"] = "ignored"

    # Write file out to temporary location
    output_path = tmp_path / "enzyme_definitions.csv"
    enzyme_definitions.to_csv(output_path, index=False)

    make_full_set_of_enzyme_classes(output_path)

    # Check that a warning is logged as expected
    expected_log = [
        (
            WARNING,
            "The following additional headers are provided in the enzyme class "
            "definition file, and were ignored: {'unused_column'}",
        ),
    ]
    log_check(caplog, expected_log)


def test_make_full_set_of_enzyme_classes_missing_required_enzyme(
    fixture_configuration,
    tmp_path,
):
    """Test function to make the enzyme classes fails if required enzyme is missing."""
    import pandas as pd

    from virtual_ecosystem.core.exceptions import InitialisationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        REQUIRED_ENZYMES,
        make_full_set_of_enzyme_classes,
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
        InitialisationError,
        match="The following required enzymes are not defined in the enzyme class "
        "definition file:",
    ):
        make_full_set_of_enzyme_classes(output_path)


def test_make_full_set_of_enzyme_classes_unexpected_enzyme(
    fixture_configuration,
    tmp_path,
):
    """Test function to make enzyme classes fails if unexpected enzyme is included."""
    import pandas as pd

    from virtual_ecosystem.core.exceptions import InitialisationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

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
        InitialisationError,
        match="The following enzyme class are provided in the definition file but are "
        "not expected by the simulation:",
    ):
        make_full_set_of_enzyme_classes(output_path)


def test_make_full_set_of_enzyme_classes_duplicate_enzyme(
    fixture_configuration,
    tmp_path,
):
    """Test function to make the enzyme classes fails an enzyme is duplicated."""
    import pandas as pd

    from virtual_ecosystem.core.exceptions import InitialisationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

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
        InitialisationError,
        match="Enzyme definition file contains duplicate copies of enzymes!",
    ):
        make_full_set_of_enzyme_classes(output_path)


def test_make_full_set_of_enzyme_classes_bad_enzyme_data(
    fixture_configuration,
    tmp_path,
):
    """Test function to make enzyme classes fails if csv data is non-numeric."""
    import pandas as pd

    from virtual_ecosystem.core.exceptions import InitialisationError
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzyme_classes,
    )

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
        InitialisationError,
        match="The following rows in the enzyme class definition file contained bad "
        "data:",
    ):
        make_full_set_of_enzyme_classes(output_path)


def test_make_full_set_of_microbial_groups(
    fixture_configuration, fixture_core_constants, enzyme_classes
):
    """Test that the function to make all the microbial group works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        MicrobialGroupConstants,
        make_full_set_of_microbial_groups,
    )
    from virtual_ecosystem.models.soil.model_config import REQUIRED_MICROBIAL_GROUPS

    functional_groups = make_full_set_of_microbial_groups(
        fixture_configuration.soil,
        enzyme_classes=enzyme_classes,
        core_constants=fixture_core_constants,
    )

    expected_groups = set(get_args(REQUIRED_MICROBIAL_GROUPS))

    assert expected_groups == set(functional_groups.keys())

    for group in expected_groups:
        assert type(functional_groups[group]) is MicrobialGroupConstants

    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert functional_groups["bacteria"].c_n_ratio == 5.2
    assert functional_groups["saprotrophic_fungi"].c_n_ratio == 6.5


def test_find_enzyme_substrates(
    fixture_configuration, fixture_core_constants, enzyme_classes
):
    """Check method to find the full set of substrates a microbe can use works."""

    from virtual_ecosystem.models.soil.microbial_groups import MicrobialGroupConstants
    from virtual_ecosystem.models.soil.model_config import SoilMicrobialGroup

    bacteria = MicrobialGroupConstants.build_microbial_group(
        group_config=SoilMicrobialGroup(taxonomic_group="bacteria"),
        enzyme_classes=enzyme_classes,
        core_constants=fixture_core_constants,
    )

    assert set(bacteria.find_enzyme_substrates()) == set(["maom", "pom"])


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
    fixture_configuration, enzyme_classes, group, expected_ratio
):
    """Check method to calculate average new biomass nutrient ratios works."""
    import numpy as np

    from virtual_ecosystem.models.soil.microbial_groups import (
        calculate_new_biomass_average_nutrient_ratios,
    )

    group_config = next(
        functional_group
        for functional_group in fixture_configuration.soil.microbial_group_definition
        if functional_group.name == group
    )

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
