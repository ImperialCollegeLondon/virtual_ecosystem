"""Test soil.model_config."""

from contextlib import nullcontext as does_not_raise
from itertools import permutations

import pytest
from pydantic import ValidationError


def test_SoilConstants_pH():
    """Test the custom validation on SoilConstants model.

    This tests all possible orderings of the four microbe pH variables.
    """
    from virtual_ecosystem.models.soil.model_config import SoilConstants

    defaults = (2.5, 4.5, 7.5, 11.0)
    keys = [
        "min_pH_microbes",
        "lowest_optimal_pH_microbes",
        "highest_optimal_pH_microbes",
        "max_pH_microbes",
    ]

    for perm in permutations(defaults):
        if perm == defaults:
            # If the ordering is the same as the defaults, all is good
            outcome = does_not_raise()
        else:
            # Otherwise not.
            outcome = pytest.raises(ValidationError)

        with outcome:
            _ = SoilConstants(**dict(zip(keys, perm)))
