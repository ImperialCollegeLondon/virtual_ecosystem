"""Test module for soil.microbial_groups.py.

This module tests the functions which generate microbial functional groups.
"""

from logging import CRITICAL

import pytest

from tests.conftest import log_check
from virtual_ecosystem.core.config import Config, ConfigurationError


def test_make_full_set_of_microbial_groups(fixture_config):
    """Test that the function to make all the microbial group works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        MicrobialGroupConstants,
        make_full_set_of_microbial_groups,
    )

    expected_groups = ["bacteria", "fungi"]

    functional_groups = make_full_set_of_microbial_groups(fixture_config)

    assert set(expected_groups) == set(functional_groups.keys())

    for group in expected_groups:
        assert type(functional_groups[group]) is MicrobialGroupConstants

    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert functional_groups["bacteria"].c_n_ratio == 5.2
    assert functional_groups["fungi"].c_n_ratio == 6.5


@pytest.mark.parametrize(
    argnames=["cfg_strings", "exp_log"],
    argvalues=[
        pytest.param(
            """[core]""",
            [
                (CRITICAL, "Model configuration for soil model not found."),
            ],
            id="no_soil_config",
        ),
        pytest.param(
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            max_uptake_rate_labile_C = 0.04
            activation_energy_uptake_rate = 47000
            half_sat_labile_C_uptake = 0.364
            activation_energy_uptake_saturation = 30000
            max_uptake_rate_ammonium = 5e-3
            half_sat_ammonium_uptake = 0.02275
            max_uptake_rate_nitrate = 5e-4
            half_sat_nitrate_uptake = 0.02275
            max_uptake_rate_labile_p = 0.0025
            half_sat_labile_p_uptake = 0.02275
            turnover_rate = 0.005
            activation_energy_turnover = 20000
            reference_temperature = 12.0
            c_n_ratio = 5.2
            c_p_ratio = 16
            """,
            [
                (
                    CRITICAL,
                    "The following expected soil microbial groups are not defined: "
                    "fungi",
                )
            ],
            id="missing_fungi",
        ),
        pytest.param(  # archaea included but they shouldn't be
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            max_uptake_rate_labile_C = 0.04
            activation_energy_uptake_rate = 47000
            half_sat_labile_C_uptake = 0.364
            activation_energy_uptake_saturation = 30000
            max_uptake_rate_ammonium = 5e-3
            half_sat_ammonium_uptake = 0.02275
            max_uptake_rate_nitrate = 5e-4
            half_sat_nitrate_uptake = 0.02275
            max_uptake_rate_labile_p = 0.0025
            half_sat_labile_p_uptake = 0.02275
            turnover_rate = 0.005
            activation_energy_turnover = 20000
            reference_temperature = 12.0
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.microbial_group_definition]]
            name = "fungi"
            max_uptake_rate_labile_C = 0.04
            activation_energy_uptake_rate = 47000
            half_sat_labile_C_uptake = 0.364
            activation_energy_uptake_saturation = 30000
            max_uptake_rate_ammonium = 5e-3
            half_sat_ammonium_uptake = 0.02275
            max_uptake_rate_nitrate = 5e-4
            half_sat_nitrate_uptake = 0.02275
            max_uptake_rate_labile_p = 0.0025
            half_sat_labile_p_uptake = 0.02275
            turnover_rate = 0.005
            activation_energy_turnover = 20000
            reference_temperature = 12.0
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.microbial_group_definition]]
            name = "archaea"
            max_uptake_rate_labile_C = 0.04
            activation_energy_uptake_rate = 47000
            half_sat_labile_C_uptake = 0.364
            activation_energy_uptake_saturation = 30000
            max_uptake_rate_ammonium = 5e-3
            half_sat_ammonium_uptake = 0.02275
            max_uptake_rate_nitrate = 5e-4
            half_sat_nitrate_uptake = 0.02275
            max_uptake_rate_labile_p = 0.0025
            half_sat_labile_p_uptake = 0.02275
            turnover_rate = 0.005
            activation_energy_turnover = 20000
            reference_temperature = 12.0
            c_n_ratio = 5.2
            c_p_ratio = 16
            """,
            [
                (
                    CRITICAL,
                    "The following microbial groups are not valid: archaea",
                ),
            ],
            id="unexpected_archaea",
        ),
        pytest.param(
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            max_uptake_rate_labile_C = 0.04
            activation_energy_uptake_rate = 47000
            half_sat_labile_C_uptake = 0.364
            activation_energy_uptake_saturation = 30000
            max_uptake_rate_ammonium = 5e-3
            half_sat_ammonium_uptake = 0.02275
            max_uptake_rate_nitrate = 5e-4
            half_sat_nitrate_uptake = 0.02275
            max_uptake_rate_labile_p = 0.0025
            half_sat_labile_p_uptake = 0.02275
            turnover_rate = 0.005
            activation_energy_turnover = 20000
            reference_temperature = 12.0
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.microbial_group_definition]]
            name = "archaea"
            max_uptake_rate_labile_C = 0.04
            activation_energy_uptake_rate = 47000
            half_sat_labile_C_uptake = 0.364
            activation_energy_uptake_saturation = 30000
            max_uptake_rate_ammonium = 5e-3
            half_sat_ammonium_uptake = 0.02275
            max_uptake_rate_nitrate = 5e-4
            half_sat_nitrate_uptake = 0.02275
            max_uptake_rate_labile_p = 0.0025
            half_sat_labile_p_uptake = 0.02275
            turnover_rate = 0.005
            activation_energy_turnover = 20000
            reference_temperature = 12.0
            c_n_ratio = 5.2
            c_p_ratio = 16
            """,
            [
                (
                    CRITICAL,
                    "The following expected soil microbial groups are not defined: "
                    "fungi",
                ),
                (
                    CRITICAL,
                    "The following microbial groups are not valid: archaea",
                ),
            ],
            id="missing_fungi_and_unexpected_archaea",
        ),
    ],
)
def test_make_full_set_of_microbial_groups_errors(caplog, cfg_strings, exp_log):
    """Check that bad configs generate errors during microbial group generation."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_microbial_groups,
    )

    config = Config(cfg_strings=cfg_strings)
    caplog.clear()

    with pytest.raises(ConfigurationError):
        _ = make_full_set_of_microbial_groups(config)

    log_check(caplog, exp_log)


def test_make_full_set_of_enzymes(fixture_config):
    """Test that the function to make all the enzyme classes works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        EnzymeConstants,
        make_full_set_of_enzymes,
    )

    expected_enzymes = ["bacteria_pom", "bacteria_maom", "fungi_pom", "fungi_maom"]

    enzyme_classes = make_full_set_of_enzymes(fixture_config)

    assert set(expected_enzymes) == set(enzyme_classes.keys())

    for enzyme in expected_enzymes:
        assert type(enzyme_classes[enzyme]) is EnzymeConstants

    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert enzyme_classes["bacteria_pom"].maximum_rate == 60.0
    assert enzyme_classes["bacteria_maom"].maximum_rate == 24.0
    assert enzyme_classes["fungi_pom"].maximum_rate == 120.0
    assert enzyme_classes["fungi_maom"].maximum_rate == 48.0


