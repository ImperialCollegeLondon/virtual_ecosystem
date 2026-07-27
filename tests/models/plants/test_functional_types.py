"""Test module for plants.functional_types.py.

This module tests the functionality of the plant functional types submodule.
"""


def test_get_flora_from_config(fixture_configuration):
    """Testing the pyrealm flora loading mechanism.

    Checks that VEFlora (an extended pyrealm Flora class) loads from CSV and populates
    the required extra fields.
    """

    from virtual_ecosystem.models.plants.functional_types import (
        VEFlora,
        get_flora_from_config,
    )

    # Initial fixture_config uses PFT definitions in the file
    flora = get_flora_from_config(config=fixture_configuration.plants)

    assert isinstance(flora, VEFlora)

    # Check one of the extended properties is present
    assert "deadwood_c_n_ratio" in flora.model_fields_set

    # Check the reference values have been copied across
    assert flora.lai == flora.lai_base
    assert flora.tau_f == flora.tau_f_base

    # Check the fruit flesh fraction has been populated
    assert flora.fruit_flesh_fraction == (5 / 6, 3 / 4)
