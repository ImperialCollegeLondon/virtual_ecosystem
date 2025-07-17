"""Test module for abiotic.energy_balance.py."""

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data, fixture_core_components):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    result = initialise_canopy_and_soil_fluxes(
        air_temperature=dummy_climate_data["air_temperature"],
        layer_structure=fixture_core_components.layer_structure,
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
        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.full((3, 4), 0.001))
        np.testing.assert_allclose(result[var][12].to_numpy(), np.repeat(0.001, 4))

    np.testing.assert_allclose(
        result["canopy_temperature"][1:4], dummy_climate_data["air_temperature"][1:4]
    )


def test_calculate_longwave_emission():
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    result = calculate_longwave_emission(
        temperature=np.repeat(290.0, 3),
        emissivity=AbioticConsts.soil_emissivity,
        stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
    )
    np.testing.assert_allclose(result, np.repeat(381.002069, 3), rtol=1e-04, atol=1e-04)


def test_calculate_sensible_heat_flux(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculation of sensible heat flux."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_sensible_heat_flux,
    )

    data = dummy_climate_data_varying_canopy
    index = fixture_core_components.layer_structure.index_filled_canopy
    # Compute flux
    computed_flux = calculate_sensible_heat_flux(
        density_air=data["density_air"][index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][index].to_numpy(),
        air_temperature=data["air_temperature"][index].to_numpy(),
        surface_temperature=data["canopy_temperature"][index].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"][index].to_numpy(),
    )

    # Expected result (manually calculated)
    expected_flux = np.array(
        [
            [-0.489356, -0.489356, -0.489356, -0.489356],
            [-0.390997, -0.390997, np.nan, np.nan],
            [-0.222852, np.nan, np.nan, np.nan],
        ]
    )

    # Assert all elements are close
    np.testing.assert_allclose(computed_flux, expected_flux, rtol=1e-5)


def test_calculate_aerodynamic_resistance(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculate aerodynamic resistance."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_aerodynamic_resistance,
    )

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data_varying_canopy

    result = calculate_aerodynamic_resistance(
        wind_heights=data["layer_heights"][lyr_str.index_filled_canopy],
        roughness_length=np.repeat(0.3, 4),
        zero_plane_displacement=np.array([0.0, 10.0, 15.0, 25.0]),
        friction_velocity=np.array([0.081, 0.086, 0.099, 0.099]),
        von_karman_constant=0.4,
    )
    exp_ra = np.array(
        [
            [1636.388306, 1281.796711, 966.156818, 499.702011],
            [1360.919965, 893.600893, np.nan, np.nan],
            [948.761442, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(result, exp_ra, rtol=1e-3, atol=1e-3)


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


def test_energy_balance_residual_only(dummy_climate_data, fixture_core_components):
    """Test energy balance residual without flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data
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


def test_energy_balance_return_fluxes(dummy_climate_data, fixture_core_components):
    """Test energy balance residual with flux return."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_energy_balance_residual,
    )

    data = dummy_climate_data

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


def test_solve_canopy_temperature(dummy_climate_data, fixture_core_components):
    """Test solving canopy temperature with Newton method."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        solve_canopy_temperature,
    )

    data = dummy_climate_data
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
    assert np.all((result > 0) & (result < 50))  # plausible range for °C


def test_update_air_temperature():
    """Test update air and canopy temperatures."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_air_temperature,
    )

    air_temperature = np.array([[30.0, 25.0], [28.0, 23.0]])
    canopy_temperature = np.array([[31.0, 26.0], [30.0, 25.0]])

    # Expected outputs
    expected_air_temperature = np.array([[30.0036, 25.0036], [28.0072, 23.0072]])

    # Call the function
    updated_air_temperature = update_air_temperature(
        air_temperature=air_temperature,
        surface_temperature=canopy_temperature,
        specific_heat_air=np.full((2, 2), 1006),
        density_air=np.full((2, 2), 1.293),
        aerodynamic_resistance=np.full((2, 2), 10.0),
        mixing_layer_thickness=np.full((2, 2), 10),
        time_interval=3600,
        cell_area=10000,
    )

    np.testing.assert_allclose(
        updated_air_temperature, expected_air_temperature, rtol=1e-4
    )


def test_calculate_ventilation_rate_scalar():
    """Test calculate ventilation rate scalar."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_ventilation_rate,
    )

    ra = 50.0  # s/m
    h = 20.0  # m
    expected = 1.0 / 1000.0
    result = calculate_ventilation_rate(ra, h)
    assert np.isclose(result, expected)


def test_calculate_ventilation_rate_array():
    """Test calculate ventilation rate array."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_ventilation_rate,
    )

    ra = np.array([10.0, 50.0, 0.0])  # s/m, includes a zero
    h = np.array([2.0, 20.0, 1.0])  # m
    expected = np.array([5.0e-02, 1.0e-03, 1.0e06])
    result = calculate_ventilation_rate(ra, h)
    np.testing.assert_allclose(result, expected)


def test_calculate_ventilation_rate_zero_denominator():
    """Test calculate ventilation rate scalar."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_ventilation_rate,
    )

    ra = 0.0
    h = 0.0
    result = calculate_ventilation_rate(ra, h)
    expected = 1.0 / 1e-6
    assert np.isclose(result, expected)


def test_calculate_mixing_coefficients():
    """Test mixing coefficients."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_mixing_coefficients_canopy,
    )

    layer_midpoints = np.array([[0.1, 0.5, 0.9], [0.2, 0.6, 0.8]])
    canopy_height = np.repeat(1.0, 3)
    friction_velocity = np.repeat(0.3, 3)
    k = 0.4

    expected = np.array([[0.00972, 0.015, 0.00108], [0.01536, 0.01152, 0.00384]])
    result = calculate_mixing_coefficients_canopy(
        layer_midpoints, canopy_height, friction_velocity, k
    )

    assert result.shape == layer_midpoints.shape
    assert np.all(result >= 0)
    np.testing.assert_allclose(result, expected, rtol=1e-6)


