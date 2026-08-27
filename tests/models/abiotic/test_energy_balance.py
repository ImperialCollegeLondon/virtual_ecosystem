"""Test module for abiotic.energy_balance.py."""

from logging import INFO

import numpy as np
import pytest
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calculate_vp_sat

from tests.conftest import log_check
from virtual_ecosystem.models.abiotic.abiotic_tools import (
    compute_aboveground_layer_thickness,
)
from virtual_ecosystem.models.abiotic.energy_balance import (
    calculate_total_absorbed_shortwave_radiation,
)


def test_initialise_canopy_and_soil_fluxes(fixture_core_components):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    lyr_str = fixture_core_components.layer_structure
    canopy_index = lyr_str.index_filled_canopy
    subcanopy_index = lyr_str.index_surface_scalar
    topsoil_index = lyr_str.index_topsoil_scalar

    result = initialise_canopy_and_soil_fluxes(
        layer_structure=lyr_str,
        initial_flux_value=0.001,
    )

    for var in [
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "longwave_emission",
        "absorbed_longwave_radiation",
    ]:
        assert var in result

    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(
            result[var][canopy_index].to_numpy(), np.full((3, 4), 0.001)
        )
        np.testing.assert_allclose(
            result[var][subcanopy_index].to_numpy(), np.repeat(0.001, 4)
        )
        np.testing.assert_allclose(
            result[var][topsoil_index].to_numpy(), np.repeat(0.001, 4)
        )


