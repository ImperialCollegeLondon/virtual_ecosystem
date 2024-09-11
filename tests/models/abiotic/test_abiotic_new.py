"""Test new abiotic model."""

import math

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


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


@pytest.mark.parametrize(
    "air_temperature, friction_velocity, sensible_heat_flux, expected",
    [
        (25, 0.5, 100.0, -114.541571),
        (15, 0.1, -50.0, 1.771197),
        # (10, 0.3, 0.0, pytest.raises(ZeroDivisionError)),
        (-10, 0.6, 150.0, -116.461982),
    ],
)
def test_calculate_monin_obukov_length(
    air_temperature,
    friction_velocity,
    sensible_heat_flux,
    expected,
):
    """Test calculation of Monin-Obukov length."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_monin_obukov_length,
    )

    result = calculate_monin_obukov_length(
        air_temperature=air_temperature,
        friction_velocity=friction_velocity,
        sensible_heat_flux=sensible_heat_flux,
        zero_degree=273.15,
        specific_heat_air=1005,
        density_air=1.2,
        von_karman_constant=0.4,
        gravitation=9.81,
    )
    np.testing.assert_allclose(result, expected, atol=1e-3)


@pytest.mark.parametrize(
    "reference_height, zero_plane_displacement, monin_obukov_length, expected",
    [
        (10.0, 10.0, 50.0, 0.0),  # Typical case with positive zeta
        (50.0, 30.0, 60.0, 0.333),  # Typical case with positive zeta
        (10.0, 10.0, 1.0, 0.0),  # Case with zero zeta
        (10.0, 5.0, 1.0, 5.0),  # Case with positive zeta
        (10.0, 5.0, -5.0, -1.0),  # Case with negative Monin-Obukov length
        # (100, 50, 0, pytest.raises(ZeroDivisionError)), # zero Monin-Obukov length
    ],
)
def test_calculate_stability_parameter(
    reference_height, zero_plane_displacement, monin_obukov_length, expected
):
    """Test calculation of stability parameter zeta."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_stability_parameter,
    )

    result = calculate_stability_parameter(
        reference_height, zero_plane_displacement, monin_obukov_length
    )
    np.testing.assert_allclose(result, expected, atol=1e-3)


@pytest.mark.parametrize(
    "stability_parameter, stability_formulation, expected_psi_h, expected_psi_m",
    [
        (
            0.5,
            "Businger_1971",
            -3.9,
            -3.0,
        ),  # Example for stable conditions, Businger_1971
        (0.5, "Dyer_1970", -2.5, -2.5),  # Example for stable conditions, Dyer_1970
        (
            -0.5,
            "Businger_1971",
            1.106216,  # Unstable conditions, Businger_1971
            0.87485,
        ),
        (
            -0.5,
            "Dyer_1970",
            1.38629,  # Unstable conditions, Dyer_1970
            0.793359,
        ),
        (
            0.0,
            "Businger_1971",
            0.0,
            0.0,
        ),  # Edge case for zero stability parameter, Businger_1971
        (
            0.0,
            "Dyer_1970",
            0.0,
            0.0,
        ),  # Edge case for zero stability parameter, Dyer_1970
        # (
        #     1.0,
        #     "Unknown_Formulation",
        #     pytest.raises(ValueError),
        # ),  # Testing unknown formulation
    ],
)
def test_calculate_diabatic_correction_factors(
    stability_parameter, stability_formulation, expected_psi_h, expected_psi_m
):
    """Test calculation of diabatic correction factors."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_diabatic_correction_factors,
    )

    result = calculate_diabatic_correction_factors(
        stability_parameter, stability_formulation
    )
    np.testing.assert_allclose(result["psi_h"], expected_psi_h, rtol=1e-5)
    np.testing.assert_allclose(result["psi_m"], expected_psi_m, rtol=1e-5)


@pytest.mark.parametrize(
    "stability_parameter, expected_phih",
    [
        (-0.5, 0.5),  # Unstable case
        (0.0, 1.5),  # Neutral case
        (1.0, 1.5),  # Stable case
    ],
)
def calculate_diabatic_influence_heat(stability_parameter, expected_phih):
    """Test calculation of diabatic influencing factor for heat."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_diabatic_influence_heat,
    )

    result = calculate_diabatic_influence_heat(stability_parameter=stability_parameter)
    np.testing.assert_allclose(result, expected_phih, atol=1e-6)


