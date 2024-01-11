"""Test module for abiotic.abiotic_model.energy_balance.py."""

import numpy as np


def test_initialise_absorbed_radiation():
    """Test initial absorbed radiation has correct dimensions."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        initialise_absorbed_radiation,
    )

    result = initialise_absorbed_radiation(
        topofcanopy_radiation=np.array([100, 50]),
        leaf_area_index=np.array([[1, 1, 1], [1, 1, 1]]),
        canopy_layer_heights=np.array([[10, 5, 2], [10, 5, 2]]),
        light_extinction_coefficient=0.01,
    )

    np.testing.assert_allclose(result, np.array([[5, 3, 2], [3, 2, 1]]))
