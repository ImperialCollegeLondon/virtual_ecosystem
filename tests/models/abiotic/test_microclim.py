"""Test microclim.py."""

import types

import numpy as np
import pytest
from pyrealm.constants import CoreConst as PyrealmCoreConst
from xarray import DataArray

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


def test_compute_weights_normal_case():
    """Test that compute_weights_from_absorbed_radiation correctly normalizes array."""
    from virtual_ecosystem.models.abiotic.microclim import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[1.0, 2.0], [3.0, 4.0]])
    weights = compute_weights_from_absorbed_radiation(radiation)
    expected = radiation / np.nansum(radiation)

    assert np.allclose(weights, expected)
    assert np.isclose(np.nansum(weights), 1.0)


def test_compute_weights_with_nans():
    """Test that compute_weights_from_absorbed_radiation correctly handles NaNs."""
    from virtual_ecosystem.models.abiotic.microclim import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[1.0, np.nan], [3.0, 6.0]])
    weights = compute_weights_from_absorbed_radiation(radiation)

    # NaN remains NaN
    assert np.isnan(weights[0, 1])

    # Valid values still normalize to 1
    assert np.isclose(np.nansum(weights), 1.0)


def test_compute_weights_zero_total_raises():
    """Test that compute_weights_from_absorbed_radiation raises ValueError."""
    from virtual_ecosystem.models.abiotic.microclim import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[0.0, 0.0], [0.0, 0.0]])

    with pytest.raises(ValueError):
        compute_weights_from_absorbed_radiation(radiation)


def test_all_nan_raises():
    """Test that compute_weights_from_absorbed_radiation raises Error when NaN."""
    from virtual_ecosystem.models.abiotic.microclim import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[np.nan, np.nan], [np.nan, np.nan]])

    with pytest.raises(ValueError):
        compute_weights_from_absorbed_radiation(radiation)


def test_prepare_static_inputs_returns_consistent_outputs(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_indices,
    fixture_abiotic_constants,
):
    """Test prepare_static_inputs returns sensible and consistent outputs."""

    from virtual_ecosystem.models.abiotic.microclim import prepare_static_inputs

    data = dummy_climate_data_varying_canopy
    layer_structure = fixture_core_components.layer_structure
    idx = fixture_abiotic_indices
    abiotic_constants = fixture_abiotic_constants

    result = prepare_static_inputs(
        data=data,
        idx=idx,
        time_index=0,
        layer_structure=layer_structure,
        abiotic_constants=abiotic_constants,
    )

    # Check expected keys exist
    expected_keys = {
        "canopy_height",
        "lai_sum",
        "evapotranspiration",
        "atmospheric_pressure",
        "atmospheric_co2",
        "geometry",
        "absorbed_longwave_radiation",
        "cell_area",
    }

    assert set(result.keys()) == expected_keys

    # Shape checks
    n_cells = data.grid.n_cells
    n_layers = layer_structure.n_layers

    assert result["canopy_height"].shape == (n_cells,)
    assert result["lai_sum"].shape == (n_cells,)
    assert result["evapotranspiration"].shape == (n_layers, n_cells)
    assert result["atmospheric_pressure"].shape == (n_layers, n_cells)
    assert result["atmospheric_co2"].shape == (n_layers, n_cells)

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

    # No unexpected infinities
    for key, value in result.items():
        if isinstance(value, dict):
            continue
        arr = np.asarray(value)
        assert not np.any(np.isinf(arr))


