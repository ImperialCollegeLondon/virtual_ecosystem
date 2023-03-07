"""Testing the utility functions."""

from contextlib import nullcontext as does_not_raise

import pint
import pytest
from numpy import datetime64, timedelta64


@pytest.mark.parametrize(
    argnames=["config", "raises", "timestep", "initial_time"],
    argvalues=[
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 hours"},
            },
            does_not_raise(),
            timedelta64(720, "m"),
            datetime64("2020-01-01"),
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 interminable hours"},
            },
            pytest.raises(pint.errors.UndefinedUnitError),
            None,
            None,
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 kilograms"},
            },
            pytest.raises(pint.errors.DimensionalityError),
            None,
            None,
        ),
    ],
)
def test_extract_model_time_details(config, raises, timestep, initial_time):
    """Tests timing details extraction utility."""

    from virtual_rainforest.core.utils import extract_model_time_details

    with raises:
        start_time, update_interval = extract_model_time_details(config, "soil")
        assert start_time == initial_time
        assert update_interval == timestep
