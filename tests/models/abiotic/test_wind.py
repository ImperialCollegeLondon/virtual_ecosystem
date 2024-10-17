"""Test module for abiotic.wind.py."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_ecosystem.models.abiotic.wind import calculate_zero_plane_displacement

    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([0.0, np.nan, 7.0, 7.0]),
        zero_plane_scaling_parameter=7.5,
    )

    np.testing.assert_allclose(result, np.array([0.0, 0.0, 25.86256, 25.86256]))


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_ecosystem.models.abiotic.wind import (
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
    from virtual_ecosystem.models.abiotic.wind import (
        calculate_monin_obukov_length,
    )

    with raises:
        result = calculate_monin_obukov_length(
            air_temperature=air_temperature,
            friction_velocity=friction_velocity,
            sensible_heat_flux=sensible_heat_flux,
            specific_heat_air=np.repeat(1005, 3),
            density_air=np.repeat(1.2, 3),
            zero_degree=273.15,
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
    from virtual_ecosystem.models.abiotic.wind import (
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

    from virtual_ecosystem.models.abiotic.wind import (
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
    from virtual_ecosystem.models.abiotic.wind import (
        calculate_diabatic_influence_heat,
    )

    result = calculate_diabatic_influence_heat(stability_parameter=stability_parameter)
    np.testing.assert_allclose(result, expected_phih, atol=1e-6)


# def test_calculate_diabatic_correction_above(dummy_climate_data):
#     """Test diabatic correction factors for heat and momentum."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_diabatic_correction_above,
#     )

#     abiotic_consts = AbioticConsts()
#     core_const = CoreConsts()
#     result = calculate_diabatic_correction_above(
#         molar_density_air=np.repeat(28.96, 4),
#         specific_heat_air=np.repeat(1.0, 4),
#         temperature=dummy_climate_data["air_temperature"][0].to_numpy(),
#         sensible_heat_flux=(
#             dummy_climate_data["sensible_heat_flux_topofcanopy"].to_numpy()
#         ),
#         friction_velocity=dummy_climate_data["friction_velocity"].to_numpy(),
#         wind_heights=dummy_climate_data["layer_heights"][0].to_numpy(),
#         zero_plane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
#         celsius_to_kelvin=core_const.zero_Celsius,
#         von_karmans_constant=core_const.von_karmans_constant,
#         yasuda_stability_parameters=abiotic_consts.yasuda_stability_parameters,
#         diabatic_heat_momentum_ratio=abiotic_consts.diabatic_heat_momentum_ratio,
#     )

#     exp_result_h = np.array([0.105164, 0.024834, 0.008092, 0.008092])
#     exp_result_m = np.array([0.063098, 0.0149, 0.004855, 0.004855])
#     np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
#     np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


# @pytest.mark.parametrize(
#     "air_temperature, wind_speed, expected_phi_m, expected_phi_h",
#     [
#         # Stable conditions (temperature increasing with height)
#         (
#             np.array([[15.0, 16.0], [14.5, 15.5]]),
#             np.array([[2.1, 2.1], [2.0, 2.0]]),
#             np.array([1.000389, 1.000388]),
#             np.array([1.000389, 1.000388]),
#         ),
#         # Unstable conditions (temperature decreasing with height)
#         (
#             np.array([[15.0, 16.0], [16.0, 17.0]]),
#             np.array([[2.0, 2.0], [3.0, 3.0]]),
#             np.array([0.999685, 0.999686]),
#             np.array([0.999685, 0.999686]),
#         ),
#     ],
# )
# def test_canopy_correction_conditions(
#     air_temperature, wind_speed, expected_phi_m, expected_phi_h
# ):
#     """Test diabatic correction canopy for stable and unstable conditions."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_diabatic_correction_canopy,
#     )

#     results = calculate_diabatic_correction_canopy(
#         air_temperature,
#         wind_speed,
#         layer_heights=np.array([[20, 20], [10, 10]]),
#         mean_mixing_length=np.array([[1.6, 1.6], [1.5, 1.5]]),
#         stable_temperature_gradient_intercept=0.5,
#         stable_wind_shear_slope=0.1,
#         yasuda_stability_parameters=[0.2, 0.3, 0.4],
#         richardson_bounds=[0.1, -0.1],
#         gravity=9.81,
#         celsius_to_kelvin=273.15,
#     )

