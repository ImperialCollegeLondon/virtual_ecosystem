"""Test module for abiotic.energy_balance.py."""

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.abiotic_tools import (
    compute_layer_thickness_for_varying_canopy,
)
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


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
    ]:
        assert var in result

    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(
            result[var][canopy_index].to_numpy(), np.full((3, 4), 0.001)
        )
        np.testing.assert_allclose(
            result[var][topsoil_index].to_numpy(), np.repeat(0.001, 4)
        )

    np.testing.assert_allclose(
        result["canopy_temperature"][canopy_index],
        data["air_temperature"][canopy_index],
    )


def test_calculate_longwave_emission(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    data = dummy_climate_data_varying_canopy
    lyr_str = fixture_core_components.layer_structure
    canopy_index = lyr_str.index_filled_canopy

    result = calculate_longwave_emission(
        temperature=data["air_temperature"][canopy_index].to_numpy()
        + CoreConsts.zero_Celsius,
        emissivity=AbioticConsts.soil_emissivity,
        stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
    )

    exp_result = np.array(
        [
            [454.022275, 454.022275, 454.022275, 454.022275],
            [448.21345, 448.21345, np.nan, np.nan],
            [438.412504, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_sensible_heat_flux(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of sensible heat flux."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_sensible_heat_flux,
    )

    data = dummy_climate_data_varying_canopy
    index = fixture_core_components.layer_structure.index_filled_canopy

    expected_flux = np.array(
        [
            [-0.489356, -0.489356, -0.489356, -0.489356],
            [-0.390997, -0.390997, np.nan, np.nan],
            [-0.222852, np.nan, np.nan, np.nan],
        ]
    )

    computed_flux = calculate_sensible_heat_flux(
        density_air=data["density_air"][index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][index].to_numpy(),
        air_temperature=data["air_temperature"][index].to_numpy(),
        surface_temperature=data["canopy_temperature"][index].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"][index].to_numpy(),
    )

    # Assert all elements are close
    np.testing.assert_allclose(computed_flux, expected_flux, rtol=1e-5)


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
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test energy balance residual without flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data_varying_canopy
    canopy_index = fixture_core_components.layer_structure.index_filled_canopy
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]

    result = calculate_energy_balance_residual(
        canopy_temperature_initial=data["canopy_temperature"][canopy_index].to_numpy(),
        air_temperature=data["air_temperature"][canopy_index].to_numpy(),
        evapotranspiration=evapotranspiration[canopy_index].to_numpy(),
        absorbed_radiation_canopy=data["shortwave_absorption"][canopy_index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][canopy_index].to_numpy(),
        density_air=data["density_air"][canopy_index].to_numpy(),
        density_water=np.full_like(data["density_air"][canopy_index], 1000),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"][
            canopy_index
        ].to_numpy(),
        latent_heat_vapourisation=data["latent_heat_vapourisation"][
            canopy_index
        ].to_numpy(),
        leaf_emissivity=AbioticConsts.leaf_emissivity,
        stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
        zero_Celsius=CoreConsts.zero_Celsius,
        seconds_to_hour=CoreConsts.seconds_to_hour,
        return_fluxes=False,
    )

    assert isinstance(result, np.ndarray)
    assert result.shape == (3, 4)
    assert np.isfinite(result[0, 0])


def test_energy_balance_return_fluxes(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test energy balance residual with flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data_varying_canopy
    canopy_index = fixture_core_components.layer_structure.index_filled_canopy
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]

    result = calculate_energy_balance_residual(
        canopy_temperature_initial=data["canopy_temperature"][canopy_index].to_numpy(),
        air_temperature=data["air_temperature"][canopy_index].to_numpy(),
        evapotranspiration=evapotranspiration[canopy_index].to_numpy(),
        absorbed_radiation_canopy=data["shortwave_absorption"][canopy_index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][canopy_index].to_numpy(),
        density_air=data["density_air"][canopy_index].to_numpy(),
        density_water=np.full_like(data["density_air"][canopy_index], 1000),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"][
            canopy_index
        ].to_numpy(),
        latent_heat_vapourisation=data["latent_heat_vapourisation"][
            canopy_index
        ].to_numpy(),
        leaf_emissivity=AbioticConsts.leaf_emissivity,
        stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
        zero_Celsius=CoreConsts.zero_Celsius,
        seconds_to_hour=CoreConsts.seconds_to_hour,
        return_fluxes=True,
    )

    assert isinstance(result, dict)
    expected_keys = {
        "longwave_emission_canopy",
        "sensible_heat_flux_canopy",
        "latent_heat_flux_canopy",
        "energy_balance_residual",
    }
    assert set(result.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (3, 4)


def test_solve_canopy_temperature(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test solving canopy temperature with Newton method."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        solve_canopy_temperature,
    )

    data = dummy_climate_data_varying_canopy
    canopy_index = fixture_core_components.layer_structure.index_filled_canopy
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]

    result = solve_canopy_temperature(
        canopy_temperature_initial=data["canopy_temperature"][canopy_index].to_numpy(),
        air_temperature=data["air_temperature"][canopy_index].to_numpy(),
        evapotranspiration=evapotranspiration[canopy_index].to_numpy() / 730,
        absorbed_radiation_canopy=data["shortwave_absorption"][canopy_index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][canopy_index].to_numpy(),
        density_air=data["density_air"][canopy_index].to_numpy(),
        density_water=1000.0,
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"][
            canopy_index
        ].to_numpy(),
        latent_heat_vapourisation=data["latent_heat_vapourisation"][
            canopy_index
        ].to_numpy(),
        emissivity_leaf=0.96,
        stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
        zero_Celsius=CoreConsts.zero_Celsius,
        seconds_to_hour=CoreConsts.seconds_to_hour,
        return_fluxes=False,
        maxiter=100,
    )

    assert isinstance(result, np.ndarray)
    assert result.shape == data["canopy_temperature"][canopy_index].shape

    # Mask where input is not NaN
    mask = ~np.isnan(data["canopy_temperature"][canopy_index])

    # Assert plausible range for non-NaN input
    assert np.all((result[mask] > 0) & (result[mask] < 50))

    # Assert NaNs are preserved
    assert np.all(np.isnan(result[~mask]))


