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
