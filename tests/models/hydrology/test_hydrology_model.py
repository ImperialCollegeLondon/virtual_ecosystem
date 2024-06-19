"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check
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
            tuple(MODEL_VAR_CHECK_LOG),
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

    with raises:
        # Initialize model
        model = HydrologyModel(
            data=dummy_climate_data,
            core_components=fixture_core_components,
            initial_soil_moisture=ini_soil_moisture,
            initial_groundwater_saturation=ini_groundwater_sat,
            model_constants=HydroConsts(),
        )

        # In cases where it passes then checks that the object has the right properties
        assert isinstance(model, BaseModel)
        assert model.model_name == "hydrology"
        assert repr(model) == "HydrologyModel(update_interval=1209600 seconds)"
        assert model.initial_soil_moisture == ini_soil_moisture
        assert model.initial_groundwater_saturation == ini_groundwater_sat
        # VIVI - not sure about the value below.
        assert model.drainage_map == {0: [], 1: [], 2: [0, 2, 3], 3: [1]}

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,sm_capacity,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n",
            0.9,
            does_not_raise(),
            tuple(
                [
                    (INFO, "Initialised hydrology.HydroConsts from config"),
                    (
                        INFO,
                        "Information required to initialise the hydrology model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG,
                ]
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n"
            "[hydrology.constants.HydroConsts]\nsoil_moisture_capacity = 0.7\n",
            0.7,
            does_not_raise(),
            tuple(
                [
                    (INFO, "Initialised hydrology.HydroConsts from config"),
                    (
                        INFO,
                        "Information required to initialise the hydrology model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG,
                ]
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
                (ERROR, "Unknown names supplied for HydroConsts: " "soilm_cap"),
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
    sm_capacity,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the hydrology model works as expected."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = HydrologyModel.from_config(
            data=dummy_climate_data,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.soil_moisture_capacity == sm_capacity

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "update_interval, raises",
    [
        pytest.param(
            pint.Quantity(1, "month"),
            does_not_raise(),
            id="updates correctly",
        ),
        pytest.param(
            pint.Quantity(1, "week"),
            pytest.raises(NotImplementedError),
            id="incorrect update frequency",
        ),
    ],
)
def test_setup(
    dummy_climate_data,
    fixture_config,
    update_interval,
    raises,
    fixture_core_components,
):
    """Test set up and update."""
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Build the config object and core components
    fixture_config["core"]["timing"]["update_interval"] = update_interval
    core_components = CoreComponents(fixture_config)

    with raises:
        # initialise model
        model = HydrologyModel.from_config(
            data=dummy_climate_data,
            core_components=core_components,
            config=fixture_config,
        )

        model.setup()

        # Test soil moisture

        exp_soilm_setup = fixture_core_components.layer_structure.from_template()
        soil_indices = fixture_core_components.layer_structure.role_indices["all_soil"]
        exp_soilm_setup[soil_indices] = np.array([[125], [375]])

        np.testing.assert_allclose(
            model.data["soil_moisture"],
            exp_soilm_setup,
            rtol=1e-3,
            atol=1e-3,
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

        # Run the update step
        model.update(time_index=1, seed=42)

        # Test 2d variables
        expected_2d = {
            "soil_moisture": [
                # [67.0621, 67.0829, 67.05435, 67.05435],
                # [209.8470, 209.8500, 209.8491, 209.8491],
                [27.39980532, 27.42582027, 27.41118745, 27.39885058],
                [332.86865956, 332.86955187, 332.8695253, 332.86842804],
            ],
            "matric_potential": [
                # [-1.532961e07, -1.536408e07, -1.528976e07, -1],
                # [-1.250262e03, -1.250131e03, -1.250172e03, -1],
                [-2.73084554e07, -2.72799538e07, -2.73203705e07, -2.73156990e07],
                [-7.14598067e02, -7.14584359e02, -7.14584775e02, -7.14601617e02],
            ],
        }

        for var_name, expected_vals in expected_2d.items():
            exp_var = fixture_core_components.layer_structure.from_template()
            exp_var[soil_indices] = expected_vals

            np.testing.assert_allclose(
                model.data[var_name], exp_var, rtol=1e-4, atol=1e-4
            )

        # Test one dimensional variables
        expected_1d = {
            # "vertical_flow": [0.69471, 0.695691, 0.695682, 0.6],
            "vertical_flow": [0.57040329, 0.5709112, 0.57090678, 0.57026227],
            # "total_river_discharge": [0, 20925, 42201, 0],
            "total_river_discharge": [0, 0, 63153, 20925],
            "surface_runoff": [0, 0, 0, 0],
            "surface_runoff_accumulated": [0, 0, 0, 0],
            # "soil_evaporation": [345.1148, 344.759928, 345.15422, 345.15422],
            "soil_evaporation": [287.6170083, 287.19527165, 287.40854562, 287.64586797],
        }

        for var_name, expected_vals in expected_1d.items():
            np.testing.assert_allclose(
                model.data[var_name],
                expected_vals,
                rtol=1e-4,
                atol=1e-4,
            )
