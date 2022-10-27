"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.model import BaseModel

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
def test_model_initialization(
    caplog, start_time, end_time, update_interval, raises, expected_log_entries
):
    """Test `Model` initialization."""

    # Check whether initialising the model fails as expected
    with raises:
        model = BaseModel(start_time, end_time, update_interval)

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "solve", "cleanup"]).issubset(dir(model))
        assert model.name == "base model"
        assert str(model) == "A base model instance"
        assert (
            repr(model) == "Model(start_time=2022-10-26, end_time=2052-10-26,"
            " update_interval=1 weeks)"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
