"""Test module for litter_model.py."""

from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import DEBUG, ERROR, INFO

import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.models.litter.constants import LitterConsts
from virtual_rainforest.models.litter.litter_model import LitterModel


@pytest.fixture
def litter_model_fixture(dummy_litter_data):
    """Create a litter model fixture based on the dummy litter data."""

    from virtual_rainforest.models.litter.litter_model import LitterModel

    config = {
        "core": {
            "timing": {"start_date": "2020-01-01", "update_interval": "12 hours"},
            "layers": {"soil_layers": 2, "canopy_layers": 10},
        },
    }
    return LitterModel.from_config(dummy_litter_data, config, pint.Quantity("12 hours"))


@pytest.mark.parametrize(
    "bad_data,raises,expected_log_entries",
    [
        (
            [],
            does_not_raise(),
            (
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_structural' checked",
                ),
            ),
        ),
        (
            1,
            pytest.raises(ValueError),
            (
                (
                    ERROR,
                    "litter model: init data missing required var "
                    "'litter_pool_above_metabolic'",
                ),
                (
                    ERROR,
                    "litter model: init data missing required var "
                    "'litter_pool_above_structural'",
                ),
                (
                    ERROR,
                    "litter model: error checking required_init_vars, see log.",
                ),
            ),
        ),
        (
            2,
            pytest.raises(InitialisationError),
            (
                (
                    INFO,
                    "Replacing data array for 'litter_pool_above_metabolic'",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_structural' checked",
                ),
                (
                    ERROR,
                    "Initial litter pools contain at least one negative value!",
                ),
            ),
        ),
    ],
)
def test_litter_model_initialization(
    caplog, dummy_litter_data, bad_data, raises, expected_log_entries
):
    """Test `LitterModel` initialization."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    with raises:
        # Initialize model
        if bad_data:
            # Make four cell grid
            grid = Grid(cell_nx=4, cell_ny=1)
            litter_data = Data(grid)
            # On second test actually populate this data to test bounds
            if bad_data == 2:
                litter_data = deepcopy(dummy_litter_data)
                # Put incorrect data in for lmwc
                litter_data["litter_pool_above_metabolic"] = DataArray(
                    [0.05, 0.02, -0.1], dims=["cell_id"]
                )
            # Initialise model with bad data object
            model = LitterModel(
                litter_data, pint.Quantity("1 week"), 2, 10, constants=LitterConsts
            )
        else:
            model = LitterModel(
                dummy_litter_data,
                pint.Quantity("1 week"),
                2,
                10,
                constants=LitterConsts,
            )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.model_name == "litter"
        assert str(model) == "A litter model instance"
        assert repr(model) == "LitterModel(update_interval = 1 week)"

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


# TODO - test other functions for this module
