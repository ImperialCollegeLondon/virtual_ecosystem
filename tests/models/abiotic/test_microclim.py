"""Test microclim.py."""

import types
import numpy as np
import pytest


def test_build_indices_returns_expected_namespace(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test that _build_indices correctly maps attributes."""

    from virtual_ecosystem.models.abiotic.microclim import _build_indices

    layer_structure = fixture_core_components.layer_structure
    data = dummy_climate_data_varying_canopy

    idx = _build_indices(data=data, layer_structure=layer_structure)

    # Check expected keys exist
    assert isinstance(idx, types.SimpleNamespace)

    def assert_equal(a, b):
        if isinstance(a, np.ndarray):
            np.testing.assert_array_equal(a, b)
        else:
            assert a == b

    assert_equal(idx.above, layer_structure.index_above)
    assert_equal(idx.canopy, layer_structure.index_filled_canopy)
    assert_equal(idx.surface, layer_structure.index_surface_scalar)
    assert_equal(idx.atm, layer_structure.index_filled_atmosphere)
    assert_equal(idx.flux, layer_structure.index_flux_layers)
    assert_equal(idx.soil, layer_structure.index_all_soil)
    assert_equal(idx.topsoil, layer_structure.index_topsoil_scalar)
    assert_equal(idx.layers, layer_structure.n_layers)
    assert_equal(idx.cell_id, data.grid.n_cells)


def test_normal_case():
    """Test that compute_weights_from_absorbed_radiation correctly normalizes array."""
    from virtual_ecosystem.models.abiotic.microclim import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[1.0, 2.0], [3.0, 4.0]])

    weights = compute_weights_from_absorbed_radiation(radiation)

    expected = radiation / np.nansum(radiation)

    assert np.allclose(weights, expected)
    assert np.isclose(np.nansum(weights), 1.0)


def test_with_nans():
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


def test_zero_total_raises():
    """Test that compute_weights_from_absorbed_radiation raises ValueError when total is zero."""
    from virtual_ecosystem.models.abiotic.microclim import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[0.0, 0.0], [0.0, 0.0]])

    with pytest.raises(ValueError):
        compute_weights_from_absorbed_radiation(radiation)


def test_all_nan_raises():
    """Test compute_weights_from_absorbed_radiation raises Error when values are NaN."""
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
    """Test _prepare_static_inputs returns sensible and consistent outputs."""

    from virtual_ecosystem.models.abiotic.microclim import _prepare_static_inputs

    data = dummy_climate_data_varying_canopy
    layer_structure = fixture_core_components.layer_structure
    idx = fixture_abiotic_indices
    abiotic_constants = fixture_abiotic_constants

    result = _prepare_static_inputs(
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
    }

    assert set(result.keys()) == expected_keys

    # Shape checks
    n_cells = data.grid.n_cells
    n_layers = layer_structure.n_layers
    n_atm_layers = sum(idx.atm)

    assert result["canopy_height"].shape == (n_cells,)
    assert result["lai_sum"].shape == (n_cells,)
    assert result["evapotranspiration"].shape == (n_layers, n_cells)
    assert result["atmospheric_pressure"].shape == (n_atm_layers, n_cells)
    assert result["atmospheric_co2"].shape == (n_atm_layers, n_cells)

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


def test_calculate_wind_profiles_general(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_static_inputs,
    fixture_abiotic_indices,
):
    """Test wind profile calculations for physical plausibility and consistency."""

    from virtual_ecosystem.models.abiotic.microclim import _calculate_wind_profiles

    data = dummy_climate_data_varying_canopy
    static_inputs = fixture_static_inputs
    idx = fixture_abiotic_indices
    time_index = 0

    result = _calculate_wind_profiles(
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
    assert result["wind_profile"].shape == (n_atm_layers, n_cells)
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
    assert np.all(result["wind_profile"] >= 0)

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
    top_layer_wind = result["wind_profile"][0]

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
        wind_above = result["wind_profile"][above_canopy]
        assert np.all(np.diff(wind_above, axis=0) >= -1e-6)


def test_generate_hourly_forcing(
    dummy_climate_data_varying_canopy,
    fixture_static_inputs,
    fixture_core_components,
):
    """Test _generate_hourly_forcing with prepared static inputs."""

    from virtual_ecosystem.models.abiotic.microclim import _generate_hourly_forcing

    data = dummy_climate_data_varying_canopy
    static_inputs = fixture_static_inputs
    time_index = 0
    month = 2
    latitude = 0.0

    forcing = _generate_hourly_forcing(
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


def test_initialize_state_shapes(
    dummy_climate_data_varying_canopy, fixture_abiotic_indices
):
    """Test _initialize_state returns all expected state variables."""

    from virtual_ecosystem.models.abiotic.microclim import _initialize_state

    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices

    state = _initialize_state(data=data, idx=idx, time_index=0)

    # Expected keys
    expected_keys = [
        "all_air_temperature",
        "canopy_air_temperature",
        "surface_air_temperature",
        "canopy_temperature",
        "understorey_temperature",
        "soil_temperature",
        "relative_humidity",
    ]
    assert set(state.keys()) == set(expected_keys)

    # Check shapes match original slices
    assert state["all_air_temperature"].shape == data["air_temperature"][idx.atm].shape
    assert (
        state["canopy_air_temperature"].shape
        == data["air_temperature"][idx.canopy].shape
    )
    assert (
        state["surface_air_temperature"].shape
        == data["air_temperature"][idx.surface].shape
    )
    assert (
        state["canopy_temperature"].shape
        == data["canopy_temperature"][idx.canopy].shape
    )
    assert (
        state["understorey_temperature"].shape
        == data["canopy_temperature"][idx.surface].shape
    )
    assert state["soil_temperature"].shape == data["soil_temperature"][idx.soil].shape
    assert state["relative_humidity"].shape == data["relative_humidity"][idx.atm].shape


def test_initialize_hourly_record(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test _initialize_hourly_record creates arrays of correct shape and type."""

    from virtual_ecosystem.models.abiotic.microclim import _initialize_hourly_record

    data = dummy_climate_data_varying_canopy
    layer_structure = fixture_core_components.layer_structure

    # Variables we want to track
    vars_updated = ("air_temperature", "soil_moisture")

    # Initialize hourly record for 24 hours
    hourly_record = _initialize_hourly_record(
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
        _update_forcing_boundary_conditions,
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
        "all_air_temperature": np.zeros((n_layers, n_cells)),
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

    expected_sw_canopy = hourly_forcing["shortwave_absorption_hourly"][
        hour, idx.canopy, :
    ]
    expected_sw_surface = hourly_forcing["shortwave_absorption_hourly"][
        hour, idx.surface, :
    ]
    expected_sw_soil = hourly_forcing["shortwave_absorption_hourly"][
        hour, idx.topsoil, :
    ]

    expected_et_canopy = hourly_forcing["evapotranspiration_hourly"][
        hour, idx.canopy, :
    ]
    expected_et_surface = hourly_forcing["evapotranspiration_hourly"][
        hour, idx.surface, :
    ]
    expected_soil_evap = hourly_forcing["soil_evaporation_hourly"][hour]

    # Call function
    updated_state = _update_forcing_boundary_conditions(
        state=state,
        hourly_forcing=hourly_forcing,
        hour=hour,
        idx=idx,
    )

    # Check in-place update
    assert updated_state is state

    # Check boundary replacement (layer 0)
    np.testing.assert_allclose(state["all_air_temperature"][0], expected_air)
    np.testing.assert_allclose(state["relative_humidity"][0], expected_rh)

    # Check shortwave slices
    np.testing.assert_allclose(state["shortwave_absorption_canopy"], expected_sw_canopy)
    np.testing.assert_allclose(
        state["shortwave_absorption_understorey"], expected_sw_surface
    )
    np.testing.assert_allclose(state["shortwave_absorption_soil"], expected_sw_soil)

    # Check evapotranspiration slices
    np.testing.assert_allclose(state["evapotranspiration_canopy"], expected_et_canopy)
    np.testing.assert_allclose(
        state["evapotranspiration_understorey"], expected_et_surface
    )
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
        _calculate_thermodynamics,
    )

    data = dummy_climate_data_varying_canopy
    static = fixture_static_inputs
    idx = fixture_abiotic_indices
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    n_cells = data.grid.n_cells
    n_layers = sum(idx.atm)
    hour = 0

    # Dummy state inputs
    state = {
        "all_air_temperature": data["air_temperature"][idx.atm].to_numpy(),
        "atmospheric_pressure": data["atmospheric_pressure"][idx.atm].to_numpy(),
    }

    wind_state = {
        "zero_plane_displacement": np.ones(n_cells) * 2.0,
    }

    static = {
        "canopy_height": data["layer_heights"][0].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
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
    result_day = _calculate_thermodynamics(
        state=state,
        wind_state=wind_state,
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
        static["aerodynamic_resistance_soil"],
    )

    # NIGHT TEST
    result_night = _calculate_thermodynamics(
        state=state,
        wind_state=wind_state,
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
    fixture_abiotic_indices,
):

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_vegetation_temperature,
    )

    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices
    evapotranspiration = (
        data["canopy_evaporation"].to_numpy() + data["transpiration"].to_numpy()
    )
    state = {
        "canopy_temperature": data["canopy_temperature"][idx.canopy].to_numpy(),
        "understorey_temperature": data["canopy_temperature"][idx.surface].to_numpy(),
        "canopy_air_temperature": data["air_temperature"][idx.canopy].to_numpy(),
        "surface_air_temperature": data["air_temperature"][idx.surface].to_numpy(),
        "evapotranspiration_canopy": evapotranspiration[idx.canopy, :],
        "evapotranspiration_understorey": evapotranspiration[idx.surface, :],
        "shortwave_absorption_canopy": data["shortwave_absorption"].to_numpy()[
            idx.canopy, :
        ],
        "shortwave_absorption_understorey": data["shortwave_absorption"].to_numpy()[
            idx.surface, :
        ],
    }

    thermodynamics = {
        "specific_heat_air": data["specific_heat_air"][idx.atm].to_numpy(),
        "density_air": data["density_air"][idx.atm].to_numpy(),
        "aerodynamic_resistance_canopy": data[
            "aerodynamic_resistance_canopy"
        ].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"][
            idx.atm
        ].to_numpy(),
    }

    static = {"absorbed_longwave_radiation": np.ones((14, 4))}

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    result = calculate_vegetation_temperature(
        state=state,
        thermodynamics=thermodynamics,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    assert isinstance(result, np.ndarray)
    assert result.shape == (4, 4)

    # Mask where input is not NaN
    mask = ~np.isnan(
        np.concatenate(
            [
                data["canopy_temperature"][idx.canopy],
                [data["canopy_temperature"][idx.surface]],
            ],
            axis=0,
        )
    )
    print(mask)
    # Assert plausible range for non-NaN input
    assert np.all((result[mask] > 0) & (result[mask] < 50))

    # Assert NaNs are preserved
    assert np.all(np.isnan(result[~mask]))


def test_calculate_vegetation_fluxes(
    fixture_abiotic_constants,
    fixture_core_constants,
    dummy_climate_data_varying_canopy,
    fixture_abiotic_indices,
):

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_vegetation_fluxes,
    )

    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices
    evapotranspiration = (
        data["canopy_evaporation"].to_numpy() + data["transpiration"].to_numpy()
    )
    state = {
        "canopy_temperature": data["canopy_temperature"][idx.canopy].to_numpy(),
        "understorey_temperature": data["canopy_temperature"][idx.surface].to_numpy(),
        "canopy_air_temperature": data["air_temperature"][idx.canopy].to_numpy(),
        "surface_air_temperature": data["air_temperature"][idx.surface].to_numpy(),
        "evapotranspiration_canopy": evapotranspiration[idx.canopy, :],
        "evapotranspiration_understorey": evapotranspiration[idx.surface, :],
        "shortwave_absorption_canopy": data["shortwave_absorption"].to_numpy()[
            idx.canopy, :
        ],
        "shortwave_absorption_understorey": data["shortwave_absorption"].to_numpy()[
            idx.surface, :
        ],
    }

    thermodynamics = {
        "specific_heat_air": data["specific_heat_air"][idx.atm].to_numpy(),
        "density_air": data["density_air"][idx.atm].to_numpy(),
        "aerodynamic_resistance_canopy": data[
            "aerodynamic_resistance_canopy"
        ].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"][
            idx.atm
        ].to_numpy(),
    }

    static = {"absorbed_longwave_radiation": np.ones((14, 4))}

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    result = calculate_vegetation_fluxes(
        state=state,
        thermodynamics=thermodynamics,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )
    print(result)
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
        assert result[key].shape == (4, 4)