@pytest.mark.parametrize(
    argnames=["cfg_strings", "exp_log"],
    argvalues=[
        pytest.param(
            """[core]""",
            [
                (CRITICAL, "Model configuration for soil model not found."),
            ],
            id="no_soil_config",
        ),
        pytest.param(
            """
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "pom"
            maximum_rate = 60.0
            half_saturation_constant = 70.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "maom"
            maximum_rate = 24.0
            half_saturation_constant = 350.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "pom"
            maximum_rate = 120.0
            half_saturation_constant = 35.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            """,
            [
                (
                    CRITICAL,
                    "The following expected enzyme classes are not defined: fungi_maom",
                )
            ],
            id="missing_most_fungi_maom",
        ),
        pytest.param(  # archaea included but they shouldn't be
            """
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "pom"
            maximum_rate = 60.0
            half_saturation_constant = 70.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "maom"
            maximum_rate = 24.0
            half_saturation_constant = 350.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "pom"
            maximum_rate = 120.0
            half_saturation_constant = 35.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "maom"
            maximum_rate = 48.0
            half_saturation_constant = 175.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "phosphate"
            maximum_rate = 48.0
            half_saturation_constant = 175.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            """,
            [
                (
                    CRITICAL,
                    "The following enzyme classes are not valid: fungi_phosphate",
                ),
            ],
            id="unexpected_phosphatase",
        ),
        pytest.param(
            """
            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "pom"
            maximum_rate = 60.0
            half_saturation_constant = 70.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "phosphate"
            maximum_rate = 48.0
            half_saturation_constant = 175.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            """,
            [
                (
                    CRITICAL,
                    "The following expected enzyme classes are not defined: ",
                ),
                (
                    CRITICAL,
                    "The following enzyme classes are not valid: fungi_phosphate",
                ),
            ],
            id="missing_most_enzymes_and_unexpected_phosphatase",
        ),
    ],
)
def test_make_full_set_of_enzymes_errors(caplog, cfg_strings, exp_log):
    """Check that bad configs generate errors during enzyme class generation."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzymes,
    )

    config = Config(cfg_strings=cfg_strings)
    caplog.clear()

    with pytest.raises(ConfigurationError):
        _ = make_full_set_of_enzymes(config)

    log_check(caplog, exp_log)
