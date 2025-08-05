"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO
from unittest.mock import patch

import numpy as np
import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check, patch_bypass_setup, patch_run_update
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (DEBUG, "hydrology model: required var 'layer_heights' checked"),
    (DEBUG, "hydrology model: required var 'elevation' checked"),
]


@pytest.mark.parametrize(
    "ini_soil_moisture, ini_groundwater_sat, raises, expected_log_entries",
    [
        pytest.param(
            0.5,
            0.9,
            does_not_raise(),
            None,
            id="succeeds",
        ),
        pytest.param(
            -0.5,
            0.9,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *MODEL_VAR_CHECK_LOG,
                    (ERROR, "The initial_soil_moisture has to be between 0 and 1!"),
                ]
            ),
            id="soil moisture out of bounds",
        ),
        pytest.param(
            DataArray([50, 30, 20, 20]),
            0.9,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *MODEL_VAR_CHECK_LOG,
                    (ERROR, "The initial_soil_moisture must be numeric!"),
                ]
            ),
            id="soil moisture not numeric",
        ),
        pytest.param(
            0.5,
            1.9,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *MODEL_VAR_CHECK_LOG,
                    (
                        ERROR,
                        "The initial_groundwater_saturation has to be between 0 and 1!",
                    ),
                ]
            ),
            id="grnd sat out of bounds",
        ),
    ],
)
def test_hydrology_model_initialization(
    caplog,
    dummy_climate_data,
    fixture_core_components,
    ini_soil_moisture,
    ini_groundwater_sat,
    raises,
    expected_log_entries,
):
    """Test `HydrologyModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # We patch the _setup step as it is tested separately
    with (
        patch_run_update(HydrologyModel),
        patch_bypass_setup(HydrologyModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        with raises:
            # Initialize model
            model = HydrologyModel(
                data=dummy_climate_data,
                core_components=fixture_core_components,
                initial_soil_moisture=ini_soil_moisture,
                initial_groundwater_saturation=ini_groundwater_sat,
                model_constants=HydroConsts(),
            )

            # In cases where it passes we check that the object has the right properties
            assert isinstance(model, BaseModel)
            assert model.model_name == "hydrology"
            assert repr(model) == "HydrologyModel(update_interval=1209600 seconds)"
            assert model.initial_soil_moisture == ini_soil_moisture
            assert model.initial_groundwater_saturation == ini_groundwater_sat
            # TODO: not sure on the value below, test with more expansive drainage maps
            assert model.drainage_map == {0: [], 1: [], 2: [0, 2, 3], 3: [1]}

    # Final check that expected logging entries are produced
    if expected_log_entries:
        log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,sm_saturation,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.51\n",
            0.51,
            does_not_raise(),
            (
                (INFO, "Initialised hydrology.HydroConsts from config"),
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                *MODEL_VAR_CHECK_LOG,
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n"
            "[hydrology.constants.HydroConsts]\nsoil_moisture_saturation = 0.7\n",
            0.7,
            does_not_raise(),
            (
                (INFO, "Initialised hydrology.HydroConsts from config"),
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                *MODEL_VAR_CHECK_LOG,
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n"
            "[hydrology.constants.HydroConsts]\nsoilm_cap = 0.7\n",
            None,
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Unknown names supplied for HydroConsts: soilm_cap"),
                (INFO, "Valid names are: "),
                (CRITICAL, "Could not initialise hydrology.HydroConsts from config"),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_hydrology_model(
    caplog,
    dummy_climate_data,
    cfg_string,
    sm_saturation,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the hydrology model works as expected."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    with (
        patch_run_update(HydrologyModel),
        patch_bypass_setup(HydrologyModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        with patch(
            "virtual_ecosystem.models.hydrology.hydrology_model.HydrologyModel._setup"
        ) as mock_setup:
            with raises:
                HydrologyModel.from_config(
                    data=dummy_climate_data,
                    core_components=core_components,
                    config=config,
                )
                mock_setup.assert_called_once()

                # Check arguments passed to _setup
                called_args, called_kwargs = mock_setup.call_args
                assert (
                    called_kwargs["initial_soil_moisture"]
                    == config["hydrology"]["initial_soil_moisture"]
                )
                assert (
                    called_kwargs["initial_groundwater_saturation"]
                    == config["hydrology"]["initial_groundwater_saturation"]
                )

                model_constants = called_kwargs["model_constants"]
                assert isinstance(model_constants, HydroConsts)
                if sm_saturation is not None:
                    assert model_constants.soil_moisture_saturation == sm_saturation

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "update_interval, raises, expected_2d, expected_1d",
    [
        pytest.param(
            pint.Quantity(1, "month"),
            does_not_raise(),
            {
                "soil_moisture": [
                    [248.938056, 248.937037, 248.935933, 248.936385],
                    [218.994795, 218.994795, 218.994795, 218.994795],
                ],
                "matric_potential": [
                    [-56.432398, -56.438614, -56.44538, -56.442609],
                    [-217.596626, -217.596626, -217.596626, -217.596626],
                ],
                "vertical_flow": [
                    [0.00017, 0.00017, 0.00017, 0.00017],
                    [0.000526, 0.000526, 0.000526, 0.000526],
                ],
            },
            {
                "total_river_discharge": [0, 0, 67002, 22095],
                "surface_runoff": [20.343781, 20.66599, 20.896484, 20.443394],
                "surface_runoff_accumulated": [0, 0, 1470, 330],
                "soil_evaporation": [5.870856, 5.870856, 5.870856, 5.870856],
            },
            id="1 month",
        ),
        pytest.param(
            pint.Quantity(1, "week"),
            does_not_raise(),
            {
                "soil_moisture": [
                    [249.628102, 249.628102, 249.628102, 249.628102],
                    [215.713193, 215.713193, 215.713193, 215.713193],
                ],
                "matric_potential": [
                    [-52.085807, -52.085807, -52.085807, -52.085807],
                    [-196.720556, -196.720556, -196.720556, -196.720556],
                ],
                "vertical_flow": [
                    [0.000295, 0.000295, 0.000295, 0.000295],
                    [0.000611, 0.000611, 0.000611, 0.000611],
                ],
            },
            {
                "total_river_discharge": [0, 0, 5767, 1910],
                "surface_runoff": [163.019971, 163.019971, 163.019971, 163.019971],
                "surface_runoff_accumulated": [0, 0, 3395, 1127],
                "soil_evaporation": [1.388223, 1.388223, 1.388223, 1.388223],
            },
            id="1 week",
        ),
    ],
)
def test_setup(
    fixture_core_components,
    dummy_climate_data,
    fixture_config,
    update_interval,
    raises,
    expected_2d,
    expected_1d,
):
    """Test set up and update."""
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Build the config object and core components
    fixture_config["core"]["timing"]["update_interval"] = update_interval
    core_components = CoreComponents(fixture_config)
    lyr_strct = core_components.layer_structure

    with (
        patch_run_update(HydrologyModel),
        patch_bypass_setup(HydrologyModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        with raises:
            # initialise model. The setup is run as part of the initialisation
            model = HydrologyModel.from_config(
                data=dummy_climate_data,
                core_components=core_components,
                config=fixture_config,
            )

            # Test soil moisture

            soil_indices = lyr_strct.index_all_soil
            expected_values = {
                "soil_moisture": (soil_indices, np.array([[250], [250]])),
                "aerodynamic_resistance_canopy": (lyr_strct.index_filled_canopy, 12.5),
            }
            for var_name, (indices, values) in expected_values.items():
                exp_var = lyr_strct.from_template()
                exp_var[indices] = values
                np.testing.assert_allclose(
                    model.data[var_name], exp_var, rtol=1e-3, atol=1e-3
                )

            # Test groundwater storage
            exp_groundwater = DataArray(
                np.full((2, fixture_core_components.grid.n_cells), 450.0),
                dims=("groundwater_layers", "cell_id"),
            )
            np.testing.assert_allclose(
                model.data["groundwater_storage"],
                exp_groundwater,
                rtol=1e-3,
                atol=1e-3,
            )

            exp_aero_resist_canopy = np.full((14, 4), np.nan)
            np.testing.assert_allclose(
                model.data["aerodynamic_resistance_canopy"],
                exp_aero_resist_canopy,
            )

            # Run the update step
            model.update(time_index=1, seed=42)

            # Test 2d variables
            for var_name, expected_vals in expected_2d.items():
                exp_var = lyr_strct.from_template()
                exp_var[soil_indices] = expected_vals

                np.testing.assert_allclose(
                    model.data[var_name][soil_indices],
                    exp_var[soil_indices],
                    rtol=1e-4,
                    atol=1e-4,
                )

            # Test one dimensional variables

            for var_name, expected_vals in expected_1d.items():
                np.testing.assert_allclose(
                    model.data[var_name],
                    expected_vals,
                    rtol=1e-2,
                    atol=1e-2,
                )
