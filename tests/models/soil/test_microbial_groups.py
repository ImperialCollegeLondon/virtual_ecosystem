"""Test module for soil.microbial_groups.py.

This module tests the functions which generate microbial functional groups.
"""


def test_make_full_set_of_microbial_groups():
    """Test that the function to make all the microbial group works."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.microbial_groups import (
        MicrobialGroup,
        make_full_set_of_microbial_groups,
    )

    expected_groups = ["bacteria", "fungi"]

    functional_groups = make_full_set_of_microbial_groups(SoilConsts)

    assert set(expected_groups) == set(functional_groups.keys())

    for group in expected_groups:
        assert type(functional_groups[group]) is MicrobialGroup

    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert functional_groups["bacteria"].c_n_ratio == 5.2
    assert functional_groups["fungi"].c_n_ratio == 6.5


def test_make_bacterial_functional_group():
    """Test that the function to make the bacterial functional group works."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.microbial_groups import (
        MicrobialGroup,
        make_bacterial_functional_group,
    )

    bacterial_group = make_bacterial_functional_group(SoilConsts)
    assert type(bacterial_group) is MicrobialGroup
    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert bacterial_group.c_n_ratio == 5.2


def test_make_fungal_functional_group():
    """Test that the function to make the fungal functional group works."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.microbial_groups import (
        MicrobialGroup,
        make_fungal_functional_group,
    )

    fungal_group = make_fungal_functional_group(SoilConsts)
    assert type(fungal_group) is MicrobialGroup
    # Only testing one value, as testing them all seems like overkill/hard to maintain
    assert fungal_group.c_n_ratio == 6.5