#     # Assert results
#     np.testing.assert_allclose(results["phi_m"], expected_phi_m, rtol=1e-4, atol=1e-4)
#     np.testing.assert_allclose(results["phi_h"], expected_phi_h, rtol=1e-4, atol=1e-4)


# def test_calculate_mean_mixing_length(dummy_climate_data):
#     """Test mixing length with and without vegetation."""

#     from virtual_ecosystem.models.abiotic.wind import calculate_mean_mixing_length

#     result = calculate_mean_mixing_length(
#         canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
#         zero_plane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
#         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
#         mixing_length_factor=AbioticConsts.mixing_length_factor,
#     )

#     np.testing.assert_allclose(
#         result, np.array([1.284154, 1.280886, 0.836903, 0.836903]), rtol=1e-4,
# atol=1e-4
#     )


# def test_generate_relative_turbulence_intensity(
#     dummy_climate_data_varying_canopy, fixture_core_components
# ):
#     """Test relative turbulence intensity for different true layers."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         generate_relative_turbulence_intensity,
#     )

#     layer_heights = dummy_climate_data_varying_canopy["layer_heights"][
#         fixture_core_components.layer_structure.index_filled_atmosphere
#     ]

#     result_t = generate_relative_turbulence_intensity(
#         layer_heights=layer_heights,
#         min_relative_turbulence_intensity=0.36,
#         max_relative_turbulence_intensity=0.9,
#         increasing_with_height=True,
#     )

#     exp_result_t = np.array(
#         [
#             [17.64, 17.64, 17.64, 17.64],
#             [16.56, 16.56, 16.56, 16.56],
#             [11.16, 11.16, np.nan, np.nan],
#             [5.76, np.nan, np.nan, np.nan],
#             [0.414, 0.414, 0.414, 0.414],
#         ]
#     )
#     result_f = generate_relative_turbulence_intensity(
#         layer_heights=layer_heights,
#         min_relative_turbulence_intensity=0.36,
#         max_relative_turbulence_intensity=0.9,
#         increasing_with_height=False,
#     )

#     exp_result_f = np.array(
#         [
#             [-16.92, -16.92, -16.92, -16.92],
#             [-15.84, -15.84, -15.84, -15.84],
#             [-10.44, -10.44, np.nan, np.nan],
#             [-5.04, np.nan, np.nan, np.nan],
#             [0.306, 0.306, 0.306, 0.306],
#         ]
#     )
#     np.testing.assert_allclose(result_t, exp_result_t, rtol=1e-3, atol=1e-3)
#     np.testing.assert_allclose(result_f, exp_result_f, rtol=1e-3, atol=1e-3)


# def test_calculate_wind_attenuation_coefficient(
#     dummy_climate_data_varying_canopy, fixture_core_components
# ):
#     """Test wind attenuation coefficient with different canopy layers."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_wind_attenuation_coefficient,
#     )

#     # TODO: Occupied canopies - the plants model should populate the filled_canopies
#     #       index in the data at some point.

#     # VIVI - this function was being used in two ways. One with the true aboveground
#     # rows and one with only the true canopy rows, adding the rows for above and
# surface
#     # My updates assume the former approach, so I've updated this test to match. The
#     # results have changed.

#     lyr_strct = fixture_core_components.layer_structure

#     leaf_area_index = dummy_climate_data_varying_canopy["leaf_area_index"][
#         lyr_strct.index_filled_atmosphere
#     ].to_numpy()

#     relative_turbulence_intensity = dummy_climate_data_varying_canopy[
#         "relative_turbulence_intensity"
#     ][lyr_strct.index_filled_atmosphere].to_numpy()

#     # TODO - create a scalar index for this canopy top layer [1]
#     canopy_height = (
#         dummy_climate_data_varying_canopy.data["layer_heights"][1].to_numpy(),
#     )

