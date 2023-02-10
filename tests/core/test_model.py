"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, WARNING

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.model import BaseModel


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
