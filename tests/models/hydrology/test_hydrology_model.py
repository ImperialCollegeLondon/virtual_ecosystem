"""Test module for hydrology.hydrology_model.py."""

from logging import DEBUG, INFO

import numpy as np
import pint
import pytest

from tests.conftest import log_check

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (
        INFO,
        "Information required to initialise the hydrology model "
        "successfully extracted.",
    ),
    (DEBUG, "hydrology model: required var 'layer_heights' checked"),
    (DEBUG, "hydrology model: required var 'elevation' checked"),
    (DEBUG, "hydrology model: required var 'air_temperature_ref' checked"),
    (DEBUG, "hydrology model: required var 'atmospheric_pressure_ref' checked"),
    (INFO, "Adding data array for 'soil_moisture'"),
    (INFO, "Adding data array for 'matric_potential'"),
    (INFO, "Adding data array for 'groundwater_storage'"),
    (INFO, "Adding data array for 'aerodynamic_resistance_soil'"),
    (INFO, "Adding data array for 'stomatal_conductance'"),
    (INFO, "Adding data array for 'aerodynamic_resistance_canopy'"),
    (INFO, "Adding data array for 'density_air'"),
    (INFO, "Adding data array for 'specific_heat_air'"),
    (INFO, "Adding data array for 'latent_heat_vapourisation'"),
]


