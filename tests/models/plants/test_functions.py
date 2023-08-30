"""Tests the handler functions in models.plants.functions."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import pytest
from numpy import ndarray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_generate_canopy_model(plants_data, flora):
    """Test the function to turn a community list into a canopy model."""

    # TODO - the functionality in this function does nothing at the moment, so this
    #        method just tests data handling

    from virtual_rainforest.models.plants.community import PlantCommunities
    from virtual_rainforest.models.plants.functions import generate_canopy_model

    communities = PlantCommunities(plants_data, flora)

    for _, community in communities.items():
        layer_hght, layer_lai = generate_canopy_model(community=community)

        assert isinstance(layer_hght, ndarray)
        assert isinstance(layer_lai, ndarray)


@pytest.mark.parametrize(
    argnames="max_layers, raises, exp_log",
    argvalues=[
        (10, does_not_raise(), None),
        (5, does_not_raise(), None),
        (
            1,
            pytest.raises(ConfigurationError),
            (
                (
                    CRITICAL,
                    "Generated canopy has more layers than the configured maximum",
                ),
            ),
        ),
    ],
)
def test_build_canopy_arrays(caplog, plants_data, flora, max_layers, raises, exp_log):
    """Test the function to turn PlantsCommunities into canopy arrays."""

    from virtual_rainforest.models.plants.community import PlantCommunities
    from virtual_rainforest.models.plants.functions import build_canopy_arrays

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    communities = PlantCommunities(plants_data, flora)

    with raises:
        layer_hght, layer_lai = build_canopy_arrays(
            communities=communities, n_canopy_layers=max_layers
        )

        if isinstance(raises, does_not_raise):
            assert layer_hght.shape == (max_layers, len(communities))
            assert layer_lai.shape == (max_layers, len(communities))

        if exp_log is not None:
            log_check(caplog, exp_log)


def test_initialise_canopy_layers(caplog, plants_data):
    """Test the function to initialise canopy layers in the data object."""

    from virtual_rainforest.models.plants.functions import initialise_canopy_layers

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    data = initialise_canopy_layers(plants_data, n_canopy_layers=10, n_soil_layers=3)

    assert "layer_heights" in data
    assert "leaf_area_index" in data

    exp_shape = (1 + 10 + 2 + 3, len(data.grid.cell_id))
    assert data["layer_heights"].shape == exp_shape
    assert data["leaf_area_index"].shape == exp_shape
