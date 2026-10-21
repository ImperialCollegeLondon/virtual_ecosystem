"""Test module for hydrology.hydrology_model.py."""

from logging import INFO
from unittest.mock import patch

import numpy as np
import pandas as pd
import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (
        INFO,
        "Information required to initialise the hydrology model "
        "successfully extracted.",
    ),
    (INFO, "hydrology model: required initial data variables checked"),
    (INFO, "Adding data array for 'snowfall'"),
    (INFO, "Adding data array for 'snow_water_equivalent'"),
    (INFO, "Adding data array for 'temperature_driven_snowmelt'"),
    (INFO, "Adding data array for 'rain_driven_snowmelt'"),
    (INFO, "Adding data array for 'sublimation_snow'"),
    (INFO, "Adding data array for 'soil_moisture'"),
    (INFO, "Adding data array for 'matric_potential'"),
    (INFO, "Adding data array for 'condensation'"),
    (INFO, "Adding data array for 'groundwater_storage'"),
    (INFO, "Adding data array for 'aerodynamic_resistance_soil'"),
    (INFO, "Adding data array for 'stomatal_conductance'"),
    (INFO, "Adding data array for 'aerodynamic_resistance_canopy'"),
    (INFO, "Adding data array for 'density_air'"),
    (INFO, "Adding data array for 'specific_heat_air'"),
    (INFO, "Adding data array for 'latent_heat_vapourisation'"),
]