def test_calculate_wind_profiles(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_static_inputs,
    fixture_abiotic_indices,
):
    """Test wind profile calculations for physical plausibility and consistency."""

    from virtual_ecosystem.models.abiotic.microclim import calculate_wind_profiles

    data = dummy_climate_data_varying_canopy
    static_inputs = fixture_static_inputs
    idx = fixture_abiotic_indices
    time_index = 0

    result = calculate_wind_profiles(
        static=static_inputs,
        data=data,
        time_index=time_index,
        abiotic_constants=fixture_abiotic_constants,
        core_constants=fixture_core_constants,
    )

    # Shape checks
    n_cells = data.grid.n_cells
    n_atm_layers = sum(idx.atm)

    assert result["zero_plane_displacement"].shape == (n_cells,)
    assert result["roughness_length"].shape == (n_cells,)
    assert result["friction_velocity"].shape == (n_cells,)
    assert result["wind_speed"].shape == (n_atm_layers, n_cells)
    assert result["mixing_coefficient"].shape == (n_atm_layers, n_cells)

    # No unexpected NaNs
    for key, arr in result.items():
        assert not np.all(np.isnan(arr)), f"{key} is entirely NaN"

    # Physical bounds
    # Roughness length must be positive
    assert np.all(result["roughness_length"] > 0)

    # Friction velocity must be >= 0
    assert np.all(result["friction_velocity"] >= 0)

    # Wind speeds should be >= minimum windspeed
    assert np.all(result["wind_speed"] >= 0)

    # Mixing coefficient must be >= 0
    assert np.all(result["mixing_coefficient"] >= 0)

    # Physical relationships
    # Zero plane displacement should be less than canopy height
    assert np.all(result["zero_plane_displacement"] <= static_inputs["canopy_height"])

    # Wind speed at reference height should match input reference
    ref_wind = (
        dummy_climate_data_varying_canopy["wind_speed_ref"]
        .isel(time_index=time_index)
        .to_numpy()
    )
    top_layer_wind = result["wind_speed"][0]

    assert np.allclose(
        top_layer_wind,
        ref_wind,
        rtol=0.3,
    )

    # Monotonic wind increase above canopy
    canopy_height = static_inputs["canopy_height"]
    heights = static_inputs["geometry"]["heights"]

    above_canopy = heights > canopy_height.max()

    if np.any(above_canopy):
        wind_above = result["wind_speed"][above_canopy]
        assert np.all(np.diff(wind_above, axis=0) >= -1e-6)


