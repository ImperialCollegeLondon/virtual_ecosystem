"""Test module for wind.py."""


import numpy as np

from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.models.abiotic.constants import AbioticConsts


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_zero_plane_displacement

    leaf_area_index = dummy_climate_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        leaf_area_index=leaf_area_index.to_numpy(),
        zero_plane_scaling_parameter=AbioticConsts.zero_plane_scaling_parameter,
    )

    np.testing.assert_allclose(result, np.array([0.0, 7.910175, 39.550874]))


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    leaf_area_index = dummy_climate_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_roughness_length_momentum(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        leaf_area_index=leaf_area_index.to_numpy(),
        zero_plane_displacement=np.array([0, 8, 43]),
        substrate_surface_drag_coefficient=(
            AbioticConsts.substrate_surface_drag_coefficient
        ),
        roughness_element_drag_coefficient=(
            AbioticConsts.roughness_element_drag_coefficient
        ),
        roughness_sublayer_depth_parameter=(
            AbioticConsts.roughness_sublayer_depth_parameter
        ),
        max_ratio_wind_to_friction_velocity=(
            AbioticConsts.max_ratio_wind_to_friction_velocity
        ),
        min_roughness_length=AbioticConsts.min_roughness_length,
        von_karman_constant=CoreConsts.von_karmans_constant,
    )

    np.testing.assert_allclose(
        result, np.array([0.003, 0.434662, 1.521318]), rtol=1e-3, atol=1e-3
    )


def test_calculate_diabatic_correction_above(dummy_climate_data):
    """Test diabatic correction factors for heat and momentum."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_diabatic_correction_above,
    )

    air_temperature = (
        dummy_climate_data.data["air_temperature"]
        .where(dummy_climate_data.data["air_temperature"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    result = calculate_diabatic_correction_above(
        molar_density_air=np.repeat(28.96, 3),
        specific_heat_air=np.repeat(1, 3),
        temperature=air_temperature.to_numpy(),
        sensible_heat_flux=dummy_climate_data.data["sensible_heat_flux_toc"].to_numpy(),
        friction_velocity=dummy_climate_data.data["friction_velocity"].to_numpy(),
        wind_heights=np.array([1, 15, 50]),
        zero_plane_displacement=np.array([0, 8, 43]),
        celsius_to_kelvin=CoreConsts.zero_Celsius,
        von_karmans_constant=CoreConsts.von_karmans_constant,
        yasuda_stability_parameter1=AbioticConsts.yasuda_stability_parameter1,
        yasuda_stability_parameter2=AbioticConsts.yasuda_stability_parameter2,
        yasuda_stability_parameter3=AbioticConsts.yasuda_stability_parameter3,
        diabatic_heat_momentum_ratio=AbioticConsts.diabatic_heat_momentum_ratio,
    )

    exp_result_h = np.array(
        [
            [0.003044, 0.026017, 0.012881],
            [0.003046, 0.026031, 0.012888],
            [0.003056, 0.026117, 0.01293],
            [0.003073, 0.026264, 0.013002],
            [0.00312, 0.026677, 0.013204],
            [0.003191, 0.027289, 0.013504],
        ]
    )
    exp_result_m = np.array(
        [
            [0.001827, 0.01561, 0.007729],
            [0.001828, 0.015619, 0.007733],
            [0.001833, 0.01567, 0.007758],
            [0.001833, 0.01567, 0.007758],
            [0.001872, 0.016006, 0.007923],
            [0.001914, 0.016374, 0.008103],
        ]
    )
    np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


def test_calculate_mean_mixing_length(dummy_climate_data):
    """Test mixing length with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_mean_mixing_length

    result = calculate_mean_mixing_length(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        zero_plane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        mixing_length_factor=AbioticConsts.mixing_length_factor,
    )

    np.testing.assert_allclose(
        result, np.array([0, 0.419, 1.467]), rtol=1e-3, atol=1e-3
    )


