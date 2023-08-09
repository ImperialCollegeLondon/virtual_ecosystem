"""Test module for litter_model.py."""

from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.models.litter.constants import LitterConsts
from virtual_rainforest.models.litter.litter_model import LitterModel


@pytest.fixture
def litter_model_fixture(dummy_litter_data):
    """Create a litter model fixture based on the dummy litter data."""

    from virtual_rainforest.models.litter.litter_model import LitterModel

    config = {
        "core": {
            "timing": {"start_date": "2020-01-01", "update_interval": "24 hours"},
            "layers": {"soil_layers": 2, "canopy_layers": 10},
        },
    }
    return LitterModel.from_config(dummy_litter_data, config, pint.Quantity("24 hours"))


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
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_woody' checked",
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
                    "litter model: init data missing required var "
                    "'litter_pool_woody'",
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
                    DEBUG,
                    "litter model: required var 'litter_pool_woody' checked",
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


@pytest.mark.parametrize(
    "config,time_interval,temp_response,raises,expected_log_entries",
    [
        (
            {},
            None,
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "24 hours",
                    },
                    "layers": {"soil_layers": 2, "canopy_layers": 10},
                },
            },
            pint.Quantity("24 hours"),
            3.36,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the litter model successfully "
                    "extracted.",
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
                    DEBUG,
                    "litter model: required var 'litter_pool_woody' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "24 hours",
                    },
                    "layers": {"soil_layers": 2, "canopy_layers": 10},
                },
                "litter": {
                    "constants": {"LitterConsts": {"litter_decomp_temp_response": 4.44}}
                },
            },
            pint.Quantity("24 hours"),
            4.44,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the litter model successfully "
                    "extracted.",
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
                    DEBUG,
                    "litter model: required var 'litter_pool_woody' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "24 hours",
                    },
                    "layers": {"soil_layers": 2, "canopy_layers": 10},
                },
                "litter": {"constants": {"LitterConsts": {"decomp_rate": 4.44}}},
            },
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for LitterConsts: decomp_rate",
                ),
                (
                    INFO,
                    "Valid names are as follows: ",
                ),
            ),
        ),
    ],
)
def test_generate_litter_model(
    caplog,
    dummy_litter_data,
    config,
    time_interval,
    temp_response,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the litter model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = LitterModel.from_config(
            dummy_litter_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.update_interval == time_interval
        assert model.constants.litter_decomp_temp_response == temp_response

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update(litter_model_fixture, dummy_litter_data):
    """Test to check that the update step works and increments the update step."""

    end_above_meta = [0.29577179, 0.14802621, 0.06922856]
    end_above_struct = [0.50055126, 0.25063497, 0.09068855]
    end_woody = [4.702103, 11.801373, 7.301836]
    c_mineral = [0.00238682, 0.00172775, 0.00090278]

    litter_model_fixture.update(time_index=0)

    # Check that data fixture has been updated correctly
    assert np.allclose(dummy_litter_data["litter_pool_above_metabolic"], end_above_meta)
    assert np.allclose(
        dummy_litter_data["litter_pool_above_structural"], end_above_struct
    )
    assert np.allclose(dummy_litter_data["litter_pool_woody"], end_woody)
    assert np.allclose(dummy_litter_data["litter_C_mineralisation_rate"], c_mineral)
