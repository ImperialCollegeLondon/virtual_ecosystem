"""Test new abiotic model."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts


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

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_solar_time

    result = calculate_solar_time(julian_day, local_time, longitude)
    np.testing.assert_allclose(result, expected_solar_time, atol=1e-3)


def test_calculate_solar_position():
    """Test calculation of solar position."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_solar_position

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

    from virtual_ecosystem.models.abiotic.abiotic_new import (
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

    from virtual_ecosystem.models.abiotic.abiotic_new import (
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

    from virtual_ecosystem.models.abiotic.abiotic_new import (
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

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_absorbed_shortwave_radiation,
    )

    # Define input parameters
    plant_area_index = np.repeat(2.0, 3)
    leaf_orientation_coefficient = np.repeat(0.5, 3)
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
    shortwave_radiation = np.repeat(800.0, 3)
    diffuse_radiation = np.repeat(200.0, 3)
    leaf_inclination_angle_coefficient = 5.0

    # Call the function to test
    result = calculate_absorbed_shortwave_radiation(
        plant_area_index=plant_area_index,
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
        plant_area_index=np.array([0.0, np.nan, 7.0, 7.0]),
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
        plant_area_index=np.array([np.nan, 0.0, 7, 7]),
        zero_plane_displacement=np.array([0.0, 0.0, 27.58673, 27.58673]),
        diabatic_correction_heat=np.array([0.0, 0.0, 0.0, 0.0]),
        substrate_surface_drag_coefficient=0.003,
        drag_coefficient=0.2,
        von_karman_constant=0.4,
        min_roughness_length=0.01,
    )

    np.testing.assert_allclose(
        result, np.array([0.01, 0.020206, 1.497673, 1.497673]), rtol=1e-3, atol=1e-3
    )


@pytest.mark.parametrize(
    "air_temperature, friction_velocity, sensible_heat_flux, raises, expected",
    [
        (
            np.repeat(25.0, 3),
            np.repeat(0.5, 3),
            np.repeat(100.0, 3),
            does_not_raise(),
            np.repeat(-114.541571, 3),
        ),
        (
            np.repeat(15.0, 3),
            np.repeat(0.1, 3),
            np.repeat(-50.0, 3),
            does_not_raise(),
            np.repeat(1.771197, 3),
        ),
        (
            np.repeat(10.0, 3),
            np.repeat(0.3, 3),
            np.repeat(0.0, 3),
            pytest.raises(ValueError),
            (),
        ),
        (
            np.repeat(-10.0, 3),
            np.repeat(0.6, 3),
            np.repeat(150.0, 3),
            does_not_raise(),
            np.repeat(-116.461982, 3),
        ),
    ],
)
def test_calculate_monin_obukov_length(
    air_temperature,
    friction_velocity,
    sensible_heat_flux,
    raises,
    expected,
):
    """Test calculation of Monin-Obukov length."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_monin_obukov_length,
    )

    with raises:
        result = calculate_monin_obukov_length(
            air_temperature=air_temperature,
            friction_velocity=friction_velocity,
            sensible_heat_flux=sensible_heat_flux,
            zero_degree=273.15,
            specific_heat_air=1005,
            density_air=1.2,
            von_karman_constant=0.4,
            gravity=9.81,
        )
        np.testing.assert_allclose(result, expected, atol=1e-3)


@pytest.mark.parametrize(
    "reference_height, zero_plane_displacement, monin_obukov_length, expected",
    [
        (  # Typical case with positive zeta
            np.repeat(10.0, 3),
            np.repeat(10, 3),
            np.repeat(50.0, 3),
            np.repeat(0.0, 3),
        ),
        (  # Typical case with positive zeta
            np.repeat(50.0, 3),
            np.repeat(30, 3),
            np.repeat(60.0, 3),
            np.repeat(0.333, 3),
        ),
        (  # Case with zero zeta
            np.repeat(10.0, 3),
            np.repeat(10, 3),
            np.repeat(1.0, 3),
            np.repeat(0.0, 3),
        ),
        (  # Case with negative Monin-Obukov length
            np.repeat(10.0, 3),
            np.repeat(5, 3),
            np.repeat(-5.0, 3),
            np.repeat(-1.0, 3),
        ),
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
            np.repeat(0.5, 3),
            "Businger_1971",
            np.repeat(-3.9, 3),
            np.repeat(-3.0, 3),
        ),  # Example for stable conditions, Businger_1971
        (
            np.repeat(0.5, 3),
            "Dyer_1970",
            np.repeat(-2.5, 3),
            np.repeat(-2.5, 3),
        ),  # Example for stable conditions, Dyer_1970
        (
            np.repeat(-0.5, 3),
            "Businger_1971",
            np.repeat(1.106216, 3),
            np.repeat(0.87485, 3),
        ),  # Unstable conditions, Businger_1971
        (
            np.repeat(-0.5, 3),
            "Dyer_1970",
            np.repeat(1.38629, 3),
            np.repeat(0.793359, 3),
        ),  # Unstable conditions, Dyer_1970
        (
            np.repeat(0.0, 3),
            "Businger_1971",
            np.repeat(0.0, 3),
            np.repeat(0.0, 3),
        ),  # Edge case for zero stability parameter, Businger_1971
        (
            np.repeat(0.0, 3),
            "Dyer_1970",
            np.repeat(0.0, 3),
            np.repeat(0.0, 3),
        ),  # Edge case for zero stability parameter, Dyer_1970
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
        (np.repeat(-0.5, 3), np.repeat(0.5, 3)),  # Unstable case
        (np.repeat(0.0, 3), np.repeat(1.0, 3)),  # Neutral case
        (np.repeat(1.0, 3), np.repeat(1.5, 3)),  # Stable case
    ],
)
def test_calculate_diabatic_influence_heat(stability_parameter, expected_phih):
    """Test calculation of diabatic influencing factor for heat."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_diabatic_influence_heat,
    )

    result = calculate_diabatic_influence_heat(stability_parameter=stability_parameter)
    np.testing.assert_allclose(result, expected_phih, atol=1e-6)


@pytest.mark.parametrize(
    "leaf_dimension, sensible_heat_flux, expected_gha",
    [
        (0.05, np.repeat(100.0, 3), np.repeat(0.168252, 3)),  # Typical case
        (0.01, np.repeat(50.0, 3), np.repeat(0.202092, 3)),  # Smaller leaf, lower flux
        (0.1, np.repeat(200.0, 3), np.repeat(0.168252, 3)),  # Larger leaf, higher flux
    ],
)
def test_calculate_free_convection(leaf_dimension, sensible_heat_flux, expected_gha):
    """Test calculation of free convection gha."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_free_convection,
    )

    result = calculate_free_convection(
        leaf_dimension=leaf_dimension, sensible_heat_flux=sensible_heat_flux
    )
    np.testing.assert_allclose(result, expected_gha, atol=1e-6)


@pytest.mark.parametrize(
    "ustar, d, zm, ph, psih, gmin, expected_conductance",
    [
        (
            np.repeat(0.3, 3),
            np.repeat(2, 3),
            np.repeat(0.1, 3),
            np.repeat(1.0, 3),
            np.repeat(0.1, 3),
            np.repeat(0.05, 3),
            np.repeat(0.05, 3),
        ),  # Typical case
        (
            np.repeat(0.2, 3),
            np.repeat(1.5, 3),
            np.repeat(0.05, 3),
            np.repeat(0.9, 3),
            np.repeat(0.05, 3),
            np.repeat(0.04, 3),
            np.repeat(0.04, 3),
        ),  # Low friction velocity, height
        (
            np.repeat(0.4, 3),
            np.repeat(2.5, 3),
            np.repeat(0.15, 3),
            np.repeat(1.2, 3),
            np.repeat(0.2, 3),
            np.repeat(0.06, 3),
            np.repeat(0.06, 3),
        ),  # High friction velocity and height
        (
            np.repeat(0.1, 3),
            np.repeat(1.0, 3),
            np.repeat(0.05, 3),
            np.repeat(0.8, 3),
            np.repeat(0.02, 3),
            np.repeat(0.1, 3),
            np.repeat(0.1, 3),
        ),  # Edge case to ensure conductance is not less than gmin
    ],
)
def test_calculate_molar_conductance_above_canopy(
    ustar, d, zm, ph, psih, gmin, expected_conductance
):
    """Test calculation of molar conductance above canopy."""
    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_molar_conductance_above_canopy,
    )

    result = calculate_molar_conductance_above_canopy(
        friction_velocity=ustar,
        zero_plane_displacement=d,
        roughness_length_momentum=zm,
        reference_height=10.0,
        molar_density_air=ph,
        diabatic_correction_heat=psih,
        minimum_conductance=gmin,
        von_karmans_constant=0.4,
    )
    np.testing.assert_allclose(result, expected_conductance, atol=1e-6)


def test_calculate_stomatal_conductance():
    """Test calculation of stomatal conductance."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_stomatal_conductance,
    )

    # Define test input values
    shortwave_radiation = np.array([1000.0, 500.0, 0.0])
    maximum_stomatal_conductance = 0.3
    half_saturation_stomatal_conductance = 100.0

    # Expected stomatal conductance value
    expected_conductance = np.array([0.293617, 0.2875, 0.0])

    actual_conductance = calculate_stomatal_conductance(
        shortwave_radiation=shortwave_radiation,
        maximum_stomatal_conductance=maximum_stomatal_conductance,
        half_saturation_stomatal_conductance=half_saturation_stomatal_conductance,
    )

    np.testing.assert_allclose(actual_conductance, expected_conductance, rtol=1e-4)


