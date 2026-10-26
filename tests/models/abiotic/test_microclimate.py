"""Test microclimate.py."""

import warnings

import numpy as np
import pytest
from pyrealm.constants import CoreConst as PyrealmCoreConst
from xarray import DataArray

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


def test_prepare_static_inputs_returns_consistent_outputs(
    dummy_climate_data,
    fixture_core_components,
    fixture_abiotic_indices,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test prepare_static_inputs returns sensible and consistent outputs."""

    from virtual_ecosystem.models.abiotic.microclimate import prepare_static_inputs

    data = dummy_climate_data
    layer_structure = fixture_core_components.layer_structure
    idx = fixture_abiotic_indices
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    result = prepare_static_inputs(
        data=data,
        idx=idx,
        time_index=0,
        layer_structure=layer_structure,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    # Check expected keys exist
    expected_keys = {
        "canopy_height",
        "leaf_area_index",
        "lai_sum",
        "evapotranspiration",
        "atmospheric_pressure",
        "atmospheric_co2",
        "geometry",
        "absorbed_longwave_radiation",
        "cell_area",
        "soil_moisture_volumetric",
    }

    assert set(result.keys()) == expected_keys

    # Shape checks
    n_cells = data.grid.n_cells
    n_layers = layer_structure.n_layers

    assert result["canopy_height"].shape == (n_cells,)
    assert result["lai_sum"].shape == (n_cells,)
    assert result["leaf_area_index"].shape == (n_layers, n_cells)
    assert result["evapotranspiration"].shape == (n_layers, n_cells)
    assert result["atmospheric_pressure"].shape == (n_layers, n_cells)
    assert result["atmospheric_co2"].shape == (n_layers, n_cells)
    assert result["geometry"]["thickness"].shape == (n_layers, n_cells)

    # Physical plausibility checks
    # Canopy height must be >= 0
    assert np.all(result["canopy_height"] >= 0)

    # LAI sum must be >= 0
    assert np.all(result["lai_sum"] >= 0)

    # Evapotranspiration must be >= 0
    assert np.all(
        result["evapotranspiration"][~np.isnan(result["evapotranspiration"])] >= 0
    )

    # Atmospheric pressure must be positive
    assert np.all(
        result["atmospheric_pressure"][~np.isnan(result["atmospheric_pressure"])] > 0
    )

    # Longwave absorption must be positive
    assert np.all(
        result["absorbed_longwave_radiation"][
            ~np.isnan(result["absorbed_longwave_radiation"])
        ]
        >= 0
    )

    # Internal consistency checks
    # ET should equal canopy_evaporation + transpiration
    expected_et = (data["canopy_evaporation"] + data["transpiration"]).to_numpy()

    np.testing.assert_allclose(
        result["evapotranspiration"],
        expected_et,
        rtol=1e-6,
        atol=1e-6,
    )

    # LAI sum equals nan-sum over canopy layers
    manual_lai = np.nansum(data["leaf_area_index"][idx.canopy].to_numpy(), axis=0)

    np.testing.assert_allclose(
        result["lai_sum"],
        manual_lai,
        rtol=1e-6,
        atol=1e-6,
    )


def test_calculate_wind_profiles(
    dummy_climate_data,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_static_inputs,
    fixture_core_components,
):
    """Test wind profile calculations for physical plausibility and consistency."""

    from virtual_ecosystem.models.abiotic.microclimate import calculate_wind_profiles

    data = dummy_climate_data
    static_inputs = fixture_static_inputs
    time_index = 0

    result = calculate_wind_profiles(
        static=static_inputs,
        data=data,
        time_index=time_index,
        abiotic_constants=fixture_abiotic_constants,
        core_constants=fixture_core_constants,
        layer_structure=fixture_core_components.layer_structure,
    )

    # Shape checks
    n_layers, n_cells = data["layer_heights"].shape

    assert result["zero_plane_displacement"].shape == (n_cells,)
    assert result["roughness_length"].shape == (n_cells,)
    assert result["friction_velocity"].shape == (n_cells,)
    assert result["wind_speed"].shape == (n_layers, n_cells)
    assert result["mixing_coefficient"].shape == (n_layers, n_cells)

    # No unexpected NaNs
    for key, arr in result.items():
        assert not np.all(np.isnan(arr)), f"{key} is entirely NaN"

    # Physical bounds
    # Roughness length must be positive
    assert np.all(result["roughness_length"] > 0)

    # Friction velocity must be >= 0
    assert np.all(result["friction_velocity"] >= 0)

    # Wind speeds should be >= minimum windspeed
    assert np.all(np.isnan(result["wind_speed"]) >= 0)

    # Mixing coefficient must be >= 0
    assert np.all(result["mixing_coefficient"] >= 0)

    # Physical relationships
    # Zero plane displacement should be less than canopy height
    assert np.all(
        result["zero_plane_displacement"][~np.isnan(static_inputs["canopy_height"])]
        <= static_inputs["canopy_height"][~np.isnan(static_inputs["canopy_height"])]
    )


def test_generate_hourly_forcing(
    dummy_climate_data,
    fixture_static_inputs,
    fixture_core_components,
    fixture_abiotic_constants,
):
    """Test generate_hourly_forcing with prepared static inputs."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_total_absorbed_shortwave_radiation,
    )
    from virtual_ecosystem.models.abiotic.microclimate import generate_hourly_forcing

    data = dummy_climate_data
    static_inputs = fixture_static_inputs
    abiotic_constants = fixture_abiotic_constants
    time_index = 0
    month = 2
    days = 30
    latitude = 0.0

    forcing = generate_hourly_forcing(
        data=data,
        static=static_inputs,
        time_index=time_index,
        month=month,
        days=days,
        latitude=latitude,
        abiotic_constants=abiotic_constants,
    )

    # Shape checks
    n_cells = data.grid.n_cells
    n_layers = fixture_core_components.layer_structure.n_layers

    assert forcing["air_temperature_hourly"].shape == (24, n_cells)
    assert forcing["relative_humidity_hourly"].shape == (24, n_cells)
    assert forcing["shortwave_absorption_hourly"].shape == (24, n_layers, n_cells)
    assert forcing["evapotranspiration_hourly"].shape == (24, n_layers, n_cells)
    assert forcing["soil_evaporation_hourly"].shape == (24, n_cells)

    # Air temperature bounds
    air_temp = forcing["air_temperature_hourly"]
    assert np.all(air_temp >= 10.0)
    assert np.all(air_temp <= 40.0)

    # Relative humidity bounds
    rh = forcing["relative_humidity_hourly"]
    assert np.all(rh >= 0.0)
    assert np.all(rh <= 100.0)

    # Shortwave radiation only during daytime
    sw = forcing["shortwave_absorption_hourly"]
    nighttime_hours = [0, 1, 2, 3, 22, 23]
    # Pick a mid-layer for testing
    assert np.all(sw[nighttime_hours, 11, :] == 0.0)

    # Check conservation over monthly totals
    mask = ~np.isnan(static_inputs["evapotranspiration"])

    monthly_sum_et = np.nansum(forcing["evapotranspiration_hourly"], axis=0) * 30
    monthly_sum_soil_evap = np.nansum(forcing["soil_evaporation_hourly"], axis=0) * 30

    np.testing.assert_allclose(
        monthly_sum_et[mask], static_inputs["evapotranspiration"][mask], rtol=1e-5
    )
    np.testing.assert_allclose(
        monthly_sum_soil_evap,
        data["soil_evaporation"].to_numpy(),
        rtol=1e-5,
    )

    monthly_mean_sw_abs = np.nanmean(forcing["shortwave_absorption_hourly"], axis=0)
    total_shortwave_absorption = calculate_total_absorbed_shortwave_radiation(
        downward_shortwave_radiation=data.get_time_slice(
            "downward_shortwave_radiation", time_index
        ).to_numpy(),
        shortwave_absorption_by_canopy=data["shortwave_absorption"].to_numpy(),
        fraction_par_used=abiotic_constants.fraction_par_used_for_photosynthesis,
        leaf_absorptance_non_par=abiotic_constants.leaf_absorptance_non_par,
        par_fraction=abiotic_constants.par_fraction_of_shortwave_radiation,
    )
    np.testing.assert_allclose(
        monthly_mean_sw_abs,
        total_shortwave_absorption,
        rtol=1e-5,
        equal_nan=True,
    )


