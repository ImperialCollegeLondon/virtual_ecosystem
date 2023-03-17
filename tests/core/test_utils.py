"""Testing the utility functions."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.base_model import InitialisationError


@pytest.mark.parametrize(
    argnames=["config", "raises", "timestep", "initial_time", "expected_log"],
    argvalues=[
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 hours"},
            },
            does_not_raise(),
            timedelta64(720, "m"),
            datetime64("2020-01-01"),
            (),
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 interminable hours"},
            },
            pytest.raises(InitialisationError),
            None,
            None,
            (
                (
                    ERROR,
                    "Model timing error: 'interminable' is not defined in the unit "
                    "registry",
                ),
            ),
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 kilograms"},
            },
            pytest.raises(InitialisationError),
            None,
            None,
            (
                (
                    ERROR,
                    "Model timing error: Cannot convert from 'kilogram' ([mass]) to "
                    "'second' ([time])",
                ),
            ),
        ),
    ],
)
def test_extract_model_time_details(
    caplog, config, raises, timestep, initial_time, expected_log
):
    """Tests timing details extraction utility."""

    from virtual_rainforest.core.utils import extract_model_time_details

    with raises:
        start_time, update_interval = extract_model_time_details(config, "soil")
        assert start_time == initial_time
        assert update_interval == timestep

    log_check(caplog, expected_log)
