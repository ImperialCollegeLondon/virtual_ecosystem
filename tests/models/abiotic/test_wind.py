"""Test module for abiotic.wind.py."""

import numpy as np

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_ecosystem.models.abiotic.wind import calculate_zero_plane_displacement

    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([0.0, np.nan, 7.0]),
        zero_plane_scaling_parameter=7.5,
    )

    np.testing.assert_allclose(result, np.array([0.0, 0.0, 25.86256]))


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    result = calculate_roughness_length_momentum(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([np.nan, 0.0, 7]),
        zero_plane_displacement=np.array([0.0, 0.0, 27.58673]),
        substrate_surface_drag_coefficient=0.003,
        roughness_element_drag_coefficient=0.3,
        roughness_sublayer_depth_parameter=0.193,
        max_ratio_wind_to_friction_velocity=0.3,
        min_roughness_length=0.01,
        von_karman_constant=CoreConsts.von_karmans_constant,
    )

    np.testing.assert_allclose(
        result, np.array([0.01, 0.01666, 0.524479]), rtol=1e-3, atol=1e-3
    )


def test_calculate_diabatic_correction_above(dummy_climate_data):
    """Test diabatic correction factors for heat and momentum."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_diabatic_correction_above,
    )

    abiotic_consts = AbioticConsts()
    core_const = CoreConsts()
    result = calculate_diabatic_correction_above(
        molar_density_air=np.repeat(28.96, 3),
        specific_heat_air=np.repeat(1.0, 3),
        temperature=dummy_climate_data["air_temperature"][0].to_numpy(),
        sensible_heat_flux=(
            dummy_climate_data["sensible_heat_flux_topofcanopy"].to_numpy()
        ),
        friction_velocity=dummy_climate_data["friction_velocity"].to_numpy(),
        wind_heights=dummy_climate_data["layer_heights"][0].to_numpy(),
        zero_plane_displacement=np.array([0.0, 25.312559, 27.58673]),
        celsius_to_kelvin=core_const.zero_Celsius,
        von_karmans_constant=core_const.von_karmans_constant,
        yasuda_stability_parameters=abiotic_consts.yasuda_stability_parameters,
        diabatic_heat_momentum_ratio=abiotic_consts.diabatic_heat_momentum_ratio,
    )

    exp_result_h = np.array([0.105164, 0.024834, 0.008092])
    exp_result_m = np.array([0.063098, 0.0149, 0.004855])
    np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


def test_calculate_diabatic_correction_canopy(dummy_climate_data):
    """Test calculate diabatic correction factors for canopy."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_diabatic_correction_canopy,
    )

    abiotic_consts = AbioticConsts()
    core_consts = CoreConsts()
    air_temperature = (
        dummy_climate_data["air_temperature"]
        .where(dummy_climate_data["air_temperature"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    layer_heights = (
        dummy_climate_data["layer_heights"]
        .where(dummy_climate_data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    wind_speed = (
        dummy_climate_data["wind_speed"]
        .where(dummy_climate_data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    result = calculate_diabatic_correction_canopy(
        air_temperature=air_temperature.to_numpy(),
        wind_speed=wind_speed.to_numpy(),
        layer_heights=layer_heights.to_numpy(),
        mean_mixing_length=dummy_climate_data["mean_mixing_length"].to_numpy(),
        stable_temperature_gradient_intercept=7.4,
        stable_wind_shear_slope=4.7,
        yasuda_stability_parameters=abiotic_consts.yasuda_stability_parameters,
        richardson_bounds=abiotic_consts.richardson_bounds,
        gravity=core_consts.gravity,
        celsius_to_kelvin=core_consts.zero_Celsius,
    )
    exp_result_h = np.array([1.0, 1.0, 1.0])
    exp_result_m = np.array([1.0, 1.0, 1.0])
    np.testing.assert_allclose(result["phi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result["phi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


def test_calculate_mean_mixing_length(dummy_climate_data):
    """Test mixing length with and without vegetation."""

    from virtual_ecosystem.models.abiotic.wind import calculate_mean_mixing_length

    result = calculate_mean_mixing_length(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        zero_plane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        mixing_length_factor=AbioticConsts.mixing_length_factor,
    )

    np.testing.assert_allclose(
        result, np.array([1.284154, 1.280886, 0.836903]), rtol=1e-4, atol=1e-4
    )


def test_generate_relative_turbulence_intensity():
    """Test relative turbulence intensity for different true layers."""

    from virtual_ecosystem.models.abiotic.wind import (
        generate_relative_turbulence_intensity,
    )

    layer_heights = np.array(
        [
            [32.0, 32.0, 32.0],
            [30.0, 30.0, 30.0],
            [20.0, 20.0, np.nan],
            [10.0, np.nan, np.nan],
            [1.5, 1.5, 1.5],
            [0.1, 0.1, 0.1],
        ]
    )
    result_t = generate_relative_turbulence_intensity(
        layer_heights=layer_heights,
        min_relative_turbulence_intensity=0.36,
        max_relative_turbulence_intensity=0.9,
        increasing_with_height=True,
    )

    exp_result_t = np.array(
        [
            [17.64, 17.64, 17.64],
            [16.56, 16.56, 16.56],
            [11.16, 11.16, np.nan],
            [5.76, np.nan, np.nan],
            [1.17, 1.17, 1.17],
            [0.414, 0.414, 0.414],
        ]
    )
    result_f = generate_relative_turbulence_intensity(
        layer_heights=layer_heights,
        min_relative_turbulence_intensity=0.36,
        max_relative_turbulence_intensity=0.9,
        increasing_with_height=False,
    )

    exp_result_f = np.array(
        [
            [-16.92, -16.92, -16.92],
            [-15.84, -15.84, -15.84],
            [-10.44, -10.44, np.nan],
            [-5.04, np.nan, np.nan],
            [-0.45, -0.45, -0.45],
            [0.306, 0.306, 0.306],
        ]
    )
    np.testing.assert_allclose(result_t, exp_result_t, rtol=1e-3, atol=1e-3)
    np.testing.assert_allclose(result_f, exp_result_f, rtol=1e-3, atol=1e-3)


def test_calculate_wind_attenuation_coefficient(dummy_climate_data):
    """Test wind attenuation coefficient with different canopy layers."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_wind_attenuation_coefficient,
    )

    leaf_area_index = np.array(
        [[1.0, 1.0, 1.0], [1.0, 1.0, np.nan], [1.0, np.nan, np.nan]]
    )
    relative_turbulence_intensity = np.array(
        [
            [17.64, 17.64, 17.64],
            [16.56, 16.56, 16.56],
            [11.16, 11.16, np.nan],
            [5.76, np.nan, np.nan],
            [1.17, 1.17, 1.17],
            [0.414, 0.414, 0.414],
        ]
    )
    result = calculate_wind_attenuation_coefficient(
        canopy_height=dummy_climate_data.data["layer_heights"][1].to_numpy(),
        leaf_area_index=leaf_area_index,
        mean_mixing_length=np.array([1.35804, 1.401984, 0.925228]),
        drag_coefficient=AbioticConsts.drag_coefficient,
        relative_turbulence_intensity=relative_turbulence_intensity,
    )

    exp_result = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.12523, 0.121305, 0.183812],
            [0.133398, 0.129216, np.nan],
            [0.197945, np.nan, np.nan],
            [0.197945, 0.129216, 0.183812],
            [0.197945, 0.129216, 0.183812],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_wind_log_profile(dummy_climate_data):
    """Test log wind profile."""

    from virtual_ecosystem.models.abiotic.wind import wind_log_profile

    layer_heights = (
        dummy_climate_data["layer_heights"]
        .where(dummy_climate_data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    diab_correction = np.array([0.105164, 0.024834, 0.008092])
    result = wind_log_profile(
        height=layer_heights.to_numpy(),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        diabatic_correction_momentum=diab_correction,
    )

    exp_result = np.array(
        [
            [7.645442, 1.551228, 1.534468],
            [7.580903, 1.195884, 0.930835],
            [7.175438, np.nan, np.nan],
            [6.482291, np.nan, np.nan],
            [4.585171, np.nan, np.nan],
            [1.877121, np.nan, np.nan],
        ]
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_friction_velocity_reference_height(dummy_climate_data):
    """Calculate friction velocity."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_friction_velocity_reference_height,
    )

    result = calculate_friction_velocity_reference_height(
        wind_speed_ref=(
            dummy_climate_data.data["wind_speed_ref"].isel(time_index=0).to_numpy()
        ),
        reference_height=(dummy_climate_data["layer_heights"][1] + 10).to_numpy(),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        diabatic_correction_momentum=np.array([0.063098, 0.0149, 0.004855]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
        min_friction_velocity=0.001,
    )
    exp_result = np.array([0.051108, 0.171817, 0.155922])
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_above_canopy():
    """Wind speed above canopy."""

    from virtual_ecosystem.models.abiotic.wind import calculate_wind_above_canopy

    result = calculate_wind_above_canopy(
        friction_velocity=np.array([0.0, 0.819397, 1.423534]),
        wind_height_above=np.array([[2.0, 32.0, 32.0], [np.nan, 30.0, 30.0]]),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        diabatic_correction_momentum=np.array([0.003, 0.026, 0.013]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
        min_wind_speed_above_canopy=0.55,
    )

    exp_result = np.array([[0.55, 3.180068, 5.478385], [np.nan, 2.452148, 3.330154]])
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_canopy(dummy_climate_data):
    """Test below canopy wind profile."""

    from virtual_ecosystem.models.abiotic.wind import calculate_wind_canopy

    attenuation_coeff = np.array(
        [
            [0.12523, 0.121305, 0.183812],
            [0.133398, 0.129216, np.nan],
            [0.197945, np.nan, np.nan],
            [0.197945, 0.129216, 0.183812],
            [0.197945, 0.129216, 0.183812],
        ]
    )
    layer_heights = np.array(
        [
            [30.0, 30.0, 30.0],
            [20.0, 20.0, np.nan],
            [10.0, np.nan, np.nan],
            [1.5, 1.5, 1.5],
            [0.1, 0.1, 0.1],
        ]
    )
    result = calculate_wind_canopy(
        top_of_canopy_wind_speed=np.array([0.5, 5.590124, 10.750233]),
        wind_layer_heights=layer_heights,
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        attenuation_coefficient=attenuation_coeff,
    )

    exp_result = np.array(
        [
            [0.5, 5.590124, 10.750233],
            [0.478254, 5.354458, np.nan],
            [0.438187, np.nan, np.nan],
            [0.414288, 4.944354, 9.027776],
            [0.410478, 4.914629, 8.950668],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_profile():
    """Test full update of wind profile."""

    from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile

    leaf_area_index = np.array(
        [[1.0, 1.0, 1.0], [1.0, 1.0, np.nan], [1.0, np.nan, np.nan]]
    )
    layer_heights = np.array(
        [
            [32.0, 32.0, 32.0],
            [30.0, 30.0, 30.0],
            [20.0, 20.0, np.nan],
            [10.0, np.nan, np.nan],
            [1.5, 1.5, 1.5],
            [0.1, 0.1, 0.1],
        ]
    )
    air_temperature = np.array(
        [
            [30.0, 30.0, 30.0],
            [29.844995, 29.844995, 29.844995],
            [28.87117, 28.87117, np.nan],
            [27.206405, np.nan, np.nan],
            [22.65, 22.65, 22.65],
            [16.145945, 16.145945, 16.145945],
        ]
    )

    wind_update = calculate_wind_profile(
        canopy_height=layer_heights[1],
        wind_height_above=layer_heights[0:2],
        wind_layer_heights=layer_heights,
        leaf_area_index=leaf_area_index,
        air_temperature=air_temperature,
        atmospheric_pressure=np.array([96.0, 96.0, 96.0]),
        sensible_heat_flux_topofcanopy=np.array([100.0, 50.0, 10.0]),
        wind_speed_ref=np.array([0.1, 5.0, 10.0]),
        wind_reference_height=(layer_heights[1] + 10),
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
    )

    friction_velocity_exp = np.array([0.012793, 0.84372, 1.811774])
    wind_speed_exp = np.array(
        [
            [0.1, 3.719967, 7.722811],
            [0.1, 3.226327, 6.915169],
            [0.09551, 3.106107, np.nan],
            [0.087254, np.nan, np.nan],
            [0.082342, 2.895383, 6.414144],
            [0.08156, 2.880031, 6.39049],
        ]
    )

    np.testing.assert_allclose(
        wind_update["friction_velocity"], friction_velocity_exp, rtol=1e-3, atol=1e-3
    )
    np.testing.assert_allclose(
        wind_update["wind_speed"], wind_speed_exp, rtol=1e-3, atol=1e-3
    )
