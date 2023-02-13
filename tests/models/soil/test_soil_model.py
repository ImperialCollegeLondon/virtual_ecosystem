"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.model import InitialisationError
from virtual_rainforest.models.soil.soil_model import SoilModel


@pytest.fixture
def data_instance():
    """Simple data instance to use in model init."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    grid = Grid()
    return Data(grid)


@pytest.mark.parametrize(
    "no_layers,raises,expected_log_entries",
    [
        (
            2,
            does_not_raise(),
            (),
        ),
        (
            -2,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "There has to be at least one soil layer in the soil model!",
                ),
            ),
        ),
        (
            2.5,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The number of soil layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_soil_model_initialization(
    caplog, data_instance, no_layers, raises, expected_log_entries
):
    """Test `SoilModel` initialization."""

    with raises:
        # Initialize model
        model = SoilModel(
            data_instance, timedelta64(1, "W"), datetime64("2022-11-01"), no_layers
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.model_name == "soil"
        assert str(model) == "A soil model instance"
        assert (
            repr(model)
            == f"SoilModel(update_interval = 1 weeks, next_update = 2022-11-08, "
            f"no_layers = {int(no_layers)})"
        )

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
                "core": {"timing": {"start_time": "2020-01-01"}},
                "soil": {"no_layers": 2, "model_time_step": "12 hours"},
            },
            timedelta64(12, "h"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
            ),
        ),
    ],
)
def test_generate_soil_model(
    caplog, data_instance, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(data_instance, config)
        assert model.no_layers == config["soil"]["no_layers"]
        assert model.update_interval == time_interval
        assert (
            model.next_update
            == datetime64(config["core"]["timing"]["start_time"]) + time_interval
        )
        # Run the update step and check that next_update has incremented properly
        model.update()
        assert (
            model.next_update
            == datetime64(config["core"]["timing"]["start_time"]) + 2 * time_interval
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