def test_calculate_soil_fluxes(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_abiotic_indices,
):

    from virtual_ecosystem.models.abiotic.microclim import (
        calculate_soil_fluxes,
    )

    data = dummy_climate_data_varying_canopy
    state = {
        "soil_temperature": data["soil_temperature"][
            fixture_abiotic_indices.soil
        ].to_numpy(),
        "surface_air_temperature": data["air_temperature"][
            fixture_abiotic_indices.surface
        ].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
        "soil_evaporation": data["soil_evaporation"].to_numpy(),
        "absorbed_shortwave_radiation_soil": data["shortwave_absorption"].to_numpy()[
            fixture_abiotic_indices.topsoil, :
        ],
    }

    static = {"absorbed_longwave_radiation": np.ones((14, 4))}

    thermodynamics = {
        "density_air": data["density_air"][fixture_abiotic_indices.atm].to_numpy(),
        "specific_heat_air": data["specific_heat_air"][
            fixture_abiotic_indices.atm
        ].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"][
            fixture_abiotic_indices.atm
        ].to_numpy(),
    }

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    idx = fixture_abiotic_indices

    time_interval = 3600

    result = calculate_soil_fluxes(
        state=state,
        static=static,
        thermodynamics=thermodynamics,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        time_interval=time_interval,
        idx=idx,
    )

    expected_ground_flux = np.array([211.142581, 204.359248, 190.792581, 190.792581])

    np.testing.assert_allclose(
        result["ground_heat_flux_soil"], expected_ground_flux, rtol=1e-5, atol=1e-5
    )

    # Ensure all keys exist
    assert set(result.keys()) == {
        "longwave_emission_soil",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "ground_heat_flux_soil",
    }