def test_calculate_longwave_emission(
    dummy_climate_data,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    data = dummy_climate_data
    lyr_str = fixture_core_components.layer_structure
    canopy_index = lyr_str.index_filled_canopy

    result = calculate_longwave_emission(
        temperature=data["canopy_temperature"][canopy_index].to_numpy()
        + fixture_core_constants.zero_Celsius,
        emissivity=fixture_abiotic_constants.leaf_emissivity,
        stefan_boltzmann=fixture_core_constants.stefan_boltzmann_constant,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 400.0)
    assert np.all(result[valid] < 500.0)


def test_normalised_source_fractions_properties_and_expected_values() -> None:
    """Test that normalised source fractions have expected properties and values."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        normalised_source_fractions,
    )

    test_cases = [
        (
            np.array([0.0, 1.0], dtype=float),
            np.array([1.0, 0.0], dtype=float),
            0.5,
        ),
        (
            np.array([0.0, 0.5, 1.0], dtype=float),
            np.array([1.0, 0.5, 0.0], dtype=float),
            0.5,
        ),
        (
            np.array([2.0, 3.0], dtype=float),
            np.array([0.0, 1.0], dtype=float),
            0.8,
        ),
        (
            np.array([0.0, 0.0], dtype=float),
            np.array([0.0, 0.0], dtype=float),
            1.0,
        ),
        (
            np.array([0.0, 1.0, 2.0], dtype=float),
            np.array([2.0, 1.0, 0.0], dtype=float),
            0.0,
        ),
        (
            np.array([5.0], dtype=float),
            np.array([5.0], dtype=float),
            1.0,
        ),
        (
            np.array([0.0, 1.0, 10.0], dtype=float),
            np.array([10.0, 1.0, 0.0], dtype=float),
            1.5,
        ),
    ]

    for lai_above, lai_below, extinction_coefficient_lw in test_cases:
        f_sky, f_soil, f_veg = normalised_source_fractions(
            cumulative_lai_above=lai_above,
            cumulative_lai_below=lai_below,
            longwave_extinction_coefficient=extinction_coefficient_lw,
        )

        assert f_sky.shape == lai_above.shape
        assert f_soil.shape == lai_below.shape
        assert f_veg.shape == lai_above.shape

        assert np.all((0.0 <= f_sky) & (f_sky <= 1.0))
        assert np.all((0.0 <= f_soil) & (f_soil <= 1.0))
        assert np.all((0.0 <= f_veg) & (f_veg <= 1.0))

        np.testing.assert_allclose(f_sky + f_soil + f_veg, 1.0)

        raw_sky = np.exp(-extinction_coefficient_lw * lai_above)
        raw_soil = np.exp(-extinction_coefficient_lw * lai_below)
        raw_veg = np.clip(1.0 - raw_sky - raw_soil, 0.0, 1.0)
        total = raw_sky + raw_soil + raw_veg

        np.testing.assert_allclose(f_sky, raw_sky / total)
        np.testing.assert_allclose(f_soil, raw_soil / total)
        np.testing.assert_allclose(f_veg, raw_veg / total)

    zero_ext_lai_above = np.array([0.0, 1.0, 2.0], dtype=float)
    zero_ext_lai_below = np.array([2.0, 1.0, 0.0], dtype=float)
    f_sky, f_soil, f_veg = normalised_source_fractions(
        cumulative_lai_above=zero_ext_lai_above,
        cumulative_lai_below=zero_ext_lai_below,
        longwave_extinction_coefficient=0.0,
    )
    np.testing.assert_allclose(f_sky, 0.5)
    np.testing.assert_allclose(f_soil, 0.5)
    np.testing.assert_allclose(f_veg, 0.0)

    high_lai_f_sky, high_lai_f_soil, high_lai_f_veg = normalised_source_fractions(
        cumulative_lai_above=np.array([5.0], dtype=float),
        cumulative_lai_below=np.array([5.0], dtype=float),
        longwave_extinction_coefficient=1.0,
    )
    assert high_lai_f_veg[0] > 0.0
    np.testing.assert_allclose(
        high_lai_f_sky[0] + high_lai_f_soil[0] + high_lai_f_veg[0],
        1.0,
    )


def test_calculate_absorbed_longwave_radiation(
    fixture_core_components,
    dummy_climate_data,
    fixture_abiotic_indices,
):
    """Test absorbed longwave radiation using diffuse view-factor formulation."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_absorbed_longwave_radiation,
    )

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data
    idx = fixture_abiotic_indices

    leaf_area_index = np.nan_to_num(data["leaf_area_index"].to_numpy(), nan=0.0)
    downward_longwave = np.array([400.0, 400.0, 400.0, 400.0])

    leaf_emissivity = 0.97
    soil_emissivity = 0.95
    stefan_boltzmann = 5.67e-8
    zero_celsius = 273.15
    extinction_coefficient_lw = 0.1

    result = calculate_absorbed_longwave_radiation(
        downward_longwave=downward_longwave,
        leaf_area_index=leaf_area_index,
        canopy_temperature=data["canopy_temperature"].to_numpy(),
        soil_temperature=data["soil_temperature"].to_numpy(),
        leaf_emissivity=leaf_emissivity,
        soil_emissivity=soil_emissivity,
        stefan_boltzmann_constant=stefan_boltzmann,
        zero_Celsius=zero_celsius,
        extinction_coefficient_lw=extinction_coefficient_lw,
        idx=idx,
    )

    # Shape
    assert result.shape == (lyr_str.n_layers, data.grid.n_cells)

    # All values non-negative and finite
    assert np.all(np.isfinite(result))
    assert np.all(result >= 0.0)

    # Surface and topsoil should absorb some longwave
    assert np.all(result[idx.surface, :] > 0.0)
    assert np.all(result[idx.topsoil, :] > 0.0)

    # Lower canopy should still receive some longwave if LAI is present
    canopy_layers = [
        layer
        for layer in range(result.shape[0])
        if layer not in (idx.surface, idx.topsoil)
    ]
    for layer in canopy_layers:
        lai_mask = leaf_area_index[layer] > 0.0
        if np.any(lai_mask):
            assert np.all(result[layer, lai_mask] > 0.0)

    # Physical reasonableness: absorbed LW should not be absurdly large
    assert np.all(result < 1000.0)


