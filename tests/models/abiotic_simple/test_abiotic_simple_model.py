"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


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
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_rainforest.models.abiotic_simple.constants import AbioticSimpleConsts

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            dummy_climate_data,
            pint.Quantity("1 week"),
            soil_layers=[-0.5, -1.0],
            canopy_layers=10,
            constants=AbioticSimpleConsts(),
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
    "cfg_string,time_interval,relative_humid,raises,expected_log_entries",
    [
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n",
            pint.Quantity("1 week"),
            5.4,
            does_not_raise(),
            (
                (INFO, "Initialised abiotic_simple.AbioticSimpleConsts from config"),
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
            id="default_config_correct",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "relative_humidity_gradient = 10.2\n",
            pint.Quantity("1 week"),
            10.2,
            does_not_raise(),
            (
                (INFO, "Initialised abiotic_simple.AbioticSimpleConsts from config"),
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
            id="modified_config_correct",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "relative_humidity_grad = 10.2\n",
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for AbioticSimpleConsts: "
                    "relative_humidity_grad",
                ),
                (INFO, "Valid names are: "),
                (
                    CRITICAL,
                    "Could not initialise abiotic_simple.AbioticSimpleConsts "
                    "from config",
                ),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog,
    dummy_climate_data,
    cfg_string,
    time_interval,
    relative_humid,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test that the initialisation of the simple abiotic model works as expected."""
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic_simple")
    # Build the config object
    config = Config(cfg_strings=cfg_string)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticSimpleModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval
        assert model.constants.relative_humidity_gradient == relative_humid

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup(
    dummy_climate_data,
    layer_roles_fixture,
):
    """Test set up and update."""
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic_simple")

    # Build the config object
    config = Config(
        cfg_strings="[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n"
    )

    # initialise model
    model = AbioticSimpleModel.from_config(
        dummy_climate_data,
        config,
        pint.Quantity(config["core"]["timing"]["update_interval"]),
    )
    assert model.layer_roles == layer_roles_fixture
    assert model.update_interval == pint.Quantity("1 week")

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
