"""Test new abiotic model."""

import math

import numpy as np
import pytest


@pytest.mark.parametrize(
    "year, month, day, expected_jd",
    [
        (2000, 1, 1, 2451545),  # Known Julian day for January 1, 2000
        (2023, 9, 4, 2460192),  # A more recent date
        (1582, 10, 4, 2299160),  # Day before the Gregorian calendar reform
        (1582, 10, 15, 2299161),  # Day after the Gregorian calendar reform
    ],
)
def test_calculate_julian_day(year, month, day, expected_jd) -> None:
    """Test Julian day calculation."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_julian_day

    result = calculate_julian_day(year=year, month=month, day=day)
    assert result == expected_jd


@pytest.mark.parametrize(
    "julian_day, local_time, longitude, expected_solar_time",
    [
        (2460192, 12.0, -74.0060, 7.08467),  # September 4, 2023, New York City
        (2451545, 12.0, 0.0, 11.946),  # Noon UTC at Prime Meridian on January 1, 2000
        (2455197, 12.0, 100.0, 18.618),  # Example case with positive longitude
        (2455197, 12.0, -100.0, 5.285),  # Example case with negative longitude
    ],
)
def test_calculate_solar_time(
    julian_day, local_time, longitude, expected_solar_time
) -> None:
    """Test calculation of solar time."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_solar_time

    result = calculate_solar_time(julian_day, local_time, longitude)
    assert math.isclose(result, expected_solar_time, rel_tol=1e-3)


def test_calculate_solar_position():
    """Test calculation of solar position."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_solar_position

    # Test Case 1: New York City, September 4, 2024
    lat = 40.7128
    lon = -74.0060
    year = 2024
    month = 9
    day = 4
    lt = -4  # Local time offset for New York City (UTC-4)

    # Expected values
    expected_zenith = 62.11
    expected_azimuth = 174.22

    result = calculate_solar_position(lat, lon, year, month, day, lt)

    np.testing.assert_allclose(result[0], expected_zenith, atol=0.5)
    np.testing.assert_allclose(result[1], expected_azimuth, atol=0.5)


@pytest.mark.parametrize(
    "slope, aspect, zenith, azimuth, shadowmask, expected_solar_index",
    [
        # Test Case 1: Basic test with no shadowmask
        (
            30.0,
            90.0,
            45.0,
            180.0,
            False,
            math.cos(math.radians(45.0)) * math.cos(math.radians(30.0))
            + math.sin(math.radians(45.0))
            * math.sin(math.radians(30.0))
            * math.cos(math.radians(180.0 - 90.0)),
        ),
        # Test Case 2: Zen > 90 with shadowmask
        (30.0, 90.0, 95.0, 180.0, True, 0.0),
        # Test Case 3: Zen > 90 without shadowmask
        (30.0, 90.0, 95.0, 180.0, False, 0.0),
        # Test Case 4: Slope = 0
        (0.0, 90.0, 45.0, 180.0, False, math.cos(math.radians(45.0))),
    ],
)
def test_solar_index(slope, aspect, zenith, azimuth, shadowmask, expected_solar_index):
    """Test calculation of solar index."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_solar_index

    result = calculate_solar_index(
        slope=slope,
        aspect=aspect,
        zenith=zenith,
        azimuth=azimuth,
        shadowmask=shadowmask,
    )
    np.testing.assert_allclose(result, expected_solar_index, atol=1e-5)


