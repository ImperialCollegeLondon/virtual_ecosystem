"""Test module for abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.base_model import InitialisationError
from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel


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
                    ERROR,
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
                    ERROR,
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
                    ERROR,
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
                    ERROR,
                    "The number of canopy layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_abiotic_model_initialization(
    caplog, data_instance, soil_layers, canopy_layers, raises, expected_log_entries
):
    """Test `AbioticModel` initialization."""

    with raises:
        # Initialize model
        model = AbioticModel(
            data_instance,
            timedelta64(1, "W"),
            datetime64("2022-11-01"),
            soil_layers,
            canopy_layers,
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
        assert model.soil_layers == soil_layers
        assert model.canopy_layers == canopy_layers

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
                "core": {"timing": {"start_date": "2020-01-01"}},
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
    caplog, data_instance, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticModel.from_config(data_instance, config)
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
