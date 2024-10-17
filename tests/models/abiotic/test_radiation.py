"""Test module for abiotic.radiation.py."""

import numpy as np
import pytest

# from virtual_ecosystem.core.constants import CoreConsts
# from virtual_ecosystem.models.abiotic.constants import AbioticConsts
# from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts


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

    from virtual_ecosystem.models.abiotic.radiation import calculate_julian_day

    result = calculate_julian_day(year=year, month=month, day=day)
    assert result == expected_jd


@pytest.mark.parametrize(
    "julian_day, local_time, longitude, expected_solar_time",
    [
        (
            2460192,
            12.0,
            np.repeat(-74.0060, 3),
            np.repeat(7.08467, 3),
        ),  # September 4, 2023, New York City
        (
            2451545,
            12.0,
            np.repeat(0.0, 3),
            np.repeat(11.946, 3),
        ),  # Noon UTC at Prime Meridian on January 1, 2000
        (
            2455197,
            12.0,
            np.repeat(100.0, 3),
            np.repeat(18.618, 3),
        ),  # Example case with positive longitude
        (
            2455197,
            12.0,
            np.repeat(-100.0, 3),
            np.repeat(5.285, 3),
        ),  # Example case with negative longitude
    ],
)
def test_calculate_solar_time(
    julian_day, local_time, longitude, expected_solar_time
) -> None:
    """Test calculation of solar time."""

    from virtual_ecosystem.models.abiotic.radiation import calculate_solar_time

    result = calculate_solar_time(julian_day, local_time, longitude)
    np.testing.assert_allclose(result, expected_solar_time, atol=1e-3)


def test_calculate_solar_position():
    """Test calculation of solar position."""

    from virtual_ecosystem.models.abiotic.radiation import calculate_solar_position

    # Test Case 1: New York City, September 4, 2024
    lat = np.repeat(40.7128, 3)
    lon = np.repeat(-74.0060, 3)
    year = 2024
    month = 9
    day = 4
    lt = -4  # Local time offset for New York City (UTC-4)

    # Expected values
    expected_zenith = np.repeat(62.11, 3)
    expected_azimuth = np.repeat(174.22, 3)

    result = calculate_solar_position(lat, lon, year, month, day, lt)

    np.testing.assert_allclose(result[0], expected_zenith, atol=0.5)
    np.testing.assert_allclose(result[1], expected_azimuth, atol=0.5)


@pytest.mark.parametrize(
    "slope, aspect, zenith, azimuth, shadowmask, expected_solar_index",
    [
        # Test Case 1: Basic test with no shadowmask
        (
            np.repeat(30.0, 3),
            np.repeat(90.0, 3),
            np.repeat(45.0, 3),
            np.repeat(180.0, 3),
            False,
            np.repeat(0.612372, 3),
        ),
        # Test Case 2: Zen > 90 with shadowmask
        (
            np.repeat(30.0, 3),
            np.repeat(90.0, 3),
            np.repeat(95.0, 3),
            np.repeat(180.0, 3),
            True,
            np.repeat(0.0, 3),
        ),
        # Test Case 3: Zen > 90 without shadowmask
        (
            np.repeat(30.0, 3),
            np.repeat(90.0, 3),
            np.repeat(95.0, 3),
            np.repeat(180.0, 3),
            False,
            np.repeat(0.866025, 3),
        ),
        # Test Case 4: Slope = 0
        (
            np.repeat(0.0, 3),
            np.repeat(90.0, 3),
            np.repeat(45.0, 3),
            np.repeat(180.0, 3),
            False,
            np.repeat(0.70710, 3),
        ),
    ],
)
def test_solar_index(slope, aspect, zenith, azimuth, shadowmask, expected_solar_index):
    """Test calculation of solar index."""

    from virtual_ecosystem.models.abiotic.radiation import calculate_solar_index

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
        (
            np.repeat(45.0, 3),
            np.repeat(25.0, 3),
            np.repeat(60.0, 3),
            np.repeat(1013.0, 3),
            np.repeat(635.166, 3),
        ),
        (
            np.repeat(30.0, 3),
            np.repeat(20.0, 3),
            np.repeat(70.0, 3),
            np.repeat(1000.0, 3),
            np.repeat(781.271, 3),
        ),
        (
            np.repeat(60.0, 3),
            np.repeat(15.0, 3),
            np.repeat(80.0, 3),
            np.repeat(950.0, 3),
            np.repeat(455.525, 3),
        ),
        (
            np.repeat(85.0, 3),
            np.repeat(30.0, 3),
            np.repeat(50.0, 3),
            np.repeat(1020.0, 3),
            np.repeat(74.968, 3),
        ),
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

    from virtual_ecosystem.models.abiotic.radiation import (
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
    "solar_zenith_angle, leaf_incl_coefficient, solar_index, expected_coefficients",
    [
        (
            np.repeat(45.0, 3),
            1.0,
            np.repeat(0.5, 3),
            (np.array([[0.70, 0.7, 0.7], [1.0, 1.0, 1.0], [0.5, 0.5, 0.5]])),
        ),
        (
            np.repeat(30.0, 3),
            2.0,
            np.repeat(1.0, 3),
            (np.array([[0.75, 0.75, 0.75], [0.65, 0.65, 0.65], [0.72, 0.72, 0.72]])),
        ),
        (
            np.repeat(85.0, 3),
            5.0,
            np.repeat(0.2, 3),
            (np.array([[2.28, 2.28, 2.28], [0.99, 0.99, 0.99], [0.91, 0.91, 0.91]])),
        ),
    ],
)
def test_calculate_canopy_extinction_coefficients(
    solar_zenith_angle,
    leaf_incl_coefficient,
    solar_index,
    expected_coefficients,
):
    """Test calculation of canopy extinction coefficients."""

    from virtual_ecosystem.models.abiotic.radiation import (
        calculate_canopy_extinction_coefficients,
    )

    computed_coefficients = calculate_canopy_extinction_coefficients(
        solar_zenith_angle, leaf_incl_coefficient, solar_index
    )
    for computed, expected in zip(computed_coefficients, expected_coefficients):
        np.testing.assert_allclose(computed, expected, atol=1e-2)


