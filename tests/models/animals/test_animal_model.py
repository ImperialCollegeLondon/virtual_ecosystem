"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest
from numpy import timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError


def test_animal_model_initialization(caplog, data_instance):
    """Test `AnimalModel` initialization."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Initialize model
    model = AnimalModel(data_instance, timedelta64(1, "W"))

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
    assert model.model_name == "animal"
    assert str(model) == "A animal model instance"
    assert repr(model) == "AnimalModel(update_interval = 1 weeks)"


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
            },
            timedelta64(12, "h"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the animal model successfully "
                    "extracted.",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "20 interminable minutes",
                    }
                },
            },
            None,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "Model timing error: 'interminable' is not defined in the unit "
                    "registry",
                ),
            ),
        ),
    ],
)
def test_generate_animal_model(
    caplog, data_instance, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the animal model behaves as expected."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AnimalModel.from_config(data_instance, config)
        assert model.update_interval == time_interval
        # Run the update step (once this does something should check output)
        model.update()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
