"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest
from numpy import timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)


@pytest.mark.parametrize(
    "soil_layers,canopy_layers,raises,expected_log_entries",
    [
        (
            2,
            3,
            does_not_raise(),
            (),
        ),
        (
            -2,
            3,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "There has to be at least one soil layer in the abiotic model!",
                ),
            ),
        ),
        (
            2,
            -3,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "There has to be at least one canopy layer in the abiotic model!",
                ),
            ),
        ),
        (
            2.5,
            3,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The number of soil layers must be an integer!",
                ),
            ),
        ),
        (
            2,
            3.4,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The number of canopy layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_abiotic_simple_model_initialization(
    caplog, data_instance, soil_layers, canopy_layers, raises, expected_log_entries
):
    """Test `AbioticSimpleModel` initialization."""

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            data_instance,
            timedelta64(1, "W"),
            soil_layers,
            canopy_layers,
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.model_name == "abiotic_simple"
        assert (
            repr(model) == f"AbioticSimpleModel(update_interval = 1 weeks, "
            f"soil_layers = {int(soil_layers)}, "
            f"canopy_layers = {int(canopy_layers)})"
        )
        assert model.soil_layers == soil_layers
        assert model.canopy_layers == canopy_layers

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval,raises,expected_log_entries",
    [
        (
            {},
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 hours",
                    }
                },
                "abiotic_simple": {
                    "soil_layers": 2,
                    "canopy_layers": 3,
                },
            },
            timedelta64(12, "h"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
            ),
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog, data_instance, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticSimpleModel.from_config(data_instance, config)
        assert model.soil_layers == config["abiotic_simle"]["soil_layers"]
        assert model.canopy_layers == config["abiotic_simple"]["canopy_layers"]
        assert model.update_interval == time_interval

        # Run the update step (once this does something should check output)
        model.update()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update_data_object():
    """Test reading from list."""
    import numpy as np
    from xarray import DataArray

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        update_data_object,
    )

    # Setup the data object with two cells.
    grid = Grid(cell_nx=3, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["air_temperature_ref"] = DataArray(
        np.full((3, 3), 30),
        dims=["cell_id", "time"],
        name="air_temperature_ref",
    )
    data["mean_annual_temperature"] = DataArray(
        np.full((3), 20),
        dims=["cell_id"],
        name="mean_annual_temperature",
    )

    var_list = [
        DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            name="air_temperature_ref",
        ),
        DataArray(np.full((3), 40), dims=["cell_id"], name="mean_annual_temperature"),
        DataArray(np.full((3), 100), dims=["cell_id"], name="new_variable"),
    ]
    update_data_object(data, var_list)

    assert data["air_temperature_ref"] == DataArray(
        np.full((3, 3), 20),
        dims=["cell_id", "time"],
        name="air_temperature_ref",
    )
    assert data["mean_annual_temperature"] == DataArray(
        np.full((3), 40),
        dims=["cell_id"],
        name="mean_annual_temperature",
    )
    assert data["new_variable"] == DataArray(
        np.full((3), 100), dims=["cell_id"], name="new_variable"
    )
