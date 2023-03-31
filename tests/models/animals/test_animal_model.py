"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.base_model import InitialisationError


def test_animal_model_initialization(caplog, data_instance):
    """Test `AnimalModel` initialization."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Initialize model
    model = AnimalModel(data_instance, timedelta64(1, "W"), datetime64("2022-11-01"))

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
    assert model.model_name == "animal"
    assert str(model) == "A animal model instance"
    assert (
        repr(model)
        == "AnimalModel(update_interval = 1 weeks, next_update = 2022-11-08)"
    )
    assert type(model.cohort_positions) is dict
    assert len(model.cohort_positions) == 100


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
                "core": {"timing": {"start_date": "2020-01-01"}},
                "animal": {"model_time_step": "12 hours"},
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
                "core": {"timing": {"start_date": "2020-01-01"}},
                "animal": {"model_time_step": "20 interminable minutes"},
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
        assert (
            model.next_update
            == datetime64(config["core"]["timing"]["start_date"]) + time_interval
        )
        # Run the update step and check that next_update has incremented properly
        model.update()
        assert (
            model.next_update
            == datetime64(config["core"]["timing"]["start_date"]) + 2 * time_interval
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
