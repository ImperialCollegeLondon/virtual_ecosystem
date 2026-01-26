"""Test module for abiotic.energy_balance.py."""

import numpy as np
import pytest

from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic.abiotic_tools import (
    compute_layer_thickness_for_varying_canopy,
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
        temperature=data["air_temperature"][canopy_index].to_numpy()
        + fixture_core_constants.zero_Celsius,
        emissivity=fixture_abiotic_constants.soil_emissivity,
        stefan_boltzmann=fixture_core_constants.stefan_boltzmann_constant,
    )

    exp_result = np.array(
        [
            [454.022275, 454.022275, 454.022275, np.nan],
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
            [-0.489356, -0.489356, -0.489356, np.nan],
            [-0.390997, -0.390997, np.nan, np.nan],
            [-0.222852, np.nan, np.nan, np.nan],
        ]
    )

    computed_flux = calculate_sensible_heat_flux(
        density_air=data["density_air"][index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][index].to_numpy(),
        air_temperature=data["air_temperature"][index].to_numpy(),
        surface_temperature=data["canopy_temperature"][index].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"].to_numpy(),
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
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
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
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"].to_numpy(),
        latent_heat_vapourisation=data["latent_heat_vapourisation"][
            canopy_index
        ].to_numpy()
        * 1000,
        leaf_emissivity=fixture_abiotic_constants.leaf_emissivity,
        stefan_boltzmann_constant=fixture_core_constants.stefan_boltzmann_constant,
        zero_Celsius=fixture_core_constants.zero_Celsius,
        seconds_to_hour=fixture_core_constants.seconds_to_hour,
        return_fluxes=False,
    )

    assert isinstance(result, np.ndarray)
    assert result.shape == (3, 4)
    assert np.isfinite(result[0, 0])


def test_energy_balance_return_fluxes(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_core_constants,
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
        aerodynamic_resistance=data["aerodynamic_resistance_canopy"].to_numpy(),
        latent_heat_vapourisation=data["latent_heat_vapourisation"][
            canopy_index
        ].to_numpy()
        * 1000,
        leaf_emissivity=fixture_abiotic_constants.leaf_emissivity,
        stefan_boltzmann_constant=fixture_core_constants.stefan_boltzmann_constant,
        zero_Celsius=fixture_core_constants.zero_Celsius,
        seconds_to_hour=fixture_core_constants.seconds_to_hour,
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
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_core_constants,
    caplog,
):
    """Test solving canopy temperature with Newton method."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        solve_canopy_temperature,
    )

    data = dummy_climate_data_varying_canopy
    canopy_index = fixture_core_components.layer_structure.index_filled_canopy
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]

    with caplog.at_level(LOGGER.level):
        result = solve_canopy_temperature(
            canopy_temperature_initial=data["canopy_temperature"][
                canopy_index
            ].to_numpy(),
            air_temperature=data["air_temperature"][canopy_index].to_numpy(),
            evapotranspiration=evapotranspiration[canopy_index].to_numpy() / 730,
            absorbed_radiation_canopy=data["shortwave_absorption"][
                canopy_index
            ].to_numpy(),
            specific_heat_air=data["specific_heat_air"][canopy_index].to_numpy(),
            density_air=data["density_air"][canopy_index].to_numpy(),
            aerodynamic_resistance=data["aerodynamic_resistance_canopy"].to_numpy(),
            latent_heat_vapourisation=data["latent_heat_vapourisation"][
                canopy_index
            ].to_numpy()
            * 1000,
            emissivity_leaf=0.96,
            stefan_boltzmann_constant=fixture_core_constants.stefan_boltzmann_constant,
            zero_Celsius=fixture_core_constants.zero_Celsius,
            seconds_to_hour=fixture_core_constants.seconds_to_hour,
            return_fluxes=False,
            maxiter=100,
        )

    messages = [record.getMessage() for record in caplog.records]
    assert any("converge" in msg for msg in messages)

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
        sensible_heat_flux=data["sensible_heat_flux"][canopy_index].to_numpy(),
        specific_heat_air=data["specific_heat_air"][canopy_index].to_numpy(),
        density_air=data["density_air"][canopy_index].to_numpy(),
        mixing_layer_thickness=above_ground_layer_thickness[1:-1],
    )

    exp_result = np.array(
        [
            [29.844995, 29.844995, 29.844995, np.nan],
            [28.87117, 28.87117, np.nan, np.nan],
            [27.206405, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(updated_air_temperature, exp_result, rtol=1e-4)


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
        cell_area=fixture_core_components.grid.cell_area,
        limits=(0, 60),
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


def test_effective_heat_capacity():
    """Test calculation of effective heat capacity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_understorey_effective_heat_capacity,
    )

    layer_thickness = np.array([0.1, 0.1, 0.1])
    leaf_area_index = np.array([0.0, 2.0, 20.0])
    leaf_mass_per_area = 0.05
    leaf_specific_heat = 3500.0
    air_volumetric_heat_capacity = 1200.0

    result = calculate_understorey_effective_heat_capacity(
        layer_thickness=layer_thickness,
        leaf_area_index=leaf_area_index,
        leaf_mass_per_area=leaf_mass_per_area,
        leaf_specific_heat=leaf_specific_heat,
        air_volumetric_heat_capacity=air_volumetric_heat_capacity,
    )

    expected_ceff = np.array([120.0, 470.0, 3620.0])

    np.testing.assert_allclose(result, expected_ceff)


