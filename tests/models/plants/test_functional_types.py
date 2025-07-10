"""Test module for plants.functional_types.py.

This module tests the functionality of the plant functional types submodule.
"""

import pytest

from virtual_ecosystem.models.plants.functional_types import ExtraTraitsPFT


def test_get_flora_from_config(shared_datadir, fixture_config):
    """Testing the pyrealm flora loading mechanism.

    This tests the loader in two different configurations (data in TOML, data in CSV)
    and checks the loader fails if both are present.
    """

    from pyrealm.demography.flora import Flora

    from virtual_ecosystem.core.exceptions import ConfigurationError
    from virtual_ecosystem.models.plants.functional_types import get_flora_from_config

    # Initial fixture_config uses PFT definitions in the file
    flora, extra_traits = get_flora_from_config(fixture_config)

    assert isinstance(flora, Flora)
    assert flora.n_pfts == 2

    # Update to add a path _without_ removing local definitions
    fixture_config["plants"]["pft_definitions_path"] = shared_datadir / "pfts.csv"

    with pytest.raises(ConfigurationError) as err:
        flora, extra_traits = get_flora_from_config(fixture_config)

    assert (
        str(err.value)
        == "Do not use both `pft_definitions_path` and `pft_definition` in config."
    )

    # Remove original local definitions
    fixture_config["plants"].pop("pft_definition")

    flora, extra_traits = get_flora_from_config(fixture_config)

    assert isinstance(flora, Flora)
    assert flora.n_pfts == 2

    assert isinstance(extra_traits, ExtraTraitsPFT)
