"""Tests the handler functions in models.plants.canopy."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import numpy as np
import pytest

from tests.conftest import log_check


def test_initialise_canopy_layers(plants_data, fixture_core_components):
    """Test the function to initialise canopy layers in the data object."""

    from virtual_ecosystem.models.plants.canopy import initialise_canopy_layers

    # Use fixture communities for now - this may need parameterised communities in the
    # future to try and trigger various warning - or might not.
    data = initialise_canopy_layers(
        data=plants_data, layer_structure=fixture_core_components.layer_structure
    )

    # Set up expectations
    expected_layers = (
        "layer_heights",
        "leaf_area_index",
        "layer_fapar",
        "layer_leaf_mass",
        "shortwave_absorption",
    )

    exp_shape = (
        fixture_core_components.layer_structure.n_layers,
        fixture_core_components.grid.n_cells,
    )

    exp_dims = {
        "layers": (True, fixture_core_components.layer_structure.n_layers),
        "layer_roles": (False, fixture_core_components.layer_structure.n_layers),
        "cell_id": (True, fixture_core_components.grid.n_cells),
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
        data["layer_heights"].to_numpy(),
        np.tile(np.array([[np.nan] * 11 + [0.1, -0.5, -1.0]]).T, 4),
        equal_nan=True,
    )


@pytest.mark.parametrize(
    "max_canopy_layers, expected_exception, expected_log",
    [
        (10, does_not_raise(), None),
        (5, does_not_raise(), None),
        (
            1,
            pytest.raises(RuntimeError),
            (
                (
                    CRITICAL,
                    "Canopy representation for the plant community in cell 1 has 3 "
                    "layers, configured maximum is 1",
                ),
            ),
        ),
    ],
)
def test_calculate_canopies(
    caplog,
    fixture_core_components,
    plants_cohort_data,
    flora,
    max_canopy_layers,
    expected_exception,
    expected_log,
):
    """Test the calculate_canopies function with different max_canopy_layers values."""
    from pyrealm.demography.canopy import Canopy

    from virtual_ecosystem.models.plants.canopy import calculate_canopies
    from virtual_ecosystem.models.plants.communities import PlantCommunities

    communities = PlantCommunities(
        cohort_data=plants_cohort_data, flora=flora, grid=fixture_core_components.grid
    )

    with expected_exception:
        canopies = calculate_canopies(communities, max_canopy_layers)

        if expected_exception is does_not_raise():
            assert isinstance(canopies, dict)
            for canopy in canopies.values():
                assert isinstance(canopy, Canopy)
                assert canopy.heights.size <= max_canopy_layers

        if expected_log is not None:
            log_check(caplog, expected_log)
