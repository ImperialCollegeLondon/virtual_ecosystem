"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, DEBUG, INFO

import pytest
from numpy import timedelta64
import numpy as np
import xarray as xr

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)


@pytest.fixture
def abiotic_model_fixture(dummy_climate_data):
    """Create a simple abiotic model fixture based on the dummy carbon data."""

    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    config = {
        "core": {"timing": {"start_date": "2020-01-01", "update_interval": "12 hours"}},
    }
    return AbioticSimpleModel.from_config(dummy_climate_data, config)


@pytest.fixture
def layer_roles_fixture():
    """Create list of layer roles for 10 canopy layers and 2 soil layers."""
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        set_layer_roles,
    )

    return set_layer_roles(10, 2)


def test_set_layer_roles():
    """Test correct order of layers."""
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        set_layer_roles,
    )

    assert set_layer_roles(10, 2) == (
        ["above"] + ["canopy"] * 10 + ["subcanopy"] + ["surface"] + ["soil"] * 2
    )


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
def test_abiotic_simple_model_initialization(
    caplog,
    dummy_climate_data,
    soil_layers,
    canopy_layers,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test `AbioticSimpleModel` initialization."""

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            dummy_climate_data,
            timedelta64(1, "W"),
            soil_layers,
            canopy_layers,
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
        assert model.model_name == "abiotic_simple"
        assert (
            repr(model) == f"AbioticSimpleModel(update_interval = 1 weeks, "
            f"soil_layers = {int(soil_layers)}, "
            f"canopy_layers = {int(canopy_layers)})"
        )
        assert model.soil_layers == soil_layers
        assert model.canopy_layers == canopy_layers
        assert model.layer_roles == layer_roles_fixture

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
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 hours",
                    }
                },
                "abiotic_simple": {
                    "soil_layers": 2,
                    "canopy_layers": 3,
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
                (
                    DEBUG,
                    "abiotic simple model: required var 'air_temperature_ref' checked",
                ),
            ),
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog, data_instance, config, time_interval, raises, expected_log_entries
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticSimpleModel.from_config(data_instance, config)
        assert model.soil_layers == config["abiotic_simle"]["soil_layers"]
        assert model.canopy_layers == config["abiotic_simple"]["canopy_layers"]
        assert model.update_interval == time_interval

        model.setup()
        xr.testing.assert_allclose(
            data_instance["air_temperature"],
            xr.DataArray(
                np.full((15, 2), np.nan),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(0, 15),
                    "layer_roles": (
                        "layers",
                        model.layer_roles[0:15],
                    ),
                    "cell_id": [0, 1, 2],
                },
                name="air_temperature",
            ),
        )
        # Run the update step (once this does something should check output)
        model.update()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update_data_object(dummy_climate_data):
    """Test reading from list."""
    import numpy as np
    from xarray import DataArray

    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        update_data_object,
    )

    var_list = [
        DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            coords=dummy_climate_data["air_temperature_ref"].coords,
            name="air_temperature_ref",
        ),
        DataArray(
            np.full((3), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
        DataArray(
            np.full((3), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="new_variable",
        ),
    ]
    update_data_object(dummy_climate_data, var_list)

    xr.testing.assert_allclose(
        dummy_climate_data["air_temperature_ref"],
        DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            coords=dummy_climate_data["air_temperature_ref"].coords,
            name="air_temperature_ref",
        ),
    )
    xr.testing.assert_allclose(
        dummy_climate_data["mean_annual_temperature"],
        DataArray(
            np.full((3), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
    )
    xr.testing.assert_allclose(
        dummy_climate_data["new_variable"],
        DataArray(
            np.full((3), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="new_variable",
        ),
    )
