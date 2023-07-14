"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, INFO

import numpy as np
import pint
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)


@pytest.mark.parametrize(
    "raises,expected_log_entries",
    [
        (
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
def test_abiotic_simple_model_initialization(
    caplog,
    dummy_climate_data,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test `AbioticSimpleModel` initialization."""
    from virtual_rainforest.models.abiotic_simple.constants import AbioticSimpleParams

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            dummy_climate_data,
            pint.Quantity("1 week"),
            soil_layers=2,
            canopy_layers=10,
            parameters=AbioticSimpleParams(),
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

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval,relative_humid,raises,expected_log_entries",
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
                        "update_interval": "1 week",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
            },
            pint.Quantity("1 week"),
            5.4,
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
                "abiotic_simple": {
                    "constants": {
                        "AbioticSimpleParams": {"relative_humidity_gradient": 10.2}
                    }
                },
            },
            pint.Quantity("1 week"),
            10.2,
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
)  # TODO - Test handling of bad dictionaries.
def test_generate_abiotic_simple_model(
    caplog,
    dummy_climate_data,
    config,
    time_interval,
    relative_humid,
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
        assert model.parameters.relative_humidity_gradient == relative_humid

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
    model = AbioticSimpleModel.from_config(
        dummy_climate_data,
        config,
        pint.Quantity(config["core"]["timing"]["update_interval"]),
    )
    assert model.layer_roles == layer_roles_fixture
    assert model.update_interval == time_interval

    model.setup()

    xr.testing.assert_allclose(
        model.data["soil_temperature"],
        DataArray(
            np.full((15, 3), np.nan),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, 15),
                "layer_roles": (
                    "layers",
                    model.layer_roles,
                ),
                "cell_id": [0, 1, 2],
            },
        ),
    )
    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((3, 3), 0.141727),
            dims=["cell_id", "time_index"],
            coords={
                "cell_id": [0, 1, 2],
            },
        ),
    )

    # Run the update step
    model.update(time_index=0)

    exp_temperature = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.91965, 29.91965, 29.91965],
                    [29.414851, 29.414851, 29.414851],
                    [28.551891, 28.551891, 28.551891],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [26.19, 26.19, 26.19],
                    [22.81851, 22.81851, 22.81851],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": (
                "layers",
                model.layer_roles,
            ),
            "cell_id": [0, 1, 2],
        },
    )

    xr.testing.assert_allclose(dummy_climate_data["air_temperature"], exp_temperature)