def test_generate_relative_turbulence_intensity(dummy_climate_data):
    """Test relative turbulence intensity."""

    from virtual_rainforest.models.abiotic.wind import (
        generate_relative_turbulence_intensity,
    )

    layer_heights = (
        dummy_climate_data.data["layer_heights"]
        .where(dummy_climate_data.data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    result = generate_relative_turbulence_intensity(
        layer_heights=layer_heights.to_numpy(),
        min_relative_turbulence_intensity=(
            AbioticConsts.min_relative_turbulence_intensity
        ),
        max_relative_turbulence_intensity=(
            AbioticConsts.max_relative_turbulence_intensity
        ),
        increasing_with_height=True,
    )

    exp_result = np.array(
        [
            [17.64, 17.64, 17.64],
            [16.56, 16.56, 16.56],
            [11.16, 11.16, 11.166],
            [5.76, 5.76, 5.76],
            [1.17, 1.17, 1.17],
            [0.414, 0.414, 0.414],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_attenuation_coefficient(dummy_climate_data):
    """Test wind attenuation coefficient with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_wind_attenuation_coefficient,
    )

    leaf_area_index = (
        dummy_climate_data.data["leaf_area_index"]
        .where(dummy_climate_data.data["leaf_area_index"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    relative_turbulence_intensity = np.array(
        [
            [17.64, 17.64, 17.64],
            [16.56, 16.56, 16.56],
            [11.16, 11.16, 11.166],
        ]
    )
    result = calculate_wind_attenuation_coefficient(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        leaf_area_index=leaf_area_index,
        mean_mixing_length=np.array([0, 0.4, 1.5]),
        drag_coefficient=AbioticConsts.drag_coefficient,
        relative_turbulence_intensity=relative_turbulence_intensity,
    )

    exp_result = np.array(
        [
            [0.0, 0.141723, 0.188964],
            [0.0, 0.150966, 0.201288],
            [0.0, 0.224014, 0.298525],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_wind_log_profile():
    """Test log wind profile."""

    from virtual_rainforest.models.abiotic.wind import wind_log_profile

    result = wind_log_profile(
        height=np.array([[1, 15, 50], [5, 20, 60]]),
        zeroplane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        diabatic_correction_momentum=np.array([-0.1, 0.0, 0.1]),
    )
    np.testing.assert_allclose(
        result,
        np.array([[5.709, 2.778, 1.627], [7.319, 3.317, 2.514]]),
        rtol=1e-3,
        atol=1e-3,
    )


def test_calculate_friction_velocity(dummy_climate_data):
    """Calculate friction velocity."""

    from virtual_rainforest.models.abiotic.wind import calculate_fricition_velocity

    result = calculate_fricition_velocity(
        wind_speed_ref=dummy_climate_data.data["wind_speed_ref"],
        reference_height=10.0,
        zeroplane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        diabatic_correction_momentum=np.array([-0.1, 0.0, 0.1]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
    )
    exp_result = np.array([0.0, 1.310997, 4.0])
    np.testing.assert_allclose(result, exp_result)


def test_calculate_wind_above_canopy():
    """Wind speed above canopy."""

    from virtual_rainforest.models.abiotic.wind import calculate_wind_above_canopy

    result = calculate_wind_above_canopy(
        friction_velocity=np.array([0, 1.3, 4]),
        wind_layer_heights=np.array([2, 12, 52]),
        zeroplane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        diabatic_correction_momentum=np.array([-0.1, 0.0, 0.1]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
        min_wind_speed_above_canopy=AbioticConsts.min_wind_speed_above_canopy,
    )

    exp_result = np.array([0.0, 7.211, 18.779])
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_canopy(dummy_climate_data):
    """Test below canopy wind profile."""

    from virtual_rainforest.models.abiotic.wind import calculate_wind_canopy

    layer_heights = (
        dummy_climate_data.data["layer_heights"]
        .where(dummy_climate_data.data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )

    result = calculate_wind_canopy(
        top_of_canopy_wind_speed=np.array([2, 5, 7]),
        wind_layer_heights=layer_heights.to_numpy(),
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        attenuation_coefficient=np.array([0.0, 0.64, 1.24]),
        min_windspeed_below_canopy=0.001,
    )

    exp_result = np.array(
        [
            [0.001, 20.438858, 4.479494],
            [0.001, 17.983199, 4.262731],
            [0.001, 9.482404, 3.326465],
            [0.001, 5.0, 2.59584],
            [0.001, 2.90211, 2.102464],
            [0.001, 2.65339, 2.030719],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)