@pytest.mark.parametrize(
    "air_temperature, effective_vapour_pressure_air, expected_dewpoint_temperature",
    [
        (np.repeat(20.0, 3), np.repeat(2.5, 3), np.repeat(21.304722, 3)),
        (np.repeat(-10.0, 3), np.repeat(0.8, 3), np.repeat(3.32904, 3)),
        (np.repeat(0.0, 3), np.repeat(1.0, 3), np.repeat(6.950734, 3)),
    ],
)
def test_calculate_dewpoint_temperature(
    air_temperature,
    effective_vapour_pressure_air,
    expected_dewpoint_temperature,
):
    """Test calculation of dewpoint temperature."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_dewpoint_temperature,
    )

    result = calculate_dewpoint_temperature(
        air_temperature=air_temperature,
        effective_vapour_pressure_air=effective_vapour_pressure_air,
    )

    np.testing.assert_allclose(result, expected_dewpoint_temperature, atol=1e-2)


def test_calculate_saturation_vapour_pressure():
    """Test calculation of saturation vapour pressure."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_saturation_vapour_pressure,
    )

    constants = AbioticSimpleConsts()
    air_temperature = np.repeat(20.0, 3)

    result = calculate_saturation_vapour_pressure(
        temperature=air_temperature,
        saturation_vapour_pressure_factors=(
            constants.saturation_vapour_pressure_factors
        ),
    )

    exp_output = np.repeat(1.094129, 3)
    np.testing.assert_allclose(result, exp_output)