def test_update_understorey_temperature_warning(caplog):
    """Test update understorey temperature warning for large temperature changes."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_understorey_temperature,
    )

    current_temperature = np.array([20.0, 15.0, 18.0])
    net_radiation = np.array([5000.0, 4000.0, 4500.0])
    sensible_heat_flux = np.array([0.0, 0.0, 0.0])
    conductive_flux = np.array([0.0, 0.0, 0.0])
    effective_heat_capacity = np.array([100.0, 150.0, 120.0])

    # Use caplog to capture the warning
    with caplog.at_level("WARNING"):
        updated_temperature = update_understorey_temperature(
            current_temperature=current_temperature,
            net_radiation=net_radiation,
            sensible_heat_flux=sensible_heat_flux,
            conductive_flux=conductive_flux,
            effective_heat_capacity=effective_heat_capacity,
            time_step_seconds=3600.0,
            latent_heat_flux=None,
            max_delta_temperature=10.0,
        )

    # Check that the warning was triggered
    assert "Large temperature change detected" in caplog.text

    # Check that temperatures increased
    assert np.all(updated_temperature > current_temperature)


def test_update_understorey_temperature():
    """Test compute understorey temperatures."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_understorey_temperature,
    )

    current_temperature = np.array([20.0, 18.0, 15.0])
    net_radiation = np.array([20.0, 18.0, 10.0])
    sensible_heat_flux = np.array([1.0, 0.5, 0.8])
    latent_heat_flux = np.array([0.1, 0.1, 0.1])
    conductive_flux = np.array([0.5, 0.5, 0.5])
    effective_heat_capacity = np.array([10000.0, 12000.0, 11000.0])
    time_step_seconds = 3600.0

    # Update temperature
    result = update_understorey_temperature(
        current_temperature=current_temperature,
        net_radiation=net_radiation,
        sensible_heat_flux=sensible_heat_flux,
        conductive_flux=conductive_flux,
        latent_heat_flux=latent_heat_flux,
        effective_heat_capacity=effective_heat_capacity,
        time_step_seconds=time_step_seconds,
        max_delta_temperature=10.0,
    )

    expected_temperature = np.array([27.416, 23.43, 18.403636])

    # Assert the temperatures match expected values
    np.testing.assert_allclose(result, expected_temperature)

    # Assert that no ΔT is unreasonably large
    assert np.all(np.abs(result - current_temperature) < 10.0)


def test_calculate_conductive_flux_understorey():
    """Test calculate conductive flux between soil and understorey."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_conductive_flux_understorey,
    )

    soil_temperature = np.array([15.0, 18.0, 20.0])
    understorey_temperature = np.array([20.0, 16.0, 22.0])
    understorey_layer_thickness = np.array([0.1, 0.15, 0.2])
    soil_thermal_conductivity = 1.2
    understorey_thermal_conductivity = 0.02

    result = calculate_conductive_flux_understorey(
        soil_temperature=soil_temperature,
        understorey_temperature=understorey_temperature,
        understorey_layer_thickness=understorey_layer_thickness,
        soil_thermal_conductivity=soil_thermal_conductivity,
        understorey_thermal_conductivity=understorey_thermal_conductivity,
    )

    # Expected: flux should be positive where understorey is warmer than soil
    exp_flux = np.array([7.745967, -2.065591, 1.549193])
    expected_flux_signs = np.sign(understorey_temperature - soil_temperature)
    actual_flux_signs = np.sign(result)
    assert np.all(actual_flux_signs == expected_flux_signs)
    np.testing.assert_allclose(result, exp_flux, rtol=1e-6)


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
