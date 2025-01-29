"""Test module for abiotic.energy_balance.py."""

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_initialise_absorbed_radiation(dummy_climate_data, fixture_core_components):
    """Test initial absorbed radiation has correct dimensions."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_absorbed_radiation,
    )

    lyr_strct = fixture_core_components.layer_structure

    leaf_area_index_true = dummy_climate_data["leaf_area_index"][
        lyr_strct.index_filled_canopy
    ]
    layer_heights_canopy = dummy_climate_data["layer_heights"][
        lyr_strct.index_filled_canopy
    ]

    result = initialise_absorbed_radiation(
        topofcanopy_radiation=dummy_climate_data["topofcanopy_radiation"]
        .isel(time_index=0)
        .to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.to_numpy(),
        light_extinction_coefficient=0.01,
    )

    exp_result = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_temperature(dummy_climate_data, fixture_core_components):
    """Test that canopy temperature is initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_temperature,
    )

    lyr_strct = fixture_core_components.layer_structure

    air_temperature = dummy_climate_data["air_temperature"][
        lyr_strct.index_filled_canopy
    ]

    absorbed_radiation = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])

    result = initialise_canopy_temperature(
        air_temperature=air_temperature,
        absorbed_radiation=absorbed_radiation,
        canopy_temperature_ini_factor=0.01,
    )
    exp_result = np.array([[29.845994] * 4, [28.872169] * 4, [27.207403] * 4])

    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data, fixture_core_components):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    result = initialise_canopy_and_soil_fluxes(
        air_temperature=dummy_climate_data["air_temperature"],
        topofcanopy_radiation=(
            dummy_climate_data["topofcanopy_radiation"].isel(time_index=0)
        ),
        leaf_area_index=dummy_climate_data["leaf_area_index"],
        layer_heights=dummy_climate_data["layer_heights"],
        layer_structure=fixture_core_components.layer_structure,
        light_extinction_coefficient=0.01,
        canopy_temperature_ini_factor=0.01,
    )

    exp_abs = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])

    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "canopy_absorption",
    ]:
        assert var in result

    np.testing.assert_allclose(
        result["canopy_absorption"][1:4].to_numpy(), exp_abs, rtol=1e-04, atol=1e-04
    )
    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.full((3, 4), 0.001))
        np.testing.assert_allclose(result[var][12].to_numpy(), np.repeat(0.001, 4))


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
    np.testing.assert_allclose(result, np.repeat(320.84384, 3), rtol=1e-04, atol=1e-04)