def test_update_air_temperature(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test update air temperature in canopy."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_air_temperature,
    )

    data = dummy_climate_data_varying_canopy
    lystr = fixture_core_components.layer_structure
    canopy_index = lystr.index_filled_canopy

    above_ground_layer_thickness = compute_layer_thickness_for_varying_canopy(
        heights=data["layer_heights"][lystr.index_filled_atmosphere].to_numpy()
    )

    updated_air_temperature = update_air_temperature(
        air_temperature=data["air_temperature"][canopy_index].to_numpy(),
        surface_temperature=data["canopy_temperature"][canopy_index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][canopy_index].to_numpy(),
        density_air=data["density_air"][canopy_index].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"][
            canopy_index
        ].to_numpy(),
        mixing_layer_thickness=above_ground_layer_thickness[1:-1],
    )

    exp_result = np.array(
        [
            [29.883755, 29.883755, 29.857958, 29.857958],
            [28.902139, 28.886732, np.nan, np.nan],
            [27.224235, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(updated_air_temperature, exp_result, rtol=1e-4)


def test_update_humidity_vpd(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test update atmospheric humidity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_humidity_vpd,
    )

    data = dummy_climate_data_varying_canopy
    lystr = fixture_core_components.layer_structure
    canopy_index = lystr.index_filled_canopy
    atm_index = lystr.index_filled_atmosphere

    above_ground_layer_thickness = compute_layer_thickness_for_varying_canopy(
        heights=data["layer_heights"][atm_index].to_numpy()
    )

    evapotranspiration = data["transpiration"] + data["canopy_evaporation"]
    saturated_vapour_pressure = np.array(
        [
            [2.5, 2.5, 2.5, 2.5],
            [2.5, 2.5, 2.5, np.nan],
            [2.0, 2.0, np.nan, np.nan],
            [1.8, np.nan, np.nan, np.nan],
            [2.0, 2.0, 2.0, 2.0],
        ]
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
        evapotranspiration=evapotranspiration[canopy_index].to_numpy(),
        soil_evaporation=data["soil_evaporation"].to_numpy(),
        saturated_vapour_pressure=saturated_vapour_pressure,
        specific_humidity=specific_humidity,
        layer_thickness=above_ground_layer_thickness,
        atmospheric_pressure=data["atmospheric_pressure"][atm_index].to_numpy(),
        density_air=data["density_air"][atm_index].to_numpy(),
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        wind_speed=data["wind_speed_ref"].isel(time_index=0).to_numpy(),
        molecular_weight_ratio_water_to_dry_air=(
            CoreConsts.molecular_weight_ratio_water_to_dry_air
        ),
        dry_air_factor=1 - CoreConsts.molecular_weight_ratio_water_to_dry_air,
        cell_area=fixture_core_components.grid.cell_area,
        time_interval=time_interval,
    )

    # Basic shape checks
    for key in [
        "relative_humidity",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "specific_humidity",
    ]:
        assert key in result
        assert isinstance(result[key], np.ndarray)
        assert np.all(np.isnan(result[key][mask]))

    # Expected trends: ET and mixing should raise humidity slightly where is not NaN
    assert np.all(result["specific_humidity"][~mask] >= 0.00)

    # VPD should be reduced where evapotranspiration or mixing adds moisture
    assert np.all(result["vapour_pressure_deficit"][~mask] >= 0.0)
    assert np.all(result["vapour_pressure"][~mask] <= saturated_vapour_pressure[~mask])

    # RH should be between 0 and 100
    assert np.all(
        (result["relative_humidity"][~mask] >= 0)
        & (result["relative_humidity"][~mask] <= 100)
    )
