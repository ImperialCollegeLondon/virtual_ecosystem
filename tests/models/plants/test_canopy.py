"""Tests the handler functions in models.plants.canopy."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import numpy as np
import pytest
from numpy import ndarray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_generate_canopy_model(plants_data, flora):
    """Test the function to turn a community list into a canopy model."""

    # TODO - the functionality in this function does nothing at the moment, so this
    #        method just tests data handling

    from virtual_rainforest.models.plants.canopy import generate_canopy_model
    from virtual_rainforest.models.plants.community import PlantCommunities

    communities = PlantCommunities(plants_data, flora)

    for _, community in communities.items():
        layer_hght, layer_lai, layer_fapar = generate_canopy_model(community=community)

        assert isinstance(layer_hght, ndarray)
        assert isinstance(layer_lai, ndarray)
        assert isinstance(layer_fapar, ndarray)

        for cohort in community:
            assert np.allclose(
                cohort.canopy_area,
                np.array([5, 5, 5]),
            )


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

    from virtual_rainforest.models.plants.canopy import build_canopy_arrays
    from virtual_rainforest.models.plants.community import PlantCommunities

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    communities = PlantCommunities(plants_data, flora)

    with raises:
        layer_hght, layer_lai, layer_fapar = build_canopy_arrays(
            communities=communities, n_canopy_layers=max_layers
        )

        if isinstance(raises, does_not_raise):
            assert layer_hght.shape == (max_layers, len(communities))
            assert layer_lai.shape == (max_layers, len(communities))
            assert layer_fapar.shape == (max_layers, len(communities))

        if exp_log is not None:
            log_check(caplog, exp_log)


def test_initialise_canopy_layers(caplog, plants_data):
    """Test the function to initialise canopy layers in the data object."""

    from virtual_rainforest.models.plants.canopy import initialise_canopy_layers

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    data = initialise_canopy_layers(plants_data, n_canopy_layers=10, n_soil_layers=3)

    # Set up expectations
    expected_layers = [
        "layer_heights",
        "leaf_area_index",
        "layer_fapar",
        "layer_absorbed_irradiation",
    ]

    n_layer = 1 + 10 + 2 + 3
    exp_shape = (n_layer, data.grid.n_cells)

    exp_dims = {
        "layers": (True, n_layer),
        "layer_roles": (False, n_layer),
        "cell_id": (True, data.grid.n_cells),
    }

    # Check each layer is i) in the data object, ii) has the right shape, iii) has the
    # expected dimensions and iv) has coordinates with the right lengths.
    for lyr in expected_layers:
        assert lyr in data
        assert data[lyr].shape == exp_shape

        for key, (is_dim, exp_n) in exp_dims.items():
            # Check the names, dimensions and coords
            if is_dim:
                assert key in data[lyr].dims

            assert key in data[lyr].coords
            assert len(data[lyr].coords[key]) == exp_n