@pytest.fixture
def fixture_hydrology_init_data(dummy_climate_data):
    """Returns a reduced dataset suitable for initialising an Abiotic Model."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    # Reduce to data to initialise model
    init_data = Data(grid=dummy_climate_data.grid)
    for var in HydrologyModel.vars_required_for_init:
        init_data[var] = dummy_climate_data.data[var]

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
    np.testing.assert_array_equal(
        model.saturated_hydraulic_conductivity[:, 0],
        np.array([3.5e-5, 3.5e-7]),
    )
    # TODO: not sure on the value below, test with more expansive drainage maps
    assert model.drainage_map == {0: [], 1: [], 2: [0], 3: [1]}

    # Final check that expected logging entries are produced
    log_check(caplog, MODEL_VAR_CHECK_LOG[1:])


@pytest.mark.parametrize(
    "configured_ksat, expected_ksat",
    [
        ([4e-5, 2e-7], (4e-5, 2e-7)),
        (1e-7, (1e-7, 1e-7)),
    ],
)
def test_hydrology_model_resolves_layer_ksat(
    fixture_hydrology_init_data,
    fixture_core_components,
    configured_ksat,
    expected_ksat,
):
    """Test pair-valued and legacy scalar Ksat configuration."""
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel
    from virtual_ecosystem.models.hydrology.model_config import HydrologyConstants

    model = HydrologyModel(
        data=fixture_hydrology_init_data,
        core_components=fixture_core_components,
        initial_soil_moisture=0.5,
        initial_groundwater_saturation=0.9,
        p_wet_wet=0.6,
        p_wet_dry=0.3,
        rainfall_shape_parameter=1.5,
        rainfall_scale_parameter=1.0,
        model_constants=HydrologyConstants(
            saturated_hydraulic_conductivity=configured_ksat
        ),
    )

    np.testing.assert_array_equal(
        model.saturated_hydraulic_conductivity[:, 0],
        np.asarray(expected_ksat),
    )


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
    core_components.grid.set_closest_neighbours()
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
    fixture_hydrology_init_data,
    dummy_climate_data,
    fixture_configuration,
    update_interval,
    monkeypatch,
    tmp_path,
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
    core_components.grid.set_closest_neighbours()

    model = HydrologyModel.from_config(
        data=fixture_hydrology_init_data,
        configuration=fixture_configuration,
        core_components=core_components,
    )
    model.daily_diagnostics_path = tmp_path / "hydrology_daily_diagnostics.csv"

    # Test soil moisture and matric potential initial values
    soil_indices = lyr_strct.index_all_soil
    expected_values = {
        "soil_moisture": (soil_indices, np.full((2, 4), 250.0)),
        "matric_potential": (soil_indices, np.full((2, 4), -49.673613)),
    }
    for var_name, (indices, values) in expected_values.items():
        exp_var = lyr_strct.from_template()
        exp_var[indices] = values
        np.testing.assert_allclose(
            model.data[var_name],
            exp_var,
            rtol=1e-3,
            atol=1e-3,
        )

    # Test groundwater storage
    exp_groundwater = DataArray(
        np.full((2, core_components.grid.n_cells), 450.0),
        dims=("groundwater_layers", "cell_id"),
        coords={"groundwater_layers": [14, 15], "cell_id": [0, 1, 2, 3]},
    )
    np.testing.assert_allclose(
        model.data["groundwater_storage"],
        exp_groundwater,
        rtol=1e-3,
        atol=1e-3,
    )

    # Add additional data required to update the model
    data_required_from_other_sources = set(model.vars_required_for_update) - set(
        model.vars_populated_by_init
    )
    for var in data_required_from_other_sources:
        model.data[var] = dummy_climate_data.data[var]

    from virtual_ecosystem.models.hydrology import below_ground

    daily_soil_moisture = []
    daily_groundwater_loss = []
    update_soil_moisture = below_ground.update_soil_moisture
    update_groundwater_storage = below_ground.update_groundwater_storage

    def record_soil_moisture(*args, **kwargs):
        result = update_soil_moisture(*args, **kwargs)
        daily_soil_moisture.append(result["soil_moisture"].copy())
        return result

    def record_groundwater_loss(*args, **kwargs):
        result = update_groundwater_storage(*args, **kwargs)
        daily_groundwater_loss.append(result["groundwater_loss"].copy())
        return result

    monkeypatch.setattr(below_ground, "update_soil_moisture", record_soil_moisture)
    monkeypatch.setattr(
        below_ground, "update_groundwater_storage", record_groundwater_loss
    )

    # Run the update step
    model.update(time_index=1, seed=42)

    daily_diagnostics = pd.read_csv(model.daily_diagnostics_path)
    assert len(daily_diagnostics) == len(daily_soil_moisture) * model.grid.n_cells
    assert set(
        (
            "update_index",
            "day_in_update",
            "cell_id",
            "precipitation_surface_mm",
            "surface_runoff_mm",
            "topsoil_to_subsoil_flow_mm_day",
            "soil_moisture_start_layer_0_mm",
            "soil_moisture_end_layer_1_mm",
        )
    ).issubset(daily_diagnostics.columns)
    assert daily_diagnostics["update_index"].eq(1).all()

    expected_mean_soil_moisture = np.mean(
        np.stack(daily_soil_moisture, axis=0),
        axis=0,
    )
    np.testing.assert_allclose(
        model.data["soil_moisture"][soil_indices],
        expected_mean_soil_moisture,
    )
    end_soil_moisture = daily_soil_moisture[-1]
    np.testing.assert_allclose(model._soil_moisture_state, end_soil_moisture)
    np.testing.assert_allclose(
        model.data["groundwater_loss"],
        np.sum(np.stack(daily_groundwater_loss, axis=0), axis=0),
    )

    # Test ranges for canopy variables
    canopy_indices = [1, 2, 3, 11]
    canopy_mask = ~np.isnan(
        dummy_climate_data["canopy_temperature"].isel(
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

    # Test ranges for 1D variables
    for var_name in [
        "total_runoff",
        "precipitation_surface",
        "snowfall",
        "subsurface_stormflow",
        "surface_runoff",
        "surface_runoff_routed_plus_local",
        "soil_evaporation",
        "groundwater_loss",
    ]:
        values = model.data[var_name]
        assert np.all(np.isfinite(values)), f"{var_name} has NaNs"

    # Mass balance check
    from virtual_ecosystem.models.hydrology import hydrology_tools

    hydrology_tools.check_monthly_mass_balance(
        drainage_map=model.drainage_map,
        surface_channel_inflow_mm=model.data[
            "surface_runoff_routed_plus_local"
        ].to_numpy(),
        monthly_precipitation_mm=dummy_climate_data.get_time_slice(
            "precipitation", 1
        ).to_numpy(),
        monthly_evaporation_mm=model.data["soil_evaporation"].to_numpy(),
    )

    next_update_start = []

    def record_balance_start(**kwargs):
        if kwargs["period"] == "day 1":
            next_update_start.append(kwargs["storage_start_mm"].copy())

    monkeypatch.setattr(hydrology_tools, "check_water_balance", record_balance_start)
    model.update(time_index=0, seed=43)

    assert next_update_start
    np.testing.assert_allclose(
        next_update_start[0][: end_soil_moisture.shape[0]],
        end_soil_moisture,
    )


def test_update_warns_when_transpiration_is_water_limited(
    fixture_core_components,
    fixture_hydrology_init_data,
    dummy_climate_data,
    fixture_configuration,
):
    """Test that reduced transpiration is reported."""
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    model = HydrologyModel.from_config(
        data=fixture_hydrology_init_data,
        configuration=fixture_configuration,
        core_components=fixture_core_components,
    )

    for var in model.vars_required_for_update:
        model.data[var] = dummy_climate_data.data[var]

    model.data["transpiration"] = dummy_climate_data["transpiration"] * 1000

    with patch(
        "virtual_ecosystem.models.hydrology.hydrology_model.LOGGER.warning"
    ) as mock_warn:
        model.update(time_index=0, seed=42)

    messages = [call.args[0] for call in mock_warn.call_args_list]

    assert any(
        "Transpiration reduced by root-zone water limitation on day 1; "
        "unmet demand totals" in message
        for message in messages
    )


def test_update_limits_soil_evaporation_to_available_topsoil_water(
    fixture_core_components,
    fixture_hydrology_init_data,
    dummy_climate_data,
    fixture_configuration,
    monkeypatch,
    tmp_path,
):
    """Test that excessive soil evaporation is capped without warnings."""
    from virtual_ecosystem.models.hydrology import above_ground
    from virtual_ecosystem.models.hydrology.hydrology_model import HydrologyModel

    model = HydrologyModel.from_config(
        data=fixture_hydrology_init_data,
        configuration=fixture_configuration,
        core_components=fixture_core_components,
    )
    model.daily_diagnostics_path = tmp_path / "hydrology_daily_diagnostics.csv"

    for var in model.vars_required_for_update:
        model.data[var] = dummy_climate_data.data[var]

    calculate_soil_evaporation = above_ground.calculate_soil_evaporation
    available_water_by_day = []

    def calculate_excessive_soil_evaporation(*args, **kwargs):
        result = calculate_soil_evaporation(*args, **kwargs)
        available_water_by_day.append(
            np.maximum(
                kwargs["soil_moisture"] - kwargs["soil_moisture_residual"],
                0.0,
            )
            * model.soil_layer_thickness_mm[0]
        )
        result["soil_evaporation"] = np.full_like(
            result["soil_evaporation"],
            1e6,
        )
        return result

    monkeypatch.setattr(
        above_ground,
        "calculate_soil_evaporation",
        calculate_excessive_soil_evaporation,
    )

    with patch(
        "virtual_ecosystem.models.hydrology.hydrology_model.LOGGER.warning"
    ) as mock_warn:
        model.update(time_index=0, seed=42)

    messages = [call.args[0] for call in mock_warn.call_args_list]
    assert not any(
        "Soil evaporation reduced by topsoil water limitation" in message
        for message in messages
    )

    daily_diagnostics = pd.read_csv(model.daily_diagnostics_path)
    for day, available_water in enumerate(available_water_by_day, start=1):
        daily_evaporation = daily_diagnostics.loc[
            daily_diagnostics["day_in_update"] == day,
            "soil_evaporation_mm",
        ].to_numpy()
        np.testing.assert_allclose(
            daily_evaporation,
            available_water,
            equal_nan=True,
        )
