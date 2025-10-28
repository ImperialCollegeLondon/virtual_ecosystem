"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, INFO
from unittest.mock import patch

import numpy as np
import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check, patch_bypass_setup, patch_run_update

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (DEBUG, "hydrology model: required var 'layer_heights' checked"),
    (DEBUG, "hydrology model: required var 'elevation' checked"),
]


@pytest.mark.parametrize(
    "ini_soil_moisture, ini_groundwater_sat, expected_log_entries",
    [
        pytest.param(
            0.5,
            0.9,
            None,
            id="succeeds",
        ),
    ],
)
def test_hydrology_model_initialization(
    caplog,
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_hydrology_constants,
    ini_soil_moisture,
    ini_groundwater_sat,
    expected_log_entries,
):
    """Test `HydrologyModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # We patch the _setup step as it is tested separately
    with (
        patch_run_update(HydrologyModel),
        patch_bypass_setup(HydrologyModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False

        # Initialize model
        model = HydrologyModel(
            data=dummy_climate_data_varying_canopy,
            core_components=fixture_core_components,
            initial_soil_moisture=ini_soil_moisture,
            initial_groundwater_saturation=ini_groundwater_sat,
            model_constants=fixture_hydrology_constants,
        )

        # In cases where it passes we check that the object has the right properties
        assert isinstance(model, BaseModel)
        assert model.model_name == "hydrology"
        assert repr(model) == "HydrologyModel(update_interval=1209600 seconds)"
        assert model.initial_soil_moisture == ini_soil_moisture
        assert model.initial_groundwater_saturation == ini_groundwater_sat
        # TODO: not sure on the value below, test with more expansive drainage maps
        assert model.drainage_map == {0: [], 1: [], 2: [0, 1, 2, 3], 3: [1]}

    # Final check that expected logging entries are produced
    if expected_log_entries:
        log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,sm_saturation,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[abiotic]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.51\n",
            0.51,
            does_not_raise(),
            (
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
            "[core]\n[abiotic]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n"
            "[hydrology.constants]\nsoil_moisture_saturation = 0.7\n",
            0.7,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                *MODEL_VAR_CHECK_LOG,
            ),
            id="modified_config_correct",
        ),
    ],
)
def test_generate_hydrology_model(
    caplog,
    dummy_climate_data_varying_canopy,
    cfg_string,
    sm_saturation,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the hydrology model works as expected."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel
    from virtual_ecosystem.models.hydrology.model_config import HydrologyConstants

    config_data = ConfigurationLoader(cfg_strings=cfg_string)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)
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
                    data=dummy_climate_data_varying_canopy,
                    configuration=configuration,
                    core_components=core_components,
                    config=configuration,
                )
                mock_setup.assert_called_once()

                # Check arguments passed to _setup
                _called_args, called_kwargs = mock_setup.call_args
                assert (
                    called_kwargs["initial_soil_moisture"]
                    == configuration.hydrology.initial_soil_moisture
                )
                assert (
                    called_kwargs["initial_groundwater_saturation"]
                    == configuration.hydrology.initial_groundwater_saturation
                )

                model_constants = called_kwargs["model_constants"]
                assert isinstance(model_constants, HydrologyConstants)
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
                    [248.938056, 246.470017, 241.110912, 230.144438],
                    [218.994795, 229.328526, 239.665128, 249.794233],
                ],
                "matric_potential": [
                    [-56.432398, -70.967411, -100.068517, -158.92492],
                    [-217.596626, -156.739248, -103.972172, -50.887597],
                ],
                "vertical_flow": [
                    [0.00017, 0.000188, 0.000745, 0.00609],
                    [0.000526, 0.000523, 0.000889, 0.025384],
                ],
            },
            {
                "total_runoff": [
                    1477.363339,
                    1476.076772,
                    7371.383915,
                    2945.792003,
                ],
                "surface_runoff": [20.343781, 6.316444, 2.721491, 1.192358],
                "surface_runoff_routed_plus_local": [
                    20.343781,
                    6.316444,
                    33.295566,
                    7.508803,
                ],
                "soil_evaporation": [5.93727, 12.359247, 25.50399, 51.620636],
            },
            id="1 month",
        ),
        pytest.param(
            pint.Quantity(1, "week"),
            does_not_raise(),
            {
                "soil_moisture": [
                    [249.628102, 248.83347, 247.201583, 243.906481],
                    [215.713193, 227.141752, 238.570238, 249.989266],
                ],
                "matric_potential": [
                    [-52.085807, -57.073175, -66.79106, -85.158475],
                    [-196.720556, -144.330243, -97.954074, -49.718984],
                ],
                "vertical_flow": [
                    [0.000295, 0.000345, 0.000433, 0.00545],
                    [0.000611, 0.000658, 0.000754, 0.009276],
                ],
            },
            {
                "total_runoff": [
                    483.741646,
                    480.053134,
                    2365.561823,
                    936.948501,
                ],
                "surface_runoff": [163.019971, 158.780549, 150.030499, 132.191482],
                "surface_runoff_routed_plus_local": [
                    163.019971,
                    158.780549,
                    754.053001,
                    290.972032,
                ],
                "soil_evaporation": [1.388223, 2.904608, 6.066225, 12.622505],
            },
            id="1 week",
        ),
    ],
)
def test_setup(
    fixture_core_components,
    dummy_climate_data_varying_canopy,
    fixture_configuration,
    update_interval,
    raises,
    expected_2d,
    expected_1d,
):
    """Test set up and update."""
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology import hydrology_tools
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Override the new update interval into the configuration object - it is frozen so
    # need to bypass that mechanism. Also need to override the computed field
    fixture_configuration.core.timing.__dict__["update_interval"] = update_interval
    fixture_configuration.core.timing.__dict__["update_interval_seconds"] = (
        update_interval.to("seconds").magnitude
    )

    core_components = CoreComponents(fixture_configuration.core)
    lyr_strct = core_components.layer_structure

    with (
        patch_run_update(HydrologyModel),
        patch_bypass_setup(HydrologyModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        with raises:
            # initialise model. The setup is run as part of the initialisation
            model = HydrologyModel.from_config(
                data=dummy_climate_data_varying_canopy,
                configuration=fixture_configuration,
                core_components=core_components,
                config=fixture_configuration,
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
            # Mass balance check for the month
            hydrology_tools.check_monthly_mass_balance(
                drainage_map=model.drainage_map,
                surface_channel_inflow_mm=model.data[
                    "surface_runoff_routed_plus_local"
                ].to_numpy(),
                monthly_precipitation_mm=dummy_climate_data_varying_canopy[
                    "precipitation"
                ]
                .isel(time_index=1)
                .to_numpy(),
                monthly_evaporation_mm=model.data["soil_evaporation"].to_numpy(),
            )
