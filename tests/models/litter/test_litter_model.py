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


def test_litter_model_initialization(caplog, dummy_litter_data):
    """Test `LitterModel` initialization."""

    expected_log_entries = (
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
            DEBUG,
            "litter model: required var 'litter_pool_below_metabolic' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'litter_pool_below_structural' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_above_structural' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_woody' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_below_structural' checked",
        ),
    )

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


def test_litter_model_initialization_no_data(caplog):
    """Test `LitterModel` initialization fails when all data is missing."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    expected_log_entries = (
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
            "litter model: init data missing required var " "'litter_pool_woody'",
        ),
        (
            ERROR,
            "litter model: init data missing required var "
            "'litter_pool_below_metabolic'",
        ),
        (
            ERROR,
            "litter model: init data missing required var "
            "'litter_pool_below_structural'",
        ),
        (
            ERROR,
            "litter model: init data missing required var " "'lignin_above_structural'",
        ),
        (
            ERROR,
            "litter model: init data missing required var " "'lignin_woody'",
        ),
        (
            ERROR,
            "litter model: init data missing required var " "'lignin_below_structural'",
        ),
        (
            ERROR,
            "litter model: error checking required_init_vars, see log.",
        ),
    )

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        litter_data = Data(grid)

        LitterModel(litter_data, pint.Quantity("1 week"), 2, 10, constants=LitterConsts)

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_litter_model_initialization_bad_pool_bounds(caplog, dummy_litter_data):
    """Test `LitterModel` initialization fails when litter pools are out of bounds."""

    expected_log_entries = (
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
            DEBUG,
            "litter model: required var 'litter_pool_below_metabolic' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'litter_pool_below_structural' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_above_structural' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_woody' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_below_structural' checked",
        ),
        (
            ERROR,
            "Pool sizes in ['litter_pool_above_metabolic'] must be greater than 0!",
        ),
    )

    with pytest.raises(InitialisationError):
        # Make four cell grid
        litter_data = deepcopy(dummy_litter_data)
        # Put incorrect data in for lmwc
        litter_data["litter_pool_above_metabolic"] = DataArray(
            [0.05, 0.02, -0.1], dims=["cell_id"]
        )

        LitterModel(litter_data, pint.Quantity("1 week"), 2, 10, constants=LitterConsts)

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_litter_model_initialization_bad_lignin_bounds(caplog, dummy_litter_data):
    """Test `LitterModel` initialization fails for lignin proportions not in bounds."""

    expected_log_entries = (
        (
            INFO,
            "Replacing data array for 'lignin_woody'",
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
            DEBUG,
            "litter model: required var 'litter_pool_below_metabolic' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'litter_pool_below_structural' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_above_structural' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_woody' checked",
        ),
        (
            DEBUG,
            "litter model: required var 'lignin_below_structural' checked",
        ),
        (
            ERROR,
            "Proportions in ['lignin_woody'] must be between 0 and 1!",
        ),
    )

    with pytest.raises(InitialisationError):
        # Make four cell grid
        litter_data = deepcopy(dummy_litter_data)
        # Put incorrect data in for woody lignin
        litter_data["lignin_woody"] = DataArray([0.5, 0.4, 1.1], dims=["cell_id"])

        LitterModel(litter_data, pint.Quantity("1 week"), 2, 10, constants=LitterConsts)

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
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_above_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_woody' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_below_structural' checked",
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
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_above_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_woody' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_below_structural' checked",
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

    end_above_meta = [0.29587973, 0.14851276, 0.07041856]
    end_above_struct = [0.50055126, 0.25010012, 0.0907076]
    end_woody = [4.702103, 11.802315, 7.300997]
    end_below_meta = [0.394145, 0.35923, 0.069006]
    end_below_struct = [0.60027118, 0.30975403, 0.02047743]
    end_lignin_above_struct = [0.4996410, 0.1004310, 0.6964345]
    end_lignin_woody = [0.49989001, 0.79989045, 0.34998229]
    end_lignin_below_struct = [0.499760108, 0.249922519, 0.737107757]
    c_mineral = [0.0212182, 0.02746286, 0.00796359]

    litter_model_fixture.update(time_index=0)

    # Check that data fixture has been updated correctly
    assert np.allclose(dummy_litter_data["litter_pool_above_metabolic"], end_above_meta)
    assert np.allclose(
        dummy_litter_data["litter_pool_above_structural"], end_above_struct
    )
    assert np.allclose(dummy_litter_data["litter_pool_woody"], end_woody)
    assert np.allclose(dummy_litter_data["litter_pool_below_metabolic"], end_below_meta)
    assert np.allclose(
        dummy_litter_data["litter_pool_below_structural"], end_below_struct
    )
    assert np.allclose(
        dummy_litter_data["lignin_above_structural"], end_lignin_above_struct
    )
    assert np.allclose(dummy_litter_data["lignin_woody"], end_lignin_woody)
    assert np.allclose(
        dummy_litter_data["lignin_below_structural"], end_lignin_below_struct
    )
    assert np.allclose(dummy_litter_data["litter_C_mineralisation_rate"], c_mineral)


def test_convert_soil_moisture_to_water_potential(
    dummy_litter_data, top_soil_layer_index
):
    """Test that function to convert soil moisture to a water potential works."""
    from virtual_rainforest.models.litter.litter_model import (
        convert_soil_moisture_to_water_potential,
    )

    expected_potentials = [-297.14104, -4.2647655, -79.666189]

    actual_potentials = convert_soil_moisture_to_water_potential(
        dummy_litter_data["soil_moisture"][top_soil_layer_index].to_numpy(),
        air_entry_water_potential=LitterConsts.air_entry_water_potential,
        water_retention_curvature=LitterConsts.water_retention_curvature,
        saturated_water_content=LitterConsts.saturated_water_content,
    )

    assert np.allclose(actual_potentials, expected_potentials)
