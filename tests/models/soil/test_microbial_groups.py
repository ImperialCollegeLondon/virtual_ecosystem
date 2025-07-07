"""Test module for soil.microbial_groups.py.

This module tests the functions which generate microbial functional groups.
"""

from logging import CRITICAL

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_ecosystem.core.config import Config, ConfigurationError


def test_make_full_set_of_microbial_groups(fixture_config, enzyme_classes):
    """Test that the function to make all the microbial group works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        MicrobialGroupConstants,
        make_full_set_of_microbial_groups,
    )

    expected_groups = [
        "bacteria",
        "saprotrophic_fungi",
        "arbuscular_mycorrhiza",
        "ectomycorrhiza",
    ]

    functional_groups = make_full_set_of_microbial_groups(
        fixture_config, enzyme_classes=enzyme_classes
    )

    assert set(expected_groups) == set(functional_groups.keys())

    for group in expected_groups:
        assert type(functional_groups[group]) is MicrobialGroupConstants

    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert functional_groups["bacteria"].c_n_ratio == 5.2
    assert functional_groups["saprotrophic_fungi"].c_n_ratio == 6.5


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
            taxonomic_group = "bacteria"
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
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005
            """,
            [
                (
                    CRITICAL,
                    "The following expected soil microbial groups are not defined: ",
                )
            ],
            id="missing_fungi",
        ),
        pytest.param(  # archaea included but they shouldn't be
            """
            [[soil.microbial_group_definition]]
            name = "bacteria"
            taxonomic_group = "bacteria"
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
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005

            [[soil.microbial_group_definition]]
            name = "saprotrophic_fungi"
            taxonomic_group = "fungi"
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
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005

            [[soil.microbial_group_definition]]
            name = "arbuscular_mycorrhiza"
            taxonomic_group = "fungi"
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
            c_n_ratio = 18.0
            c_p_ratio = 120.0
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005

            [[soil.microbial_group_definition]]
            name = "ectomycorrhiza"
            taxonomic_group = "fungi"
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
            c_n_ratio = 18.0
            c_p_ratio = 120.0
            enzyme_production.pom = 0.02
            enzyme_production.maom = 0.02

            [[soil.microbial_group_definition]]
            name = "archaea"
            taxonomic_group = "archaea"
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
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005
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
            taxonomic_group = "bacteria"
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
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005

            [[soil.microbial_group_definition]]
            name = "archaea"
            taxonomic_group = "archaea"
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
            enzyme_production.pom = 0.005
            enzyme_production.maom = 0.005
            """,
            [
                (
                    CRITICAL,
                    "The following expected soil microbial groups are not defined: ",
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
def test_make_full_set_of_microbial_groups_errors(
    caplog, enzyme_classes, cfg_strings, exp_log
):
    """Check that bad configs generate errors during microbial group generation."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_microbial_groups,
    )

    config = Config(cfg_strings=cfg_strings)
    caplog.clear()

    with pytest.raises(ConfigurationError):
        _ = make_full_set_of_microbial_groups(config, enzyme_classes=enzyme_classes)

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
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "maom"
            maximum_rate = 24.0
            half_saturation_constant = 350.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 5.2
            c_p_ratio = 16
            
            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "pom"
            maximum_rate = 120.0
            half_saturation_constant = 35.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 6.5
            c_p_ratio = 40.0
            """,
            [
                (
                    CRITICAL,
                    "The following expected enzyme classes are not defined: fungi_maom",
                )
            ],
            id="missing_fungi_maom",
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
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.enzyme_class_definition]]
            source = "bacteria"
            substrate = "maom"
            maximum_rate = 24.0
            half_saturation_constant = 350.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "pom"
            maximum_rate = 120.0
            half_saturation_constant = 35.0
            activation_energy_rate = 37000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 6.5
            c_p_ratio = 40.0

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "maom"
            maximum_rate = 48.0
            half_saturation_constant = 175.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 6.5
            c_p_ratio = 40.0

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "phosphate"
            maximum_rate = 48.0
            half_saturation_constant = 175.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 6.5
            c_p_ratio = 40.0
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
            c_n_ratio = 5.2
            c_p_ratio = 16

            [[soil.enzyme_class_definition]]
            source = "fungi"
            substrate = "phosphate"
            maximum_rate = 48.0
            half_saturation_constant = 175.0
            activation_energy_rate = 47000
            activation_energy_saturation = 30000
            reference_temperature = 12.0
            turnover_rate = 2.4e-2
            c_n_ratio = 6.5
            c_p_ratio = 40.0
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


def test_find_enzyme_substrates(fixture_config, enzyme_classes):
    """Check method to find the full set of substrates a microbe can use works."""
    from virtual_ecosystem.models.soil.microbial_groups import MicrobialGroupConstants

    bacteria = MicrobialGroupConstants.build_microbial_group(
        group_config=next(
            functional_group
            for functional_group in fixture_config["soil"]["microbial_group_definition"]
            if functional_group["name"] == "bacteria"
        ),
        enzyme_classes=enzyme_classes,
    )

    assert set(bacteria.find_enzyme_substrates()) == set(["maom", "pom"])


def test_build_microbial_group_errors(caplog, enzyme_classes):
    """Check that build_microbial_group factory method raises errors correctly."""
    from virtual_ecosystem.models.soil.microbial_groups import MicrobialGroupConstants

    group_config = {
        "name": "archaea",
        "taxonomic_group": "archaea",
        "max_uptake_rate_labile_C": 0.04,
        "activation_energy_uptake_rate": 47000,
        "half_sat_labile_C_uptake": 0.364,
        "activation_energy_uptake_saturation": 30000,
        "max_uptake_rate_ammonium": 5e-3,
        "half_sat_ammonium_uptake": 0.02275,
        "max_uptake_rate_nitrate": 5e-4,
        "half_sat_nitrate_uptake": 0.02275,
        "max_uptake_rate_labile_p": 0.0025,
        "half_sat_labile_p_uptake": 0.02275,
        "turnover_rate": 0.005,
        "activation_energy_turnover": 20000,
        "reference_temperature": 12.0,
        "c_n_ratio": 5.2,
        "c_p_ratio": 16,
        "enzyme_production": {"pom": 0.005, "maom": 0.005},
    }

    caplog.clear()

    exp_log = ((CRITICAL, "Taxonomic group archaea not allowed. Must be one of "),)

    with pytest.raises(ValueError):
        _ = MicrobialGroupConstants.build_microbial_group(
            group_config=group_config,
            enzyme_classes=enzyme_classes,
        )

    log_check(caplog, exp_log)


def test_find_microbial_stoichiometries(fixture_config):
    """Check that extraction of stoichiometries from microbial groups works."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        find_microbial_stoichiometries,
    )

    expected_ratios = {
        "bacteria": {"nitrogen": 5.2, "phosphorus": 16.0},
        "saprotrophic_fungi": {"nitrogen": 6.5, "phosphorus": 40.0},
        "arbuscular_mycorrhiza": {"nitrogen": 18.0, "phosphorus": 120.0},
        "ectomycorrhiza": {"nitrogen": 18.0, "phosphorus": 120.0},
    }

    actual_ratios = find_microbial_stoichiometries(config=fixture_config)

    assert expected_ratios == actual_ratios


def test_calculate_new_biomass_average_nutrient_ratios(fixture_config, enzyme_classes):
    """Check method to calculate average new biomass nutrient ratios works."""
    import numpy as np

    from virtual_ecosystem.models.soil.microbial_groups import (
        calculate_new_biomass_average_nutrient_ratios,
    )

    group_config = next(
        functional_group
        for functional_group in fixture_config["soil"]["microbial_group_definition"]
        if functional_group["taxonomic_group"] == "bacteria"
    )

    averaged_nutrient_ratios = calculate_new_biomass_average_nutrient_ratios(
        taxonomic_group=group_config["taxonomic_group"],
        c_n_ratio=5.7,
        c_p_ratio=15.5,
        enzyme_production=group_config["enzyme_production"],
        enzyme_classes=enzyme_classes,
    )

    assert np.isclose(averaged_nutrient_ratios["nitrogen"], 5.695)
    assert np.isclose(averaged_nutrient_ratios["phosphorus"], 15.505)


def test_calculate_symbiotic_carbon_supply(dummy_carbon_data):
    """Test that calculation of splitting of carbon supply between symbiotes works."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
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
        / CoreConsts.max_depth_of_microbial_activity,
        nitrogen_fixer_fraction=SoilConsts.nitrogen_fixer_supply_fraction,
        ectomycorrhiza_fraction=SoilConsts.ectomycorrhiza_supply_fraction,
    )

    # Check all (non-private) dataclass attributes against the dictionary
    for attr in dir(actual_supply):
        if not attr.startswith("_"):
            assert attr in expected_supply.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_supply, attr), expected_supply[attr])