def test_calculate_latent_heat_vapourisation():
    """Test calculation of latent heat of vapourization."""

    from virtual_ecosystem.models.abiotic.abiotic_tools import (
        calculate_latent_heat_vapourisation,
    )

    constants = AbioticConsts()
    result = calculate_latent_heat_vapourisation(
        temperature=np.array([[25.0] * 3, [20.0] * 3, [18.0] * 3]),
        celsius_to_kelvin=CoreConsts.zero_Celsius,
        latent_heat_vap_equ_factors=constants.latent_heat_vap_equ_factors,
    )
    exp_result = np.array([[2442.447596] * 3, [2453.174942] * 3, [2457.589459] * 3])

    np.testing.assert_allclose(result, exp_result, rtol=1e-5, atol=1e-5)


def test_calculate_surface_temperature():
    """Test calculation of surface temperature."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_surface_temperature,
    )

    core_consts = CoreConsts()
    abiotic_consts = AbioticConsts()

    result = calculate_surface_temperature(
        absorbed_shortwave_radiation=np.repeat(400, 3),
        heat_conductivity=np.repeat(0.2, 3),
        vapour_conductivity=np.repeat(0.01, 3),
        surface_temperature=np.repeat(25.0, 3),
        temperature_average_air_surface=np.repeat(20.0, 3),  # tair+tleaf/2
        atmospheric_pressure=np.repeat(101.3, 3),
        effective_vapour_pressure_air=np.repeat(1.2, 3),
        surface_emissivity=0.9,
        ground_heat_flux=np.repeat(30.0, 3),
        relative_humidity=np.repeat(0.6, 3),
        stefan_boltzmann_constant=core_consts.stefan_boltzmann_constant,
        celsius_to_kelvin=core_consts.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_consts.latent_heat_vap_equ_factors,
        molar_heat_capacity_air=29.1,
        specific_heat_equ_factors=abiotic_consts.specific_heat_equ_factors,
        saturation_vapour_pressure_factors=[0.61078, 7.5, 237.3],
    )
    exp_result = np.repeat(21.96655, 3)

    np.testing.assert_allclose(result, exp_result, atol=1e-5)


@pytest.mark.parametrize(
    "hourly, stat, expected",
    [
        # Test case 1: max
        (np.arange(1, 25), "max", np.array([24] * 24)),
        # Test case 2: min
        (np.arange(24, 0, -1), "min", np.array([1] * 24)),
        # Test case 3: mean
        (np.arange(1, 25), "mean", np.array([12.0] * 24)),
    ],
)
def test_hour_to_day(hourly, stat, expected):
    """Test calculation of daily from hourly with replication."""

    from virtual_ecosystem.models.abiotic.abiotic_new import hour_to_day

    result = hour_to_day(hourly, stat)
    np.testing.assert_allclose(result, expected)


def test_hour_to_day_invalid_stat():
    """Test exceptions of daily from hourly with replication."""

    from virtual_ecosystem.models.abiotic.abiotic_new import hour_to_day

    hourly_data = np.arange(1, 25)

    # Assert that calling the function with an invalid statistic raises an error
    with pytest.raises(ValueError, match="Invalid statistic"):
        hour_to_day(hourly_data, "invalid_stat")


@pytest.mark.parametrize(
    "stat, expected",
    [
        ("max", np.array([4, 6])),
        ("min", np.array([1, 3])),
        ("mean", np.array([2.5, 4.5])),
        ("sum", np.array([60, 108])),
    ],
)
def test_hour_to_day_no_replication(stat, expected):
    """Test calculation of daily from hourly without replication."""

    from virtual_ecosystem.models.abiotic.abiotic_new import hour_to_day_no_replication

    hourly = np.array([1, 2, 3, 4] * 6 + [3, 4, 5, 6] * 6)  # 48 hours

    result = hour_to_day_no_replication(hourly_data=hourly, output_statistic=stat)

    np.testing.assert_allclose(result, expected)


@pytest.mark.parametrize(
    "hourly, stat, expected_exception",
    [
        (
            np.array([1, 2, 3, 4] * 5 + [1]),
            "max",
            ValueError,
        ),  # Not multiple of 24
        (
            np.array([1, 2, 3, 4] * 6),
            "invalid_stat",
            ValueError,
        ),  # Invalid stat
    ],
)
def test_hour_to_day_no_replication_exceptions(hourly, stat, expected_exception):
    """Test exceptions of daily from hourly without replication."""

    from virtual_ecosystem.models.abiotic.abiotic_new import hour_to_day_no_replication

    with pytest.raises(expected_exception):
        hour_to_day_no_replication(hourly_data=hourly, output_statistic=stat)


@pytest.mark.parametrize(
    "values, window_size, expected",
    [
        (np.array([1, 2, 3, 4, 5]), 2, np.array([3.0, 1.5, 2.5, 3.5, 4.5])),
        (np.array([1, 2, 3, 4, 5]), 3, np.array([3.333333, 2.666667, 2.0, 3.0, 4.0])),
        (np.array([10, 20, 30, 40, 50]), 2, np.array([30.0, 15.0, 25.0, 35.0, 45.0])),
    ],
)  # TODO check
def test_calculate_moving_average(values, window_size, expected):
    """Test calculation of moving average."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_moving_average

    result = calculate_moving_average(values, window_size)
    np.testing.assert_array_almost_equal(result, expected)