#     result = calculate_wind_attenuation_coefficient(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index,
#         mean_mixing_length=np.array([1.35804, 1.401984, 0.925228, 0.925228]),
#         drag_coefficient=AbioticConsts.drag_coefficient,
#         relative_turbulence_intensity=relative_turbulence_intensity,
#     )

#     exp_result = np.array(
#         # [
#         #     [0.0, 0.0, 0.0, 0.0],
#         #     [0.12523, 0.121305, 0.183812, 0.183812],
#         #     [0.133398, 0.129216, np.nan, np.nan],
#         #     [0.197945, np.nan, np.nan, np.nan],
#         #     # [0.197945, 0.129216, 0.183812, 0.183812],
#         #     [0.197945, 0.129216, 0.183812, 0.183812],
#         # ]
#         [
#             [0.0, 0.0, 0.0, 0.0],
#             [0.13339771, 0.12921647, 0.19579976, 0.19579976],
#             [0.19794498, 0.19174057, np.nan, np.nan],
#             [0.3835184, np.nan, np.nan, np.nan],
#             [0.3835184, 0.19174057, 0.19579976, 0.19579976],
#         ]
#     )
#     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# def test_wind_log_profile(fixture_core_components, dummy_climate_data):
#     """Test log wind profile."""

#     from virtual_ecosystem.models.abiotic.wind import wind_log_profile

#     layer_heights = dummy_climate_data["layer_heights"][
#         fixture_core_components.layer_structure.index_filled_atmosphere
#     ].to_numpy()

#     result = wind_log_profile(
#         height=layer_heights,
#         zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
#         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
#         diabatic_correction_momentum=np.array([0.105164, 0.024834, 0.008092,
# 0.008092]),
#     )

#     exp_result = np.array(
#         [
#             [7.645442, 1.551228, 1.534468, 1.534468],
#             [7.580903, 1.195884, 0.930835, 0.930835],
#             [7.175438, np.nan, np.nan, np.nan],
#             [6.482291, np.nan, np.nan, np.nan],
#             [1.877121, np.nan, np.nan, np.nan],
#         ]
#     )

#     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# def test_calculate_friction_velocity_reference_height(dummy_climate_data):
#     """Calculate friction velocity."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_friction_velocity_reference_height,
#     )

#     result = calculate_friction_velocity_reference_height(
#         wind_speed_ref=(
#             dummy_climate_data.data["wind_speed_ref"].isel(time_index=0).to_numpy()
#         ),
#         reference_height=(dummy_climate_data["layer_heights"][1] + 10).to_numpy(),
#         zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
#         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
#         diabatic_correction_momentum=np.array([0.063098, 0.0149, 0.004855, 0.004855]),
#         von_karmans_constant=CoreConsts.von_karmans_constant,
#         min_friction_velocity=0.001,
#     )
#     exp_result = np.array([0.051108, 0.171817, 0.155922, 0.155922])
#     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# def test_calculate_wind_above_canopy():
#     """Wind speed above canopy."""

#     from virtual_ecosystem.models.abiotic.wind import calculate_wind_above_canopy

#     result = calculate_wind_above_canopy(
#         friction_velocity=np.array([0.0, 0.819397, 1.423534, 1.423534]),
#         wind_height_above=np.array(
#             [[2.0, 32.0, 32.0, 32.0], [np.nan, 30.0, 30.0, 30.0]]
#         ),
#         zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
#         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
#         diabatic_correction_momentum=np.array([0.003, 0.026, 0.013, 0.013]),
#         von_karmans_constant=CoreConsts.von_karmans_constant,
#         min_wind_speed_above_canopy=0.55,
#     )

#     exp_result = np.array(
#         [[0.55, 3.180068, 5.478385, 5.478385], [np.nan, 2.452148, 3.330154, 3.330154]]
#     )
#     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# def test_calculate_wind_canopy(
#     dummy_climate_data_varying_canopy, fixture_core_components
# ):
#     """Test below canopy wind profile."""

#     from virtual_ecosystem.models.abiotic.wind import calculate_wind_canopy

#     lyr_strct = fixture_core_components.layer_structure