@pytest.mark.parametrize(
    "adj_pai, scatter_coeff, backward_coeff, diffuse_coeff, ground_refl, expected",
    [
        (
            np.array([0.5, 1.0, 1.5]),
            0.2,
            0.3,
            0.4,
            0.6,
            [
                np.array([0.310228, 0.317483, 0.322539]),
                np.array([0.207952, 0.142654, 0.097147]),
                np.array([0.930683, 0.952449, 0.967618]),
                np.array([0.069317, 0.047551, 0.032382]),
            ],
        ),
        (
            np.array([0.1, 0.2, 0.3]),
            0.5,
            0.2,
            0.3,
            0.8,
            [
                np.array([-0.226365, -0.258451, -0.298267]),
                np.array([1.065912, 1.146128, 1.245667]),
                np.array([1.368131, 1.339416, 1.313454]),
                np.array([-0.368131, -0.339416, -0.313454]),
            ],
        ),
    ],
)
def test_calculate_diffuse_radiation_parameters(
    adj_pai, scatter_coeff, backward_coeff, diffuse_coeff, ground_refl, expected
):
    """Test calculation of diffuse radiation parameters."""

    from virtual_ecosystem.models.abiotic.radiation import (
        calculate_diffuse_radiation_parameters,
    )

    result = calculate_diffuse_radiation_parameters(
        adjusted_plant_area_index=adj_pai,
        scatter_absorption_coefficient=scatter_coeff,
        backward_scattering_coefficient=backward_coeff,
        diffuse_scattering_coefficient=diffuse_coeff,
        ground_reflectance=ground_refl,
    )

    np.testing.assert_allclose(result[0], expected[0], rtol=1e-5)
    np.testing.assert_allclose(result[1], expected[1], rtol=1e-5)
    np.testing.assert_allclose(result[2], expected[2], rtol=1e-5)
    np.testing.assert_allclose(result[3], expected[3], rtol=1e-5)


