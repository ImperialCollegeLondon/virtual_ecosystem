"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO, WARNING

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
    model = BaseModel(timedelta64(1, "W"))

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "solve", "cleanup"]).issubset(dir(model))
    assert model.name == "base"
    assert str(model) == "A base model instance"
    assert repr(model) == "BaseModel(update_interval = 1 weeks)"
    assert model.should_update(datetime64("2023-10-26"))
    assert not model.should_update(datetime64("2022-10-28"))

    # Final check that expected (i.e. no) logging entries are produced
    log_check(
        caplog,
        (),
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
        model = SoilModel(timedelta64(1, "W"), no_layers)

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "solve", "cleanup"]).issubset(dir(model))
        assert model.name == "soil"
        assert str(model) == "A soil model instance"
        assert (
            repr(model)
            == f"SoilModel(update_interval = 1 weeks, no_layers = {int(no_layers)})"
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
    "config,valid,expected_log_entries",
    [
        (
            {},
            False,
            (
                (
                    ERROR,
                    "Configuration is missing information required to initialise the "
                    "soil model. The first missing key is 'core'",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "min_time_step": "0.5 days",
                    }
                },
                "soil": {"no_layers": 2},
            },
            True,
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
def test_generate_soil_model(caplog, config, valid, expected_log_entries):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    model = SoilModel.factory(config)
    if valid is False:
        assert model is None
    else:
        assert model.no_layers == config["soil"]["no_layers"]

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
