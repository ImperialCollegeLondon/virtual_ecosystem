"""Test module for soil.microbial_groups.py.

This module tests the functions which generate microbial functional groups.
"""

from typing import get_args

import numpy as np
import pytest


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
            {"nitrogen": 5.936557, "phosphorus": 16.79287},
            id="fungi",
        ),
    ],
)
def test_calculate_new_biomass_average_nutrient_ratios(
    fixture_configuration, enzyme_classes, group, expected_ratio, fixture_core_constants
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
        c_n_ratio_fruiting_bodies=fixture_core_constants.fungal_fruiting_bodies_c_n_ratio,
        c_p_ratio_fruiting_bodies=fixture_core_constants.fungal_fruiting_bodies_c_p_ratio,
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