def test_generate_hourly_forcing(
    dummy_climate_data_varying_canopy,
    fixture_static_inputs,
    fixture_core_components,
):
    """Test generate_hourly_forcing with prepared static inputs."""

    from virtual_ecosystem.models.abiotic.microclim import generate_hourly_forcing

    data = dummy_climate_data_varying_canopy
    static_inputs = fixture_static_inputs
    time_index = 0
    month = 2
    latitude = 0.0

    forcing = generate_hourly_forcing(
        data=data,
        static=static_inputs,
        time_index=time_index,
        month=month,
        latitude=latitude,
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
    air_temp_monthly = (
        data["air_temperature_ref"].isel(time_index=time_index).to_numpy()
    )
    daily_amp = 5.0
    assert np.all(air_temp >= air_temp_monthly - daily_amp - 1e-6)
    assert np.all(air_temp <= air_temp_monthly + daily_amp + 1e-6)

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
    monthly_sum_sw_abs = np.nansum(forcing["shortwave_absorption_hourly"], axis=0)
    monthly_sum_soil_evap = np.nansum(forcing["soil_evaporation_hourly"], axis=0) * 30

    assert np.allclose(
        monthly_sum_et[mask], static_inputs["evapotranspiration"][mask], rtol=1e-5
    )
    assert np.allclose(
        monthly_sum_sw_abs[mask],
        data["shortwave_absorption"].to_numpy()[mask],
        rtol=1e-5,
    )
    assert np.allclose(
        monthly_sum_soil_evap,
        data["soil_evaporation"].to_numpy(),
        rtol=1e-5,
    )


def test_initialize_state_shapes(dummy_climate_data_varying_canopy):
    """Test initialize_state returns all expected state variables."""

    from virtual_ecosystem.models.abiotic.microclim import initialize_state

    data = dummy_climate_data_varying_canopy
    state = initialize_state(data=data)

    # Expected keys
    expected_keys = [
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
        "relative_humidity",
        "aerodynamic_resistance_soil",
    ]
    assert set(state.keys()) == set(expected_keys)

    # # Check shapes match original slices
    # assert state["air_temperature"].shape == data["air_temperature"][idx.atm].shape
    # assert (
    #     state["canopy_air_temperature"].shape
    #     == data["air_temperature"][idx.canopy].shape
    # )
    # assert (
    #     state["surface_air_temperature"].shape
    #     == data["air_temperature"][idx.surface].shape
    # )
    # assert (
    #     state["canopy_temperature"].shape
    #     == data["canopy_temperature"][idx.canopy].shape
    # )
    # assert (
    #     state["understorey_temperature"].shape
    #     == data["canopy_temperature"][idx.surface].shape
    # )
    # assert state["soil_temperature"].shape == data["soil_temperature"][idx.soil].shape
    # assert state["relative_humidity"].shape == data["relative_humidity"][idx.atm].shape


def test_initialize_hourly_record(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test _initialize_hourly_record creates arrays of correct shape and type."""

    from virtual_ecosystem.models.abiotic.microclim import initialize_hourly_record

    data = dummy_climate_data_varying_canopy
    layer_structure = fixture_core_components.layer_structure

    # Variables we want to track
    vars_updated = ("air_temperature", "soil_moisture")

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
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test update forcingcorrectly updates state with hourly forcing."""

    from virtual_ecosystem.models.abiotic.microclim import (
        update_forcing_boundary_conditions,
    )

    # Dimensions
    time_dim = 24
    n_cells = dummy_climate_data_varying_canopy.grid.n_cells
    n_layers = fixture_core_components.layer_structure.n_layers
    hour = 1

    # Layer index structure
    idx = types.SimpleNamespace(
        canopy=np.array([1, 2]),
        surface=np.array([3]),
        topsoil=np.array([4]),
    )

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
        idx=idx,
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
    dummy_climate_data_varying_canopy,
    fixture_static_inputs,
    fixture_abiotic_indices,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test _calculate_thermodynamics produces expected outputs for day and night."""

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_thermodynamics,
    )

    data = dummy_climate_data_varying_canopy
    static = fixture_static_inputs
    idx = fixture_abiotic_indices
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    n_cells = data.grid.n_cells
    n_layers = 14
    hour = 0

    state = {
        "air_temperature": data["air_temperature"].to_numpy(),
        "atmospheric_pressure": data["atmospheric_pressure"].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
        "zero_plane_displacement": np.ones(n_cells) * 2.0,
    }

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
    )

    assert isinstance(result_day, dict)
    assert result_day["aerodynamic_resistance_canopy"].shape == (n_cells,)
    assert np.all(result_day["aerodynamic_resistance_canopy"] == 50.0)
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
    )

    assert np.all(result_night["aerodynamic_resistance_canopy"] == 250.0)
    assert np.all(result_night["aerodynamic_resistance_soil"] == 150.0)

    # Output shape checks
    assert result_day["density_air"].shape == (n_layers, n_cells)
    assert result_day["specific_heat_air"].shape == (n_layers, n_cells)
    assert result_day["latent_heat_vapourisation"].shape == (n_layers, n_cells)
    assert result_day["ventilation_rate"].shape == (n_cells,)


def test_calculate_vegetation_temperature(
    fixture_abiotic_constants,
    fixture_core_constants,
    dummy_climate_data_varying_canopy,
    fixture_static_inputs,
):
    """Test calculate_vegetation_temperature produces expected outputs."""

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_vegetation_temperature,
    )

    data = dummy_climate_data_varying_canopy
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    static = fixture_static_inputs

    evapotranspiration = (
        data["canopy_evaporation"].to_numpy() + data["transpiration"].to_numpy()
    )
    state = {
        "canopy_temperature": data["canopy_temperature"].to_numpy(),
        "air_temperature": data["air_temperature"].to_numpy(),
        "evapotranspiration": evapotranspiration,
        "shortwave_absorption": data["shortwave_absorption"].to_numpy(),
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "aerodynamic_resistance_canopy": data[
            "aerodynamic_resistance_canopy"
        ].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"].to_numpy(),
    }

    result = calculate_vegetation_temperature(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    # Shape checks
    assert isinstance(result, np.ndarray)
    assert result.shape == (14, 4)

    # Mask where input is not NaN
    mask = ~np.isnan(data["air_temperature"])

    # Assert plausible range for non-NaN input
    assert np.all((result[mask] > 0) & (result[mask] < 50))

    # Assert NaNs are preserved
    assert np.all(np.isnan(result[~mask]))


def test_calculate_vegetation_fluxes(
    fixture_abiotic_constants,
    fixture_core_constants,
    dummy_climate_data_varying_canopy,
    fixture_static_inputs,
):
    """Test calculate_vegetation_fluxes produces expected outputs."""

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_vegetation_fluxes,
    )

    data = dummy_climate_data_varying_canopy
    static = fixture_static_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    evapotranspiration = (
        data["canopy_evaporation"].to_numpy() + data["transpiration"].to_numpy()
    )
    state = {
        "canopy_temperature": data["canopy_temperature"].to_numpy(),
        "air_temperature": data["air_temperature"].to_numpy(),
        "evapotranspiration": evapotranspiration,
        "shortwave_absorption": data["shortwave_absorption"].to_numpy(),
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "aerodynamic_resistance_canopy": data[
            "aerodynamic_resistance_canopy"
        ].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"].to_numpy(),
    }

    result = calculate_vegetation_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    # Assert all expected keys exist and have correct shapes
    assert isinstance(result, dict)
    expected_keys = {
        "longwave_emission",
        "sensible_heat_flux",
        "latent_heat_flux",
        "energy_balance_residual",
    }
    assert set(result.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (14, 4)


def test_calculate_soil_fluxes(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_abiotic_indices,
    fixture_static_inputs,
):
    """Test calculate_soil_fluxes produces expected outputs."""

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_soil_fluxes,
    )

    data = dummy_climate_data_varying_canopy
    static = fixture_static_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    idx = fixture_abiotic_indices
    time_interval = 3600

    state = {
        "soil_temperature": data["soil_temperature"].to_numpy(),
        "air_temperature": data["air_temperature"].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
        "soil_evaporation": data["soil_evaporation"].to_numpy(),
        "shortwave_absorption": data["shortwave_absorption"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"].to_numpy(),
    }

    result = calculate_soil_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        time_interval=time_interval,
        idx=idx,
    )

    # Check output keys and shapes
    expected_ground_flux = np.array([239.299606, 232.516272, 218.949606, 218.949606])

    np.testing.assert_allclose(
        result["ground_heat_flux"], expected_ground_flux, rtol=1e-5, atol=1e-5
    )

    # Ensure all keys exist
    assert set(result.keys()) == {
        "longwave_emission_soil",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "ground_heat_flux",
    }


def test_update_air_temperature(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_indices,
    fixture_abiotic_simple_configuration,
    fixture_static_inputs,
    fixture_core_components,
):
    """Integration-style test for update_air_temperature."""

    from virtual_ecosystem.models.abiotic.microclim import update_air_temperature

    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices
    static = fixture_static_inputs
    time_interval = 1
    abiotic_bounds = fixture_abiotic_simple_configuration.bounds

    n_layers = 14
    n_cells = 4

    mixing_coefficient = fixture_core_components.layer_structure.from_template()
    mixing_coefficient[idx.atm] = np.array(
        [
            [0.1, 0.1, 0.1, 0.1],
            [0.1, 0.1, 0.1, np.nan],
            [0.1, 0.1, np.nan, np.nan],
            [0.1, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )
    state = {
        "air_temperature": data["air_temperature"].to_numpy(),
        "sensible_heat_flux": np.ones((n_layers, n_cells)) * 5.0,
        "sensible_heat_flux_soil": np.ones(n_cells) * 2.0,
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "ventilation_rate": np.repeat(0.05, n_cells),
        "mixing_coefficient": mixing_coefficient,
    }

    result = update_air_temperature(
        state=state,
        static=static,
        abiotic_bounds=abiotic_bounds,
        time_interval=time_interval,
        idx=idx,
    )

    # Check output is correct shape and type
    assert isinstance(result, np.ndarray)
    assert result.shape == state["air_temperature"].shape

    # Check values are within bounds
    lower, upper = abiotic_bounds.air_temperature[:2]
    mask = ~np.isnan(data["air_temperature"])
    assert np.all(result[mask] >= lower)
    assert np.all(result[mask] <= upper)


def test_update_atmospheric_humidity(
    dummy_climate_data_varying_canopy,
    fixture_core_constants,
    fixture_abiotic_constants,
    fixture_abiotic_indices,
    fixture_static_inputs,
    fixture_core_components,
):
    """Test update atmospheric humidity."""

    from pyrealm.core.hygro import calc_vp_sat

    from virtual_ecosystem.models.abiotic.microclim import (
        update_atmospheric_humidity,
    )

    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices
    static = fixture_static_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    pyrealm_core_constants = PyrealmCoreConst()

    mixing_coefficient = fixture_core_components.layer_structure.from_template()
    mixing_coefficient[idx.atm] = np.array(
        [
            [0.1, 0.1, 0.1, 0.1],
            [0.1, 0.1, 0.1, np.nan],
            [0.1, 0.1, np.nan, np.nan],
            [0.1, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )

    state = {
        "air_temperature": data["air_temperature"].to_numpy(),
        "relative_humidity": data["relative_humidity"].to_numpy(),
        "atmospheric_pressure": data["atmospheric_pressure"].to_numpy(),
        "evapotranspiration": data["canopy_evaporation"].to_numpy()
        + data["transpiration"].to_numpy(),
        "soil_evaporation": data["soil_evaporation"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "mixing_coefficient": mixing_coefficient,
        "ventilation_rate": np.array([0.01, 0.01, 0.01, 0.01]),
    }

    vp_sat = calc_vp_sat(
        ta=state["air_temperature"],
        core_const=pyrealm_core_constants,
    )
    result = update_atmospheric_humidity(
        state=state,
        static=static,
        pyrealm_core_constants=pyrealm_core_constants,
        core_constants=core_constants,
        abiotic_constants=abiotic_constants,
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
    ]:
        assert key in result
        assert isinstance(result[key], np.ndarray)
        assert np.all(np.isnan(result[key][~mask]))

    # Expected trends: ET and mixing should raise humidity slightly where is not NaN
    assert np.all(result["specific_humidity"][mask] >= 0.00)

    # VPD should be reduced where evapotranspiration or mixing adds moisture
    assert np.all(result["vapour_pressure_deficit"][mask] >= 0.0)
    assert np.all(result["vapour_pressure"][mask] <= vp_sat[mask])

    # RH should be between 0 and 100
    assert np.all(
        (result["relative_humidity"][mask] >= 0)
        & (result["relative_humidity"][mask] <= 100)
    )


def test_run_hour_step_orchestration(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_indices,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_static_inputs,
):
    """Test hourly loop."""

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_wind_profiles,
        generate_hourly_forcing,
        initialize_state,
        run_hour_step,
    )

    # Set up
    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices
    hour = 12
    time_interval = 3600
    time_index = 0
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    pyrealm_constants = PyrealmCoreConst()
    abiotic_bounds = AbioticSimpleBounds()

    # get inputs
    state = state = initialize_state(
        data=data,
        idx=idx,
    )
    static = fixture_static_inputs
    hourly_forcing = generate_hourly_forcing(
        data=data,
        static=static,
        time_index=time_index,
        month=1,
        latitude=0,
    )
    wind = calculate_wind_profiles(
        static=static,
        data=data,
        time_index=time_index,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )
    state.update(wind)

    result = run_hour_step(
        state=state,
        static=static,
        hourly_forcing=hourly_forcing,
        hour=hour,
        idx=idx,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        pyrealm_constants=pyrealm_constants,
        abiotic_bounds=abiotic_bounds,
        time_interval=time_interval,
    )

    # Shape checks
    expected_shapes = {
        "air_temperature": (14, 4),
        "canopy_temperature": (14, 4),
        "soil_temperature": (14, 4),
        "relative_humidity": (14, 4),
        "aerodynamic_resistance_soil": (4,),
        "zero_plane_displacement": (4,),
        "roughness_length": (4,),
        "friction_velocity": (4,),
        "wind_speed": (14, 4),
        "mixing_coefficient": (14, 4),
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
        "longwave_emission_soil": (4,),
        "sensible_heat_flux_soil": (4,),
        "latent_heat_flux_soil": (4,),
        "ground_heat_flux": (4,),
        "vapour_pressure": (14, 4),
        "vapour_pressure_deficit": (14, 4),
        "specific_humidity": (14, 4),
    }

    for key, shape in expected_shapes.items():
        arr = result.get(key)
        assert arr is not None, f"{key} missing from output"
        assert arr.shape == shape, f"{key} shape mismatch: {arr.shape} != {shape}"

    # Physical sanity checks
    def finite_and_within(arr, min_val, max_val, name):
        valid = arr[~np.isnan(arr)]
        assert np.all(np.isfinite(valid)), f"{name} contains non-finite values"
        assert np.all(valid >= min_val), f"{name} below physical minimum {min_val}"
        assert np.all(valid <= max_val), f"{name} above physical maximum {max_val}"

    # Temperatures in Celsius
    for key in [
        "air_temperature",
        "canopy_air_temperature",
        "canopy_temperature",
        "surface_air_temperature",
        "understorey_temperature",
        "soil_temperature",
        "vegetation_temperature",
    ]:
        finite_and_within(result[key], -50, 60, key)

    # Relative humidity (%)
    finite_and_within(result["relative_humidity"], 0, 100, "relative_humidity")

    # Vapour pressure (kPa) and deficit
    finite_and_within(result["vapour_pressure"], 0, 10, "vapour_pressure")
    finite_and_within(
        result["vapour_pressure_deficit"], 0, 10, "vapour_pressure_deficit"
    )

    # Specific humidity (kg/kg)
    finite_and_within(result["specific_humidity"], 0, 0.05, "specific_humidity")

    # Fluxes (W/m²), rough ranges
    finite_and_within(result["longwave_emission"], 0, 5000, "longwave_emission")
    finite_and_within(result["sensible_heat_flux"], -1000, 1000, "sensible_heat_flux")
    finite_and_within(result["latent_heat_flux"], 0, 500, "latent_heat_flux")
    finite_and_within(result["ground_heat_flux"], -1000, 1000, "ground_heat_flux")

    # Mixing coefficient sanity
    finite_and_within(result["mixing_coefficient"], 0, 1e3, "mixing_coefficient")

    # Wind speed
    finite_and_within(result["wind_speed"], 0, 50, "wind_speed")

    # Aerodynamic resistances
    finite_and_within(
        result["aerodynamic_resistance_canopy"],
        0,
        1000,
        "aerodynamic_resistance_canopy",
    )
    finite_and_within(
        result["aerodynamic_resistance_soil"], 0, 1000, "aerodynamic_resistance_soil"
    )

    # Evapotranspiration (kg/m² per hour)
    finite_and_within(result["evapotranspiration"], 0, 5, "evapotranspiration")
    finite_and_within(result["soil_evaporation"], 0, 5, "soil_evaporation")


def test_build_output_from_record(
    fixture_core_components,
    fixture_abiotic_indices,
):
    """Test build output from record."""
    from virtual_ecosystem.models.abiotic.microclim import build_output_from_record

    n_time = 2
    n_layers = 14
    n_cells = 4

    layer_structure = fixture_core_components.layer_structure
    idx = fixture_abiotic_indices

    # Mock data_record
    data_record = {
        "cell_var": np.array([[1, 2, 3, 4], [5, 6, 7, 8]]),  # shape (time, cell)
        "layer_var": np.ones((n_time, n_layers, n_cells)) * 10,
    }

    state = {
        "density_air": np.array([1.2, 1.3, 1.2, 1.2]),  # per cell
    }

    static = {
        "atmospheric_pressure": np.array([101.325, 101.300, 101.325, 101.300]),
    }

    output = build_output_from_record(
        data_record=data_record,
        static=static,
        state=state,
        layer_structure=layer_structure,
        idx=idx,
    )

    # Cell variable mean
    expected_cell_mean = np.array([3.0, 4.0, 5.0, 6.0])
    np.testing.assert_allclose(
        output["cell_var"].values,
        expected_cell_mean,
    )
    assert output["cell_var"].dims == ("cell_id",)

    # Layer variable mean
    expected_layer_mean = np.ones((n_layers, n_cells)) * 10
    np.testing.assert_allclose(
        output["layer_var"].values,
        expected_layer_mean,
    )
    assert output["layer_var"].dims == ("layers", "cell_id")


def test_run_microclimate(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Full integration test microclimate."""

    from virtual_ecosystem.models.abiotic.microclim import run_microclimate

    data = dummy_climate_data_varying_canopy
    vars_updated = (
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
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
    )
    time_interval = 3600
    time_index = 0
    time_dim = 24
    month = 1
    latitude = 0
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    pyrealm_constants = PyrealmCoreConst()
    abiotic_bounds = AbioticSimpleBounds()

    result = run_microclimate(
        data=data,
        vars_updated=vars_updated,
        time_index=time_index,
        time_dim=time_dim,
        time_interval=time_interval,
        month=month,
        latitude=latitude,
        layer_structure=fixture_core_components.layer_structure,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        abiotic_bounds=abiotic_bounds,
        pyrealm_constants=pyrealm_constants,
    )

    for var in vars_updated:
        assert var in result

    def get_values(arr):
        """Return numpy array regardless of DataArray or ndarray."""
        return arr.values if hasattr(arr, "values") else arr

    # ------------------------------------------------------------
    # 1️⃣ Ensure no infinities anywhere
    # ------------------------------------------------------------
    for key, arr in result.items():
        vals = get_values(arr)
        valid = vals[~np.isnan(vals)]
        assert np.all(np.isfinite(valid)), f"{key} contains inf values"

    # ------------------------------------------------------------
    # 2️⃣ Atmospheric pressure (kPa)
    # Expected: ~90–105 kPa near surface
    # ------------------------------------------------------------
    pressure = get_values(result["atmospheric_pressure"])
    valid = pressure[~np.isnan(pressure)]
    assert np.all(valid > 80)
    assert np.all(valid < 110)

    # ------------------------------------------------------------
    # 3️⃣ CO2 (ppm)
    # ------------------------------------------------------------
    co2 = get_values(result["atmospheric_co2"])
    valid = co2[~np.isnan(co2)]
    assert np.all(valid > 300)
    assert np.all(valid < 500)

    # ------------------------------------------------------------
    # 4️⃣ Air temperature (°C)
    # ------------------------------------------------------------
    air_temp = get_values(result["air_temperature"])
    valid = air_temp[~np.isnan(air_temp)]
    assert np.all(valid > -50)
    assert np.all(valid < 60)

    # ------------------------------------------------------------
    # 5️⃣ Relative humidity (%)
    # ------------------------------------------------------------
    rh = get_values(result["relative_humidity"])
    valid = rh[~np.isnan(rh)]
    assert np.all(valid >= 0)
    assert np.all(valid <= 100)

    # ------------------------------------------------------------
    # 6️⃣ Vapour pressure deficit (kPa)
    # ------------------------------------------------------------
    vpd = get_values(result["vapour_pressure_deficit"])
    valid = vpd[~np.isnan(vpd)]
    assert np.all(valid >= 0)
    assert np.all(valid < 10)

    # ------------------------------------------------------------
    # 7️⃣ Air density (kg m-3)
    # Typical ~1.0–1.3
    # ------------------------------------------------------------
    rho = get_values(result["density_air"])
    valid = rho[~np.isnan(rho)]
    assert np.all(valid > 0.8)
    assert np.all(valid < 1.5)

    # ------------------------------------------------------------
    # 8️⃣ Specific heat air (J kg-1 K-1)
    # ------------------------------------------------------------
    cp = get_values(result["specific_heat_air"])
    valid = cp[~np.isnan(cp)]
    assert np.all(valid > 900)
    assert np.all(valid < 1100)

    # ------------------------------------------------------------
    # 9️⃣ Wind speed (m/s)
    # ------------------------------------------------------------
    wind = get_values(result["wind_speed"])
    valid = wind[~np.isnan(wind)]
    assert np.all(valid >= 0)
    assert np.all(valid < 50)

    # ------------------------------------------------------------
    # 🔟 Latent heat of vaporisation (J/kg)
    # ------------------------------------------------------------
    lv = get_values(result["latent_heat_vapourisation"])
    valid = lv[~np.isnan(lv)]
    assert np.all(valid > 2.3e6)
    assert np.all(valid < 2.6e6)

    # ------------------------------------------------------------
    # 1️⃣1️⃣ Soil temperature (°C)
    # ------------------------------------------------------------
    soil = get_values(result["soil_temperature"])
    valid = soil[~np.isnan(soil)]
    assert np.all(valid > -20)
    assert np.all(valid < 60)

    # ------------------------------------------------------------
    # 1️⃣2️⃣ Radiative longwave emission (W m-2)
    # Typical canopy: 300–600
    # ------------------------------------------------------------
    lw = get_values(result["longwave_emission"])
    valid = lw[~np.isnan(lw)]
    assert np.all(valid >= 0)
    assert np.all(valid < 1000)

    # ------------------------------------------------------------
    # 1️⃣3️⃣ Sensible heat flux (W m-2)
    # Can be negative
    # ------------------------------------------------------------
    sh = get_values(result["sensible_heat_flux"])
    valid = sh[~np.isnan(sh)]
    assert np.all(valid > -500)
    assert np.all(valid < 1000)

    # ------------------------------------------------------------
    # 1️⃣4️⃣ Latent heat flux (W m-2)
    # ------------------------------------------------------------
    lh = get_values(result["latent_heat_flux"])
    valid = lh[~np.isnan(lh)]
    assert np.all(valid >= 0)
    assert np.all(valid < 1000)

    # ------------------------------------------------------------
    # 1️⃣5️⃣ Canopy temperature (°C)
    # ------------------------------------------------------------
    canopy = get_values(result["canopy_temperature"])
    valid = canopy[~np.isnan(canopy)]
    assert np.all(valid > -30)
    assert np.all(valid < 60)

    # ------------------------------------------------------------
    # 1️⃣6️⃣ Ground heat flux (W m-2)
    # ------------------------------------------------------------
    ghf = get_values(result["ground_heat_flux"])
    valid = ghf[~np.isnan(ghf)]
    assert np.all(valid > -500)
    assert np.all(valid < 500)

    # ------------------------------------------------------------
    # 1️⃣7️⃣ Aerodynamic resistance (s m-1)
    # ------------------------------------------------------------
    ra = get_values(result["aerodynamic_resistance_canopy"])
    valid = ra[~np.isnan(ra)]
    assert np.all(valid > 0)
    assert np.all(valid < 1000)

    # ------------------------------------------------------------
    # 1️⃣8️⃣ Check NaN mask consistency
    # Atmospheric variables should share mask pattern
    # ------------------------------------------------------------
    atm_vars = [
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "density_air",
        "specific_heat_air",
        "wind_speed",
    ]

    masks = [np.isnan(get_values(result[var])) for var in atm_vars]

    # All atmospheric masks should match
    for m in masks[1:]:
        assert np.array_equal(masks[0], m), (
            "Atmospheric variables have inconsistent NaN masks"
        )