@pytest.fixture
def fixture_hydrology_init_data(dummy_climate_data_varying_canopy):
    """Returns a reduced dataset suitable for initialising an Abiotic Model."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Reduce to data to initialise model
    init_data = Data(grid=dummy_climate_data_varying_canopy.grid)
    for var in HydrologyModel.vars_required_for_init:
        init_data[var] = dummy_climate_data_varying_canopy[var]

    return init_data


@pytest.mark.parametrize(
    "ini_soil_moisture, ini_groundwater_sat,ini_wet,ini_dry, ini_shape, ini_scale",
    [
        pytest.param(
            0.5,
            0.9,
            0.6,
            0.3,
            1.5,
            1.0,
            id="succeeds",
        ),
    ],
)
def test_hydrology_model_initialization(
    caplog,
    fixture_hydrology_init_data,
    fixture_core_components,
    fixture_hydrology_constants,
    ini_soil_moisture,
    ini_groundwater_sat,
    ini_wet,
    ini_dry,
    ini_shape,
    ini_scale,
):
    """Test `HydrologyModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Initialize model
    model = HydrologyModel(
        data=fixture_hydrology_init_data,
        core_components=fixture_core_components,
        initial_soil_moisture=ini_soil_moisture,
        initial_groundwater_saturation=ini_groundwater_sat,
        p_wet_wet=ini_wet,
        p_wet_dry=ini_dry,
        rainfall_shape_parameter=ini_shape,
        rainfall_scale_parameter=ini_scale,
        model_constants=fixture_hydrology_constants,
    )

    # In cases where it passes we check that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "hydrology"
    assert repr(model) == "HydrologyModel(update_interval=1209600 seconds)"
    assert model.initial_soil_moisture == ini_soil_moisture
    assert model.initial_groundwater_saturation == ini_groundwater_sat
    assert model.p_wet_wet == ini_wet
    assert model.p_wet_dry == ini_dry
    assert model.rainfall_shape_parameter == ini_shape
    assert model.rainfall_scale_parameter == ini_scale
    # TODO: not sure on the value below, test with more expansive drainage maps
    assert model.drainage_map == {0: [], 1: [], 2: [0, 1, 2, 3], 3: [1]}

    # Final check that expected logging entries are produced
    log_check(caplog, MODEL_VAR_CHECK_LOG[1:])


@pytest.mark.parametrize(
    "cfg_string,sm_saturation,expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
            "[abiotic]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.51\n"
            "p_wet_wet = 0.6\n"
            "p_wet_dry = 0.3\n"
            "rainfall_shape_parameter = 1.5\n"
            "rainfall_scale_parameter = 1.0\n",
            0.51,
            MODEL_VAR_CHECK_LOG,
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
            "[abiotic]\n"
            "[hydrology]\ninitial_soil_moisture = 0.5\n"
            "initial_groundwater_saturation = 0.9\n"
            "p_wet_wet = 0.6\n"
            "p_wet_dry = 0.3\n"
            "rainfall_shape_parameter = 1.5\n"
            "rainfall_scale_parameter = 1.0\n"
            "[hydrology.constants]\nsoil_moisture_saturation = 0.7\n",
            0.7,
            MODEL_VAR_CHECK_LOG,
            id="modified_config_correct",
        ),
    ],
)
def test_generate_hydrology_model(
    caplog,
    fixture_hydrology_init_data,
    cfg_string,
    sm_saturation,
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

    model = HydrologyModel.from_config(
        data=fixture_hydrology_init_data,
        configuration=configuration,
        core_components=core_components,
    )

    assert isinstance(model.model_constants, HydrologyConstants)
    assert model.model_constants.soil_moisture_saturation == sm_saturation

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "update_interval",
    [
        pytest.param(pint.Quantity(1, "month"), id="1 month"),
        pytest.param(pint.Quantity(1, "week"), id="1 week"),
    ],
)
def test_setup_and_update_hydrology_model_ranges(
    fixture_core_components,
    fixture_hydrology_init_data,
    dummy_climate_data_varying_canopy,
    fixture_configuration,
    update_interval,
):
    """Test hydrology model update with ranges."""

    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Override update interval
    fixture_configuration.core.timing.__dict__["update_interval"] = update_interval
    fixture_configuration.core.timing.__dict__["update_interval_seconds"] = (
        update_interval.to("seconds").magnitude
    )

    # Initialize core and model
    core_components = CoreComponents(fixture_configuration.core)
    lyr_strct = core_components.layer_structure

    model = HydrologyModel.from_config(
        data=fixture_hydrology_init_data,
        configuration=fixture_configuration,
        core_components=core_components,
    )

    # Populate variables required for update
    missing_vars = set(model.vars_required_for_update) - set(
        model.vars_populated_by_init
    )
    for var in missing_vars:
        model.data[var] = dummy_climate_data_varying_canopy[var]

    # Run update
    model.update(time_index=1, seed=42)

    # Test ranges for canopy variables
    canopy_indices = [1, 2, 3, 11]
    canopy_mask = ~np.isnan(
        dummy_climate_data_varying_canopy["canopy_temperature"].isel(
            layers=lyr_strct.index_filled_canopy
        )
    )
    for var_name in ["canopy_evaporation", "interception"]:
        values = model.data[var_name][canopy_indices]
        masked_values = np.isfinite(values.where(canopy_mask))
        # All values finite
        assert np.all(masked_values), f"{var_name} has NaNs"
        # Values non-negative
        assert np.all(masked_values >= 0), f"{var_name} has negative values"
        # Reasonable upper bound (example: 20 mm/day)
        assert np.all(masked_values <= 20), f"{var_name} exceeds expected upper bound"

    # Test ranges for 2D soil variables
    soil_indices = lyr_strct.index_all_soil
    for var_name in [
        "soil_moisture",
        "matric_potential",
        "vertical_flow",
    ]:
        values = model.data[var_name][soil_indices]
        assert np.all(np.isfinite(values)), f"{var_name} has NaNs"
        # Typical physical ranges
        if var_name == "soil_moisture":
            assert np.all((values >= 0) & (values <= 500)), f"{var_name} out of range"
        elif var_name == "matric_potential":
            assert np.all((values <= 0) & (values >= -500)), f"{var_name} out of range"
        elif var_name == "vertical_flow":
            assert np.all(values >= 0), f"{var_name} negative"

    # Test ranges for 1D variables
    for var_name in [
        "total_runoff",
        "surface_runoff",
        "surface_runoff_routed_plus_local",
        "soil_evaporation",
    ]:
        values = model.data[var_name]
        assert np.all(np.isfinite(values)), f"{var_name} has NaNs"
        assert np.all(values >= 0), f"{var_name} negative"
        assert np.all(values <= 10000), f"{var_name} exceeds expected max"

    # Mass balance check
    from virtual_ecosystem.models.hydrology import hydrology_tools

    hydrology_tools.check_monthly_mass_balance(
        drainage_map=model.drainage_map,
        surface_channel_inflow_mm=surface_runoff_mm,
        monthly_precipitation_mm=precipitation_mm,
        monthly_evaporation_mm=soil_evap_mm,
    )

    # 5. 2D variables have finite values somewhere
    for var in ["matric_potential", "vertical_flow"]:
        vals = model.data[var].to_numpy().flatten()
        vals = vals[~np.isnan(vals)]
        assert len(vals) > 0, f"{var} has no valid values"