def test_calculate_sensible_heat_flux(dummy_climate_data, fixture_core_components):
    """Test calculation of sensible heat flux."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_sensible_heat_flux,
    )

    data = dummy_climate_data
    index = fixture_core_components.layer_structure.index_filled_canopy

    result = calculate_sensible_heat_flux(
        density_air=data["density_air"][index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][index].to_numpy(),
        air_temperature=data["air_temperature"][index].to_numpy(),
        surface_temperature=data["canopy_temperature"][index].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"].to_numpy(),
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > -300.0)
    assert np.all(result[valid] > 0.0)


@pytest.mark.parametrize(
    "g, soil_temp, dz, k, rho, cp, dt, exp_n, exp_temp",
    [
        # Test case for 2 soil layers and constant (float) soil parameters
        (
            np.array([20.0, 25.0, 18.0, 22.0]),
            np.array([[15.0, 16.0, 14.0, 13.0], [14.0, 15.0, 13.0, 12.0]]),
            np.array([[0.1, 0.1, 0.1, 0.1], [0.1, 0.1, 0.1, 0.1]]),
            1.2,
            1300.0,
            800.0,
            3600.0,  # time_interval (1 hour)
            2,
            np.array(
                [
                    [15.692308, 16.865385, 14.623077, 13.761538],
                    [14.702959, 15.774852, 13.674201, 12.731716],
                ],
            ),
        ),
        # Test case for 5 soil layers and arrays of soil parameters
        (
            np.array([18.0, 19.0, 20.0, 21.0]),
            np.array(
                [
                    [15.0, 16.0, 14.0, 13.0],
                    [14.5, 15.5, 13.5, 12.5],
                    [14.2, 15.2, 13.2, 12.2],
                    [14.1, 15.1, 13.1, 12.1],
                    [14.0, 15.0, 13.0, 12.0],
                ],
            ),
            np.array([[0.1], [0.2], [0.2], [0.3], [0.2]]) * np.ones((1, 4)),
            np.repeat(1.2, 4),
            np.repeat(1300.0, 4),
            np.repeat(800.0, 4),
            3600.0,  # time_interval (1 hour)
            5,
            np.array(
                [
                    [15.623077, 16.657692, 14.692308, 13.726923],
                    [14.520769, 15.520769, 13.520769, 12.520769],
                    [14.222926, 15.222926, 13.222926, 12.222926],
                    [14.1, 15.1, 13.1, 12.1],
                    [14.010385, 15.010385, 13.010385, 12.010385],
                ],
            ),
        ),
    ],
)
def test_update_soil_temperature(g, soil_temp, dz, k, rho, cp, dt, exp_n, exp_temp):
    """Test update soil temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import update_soil_temperature

    updated_temperature = update_soil_temperature(
        ground_heat_flux=g,
        soil_temperature=soil_temp,
        soil_layer_thickness=dz,
        soil_thermal_conductivity=k,
        soil_bulk_density=rho,
        specific_heat_capacity_soil=cp,
        time_interval=dt,
    )

    # Check that the number of layers matches the expected layers
    assert updated_temperature.shape[0] == exp_n
    np.testing.assert_allclose(updated_temperature, exp_temp, rtol=1e-4, atol=1e-4)


def test_energy_balance_residual_only(
    dummy_climate_data,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test energy balance residual without flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]
    aerodynamic_resistance_2d = np.tile(data["aerodynamic_resistance_canopy"], (14, 1))

    result = calculate_energy_balance_residual(
        canopy_temperature_initial=data["canopy_temperature"].to_numpy(),
        air_temperature=data["air_temperature"].to_numpy(),
        evapotranspiration=evapotranspiration.to_numpy(),
        absorbed_shortwave_radiation=data["shortwave_absorption"].to_numpy(),
        absorbed_longwave_radiation=data["downward_longwave_radiation"]
        .isel(time_index=0)
        .to_numpy()
        * fixture_abiotic_constants.leaf_emissivity,
        specific_heat_air=data["specific_heat_air"].to_numpy(),
        density_air=data["density_air"].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_2d,
        latent_heat_vapourisation=data["latent_heat_vapourisation"].to_numpy() * 1000,
        leaf_emissivity=fixture_abiotic_constants.leaf_emissivity,
        stefan_boltzmann_constant=fixture_core_constants.stefan_boltzmann_constant,
        zero_Celsius=fixture_core_constants.zero_Celsius,
        seconds_to_hour=fixture_core_constants.seconds_to_hour,
        return_fluxes=False,
    )

    assert isinstance(result, np.ndarray)
    assert result.shape == (14, 4)
    mask = ~np.isnan(evapotranspiration)
    assert np.all(np.isfinite(result[mask]))