@pytest.mark.parametrize(
    "values, window_size",
    [
        (np.array([1, 2, 3], dtype=np.float64), 4),  # Window size larger than the array
    ],
)
def test_calculate_moving_average_exceptions(values, window_size):
    """Test exceptions of moving average."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_moving_average

    with pytest.raises(ValueError):
        calculate_moving_average(values, window_size)


@pytest.mark.parametrize(
    "hourly_values, window_size, expected",
    [
        # 1 year of random hourly data
        (
            np.random.rand(365 * 24),
            91,
            None,  # We won't check expected value here, just validate length later
        ),
        # Edge case with constant data
        (
            np.array([2.0] * 24 * 365),  # 1 year of constant data
            91,
            np.repeat([2.0], 24 * 365),  # All means are 2.0, replicated for each hour
        ),
    ],
)
def test_calculate_yearly_moving_average(hourly_values, window_size, expected):
    """Test calcualtion of yearly moving average."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_yearly_moving_average,
    )

    if expected is not None:
        result = calculate_yearly_moving_average(hourly_values, window_size)
        np.testing.assert_allclose(result, expected, rtol=1e-4)
    else:
        result_large = calculate_yearly_moving_average(hourly_values, window_size)
        assert (
            len(result_large) == 365 * 24
        )  # Ensure output has the same length as input


