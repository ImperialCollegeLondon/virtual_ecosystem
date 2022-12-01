"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO, WARNING

import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.model import BaseModel, InitialisationError
from virtual_rainforest.soil.model import SoilModel

from .conftest import log_check


def test_base_model_initialization(caplog, mocker):
    """Test `BaseModel` initialization."""

    # Patch abstract methods so that BaseModel can be instantiated for testing
    mocker.patch.object(BaseModel, "__abstractmethods__", new_callable=set)

    # Initialise model
    model = BaseModel(timedelta64(1, "W"), datetime64("2022-11-01"))

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
    assert model.name == "base"
    assert str(model) == "A base model instance"
    assert (
        repr(model) == "BaseModel(update_interval = 1 weeks, next_update = 2022-11-08)"
    )


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
                    CRITICAL,
                    "There has to be at least one soil layer in the soil model!",
                ),
            ),
        ),
        (
            2.5,
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "The number of soil layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_soil_model_initialization(caplog, no_layers, raises, expected_log_entries):
    """Test `SoilModel` initialization."""

    with raises:
        # Initialize model
        model = SoilModel(timedelta64(1, "W"), datetime64("2022-11-01"), no_layers)

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.name == "soil"
        assert str(model) == "A soil model instance"
        assert (
            repr(model)
            == f"SoilModel(update_interval = 1 weeks, next_update = 2022-11-08, "
            f"no_layers = {int(no_layers)})"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_register_model_errors(caplog):
    """Test that the schema registering models generates correct errors/warnings."""

    class NewSoilModel(BaseModel, model_name="soil"):
        """Test class for use in testing __init_subclass__."""

    # Then check that the correct (warning) log messages are emitted
    expected_log_entries = (
        (
            WARNING,
            "Model with name soil already exists and is being replaced",
        ),
    )
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
    caplog, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(config)
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
