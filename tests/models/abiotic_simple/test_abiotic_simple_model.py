"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)


def test_set_layer_roles():
    """Test correct order of layers."""
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        set_layer_roles,
    )

    assert set_layer_roles(10, 2) == (
        ["above"] + ["canopy"] * 10 + ["subcanopy"] + ["surface"] + ["soil"] * 2
    )


@pytest.mark.parametrize(
    "soil_layers,canopy_layers,ini_soil_moisture,raises,expected_log_entries",
    [
        (
            2,
            10,
            50.0,
            does_not_raise(),
            (
                (
                    DEBUG,
                    "abiotic_simple model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'relative_humidity_ref' "
                    "checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'atmospheric_pressure_ref' "
                    "checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'atmospheric_co2_ref' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'mean_annual_temperature' "
                    "checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'layer_heights' checked",
                ),
            ),
        ),
        (
            -2,
            10,
            50.0,
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
            50.0,
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
            10,
            50.0,
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
            50.0,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The number of canopy layers must be an integer!",
                ),
            ),
        ),
        (
            2,
            10,
            -50.0,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The initial soil moisture has to be between 0 and 100!",
                ),
            ),
        ),
        (
            2,
            10,
            DataArray([50, 30, 20]),
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The initial soil moisture must be a float!",
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
    ini_soil_moisture,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test `AbioticSimpleModel` initialization."""

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            dummy_climate_data,
            pint.Quantity("1 week"),
            soil_layers,
            canopy_layers,
            ini_soil_moisture,
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(
            [
                "setup",
                "spinup",
                "update",
                "cleanup",
            ]
        ).issubset(dir(model))
        assert model.model_name == "abiotic_simple"
        assert repr(model) == "AbioticSimpleModel(update_interval = 1 week)"
        assert model.layer_roles == layer_roles_fixture
        assert model.initial_soil_moisture == ini_soil_moisture

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
                        "update_interval": "1 week",
                    }
                },
                "abiotic_simple": {
                    "soil_layers": 2,
                    "canopy_layers": 10,
                    "initial_soil_moisture": 50.0,
                },
            },
            pint.Quantity("1 week"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the abiotic simple model "
                    "successfully extracted.",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'relative_humidity_ref' "
                    "checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'atmospheric_pressure_ref' "
                    "checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'atmospheric_co2_ref' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'mean_annual_temperature' "
                    "checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "abiotic_simple model: required var 'layer_heights' checked",
                ),
            ),
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog,
    dummy_climate_data,
    config,
    time_interval,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test that the initialisation of the simple abiotic model works as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticSimpleModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval

        # TODO Setup and update has to wait for simple_regression.py
        # model.setup()
        # xr.testing.assert_allclose(
        #     dummy_climate_data["air_temperature"],
        #     xr.DataArray(
        #         np.full((15, 3), np.nan),
        #         dims=["layers", "cell_id"],
        #         coords={
        #             "layers": np.arange(0, 15),
        #             "layer_roles": (
        #                 "layers",
        #                 model.layer_roles_fixture,
        #             ),
        #             "cell_id": [0, 1, 2],
        #         },
        #         name="air_temperature",
        #     ),
        # )
        # # Run the update step
        # model.update()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update_data_object(dummy_climate_data):
    """Test reading from dictionary."""

    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        update_data_object,
    )

    var_dict = {
        "air_temperature": DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            coords=dummy_climate_data["air_temperature_ref"].coords,
            name="air_temperature_ref",
        ),
        "mean_annual_temperature": DataArray(
            np.full((3), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
        "new_variable": DataArray(
            np.full((3), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="new_variable",
        ),
    }

    update_data_object(dummy_climate_data, var_dict)

    xr.testing.assert_allclose(
        dummy_climate_data["air_temperature"],
        DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            coords=dummy_climate_data["air_temperature"].coords,
            name="air_temperature",
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
