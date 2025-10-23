"""Test soil.model_config."""

from contextlib import nullcontext as does_not_raise
from itertools import permutations

import pytest
from pydantic import ValidationError

from virtual_ecosystem.core.exceptions import ConfigurationError


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
                "enzyme_class_definition": [
                    {"source": "fungi", "substrate": "maom"},
                    {"source": "fungi", "substrate": "pom"},
                    {"source": "bacteria", "substrate": "maom"},
                    {"source": "bacteria", "substrate": "pom"},
                ]
            },
            does_not_raise(),
            id="user data provides required",
        ),
        pytest.param(
            {"enzyme_class_definition": [{"source": "fungi", "substrate": "maom"}]},
            pytest.raises(ValidationError),
            id="user data only provides one",
        ),
    ),
)
def test_SoilConfiguration_enzyme_class_definition(data, outcome):
    """Test the custom validation on SoilConfiguration.enzyme_class_definition."""
    from virtual_ecosystem.models.soil.model_config import SoilConfiguration

    with outcome:
        _ = SoilConfiguration(**data)


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


@pytest.mark.parametrize(
    argnames=["cfg_strings"],
    argvalues=[
        pytest.param(
            """
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "pom"
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "maom"
            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "pom"
            """,
            id="missing_fungi_maom",
        ),
        pytest.param(  # archaea included but they shouldn't be
            """
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "pom"
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "maom"
            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "pom"
            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "maom"
            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "phosphate"
            """,
            id="unexpected_phosphatase",
        ),
        pytest.param(
            """
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "pom"

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "phosphate"
            """,
            id="missing_most_enzymes_and_unexpected_phosphatase",
        ),
    ],
)
def test_soil_enzyme_definition_via_toml(caplog, cfg_strings):
    """Check that bad configs generate errors during enzyme class generation.

    This is a cut down version of testing of the old make_full_set_of_enzymes_errors
    function, retained as a bit of a belt and braces test for testing the full path from
    TOML.
    """

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )

    config_data = ConfigurationLoader(cfg_strings=cfg_strings)
    caplog.clear()

    with pytest.raises(ConfigurationError):
        _ = generate_configuration(config_data.data)


@pytest.mark.parametrize(
    argnames="cfg_strings",
    argvalues=[
        pytest.param(
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            taxonomic_group = "bacteria"
            """,
            id="missing_fungi",
        ),
        pytest.param(
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            taxonomic_group = "bacteria"
            [[soil.microbial_group_definition]]
            name = "saprotrophic_fungi"
            taxonomic_group = "fungi"
            [[soil.microbial_group_definition]]
            name = "arbuscular_mycorrhiza"
            taxonomic_group = "fungi"
            [[soil.microbial_group_definition]]
            name = "ectomycorrhiza"
            taxonomic_group = "fungi"
            [[soil.microbial_group_definition]]
            name = "archaea"
            taxonomic_group = "archaea"
            """,
            id="unexpected_archaea",
        ),
        pytest.param(
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            taxonomic_group = "bacteria"
            [[soil.microbial_group_definition]]
            name = "archaea"
            taxonomic_group = "archaea"

            """,
            id="missing_fungi_and_unexpected_archaea",
        ),
    ],
)
def test_make_full_set_of_microbial_groups_errors(cfg_strings):
    """Check that bad configs generate errors during microbial group generation.

    This is a cut down version of testing of the old
    test_make_full_set_of_microbial_groups_errors function, retained as a bit of a belt
    and braces test for testing the full path from TOML.
    """
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )

    config_data = ConfigurationLoader(cfg_strings=cfg_strings)

    with pytest.raises(ConfigurationError):
        _ = generate_configuration(config_data.data)
