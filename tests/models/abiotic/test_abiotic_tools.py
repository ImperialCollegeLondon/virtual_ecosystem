"""Test abiotic_tools.py."""

from types import SimpleNamespace

import numpy as np
import pytest
from xarray import DataArray


def test_compute_weights_with_nans():
    """Test that compute_weights_from_absorbed_radiation correctly handles NaNs."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        compute_weights_from_absorbed_radiation,
    )

    radiation = np.array([[1.0, np.nan], [3.0, 6.0]])
    weights = compute_weights_from_absorbed_radiation(radiation)

    # NaN input remains NaN in output
    assert np.isnan(weights[0, 1])

    # Per-cell weights sum to 1.0, ignoring NaNs
    per_cell_sums = np.nansum(weights, axis=0)
    assert np.allclose(per_cell_sums, 1.0)

    # Exact values for cell 0
    assert np.isclose(weights[0, 0], 0.25)
    assert np.isclose(weights[1, 0], 0.75)

    # Exact values for cell 1, only one valid entry so weight must be 1.0
    assert np.isclose(weights[1, 1], 1.0)


def test_build_indices_returns_expected_namespace(
    dummy_climate_data, fixture_core_components
):
    """Test that _build_indices correctly maps attributes."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import build_indices

    layer_structure = fixture_core_components.layer_structure
    data = dummy_climate_data

    idx = build_indices(data=data, layer_structure=layer_structure)

    # Check expected keys exist
    assert isinstance(idx, SimpleNamespace)

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


def test_calculate_molar_density_air(
    dummy_climate_data, fixture_core_components, fixture_core_constants
):
    """Test calculate temperature-dependent molar desity of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_molar_density_air,
    )

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_molar_density_air(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        standard_mole=fixture_core_constants.standard_mole,
        standard_pressure=fixture_core_constants.standard_pressure,
        celsius_to_kelvin=fixture_core_constants.zero_Celsius,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 35.0)
    assert np.all(result[valid] < 45.0)


def test_calculate_air_density(
    dummy_climate_data, fixture_core_components, fixture_core_constants
):
    """Test calculate the density of air."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import calculate_air_density

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_air_density(
        air_temperature=data["air_temperature"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        specific_gas_constant_dry_air=fixture_core_constants.specific_gas_constant_dry_air,
        celsius_to_kelvin=fixture_core_constants.zero_Celsius,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 0.8)
    assert np.all(result[valid] < 1.4)


def test_calculate_latent_heat_vapourisation(
    dummy_climate_data,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test calculation of latent heat of vapourization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_latent_heat_vapourisation,
    )

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere
    constants = fixture_abiotic_constants

    result = calculate_latent_heat_vapourisation(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        celsius_to_kelvin=fixture_core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=constants.latent_heat_vap_equ_factors,
    )
    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 2400.0)
    assert np.all(result[valid] < 2500.0)