def test_energy_balance_return_fluxes(
    dummy_climate_data,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test energy balance residual with flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]
    aerodynamic_resistance_2d = np.tile(data["aerodynamic_resistance_canopy"], (14, 1))

    result = calculate_energy_balance_residual(
        canopy_temperature_initial=data["canopy_temperature"].to_numpy(),
        air_temperature=data["air_temperature"].to_numpy(),
        evapotranspiration=evapotranspiration.to_numpy(),
        absorbed_shortwave_radiation=data["shortwave_absorption"].to_numpy(),
        absorbed_longwave_radiation=data["shortwave_absorption"].to_numpy() * 0.5,
        specific_heat_air=data["specific_heat_air"].to_numpy(),
        density_air=data["density_air"].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_2d,
        latent_heat_vapourisation=data["latent_heat_vapourisation"].to_numpy() * 1000,
        leaf_emissivity=fixture_abiotic_constants.leaf_emissivity,
        stefan_boltzmann_constant=fixture_core_constants.stefan_boltzmann_constant,
        zero_Celsius=fixture_core_constants.zero_Celsius,
        seconds_to_hour=fixture_core_constants.seconds_to_hour,
        return_fluxes=True,
    )

    assert isinstance(result, dict)
    expected_keys = {
        "longwave_emission",
        "sensible_heat_flux",
        "latent_heat_flux",
        "energy_balance_residual",
        "net_radiation",
    }
    mask = ~np.isnan(evapotranspiration)

    assert set(result.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (14, 4)
        assert np.all(np.isfinite(result[key][mask]))


def test_update_canopy_air_temperature(dummy_climate_data):
    """Test update air temperature in canopy."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_canopy_air_temperature,
    )

    data = dummy_climate_data

    layer_thickness = compute_aboveground_layer_thickness(
        heights=data["layer_heights"].to_numpy()
    )

    result = update_canopy_air_temperature(
        air_temperature=data["air_temperature"].to_numpy(),
        sensible_heat_flux=data["sensible_heat_flux"].to_numpy(),
        specific_heat_air=data["specific_heat_air"].to_numpy(),
        density_air=data["density_air"].to_numpy(),
        mixing_layer_thickness=layer_thickness,
        integration_time_step=60.0,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 10.0)
    assert np.all(result[valid] < 45.0)


def test_update_specific_humidity(dummy_climate_data, fixture_core_components):
    """Test update specific humidity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_specific_humidity,
    )

    data = dummy_climate_data
    lystr = fixture_core_components.layer_structure

    above_ground_layer_thickness = compute_aboveground_layer_thickness(
        heights=data["layer_heights"].to_numpy()
    )

    evapotranspiration = data["transpiration"] + data["canopy_evaporation"]

    exp = np.array(
        [
            [0.0143, 0.0135, 0.0122, 0.0105],
            [0.02167311, 0.01866102, 0.01435907, np.nan],
            [0.0193, 0.01566248, np.nan, np.nan],
            [0.01644998, np.nan, np.nan, np.nan],
            [0.20544839, 0.17349508, 0.14823333, 0.13816102],
        ]
    )

    result = update_specific_humidity(
        evapotranspiration=evapotranspiration.to_numpy(),
        soil_evaporation=data["soil_evaporation"].to_numpy(),
        specific_humidity=data["specific_humidity"].to_numpy(),
        layer_thickness=above_ground_layer_thickness,
        density_air=data["density_air"].to_numpy(),
        mm_to_kg=1e-3,
        cell_area=fixture_core_components.grid.cell_area,
        time_interval=3600.0,
        surface_index=lystr.index_surface_scalar,
    )

    np.testing.assert_allclose(exp, result[lystr.index_filled_atmosphere], rtol=1e-6)