@pytest.mark.parametrize(
    "solar_zenith_angle, temperature, relative_humidity, atm_pressure, expected",
    [
        (45.0, 25.0, 60.0, 1013.0, 635.166),
        (30.0, 20.0, 70.0, 1000.0, 781.271),
        (60.0, 15.0, 80.0, 950.0, 455.525),
        (85.0, 30.0, 50.0, 1020.0, 74.968),
    ],
)
def test_calculate_clear_sky_radiation(
    solar_zenith_angle,
    temperature,
    relative_humidity,
    atm_pressure,
    expected,
):
    """Test calculation of clear sky radiation."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_clear_sky_radiation,
    )

    computed_clear_sky_radiation = calculate_clear_sky_radiation(
        solar_zenith_angle=solar_zenith_angle,
        temperature=temperature,
        relative_humidity=relative_humidity,
        atmospheric_pressure=atm_pressure,
    )
    np.testing.assert_allclose(computed_clear_sky_radiation, expected, atol=1e-2)


@pytest.mark.parametrize(
    "solar_zenith_angle, slope_factor, solar_index, expected_coefficients",
    [
        (45.0, 1.0, 0.5, [0.70, 1.0, 0.5]),
        (30.0, 2.0, 1.0, [0.75, 0.65, 0.72]),
        (85.0, 5.0, 0.2, [2.28, 0.99, 0.91]),
    ],
)
def test_calculate_canopy_extinction_coefficients(
    solar_zenith_angle, slope_factor, solar_index, expected_coefficients
):
    """Test calculation of canopy extinction coefficients."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_canopy_extinction_coefficients,
    )

    computed_coefficients = calculate_canopy_extinction_coefficients(
        solar_zenith_angle, slope_factor, solar_index
    )
    for computed, expected in zip(computed_coefficients, expected_coefficients):
        np.testing.assert_allclose(computed, expected, atol=1e-2)


@pytest.mark.parametrize(
    "adj_lai, absorption_coeff, gma, h, ground_refl, expected",
    [
        (1.0, 0.5, 0.2, 0.3, 0.8, [-2.048, 5.621, 1.185, -0.185]),
        (5.0, 0.6, 0.3, 0.4, 0.9, [0.240, -0.025, 1.004, -0.004]),
        (0.0, 0.4, 0.1, 0.2, 0.7, [-0.275, 0.975, 1.575, -0.575]),
    ],
)
def test_calculate_diffuse_radiation_parameters(
    adj_lai,
    absorption_coeff,
    gma,
    h,
    ground_refl,
    expected,
):
    """Test calculation of diffuse radiation parameters."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_diffuse_radiation_parameters,
    )

    computed_parameters = calculate_diffuse_radiation_parameters(
        adjusted_leaf_area_index=adj_lai,
        scatter_absorption_coefficient=absorption_coeff,
        gma=gma,
        h=h,
        ground_reflectance=ground_refl,
    )
    for computed, expected in zip(computed_parameters, expected):
        np.testing.assert_allclose(computed, expected, atol=1e-2)


@pytest.mark.parametrize(
    "alai, scat_alb, scat_abs, gma, h, gref, incl, delta, k, kd, sigma, expected",
    [
        (
            1.0,
            0.3,
            0.5,
            0.1,
            0.2,
            0.7,
            1.0,
            0.3,
            0.5,
            0.4,
            5.67e-8,
            [-0.037, 1545642.023, -1437844.330, -0.0974, 2226060.190, -506483.471],
        ),
        (
            5.0,
            0.4,
            0.6,
            0.2,
            0.3,
            0.8,
            1.2,
            0.4,
            0.6,
            0.5,
            5.67e-8,
            [-0.084, 1840667.98, -197616.985, -0.228, 4083735.106, -62571.085],
        ),
        (
            0.0,
            0.35,
            0.55,
            0.18,
            0.25,
            0.75,
            1.1,
            0.35,
            0.55,
            0.45,
            5.67e-8,
            [-0.063, 1568518.376, -448147.255, -0.165, 4087654.243, -1167901.157],
        ),
    ],
)
def test_calculate_direct_radiation_parameters(
    alai, scat_alb, scat_abs, gma, h, gref, incl, delta, k, kd, sigma, expected
):
    """Test calculation of direct radiation parameters."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_direct_radiation_parameters,
    )

    computed_parameters = calculate_direct_radiation_parameters(
        adjusted_leaf_area_index=alai,
        scattering_albedo=scat_alb,
        scatter_absorption_coefficient=scat_abs,
        gma=gma,
        h=h,
        ground_reflectance=gref,
        inclination_distribution=incl,
        delta_reflectance_transmittance=delta,
        extinction_coefficient_k=k,
        extinction_coefficient_kd=kd,
        sigma=sigma,
    )
    for computed, expected in zip(computed_parameters, expected):
        np.testing.assert_allclose(computed, expected, atol=1e-2)


