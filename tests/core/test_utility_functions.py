"""Testing the utility functions."""

from contextlib import nullcontext as does_not_raise

import pint
import pytest


# BASICALLY WANT TO CHUCK A LOAD OF CONFIGS AT THIS
# CHECK CORRECT ERRORS ARE THROWN
# AND THAT DETAILS ARE EXTRACTED CORRECTLY
@pytest.mark.parametrize(
    argnames=["config", "raises"],
    argvalues=[
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 hours"},
            },
            does_not_raise(),
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 interminable hours"},
            },
            pytest.raises(pint.errors.UndefinedUnitError),
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "soil": {"model_time_step": "12 kilograms"},
            },
            pytest.raises(pint.errors.DimensionalityError),
        ),
    ],
)
def test_extract_model_time_details(config, raises):
    """Tests timing details extraction utility."""

    from virtual_rainforest.core.utility_functions import extract_model_time_details

    with raises:
        start_time, update_interval = extract_model_time_details(config, "soil")
