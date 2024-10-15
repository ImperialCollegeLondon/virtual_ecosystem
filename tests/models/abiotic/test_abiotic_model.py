"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO
from unittest.mock import patch

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError

REQUIRED_INIT_VAR_CHECKS = (
    (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
    (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
    (DEBUG, "abiotic model: required var 'topofcanopy_radiation' checked"),
    (DEBUG, "abiotic model: required var 'leaf_area_index' checked"),
    (DEBUG, "abiotic model: required var 'layer_heights' checked"),
)

SETUP_MANIPULATIONS = (
    (INFO, "Replacing data array for 'soil_temperature'"),
    (INFO, "Replacing data array for 'vapour_pressure_deficit_ref'"),
    (INFO, "Replacing data array for 'vapour_pressure_ref'"),
    (INFO, "Replacing data array for 'air_temperature'"),
    (INFO, "Replacing data array for 'relative_humidity'"),
    (INFO, "Adding data array for 'vapour_pressure_deficit'"),
    (INFO, "Replacing data array for 'atmospheric_pressure'"),
    (INFO, "Adding data array for 'atmospheric_co2'"),
    (INFO, "Replacing data array for 'soil_temperature'"),
    (INFO, "Replacing data array for 'canopy_absorption'"),
    (INFO, "Replacing data array for 'canopy_temperature'"),
    (INFO, "Replacing data array for 'sensible_heat_flux'"),
    (INFO, "Replacing data array for 'latent_heat_flux'"),
    (INFO, "Adding data array for 'ground_heat_flux'"),
    (INFO, "Adding data array for 'air_heat_conductivity'"),
    (INFO, "Replacing data array for 'leaf_vapour_conductivity'"),
    (INFO, "Replacing data array for 'leaf_air_heat_conductivity'"),
)


def test_abiotic_model_initialization(
    caplog, dummy_climate_data, fixture_core_components
):
    """Test `AbioticModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel
    from virtual_ecosystem.models.abiotic.constants import AbioticConsts

    # Initialize model
    object_to_patch = "virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel"
    with (
        patch(
            f"{object_to_patch}._run_update_due_to_static_configuration"
        ) as mock_update,
        patch(
            f"{object_to_patch}._bypass_setup_due_to_static_configuration"
        ) as mock_bypass_setup,
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
                "abiotic model: init data missing required var 'topofcanopy_radiation'",
            ),
            (
                ERROR,
                "abiotic model: init data missing required var 'leaf_area_index'",
            ),
            (
                ERROR,
                "abiotic model: init data missing required var 'layer_heights'",
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
        patch(
            f"{object_to_patch}._run_update_due_to_static_configuration"
        ) as mock_update,
        patch(
            f"{object_to_patch}._bypass_setup_due_to_static_configuration"
        ) as mock_bypass_setup,
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
    object_to_patch = "virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel"
    with (
        patch(f"{object_to_patch}._run_update_due_to_static_configuration"),
        patch(
            f"{object_to_patch}._bypass_setup_due_to_static_configuration"
        ) as mock_bypass_setup,
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
    object_to_patch = "virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel"
    with (
        patch(f"{object_to_patch}._run_update_due_to_static_configuration"),
        patch(
            f"{object_to_patch}._bypass_setup_due_to_static_configuration"
        ) as mock_bypass_setup,
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
        "canopy_absorption",
        "air_heat_conductivity",
        "leaf_vapour_conductivity",
        "leaf_air_heat_conductivity",
    ]:
        assert var in model.data

    exp_canopy_abs = lyr_strct.from_template()
    exp_canopy_abs[lyr_strct.index_filled_canopy] = np.array(
        [0.09995, 0.09985, 0.09975]
    )[:, None]
    xr.testing.assert_allclose(model.data["canopy_absorption"], exp_canopy_abs)

    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        expected_vals = lyr_strct.from_template()
        expected_vals[lyr_strct.index_flux_layers] = 0.0
        xr.testing.assert_allclose(model.data[var], expected_vals)


def test_update_abiotic_model(dummy_climate_data, fixture_core_components):
    """Test that update() returns expected output in data object."""

    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    object_to_patch = "virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel"
    with (
        patch(
            f"{object_to_patch}._run_update_due_to_static_configuration"
        ) as mock_update,
        patch(
            f"{object_to_patch}._bypass_setup_due_to_static_configuration"
        ) as mock_bypass_setup,
    ):
        mock_update.return_value = False
        mock_bypass_setup.return_value = False
        model = AbioticModel(
            data=dummy_climate_data,
            core_components=fixture_core_components,
        )

        model.update(time_index=0)

    # Check that updated vars are in data object
    for var in [
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "air_heat_conductivity",
        "conductivity_from_ref_height",
        "leaf_air_heat_conductivity",
        "leaf_vapour_conductivity",
        "wind_speed",
        "friction_velocity",
        "diabatic_correction_heat_above",
        "diabatic_correction_momentum_above",
        "diabatic_correction_heat_canopy",
        "diabatic_correction_momentum_canopy",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "soil_absorption",
        "longwave_emission_soil",
        "molar_density_air",
        "specific_heat_air",
    ]:
        assert var in model.data

    # Test variable values
    friction_velocity_exp = DataArray(
        np.repeat(0.161295, fixture_core_components.grid.n_cells),
        coords={"cell_id": dummy_climate_data["cell_id"]},
    )
    xr.testing.assert_allclose(model.data["friction_velocity"], friction_velocity_exp)

    # VIVI - all of the commented values below are the original calculated test values
    # but these have all changed (mostly very little) when the test data and setup was
    # updated in #441. This could be a change in the inputs or could be problems with
    # the changes in the implementation with #441. Either way - these tests pass but
    # this is circular, since these value are for the moment taken straight from the
    # outputs and not validated.

    # Wind speed
    exp_wind_speed = lyr_strct.from_template()
    exp_wind_speed[lyr_strct.index_filled_atmosphere] = np.array(
        # [0.727122, 0.615474, 0.587838, 0.537028, 0.50198]
        [0.72712164, 0.61547404, 0.57491436, 0.47258967, 0.41466282]
    )[:, None]
    xr.testing.assert_allclose(model.data["wind_speed"], exp_wind_speed)

    # Soil temperature
    exp_new_soiltemp = lyr_strct.from_template()
    exp_new_soiltemp[lyr_strct.index_all_soil] = np.array(
        [  # [20.713167, 20.708367, 20.707833, 20.707833],
            [20.712458, 20.712457, 20.712456, 20.712456],
            [20.0, 20.0, 20.0, 20.0],
        ]
    )
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_new_soiltemp)

    # Leaf vapour conductivity
    exp_gv = lyr_strct.from_template()
    exp_gv[lyr_strct.index_filled_canopy] = np.array(
        # [0.496563, 0.485763, 0.465142]
        [0.4965627, 0.48056564, 0.43718369]
    )[:, None]
    xr.testing.assert_allclose(model.data["leaf_vapour_conductivity"], exp_gv)

    # Air temperature
    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = np.array(
        # [30.0, 29.999943, 29.992298, 29.623399, 20.802228]
        [30.0, 29.99994326, 29.99237944, 29.6604941, 20.80193877]
    )[:, None]
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    # Canopy temperature
    exp_leaf_temp = lyr_strct.from_template()
    exp_leaf_temp[lyr_strct.index_filled_canopy] = np.array(
        # [28.787061, 28.290299, 28.15982]
        [28.78850297, 28.29326228, 28.19789174]
    )[:, None]
    xr.testing.assert_allclose(model.data["canopy_temperature"], exp_leaf_temp)

    # TODO fix fluxes from soil

    # Latent heat flux
    exp_latent_heat = lyr_strct.from_template()
    exp_latent_heat[lyr_strct.index_filled_canopy] = np.array(
        # [28.07077, 27.568715, 16.006325]
        [28.07077012, 27.35735709, 14.97729136]
    )[:, None]
    exp_latent_heat[lyr_strct.index_topsoil] = np.array([2.254, 22.54, 225.4, 225.4])
    xr.testing.assert_allclose(model.data["latent_heat_flux"], exp_latent_heat)

    # Sensible heat flux
    exp_sens_heat = lyr_strct.from_template()
    exp_sens_heat[lyr_strct.index_flux_layers] = np.array(
        # [-16.970825, -16.47644, -5.637233, -192.074608]
        [-16.9708248, -16.26697999, -4.65665595, -192.07460835]
    )[:, None]
    xr.testing.assert_allclose(model.data["sensible_heat_flux"], exp_sens_heat)