def test_calculate_absorbed_shortwave_radiation():
    """Test calculation of ground and canopy absorption, very basic."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_absorbed_shortwave_radiation,
    )

    # Define input parameters
    leaf_area_index = 2.0
    leaf_orientation_coefficient = 0.5
    leaf_reluctance_shortwave = 0.15
    leaf_transmittance_shortwave = 0.05
    clumping_factor = 0.9
    ground_reflectance = 0.3
    slope = 5.0
    aspect = 180.0
    latitude = 45.0
    longitude = -123.0
    year = np.array([2023], dtype=np.int32)
    month = np.array([6], dtype=np.int32)
    day = np.array([21], dtype=np.int32)
    local_time = np.array([12.0], dtype=np.float32)
    shortwave_radiation = np.array([800.0], dtype=np.float32)
    diffuse_radiation = np.array([200.0], dtype=np.float32)

    # Call the function to test
    result = calculate_absorbed_shortwave_radiation(
        leaf_area_index=leaf_area_index,
        leaf_orientation_coefficient=leaf_orientation_coefficient,
        leaf_reluctance_shortwave=leaf_reluctance_shortwave,
        leaf_transmittance_shortwave=leaf_transmittance_shortwave,
        clumping_factor=clumping_factor,
        ground_reflectance=ground_reflectance,
        slope=slope,
        aspect=aspect,
        latitude=latitude,
        longitude=longitude,
        year=year,
        month=month,
        day=day,
        local_time=local_time,
        shortwave_radiation=shortwave_radiation,
        diffuse_radiation=diffuse_radiation,
    )

    # Define expected output values
    expected_ground_absorption = np.array([551.56153])
    expected_canopy_absorption = np.array([647.2457])
    expected_albedo = np.array([0.1909])

    # Assert the results
    np.testing.assert_allclose(
        result["ground_shortwave_absorption"],
        expected_ground_absorption,
        atol=1e-3,
    )
    np.testing.assert_allclose(
        result["canopy_shortwave_absorption"],
        expected_canopy_absorption,
        atol=1e-3,
    )
    np.testing.assert_allclose(
        result["albedo"],
        expected_albedo,
        atol=1e-3,
    )


from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_calculate_molar_density_air():
    """Test calculate temperature-dependent molar desity of air."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_molar_density_air,
    )

    result = calculate_molar_density_air(
        temperature=np.array([[25.0] * 3, [20.0] * 3, [18.0] * 3]),
        atmospheric_pressure=np.full((3, 3), 96.0),
        standard_mole=CoreConsts.standard_mole,
        standard_pressure=CoreConsts.standard_pressure,
        celsius_to_kelvin=CoreConsts.zero_Celsius,
    )
    np.testing.assert_allclose(
        result,
        np.array([[38.749371] * 3, [39.410285] * 3, [39.681006] * 3]),
        rtol=1e-5,
        atol=1e-5,
    )


def test_calculate_specific_heat_air():
    """Test calculate specific heat of air."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_specific_heat_air,
    )

    constants = AbioticConsts()
    result = calculate_specific_heat_air(
        temperature=np.array([[25.0] * 3, [20.0] * 3, [18.0] * 3]),
        molar_heat_capacity_air=CoreConsts.molar_heat_capacity_air,
        specific_heat_equ_factors=constants.specific_heat_equ_factors,
    )

    exp_result = np.array([[29.2075] * 3, [29.202] * 3, [29.2] * 3])

    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_zero_plane_displacement,
    )

    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([0.0, np.nan, 7.0, 7.0]),
        zero_plane_scaling_parameter=7.5,
    )

    np.testing.assert_allclose(result, np.array([0.0, 0.0, 25.86256, 25.86256]))


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_roughness_length_momentum,
    )

    result = calculate_roughness_length_momentum(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([np.nan, 0.0, 7, 7]),
        zero_plane_displacement=np.array([0.0, 0.0, 27.58673, 27.58673]),
        substrate_surface_drag_coefficient=0.003,
        roughness_element_drag_coefficient=0.3,
        roughness_sublayer_depth_parameter=0.193,
        max_ratio_wind_to_friction_velocity=0.3,
        min_roughness_length=0.01,
        von_karman_constant=CoreConsts.von_karmans_constant,
    )

    np.testing.assert_allclose(
        result, np.array([0.01, 0.01666, 0.524479, 0.524479]), rtol=1e-3, atol=1e-3
    )
