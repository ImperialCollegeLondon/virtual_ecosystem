"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (DEBUG, "hydrology model: required var 'precipitation' checked"),
    (DEBUG, "hydrology model: required var 'leaf_area_index' checked"),
    (DEBUG, "hydrology model: required var 'air_temperature_ref' checked"),
    (DEBUG, "hydrology model: required var 'relative_humidity_ref' checked"),
    (DEBUG, "hydrology model: required var 'atmospheric_pressure_ref' checked"),
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
                MODEL_VAR_CHECK_LOG
                + [(ERROR, "The initial_soil_moisture has to be between 0 and 1!")]
            ),
            id="soil moisture out of bounds",
        ),
        pytest.param(
            DataArray([50, 30, 20]),
            0.9,
            pytest.raises(InitialisationError),
            tuple(
                MODEL_VAR_CHECK_LOG
                + [(ERROR, "The initial_soil_moisture must be numeric!")]
            ),
            id="soil moisture not numeric",
        ),
        pytest.param(
            0.5,
            1.9,
            pytest.raises(InitialisationError),
            tuple(
                MODEL_VAR_CHECK_LOG
                + [
                    (
                        ERROR,
                        "The initial_groundwater_saturation has to be between 0 and 1!",
                    )
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
        assert model.drainage_map == {0: [], 1: [0], 2: [1, 2]}

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
                ]
                + MODEL_VAR_CHECK_LOG
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
                ]
                + MODEL_VAR_CHECK_LOG
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
    "cfg_string, raises",
    [
        pytest.param(
            "[core]\n"
            "[core.timing]\nupdate_interval = '1 month'\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n",
            does_not_raise(),
            id="updates correctly",
        ),
        pytest.param(
            "[core]\n"
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n",
            pytest.raises(NotImplementedError),
            id="incorrect update frequency",
        ),
    ],
)
def test_setup(
    dummy_climate_data,
    cfg_string,
    raises,
):
    """Test set up and update."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)

    with raises:
        # initialise model
        model = HydrologyModel.from_config(
            data=dummy_climate_data,
            core_components=core_components,
            config=config,
        )

        model.setup()

        soil_moisture_values = np.repeat(a=[np.nan, 0.5], repeats=[13, 2])

        np.testing.assert_allclose(
            dummy_climate_data["soil_moisture"],
            DataArray(
                np.broadcast_to(soil_moisture_values, (3, 15)).T,
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(15),
                    "layer_roles": (
                        "layers",
                        core_components.layer_structure.layer_roles,
                    ),
                    "cell_id": [0, 1, 2],
                },
                name="soil_moisture",
            ),
            rtol=1e-3,
            atol=1e-3,
        )

        np.testing.assert_allclose(
            dummy_climate_data["groundwater_storage"],
            DataArray(
                [[450.0, 450.0, 450.0], [450.0, 450.0, 450.0]],
                dims=("groundwater_layers", "cell_id"),
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
                    [[0.52002, 0.520263, 0.520006], [0.455899, 0.456052, 0.455858]],
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
                        [-201.975325, -201.197219, -202.071172],
                        [-549.007624, -547.513334, -549.340899],
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
            [1.111498, 1.114365, 1.11434],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_soil_evap = DataArray(
            [16.433136, 16.433136, 16.433136],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_total_discharge = DataArray(
            [0, 1423, 2846],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_runoff_acc = DataArray(
            [0, 0, 0],
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
            model.data["total_river_discharge"],
            exp_total_discharge,
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
            model.data["matric_potential"],
            exp_matric_pot,
            rtol=1e-4,
            atol=1e-4,
        )


def test_calculate_layer_thickness():
    """Test."""

    from virtual_ecosystem.models.hydrology.hydrology_model import (
        calculate_layer_thickness,
    )

    soil_layer_heights = np.array([[-0.5, -0.5, -0.5], [-1.2, -1.2, -1.2]])
    exp_result = np.array([[500, 500, 500], [700, 700, 700]])

    result = calculate_layer_thickness(soil_layer_heights, 1000)

    np.testing.assert_allclose(result, exp_result)


def test_setup_hydrology_input_current_timestep(
    dummy_climate_data, fixture_core_components
):
    """Test that correct values are selected for current time step."""

    from virtual_ecosystem.models.hydrology.hydrology_model import (
        setup_hydrology_input_current_timestep,
    )

    result = setup_hydrology_input_current_timestep(
        data=dummy_climate_data,
        time_index=1,
        days=30,
        seed=42,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        soil_moisture_capacity=0.9,
        soil_moisture_residual=0.1,
        meters_to_mm=1000,
    )

    # Check if all variables were created
    var_list = [
        "current_precipitation",
        "subcanopy_temperature",
        "subcanopy_humidity",
        "subcanopy_pressure",
        "leaf_area_index_sum"
        "current_evapotranspiration"
        "soil_layer_heights"
        "soil_layer_thickness"
        "top_soil_moisture_capacity_mm"
        "top_soil_moisture_residual_mm"
        "soil_moisture_mm"
        "previous_accumulated_runoff"
        "previous_subsurface_flow_accumulated"
        "groundwater_storage",
    ]

    variables = [var for var in result if var not in var_list]
    assert variables

    # check if climate values are selected correctly
    np.testing.assert_allclose(
        np.sum(result["current_precipitation"], axis=1),
        (dummy_climate_data["precipitation"].isel(time_index=1)).to_numpy(),
    )
    np.testing.assert_allclose(
        result["subcanopy_temperature"], dummy_climate_data["air_temperature"][11]
    )
    np.testing.assert_allclose(
        result["subcanopy_humidity"], dummy_climate_data["relative_humidity"][11]
    )
    np.testing.assert_allclose(
        result["subcanopy_pressure"],
        (dummy_climate_data["atmospheric_pressure_ref"].isel(time_index=1)).to_numpy(),
    )
