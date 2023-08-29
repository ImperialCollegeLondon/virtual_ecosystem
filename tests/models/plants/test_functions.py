"""Tests the handler functions in models.plants.functions."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    argnames="max_layers, raises, msg",
    argvalues=[
        (10, does_not_raise(), None),
        (5, does_not_raise(), None),
        (
            3,
            pytest.raises(ConfigurationError),
            (
                (
                    CRITICAL,
                    "Generated canopy has more layers than the configured maximum.",
                ),
            ),
        ),
    ],
)
def test_generate_canopy_model(plant_data, pfts, max_layers, raises, exp_log):
    """Test the function to turn a community list into a canopy model."""

    # TODO - the functionality in this function does very little at the moment, so this
    #        method just tests data handling and exceptions

    from virtual_rainforest.models.plants.community import PlantCommunities
    from virtual_rainforest.models.plants.functions import generate_canopy_model

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    communities = PlantCommunities(plant_data, pfts)

    for _, community in communities:
        with raises:
            layer_hght, layer_lai = generate_canopy_model(
                community=community, max_layers=max_layers
            )

            if isinstance(raises, does_not_raise):
                assert len(layer_hght) == max_layers
                assert len(layer_lai) == max_layers

        log_check(exp_log)