def test_update_humidity_vpd(
    dummy_climate_data, fixture_core_components, fixture_core_constants
):
    """Test update atmospheric humidity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_humidity_vpd,
    )

    data = dummy_climate_data
    lystr = fixture_core_components.layer_structure
    atm_index = lystr.index_filled_atmosphere
    pyr_const = PyrealmCoreConst()

    above_ground_layer_thickness = compute_aboveground_layer_thickness(
        heights=data["layer_heights"][atm_index].to_numpy()
    )

    saturated_vapour_pressure = calculate_vp_sat(
        tc=data["air_temperature"][atm_index].to_numpy(), core_const=pyr_const
    )
    mask = np.isnan(saturated_vapour_pressure)

    # Run function
    result = update_humidity_vpd(
        saturated_vapour_pressure=saturated_vapour_pressure,
        specific_humidity_mixed=data["specific_humidity"][atm_index].to_numpy(),
        layer_thickness=above_ground_layer_thickness,
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        density_air=data["density_air"][atm_index].to_numpy(),
        molecular_weight_ratio_water_to_dry_air=(
            fixture_core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        dry_air_factor=1
        - fixture_core_constants.molecular_weight_ratio_water_to_dry_air,
        cell_area=fixture_core_components.grid.cell_area,
        limits_relative_humidity=(0.001, 99.999),
        denominator_tolerance=1e-12,
        limits_vapour_pressure_deficit=(0.01, 50),
    )

    # Basic shape checks
    for key in [
        "relative_humidity",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "specific_humidity",
        "condensation",
    ]:
        assert key in result
        assert isinstance(result[key], np.ndarray)
        assert np.all(np.isnan(result[key][mask]))

    # Expected trends: ET and mixing should raise humidity slightly where is not NaN
    assert np.all(result["specific_humidity"][~mask] >= 0.00)

    # VPD should be reduced where evapotranspiration or mixing adds moisture
    assert np.all(result["vapour_pressure_deficit"][~mask] > 0.0)
    assert np.all(result["vapour_pressure"][~mask] <= saturated_vapour_pressure[~mask])

    # RH should be between 0 and 100
    assert np.all(
        (result["relative_humidity"][~mask] > 0)
        & (result["relative_humidity"][~mask] < 100)
    )

    # Condensation should be >=0
    assert np.all(result["condensation"][~mask] >= 0)


def test_calculate_latent_heat_flux(dummy_climate_data, fixture_core_components):
    """Test calculation of latent heat flux."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_latent_heat_flux,
    )

    evapotranspiration = (
        dummy_climate_data["transpiration"] + dummy_climate_data["canopy_evaporation"]
    ).to_numpy()
    canopy_layers = fixture_core_components.layer_structure.index_filled_canopy
    surface_layer = fixture_core_components.layer_structure.index_surface_scalar

    result = calculate_latent_heat_flux(
        evapotranspiration=evapotranspiration
        / (30 * 24),  # convert mm month-1 to mm hour-1
        latent_heat_vapourisation=dummy_climate_data[
            "latent_heat_vapourisation"
        ].to_numpy()
        * 1000,
        time_interval=3600.0,
    )

    exp_canopy = np.array(
        [
            [87.21836, 62.98064, 29.03422, np.nan],
            [67.86111, 43.54421, np.nan, np.nan],
            [43.80902, np.nan, np.nan, np.nan],
        ]
    )
    exp_surface = np.array([19.77662, 13.94066, 8.09999, 3.1083])

    np.testing.assert_allclose(result[canopy_layers], exp_canopy, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result[surface_layer], exp_surface, rtol=1e-4, atol=1e-4)


def test_total_absorbed_shortwave_radiation(
    dummy_climate_data, fixture_core_components
):
    """Test calculation of total absorbed shortwave radiation."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        compute_weights_from_absorbed_radiation,
    )

    data = dummy_climate_data
    canopy_index = fixture_core_components.layer_structure.index_filled_canopy

    downward_sw = data["downward_shortwave_radiation"].isel(time_index=0).to_numpy()
    canopy_absorption = data["shortwave_absorption"][canopy_index].to_numpy()

    weights = compute_weights_from_absorbed_radiation(radiation=canopy_absorption)
    result = calculate_total_absorbed_shortwave_radiation(
        downward_shortwave_radiation=downward_sw,
        shortwave_absorption_by_canopy=canopy_absorption,
        par_fraction=0.48,
        fraction_par_used=0.1,
        leaf_absorptance_non_par=0.5,
    )

    assert result.shape == canopy_absorption.shape

    # Compute upper bound
    shortwave_non_par = downward_sw * (1 - 0.48)
    max_nir_absorbed = 0.5 * shortwave_non_par * weights
    total_available = canopy_absorption + max_nir_absorbed

    # Build mask: only test where all relevant values are finite
    valid_mask = np.isfinite(canopy_absorption)

    # Energy conservation (only on valid points)
    assert np.all(result[valid_mask] <= total_available[valid_mask] + 1e-6)

    # Non-negative check
    assert np.all(result[valid_mask] >= 0)


def test_secant_nan_handling():
    """Test that secant solver handles NaNs correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        secant_solve_cells_layers,
    )

    target = np.array(
        [
            [1.0, 2.0, 3.0],
            [4.0, np.nan, np.nan],
            [np.nan, np.nan, np.nan],
        ]
    )

    def residual(temperature):
        return temperature - target

    initial_temperature = np.zeros_like(target)

    result = secant_solve_cells_layers(
        residual_function=residual,
        initial_guess=initial_temperature,
        maxiter_secant=10,
        convergence_tolerance=1e-12,
        small_perturbation_second_guess=1e-6,
        denominator_tolerance=1e-12,
    )

    # valid cells solved correctly
    mask = ~np.isnan(target)
    assert np.allclose(result[mask], target[mask], atol=1e-4)

    # NaNs preserved
    assert np.all(np.isnan(result[~mask]))


