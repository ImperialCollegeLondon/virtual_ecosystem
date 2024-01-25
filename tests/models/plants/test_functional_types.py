"""Test module for plants.functional_types.py.

This module tests the functionality of the plant functional types submodule.
"""


def test_plant_functional_type():
    """Simple test of PlantFunctionalType dataclass."""
    from virtual_rainforest.models.plants.functional_types import PlantFunctionalType

    pft = PlantFunctionalType(pft_name="tree", max_height=12.0)

    assert pft.pft_name == "tree"
    assert pft.max_height == 12.0


def test_flora__init__():
    """Simple test of Flora __init__."""
    from virtual_rainforest.models.plants.functional_types import (
        Flora,
        PlantFunctionalType,
    )

    flora = Flora(
        [
            PlantFunctionalType(pft_name="shrub", max_height=1.0),
            PlantFunctionalType(pft_name="broadleaf", max_height=50.0),
        ]
    )

    assert len(flora) == 2
    assert tuple(flora.keys()) == ("shrub", "broadleaf")


def test_plant_functional_types_from_config(fixture_config):
    """Simple test of Flora from_config factory method."""

    from virtual_rainforest.models.plants.functional_types import Flora

    flora = Flora.from_config(fixture_config)

    assert len(flora) == 2
    assert tuple(flora.keys()) == ("shrub", "broadleaf")