def test_initialize_state_shapes(dummy_climate_data):
    """Test initialize_state returns all expected state variables."""

    from virtual_ecosystem.models.abiotic.microclimate import initialize_state

    data = dummy_climate_data
    state = initialize_state(data=data)

    # Expected keys
    expected_keys = [
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
        "relative_humidity",
        "aerodynamic_resistance_soil",
        "longwave_emission",
    ]
    assert set(state.keys()) == set(expected_keys)


def test_initialize_hourly_record(dummy_climate_data, fixture_core_components):
    """Test _initialize_hourly_record creates arrays of correct shape and type."""

    from virtual_ecosystem.models.abiotic.microclimate import initialize_hourly_record

    data = dummy_climate_data
    layer_structure = fixture_core_components.layer_structure

    # Variables we want to track
    vars_updated = ("air_temperature", "soil_temperature")

    # Initialize hourly record for 24 hours
    hourly_record = initialize_hourly_record(
        data=data,
        vars_updated=vars_updated,
        time_dim=24,
        layer_structure=layer_structure,
    )

    # Check the returned object is a dict
    assert isinstance(hourly_record, dict)

    # Check all requested variables are present
    for var in vars_updated:
        assert var in hourly_record

    # Check the shape of each variable array
    for var in vars_updated:
        arr = hourly_record[var]
        # Should have shape (time_dim, n_layers, n_cells)
        assert arr.shape[0] == 24
        assert arr.shape[1] == layer_structure.n_layers
        assert arr.shape[2] == data.grid.n_cells

        # Arrays should be numeric
        assert np.issubdtype(arr.dtype, np.number)