@pytest.mark.parametrize(
    "leaf_dimension, sensible_heat_flux, expected_gha",
    [
        (0.05, 100.0, 0.168252),  # Typical case
        (0.01, 50.0, 0.202092),  # Smaller leaf, lower flux
        (0.1, 200.0, 0.168252),  # Larger leaf, higher flux
        (0.02, 10.0, 0.1),  # Edge case where gha might be less than 0.1, ensure clipped
    ],
)
def calculate_free_convection(leaf_dimension, sensible_heat_flux, expected_gha):
    """Test calculation of free convection gha."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_free_convection,
    )

    result = calculate_free_convection(
        leaf_dimension=leaf_dimension, sensible_heat_flux=sensible_heat_flux
    )
    np.testing.assert_allclose(result, expected_gha, atol=1e-6)


@pytest.mark.parametrize(
    "ustar, d, zm, rh, ph, psih, gmin, expected_conductance",
    [
        (0.3, 2.0, 0.1, 10.0, 1.0, 0.1, 0.05, 0.08128),  # Typical case
        (
            0.2,
            1.5,
            0.05,
            8.0,
            0.9,
            0.05,
            0.04,
            0.04769,
        ),  # Low friction velocity, height
        (
            0.4,
            2.5,
            0.15,
            12.0,
            1.2,
            0.2,
            0.06,
            0.126060,
        ),  # High friction velocity and height
        (
            0.1,
            1.0,
            0.05,
            5.0,
            0.8,
            0.02,
            0.1,
            0.1,
        ),  # Edge case to ensure conductance is not less than gmin
    ],
)
def calculate_molar_conductance_above_canopy(
    ustar, d, zm, rh, ph, psih, gmin, expected_conductance
):
    """Test calculation of molar conductance above canopy."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_molar_conductance_above_canopy,
    )

    result = calculate_molar_conductance_above_canopy(
        friction_velocity=ustar,
        zero_plane_displacement=d,
        roughness_length_momentum=zm,
        reference_height=rh,
        ph=ph,
        diabatic_correction_heat=psih,
        minimum_conductance=gmin,
    )
    np.testing.assert_allclose(result, expected_conductance, atol=1e-6)


def calculate_stomatal_conductance():
    """Test calculation of stomatal conductance."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_stomatal_conductance,
    )

    # Define test input values
    shortwave_radiation = 500.0  # W m-2
    maximum_stomatal_conductance = 0.3  # mol m-2 s-1
    half_saturation_stomatal_conductance = 100.0  # W m-2

    # Expected stomatal conductance value
    expected_conductance = 0.2875

    actual_conductance = calculate_stomatal_conductance(
        shortwave_radiation=shortwave_radiation,
        maximum_stomatal_conductance=maximum_stomatal_conductance,
        half_saturation_stomatal_conductance=half_saturation_stomatal_conductance,
    )

    np.testing.assert_allclose(actual_conductance, expected_conductance, rtol=1e-2)


@pytest.mark.parametrize(
    "air_temperature, actual_vapour_pressure, expected_dewpoint_temperature",
    [
        (20.0, 2.5, 21.304722),
        (-10.0, 0.8, 3.32904),
        (0.0, 1.0, 6.950734),
    ],
)
def test_calculate_dewpoint_temperature(
    air_temperature,
    actual_vapour_pressure,
    expected_dewpoint_temperature,
):
    """Test calculation of dewpoint temperature."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_dewpoint_temperature,
    )

    result = calculate_dewpoint_temperature(
        air_temperature=air_temperature, actual_vapour_pressure=actual_vapour_pressure
    )

    np.testing.assert_allclose(result, expected_dewpoint_temperature, atol=1e-2)


