"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.model import BaseModel
from virtual_rainforest.soil.model import SoilModel

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
        assert model.name == "base model"
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
        assert model.name == "soil model"
        assert str(model) == "A soil model instance"
        assert (
            repr(model) == "SoilModel(start_time=2022-10-26, end_time=2052-10-26,"
            " update_interval=1 weeks, no_layers=2)"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