def test_mix_and_ventilate(dummy_climate_data, fixture_core_components):
    """Test mixing and ventilation."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        mix_and_ventilate,
    )

    lystr = fixture_core_components.layer_structure
    data = dummy_climate_data
    input_variable = data["relative_humidity"][lystr.index_filled_atmosphere].to_numpy()

    layer_thickness = np.array(
        [
            [2.0, 2.0, 2.0, 2.0],
            [10.0, 10.0, 10.0, 10.0],
            [5.0, 5.0, 5.0, 5.0],
            [2.0, 2.0, 2.0, 2.0],
            [0.25, 0.25, 0.25, 0.25],
        ]
    )
    exp_result = np.array(
        [
            [77.700816, 65.401632, 53.102448, 40.803264],
            [90.341644, 90.341644, 90.341644, 90.341644],
            [92.70733, 92.70733, 92.70733, 92.70733],
            [96.313381, 96.313381, 96.313381, 96.313381],
            [100.0, 100.0, 100.0, 100.0],
        ]
    )
    result = mix_and_ventilate(
        input_variable=input_variable,
        layer_thickness=layer_thickness,
        mixing_coefficient=np.full((5, 4), 0.001),
        ventilation_rate=np.array([0.01, 0.02, 0.03, 0.04]),
        time_interval=3600.0,
    )
    np.testing.assert_allclose(result, exp_result)


def test_advect_from_toplayer():
    """Test advection of moisture from top layer."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        advect_water_from_toplayer,
    )

    specific_humidity = np.array([0.010, 0.008, 0.006])
    layer_thickness = np.array([10.0, 10.0, 10.0])
    density_air = np.array([1.2, 1.1, 1.0])
    wind_speed = np.array([1.0, 0.5, 2.0])
    time_interval = 3600.0

    expected_specific_humidity = np.array([0, 0, 0])

    # Run function
    result = advect_water_from_toplayer(
        specific_humidity=specific_humidity,
        layer_thickness=layer_thickness,
        density_air=density_air,
        wind_speed=wind_speed,
        characteristic_length=100,
        time_interval=time_interval,
    )

    np.testing.assert_allclose(result, expected_specific_humidity)


def test_update_humidity_vpd():
    """Test update atmospheric humidity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_humidity_vpd,
    )

    # Define test inputs
    evapotranspiration = np.tile([0.1, 0.2, 0.3, 0.3], (3, 1))
    soil_evaporation = np.array([0.05, 0.02, 0.03, 0.04])
    saturated_vapour_pressure = np.tile([3.0, 2.5, 2.0, 2.0], (5, 1))
    specific_humidity = np.tile([0.010, 0.012, 0.014, 0.015], (5, 1))
    layer_thickness = np.array(
        [
            [2.0, 2.0, 2.0, 2.0],
            [10.0, 10.0, 10.0, 10.0],
            [5.0, 5.0, 5.0, 5.0],
            [2.0, 2.0, 2.0, 2.0],
            [0.25, 0.25, 0.25, 0.25],
        ]
    )
    atmospheric_pressure = np.tile([100.0, 95.0, 90.0, 90.0], (5, 1))
    density_air = np.tile([1.2, 1.2, 1.2, 1.2], (5, 1))
    mixing_coefficient = np.tile([0.001, 0.005, 0.01, 0.001], (5, 1))
    ventilation_rate = np.array([0.01, 0.0, 0.0, 0.02])
    wind_speed = np.array([1, 2, 0.5, 0.1])

    molecular_weight_ratio_water_to_dry_air = 0.622
    dry_air_factor = 1.0 - 0.622
    cell_area = 10000.0
    time_interval = 3600.0

    # Run function
    result = update_humidity_vpd(
        evapotranspiration=evapotranspiration,
        soil_evaporation=soil_evaporation,
        saturated_vapour_pressure=saturated_vapour_pressure,
        specific_humidity=specific_humidity,
        layer_thickness=layer_thickness,
        atmospheric_pressure=atmospheric_pressure,
        density_air=density_air,
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        wind_speed=wind_speed,
        molecular_weight_ratio_water_to_dry_air=molecular_weight_ratio_water_to_dry_air,
        dry_air_factor=dry_air_factor,
        cell_area=cell_area,
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

    # Expected trends: ET and mixing should raise humidity slightly
    assert np.all(result["specific_humidity"] >= 0.00)

    # VPD should be reduced where evapotranspiration or mixing adds moisture
    assert np.all(result["vapour_pressure_deficit"] >= 0.0)
    assert np.all(result["vapour_pressure"] <= saturated_vapour_pressure)

    # RH should be between 0 and 100
    assert np.all(
        (result["relative_humidity"] >= 0) & (result["relative_humidity"] <= 100)
    )
    np.testing.assert_allclose(result["relative_humidity"][0], np.array([0, 0, 0, 0]))
    np.testing.assert_allclose(
        result["relative_humidity"][1], np.array([100.0, 100.0, 100.0, 100.0])
    )
