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


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
@pytest.mark.parametrize(
    "max_canopy_layers, expected_exception, expected_log",
    [
        pytest.param(10, does_not_raise(), None, id="10_layers"),
        pytest.param(5, does_not_raise(), None, id="5_layers"),
        pytest.param(
            1,
            pytest.raises(RuntimeError),
            (
                (
                    CRITICAL,
                    "Canopy representation for the plant community in cell 1 has 3 "
                    "layers, configured maximum is 1",
                ),
            ),
            id="1_layer",
        ),
    ],
)
def test_calculate_canopies(
    caplog,
    fixture_core_components,
    plants_cohort_data,
    fixture_flora,
    max_canopy_layers,
    expected_exception,
    expected_log,
    tricky_plant_cohorts,
):
    """Test the calculate_canopies function with different max_canopy_layers values.

    This does not use the tricky cohorts because it is primarily aimed at checking the
    layer clipping. The test_PlantsModel_update_canopy_layers test is aimed at
    validating the expected arrays of layer heights etc.
    """
    from pyrealm.demography.canopy import Canopy
    from pyrealm.demography.cohorts import cohort_id_generator

    from virtual_ecosystem.models.plants.canopy import calculate_canopies
    from virtual_ecosystem.models.plants.communities import PlantCommunities

    communities = PlantCommunities(
        cohort_id_generator=cohort_id_generator(mode="str"),
        cohort_data=plants_cohort_data,
        flora=fixture_flora,
        grid=fixture_core_components.grid,
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
