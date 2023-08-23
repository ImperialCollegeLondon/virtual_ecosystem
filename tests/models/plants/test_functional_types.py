"""Test module for plants.functional_types.py.

This module tests the functionality of the plant functional types submodule.
"""

import pytest


@pytest.fixture()
def plant_config(shared_datadir):
    """Simple configuration fixture for use in tests."""

    from virtual_rainforest.core.config import Config

    return Config(shared_datadir / "all_config.toml")


def test_plant_functional_type():
    """Simple test of PlantFunctionalType dataclass."""
    from virtual_rainforest.models.plants.functional_types import PlantFunctionalType

    pft = PlantFunctionalType(pft_name="tree", maxh=12.0)

    assert pft.pft_name == "tree"
    assert pft.maxh == 12.0


def test_plant_functional_types__init__():
    """Simple test of PlantFunctionalTypes __init__."""
    from virtual_rainforest.models.plants.functional_types import (
        PlantFunctionalType,
        PlantFunctionalTypes,
    )

    pfts = PlantFunctionalTypes(
        {
            "shrub": PlantFunctionalType(pft_name="shrub", maxh=1.0),
            "broadleaf": PlantFunctionalType(pft_name="broadleaf", maxh=50.0),
        }
    )

    assert len(pfts) == 2
    assert tuple(pfts.keys()) == ("shrub", "broadleaf")


def test_plant_functional_types_from_config(plant_config):
    """Simple test of PlantFunctionalTypes from_config factory method."""

    from virtual_rainforest.models.plants.functional_types import PlantFunctionalTypes

    pfts = PlantFunctionalTypes.from_config(plant_config)

    assert len(pfts) == 2
    assert tuple(pfts.keys()) == ("shrub", "broadleaf")
