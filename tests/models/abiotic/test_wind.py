"""Test module for abiotic.wind.py."""

import numpy as np

from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.models.abiotic.constants import AbioticConsts


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_zero_plane_displacement

    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        leaf_area_index=np.array([0, 3, 7]),
        zero_plane_scaling_parameter=7.5,
    )

    np.testing.assert_allclose(result, np.array([0.0, 25.312559, 27.58673]))


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    result = calculate_roughness_length_momentum(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        leaf_area_index=np.array([0, 3, 7]),
        zero_plane_displacement=np.array([0.0, 25.312559, 27.58673]),
        substrate_surface_drag_coefficient=0.003,
        roughness_element_drag_coefficient=0.3,
        roughness_sublayer_depth_parameter=0.193,
        max_ratio_wind_to_friction_velocity=0.3,
        min_roughness_length=0.05,
        von_karman_constant=CoreConsts.von_karmans_constant,
    )

    np.testing.assert_allclose(
        result, np.array([0.017, 1.4533, 0.9591]), rtol=1e-3, atol=1e-3
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
        sensible_heat_flux=(
            dummy_climate_data.data["sensible_heat_flux_topofcanopy"].to_numpy()
        ),
        friction_velocity=dummy_climate_data.data["friction_velocity"].to_numpy(),
        wind_heights=np.array([1, 15, 50]),
        zero_plane_displacement=np.array([0.0, 25.312559, 27.58673]),
        celsius_to_kelvin=CoreConsts.zero_Celsius,
        von_karmans_constant=CoreConsts.von_karmans_constant,
        yasuda_stability_parameter1=AbioticConsts.yasuda_stability_parameter1,
        yasuda_stability_parameter2=AbioticConsts.yasuda_stability_parameter2,
        yasuda_stability_parameter3=AbioticConsts.yasuda_stability_parameter3,
        diabatic_heat_momentum_ratio=AbioticConsts.diabatic_heat_momentum_ratio,
    )

    exp_result_h = np.array(
        [
            [0.003044, -0.036571, 0.042159],
            [0.003046, -0.03659, 0.042182],
            [0.003056, -0.036704, 0.042322],
            [0.003073, -0.036902, 0.042564],
            [0.00312, -0.037455, 0.043242],
            [0.003191, -0.038274, 0.044247],
        ]
    )
    exp_result_m = np.array(
        [
            [0.001827, -0.021943, 0.025296],
            [0.001828, -0.021954, 0.025309],
            [0.001833, -0.022023, 0.025393],
            [0.001844, -0.022141, 0.025539],
            [0.001872, -0.022473, 0.025945],
            [0.001914, -0.022964, 0.026548],
        ]
    )
    np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