def test_calculate_saturation_vapour_pressure():
    """Test calculation of saturation vapour pressure."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_saturation_vapour_pressure,
    )
    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts

    constants = AbioticSimpleConsts()
    air_temperature = 20.0

    result = calculate_saturation_vapour_pressure(
        temperature=air_temperature,
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )

    exp_output = 1.094129
    np.testing.assert_allclose(result, exp_output)


@pytest.mark.parametrize(
    "hourly_data, output_statistic, expected_result",
    [
        # Test case for "max" statistic
        ([1, 2, 3] * 8, "max", [3] * 24),  # One day data
        ([1, 2, 3] * 8 + [4, 5, 6] * 8, "max", [3] * 24 + [6] * 24),  # Two days data
        ([10, 20, 30] * 8, "max", [30] * 24),  # All values the same in the day
        # Test case for "min" statistic
        ([3, 2, 1] * 8, "min", [1] * 24),  # One day data
        ([3, 2, 1] * 8 + [6, 5, 4] * 8, "min", [1] * 24 + [4] * 24),  # Two days data
        # Test case for "mean" statistic
        ([1] * 24, "mean", [1] * 24),  # Mean should be 1
        ([1, 2] * 12, "mean", [1.5] * 24),  # Alternating 1, 2 should give mean 1.5
        (
            [i for i in range(24)] + [i for i in range(24)],
            "mean",
            [11.5] * 24 + [11.5] * 24,
        ),  # Mean of 0-23 should be 11.5
        # Test case for invalid statistic
        (
            [1, 2, 3] * 8,
            "median",
            "Invalid statistic. Please use 'max', 'min', or 'mean'.",
        ),  # Invalid statistic
    ],
)
def test_hour_to_day(hourly_data, output_statistic, expected_result):
    """Test calculation of daily from hourly with replication."""

    from virtual_ecosystem.models.abiotic.abiotic_new import hour_to_day

    if output_statistic in ["max", "min", "mean"]:
        result = hour_to_day(hourly_data=hourly_data, output_statistic=output_statistic)
        assert np.allclose(
            result, expected_result
        ), f"Failed for output_statistic={output_statistic}"
    else:
        with pytest.raises(ValueError, match=expected_result):
            hour_to_day(hourly_data, output_statistic)


@pytest.mark.parametrize(
    "hourly_data, output_statistic, expected_result",
    [
        # Test cases for "max" statistic
        ([1, 2, 3] * 8, "max", [3]),  # One day data, max value is 3
        ([1, 2, 3] * 8 + [4, 5, 6] * 8, "max", [3, 6]),  # Two days data
        # Test cases for "min" statistic
        ([3, 2, 1] * 8, "min", [1]),  # One day data, min value is 1
        ([3, 2, 1] * 8 + [6, 5, 4] * 8, "min", [1, 4]),  # Two days data
        # Test cases for "mean" statistic
        ([1] * 24, "mean", [1]),  # Mean of 24 values of 1 is 1
        ([1, 2] * 12, "mean", [1.5]),  # Alternating 1 and 2 should give mean 1.5
        ([i for i in range(24)], "mean", [11.5]),  # Mean of 0-23 is 11.5
        # Test cases for "sum" statistic
        ([1] * 24, "sum", [24]),  # Sum of 24 values of 1 is 24
        ([i for i in range(24)], "sum", [276]),  # Sum of 0-23 is 276
        (
            [i for i in range(24)] + [i + 1 for i in range(24)],
            "sum",
            [276, 300],
        ),  # Two days with sum 276 and 300
        # Test case for invalid statistic
        (
            [1, 2, 3] * 8,
            "median",
            "Invalid statistic. Please use 'max', 'min', 'mean', or 'sum'.",
        ),  # Invalid statistic
    ],
)
def test_hour_to_day_no_replication(hourly_data, output_statistic, expected_result):
    """Test calculation of daily from hourly without replication."""

    from virtual_ecosystem.models.abiotic.abiotic_new import hour_to_day_no_replication

    if output_statistic in ["max", "min", "mean", "sum"]:
        result = hour_to_day_no_replication(
            hourly_data=hourly_data, output_statistic=output_statistic
        )
        assert np.allclose(result, expected_result)
    else:
        with pytest.raises(ValueError, match=expected_result):
            hour_to_day_no_replication(hourly_data, output_statistic)


@pytest.mark.parametrize(
    "values, window_size, expected_result",
    [
        # Test cases with typical data
        ([1, 2, 3, 4, 5], 3, [3.333333, 2.666667, 2.0, 3.0, 4.0]),  # 3 elements
        ([10, 20, 30, 40, 50], 2, [30.0, 15.0, 25.0, 35.0, 45.0]),  # 2 elements CHECK!!
        ([10, 20, 30, 40, 50], 5, [30.0, 30.0, 30.0, 30.0, 30.0]),  # entire list
        # Edge cases
        ([1], 1, [1.0]),  # Single element list
        ([1, 2], 1, [1.0, 2.0]),  # should return the same list
        # moving average with repetition
        ([1, 2, 3, 4, 5], 4, [3.25, 3.0, 2.75, 2.5, 3.5]),
    ],
)
def test_calculate_moving_average(values, window_size, expected_result):
    """Test calculation of moving average."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_moving_average

    result = calculate_moving_average(values=values, window_size=window_size)
    np.testing.assert_allclose(result, expected_result, atol=1e-6)