def test_update_forcing_boundary_conditions(
    dummy_climate_data, fixture_core_components
):
    """Test update forcing_correctly updates state with hourly forcing."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        update_forcing_boundary_conditions,
    )

    # Dimensions
    time_dim = 24
    n_cells = dummy_climate_data.grid.n_cells
    n_layers = fixture_core_components.layer_structure.n_layers
    hour = 1

    # Initial state
    state = {
        "air_temperature": np.zeros((n_layers, n_cells)),
        "relative_humidity": np.zeros((n_layers, n_cells)),
    }

    # Dummy forcing arrays
    hourly_forcing = {
        "air_temperature_hourly": np.random.rand(time_dim, n_cells),
        "relative_humidity_hourly": np.random.rand(time_dim, n_cells),
        "shortwave_absorption_hourly": np.random.rand(time_dim, n_layers, n_cells),
        "evapotranspiration_hourly": np.random.rand(time_dim, n_layers, n_cells),
        "soil_evaporation_hourly": np.random.rand(time_dim, n_cells),
    }

    # Keep expected slices for comparison
    expected_air = hourly_forcing["air_temperature_hourly"][hour]
    expected_rh = hourly_forcing["relative_humidity_hourly"][hour]
    expected_sw = hourly_forcing["shortwave_absorption_hourly"][hour, :, :]
    expected_et = hourly_forcing["evapotranspiration_hourly"][hour, :, :]
    expected_soil_evap = hourly_forcing["soil_evaporation_hourly"][hour]

    updated_state = update_forcing_boundary_conditions(
        state=state,
        hourly_forcing=hourly_forcing,
        hour=hour,
    )

    # Check in-place update
    assert updated_state is state

    # Check boundary replacement (layer 0)
    np.testing.assert_allclose(state["air_temperature"][0], expected_air)
    np.testing.assert_allclose(state["relative_humidity"][0], expected_rh)

    # Check
    np.testing.assert_allclose(state["shortwave_absorption"], expected_sw)
    np.testing.assert_allclose(state["evapotranspiration"], expected_et)
    np.testing.assert_allclose(state["soil_evaporation"], expected_soil_evap)


def test_calculate_thermodynamics_day_and_night(
    dummy_climate_data,
    fixture_static_inputs,
    fixture_state_inputs,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_abiotic_indices,
):
    """Test _calculate_thermodynamics produces expected outputs for day and night."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        calculate_thermodynamics,
    )

    data = dummy_climate_data
    static = fixture_static_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    idx = fixture_abiotic_indices
    n_cells = data.grid.n_cells
    n_layers = 14
    hour = 0

    state = fixture_state_inputs

    # Daytime forcing (non-zero shortwave)
    hourly_forcing_day = {
        "shortwave_absorption_hourly": np.ones((1, n_layers, n_cells)),
    }

    # Night forcing (zero shortwave)
    hourly_forcing_night = {
        "shortwave_absorption_hourly": np.zeros((1, n_layers, n_cells)),
    }

    # DAY TEST
    result_day = calculate_thermodynamics(
        state=state,
        static=static,
        hourly_forcing=hourly_forcing_day,
        hour=hour,
        n_cells=n_cells,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )

    assert isinstance(result_day, dict)
    assert result_day["aerodynamic_resistance_canopy"].shape == (n_cells,)
    np.testing.assert_allclose(
        result_day["aerodynamic_resistance_soil"],
        data["aerodynamic_resistance_soil"],
    )

    # NIGHT TEST
    result_night = calculate_thermodynamics(
        state=state,
        static=static,
        hourly_forcing=hourly_forcing_night,
        hour=hour,
        n_cells=n_cells,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )

    assert np.all(result_night["aerodynamic_resistance_canopy"] == 100.0)
    assert np.all(result_night["aerodynamic_resistance_soil"] == 500.0)

    # Output shape checks
    assert result_day["density_air"].shape == (n_layers, n_cells)
    assert result_day["specific_heat_air"].shape == (n_layers, n_cells)
    assert result_day["latent_heat_vapourisation"].shape == (n_layers, n_cells)
    assert result_day["ventilation_rate"].shape == (n_cells,)


