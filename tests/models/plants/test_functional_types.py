"""Test module for plants.functional_types.py.

This module tests the functionality of the plant functional types submodule.
"""

from virtual_ecosystem.models.plants.functional_types import ExtraTraitsPFT


def test_get_flora_from_config(fixture_configuration):
    """Testing the pyrealm flora loading mechanism.

    This tests the loader in two different configurations (data in TOML, data in CSV)
    and checks the loader fails if both are present.
    """

    from pyrealm.demography.flora import Flora

    from virtual_ecosystem.models.plants.functional_types import get_flora_from_config

    # Initial fixture_config uses PFT definitions in the file
    flora, extra_traits = get_flora_from_config(config=fixture_configuration.plants)

    assert isinstance(flora, Flora)
    assert flora.n_pfts == 2
    assert isinstance(extra_traits, ExtraTraitsPFT)