SECANT_NONCONVERGENCE_LOG = (
    (
        INFO,
        "Secant solver did not fully converge within 2 iterations. "
        "2 unconverged layer(s), 3 unconverged cell(s), "
        "and 5 unconverged (layer, cell_id) pair(s).",
    ),
    (
        INFO,
        "Unconverged cell IDs: [0, 1, 2]",
    ),
    (
        INFO,
        "Unconverged (layer, cell_id) pairs: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]",
    ),
)


def test_secant_solver_logs_unconverged_pairs(caplog):
    """Test secant solver no convergence."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        secant_solve_cells_layers,
    )

    # Initial guess of canopy temperature, assuming not all layers are filled
    initial_guess = np.array(
        [[25.0, 25.0, 25.0], [21.0, 21.0, np.nan], [np.nan, np.nan, np.nan]]
    )

    # Generate simple residual function that is solved using the secant methods
    # In the abiotic model, this is the residual of the energy balance
    def residual_function(temperature):
        return np.ones_like(temperature)

    secant_solve_cells_layers(
        residual_function=residual_function,
        initial_guess=initial_guess,
        maxiter_secant=2,
        convergence_tolerance=1e-12,
        small_perturbation_second_guess=1e-3,
        denominator_tolerance=1e-12,
    )

    log_check(
        caplog,
        expected_log=SECANT_NONCONVERGENCE_LOG,
    )


def test_make_canopy_residual_changes_with_temperature(
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_abiotic_indices,
    fixture_state_inputs,
    fixture_static_inputs,
):
    """Test that canopy residual changes with temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import make_canopy_residual

    state = fixture_state_inputs
    static = fixture_static_inputs

    aerodynamic_resistance = np.full_like(state["air_temperature"], 50)

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    residual = make_canopy_residual(
        state=state,
        static=static,
        aerodynamic_resistance=aerodynamic_resistance,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    temperature1 = state["air_temperature"]
    temperature2 = state["air_temperature"] + 2.0

    residual1 = residual(temperature1)
    residual2 = residual(temperature2)

    assert not np.allclose(residual1, residual2)


def test_make_canopy_residual_uses_state(
    fixture_abiotic_constants,
    fixture_core_constants,
    fixture_state_inputs,
    fixture_static_inputs,
):
    """Test that canopy residual reflects changes in state variables."""

    from virtual_ecosystem.models.abiotic.energy_balance import make_canopy_residual

    state = fixture_state_inputs
    static = fixture_static_inputs

    aerodynamic_resistance = np.full_like(state["air_temperature"], 50)

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    residual = make_canopy_residual(
        state=state,
        static=static,
        aerodynamic_resistance=aerodynamic_resistance,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    temperature1 = np.full_like(state["air_temperature"], 29)

    residual1 = residual(temperature1)

    # change state AFTER creating closure
    state["air_temperature"] += 10

    temperature2 = np.full_like(state["air_temperature"], 39)
    residual2 = residual(temperature2)

    # closure should reflect updated state
    assert not np.allclose(residual1, residual2)


def test_solve_canopy_temperature_with_air_coupling(
    fixture_state_inputs,
    fixture_static_inputs,
    fixture_abiotic_constants,
    fixture_abiotic_indices,
    fixture_core_constants,
):
    """Test coupled canopy-air temperature solve returns consistent outputs."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        solve_canopy_temperature_with_air_coupling,
    )

    state = fixture_state_inputs
    static = fixture_static_inputs
    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants
    idx = fixture_abiotic_indices

    canopy_temperature, air_temperature, fluxes = (
        solve_canopy_temperature_with_air_coupling(
            state=state,
            static=static,
            abiotic_constants=abiotic_constants,
            core_constants=core_constants,
            maxiter_air=100,
            air_temperature_tolerance=1e-4,
            maxiter_secant=10,
            convergence_tolerance=1e-6,
            small_perturbation_second_guess=0.5,
            denominator_tolerance=1e-12,
            idx=idx,
        )
    )

    # Shape checks
    assert canopy_temperature.shape == state["air_temperature"].shape
    assert air_temperature.shape == state["air_temperature"].shape

    for key in (
        "longwave_emission",
        "sensible_heat_flux",
        "latent_heat_flux",
        "energy_balance_residual",
        "net_radiation",
    ):
        assert key in fluxes
        assert fluxes[key].shape == state["air_temperature"].shape

    # Air temperature should change if sensible heat flux is non-zero
    assert not np.allclose(
        air_temperature,
        state["air_temperature"],
    )

    # Check reference value is replaced
    assert np.isfinite(air_temperature[idx.above]).all()

    # Check surface value is finite
    assert np.all(np.isfinite(air_temperature[idx.surface]))
