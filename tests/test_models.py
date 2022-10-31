"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO, WARNING

import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.model import BaseModel, register_model
from virtual_rainforest.soil import generate_soil_model
from virtual_rainforest.soil.model import InitialisationError, SoilModel

from .conftest import log_check


@pytest.mark.parametrize(
    "start_time,end_time,update_interval,raises,expected_log_entries",
    [
        (
            datetime64("2022-10-26"),
            datetime64("2052-10-26"),
            timedelta64(1, "W"),
            does_not_raise(),
            (),
        ),
        (
            datetime64("2052-10-26"),
            datetime64("2022-10-26"),
            timedelta64(1, "W"),
            pytest.raises(ValueError),
            (
                (
                    CRITICAL,
                    "Model cannot end at an earlier time than it starts!",
                ),
            ),
        ),
    ],
)
def test_base_model_initialization(
    caplog, start_time, end_time, update_interval, raises, expected_log_entries
):
    """Test `BaseModel` initialization."""

    # Check whether initialising the model fails as expected
    with raises:
        model = BaseModel(start_time, end_time, update_interval)

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "solve", "cleanup"]).issubset(dir(model))
        assert model.name == "base"
        assert str(model) == "A base model instance"
        assert (
            repr(model) == "BaseModel(start_time=2022-10-26, end_time=2052-10-26,"
            " update_interval=1 weeks)"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "start_time,end_time,no_layers,raises,expected_log_entries",
    [
        (
            datetime64("2022-10-26"),
            datetime64("2052-10-26"),
            2,
            does_not_raise(),
            (),
        ),
        (
            datetime64("2052-10-26"),
            datetime64("2022-10-26"),
            2,
            pytest.raises(ValueError),
            (
                (
                    CRITICAL,
                    "Model cannot end at an earlier time than it starts!",
                ),
            ),
        ),
        (
            datetime64("2022-10-26"),
            datetime64("2052-10-26"),
            -2,
            pytest.raises(ValueError),
            (
                (
                    CRITICAL,
                    "There has to be at least one soil layer in the soil model!",
                ),
            ),
        ),
        (
            datetime64("2022-10-26"),
            datetime64("2052-10-26"),
            2.5,
            pytest.raises(TypeError),
            (
                (
                    CRITICAL,
                    "The number of soil layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_soil_model_initialization(
    caplog, start_time, end_time, no_layers, raises, expected_log_entries
):
    """Test `SoilModel` initialization."""

    # Check whether initialising the model fails as expected
    with raises:
        model = SoilModel(start_time, end_time, timedelta64(1, "W"), no_layers)

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "solve", "cleanup"]).issubset(dir(model))
        assert model.name == "soil"
        assert str(model) == "A soil model instance"
        assert (
            repr(model) == "SoilModel(start_time=2022-10-26, end_time=2052-10-26,"
            " update_interval=1 weeks, no_layers=2)"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_register_model_errors(caplog):
    """Test that the schema registering models generates correct errors/warnings."""

    @register_model("soil")
    def to_be_decorated() -> SoilModel:
        return SoilModel(
            datetime64("2022-10-26"),
            datetime64("2052-10-26"),
            timedelta64(1, "W"),
            2,
        )

    to_be_decorated()

    # Then check that the correct (critical error) log messages are emitted
    expected_log_entries = (
        (
            WARNING,
            "Model type soil already exists and is being replaced",
        ),
    )
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,raises,expected_log_entries",
    [
        (
            {},
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Configuration is missing information required to initialise the "
                    "soil model. The first missing key is 'core'",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_time": "2022-01-01",
                        "end_time": "20H2-01-01",
                        "update_interval": 0.5,
                    }
                },
                "soil": {"no_layers": 2},
            },
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Configuration types appear not to have been properly validated. "
                    "This problem prevents initialisation of the soil model. The first "
                    "instance of this problem is as follows: Error parsing datetime "
                    'string "20H2-01-01" at position 2',
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_time": "2022-01-01",
                        "end_time": "2052-01-01",
                        "update_interval": 0.5,
                    }
                },
                "soil": {"no_layers": 2},
            },
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
def test_generate_soil_model(caplog, config, raises, expected_log_entries):
    """Test that the function to initialise the soil model behaves as expected."""
    # Check whether initialising the model fails as expected
    with raises:
        model = generate_soil_model(config)
        assert model.no_layers == config["soil"]["no_layers"]

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