def test_update_air_temperature(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_indices,
    fixture_abiotic_simple_configuration,
):
    """Integration-style test for update_air_temperature."""

    from virtual_ecosystem.models.abiotic.microclim import update_air_temperature

    data = dummy_climate_data_varying_canopy
    idx = fixture_abiotic_indices

    n_layers = 4
    n_cells = 4

    # Build state arrays
    state = {
        "canopy_air_temperature": data["air_temperature"][idx.canopy].to_numpy(),
        "surface_air_temperature": data["air_temperature"][idx.surface].to_numpy(),
        "all_air_temperature": data["air_temperature"][idx.atm].to_numpy(),
    }

    # Build fluxes
    vegetation_fluxes = {"sensible_heat_flux": np.ones((n_layers, n_cells)) * 5.0}
    soil_fluxes = {"sensible_heat_flux": np.ones(n_cells) * 2.0}

    # Build thermodynamics arrays
    thermodynamics = {
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
    }

    # Static geometry
    static = {
        "geometry": {"thickness": np.ones((5, n_cells))},
        "mixing_coefficient": np.full((5, n_cells), 0.1),
    }

    # Wind profile
    wind_state = {"ventilation_rate": 0.05}

    # Time interval
    time_interval = 3600

    # Abiotic bounds
    abiotic_bounds = fixture_abiotic_simple_configuration.bounds

    result = update_air_temperature(
        state=state,
        vegetation_fluxes=vegetation_fluxes,
        soil_fluxes=soil_fluxes,
        static=static,
        thermodynamics=thermodynamics,
        wind_state=wind_state,
        abiotic_bounds=abiotic_bounds,
        idx=idx,
        time_interval=time_interval,
    )

    assert isinstance(result, np.ndarray)
    assert result.shape == state["all_air_temperature"].shape

    # Canopy layer should be updated (not equal to initial)
    canopy_slice = result[1 : 1 + state["canopy_air_temperature"].shape[0]]
    np.testing.assert_array_less(state["canopy_air_temperature"], canopy_slice + 1e-6)

    # Surface layer should be updated
    np.testing.assert_array_less(state["surface_air_temperature"], result[-1] + 1e-6)

    # Check values are within bounds
    lower, upper = abiotic_bounds.air_temperature[:2]
    mask = ~np.isnan(data["air_temperature"][idx.atm])
    assert np.all(result[mask] >= lower)
    assert np.all(result[mask] <= upper)