def test_calculate_vegetation_temperature(
    fixture_abiotic_constants,
    fixture_core_constants,
    dummy_climate_data,
    fixture_static_inputs,
    fixture_state_inputs,
    fixture_abiotic_indices,
):
    """Test calculate_vegetation_temperature produces expected outputs."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        calculate_vegetation_temperature,
    )

    data = dummy_climate_data
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    static = fixture_static_inputs
    state = fixture_state_inputs
    idx = fixture_abiotic_indices

    result = calculate_vegetation_temperature(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )

    # Shape checks
    assert isinstance(result, np.ndarray)
    assert result.shape == (14, 4)

    # Mask where input is not NaN
    mask = ~np.isnan(data["canopy_temperature"])

    # Assert plausible range for non-NaN input
    assert np.all((result[mask] > 0) & (result[mask] < 50))

    # Assert NaNs are preserved
    assert np.all(np.isnan(result[~mask]))


def test_calculate_vegetation_fluxes(
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_static_inputs,
    fixture_state_inputs,
    fixture_abiotic_indices,
):
    """Test calculate_vegetation_fluxes produces expected outputs."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        calculate_vegetation_fluxes,
    )

    static = fixture_static_inputs
    state = fixture_state_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    idx = fixture_abiotic_indices

    result = calculate_vegetation_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )

    # Assert all expected keys exist and have correct shapes
    assert isinstance(result, dict)
    expected_keys = {
        "longwave_emission",
        "sensible_heat_flux",
        "latent_heat_flux",
        "energy_balance_residual",
        "net_radiation",
    }
    assert set(result.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (14, 4)


def test_calculate_soil_fluxes(
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_abiotic_indices,
    fixture_static_inputs,
    fixture_state_inputs,
):
    """Test calculate_soil_fluxes produces expected outputs."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        calculate_soil_fluxes,
    )

    static = fixture_static_inputs
    state = fixture_state_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    idx = fixture_abiotic_indices
    time_interval = 3600

    result = calculate_soil_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        time_interval=time_interval,
        idx=idx,
    )

    # Check values, output keys and shapes
    expected_ground_flux = np.array(
        [-301.374188, -331.896355, -373.303554, -393.390826]
    )

    np.testing.assert_allclose(
        result["ground_heat_flux"], expected_ground_flux, rtol=1e-5, atol=1e-5
    )

    # Ensure all keys exist
    assert set(result.keys()) == {
        "longwave_emission_soil",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "ground_heat_flux",
        "net_radiation_soil",
    }


def test_update_atmospheric_humidity(
    dummy_climate_data,
    fixture_core_constants,
    fixture_abiotic_constants,
    fixture_abiotic_indices,
    fixture_static_inputs,
    fixture_state_inputs,
):
    """Test update atmospheric humidity."""

    from pyrealm.core.hygro import calculate_vp_sat

    from virtual_ecosystem.models.abiotic.microclimate import (
        update_atmospheric_humidity,
    )

    data = dummy_climate_data
    idx = fixture_abiotic_indices
    static = fixture_static_inputs
    state = fixture_state_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    pyrealm_core_constants = PyrealmCoreConst()
    abiotic_bounds = AbioticSimpleBounds()

    vp_sat = calculate_vp_sat(
        tc=state["air_temperature"],
        core_const=pyrealm_core_constants,
    )
    result = update_atmospheric_humidity(
        state=state,
        static=static,
        pyrealm_core_constants=pyrealm_core_constants,
        core_constants=core_constants,
        abiotic_constants=abiotic_constants,
        abiotic_bounds=abiotic_bounds,
        idx=idx,
        time_interval=3600,
    )

    # Check output keys and shapes
    mask = ~np.isnan(data["relative_humidity"].to_numpy())
    for key in [
        "relative_humidity",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "specific_humidity",
        "condensation",
    ]:
        assert key in result
        assert isinstance(result[key], np.ndarray)
        assert np.all(np.isnan(result[key][~mask]))

    # Expected trends: ET and mixing should raise humidity slightly where is not NaN
    assert np.all(result["specific_humidity"][mask] >= 0.00)

    # VPD should be reduced where evapotranspiration or mixing adds moisture
    assert np.all(result["vapour_pressure_deficit"][mask] > 0.0)

    # VP should be below saturation except above canopy where it accumulated with mixing
    tolerance = 0.02
    assert np.all(
        result["vapour_pressure"][1:][mask[1:]] <= vp_sat[1:][mask[1:]] + tolerance
    )

    # RH should be between 0 and 100
    assert np.all(
        (result["relative_humidity"][mask] > 0)
        & (result["relative_humidity"][mask] < 100)
    )

    # Condensation should be >=0
    assert np.all(result["condensation"][mask] >= 0)


def test_run_hour_step_orchestration(
    dummy_climate_data,
    fixture_abiotic_indices,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_static_inputs,
    fixture_core_components,
):
    """Test that one hourly microclimate step runs and returns expected outputs.

    This is a plumbing/orchestration test only. It checks that the function executes,
    updates the expected variables, and preserves expected array shapes. It does not
    impose strict physical bounds because the synthetic dummy fixture is not guaranteed
    to be dynamically equilibrated for the fully coupled hourly solve.
    """

    from virtual_ecosystem.models.abiotic.microclimate import (
        calculate_wind_profiles,
        generate_hourly_forcing,
        initialize_state,
        run_hour_step,
    )

    # Setup
    data = dummy_climate_data
    idx = fixture_abiotic_indices
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    static = fixture_static_inputs
    layer_structure = fixture_core_components.layer_structure

    hour = 12
    days = 30
    time_interval = 3600
    time_index = 0

    pyrealm_core_constants = PyrealmCoreConst()
    abiotic_bounds = AbioticSimpleBounds()

    state = initialize_state(data=data)

    hourly_forcing = generate_hourly_forcing(
        data=data,
        static=static,
        time_index=time_index,
        month=1,
        days=days,
        latitude=0,
        abiotic_constants=abiotic_constants,
    )

    wind = calculate_wind_profiles(
        static=static,
        data=data,
        time_index=time_index,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        layer_structure=layer_structure,
    )
    static.update(wind)

    # Run
    result = run_hour_step(
        state=state,
        static=static,
        hourly_forcing=hourly_forcing,
        hour=hour,
        idx=idx,
        layer_structure=layer_structure,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        pyrealm_core_constants=pyrealm_core_constants,
        abiotic_bounds=abiotic_bounds,
        time_interval=time_interval,
    )

    # run_hour_step mutates and returns state; use returned dict explicitly
    state = result

    # Shape checks
    expected_static = {
        "zero_plane_displacement": (4,),
        "roughness_length": (4,),
        "friction_velocity": (4,),
        "wind_speed": (14, 4),
        "mixing_coefficient": (14, 4),
    }
    expected_state = {
        "air_temperature": (14, 4),
        "canopy_temperature": (14, 4),
        "soil_temperature": (14, 4),
        "relative_humidity": (14, 4),
        "aerodynamic_resistance_soil": (4,),
        "shortwave_absorption": (14, 4),
        "evapotranspiration": (14, 4),
        "soil_evaporation": (4,),
        "density_air": (14, 4),
        "specific_heat_air": (14, 4),
        "latent_heat_vapourisation": (14, 4),
        "aerodynamic_resistance_canopy": (4,),
        "ventilation_rate": (4,),
        "longwave_emission": (14, 4),
        "sensible_heat_flux": (14, 4),
        "latent_heat_flux": (14, 4),
        "energy_balance_residual": (14, 4),
        "ground_heat_flux": (4,),
        "vapour_pressure": (14, 4),
        "vapour_pressure_deficit": (14, 4),
        "specific_humidity": (14, 4),
        "condensation": (14, 4),
    }

    for key, shape in expected_static.items():
        arr = static.get(key)
        assert arr is not None, f"{key} missing from static output"
        assert arr.shape == shape, f"{key} shape mismatch: {arr.shape} != {shape}"

    for key, shape in expected_state.items():
        arr = state.get(key)
        assert arr is not None, f"{key} missing from state output"
        assert arr.shape == shape, f"{key} shape mismatch: {arr.shape} != {shape}"


def test_static_variable_created(fixture_core_components):
    """Test static variables created in update."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    layer_structure = fixture_core_components.layer_structure
    static = {"atmospheric_pressure": np.full((14, 4), 96)}
    data_record = {}
    vars_updated = ("atmospheric_pressure",)
    variable_data = {
        "atmospheric_pressure": DataArray(
            static["atmospheric_pressure"], dims=("layers", "cell_id")
        )
    }
    output_templates = create_output_templates(
        variable_data=variable_data,
        vars_updated=vars_updated,
        layer_structure=layer_structure,
        time_dim=24,
    )

    output = build_output_from_record(
        data_record,
        static,
        vars_updated,
        output_templates,
        layer_structure,
    )

    assert "atmospheric_pressure" in output
    assert output["atmospheric_pressure"].dims == ("layers", "cell_id")
    atmosphere_layers = layer_structure.index_filled_atmosphere
    np.testing.assert_allclose(
        output["atmospheric_pressure"].to_numpy()[atmosphere_layers],
        static["atmospheric_pressure"][atmosphere_layers],
    )
    assert np.isnan(output["atmospheric_pressure"].to_numpy()[~atmosphere_layers]).all()

    with pytest.raises(
        ValueError,
        match="Hourly output requested for unavailable variable 'atmospheric_pressure'",
    ):
        build_output_from_record(
            data_record={"air_temperature": np.full((24, 14, 4), 25.0)},
            static=static,
            vars_updated=("atmospheric_pressure", "atmospheric_pressure_hourly"),
            output_templates=create_output_templates(
                variable_data=variable_data,
                vars_updated=(
                    "atmospheric_pressure",
                    "atmospheric_pressure_hourly",
                ),
                layer_structure=layer_structure,
                time_dim=24,
            ),
            layer_structure=layer_structure,
        )


def test_time_cell_variable_averaged(fixture_core_components):
    """Test time cell variables averaged in update."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    layer_structure = fixture_core_components.layer_structure
    static = {}
    data_record = {"ground_heat_flux": np.random.rand(24, 4)}
    vars_updated = ("ground_heat_flux",)
    output_templates = create_output_templates(
        variable_data={"ground_heat_flux": DataArray(np.empty(4), dims=("cell_id",))},
        vars_updated=vars_updated,
        layer_structure=layer_structure,
        time_dim=24,
    )

    output = build_output_from_record(
        data_record,
        static,
        vars_updated,
        output_templates,
        layer_structure,
    )

    expected = np.nanmean(data_record["ground_heat_flux"], axis=0)

    np.testing.assert_allclose(
        output["ground_heat_flux"].values,
        expected,
    )

    assert output["ground_heat_flux"].dims == ("cell_id",)


def test_time_layer_cell_variable_averaged(fixture_core_components):
    """Test time layer cell variables averaged in update."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    layer_structure = fixture_core_components.layer_structure
    static = {}
    data_record = {"soil_temperature": np.random.rand(24, 2, 4)}
    vars_updated = ("soil_temperature", "soil_temperature_hourly")
    output_templates = create_output_templates(
        variable_data={
            "soil_temperature": DataArray(
                np.empty((2, 4)),
                dims=("layers", "cell_id"),
                coords={"layers": [0, 1], "cell_id": [0, 1, 2, 3]},
            )
        },
        vars_updated=vars_updated,
        layer_structure=layer_structure,
        time_dim=24,
    )

    output = build_output_from_record(
        data_record,
        static,
        vars_updated,
        output_templates,
        layer_structure,
    )

    expected = np.nanmean(data_record["soil_temperature"], axis=0)

    np.testing.assert_allclose(
        output["soil_temperature"].values,
        expected,
    )

    assert output["soil_temperature"].dims == ("layers", "cell_id")
    assert output["soil_temperature_hourly"].dims == ("hour", "layers", "cell_id")
    np.testing.assert_array_equal(
        output["soil_temperature_hourly"]["hour"],
        np.arange(data_record["soil_temperature"].shape[0]),
    )
    np.testing.assert_allclose(
        output["soil_temperature_hourly"],
        data_record["soil_temperature"],
    )


def test_output_templates_and_recorded_values_across_dimensions(
    fixture_core_components,
):
    """Check output dimensions, coordinates, and values for all output shapes."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    layer_structure = fixture_core_components.layer_structure
    cell_ids = layer_structure.from_template()["cell_id"].to_numpy()
    layers = layer_structure.from_template()["layers"].to_numpy()
    data_record = {
        "air_temperature": np.arange(24 * len(cell_ids), dtype=float).reshape(
            24, len(cell_ids)
        ),
        "soil_temperature": np.arange(
            24 * len(layers) * len(cell_ids), dtype=float
        ).reshape(24, len(layers), len(cell_ids)),
    }
    variables = {
        "air_temperature": DataArray(
            np.empty(len(cell_ids)), dims=("cell_id",), coords={"cell_id": cell_ids}
        ),
        "soil_temperature": DataArray(
            np.empty((len(layers), len(cell_ids))),
            dims=("layers", "cell_id"),
            coords={"layers": layers, "cell_id": cell_ids},
        ),
    }
    vars_updated = (
        "air_temperature",
        "air_temperature_hourly",
        "soil_temperature",
        "soil_temperature_hourly",
    )
    templates = create_output_templates(
        variable_data=variables,
        vars_updated=vars_updated,
        layer_structure=layer_structure,
        time_dim=24,
    )
    assert all(isinstance(template, DataArray) for template in templates.values())

    outputs = build_output_from_record(
        data_record=data_record,
        static={},
        vars_updated=vars_updated,
        output_templates=templates,
        layer_structure=layer_structure,
    )

    assert set(outputs) == set(vars_updated)
    for name in vars_updated:
        assert templates[name].dims == outputs[name].dims
        assert templates[name].shape == outputs[name].shape
        for coordinate in outputs[name].coords:
            np.testing.assert_array_equal(
                templates[name].coords[coordinate],
                outputs[name][coordinate],
            )

    assert outputs["air_temperature"].dims == ("cell_id",)
    assert outputs["air_temperature_hourly"].dims == ("hour", "cell_id")
    assert outputs["soil_temperature"].dims == ("layers", "cell_id")
    assert outputs["soil_temperature_hourly"].dims == (
        "hour",
        "layers",
        "cell_id",
    )

    for name, expected_dims in (
        ("air_temperature_hourly", ("hour", "cell_id")),
        ("soil_temperature_hourly", ("hour", "layers", "cell_id")),
    ):
        for dim in expected_dims:
            np.testing.assert_array_equal(
                outputs[name][dim],
                np.arange(24)
                if dim == "hour"
                else variables[name.removesuffix("_hourly")][dim],
            )

    np.testing.assert_allclose(
        outputs["air_temperature"],
        np.mean(data_record["air_temperature"], axis=0),
    )
    np.testing.assert_allclose(
        outputs["air_temperature_hourly"],
        data_record["air_temperature"],
    )
    np.testing.assert_allclose(
        outputs["soil_temperature"],
        np.mean(data_record["soil_temperature"], axis=0),
    )
    np.testing.assert_allclose(
        outputs["soil_temperature_hourly"],
        data_record["soil_temperature"],
    )


def test_nan_slices_do_not_emit_runtime_warnings(fixture_core_components):
    """All-NaN cells remain NaN without leaking NumPy reduction warnings."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    layer_structure = fixture_core_components.layer_structure
    cell_ids = layer_structure.from_template()["cell_id"].to_numpy()
    layers = layer_structure.from_template()["layers"].to_numpy()
    air_temperature = np.full((24, len(layers), len(cell_ids)), np.nan)
    soil_temperature = np.full_like(air_temperature, np.nan)
    air_temperature[:, :, 0] = 20.0
    soil_temperature[:, :, 0] = 15.0
    record = {
        "air_temperature": air_temperature,
        "soil_temperature": soil_temperature,
    }
    variables = {
        name: DataArray(
            np.empty((len(layers), len(cell_ids))),
            dims=("layers", "cell_id"),
            coords={"layers": layers, "cell_id": cell_ids},
        )
        for name in ("air_temperature", "soil_temperature", "diurnal_temperature_range")
    }
    vars_updated = (
        "air_temperature",
        "soil_temperature",
        "diurnal_temperature_range",
    )
    templates = create_output_templates(
        variable_data=variables,
        vars_updated=vars_updated,
        layer_structure=layer_structure,
        time_dim=24,
    )

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        outputs = build_output_from_record(
            data_record=record,
            static={},
            vars_updated=vars_updated,
            output_templates=templates,
            layer_structure=layer_structure,
        )

    assert caught_warnings == []
    assert np.isnan(outputs["air_temperature"].to_numpy()[:, 1:]).all()
    assert np.isnan(outputs["soil_temperature"].to_numpy()[:, 1:]).all()
    assert np.isnan(outputs["diurnal_temperature_range"].to_numpy()[:, 1:]).all()
    np.testing.assert_allclose(outputs["diurnal_temperature_range"][:, 0], 5.0)


def test_unrequested_variable_skipped(fixture_core_components):
    """Test unrequested variable skipped in update."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    layer_structure = fixture_core_components.layer_structure
    static = {}
    data_record = {
        "temperature": np.random.rand(24, 4),
        "humidity": np.random.rand(24, 4),
    }
    vars_updated = ("temperature",)
    output_templates = create_output_templates(
        variable_data={"temperature": DataArray(np.empty(4), dims=("cell_id",))},
        vars_updated=vars_updated,
        layer_structure=layer_structure,
        time_dim=24,
    )

    output = build_output_from_record(
        data_record,
        static,
        vars_updated,
        output_templates,
        layer_structure,
    )

    assert "temperature" in output
    assert "humidity" not in output


def test_missing_requested_variable_raises(fixture_core_components):
    """Test missing variables raised in update."""

    from virtual_ecosystem.models.abiotic.microclimate import build_output_from_record

    static = {}
    data_record = {}
    vars_updated = ("temperature",)

    with pytest.raises(ValueError):
        build_output_from_record(
            data_record,
            static,
            vars_updated,
            {},
            fixture_core_components.layer_structure,
        )


def test_run_microclimate(
    dummy_climate_data,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Full integration test microclimate."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import create_output_templates
    from virtual_ecosystem.models.abiotic.microclimate import run_microclimate

    data = dummy_climate_data
    vars_updated = (
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "relative_humidity",
        "wind_speed",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "density_air",
        "specific_heat_air",
        "latent_heat_vapourisation",
        "aerodynamic_resistance_canopy",
        "longwave_emission",
        "atmospheric_pressure",
        "atmospheric_co2",
        "net_radiation",
        "diurnal_temperature_range",
        "condensation",
        "air_temperature_hourly",
        "soil_temperature_hourly",
        "net_radiation_hourly",
    )
    time_interval = 3600
    time_index = 0
    time_dim = 24
    month = 1
    days = 30
    latitude = 0
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    pyrealm_core_constants = PyrealmCoreConst()
    abiotic_bounds = AbioticSimpleBounds()
    output_templates = create_output_templates(
        variable_data={
            name: data[name] for name in vars_updated if not name.endswith("_hourly")
        },
        vars_updated=vars_updated,
        layer_structure=fixture_core_components.layer_structure,
        time_dim=time_dim,
    )

    result = run_microclimate(
        data=data,
        vars_updated=vars_updated,
        time_index=time_index,
        time_dim=time_dim,
        time_interval=time_interval,
        month=month,
        days=days,
        latitude=latitude,
        layer_structure=fixture_core_components.layer_structure,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        abiotic_bounds=abiotic_bounds,
        pyrealm_core_constants=pyrealm_core_constants,
        output_templates=output_templates,
    )

    assert set(result) == set(vars_updated)
    for var in vars_updated:
        if var.endswith("_hourly"):
            source_name = var.removesuffix("_hourly")
            assert result[var].shape == (time_dim, *data[source_name].shape)
        else:
            assert result[var].shape == data[var].shape

    for name, source_name in (
        ("air_temperature_hourly", "air_temperature"),
        ("soil_temperature_hourly", "soil_temperature"),
        ("net_radiation_hourly", "net_radiation"),
    ):
        hourly = result[name]
        assert hourly.dims[0] == "hour"
        np.testing.assert_array_equal(hourly["hour"], np.arange(time_dim))
        np.testing.assert_allclose(
            hourly.mean(dim="hour"),
            result[source_name],
            equal_nan=True,
        )

    for var in ["air_temperature", "relative_humidity"]:
        assert np.all(result[var] != data[var])