# Mock input data for the test
def generate_test_data(num_cells, num_hours):
    """Generate test data for ground heat flux."""
    soil_surface_temperature = [
        np.random.uniform(10, 30, num_hours) for _ in range(num_cells)
    ]
    soil_moisture = [np.random.uniform(0.1, 0.3, num_hours) for _ in range(num_cells)]
    return soil_surface_temperature, soil_moisture


# Test function for calculate_ground_heat_flux
def test_calculate_ground_heat_flux():
    """Test calculation of ground heat flux."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_ground_heat_flux

    num_cells = 5  # Number of grid cells
    num_hours = 24 * 365  # Number of hours in a year

    # Generate test data
    soil_surface_temperature, soil_moisture = generate_test_data(num_cells, num_hours)

    # Set constant parameters for the test
    bulk_density_soil = 1.3  # g/cm³
    volumetric_mineral_content = 0.4  # Volumetric mineral content
    volumetric_quartz_content = 0.2  # Volumetric quartz content
    mass_fraction_clay = 0.1  # Mass fraction of clay

    # Call the function
    result = calculate_ground_heat_flux(
        soil_surface_temperature,
        soil_moisture,
        bulk_density_soil,
        volumetric_mineral_content,
        volumetric_quartz_content,
        mass_fraction_clay,
        calculate_yearly_flux=True,
        window_size_yearly=30,  # Example window size
    )

    # Check that the result contains the expected keys
    assert "ground_heat_flux" in result
    assert "min_ground_heat_flux" in result
    assert "max_ground_heat_flux" in result

    # Check that the output lists have the same length as the number of cells
    assert len(result["ground_heat_flux"]) == num_cells
    assert len(result["min_ground_heat_flux"]) == num_cells
    assert len(result["max_ground_heat_flux"]) == num_cells

    # Optionally check the shape of each output array
    for ghf in result["ground_heat_flux"]:
        assert ghf.shape == (num_hours,)
    for minghf in result["min_ground_heat_flux"]:
        assert minghf.shape == (num_hours,)
    for maxghf in result["max_ground_heat_flux"]:
        assert maxghf.shape == (num_hours,)


@pytest.fixture
def mock_data_soil_moisture():
    """Generate test data for soil moisture."""
    # Example input data, with 24 hourly values for 2 days (48 hours)
    air_temperature = np.array([15] * 24 + [16] * 24, dtype=np.float64)
    shortwave_radiation_down = np.array([200] * 24 + [150] * 24, dtype=np.float64)
    longwave_radiation_down = np.array([300] * 24 + [320] * 24, dtype=np.float64)
    precipitation = np.array([0] * 24 + [5] * 24, dtype=np.float64)
    return (
        air_temperature,
        shortwave_radiation_down,
        longwave_radiation_down,
        precipitation,
    )


def test_calculate_soil_moisture(mock_data_soil_moisture):
    """Test calculation of soil moisture."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_soil_moisture

    (
        air_temperature,
        shortwave_radiation_down,
        longwave_radiation_down,
        precipitation,
    ) = mock_data_soil_moisture

    # Model parameters
    rmu = 0.5
    mult = 0.2
    pwr = 2
    soil_moisture_capacity = 100
    soil_moisture_residual = 10
    saturated_hydraulic_conductivity = 5
    a = 0.1

    # Run the model
    soil_moisture = calculate_soil_moisture(
        air_temperature=air_temperature,
        shortwave_radiation_down=shortwave_radiation_down,
        longwave_radiation_down=longwave_radiation_down,
        precipitation=precipitation,
        infiltration_rate=rmu,
        evaporation_rate=mult,
        pwr=pwr,
        soil_moisture_capacity=soil_moisture_capacity,
        soil_moisture_residual=soil_moisture_residual,
        saturated_hydraulic_conductivity=saturated_hydraulic_conductivity,
        a=a,
    )

    # Basic checks
    assert soil_moisture is not None, "Soil moisture should not be None"
    assert isinstance(soil_moisture, np.ndarray), "Output should be a numpy array"

    # Check soil moisture values are within the specified bounds
    assert np.all(
        soil_moisture >= soil_moisture_residual
    ), "Soil moisture should not go below residual"
    assert np.all(
        soil_moisture <= soil_moisture_capacity
    ), "Soil moisture should not exceed capacity"

    # Check for correct initial condition
    assert (
        soil_moisture[0] == soil_moisture_capacity
    ), "Initial soil moisture should match capacity"


