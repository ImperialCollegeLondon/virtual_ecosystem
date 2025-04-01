"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO
from unittest.mock import patch

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import (
    log_check,
    patch_bypass_setup,
    patch_run_update,
    patch_static_config,
)
from virtual_ecosystem.core.exceptions import ConfigurationError

REQUIRED_INIT_VAR_CHECKS = (
    (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
    (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
    (DEBUG, "abiotic model: required var 'downward_shortwave_radiation' checked"),
    (DEBUG, "abiotic model: required var 'leaf_area_index' checked"),
    (DEBUG, "abiotic model: required var 'layer_heights' checked"),
    (DEBUG, "abiotic model: required var 'wind_speed_ref' checked"),
)

SETUP_MANIPULATIONS = (
    (INFO, "Replacing data array for 'soil_temperature'"),
    (INFO, "Replacing data array for 'vapour_pressure_deficit_ref'"),
    (INFO, "Replacing data array for 'vapour_pressure_ref'"),
    (INFO, "Replacing data array for 'air_temperature'"),
    (INFO, "Replacing data array for 'relative_humidity'"),
    (INFO, "Replacing data array for 'vapour_pressure_deficit'"),
    (INFO, "Replacing data array for 'wind_speed'"),
    (INFO, "Replacing data array for 'atmospheric_pressure'"),
    (INFO, "Adding data array for 'atmospheric_co2'"),
    (INFO, "Replacing data array for 'soil_temperature'"),
    (INFO, "Replacing data array for 'shortwave_absorption'"),
    (INFO, "Replacing data array for 'canopy_temperature'"),
    (INFO, "Replacing data array for 'sensible_heat_flux'"),
    (INFO, "Replacing data array for 'latent_heat_flux'"),
    (INFO, "Adding data array for 'ground_heat_flux'"),
)


def test_abiotic_model_initialization(
    caplog, dummy_climate_data, fixture_core_components
):
    """Test `AbioticModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel
    from virtual_ecosystem.models.abiotic.constants import AbioticConsts

    # Initialize model
    with (
        patch_run_update(AbioticModel) as mock_update,
        patch_bypass_setup(AbioticModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        model = AbioticModel(
            dummy_climate_data,
            core_components=fixture_core_components,
            model_constants=AbioticConsts(),
        )
        mock_update.assert_called_once()
        mock_bypass_setup.assert_called_once()

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "abiotic"
    assert str(model) == "A abiotic model instance"
    assert repr(model) == "AbioticModel(update_interval=1209600 seconds)"

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=REQUIRED_INIT_VAR_CHECKS + SETUP_MANIPULATIONS,
    )


def test_abiotic_model_initialization_no_data(caplog, fixture_core_components):
    """Test `AbioticModel` initialization with no data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel
    from virtual_ecosystem.models.abiotic.constants import AbioticConsts

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
            (
                ERROR,
                "abiotic model: init data missing required var "
                "'downward_shortwave_radiation'",
            ),
            (
                ERROR,
                "abiotic model: init data missing required var 'leaf_area_index'",
            ),
            (
                ERROR,
                "abiotic model: init data missing required var 'layer_heights'",
            ),
            (
                ERROR,
                "abiotic model: init data missing required var 'wind_speed_ref'",
            ),
            (ERROR, "abiotic model: error checking vars_required_for_init, see log."),
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
                *REQUIRED_INIT_VAR_CHECKS,
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
                *REQUIRED_INIT_VAR_CHECKS,
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

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel
    from virtual_ecosystem.models.abiotic.constants import AbioticConsts

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # We patch the _setup step as it is tested separately
    expected_constants = AbioticConsts(drag_coefficient=drag_coeff)
    object_to_patch = "virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel"
    with (
        patch_run_update(AbioticModel) as mock_update,
        patch_bypass_setup(AbioticModel) as mock_bypass_setup,
        patch(f"{object_to_patch}._setup") as mock_setup,
    ):
        mock_bypass_setup.return_value = False
        # Check whether model is initialised (or not) as expected
        with raises:
            AbioticModel.from_config(
                data=dummy_climate_data,
                core_components=core_components,
                config=config,
            )
            mock_setup.assert_called_once_with(model_constants=expected_constants)
            mock_bypass_setup.assert_called_once()
            mock_update.assert_called_once()

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
                *REQUIRED_INIT_VAR_CHECKS,
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

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with (
        patch_run_update(AbioticModel),
        patch_bypass_setup(AbioticModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        with raises:
            _ = AbioticModel.from_config(
                data=dummy_climate_data,
                core_components=core_components,
                config=config,
            )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup_abiotic_model(dummy_climate_data, fixture_core_components):
    """Test that setup() returns expected output in data object."""

    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    with (
        patch_run_update(AbioticModel),
        patch_bypass_setup(AbioticModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        model = AbioticModel(
            data=dummy_climate_data,
            core_components=fixture_core_components,
        )

    # check all variables are in data object
    for var in [
        "air_temperature",
        "soil_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
        "wind_speed",
    ]:
        assert var in model.data

    # Test that VPD was calculated for all time steps
    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((4, 3), 0.141727),
            dims=["cell_id", "time_index"],
            coords={
                "cell_id": [0, 1, 2, 3],
            },
        ),
    )

    # Test that soil temperature was created correctly
    expected_soil_temp = lyr_strct.from_template()
    expected_soil_temp[lyr_strct.index_all_soil] = np.array([20.712458, 20.0])[:, None]
    xr.testing.assert_allclose(model.data["soil_temperature"], expected_soil_temp)

    # Test that air temperature was interpolated correctly
    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = np.array(
        [30, 29.91965, 29.414851, 28.551891, 22.81851]
    )[:, None]
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    # Test other variables have been inserted and some check values
    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "shortwave_absorption",
    ]:
        assert var in model.data

    exp_shortwave_abs = lyr_strct.from_template()
    indices = [1, 2, 3, 12]
    exp_shortwave_abs[indices] = np.array([0.09995, 0.09985, 0.09975, 0])[:, None]
    xr.testing.assert_allclose(model.data["shortwave_absorption"], exp_shortwave_abs)

    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        expected_vals = lyr_strct.from_template()
        expected_vals[lyr_strct.index_flux_layers] = 0.001
        xr.testing.assert_allclose(model.data[var], expected_vals)

    # initialise model
    with patch_static_config(AbioticModel) as mock_static_config:
        mock_static_config.return_value = False, False
        model = AbioticModel(
            data=dummy_climate_data,
            core_components=fixture_core_components,
        )

        model.update(time_index=0)

    expected_soil_temp1 = lyr_strct.from_template()
    expected_soil_temp1[lyr_strct.index_all_soil] = np.array([18.730802, 19.989525])[
        :, None
    ]
    expected_soil_moist = lyr_strct.from_template()
    expected_soil_moist[lyr_strct.index_all_soil] = np.array([5.0, 500])[:, None]
    xr.testing.assert_allclose(
        model.data["soil_temperature"], expected_soil_temp1, rtol=0.0001
    )
    xr.testing.assert_allclose(model.data["soil_moisture"], expected_soil_moist)
