"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_abiotic_model_initialization(
    caplog, dummy_climate_data, fixture_core_components
):
    """Test `AbioticModel` initialization."""
    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    # Initialize model
    model = AbioticModel(
        dummy_climate_data,
        core_components=fixture_core_components,
        model_constants=AbioticConsts(),
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "abiotic"
    assert str(model) == "A abiotic model instance"
    assert repr(model) == "AbioticModel(update_interval=1209600 seconds)"

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
            (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
        ),
    )


def test_abiotic_model_initialization_no_data(caplog, fixture_core_components):
    """Test `AbioticModel` initialization with no data."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        empty_data = Data(grid)

        # Try and initialise model with empty data object
        _ = AbioticModel(
            empty_data,
            core_components=fixture_core_components,
            model_constants=AbioticConsts(),
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (
                ERROR,
                "abiotic model: init data missing required var 'air_temperature_ref'",
            ),
            (
                ERROR,
                "abiotic model: init data missing required var 'relative_humidity_ref'",
            ),
            (ERROR, "abiotic model: error checking required_init_vars, see log."),
        ),
    )


@pytest.mark.parametrize(
    "cfg_string, drag_coeff, raises, expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n[abiotic]\n",
            0.2,
            does_not_raise(),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
                (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
                (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[abiotic.constants.AbioticConsts]\ndrag_coefficient = 0.05\n",
            0.05,
            does_not_raise(),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
                (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
                (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[abiotic.constants.AbioticConsts]\ndrag_coefficients = 0.05\n",
            None,
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Unknown names supplied for AbioticConsts: drag_coefficients"),
                (INFO, "Valid names are: "),
                (CRITICAL, "Could not initialise abiotic.AbioticConsts from config"),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_abiotic_model(
    caplog,
    dummy_climate_data,
    cfg_string,
    drag_coeff,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the abiotic model behaves as expected."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import CoreComponents
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticModel.from_config(
            data=dummy_climate_data,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.drag_coefficient == drag_coeff

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string, raises, expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '1 year'\n[abiotic]\n",
            pytest.raises(ConfigurationError),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model "
                    "successfully extracted.",
                ),
                (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
                (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
                (
                    ERROR,
                    "The update interval is slower than the abiotic upper "
                    "bound of 1 month.",
                ),
            ),
            id="time interval out of bounds",
        ),
    ],
)
def test_generate_abiotic_model_bounds_error(
    caplog,
    dummy_climate_data,
    cfg_string,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the abiotic model from config."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import CoreComponents
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        _ = AbioticModel.from_config(
            data=dummy_climate_data,
            core_components=core_components,
            config=config,
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '1 day'\n[abiotic]\n",
            id="updates correctly",
        ),
    ],
)
def test_setup_abiotic_model(dummy_climate_data, cfg_string):
    """Test that setup() returns expected output in data object."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import CoreComponents
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)

    # initialise model
    model = AbioticModel.from_config(
        data=dummy_climate_data,
        core_components=core_components,
        config=config,
    )

    model.setup()

    # check all variables are in data object
    for var in [
        "air_temperature",
        "soil_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
    ]:
        assert var in model.data

    # Test that VPD was calculated for all time steps
    np.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((3, 3), 0.141727),
            dims=["cell_id", "time_index"],
            coords={
                "cell_id": [0, 1, 2],
            },
        ),
    )

    # Test that soil temperature was created correctly
    np.testing.assert_allclose(
        model.data["soil_temperature"][12:15],
        DataArray(
            [[np.nan, np.nan, np.nan], [20.712458, 20.712458, 20.712458], [20, 20, 20]],
            dims=["layers", "cell_id"],
            coords={
                "layers": [12, 13, 14],
                "layer_roles": ("layers", ["surface", "soil", "soil"]),
                "cell_id": [0, 1, 2],
            },
        ),
    )

    # Test that air temperature was interpolated correctly
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
                model.layer_structure.layer_roles,
            ),
            "cell_id": [0, 1, 2],
        },
    )

    np.testing.assert_allclose(
        model.data["air_temperature"], exp_temperature, rtol=1e-3, atol=1e-3
    )

    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "canopy_absorption",
        "air_conductivity",
        "leaf_vapor_conductivity",
        "leaf_air_conductivity",
    ]:
        assert var in model.data

    np.testing.assert_allclose(
        model.data["canopy_absorption"][1:4].to_numpy(),
        np.array(
            [
                [9.516258, 8.610666, 7.791253],
                [9.516258, 8.610666, 7.791253],
                [9.516258, 8.610666, 7.791253],
            ]
        ),
    )
    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(model.data[var][1:4].to_numpy(), np.zeros((3, 3)))
        np.testing.assert_allclose(model.data[var][12].to_numpy(), np.zeros(3))


@pytest.mark.parametrize(
    "cfg_string",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '1 day'\n[abiotic]\n",
            id="updates correctly",
        ),
    ],
)
def test_update_abiotic_model(dummy_climate_data, cfg_string):
    """Test that update() returns expected output in data object."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import CoreComponents
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)

    # initialise model
    model = AbioticModel.from_config(
        data=dummy_climate_data,
        core_components=core_components,
        config=config,
    )

    model.setup()

    model.update(time_index=0)

    friction_velocity_exp = np.array(
        [
            [0.162293, 0.163096, 0.163727],
            [0.162776, 0.163333, 0.163774],
            [0.165103, 0.164498, 0.164007],
            [0.167306, 0.16563, 0.164239],
            [0.169096, 0.166569, 0.164435],
            [0.169385, 0.166722, 0.164467],
        ]
    )
    wind_speed_exp = np.array(
        [
            [1.106333, 1.10686, 1.107273],
            [1.097423, 1.097945, 1.098355],
            [1.053935, 1.054437, 1.05483],
            [1.012171, 1.012653, 1.013031],
            [0.977975, 0.97844, 0.978806],
            [0.972455, 0.972918, 0.973281],
        ]
    )

    wind_above_exp = np.array([1.106333, 1.10686, 1.107273])

    np.testing.assert_allclose(
        model.data["wind_speed_above_canopy"], wind_above_exp, rtol=1e-3, atol=1e-3
    )
    np.testing.assert_allclose(
        model.data["friction_velocity"],
        DataArray(np.concatenate((friction_velocity_exp, np.full((9, 3), np.nan)))),
        rtol=1e-3,
        atol=1e-3,
    )
    np.testing.assert_allclose(
        model.data["wind_speed_canopy"],
        DataArray(np.concatenate((wind_speed_exp, np.full((9, 3), np.nan)))),
        rtol=1e-3,
        atol=1e-3,
    )

    exp_new_soiltemp = DataArray(
        np.concatenate(
            [
                [[np.nan, np.nan, np.nan]] * 13,
                [[20.713125, 20.712525, 20.712458], [20.0, 20.0, 20.0]],
            ],
            axis=0,
        ),
        dims=["layers", "cell_id"],
    )
    np.testing.assert_allclose(
        model.data["soil_temperature"],
        exp_new_soiltemp,
        rtol=1e-04,
        atol=1e-04,
    )
