"""Test module for abiotic.energy_balance.py."""

import numpy as np
import pytest
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calc_vp_sat

from virtual_ecosystem.models.abiotic.abiotic_tools import (
    compute_aboveground_layer_thickness,
)
from virtual_ecosystem.models.abiotic.energy_balance import (
    calculate_total_absorbed_shortwave_radiation,
)


def test_initialise_canopy_and_soil_fluxes(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    data = dummy_climate_data_varying_canopy
    lyr_str = fixture_core_components.layer_structure
    canopy_index = lyr_str.index_filled_canopy
    subcanopy_index = lyr_str.index_surface_scalar
    topsoil_index = lyr_str.index_topsoil_scalar

    result = initialise_canopy_and_soil_fluxes(
        air_temperature=data["air_temperature"],
        layer_structure=lyr_str,
        initial_flux_value=0.001,
    )

    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "longwave_emission",
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

    np.testing.assert_allclose(
        result["canopy_temperature"][canopy_index],
        data["air_temperature"][canopy_index],
    )
    np.testing.assert_allclose(
        result["canopy_temperature"][subcanopy_index],
        data["air_temperature"][subcanopy_index],
    )


def test_calculate_longwave_emission(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    data = dummy_climate_data_varying_canopy
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


def test_calculate_sensible_heat_flux(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of sensible heat flux."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_sensible_heat_flux,
    )

    data = dummy_climate_data_varying_canopy
    index = fixture_core_components.layer_structure.index_filled_canopy

    result = calculate_sensible_heat_flux(
        density_air=data["density_air"][index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][index].to_numpy(),
        air_temperature=data["air_temperature"][index].to_numpy() + 0.5,
        surface_temperature=data["canopy_temperature"][index].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"].to_numpy(),
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > -30.0)
    assert np.all(result[valid] < 0.0)


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
    dummy_climate_data_varying_canopy,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test energy balance residual without flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data_varying_canopy
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
    dummy_climate_data_varying_canopy,
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test energy balance residual with flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data_varying_canopy
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


def test_update_air_temperature(dummy_climate_data_varying_canopy):
    """Test update air temperature in canopy."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_air_temperature,
    )

    data = dummy_climate_data_varying_canopy

    layer_thickness = compute_aboveground_layer_thickness(
        heights=data["layer_heights"].to_numpy()
    )

    result = update_air_temperature(
        air_temperature=data["air_temperature"].to_numpy(),
        sensible_heat_flux=data["sensible_heat_flux"].to_numpy(),
        specific_heat_air=data["specific_heat_air"].to_numpy(),
        density_air=data["density_air"].to_numpy(),
        mixing_layer_thickness=layer_thickness,
    )

    # Mask valid values
    valid = ~np.isnan(result)

    assert np.all(result[valid] > 10.0)
    assert np.all(result[valid] < 45.0)


def test_update_humidity_vpd(
    dummy_climate_data_varying_canopy, fixture_core_components, fixture_core_constants
):
    """Test update atmospheric humidity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_humidity_vpd,
    )

    data = dummy_climate_data_varying_canopy
    lystr = fixture_core_components.layer_structure
    canopy_index = lystr.index_filled_canopy
    atm_index = lystr.index_filled_atmosphere
    pyr_const = PyrealmCoreConst()

    above_ground_layer_thickness = compute_aboveground_layer_thickness(
        heights=data["layer_heights"][atm_index].to_numpy()
    )

    evapotranspiration = data["transpiration"] + data["canopy_evaporation"]
    saturated_vapour_pressure = calc_vp_sat(
        ta=data["air_temperature"][atm_index].to_numpy(), core_const=pyr_const
    )
    specific_humidity = np.array(
        [
            [0.02, 0.02, 0.02, 0.02],
            [0.012, 0.012, 0.012, np.nan],
            [0.014, 0.014, np.nan, np.nan],
            [0.015, np.nan, np.nan, np.nan],
            [0.012, 0.012, 0.012, 0.012],
        ]
    )

    mixing_coefficient = np.array(
        [
            [0.001, 0.001, 0.001, 0.001],
            [0.005, 0.005, 0.005, np.nan],
            [0.01, 0.01, np.nan, np.nan],
            [0.001, np.nan, np.nan, np.nan],
            [0.012, 0.012, 0.012, 0.012],
        ]
    )
    ventilation_rate = np.array([0.01, 0.01, 0.01, 0.01])
    time_interval = 3600.0
    mask = np.isnan(specific_humidity)

    # Run function
    result = update_humidity_vpd(
        canopy_evapotranspiration=evapotranspiration[canopy_index].to_numpy(),
        understorey_evapotranspiration=evapotranspiration[
            lystr.index_surface_scalar
        ].to_numpy(),
        soil_evaporation=data["soil_evaporation"].to_numpy(),
        saturated_vapour_pressure=saturated_vapour_pressure,
        specific_humidity=specific_humidity,
        layer_thickness=above_ground_layer_thickness,
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        density_air=data["density_air"][atm_index].to_numpy(),
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        molecular_weight_ratio_water_to_dry_air=(
            fixture_core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        dry_air_factor=1
        - fixture_core_constants.molecular_weight_ratio_water_to_dry_air,
        mm_to_kg=1e-3,
        cell_area=fixture_core_components.grid.cell_area,
        limits_specific_humidity=(0, 60),
        limits_relative_humidity=(0.001, 99.999),
        time_interval=time_interval,
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


def test_calculate_latent_heat_flux(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of latent heat flux."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_latent_heat_flux,
    )

    evapotranspiration = (
        dummy_climate_data_varying_canopy["transpiration"]
        + dummy_climate_data_varying_canopy["canopy_evaporation"]
    ).to_numpy()
    canopy_layers = fixture_core_components.layer_structure.index_filled_canopy
    surface_layer = fixture_core_components.layer_structure.index_surface_scalar

    result = calculate_latent_heat_flux(
        evapotranspiration=evapotranspiration
        / (30 * 24),  # convert mm month-1 to mm hour-1
        latent_heat_vapourisation=dummy_climate_data_varying_canopy[
            "latent_heat_vapourisation"
        ].to_numpy()
        * 1000,
        time_interval=3600.0,
    )

    exp_canopy = np.array(
        [
            [65.949074, 65.949074, 65.949074, np.nan],
            [47.106481, 47.106481, np.nan, np.nan],
            [28.263889, np.nan, np.nan, np.nan],
        ]
    )
    exp_surface = np.array([37.685185, 37.685185, 37.685185, 37.685185])

    np.testing.assert_allclose(result[canopy_layers], exp_canopy, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result[surface_layer], exp_surface, rtol=1e-4, atol=1e-4)


def test_total_absorbed_shortwave_radiation(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of total absorbed shortwave radiation."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        compute_weights_from_absorbed_radiation,
    )

    data = dummy_climate_data_varying_canopy
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


def test_make_canopy_residual_changes_with_temperature(
    fixture_abiotic_constants,
    fixture_core_constants,
):
    """Test that canopy residual changes with temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import make_canopy_residual

    shape = (2, 2)

    state = {
        "air_temperature": np.ones(shape) * 290,
        "evapotranspiration": np.ones(shape),
        "shortwave_absorption": np.ones(shape) * 200,
        "specific_heat_air": np.ones(shape) * 1005,
        "density_air": np.ones(shape) * 1.2,
        "latent_heat_vapourisation": np.ones(shape) * 2.45e6,
    }

    static = {
        "absorbed_longwave_radiation": np.ones(shape) * 300,
    }

    aerodynamic_resistance = np.ones(shape) * 50

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    residual = make_canopy_residual(
        state=state,
        static=static,
        aerodynamic_resistance=aerodynamic_resistance,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    temperature1 = np.ones(shape) * 28
    temperature2 = np.ones(shape) * 30

    residual1 = residual(temperature1)
    residual2 = residual(temperature2)

    assert not np.allclose(residual1, residual2)


def test_make_canopy_residual_uses_state(
    fixture_abiotic_constants, fixture_core_constants
):
    """Test that canopy residual reflects changes in state variables."""

    from virtual_ecosystem.models.abiotic.energy_balance import make_canopy_residual

    shape = (2, 2)

    state = {
        "air_temperature": np.ones(shape) * 29,
        "evapotranspiration": np.zeros(shape),
        "shortwave_absorption": np.zeros(shape),
        "specific_heat_air": np.ones(shape) * 1005,
        "density_air": np.ones(shape) * 1.2,
        "latent_heat_vapourisation": np.ones(shape) * 2.45e6,
    }

    static = {
        "absorbed_longwave_radiation": np.zeros(shape),
    }

    aerodynamic_resistance = np.ones(shape) * 50

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    residual = make_canopy_residual(
        state=state,
        static=static,
        aerodynamic_resistance=aerodynamic_resistance,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    temperature1 = np.ones(shape) * 29

    residual1 = residual(temperature1)

    # change state AFTER creating closure
    state["air_temperature"] += 10

    temperature2 = np.ones(shape) * 39
    residual2 = residual(temperature2)

    # closure should reflect updated state
    assert not np.allclose(residual1, residual2)


def test_make_canopy_residual_with_nans(
    fixture_abiotic_constants, fixture_core_constants
):
    """Test that canopy residual handles NaNs in state variables."""

    from virtual_ecosystem.models.abiotic.energy_balance import make_canopy_residual

    shape = (2, 3)

    state = {
        "air_temperature": np.ones(shape) * 290,
        "evapotranspiration": np.ones(shape),
        "shortwave_absorption": np.ones(shape) * 200,
        "specific_heat_air": np.ones(shape) * 1005,
        "density_air": np.ones(shape) * 1.2,
        "latent_heat_vapourisation": np.ones(shape) * 2.45e6,
    }

    static = {
        "absorbed_longwave_radiation": np.ones(shape) * 300,
    }

    aerodynamic_resistance = np.ones(shape) * 50

    abiotic_constants = fixture_abiotic_constants
    core_constants = fixture_core_constants

    residual = make_canopy_residual(
        state=state,
        static=static,
        aerodynamic_resistance=aerodynamic_resistance,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    temperature = np.array(
        [
            [29, 29, 29],
            [29, np.nan, np.nan],
        ]
    )

    result = residual(temperature)

    assert np.isnan(result[1, 1])
    assert np.isnan(result[1, 2])
