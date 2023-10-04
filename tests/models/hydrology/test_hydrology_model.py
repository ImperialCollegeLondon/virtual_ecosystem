"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.models.hydrology.constants import HydroConsts
from virtual_rainforest.models.hydrology.hydrology_model import HydrologyModel


@pytest.mark.parametrize(
    "ini_soil_moisture,raises,expected_log_entries",
    [
        (
            0.5,
            does_not_raise(),
            (
                (
                    DEBUG,
                    "hydrology model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'relative_humidity_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'atmospheric_pressure_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'evapotranspiration' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'elevation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'surface_runoff' checked",
                ),
            ),
        ),
        (
            -0.5,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The initial soil moisture has to be between 0 and 1!",
                ),
            ),
        ),
        (
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
def test_hydrology_model_initialization(
    caplog,
    dummy_climate_data,
    ini_soil_moisture,
    raises,
    expected_log_entries,
    layer_roles_fixture,
    soil_layers=[-0.5, -1.0],
    canopy_layers=10,
):
    """Test `HydrologyModel` initialization."""

    with raises:
        # Initialize model
        model = HydrologyModel(
            dummy_climate_data,
            pint.Quantity("1 month"),
            soil_layers,
            canopy_layers,
            ini_soil_moisture,
            constants=HydroConsts,
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
        assert model.model_name == "hydrology"
        assert repr(model) == "HydrologyModel(update_interval = 1 month)"
        assert model.layer_roles == layer_roles_fixture
        assert model.initial_soil_moisture == ini_soil_moisture
        assert model.drainage_map == {0: [], 1: [0], 2: [1, 2]}

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval,sm_capacity,raises,expected_log_entries",
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
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": [-0.5, -1.0],
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 month"),
            0.9,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'relative_humidity_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'atmospheric_pressure_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'evapotranspiration' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'elevation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'surface_runoff' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": [-0.5, -1.0],
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                    "constants": {"HydroConsts": {"soil_moisture_capacity": 0.7}},
                },
            },
            pint.Quantity("1 month"),
            0.7,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'relative_humidity_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'atmospheric_pressure_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'evapotranspiration' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'elevation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'surface_runoff' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": [-0.5, -1.0],
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                    "constants": {"HydroConsts": {"soilm_cap": 0.7}},
                },
            },
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for HydroConsts: " "soilm_cap",
                ),
                (
                    INFO,
                    "Valid names are as follows: ",
                ),
            ),
        ),
    ],
)
def test_generate_hydrology_model(
    caplog,
    dummy_climate_data,
    config,
    time_interval,
    sm_capacity,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test that the initialisation of the hydrology model works as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = HydrologyModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval
        assert model.constants.soil_moisture_capacity == sm_capacity

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval, raises",
    [
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": [-0.5, -1.0],
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 month"),
            does_not_raise(),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 week",
                    },
                    "layers": {
                        "soil_layers": [-0.5, -1.0],
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 week"),
            pytest.raises(NotImplementedError),
        ),
    ],
)
def test_setup(
    dummy_climate_data,
    config,
    layer_roles_fixture,
    time_interval,
    raises,
):
    """Test set up and update."""

    with raises:
        # initialise model
        model = HydrologyModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval

        model.setup()

        soil_moisture_values = np.repeat(a=[np.nan, 0.5], repeats=[13, 2])

        np.testing.assert_allclose(
            dummy_climate_data["soil_moisture"],
            DataArray(
                np.broadcast_to(soil_moisture_values, (3, 15)).T,
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(15),
                    "layer_roles": ("layers", layer_roles_fixture),
                    "cell_id": [0, 1, 2],
                },
                name="soil_moisture",
            ),
            rtol=1e-3,
            atol=1e-3,
        )

        # Run the update step
        model.update(time_index=1, seed=42)

        exp_soil_moisture = xr.concat(
            [
                DataArray(
                    np.full((13, 3), np.nan),
                    dims=["layers", "cell_id"],
                ),
                DataArray(
                    [[0.435508, 0.435743, 0.435522], [0.436075, 0.436175, 0.436045]],
                    dims=["layers", "cell_id"],
                ),
            ],
            dim="layers",
        ).assign_coords(model.data["layer_heights"].coords)

        exp_matric_pot = xr.concat(
            [
                DataArray(
                    np.full((13, 3), np.nan),
                    dims=["layers", "cell_id"],
                ),
                DataArray(
                    [
                        [-819.126131, -817.937497, -817.31294],
                        [-865.452922, -863.787411, -865.884216],
                    ],
                    dims=["layers", "cell_id"],
                ),
            ],
            dim="layers",
        ).assign_coords(model.data["layer_heights"].coords)

        exp_surf_prec = DataArray(
            [177.121093, 177.118977, 177.121364],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_runoff = DataArray(
            [0.0, 0.0, 0.0],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_vertical_flow = DataArray(
            [31.965002, 32.054212, 31.948825],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_soil_evap = DataArray(
            [128.548244, 128.567175, 128.560722],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_stream_flow = DataArray(
            [117.339795, 117.338423, 117.34047],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_runoff_acc = DataArray(
            [0, 10, 150],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )

        np.testing.assert_allclose(
            model.data["precipitation_surface"],
            exp_surf_prec,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["soil_moisture"],
            exp_soil_moisture,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["vertical_flow"],
            exp_vertical_flow,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["surface_runoff"],
            exp_runoff,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["soil_evaporation"],
            exp_soil_evap,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["stream_flow"],
            exp_stream_flow,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["surface_runoff_accumulated"],
            exp_runoff_acc,
            rtol=1e-4,
            atol=1e-4,
        )
        np.testing.assert_allclose(
            model.data["matric_potential"].isel(layers=-2),
            exp_matric_pot.isel(layers=-2),
            rtol=1e-4,
            atol=1e-4,
        )


def test_calculate_layer_thickness():
    """Test."""

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_layer_thickness,
    )

    soil_layer_heights = np.array([[-0.5, -0.5, -0.5], [-1.2, -1.2, -1.2]])
    exp_result = np.array([[500, 500, 500], [700, 700, 700]])

    result = calculate_layer_thickness(soil_layer_heights, 1000)

    np.testing.assert_allclose(result, exp_result)