@pytest.mark.parametrize(
    "incoming_radiation, absorbed_radiation, longwave_emission, albedo, expected",
    [
        # Test case 1: Typical inputs
        (
            np.array([400.0, 500.0, 600.0], dtype=np.float32),
            np.array([100.0, 150.0, 200.0], dtype=np.float32),
            np.array([50.0, 75.0, 100.0], dtype=np.float32),
            0.2,
            np.array([170.0, 175.0, 180.0], dtype=np.float32),
        ),
        # Test case 2: Edge case with zero values
        (
            np.array([0.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 0.0, 0.0], dtype=np.float32),
            0.0,
            np.array([0.0, 0.0, 0.0], dtype=np.float32),
        ),
        # Test case 3: Nighttime condition with negative incoming radiation
        (
            np.array([-200.0, -150.0, -100.0], dtype=np.float32),
            np.array([50.0, 75.0, 100.0], dtype=np.float32),
            np.array([20.0, 30.0, 40.0], dtype=np.float32),
            0.1,
            np.array([-250.0, -240.0, -230.0], dtype=np.float32),
        ),
    ],
)
def test_calculate_net_radiation(
    incoming_radiation, absorbed_radiation, longwave_emission, albedo, expected
):
    """Test net radiation."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_net_radiation,
    )

    result = calculate_net_radiation(
        incoming_radiation, absorbed_radiation, longwave_emission, albedo
    )
    np.testing.assert_allclose(result, expected, rtol=1e-5)


def test_calculate_aerodynamic_resistance(dummy_climate_data, fixture_core_components):
    """Test calculate aerodynamic resistance."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_aerodynamic_resistance,
    )

    lyr_str = fixture_core_components.layer_structure

    result = calculate_aerodynamic_resistance(
        wind_heights=dummy_climate_data["layer_heights"][lyr_str.index_filled_canopy],
        roughness_length=np.repeat(0.3, 4),
        zero_plane_displacement=np.array([0.0, 10.0, 15.0, 25.0]),
        friction_velocity=np.array([0.081, 0.086, 0.099, 0.099]),
        von_karman_constant=0.4,
    )
    exp_ra = np.array(
        [
            [142.134882, 122.08445, 98.78846, 71.045725],
            [129.620527, 101.934823, 71.04573, np.nan],
            [108.227096, 0.001, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(result, exp_ra, rtol=1e-3, atol=1e-3)


def test_calculate_leaf_vapour_conductivity():
    """Test calculate leaf vapour conductivity."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_leaf_vapour_conductivity,
    )

    air_heat_conductivity = np.tile([0.5, 1.0, 2.0], 4)
    stomatal_conductivity = np.tile([0.2, 0.001, 1.0], 4)

    exp_output = np.tile([0.142857, 0.000999, 0.666667], 4)

    result = calculate_leaf_vapour_conductivity(
        air_heat_conductivity, stomatal_conductivity
    )

    np.testing.assert_allclose(result, exp_output, rtol=1e-5, atol=1e-8)


def test_calculate_latent_heat_flux():
    """Test calculate latent heat flux from canopy or soil."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_latent_heat_flux,
    )

    result = calculate_latent_heat_flux(
        latent_heat_vapourisation=2245.0,
        leaf_vapour_conductivity=np.array([[0.142857, 0.0, 0.666667]] * 4),
        effective_vapour_pressure_leaf=np.array([[0.8, 1.275543, 2.5]] * 4),
        effective_vapour_pressure_air=np.array([[1.275543, 1.275448, 1.274309]] * 4),
        atmospheric_pressure=np.full((4, 3), 96.0),
    )

    exp_result = np.array([[-1.58868, 0.0, 19.108873]] * 4)
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


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
            3600,  # time_interval (1 hour)
            2,
            np.array(
                [
                    [15.692308, 16.865385, 14.623077, 13.761538],
                    [14.415385, 15.415385, 13.415385, 12.415385],
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
            3600,  # time_interval (1 hour)
            5,
            np.array(
                [
                    [15.623077, 16.657692, 14.692308, 13.726923],
                    [14.520769, 15.520769, 13.520769, 12.520769],
                    [14.220769, 15.220769, 13.220769, 12.220769],
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


def test_update_air_canopy_temperature():
    """Test update air and canopy temperatures."""
    from virtual_ecosystem.models.abiotic.energy_balance import (
        update_air_canopy_temperature,
    )

    # Test inputs (2D arrays for layers and grid cells)
    net_radiation_canopy = np.array([[190.0, 240.0], [290.0, 340.0]])
    sensible_heat_flux_canopy = np.array([[50.0, 60.0], [70.0, 80.0]])
    latent_heat_flux_canopy = np.array([[30.0, 40.0], [50.0, 60.0]])
    air_temperature = np.array([[300.0, 295.0], [290.0, 285.0]])  # K
    canopy_temperature = np.array([[305.0, 300.0], [295.0, 290.0]])  # K
    density_air = np.array([[1.2, 1.2], [1.2, 1.2]])  # kg m-3
    specific_heat_air = np.array([[1005.0, 1005.0], [1005.0, 1005.0]])  # J kg-1 K-1

    # Expected outputs (calculated manually)
    expected_canopy_temperature = np.array(
        [[305.091211, 300.116086], [295.140962, 290.165837]]
    )
    expected_air_temperature = np.array(
        [[300.041459, 295.049751], [290.058043, 285.066335]]
    )

    # Call the function
    updated_canopy_temperature, updated_air_temperature = update_air_canopy_temperature(
        net_radiation_canopy=net_radiation_canopy,
        sensible_heat_flux_canopy=sensible_heat_flux_canopy,
        latent_heat_flux_canopy=latent_heat_flux_canopy,
        air_temperature=air_temperature,
        canopy_temperature=canopy_temperature,
        density_air=density_air,
        specific_heat_air=specific_heat_air,
    )

    # Assertions
    np.testing.assert_allclose(
        updated_canopy_temperature, expected_canopy_temperature, rtol=1e-4
    )
    np.testing.assert_allclose(
        updated_air_temperature, expected_air_temperature, rtol=1e-4
    )