@pytest.mark.parametrize(
    "input_array, expected",
    [
        (np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]), np.array([4.0, 5.0, 6.0])),
        (
            np.array([[1.0, np.nan, 3.0], [4.0, 5.0, np.nan], [np.nan, 8.0, 9.0]]),
            np.array([4.0, 8.0, 9.0]),
        ),
        (
            np.array([[np.nan, 2.0, np.nan], [np.nan, 5.0, np.nan]]),
            np.array([np.nan, 5.0, np.nan]),
        ),
        (np.array([[np.nan, 2.0, 3.0]]), np.array([np.nan, 2.0, 3.0])),
        (
            np.array([[np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan]]),
            np.array([np.nan, np.nan, np.nan]),
        ),
    ],
)
def test_find_last_valid_row(input_array, expected):
    """Test that last true value is selected for each column."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import find_last_valid_row

    result = find_last_valid_row(input_array)
    np.testing.assert_allclose(result, expected)


def test_calculate_slope_of_saturated_pressure_curve(
    dummy_climate_data,
    fixture_core_components,
    fixture_abiotic_constants,
):
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_slope_of_saturated_pressure_curve,
    )

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_slope_of_saturated_pressure_curve(
        temperature=data["air_temperature"][atm_index].to_numpy(),
        saturated_pressure_slope_parameters=fixture_abiotic_constants.saturated_pressure_slope_parameters,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 0.1)
    assert np.all(result[valid] < 0.5)


def test_calculate_actual_vapour_pressure(
    dummy_climate_data, fixture_core_components, fixture_pyrealm_config
):
    """Test calculate effective vapour pressure."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_actual_vapour_pressure,
    )

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_actual_vapour_pressure(
        air_temperature=data["air_temperature"][atm_index],
        relative_humidity=data["relative_humidity"][atm_index],
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    result_np = result.to_numpy()
    valid = ~np.isnan(result_np)

    assert np.all(result_np[valid] > 0)
    assert np.all(result_np[valid] < 4)


@pytest.mark.parametrize(
    "input_array, input_nan_mask, expected",
    [
        # Test case 1: Some NaNs, one intended
        (
            np.array([[1.0, np.nan], [3.0, np.nan]]),
            np.array([[False, True], [False, False]]),
            np.array([[1.0, np.nan], [3.0, 0.0]]),
        ),
        # Test case 2: All valid
        (
            np.array([[1.0, 2.0], [3.0, 4.0]]),
            np.array([[False, False], [False, False]]),
            np.array([[1.0, 2.0], [3.0, 4.0]]),
        ),
        # Test case 3: All intended NaNs
        (
            np.array([[np.nan, np.nan], [np.nan, np.nan]]),
            np.array([[True, True], [True, True]]),
            np.array([[np.nan, np.nan], [np.nan, np.nan]]),
        ),
        # Test case 4: One unintended NaN
        (
            np.array([[np.nan, 5.0], [6.0, 7.0]]),
            np.array([[False, False], [False, False]]),
            np.array([[0.0, 5.0], [6.0, 7.0]]),
        ),
    ],
)
def test_set_unintended_nan_to_zero(input_array, input_nan_mask, expected):
    """Test 2D arrays: unintended NaNs are zeroed, intended preserved."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        set_unintended_nan_to_zero,
    )

    result = set_unintended_nan_to_zero(input_array, input_nan_mask)
    np.testing.assert_allclose(result, expected, equal_nan=True)


def test_compute_layer_thickness_for_varying_canopy(
    dummy_climate_data, fixture_core_components
):
    """Test layer thickness for varying canopy."""
    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        compute_layer_thickness_for_varying_canopy,
    )

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    exp_result = np.array(
        [
            [2.0, 2.0, 2.0, 2.9],
            [10.0, 10.0, 9.9, np.nan],
            [10.0, 11.9, np.nan, np.nan],
            [9.9, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )

    result = compute_layer_thickness_for_varying_canopy(
        heights=data["layer_heights"][atm_index].to_numpy()
    )

    np.testing.assert_allclose(result, exp_result)


def test_compute_layer_thickness(dummy_climate_data, fixture_core_components):
    """Test compute layer thickness for all layers."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        compute_aboveground_layer_thickness,
    )

    data = dummy_climate_data
    lyr_str = fixture_core_components.layer_structure

    result = compute_aboveground_layer_thickness(
        heights=data["layer_heights"].to_numpy(),
    )
    exp = lyr_str.from_template()
    exp[lyr_str.index_filled_atmosphere] = np.array(
        [
            [2.0, 2.0, 2.0, 2.9],
            [10.0, 10.0, 9.9, np.nan],
            [10.0, 11.9, np.nan, np.nan],
            [9.9, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )
    np.testing.assert_allclose(result, exp.to_numpy())


def test_calculate_specific_humidity(
    dummy_climate_data, fixture_core_components, fixture_pyrealm_config
):
    """Test specific humidity."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_specific_humidity,
    )

    data = dummy_climate_data
    atm_index = fixture_core_components.layer_structure.index_filled_atmosphere

    result = calculate_specific_humidity(
        air_temperature=data["air_temperature"][atm_index].to_numpy(),
        relative_humidity=data["relative_humidity"][atm_index].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        molecular_weight_ratio_water_to_dry_air=0.622,
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 0.0)
    assert np.all(result[valid] < 1.0)


def test_update_profile_from_reference(fixture_core_components, dummy_climate_data):
    """Test update atmospheric pressure for varying canopy."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        update_profile_from_reference,
    )

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data

    result = update_profile_from_reference(
        layer_structure=lyr_str,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_pressure_ref"],
        time_index=1,
    )

    exp_result = np.array(
        [
            [96.0, 95.8, 95.5, 95.2],
            [96, 95.8, 95.5, np.nan],
            [96, 95.8, np.nan, np.nan],
            [96, np.nan, np.nan, np.nan],
            [96, 95.8, 95.5, 95.2],
        ]
    )
    np.testing.assert_allclose(
        result[lyr_str.index_filled_atmosphere], exp_result, rtol=1e-04, atol=1e-04
    )


def test_calculate_atmospheric_layer_geometry(
    dummy_climate_data, fixture_abiotic_indices
):
    """Test update atmospheric pressure for varying canopy."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_atmospheric_layer_geometry,
    )

    data = dummy_climate_data
    idx = fixture_abiotic_indices

    result = calculate_atmospheric_layer_geometry(
        data=data,
        idx=idx,
        minimum_mixing_depth=1.5,
    )

    for var in ["heights", "thickness", "layer_midpoints"]:
        assert var in result

    exp_heights = np.array(
        [
            [32.0, 24.0, 12.0, 3.0],
            [30.0, 22.0, 10, np.nan],
            [20.0, 12.0, np.nan, np.nan],
            [10.0, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )

    np.testing.assert_allclose(
        result["heights"][idx.atm], exp_heights, rtol=1e-04, atol=1e-04
    )

    exp_thickness = np.array(
        [
            [2.0, 2.0, 2.0, 2.9],
            [10.0, 10.0, 9.9, np.nan],
            [10.0, 11.9, np.nan, np.nan],
            [9.9, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )
    np.testing.assert_allclose(
        result["thickness"][idx.atm], exp_thickness, rtol=1e-04, atol=1e-04
    )

    exp_midpoints = np.array(
        [
            [31.0, 23.0, 11.0, 1.55],
            [25.0, 17.0, 5.05, np.nan],
            [15.0, 6.05, np.nan, np.nan],
            [5.05, np.nan, np.nan, np.nan],
            [0.05, 0.05, 0.05, 0.05],
        ]
    )

    np.testing.assert_allclose(
        result["layer_midpoints"][idx.atm], exp_midpoints, rtol=1e-04, atol=1e-04
    )


def test_generate_diurnal_cycle_from_monthly_data(dummy_climate_data):
    """Test generation of a single-day diurnal cycle from monthly means."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        generate_diurnal_cycle_from_monthly_data,
    )

    latitude_deg = 0.0
    month = 2
    days = 30

    data = dummy_climate_data
    n_layers, n_cells = data["canopy_evaporation"].shape
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]
    daily_temp_amplitude = (
        data["diurnal_temperature_range_ref"].isel(time_index=1).to_numpy()
    )

    # Generate diurnal cycle
    forcing = generate_diurnal_cycle_from_monthly_data(
        monthly_air_temperature=data["air_temperature_ref"]
        .isel(time_index=1)
        .to_numpy(),
        monthly_relative_humidity=data["relative_humidity_ref"]
        .isel(time_index=1)
        .to_numpy(),
        monthly_shortwave_absorption=data["shortwave_absorption"].to_numpy(),
        monthly_evapotranspiration=evapotranspiration.to_numpy(),
        monthly_soil_evaporation=data["soil_evaporation"].to_numpy(),
        latitude_deg=latitude_deg,
        month=month,
        days=days,
        daily_temp_amplitude=daily_temp_amplitude,
    )

    # Shape checks
    assert forcing["air_temperature_hourly"].shape == (24, n_cells)
    assert forcing["relative_humidity_hourly"].shape == (24, n_cells)
    assert forcing["shortwave_absorption_hourly"].shape == (24, n_layers, n_cells)
    assert forcing["evapotranspiration_hourly"].shape == (24, n_layers, n_cells)
    assert forcing["soil_evaporation_hourly"].shape == (24, n_cells)

    # Air temperature bounds
    air_temp = forcing["air_temperature_hourly"]
    air_temp_monthly = data["air_temperature_ref"].isel(time_index=1).to_numpy()
    assert np.all(air_temp >= air_temp_monthly - daily_temp_amplitude - 1e-6)
    assert np.all(air_temp <= air_temp_monthly + daily_temp_amplitude + 1e-6)

    # Relative humidity bounds
    rh = forcing["relative_humidity_hourly"]
    assert np.all(rh >= 0.0)
    assert np.all(rh <= 100.0)

    # Radiation only during daytime
    sw = forcing["shortwave_absorption_hourly"]
    nighttime_sw = sw[[0, 1, 2, 3, 22, 23], 11, :]
    assert np.all(nighttime_sw == 0.0)

    # Check conservation
    monthly_sum_et = np.nansum(forcing["evapotranspiration_hourly"], axis=0) * days
    monthly_sum_sw_abs = np.nansum(forcing["shortwave_absorption_hourly"], axis=0)
    monthly_sum_soil_evap = np.nansum(forcing["soil_evaporation_hourly"], axis=0) * days

    # Mask for valid monthly
    mask = ~np.isnan(evapotranspiration.to_numpy())

    assert np.allclose(
        monthly_sum_et[mask], evapotranspiration.to_numpy()[mask], rtol=1e-5
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


def test_fill_layer_template(fixture_core_components, fixture_abiotic_indices):
    """Test fill layer template."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import fill_layer_template

    layer_structure = fixture_core_components.layer_structure
    idx = fixture_abiotic_indices

    # Define values
    canopy_vals = np.array([[10.0, 20.0, 30.0, 40.0]] * 3)
    surface_vals = np.array([1.0, 2.0, 3.0, 4.0])
    soil_vals = np.array([[5.0, 5.0, 5.0, 5.0], [5.0, 5.0, 5.0, 5.0]])

    assignments = [
        (idx.canopy, canopy_vals),
        (idx.surface, surface_vals),
        (idx.soil, soil_vals),
    ]

    out = fill_layer_template(layer_structure, assignments)

    assert np.allclose(out[idx.canopy], canopy_vals)
    assert np.allclose(out[idx.surface], surface_vals)
    assert np.allclose(out[idx.soil], soil_vals)

    # Unfilled layers remain NaN
    assert np.all(np.isnan(out[0]))


def test_record_hourly_output():
    """Test recording hourly 1D and layered variables."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import record_hourly_output

    hours, layers, cells = 24, 14, 4
    hour = 5

    # Initialise data_record
    data_record = {
        "ground_heat_flux": np.full((hours, cells), np.nan),
        "longwave_emission": np.full((hours, layers, cells), np.nan),
    }

    # Hourly values
    hourly_values = {
        "ground_heat_flux": np.array([1.0, 2.0, 3.0, 4.0]),
        "longwave_emission": np.arange(layers * cells).reshape(layers, cells),
        "unknown_var": np.array([0, 0, 0, 0]),  # should be ignored
    }

    updated = record_hourly_output(
        hour=hour,
        data_record=data_record,
        hourly_values=hourly_values,
    )

    # 1D variable
    np.testing.assert_allclose(
        updated["ground_heat_flux"][hour], hourly_values["ground_heat_flux"]
    )

    # Other hours untouched
    for var in data_record:
        # All hours before current hour
        assert np.all(np.isnan(updated[var][:hour]))
        # The next hour specifically
        assert np.all(np.isnan(updated[var][hour + 1]))
        # All hours after next hour
        if hour + 2 < hours:
            assert np.all(np.isnan(updated[var][hour + 2 :]))


def test_mean_to_layers(fixture_core_components):
    """Test mean_to_layers function."""
    from virtual_ecosystem.models.abiotic.abiotic_tools import mean_to_layers

    data = np.arange(24 * 14 * 4, dtype=float).reshape(24, 14, 4)
    data[0, 2, 3] = np.nan
    data[5, 10, 1] = np.nan
    data_record = {"test_var": data}

    layer_structure = fixture_core_components.layer_structure
    index = layer_structure.index_filled_canopy

    result = mean_to_layers(
        var="test_var",
        index=index,
        data_record=data_record,
        layer_structure=layer_structure,
    )

    mean_vals = np.nanmean(data, axis=0)
    expected = np.full((14, 4), np.nan)
    expected[index] = mean_vals[index]

    assert result.shape == (14, 4)
    np.testing.assert_allclose(result, expected, rtol=1e-8)


def test_initialize_data_record_shapes_and_nans():
    """Test initialize_data_record for correct shapes and NaN initialization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import initialize_data_record

    time_dim = 24
    layers = 3
    cell_ids = 5

    variables = {
        "one_d_var": DataArray(np.zeros(cell_ids)),
        "two_d_var": DataArray(np.zeros((layers, cell_ids))),
    }

    result = initialize_data_record(
        variables=variables,
        time_dim=time_dim,
        layers=layers,
        cell_ids=cell_ids,
    )

    # Check keys preserved
    assert set(result.keys()) == set(variables.keys())

    # 1D -> (time, cell_ids)
    assert result["one_d_var"].shape == (time_dim, cell_ids)

    # 2D -> (time, layers, cell_ids)
    assert result["two_d_var"].shape == (time_dim, layers, cell_ids)

    # All values should be NaN
    for arr in result.values():
        assert np.isnan(arr).all()


def test_initialize_data_record_raises_on_invalid_dim():
    """Test initialize_data_record raises error on invalid variable dimensions."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import initialize_data_record

    variables = {
        "bad_var": DataArray(np.zeros((2, 3, 4))),
    }

    with pytest.raises(ValueError, match="Unsupported number of dimensions"):
        initialize_data_record(
            variables=variables,
            time_dim=24,
            layers=3,
            cell_ids=4,
        )


@pytest.mark.parametrize(
    "names, values, exclude, should_raise",
    [
        # Would normally fail, but excluded → OK
        (
            ("a", "b", "c"),
            {"a": 1},
            ("b", "c"),
            False,
        ),
        # Still fails: non-excluded missing
        (
            ("a", "b", "c"),
            {"a": 1},
            ("b",),
            True,
        ),
    ],
)
def test_validate_variables_with_exclude(names, values, exclude, should_raise):
    """Test variable validation between vars_updated and hourly record."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import validate_variables

    if should_raise:
        with pytest.raises(ValueError):
            validate_variables(names, values, exclude=exclude)
    else:
        validate_variables(names, values, exclude=exclude)


def test_all_finite_within_bounds():
    """Test all finite within blunds."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import finite_and_within

    arr = np.array([10, 20, 30])
    # should not raise
    finite_and_within(arr, 0, 40, "test_var")


def test_some_values_out_of_bounds():
    """Test some values out of bounds."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import finite_and_within

    arr = np.array([10, 50, 30])
    with pytest.raises(AssertionError, match="above 40"):
        finite_and_within(arr, 0, 40, "test_var")

    arr = np.array([-5, 20, 10])
    with pytest.raises(AssertionError, match="below 0"):
        finite_and_within(arr, 0, 40, "test_var")


def test_nan_values_ignored():
    """Test nan values ignored."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import finite_and_within

    arr = np.array([10, np.nan, 20])
    # min=10, max=20, within bounds should pass
    finite_and_within(arr, 0, 30, "test_var")


def test_no_finite_values_raises():
    """Test no finite raises error."""
    from virtual_ecosystem.models.abiotic.abiotic_tools import finite_and_within

    arr = np.array([np.nan, np.nan])
    with pytest.raises(AssertionError, match="has no finite values"):
        finite_and_within(arr, 0, 10, "test_var")


def test_multidimensional_array():
    """Test multidimensional array."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import finite_and_within

    arr = np.array([[10, 20], [30, 40]])
    finite_and_within(arr, 0, 50, "test_var")

    arr = np.array([[10, 60], [30, 40]])
    with pytest.raises(AssertionError, match="above 50"):
        finite_and_within(arr, 0, 50, "test_var")