def test_calculate_longwave_radiation_weights():
    """Calculate longwave radiation transmission weights."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_longwave_radiation_weights,
    )

    plant_area_index_profile = np.array([[0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.3, 0.4]])

    expected_trg = np.array(
        [
            [0.904837, 0.740818, 0.548812, 0.367879],
            [0.904837, 0.740818, 0.548812, 0.367879],
        ]
    )
    expected_trh = np.array(
        [[0.40657, 0.496585, 0.67032, 1.0], [0.40657, 0.496585, 0.67032, 1.0]]
    )
    expected_wgt = np.array(
        [
            [
                [0.164384, 0.269172, 0.299111, 0.267334],
                [0.116503, 0.284595, 0.31625, 0.282652],
                [0.078066, 0.1907, 0.386128, 0.345106],
                [0.054863, 0.134018, 0.271359, 0.53976],
            ],
            [
                [0.164384, 0.269172, 0.299111, 0.267334],
                [0.116503, 0.284595, 0.31625, 0.282652],
                [0.078066, 0.1907, 0.386128, 0.345106],
                [0.054863, 0.134018, 0.271359, 0.53976],
            ],
        ]
    )

    result = calculate_longwave_radiation_weights(
        plant_area_index_profile=plant_area_index_profile
    )

    # Compare arrays with precision tolerance
    np.testing.assert_allclose(result["trg"], expected_trg, rtol=1e-4)
    np.testing.assert_allclose(result["trh"], expected_trh, rtol=1e-4)
    np.testing.assert_allclose(result["wgt"], expected_wgt, rtol=1e-4)


def test_calculate_longwave_radiation_below_canopy():
    """Test calculation of longwave radiation below canopy."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_longwave_radiation_below_canopy,
    )

    # Define inputs
    plant_area_index_profile = np.array([[0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.3, 0.4]])
    longwave_radiation_down = np.array([300.0, 300.0])
    ground_temperature = np.array([15.0, 15.0])
    ground_emissivity = 0.95
    vegetation_emissivity = 0.98
    leaf_temperature = np.array([[18.0, 19.0, 20.0, 21.0], [18.0, 19.0, 20.0, 21.0]])
    stefan_boltzmann_constant = 5.670374419e-8

    # Expected outputs
    expected_longwave_radiation_down = np.array(
        [
            [364.430765, 355.575311, 337.269313, 300.0],
            [364.430765, 355.575311, 337.269313, 300.0],
        ],
    )
    expected_longwave_radiation_up = np.array(
        [
            [374.030725, 379.626279, 387.648895, 397.100664],
            [374.030725, 379.626279, 387.648895, 397.100664],
        ]
    )

    # Call the function
    result = calculate_longwave_radiation_below_canopy(
        plant_area_index_profile=plant_area_index_profile,
        longwave_radiation_down=longwave_radiation_down,
        ground_temperature=ground_temperature,
        ground_emissivity=ground_emissivity,
        vegetation_emissivity=vegetation_emissivity,
        leaf_temperature=leaf_temperature,
        stefan_boltzmann_constant=stefan_boltzmann_constant,
    )

    # Compare arrays with precision tolerance
    np.testing.assert_allclose(
        result["longwave_radiation_down"], expected_longwave_radiation_down, rtol=1e-4
    )
    np.testing.assert_allclose(
        result["longwave_radiation_up"], expected_longwave_radiation_up, rtol=1e-4
    )


def test_calculate_canopy_wind():
    """Test calculation of canopy wind."""

    from virtual_ecosystem.models.abiotic.abiotic_new import calculate_canopy_wind

    # Define test input data
    hgt = np.array([10.0, 15.0, 20.0])  # Heights for each grid cell
    paii = np.array(
        [
            [0.5, 0.3, 0.2, 0.1],
            [0.4, 0.4, 0.2, 0.1],
            [0.3, 0.5, 0.2, 0.1],
        ]
    )

    # Call the function
    ui = calculate_canopy_wind(canopy_height=hgt, plant_area_index_profile=paii)

    # Check output shape
    assert ui.shape == paii.shape

    # Canopy wind coefficients should generally be positive
    assert np.all(ui >= 0)

    # Check that the wind shelter coefficient decreases with height
    for i in range(ui.shape[0]):
        assert np.all(np.diff(ui[i, :]) >= 0)

    # Check if bottom wind profiles are lower than top ones
    assert np.all(ui[:, 0] < ui[:, -1])

    np.testing.assert_allclose(
        ui,
        np.array(
            [
                [0.214505, 0.424326, 0.689999, 1.0],
                [0.215855, 0.386532, 0.692166, 1.0],
                [0.214505, 0.348808, 0.689999, 1.0],
            ],
        ),
        rtol=1e-4,
    )