@pytest.mark.parametrize(
    "apai, scat_alb, scat_abs, back_c, diff_c, gref, incl, delt, k, kd, sg, exp",
    [
        (
            np.repeat(1.0, 3),
            0.3,
            0.5,
            0.1,
            0.2,
            0.7,
            1.0,
            0.3,
            np.repeat(0.5, 3),
            np.repeat(0.4, 3),
            5.67e-8,
            [
                np.repeat(-0.0375, 3),
                np.repeat(1545642.023, 3),
                np.repeat(-1437844.330, 3),
                np.repeat(-0.0974, 3),
                np.repeat(2226060.190, 3),
                np.repeat(-506483.471, 3),
            ],
        ),
        (
            np.repeat(0.0, 3),
            0.35,
            0.55,
            0.18,
            0.25,
            0.75,
            1.1,
            0.35,
            np.repeat(0.55, 3),
            np.repeat(0.45, 3),
            5.67e-8,
            [
                np.repeat(-0.063, 3),
                np.repeat(1568518.376, 3),
                np.repeat(-448147.255, 3),
                np.repeat(-0.165, 3),
                np.repeat(4087654.243, 3),
                np.repeat(-1167901.157, 3),
            ],
        ),
    ],
)
def test_calculate_direct_radiation_parameters(
    apai,
    scat_alb,
    scat_abs,
    back_c,
    diff_c,
    gref,
    incl,
    delt,
    k,
    kd,
    sg,
    exp,
):
    """Test calculation of direct radiation parameters."""

    from virtual_ecosystem.models.abiotic.radiation import (
        calculate_direct_radiation_parameters,
    )

    computed_parameters = calculate_direct_radiation_parameters(
        adjusted_plant_area_index=apai,
        scattering_albedo=scat_alb,
        scatter_absorption_coefficient=scat_abs,
        backward_scattering_coefficient=back_c,
        diffuse_scattering_coefficient=diff_c,
        ground_reflectance=gref,
        inclination_distribution=incl,
        delta_reflectance_transmittance=delt,
        extinction_coefficient_k=k,
        extinction_coefficient_kd=kd,
        sigma=sg,
    )
    for computed, expected in zip(computed_parameters, exp):
        np.testing.assert_allclose(computed, expected, atol=1e-2)


def test_calculate_absorbed_shortwave_radiation():
    """Test calculation of ground and canopy absorption, very basic."""

    from virtual_ecosystem.models.abiotic.radiation import (
        calculate_absorbed_shortwave_radiation,
    )

    # Define input parameters
    plant_area_index_sum = np.repeat(2.0, 3)
    leaf_orientation_coefficient = 0.5
    leaf_reluctance_shortwave = 0.15
    leaf_transmittance_shortwave = 0.05
    clumping_factor = 0.9
    ground_reflectance = 0.3
    slope = np.repeat(5.0, 3)
    aspect = np.repeat(180.0, 3)
    latitude = np.repeat(45.0, 3)
    longitude = np.repeat(-123.0, 3)
    year = np.array([2023], dtype=np.int32)
    month = np.array([6], dtype=np.int32)
    day = np.array([21], dtype=np.int32)
    local_time = np.array([12.0], dtype=np.float32)
    topofcanopy_shortwave_radiation = np.repeat(800.0, 3)
    topofcanopy_diffuse_radiation = np.repeat(200.0, 3)
    leaf_inclination_angle_coefficient = 5.0

    # Call the function to test
    result = calculate_absorbed_shortwave_radiation(
        plant_area_index_sum=plant_area_index_sum,
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
        topofcanopy_shortwave_radiation=topofcanopy_shortwave_radiation,
        topofcanopy_diffuse_radiation=topofcanopy_diffuse_radiation,
        leaf_inclination_angle_coefficient=leaf_inclination_angle_coefficient,
    )

    # Define expected output values
    expected_ground_absorption = np.repeat(551.561586, 3)
    expected_canopy_absorption = np.repeat(647.24574, 3)
    expected_albedo = np.repeat(0.190943, 3)

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


def test_calculate_canopy_longwave_emission():
    """Test calculation of canopy longwave emission."""

    from virtual_ecosystem.models.abiotic.radiation import (
        calculate_canopy_longwave_emission,
    )

    expected_emission = np.array(
        [[425.643415, 437.179768, 431.382669], [454.922015, 460.954381, 448.949052]]
    )

    # Calculate the actual emission
    result = calculate_canopy_longwave_emission(
        leaf_emissivity=0.95,
        canopy_temperature=np.array([[25, 27, 26], [30, 31, 29]]),
        stefan_boltzmann_constant=5.67e-8,
        zero_Celsius=273.15,
    )

    # Compare the result with the expected value
    np.testing.assert_allclose(result, expected_emission, rtol=1e-6)


def test_calculate_longwave_emission_ground():
    """Test calculation of ground longwave emission."""

    from virtual_ecosystem.models.abiotic.radiation import (
        calculate_longwave_emission_ground,
    )

    expected_emission = np.array([349.6, 389.16])

    # Calculate the actual emission
    result = calculate_longwave_emission_ground(
        ground_emissivity=0.92,
        radiation_transmission_coefficient=np.array([0.6, 0.7]),
        longwave_downward_radiation_sky=np.array([400, 450]),
        canopy_longwave_emission=np.array([350, 360]),
    )

    # Compare the result with the expected value
    np.testing.assert_allclose(result, expected_emission, rtol=1e-6)
