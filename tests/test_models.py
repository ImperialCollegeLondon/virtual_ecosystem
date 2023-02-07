"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO, WARNING

import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.model import BaseModel, InitialisationError
from virtual_rainforest.models.abiotic.model import AbioticModel
from virtual_rainforest.models.soil.model import SoilModel

from .conftest import log_check


def test_base_model_initialization(caplog, mocker):
    """Test `BaseModel` initialization."""

    # Patch abstract methods so that BaseModel can be instantiated for testing
    mocker.patch.object(BaseModel, "__abstractmethods__", new_callable=set)

    # Initialise model
    model = BaseModel(timedelta64(1, "W"), datetime64("2022-11-01"))

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
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
    "name,raises,expected_log_entries",
    [
        (
            27,
            pytest.raises(TypeError),
            ((CRITICAL, "Models should only be named using strings!"),),
        ),
        (
            "soil",
            does_not_raise(),
            (
                (
                    WARNING,
                    "Model with name soil already exists and is being replaced",
                ),
            ),
        ),
        (
            "abiotic",
            does_not_raise(),
            (
                (
                    WARNING,
                    "Model with name abiotic already exists and is being replaced",
                ),
            ),
        ),
        (
            "freshwater",
            does_not_raise(),
            (),
        ),
    ],
)
def test_register_model_errors(caplog, name, raises, expected_log_entries):
    """Test that the function registering models generates correct errors/warnings."""

    with raises:

        class NewSoilModel(BaseModel):
            """Test class for use in testing __init_subclass__."""

            model_name = name
            """The model name for use in registering the model and logging."""

    # Then check that the correct (warning) log messages are emitted
    log_check(caplog, expected_log_entries)


def test_unnamed_model(caplog):
    """Test that the registering a model without a name fails correctly."""

    with pytest.raises(ValueError):

        class UnnamedModel(BaseModel):
            """Model where a model_name hasn't been included."""

    expected_log_entries = ((CRITICAL, "Models must have a model_name attribute!"),)

    # Then check that the correct (warning) log messages are emitted
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


# -------------------------------------
# abiotic model tests
# -------------------------------------


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
                    CRITICAL,
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
                    CRITICAL,
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
                    CRITICAL,
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
                    CRITICAL,
                    "The number of canopy layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_abiotic_model_initialization(
    caplog, soil_layers, canopy_layers, raises, expected_log_entries
):
    """Test `AbioticModel` initialization."""

    with raises:
        # Initialize model
        model = AbioticModel(
            timedelta64(1, "W"), datetime64("2022-11-01"), soil_layers, canopy_layers
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.model_name == "abiotic"
        assert (
            repr(model)
            == f"AbioticModel(update_interval = 1 weeks, next_update = 2022-11-08, "
            f"soil_layers = {int(soil_layers)}, "
            f"canopy_layers = {int(canopy_layers)})"
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
                "abiotic": {
                    "soil_layers": 2,
                    "canopy_layers": 3,
                    "model_time_step": "12 hours",
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
def test_generate_abiotic_model(
    caplog, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticModel.from_config(config)
        assert model.soil_layers == config["abiotic"]["soil_layers"]
        assert model.canopy_layers == config["abiotic"]["canopy_layers"]
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
