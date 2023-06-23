"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError
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
    soil_layers=2,
    canopy_layers=10,
):
    """Test `HydrologyModel` initialization."""

    with raises:
        # Initialize model
        model = HydrologyModel(
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
        assert model.model_name == "hydrology"
        assert repr(model) == "HydrologyModel(update_interval = 1 week)"
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
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 week"),
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
            ),
        ),
    ],
)
def test_generate_hydrology_model(
    caplog,
    dummy_climate_data,
    config,
    time_interval,
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

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval",
    [
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 week",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 week"),
        )
    ],
)
def test_setup(
    dummy_climate_data,
    config,
    layer_roles_fixture,
    time_interval,
):
    """Test set up and update."""

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

    xr.testing.assert_allclose(
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
    )

    # Run the update step
    model.update()

    exp_soil_moisture = xr.concat(
        [
            DataArray(
                np.full((13, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [[0.499999, 0.499999, 0.499978], [0.499999, 0.499999, 0.499978]],
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    ).assign_coords(model.data["layer_heights"].coords)

    xr.testing.assert_allclose(model.data["soil_moisture"], exp_soil_moisture)
    # test that time_index was updated
    assert model.time_index == 1


def test_calculate_soil_moisture(dummy_climate_data, layer_roles_fixture):
    """Test that soil moisture and runoff are calculated correctly."""

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_soil_moisture,
    )

    data = dummy_climate_data
    precipitation_surface = data["precipitation"].isel(time_index=0) * (
        1 - 0.1 * data["leaf_area_index"].sum(dim="layers")
    )

    exp_soil_moisture = xr.concat(
        [
            DataArray(
                np.full((13, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [[0.199998, 0.2, 0.199978], [0.199998, 0.2, 0.199978]],
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    ).assign_coords(data["layer_heights"].coords)

    exp_runoff = DataArray(
        [0, 0, 260],
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2]},
    )

    exp_vertical_flow = DataArray(
        [1.749375e-03, 6.883677e-05, 2.389091e-02],
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2]},
    )

    result = calculate_soil_moisture(
        layer_roles=layer_roles_fixture,
        layer_heights=data["layer_heights"],
        precipitation_surface=precipitation_surface,
        current_soil_moisture=data["soil_moisture"],
        soil_moisture_capacity=DataArray([0.3, 0.6, 0.6], dims=["cell_id"]),
    )

    xr.testing.assert_allclose(result[0], exp_soil_moisture)
    xr.testing.assert_allclose(result[1], exp_runoff)
    xr.testing.assert_allclose(result[2], exp_vertical_flow)


def test_calculate_vertical_flow(layer_roles_fixture):
    """test."""

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_vertical_flow,
    )

    soil_moisture_residual = DataArray([0.3, 0.6, 0.9], dims=["cell_id"])
    soil_depth = DataArray([1100, 1100, 1100], dims=["cell_id"])
    result = calculate_vertical_flow(soil_moisture_residual, soil_depth)
    exp_flow = DataArray([4.511561e-05, 1.264894e-03, 2.389091e-02], dims=["cell_id"])
    xr.testing.assert_allclose(result, exp_flow)
