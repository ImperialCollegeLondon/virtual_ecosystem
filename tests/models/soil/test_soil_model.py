"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.models.soil.soil_model import SoilModel


@pytest.mark.parametrize(
    "no_layers,raises,expected_log_entries",
    [
        (
            2,
            does_not_raise(),
            (),
        ),
    ],
)
def test_soil_model_initialization(
    caplog, dummy_carbon_data, no_layers, raises, expected_log_entries
):
    """Test `SoilModel` initialization."""

    with raises:
        # Initialize model
        model = SoilModel(
            dummy_carbon_data, timedelta64(1, "W"), datetime64("2022-11-01")
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.model_name == "soil"
        assert str(model) == "A soil model instance"
        assert (
            repr(model)
            == "SoilModel(update_interval = 1 weeks, next_update = 2022-11-08)"
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
                "soil": {"model_time_step": "12 hours"},
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
    caplog, dummy_carbon_data, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(dummy_carbon_data, config)
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