@pytest.mark.parametrize(
    "hourly_values, window_size, expected_result",
    [
        (
            [1] * 24 * 365,
            7,
            [1] * (24 * 365),
        ),  # moving average over a week
        (
            [1] * 24 * 365,
            30,
            [1] * (24 * 365),
        ),  # moving average over a month
        # Edge case: Single day of hourly values
        ([10] * 24, 91, [10.0] * 24),  # Only one day of data
        # Edge case: Window size larger than the number of days
        ([10] * 24 * 30, 365, [10.0] * (24 * 30)),  # Larger window than the dataset
        # Edge case: No data
        ([], 91, []),  # No data should return an empty list
    ],
)
def test_calculate_yearly_moving_average(hourly_values, window_size, expected_result):
    """Test calcualtion of yearly moving average."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_yearly_moving_average,
    )

    result = calculate_yearly_moving_average(hourly_values, window_size)
    np.testing.assert_allclose(result, expected_result, atol=1e-6)


def test_calculate_ground_heat_flux():
    """Test calculation of ground heat flux."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_ground_heat_flux

    # Define test input data
    soil_surface_temperature = [
        35.0
    ] * 8760  # Assume hourly temperature data for 1 year
    soil_moisture = [0.2] * 8760  # Constant soil moisture
    bulk_density_soil = 1.5  # g/cm^3
    volumetric_mineral_content = 0.4
    volumetric_quartz_content = 0.3
    mass_fraction_clay = 0.2
    calculate_yearly_flux = True

    expected_ground_heat_flux = [0.0] * 8760  # TODO not sure this is correct
    expected_min_ground_heat_flux = [0.0] * 8760
    expected_max_ground_heat_flux = [0.0] * 8760

    result = calculate_ground_heat_flux(
        soil_surface_temperature,
        soil_moisture,
        bulk_density_soil,
        volumetric_mineral_content,
        volumetric_quartz_content,
        mass_fraction_clay,
        calculate_yearly_flux,
    )

    # Assert the results are as expected
    assert len(result["ground_heat_flux"]) == len(soil_surface_temperature)
    assert len(result["min_ground_heat_flux"]) == len(soil_surface_temperature)
    assert len(result["max_ground_heat_flux"]) == len(soil_surface_temperature)

    np.testing.assert_allclose(
        result["ground_heat_flux"], expected_ground_heat_flux, atol=1e-2
    )
    np.testing.assert_allclose(
        result["min_ground_heat_flux"], expected_min_ground_heat_flux, atol=1e-2
    )
    np.testing.assert_allclose(
        result["max_ground_heat_flux"], expected_max_ground_heat_flux, atol=1e-2
    )
