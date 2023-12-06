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
        canopy_data = generate_canopy_model(community=community)

        assert isinstance(canopy_data[0], ndarray)  # layer_hght
        assert isinstance(canopy_data[1], ndarray)  # layer_lai
        assert isinstance(canopy_data[2], ndarray)  # layer_fapar
        assert isinstance(canopy_data[3], ndarray)  # layer_leaf_mass

        assert np.all([arr.ndim == 1 for arr in canopy_data])

        for cohort in community:
            assert np.allclose(
                cohort.canopy_area,
                np.array([5, 5, 5]),
            )


@pytest.mark.parametrize(
    argnames="max_layers, raises, exp_log",
    argvalues=[
        pytest.param(10, does_not_raise(), None, id="many_layers"),
        pytest.param(5, does_not_raise(), None, id="enough_layers"),
        pytest.param(
            1,
            pytest.raises(ConfigurationError),
            (
                (
                    CRITICAL,
                    "Generated canopy has more layers than the configured maximum",
                ),
            ),
            id="not_enough_layers",
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
        # Build the canopy layers, which takes the generated canopy model, pads to the
        # configured maximum and stacks into arrays by cell id
        canopy_data = build_canopy_arrays(
            communities=communities, n_canopy_layers=max_layers
        )

        # Check the canopy layers arrays are the right size and that the
        # cohort.canopy_areas have been padded successfully
        if isinstance(raises, does_not_raise):
            for arr in canopy_data:
                assert arr.shape == (max_layers, len(communities))

            for community in communities.values():
                for cohort in community:
                    assert cohort.canopy_area.shape == (max_layers,)

        if exp_log is not None:
            log_check(caplog, exp_log)


def test_initialise_canopy_layers(plants_data, layer_structure):
    """Test the function to initialise canopy layers in the data object."""

    from virtual_rainforest.models.plants.canopy import initialise_canopy_layers

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    data = initialise_canopy_layers(data=plants_data, layer_structure=layer_structure)

    # Set up expectations
    expected_layers = (
        "layer_heights",
        "leaf_area_index",
        "layer_fapar",
        "layer_leaf_mass",
        "layer_absorbed_irradiation",
    )

    n_layer = 1 + 10 + 2 + 2
    exp_shape = (n_layer, data.grid.n_cells)

    exp_dims = {
        "layers": (True, n_layer),
        "layer_roles": (False, n_layer),
        "cell_id": (True, data.grid.n_cells),
    }

    # Check each layer is i) in the data object, ii) has the right shape, iii) has the
    # expected dimensions and iv) has coordinates with the right lengths.
    for layer in expected_layers:
        assert layer in data
        assert data[layer].shape == exp_shape

        for key, (is_dim, exp_n) in exp_dims.items():
            # Check the names, dimensions and coords
            if is_dim:
                assert key in data[layer].dims

            assert key in data[layer].coords
            assert len(data[layer].coords[key]) == exp_n

    # Specifically for layer heights, check that the fixed layer heights are as expected
    assert np.allclose(
        data["layer_heights"].mean(dim="cell_id").to_numpy(),
        np.array([np.nan] * 11 + [1.5, 0.1, -0.5, -1.0]),
        equal_nan=True,
    )