def test_calculate_canopy_heat_fluxes():
    """Test calculation of canopy heat fluxes."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_canopy_heat_fluxes,
    )

    # Define test inputs

    num_cells, num_layers = 2, 3

    wind_speed_ref = np.repeat(2.0, num_cells)
    atmospheric_pressure = np.repeat(101.325, num_cells)
    shortwave_radiation_par = np.random.uniform(100, 300, (num_cells, num_layers))
    shortwave_radiation_absorbed = np.random.uniform(100, 300, (num_cells, num_layers))
    longwave_radiation_down = np.random.uniform(300, 400, (num_cells, num_layers))
    longwave_radiation_up = np.random.uniform(300, 400, (num_cells, num_layers))
    wc = np.random.uniform(0.5, 1.5, (num_cells, num_layers))
    leaf_dimension = 0.05
    maximum_stomatal_conductance = 0.01
    half_saturation_stomatal_conductance = 100
    vegetation_emissivity = 0.95
    leaf_temperature = np.random.uniform(15, 25, (num_cells, num_layers))
    air_temperature = np.random.uniform(20, 30, (num_cells, num_layers))
    relative_humidity = np.random.uniform(0.40, 0.60, (num_cells, num_layers))
    effective_vapour_pressure_air = np.random.uniform(
        1000, 2000, (num_cells, num_layers)
    )
    wet_surface_fraction = 0.2

    abiotic_const = AbioticConsts()
    core_const = CoreConsts()
    simple_const = AbioticSimpleConsts()

    # Call the function
    result = calculate_canopy_heat_fluxes(
        wind_speed_ref,
        atmospheric_pressure,
        shortwave_radiation_par,
        shortwave_radiation_absorbed,
        longwave_radiation_down,
        longwave_radiation_up,
        wc,
        leaf_dimension,
        maximum_stomatal_conductance,
        half_saturation_stomatal_conductance,
        vegetation_emissivity,
        leaf_temperature,
        air_temperature,
        relative_humidity,
        effective_vapour_pressure_air,
        wet_surface_fraction,
        stefan_boltzmann_constant=core_const.stefan_boltzmann_constant,
        celsius_to_kelvin=core_const.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_const.latent_heat_vap_equ_factors,
        molar_heat_capacity_air=core_const.molar_heat_capacity_air,
        specific_heat_equ_factors=abiotic_const.specific_heat_equ_factors,
        saturation_vapour_pressure_factors=(
            simple_const.saturation_vapour_pressure_factors
        ),
    )

    # Check output shape
    assert result["sensible_heat_flux"].shape == (num_cells, num_layers)
    assert result["latent_heat_flux"].shape == (num_cells, num_layers)
    assert result["leaf_temperature"].shape == (num_cells, num_layers)
    assert result["wind_speed"].shape == (num_cells, num_layers)

    # Optionally check some specific values if the output can be predicted or ranges
    assert np.all(result["leaf_temperature"] >= leaf_temperature.min())
    assert np.all(result["leaf_temperature"] <= 40.0)


def test_calculate_friction_velocity(dummy_climate_data):
    """Calculate friction velocity."""

    from virtual_ecosystem.models.abiotic.abiotic_new import (
        calculate_friction_velocity,
    )

    result = calculate_friction_velocity(
        wind_speed_ref=(
            dummy_climate_data.data["wind_speed_ref"].isel(time_index=0).to_numpy()
        ),
        canopy_height=(dummy_climate_data["layer_heights"][1]).to_numpy(),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
        diabatic_correction_momentum=np.array([0.063098, 0.0149, 0.004855, 0.004855]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
        min_friction_velocity=0.001,
    )
    exp_result = np.array([0.053059, 0.337282, 0.431221, 0.431221])
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def mock_calculate_canopy_heat_fluxes(**kwargs):
    """Mock canopy fluxes."""
    num_layers = kwargs["leaf_temperature"].shape[0]
    return {
        "leaf_temperature": np.array([25.0 + i for i in range(num_layers)]),
        "sensible_heat_flux": np.array([50.0 + i for i in range(num_layers)]),
        "latent_heat_flux": np.array([40.0 + i for i in range(num_layers)]),
        "wind_speed": np.array([3.0, 2.5]),
    }


@pytest.fixture
def lagrangian_inputs():
    """Create inputs for lagrangian function."""
    return {
        "wind_speed_ref": np.array([2.5, 2.5]),
        "air_temperature_topofcanopy": np.array([20.0, 20.0]),
        "leaf_temperature_topofcanopy": np.array([22.0, 22.0]),
        "effective_vapour_pressure_air_topofcanopy": np.array([1.5, 1.5]),
        "atmospheric_pressure": np.array([1013.25, 1013.25]),
        "longwave_radiation_down": np.array([100.0, 110.0]),
        "shortwave_radiation": {
            "par": np.array([[600.0, 610.0, 620.0], [600.0, 610.0, 620.0]]),
            "absorbed_shortwave_radiation": np.array(
                [[300.0, 305.0, 3.10], [300.0, 305.0, 310.0]]
            ),
        },
        "wc": np.array([[0.2, 0.25, 0.27], [0.2, 0.25, 0.27]]),
        "canopy_height": np.array([10.0, 10.0]),
        "plant_area_index_sum": np.array([4.0, 4.0]),
        "leaf_dimension": 0.02,
        "vegetation_emissivity": 0.98,
        "maximum_stomatal_conductance": 0.003,
        "half_saturation_stomatal_conductance": 200.0,
        "plant_area_index_profile": np.array([[3.0, 2.5, 1.5], [3.0, 2.5, 1.5]]),
        "ground_emissivity": 0.95,
        "leaf_temperature": np.array([[22.0, 21.5, 21.0], [22.0, 21.5, 21.0]]),
        "air_temperature": np.array([[20.0, 19.5, 19.0], [20.0, 19.5, 19.0]]),
        "relative_humidity": np.array([[60.0, 65.0, 70.0], [60.0, 65, 70.0]]),
        "effective_vapour_pressure_air": np.array([[1.2, 1.1, 1.0], [1.2, 1.1, 1.0]]),
        "ground_temperature": np.array([15.0, 15]),
        "wet_surface_fraction": 0.1,
        "theta": 1.0,
        "psim": np.array([0.1, 0.1]),
        "psih": np.array([0.05, 0.05]),
        "phih": np.array([0.2, 0.2]),
        "z": np.array([5.0, 10.0]),
        "stefan_boltzmann_constant": 5.67e-8,
        "celsius_to_kelvin": 273.15,
        "latent_heat_vap_equ_factors": [1.0, 0.2],
        "molar_heat_capacity_air": 29.0,
        "specific_heat_equ_factors": [1.0, 0.2],
        "saturation_vapour_pressure_factors": [0.61078, 7.5, 237.3],
        "zero_plane_scaling_parameter": 0.7,
        "substrate_surface_drag_coefficient": 0.005,
        "drag_coefficient": 0.3,
        "min_roughness_length": 0.01,
        "von_karman_constant": 0.41,
        "min_friction_velocity": 0.1,
        "standard_mole": 44.6,
        "standard_pressure": 1013.25,
        "max_surface_air_temperature_difference": 10.0,
        "a0": 0.25,
        "a1": 1.25,
    }


def test_run_lagrangian(mocker, lagrangian_inputs):
    """Test run lagrangian model."""

    from virtual_ecosystem.models.abiotic.abiotic_new import run_lagrangian

    # Mock the external functions
    mocker.patch(
        "virtual_ecosystem.models.abiotic.abiotic_new.calculate_canopy_heat_fluxes",
        side_effect=mock_calculate_canopy_heat_fluxes,
    )

    # Run the function
    result = run_lagrangian(**lagrangian_inputs)

    # Assertions
    assert "leaf_temperature" in result
    assert "air_temperature" in result
    assert "effective_vapour_pressure_air" in result
    assert "wind_speed" in result
    assert "longwave_radiation_down" in result
    assert "longwave_radiation_up" in result
    assert isinstance(result["leaf_temperature"], np.ndarray)
    assert isinstance(result["air_temperature"], np.ndarray)
    assert isinstance(result["effective_vapour_pressure_air"], np.ndarray)

    # Check some specific values
    np.testing.assert_almost_equal(result["leaf_temperature"], np.array([25.0, 26.0]))
    np.testing.assert_almost_equal(result["air_temperature"], np.array([22.5, 23.0]))
    np.testing.assert_almost_equal(result["wind_speed"], np.array([3.0, 2.5, 2.0]))
