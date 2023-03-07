"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import pytest
from numpy import allclose, datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.models.soil.soil_model import SoilModel


@pytest.mark.parametrize(
    "bad_data,raises,expected_log_entries",
    [
        (
            False,
            does_not_raise(),
            (
                (
                    DEBUG,
                    "soil model: required var 'mineral_associated_om' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'low_molecular_weight_c' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'pH' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'bulk_density' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_moisture' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_temperature' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'percent_clay' checked",
                ),
            ),
        ),
        (
            True,
            pytest.raises(ValueError),
            (
                (
                    ERROR,
                    "soil model: init data missing required var "
                    "'mineral_associated_om'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var "
                    "'low_molecular_weight_c'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'pH'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'bulk_density'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'soil_moisture'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'soil_temperature'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'percent_clay'",
                ),
                (
                    ERROR,
                    "soil model: error checking required_init_vars, see log.",
                ),
            ),
        ),
    ],
)
def test_soil_model_initialization(
    caplog, dummy_carbon_data, bad_data, raises, expected_log_entries
):
    """Test `SoilModel` initialization."""

    with raises:
        # Initialize model
        if bad_data:
            model = SoilModel(
                [3.0, 4.0],
                timedelta64(1, "W"),
                datetime64("2022-11-01"),
            )
        else:
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
    "config,time_interval,raises,expected_log_entries,end_carbon",
    [
        (
            {},
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
            [],
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
                (
                    DEBUG,
                    "soil model: required var 'mineral_associated_om' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'low_molecular_weight_c' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'pH' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'bulk_density' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_moisture' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_temperature' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'percent_clay' checked",
                ),
                (INFO, "Replacing data array for 'mineral_associated_om'"),
                (INFO, "Replacing data array for 'low_molecular_weight_c'"),
            ),
            [
                [2.50019883, 1.70000589, 4.50007171, 0.50000014],
                [0.04980117, 0.01999411, 0.09992829, 0.00499986],
            ],
        ),
    ],
)
def test_generate_soil_model(
    caplog,
    dummy_carbon_data,
    config,
    time_interval,
    raises,
    expected_log_entries,
    end_carbon,
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(dummy_carbon_data, config)
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
        # Check that updates to data fixture are correct
        assert allclose(dummy_carbon_data["mineral_associated_om"], end_carbon[0])
        assert allclose(dummy_carbon_data["low_molecular_weight_c"], end_carbon[1])

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