#     # TODO we want to use fixture here, but there is a conflict with expected results
#     # in conductivities (attenuation coefficient two orders of magnitude different,
# and
#     # test fixture does not include gradient.) FIX in separate PR.
#     attenuation_coeff = np.array(
#         [
#             [0.12523, 0.121305, 0.183812, 0.183812],
#             [0.133398, 0.129216, np.nan, np.nan],
#             [0.197945, np.nan, np.nan, np.nan],
#             [0.197945, 0.129216, 0.183812, 0.183812],
#         ]
#     )

#     layer_heights_np = dummy_climate_data_varying_canopy["layer_heights"].to_numpy()
#     layer_heights = layer_heights_np[
#         np.logical_or(lyr_strct.index_filled_canopy, lyr_strct.index_surface)
#     ]
#     canopy_height = layer_heights_np[1]

#     result = calculate_wind_canopy(
#         top_of_canopy_wind_speed=np.array([0.5, 5.590124, 10.750233, 10.750233]),
#         wind_layer_heights=layer_heights,
#         canopy_height=canopy_height,
#         attenuation_coefficient=attenuation_coeff,
#     )

#     exp_result = np.array(
#         [
#             [0.5, 5.590124, 10.750233, 10.750233],
#             [0.478254, 5.354458, np.nan, np.nan],
#             [0.438187, np.nan, np.nan, np.nan],
#             [0.410478, 4.914629, 8.950668, 8.950668],
#         ]
#     )
#     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# def test_calculate_wind_profile(
#     dummy_climate_data_varying_canopy, fixture_core_components
# ):
#     """Test full update of wind profile."""

#     from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile

#     lyr_strct = fixture_core_components.layer_structure

#     # VIVI - same deal here. Feeding the full true aboveground rows into this, not
# just
#     # the true canopy rows. Seeing minor test value changes as a result.
#     leaf_area_index = dummy_climate_data_varying_canopy["leaf_area_index"][
#         lyr_strct.index_filled_atmosphere
#     ].to_numpy()
#     layer_heights = dummy_climate_data_varying_canopy["layer_heights"][
#         lyr_strct.index_filled_atmosphere
#     ].to_numpy()
#     air_temperature = dummy_climate_data_varying_canopy["air_temperature"][
#         lyr_strct.index_filled_atmosphere
#     ].to_numpy()

#     wind_update = calculate_wind_profile(
#         canopy_height=layer_heights[1],
#         wind_height_above=layer_heights[0:2],
#         wind_layer_heights=layer_heights,
#         leaf_area_index=leaf_area_index,
#         air_temperature=air_temperature,
#         atmospheric_pressure=np.repeat(96.0, 4),
#         sensible_heat_flux_topofcanopy=np.array([100.0, 50.0, 10.0, 10.0]),
#         wind_speed_ref=np.array([0.1, 5.0, 10.0, 10.0]),
#         wind_reference_height=(layer_heights[1] + 10),
#         abiotic_constants=AbioticConsts(),
#         core_constants=CoreConsts(),
#     )

#     friction_velocity_exp = np.array([0.012793, 0.84372, 1.811774, 1.811774])
#     wind_speed_exp = np.array(
#         # [
#         #     [0.1, 3.719967, 7.722811, 7.722811],
#         #     [0.1, 3.226327, 6.915169, 6.915169],
#         #     [0.09551, 3.106107, np.nan, np.nan],
#         #     [0.087254, np.nan, np.nan, np.nan],
#         #     [0.08156, 2.880031, 6.39049, 6.39049],
#         # ]
#         [
#             [0.1, 3.7199665, 7.72281114, 7.72281114],
#             [0.1, 3.22632714, 6.91516866, 6.91516866],
#             [0.09341001, 3.04955397, np.nan, np.nan],
#             [0.07678466, np.nan, np.nan, np.nan],
#             [0.06737292, 2.7260693, 6.35768904, 6.35768904],
#         ]
#     )

#     np.testing.assert_allclose(
#         wind_update["friction_velocity"], friction_velocity_exp, rtol=1e-3, atol=1e-3
#     )
#     np.testing.assert_allclose(
#         wind_update["wind_speed"], wind_speed_exp, rtol=1e-3, atol=1e-3
#     )