def test_calculate_mean_mixing_length(dummy_climate_data):
    """Test mixing length with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_mean_mixing_length

    result = calculate_mean_mixing_length(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        zero_plane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        mixing_length_factor=AbioticConsts.mixing_length_factor,
    )

    np.testing.assert_allclose(
        result, np.array([1.35804, 1.401984, 0.925228]), rtol=1e-4, atol=1e-4
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
    result_t = generate_relative_turbulence_intensity(
        layer_heights=layer_heights.to_numpy(),
        min_relative_turbulence_intensity=0.36,
        max_relative_turbulence_intensity=0.9,
        increasing_with_height=True,
    )

    exp_result_t = np.array(
        [
            [17.64, 17.64, 17.64],
            [16.56, 16.56, 16.56],
            [11.16, 11.16, 11.166],
            [5.76, 5.76, 5.76],
            [1.17, 1.17, 1.17],
            [0.414, 0.414, 0.414],
        ]
    )
    result_f = generate_relative_turbulence_intensity(
        layer_heights=layer_heights.to_numpy(),
        min_relative_turbulence_intensity=0.36,
        max_relative_turbulence_intensity=0.9,
        increasing_with_height=False,
    )

    exp_result_f = np.array(
        [
            [-16.38, -16.38, -16.38],
            [-15.3, -15.3, -15.3],
            [-9.9, -9.9, -9.9],
            [-4.5, -4.5, -4.5],
            [0.09, 0.09, 0.09],
            [0.846, 0.846, 0.846],
        ]
    )
    np.testing.assert_allclose(result_t, exp_result_t, rtol=1e-3, atol=1e-3)
    np.testing.assert_allclose(result_f, exp_result_f, rtol=1e-3, atol=1e-3)


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
            [5.76, 5.76, 5.76],
            [1.17, 1.17, 1.17],
            [0.414, 0.414, 0.414],
        ]
    )
    result = calculate_wind_attenuation_coefficient(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        leaf_area_index=leaf_area_index,
        mean_mixing_length=np.array([1.35804, 1.401984, 0.925228]),
        drag_coefficient=AbioticConsts.drag_coefficient,
        relative_turbulence_intensity=relative_turbulence_intensity,
    )

    exp_result = np.array(
        [
            [0.133579, 0.129392, 0.196066],
            [0.142291, 0.137831, 0.208853],
            [0.211141, 0.204523, 0.309744],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_wind_log_profile(dummy_climate_data):
    """Test log wind profile."""

    from virtual_rainforest.models.abiotic.wind import wind_log_profile

    layer_heights = (
        dummy_climate_data.data["layer_heights"]
        .where(dummy_climate_data.data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    diab_correction = np.array([0.003044, -0.036571, 0.042159])
    result = wind_log_profile(
        height=layer_heights.to_numpy(),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        diabatic_correction_momentum=diab_correction,
    )

    exp_result = np.array(
        [
            [7.543322, 1.489823, 1.568535],
            [7.478785, 1.13446, 0.964925],
            [7.07333, 1.0, 1.0],
            [6.3802, 1.0, 1.0],
            [4.483127, 1.0, 1.0],
            [1.775148, 1.0, 1.0],
        ]
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_friction_velocity(dummy_climate_data):
    """Calculate friction velocity."""

    from virtual_rainforest.models.abiotic.wind import calculate_fricition_velocity

    result = calculate_fricition_velocity(
        wind_speed_ref=(
            dummy_climate_data.data["wind_speed_ref"].isel(time_index=0).to_numpy()
        ),
        reference_height=(dummy_climate_data.data["canopy_height"] + 10).to_numpy(),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        diabatic_correction_momentum=np.array([-0.1, 0.0, 0.1]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
    )
    exp_result = np.array([0.051866, 0.163879, 0.142353])
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_above_canopy(dummy_climate_data):
    """Wind speed above canopy."""

    from virtual_rainforest.models.abiotic.wind import calculate_wind_above_canopy

    result = calculate_wind_above_canopy(
        friction_velocity=np.array([0.0, 0.819397, 1.423534]),
        wind_height_above=(dummy_climate_data.data["canopy_height"] + 15).to_numpy(),
        zeroplane_displacement=np.array([0.0, 25.312559, 27.58673]),
        roughness_length_momentum=np.array([0.017, 1.4533, 0.9591]),
        diabatic_correction_momentum=np.array([0.003, 0.026, 0.013]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
        min_wind_speed_above_canopy=0.55,
    )

    exp_result = np.array([0.55, 5.590124, 10.750233])
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
        top_of_canopy_wind_speed=np.array([0.55, 5.590124, 10.750233]),
        wind_layer_heights=layer_heights.to_numpy(),
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        attenuation_coefficient=np.array([0.133579, 0.129392, 0.196066]),
        min_windspeed_below_canopy=0.001,
    )

    exp_result = np.array(
        [
            [0.55, 5.590124, 10.750233],
            [0.545427, 5.545099, 10.619302],
            [0.523128, 5.325355, 9.988183],
            [0.50174, 5.11432, 9.394572],
            [0.48425, 4.941529, 8.917824],
            [0.481428, 4.913634, 8.841656],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_profile(dummy_climate_data):
    """Test full update of wind profile."""

    from virtual_rainforest.models.abiotic.wind import calculate_wind_profile

    wind_layer_heights = (
        dummy_climate_data.data["layer_heights"]
        .where(dummy_climate_data.data["layer_heights"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    leaf_area_index = (
        dummy_climate_data.data["leaf_area_index"]
        .where(dummy_climate_data.data["leaf_area_index"].layer_roles != "soil")
        .dropna(dim="layers")
    )
    air_temperature = (
        dummy_climate_data.data["air_temperature"]
        .where(dummy_climate_data.data["air_temperature"].layer_roles != "soil")
        .dropna(dim="layers")
    )

    wind_update = calculate_wind_profile(
        canopy_height=dummy_climate_data.data["canopy_height"].to_numpy(),
        wind_height_above=(dummy_climate_data.data["canopy_height"] + 15).to_numpy(),
        wind_layer_heights=wind_layer_heights.to_numpy(),
        leaf_area_index=leaf_area_index.to_numpy(),
        air_temperature=air_temperature.to_numpy(),
        atmospheric_pressure=np.array([96, 96, 96]),
        sensible_heat_flux_topofcanopy=np.array([100, 50, 10]),
        wind_speed_ref=np.array([0, 5, 10]),
        wind_reference_height=(
            dummy_climate_data.data["canopy_height"] + 10
        ).to_numpy(),
        abiotic_constants=AbioticConsts,
        core_constants=CoreConsts,
    )

    friction_velocity_exp = np.array(
        [
            [0.0, 0.818637, 1.638679],
            [0.0, 0.81887, 1.638726],
            [0.0, 0.820036, 1.638959],
            [0.0, 0.821194, 1.639192],
            [0.0, 0.822174, 1.63939],
            [0.0, 0.822336, 1.639422],
        ]
    )
    wind_speed_exp = np.array(
        [
            [0.55, 5.536364, 11.07365],
            [0.54557, 5.491774, 10.984462],
            [0.523951, 5.274152, 10.549181],
            [0.503188, 5.065153, 10.13115],
            [0.486188, 4.89403, 9.788873],
            [0.483444, 4.866404, 9.733618],
        ]
    )

    wind_above_exp = np.array([0.55, 5.536364, 11.07365])

    np.testing.assert_allclose(
        wind_update["wind_speed_above_canopy"], wind_above_exp, rtol=1e-3, atol=1e-3
    )
    np.testing.assert_allclose(
        wind_update["friction_velocity"], friction_velocity_exp, rtol=1e-3, atol=1e-3
    )
    np.testing.assert_allclose(
        wind_update["wind_speed_canopy"], wind_speed_exp, rtol=1e-3, atol=1e-3
    )
