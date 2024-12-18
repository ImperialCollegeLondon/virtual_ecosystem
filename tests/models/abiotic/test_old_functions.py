"""Test module for abiotic.conductivities.py."""

# import numpy as np
# import pytest


# def test_initialise_conductivities(dummy_climate_data, fixture_core_components):
#     """Test conductivities are initialised correctly."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         initialise_conductivities,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     result = initialise_conductivities(
#         layer_structure=lyr_strct,
#         layer_heights=dummy_climate_data["layer_heights"],
#         initial_air_conductivity=50.0,
#         top_leaf_vapour_conductivity=0.32,
#         bottom_leaf_vapour_conductivity=0.25,
#         top_leaf_air_conductivity=0.19,
#         bottom_leaf_air_conductivity=0.13,
#     )

#     exp_air_cond = lyr_strct.from_template()
#     exp_air_cond[lyr_strct.index_atmosphere] = np.repeat(
#         a=[4.166667, 3.33333333, 6.66666667], repeats=[1, 10, 1]
#     )[:, None]

#     exp_leaf_vap_cond = lyr_strct.from_template()
#     exp_leaf_vap_cond[lyr_strct.index_filled_canopy] = np.array(
#         [0.254389, 0.276332, 0.298276]
#     )[:, None]

#     exp_leaf_air_cond = lyr_strct.from_template()
#     exp_leaf_air_cond[lyr_strct.index_filled_canopy] = np.array(
#         [0.133762, 0.152571, 0.171379]
#     )[:, None]

#     np.testing.assert_allclose(
#         result["air_heat_conductivity"], exp_air_cond, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["leaf_vapour_conductivity"], exp_leaf_vap_cond, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#        result["leaf_air_heat_conductivity"], exp_leaf_air_cond, rtol=1e-04, atol=1e-04
#     )


# def test_interpolate_along_heights(dummy_climate_data, fixture_core_components):
#     """Test linear interpolation along heights."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         interpolate_along_heights,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     layer_heights = dummy_climate_data["layer_heights"].to_numpy()

#     result = interpolate_along_heights(
#         start_height=layer_heights[lyr_strct.index_surface],
#         end_height=layer_heights[lyr_strct.index_above],
#         target_heights=layer_heights[lyr_strct.index_filled_atmosphere],
#         start_value=50.0,
#         end_value=20.0,
#     )

#     # Get layer structure and reduce to only atmospheric layers
#     exp_result = lyr_strct.from_template()
#     exp_result[lyr_strct.index_filled_atmosphere] = np.array(
#         [20.0, 21.88087774, 31.28526646, 40.68965517, 50.0]
#     )[:, None]
#     exp_result = exp_result[lyr_strct.index_filled_atmosphere]

#     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


# deftest_interpolate_along_heights_arrays(fixture_core_components, dummy_climate_data):
#     """Test linear interpolation along heights with arrays of boundary values."""

#     # TODO - I don't think this differs from the test above.

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         interpolate_along_heights,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     # Extract the block of atmospheric layer heights.
#     layer_heights = dummy_climate_data["layer_heights"][
#         lyr_strct.index_atmosphere
#     ].to_numpy()

#     # Interpolate from the top to bottom across the atmosphere
#     result = interpolate_along_heights(
#         start_height=layer_heights[-1],
#         end_height=layer_heights[0],
#         target_heights=layer_heights,
#         start_value=np.repeat(50.0, 4),
#         end_value=np.repeat(20.0, 4),
#     )

#    # The function only returns values for the atmospheric layers, so fill the template
#     # and then truncate to the atmosphere.
#     exp_result = lyr_strct.from_template()
#     exp_result[lyr_strct.index_filled_atmosphere] = np.array(
#         [20.0, 21.88087774, 31.28526646, 40.68965517, 50.0]
#     )[:, None]
#     exp_result = exp_result[lyr_strct.index_atmosphere]

#     np.testing.assert_allclose(
#         result, exp_result, rtol=1e-04, atol=1e-04, equal_nan=True
#     )


# # def test_calculate_air_heat_conductivity_above(dummy_climate_data):
# #     """Test heat conductivity above canopy."""

# #     from virtual_ecosystem.models.abiotic.conductivities import (
# #         calculate_air_heat_conductivity_above,
# #     )

# #     result = calculate_air_heat_conductivity_above(
# #         height_above_canopy=dummy_climate_data["layer_heights"][0],
# #         zero_displacement_height=(
# #             dummy_climate_data["zero_displacement_height"].to_numpy()
# #         ),
# #         canopy_height=dummy_climate_data["layer_heights"][1],
# #         friction_velocity=dummy_climate_data["friction_velocity"].to_numpy(),
# #         molar_density_air=dummy_climate_data["molar_density_air"][0].to_numpy(),
# #         diabatic_correction_heat=(
# #             dummy_climate_data["diabatic_correction_heat_above"].to_numpy()
# #         ),
# #         von_karmans_constant=CoreConsts.von_karmans_constant,
# #     )
# #     np.testing.assert_allclose(
# #         result,
# #         np.array([523.39996, 218.083317, 87.233327, 87.233327]),
# #         rtol=1e-04,
# #         atol=1e-04,
# #     )


# @pytest.mark.parametrize(
#     "ustar, d, zm, ph, psih, gmin, expected_conductance",
#     [
#         (
#             np.repeat(0.3, 3),
#             np.repeat(2, 3),
#             np.repeat(0.1, 3),
#             np.repeat(1.0, 3),
#             np.repeat(0.1, 3),
#             np.repeat(0.05, 3),
#             np.repeat(0.05, 3),
#         ),  # Typical case
#         (
#             np.repeat(0.2, 3),
#             np.repeat(1.5, 3),
#             np.repeat(0.05, 3),
#             np.repeat(0.9, 3),
#             np.repeat(0.05, 3),
#             np.repeat(0.04, 3),
#             np.repeat(0.04, 3),
#         ),  # Low friction velocity, height
#         (
#             np.repeat(0.4, 3),
#             np.repeat(2.5, 3),
#             np.repeat(0.15, 3),
#             np.repeat(1.2, 3),
#             np.repeat(0.2, 3),
#             np.repeat(0.06, 3),
#             np.repeat(0.06, 3),
#         ),  # High friction velocity and height
#         (
#             np.repeat(0.1, 3),
#             np.repeat(1.0, 3),
#             np.repeat(0.05, 3),
#             np.repeat(0.8, 3),
#             np.repeat(0.02, 3),
#             np.repeat(0.1, 3),
#             np.repeat(0.1, 3),
#         ),  # Edge case to ensure conductance is not less than gmin
#     ],
# )
# def test_calculate_molar_conductance_above_canopy(
#     ustar, d, zm, ph, psih, gmin, expected_conductance
# ):
#     """Test calculation of molar conductance above canopy."""
#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_molar_conductance_above_canopy,
#     )

#     result = calculate_molar_conductance_above_canopy(
#         friction_velocity=ustar,
#         zero_plane_displacement=d,
#         roughness_length_momentum=zm,
#         reference_height=np.repeat(10.0, 3),
#         molar_density_air=ph,
#         diabatic_correction_heat=psih,
#         minimum_conductance=gmin,
#         von_karmans_constant=0.4,
#     )
#     np.testing.assert_allclose(result, expected_conductance, atol=1e-6)


# @pytest.mark.parametrize(
#     "leaf_dimension, sensible_heat_flux, expected_gha",
#     [
#         (0.05, np.repeat(100.0, 3), np.repeat(0.168252, 3)),  # Typical case
#        (0.01, np.repeat(50.0, 3), np.repeat(0.202092, 3)),  # Smaller leaf, lower flux
#        (0.1, np.repeat(200.0, 3), np.repeat(0.168252, 3)),  # Larger leaf, higher flux
#     ],
# )
# def test_calculate_free_convection(leaf_dimension, sensible_heat_flux, expected_gha):
#     """Test calculation of free convection gha."""
#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_free_convection,
#     )

#     result = calculate_free_convection(
#         leaf_dimension=leaf_dimension, sensible_heat_flux=sensible_heat_flux
#     )
#     np.testing.assert_allclose(result, expected_gha, atol=1e-6)


# def test_calculate_stomatal_conductance():
#     """Test calculation of stomatal conductance."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_stomatal_conductance,
#     )

#     # Define test input values
#     shortwave_radiation = np.array([1000.0, 500.0, 0.0])
#     maximum_stomatal_conductance = 0.3
#     half_saturation_stomatal_conductance = 100.0

#     # Expected stomatal conductance value
#     expected_conductance = np.array([0.293617, 0.2875, 0.0])

#     actual_conductance = calculate_stomatal_conductance(
#         shortwave_radiation=shortwave_radiation,
#         maximum_stomatal_conductance=maximum_stomatal_conductance,
#         half_saturation_stomatal_conductance=half_saturation_stomatal_conductance,
#     )

#     np.testing.assert_allclose(actual_conductance, expected_conductance, rtol=1e-4)


# # def test_calculate_air_heat_conductivity_canopy(dummy_climate_data):
# #     """Test calculate air heat conductivity in canopy."""

# #     from virtual_ecosystem.models.abiotic.conductivities import (
# #         calculate_air_heat_conductivity_canopy,
# #     )

# #     result = calculate_air_heat_conductivity_canopy(
# #         attenuation_coefficient=(
# #             dummy_climate_data["attenuation_coefficient"][1].to_numpy()
# #         ),
# #         mean_mixing_length=dummy_climate_data["mean_mixing_length"].to_numpy(),
# #         molar_density_air=dummy_climate_data["molar_density_air"][1].to_numpy(),
# #         upper_height=np.repeat(10.0, 4),
# #         lower_height=np.repeat(5.0, 4),
# #         relative_turbulence_intensity=(
# #             dummy_climate_data["relative_turbulence_intensity"][1].to_numpy()
# #         ),
# #         top_of_canopy_wind_speed=np.repeat(1.0, 4),
# #         diabatic_correction_momentum=(
# #             dummy_climate_data["diabatic_correction_momentum_canopy"].to_numpy()
# #         ),
# #         canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
# #     )
# #     exp_result = np.repeat(0.236981, 4)
# #     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


# # def test_calculate_leaf_air_heat_conductivity(
# #     dummy_climate_data, fixture_core_components
# # ):
# #     """Test calculation of leaf air heat conductivity."""

# #     from virtual_ecosystem.models.abiotic.conductivities import (
# #         calculate_leaf_air_heat_conductivity,
# #     )

# #     lyr_strct = fixture_core_components.layer_structure
# #     abiotic_consts = AbioticConsts()

# #     result = calculate_leaf_air_heat_conductivity(
# #         temperature=dummy_climate_data["air_temperature"].to_numpy(),
# #         wind_speed=dummy_climate_data["wind_speed"].to_numpy(),
# #         characteristic_dimension_leaf=0.1,
# #         temperature_difference=(
# #             dummy_climate_data["canopy_temperature"]
# #             - dummy_climate_data["air_temperature"]
# #         ).to_numpy(),
# #         molar_density_air=dummy_climate_data["molar_density_air"].to_numpy(),
# #        kinematic_viscosity_parameters=abiotic_consts.kinematic_viscosity_parameters,
# #        thermal_diffusivity_parameters=abiotic_consts.thermal_diffusivity_parameters,
# #         grashof_parameter=abiotic_consts.grashof_parameter,
# #         forced_conductance_parameter=abiotic_consts.forced_conductance_parameter,
# #         positive_free_conductance_parameter=(
# #             abiotic_consts.positive_free_conductance_parameter
# #         ),
# #         negative_free_conductance_parameter=(
# #             abiotic_consts.negative_free_conductance_parameter
# #         ),
# #     )
# #     exp_result = lyr_strct.from_template()
# #     exp_result[lyr_strct.index_filled_canopy] = np.array(
# #         [0.065242, 0.065062, 0.064753]
# #     )[:, None]

# #     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)
# #


# def test_calculate_leaf_vapour_conductivity():
#     """Test calculate leaf vapour conductivity."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_leaf_vapour_conductivity,
#     )

#     result = calculate_leaf_vapour_conductivity(
#         leaf_air_conductivity=np.repeat(5.0, 4),
#         stomatal_conductance=np.repeat(5.0, 4),
#     )
#     np.testing.assert_allclose(result, np.repeat(2.5, 4), rtol=1e-04, atol=1e-04)


# def test_calculate_current_conductivities(dummy_climate_data, fixture_core_components)
# # :
# #     """Test update current conductivities."""

# #     from virtual_ecosystem.models.abiotic.conductivities import (
# #         calculate_current_conductivities,
# #     )

# #     lyr_strct = fixture_core_components.layer_structure

# #     result = calculate_current_conductivities(
# #         data=dummy_climate_data,
# #         characteristic_dimension_leaf=0.01,
# #         von_karmans_constant=CoreConsts.von_karmans_constant,
# #         abiotic_constants=AbioticConsts(),
# #     )

# #     exp_gt = lyr_strct.from_template()
# #     exp_gt[lyr_strct.index_above] = np.array(
# #         [1.460964e02, 6.087350e01, 2.434940e01, 2.434940e01]
# #     )
# #     exp_gt[lyr_strct.index_flux_layers] = np.array(
# #         [1.95435e03, 1.414247e01, 0.125081, 13.654908]
# #     )[:, None]

# #     exp_gv = lyr_strct.from_template()
# #   exp_gv[lyr_strct.index_filled_canopy] = np.array([0.203513, 0.202959, 0.202009])[
# #         :, None
# #     ]

# #     exp_gha = lyr_strct.from_template()
# #   exp_gha[lyr_strct.index_filled_canopy] = np.array([0.206312, 0.205743, 0.204766])[
# #         :, None
# #     ]

# #     exp_gtr = lyr_strct.from_template()
# #     exp_gtr[lyr_strct.index_flux_layers] = np.array(
# #         [1.954354e03, 1.403429e01, 0.123447, 0.604689]
# #     )[:, None]

# #     np.testing.assert_allclose(
# #         result["air_heat_conductivity"], exp_gt, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["leaf_air_heat_conductivity"], exp_gha, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["conductivity_from_ref_height"], exp_gtr, rtol=1e-04, atol=1e-04
# #     )

# """Test bigleaf module."""

# import numpy as np

# from virtual_ecosystem.core.constants import CoreConsts
# from virtual_ecosystem.models.abiotic.constants import AbioticConsts
# from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
# from virtual_ecosystem.models.hydrology.constants import HydroConsts


# def test_bigleaf(dummy_climate_data, fixture_core_components):
#     """Test bigleaf model."""

#     from virtual_ecosystem.models.abiotic.bigleaf import bigleaf

#     data = dummy_climate_data
#     timestep = {
#         "year": 2024,
#         "month": 10,
#         "day": 16,
#         "hour": 12,
#     }

#     latitude = np.array([5.0, 5.1, 5.2, 5.3])
#     longitude = np.repeat(102.0, 4)
#     slope = np.array([5.0, 10.0, 5.0, 10.0])
#     aspect = np.array([0.0, 180.0, 0.0, 180.0])

#     core_constants = CoreConsts()
#     abiotic_constants = AbioticConsts()
#     abiotic_simple_constants = AbioticSimpleConsts()
#     hydro_constants = HydroConsts()
#     layer_structure = fixture_core_components.layer_structure

#     # Expected result
#     expected_output = {
#         "canopy_temperature": np.array([26.161933, 26.189558, 26.161933, 26.189558]),
#         "ground_temperature": np.array([23.570943, 23.602405, 23.570943, 23.602405]),
#         "sensible_heat_flux": np.array(
#             [-283.829567, -281.20334, -283.848943, -281.176712]
#         ),
#         "ground_heat_flux": np.array([0.0, 0.0, 0.0, 0.0]),
#         "net_radiation": np.array([-182.354931, -174.56186, -182.354931, -174.56186]),
#        "psih": np.array([-4.553863e-12, -4.512036e-12, -4.553863e-12, -4.512036e-12]),
#        "psim": np.array([-3.502971e-12, -3.470797e-12, -3.502971e-12, -3.470797e-12]),
#        "phih": np.array([1.0, 1.0, 1.0, 1.0]),
#         "monin_obukov_length": np.array(
#             [1.416422e13, 1.429552e13, 1.416422e13, 1.429552e13]
#         ),
#         "friction_velocity": np.array([0.550454, 0.550454, 0.550454, 0.550454]),
#         "albedo": np.array([0.210373, 0.183297, 0.210373, 0.183297]),
#         "canopy_shortwave_absorption": np.array(
#             [236.887959, 245.01088, 236.887959, 245.01088]
#         ),
#         "ground_shortwave_absorption": np.array(
#             [47.898979, 54.152699, 47.898979, 54.152699]
#         ),
#     }

#     # Run the function
#     output = bigleaf(
#         data=data,
#         timestep=timestep,
#         time_index=0,
#         latitude=latitude,
#         longitude=longitude,
#         slope=slope,
#         aspect=aspect,
#         core_constants=core_constants,
#         abiotic_constants=abiotic_constants,
#         abiotic_simple_constants=abiotic_simple_constants,
#         hydro_constants=hydro_constants,
#         layer_structure=layer_structure,
#     )

#     # Compare results
#     for var in expected_output:
#         np.testing.assert_allclose(output[var], expected_output[var], rtol=1e-4)

# """Test module for abiotic.energy_balance.py."""

# import numpy as np

# from virtual_ecosystem.core.constants import CoreConsts
# from virtual_ecosystem.models.abiotic.constants import AbioticConsts


# def test_initialise_absorbed_radiation(dummy_climate_data, fixture_core_components):
#     """Test initial absorbed radiation has correct dimensions."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         initialise_absorbed_radiation,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     leaf_area_index_true = dummy_climate_data["leaf_area_index"][
#         lyr_strct.index_filled_canopy
#     ]
#     layer_heights_canopy = dummy_climate_data["layer_heights"][
#         lyr_strct.index_filled_canopy
#     ]

#     result = initialise_absorbed_radiation(
#         topofcanopy_radiation=dummy_climate_data["topofcanopy_radiation"]
#         .isel(time_index=0)
#         .to_numpy(),
#         leaf_area_index=leaf_area_index_true.to_numpy(),
#         layer_heights=layer_heights_canopy.to_numpy(),
#         light_extinction_coefficient=0.01,
#     )

#     exp_result = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])
#     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


# def test_initialise_canopy_temperature(dummy_climate_data, fixture_core_components):
#     """Test that canopy temperature is initialised correctly."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         initialise_canopy_temperature,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     air_temperature = dummy_climate_data["air_temperature"][
#         lyr_strct.index_filled_canopy
#     ]

#     absorbed_radiation = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])

#     result = initialise_canopy_temperature(
#         air_temperature=air_temperature,
#         absorbed_radiation=absorbed_radiation,
#         canopy_temperature_ini_factor=0.01,
#     )
#     exp_result = np.array([[29.845994] * 4, [28.872169] * 4, [27.207403] * 4])

#     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


# def test_calculate_slope_of_saturated_pressure_curve():
#     """Test calculation of slope of saturated pressure curve."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         calculate_slope_of_saturated_pressure_curve,
#     )

#     const = AbioticConsts()
#     result = calculate_slope_of_saturated_pressure_curve(
#         temperature=np.full((4, 3), 20.0),
#         saturated_pressure_slope_parameters=const.saturated_pressure_slope_parameters,
#     )
#     exp_result = np.full((4, 3), 0.14474)
#     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


# deftest_initialise_canopy_and_soil_fluxes(
# dummy_climate_data, fixture_core_components
# ):
#     """Test that canopy and soil fluxes initialised correctly."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         initialise_canopy_and_soil_fluxes,
#     )

#     result = initialise_canopy_and_soil_fluxes(
#         air_temperature=dummy_climate_data["air_temperature"],
#         topofcanopy_radiation=(
#             dummy_climate_data["topofcanopy_radiation"].isel(time_index=0)
#         ),
#         leaf_area_index=dummy_climate_data["leaf_area_index"],
#         layer_heights=dummy_climate_data["layer_heights"],
#         layer_structure=fixture_core_components.layer_structure,
#         light_extinction_coefficient=0.01,
#         canopy_temperature_ini_factor=0.01,
#     )

#     exp_abs = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])

#     for var in [
#         "canopy_temperature",
#         "sensible_heat_flux",
#         "latent_heat_flux",
#         "ground_heat_flux",
#         "canopy_absorption",
#     ]:
#         assert var in result

#     np.testing.assert_allclose(
#         result["canopy_absorption"][1:4].to_numpy(), exp_abs, rtol=1e-04, atol=1e-04
#     )
#     for var in ["sensible_heat_flux", "latent_heat_flux"]:
#        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.full((3, 4), 0.001))
#         np.testing.assert_allclose(result[var][12].to_numpy(), np.repeat(0.001, 4))


# def test_calculate_longwave_emission():
#     """Test that longwave radiation is calculated correctly."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         calculate_longwave_emission,
#     )

#     result = calculate_longwave_emission(
#         temperature=np.repeat(290.0, 3),
#         emissivity=AbioticConsts.soil_emissivity,
#         stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
#     )
#    np.testing.assert_allclose(result, np.repeat(320.84384, 3), rtol=1e-04, atol=1e-04)


# def test_calculate_surface_temperature():
#     """Test calculation of surface temperature."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         calculate_surface_temperature,
#     )

#     core_consts = CoreConsts()
#     abiotic_consts = AbioticConsts()

#     result = calculate_surface_temperature(
#         total_absorbed_radiation=np.repeat(400, 3),
#         heat_conductivity=np.repeat(0.2, 3),
#         vapour_conductivity=np.repeat(0.01, 3),
#         surface_temperature=np.repeat(25.0, 3),
#         temperature_average_air_surface=np.repeat(20.0, 3),
#         atmospheric_pressure=np.repeat(101.3, 3),
#         effective_vapour_pressure_air=np.repeat(1.2, 3),
#         surface_emissivity=0.9,
#         ground_heat_flux=np.repeat(30.0, 3),
#         relative_humidity=np.repeat(0.6, 3),
#         stefan_boltzmann_constant=core_consts.stefan_boltzmann_constant,
#         celsius_to_kelvin=core_consts.zero_Celsius,
#         latent_heat_vap_equ_factors=abiotic_consts.latent_heat_vap_equ_factors,
#         molar_heat_capacity_air=29.1,
#         specific_heat_equ_factors=abiotic_consts.specific_heat_equ_factors,
#         saturation_vapour_pressure_factors=[0.61078, 7.5, 237.3],
#     )
#     exp_result = np.repeat(21.96655, 3)

#     np.testing.assert_allclose(result, exp_result, atol=1e-5)


# # def test_calculate_leaf_and_air_temperature(
# #     fixture_core_components,
# #     dummy_climate_data,
# # ):
# #     """Test updating leaf and air temperature."""

# #     from virtual_ecosystem.models.abiotic.energy_balance import (
# #         calculate_leaf_and_air_temperature,
# #     )
# #    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts

# #     lyr_strct = fixture_core_components.layer_structure

# #     result = calculate_leaf_and_air_temperature(
# #         data=dummy_climate_data,
# #         time_index=1,
# #         layer_structure=lyr_strct,
# #         abiotic_constants=AbioticConsts(),
# #         abiotic_simple_constants=AbioticSimpleConsts(),
# #         core_constants=CoreConsts(),
# #     )

# #     exp_air_temp = lyr_strct.from_template()
# #     exp_air_temp[lyr_strct.index_filled_atmosphere] = np.array(
# #         [30.0, 29.999969, 29.995439, 28.796977, 20.08797]
# #     )[:, None]

# #     exp_leaf_temp = lyr_strct.from_template()
# #     exp_leaf_temp[lyr_strct.index_filled_canopy] = np.array(
# #         [30.078613, 29.091601, 26.951191]
# #     )[:, None]

# #     exp_vp = lyr_strct.from_template()
# #     exp_vp[lyr_strct.index_filled_atmosphere] = np.array(
# #         [0.14, 0.140323, 0.18372, 1.296359, 0.023795]
# #     )[:, None]

# #     exp_vpd = lyr_strct.from_template()
# #     exp_vpd[lyr_strct.index_filled_atmosphere] = np.array(
# #         [0.098781, 0.099009, 0.129644, 0.94264, 0.021697]
# #     )[:, None]

# #     exp_gv = lyr_strct.from_template()
# #    exp_gv[lyr_strct.index_filled_canopy] = np.array([0.203513, 0.202959, 0.202009])[
# #         :, None
# #     ]

# #   # TODO - flux layer index does not include above but these tests do - what is best
# #     flux_index = np.logical_or(lyr_strct.index_flux_layers, lyr_strct.index_above)

# #     exp_sens_heat = lyr_strct.from_template()
# #     exp_sens_heat[flux_index] = np.array([0.0, 1.397746, 1.315211, -1.515519, 1.0])[
# #         :, None
# #     ]

# #     exp_latent_heat = lyr_strct.from_template()
# #   exp_latent_heat[flux_index] = np.array([0.0, 8.330748, 8.426556, 11.740824, 1.0])[
# #         :, None
# #     ]

# #     np.testing.assert_allclose(
# #         result["air_temperature"], exp_air_temp, rtol=1e-03, atol=1e-03
# #     )
# #     np.testing.assert_allclose(
# #         result["canopy_temperature"], exp_leaf_temp, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["vapour_pressure"], exp_vp, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["vapour_pressure_deficit"], exp_vpd, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #         result["sensible_heat_flux"], exp_sens_heat, rtol=1e-04, atol=1e-04
# #     )
# #     np.testing.assert_allclose(
# #       result["latent_heat_flux"][1:4], exp_latent_heat[1:4], rtol=1e-04, atol=1e-04
# #     )


# # def test_leaf_and_air_temperature_linearisation(
# #     fixture_core_components, dummy_climate_data
# # ):
# #     """Test linearisation of air and leaf temperature."""

# #     from virtual_ecosystem.models.abiotic.energy_balance import (
# #         leaf_and_air_temperature_linearisation,
# #     )

# #     lyr_strct = fixture_core_components.layer_structure

# #     a_A, b_A = leaf_and_air_temperature_linearisation(
# #         conductivity_from_ref_height=(
# #             dummy_climate_data["conductivity_from_ref_height"][
# #                 lyr_strct.index_filled_canopy
# #             ]
# #         ),
# #         conductivity_from_soil=np.repeat(0.1, 4),
# #         leaf_air_heat_conductivity=(
# #             dummy_climate_data["leaf_air_heat_conductivity"][
# #                 lyr_strct.index_filled_canopy
# #             ]
# #         ),
# #         air_temperature_ref=(
# #             dummy_climate_data["air_temperature_ref"].isel(time_index=0).to_numpy()
# #         ),
# #         top_soil_temperature=dummy_climate_data["soil_temperature"][
# #             lyr_strct.index_topsoil
# #         ].to_numpy(),
# #     )

# #     exp_a = np.full((3, 4), fill_value=29.677419)
# #     exp_b = np.full((3, 4), fill_value=0.04193548)
# #     np.testing.assert_allclose(a_A, exp_a)
# #     np.testing.assert_allclose(b_A, exp_b)


# # def test_longwave_radiation_flux_linearisation():
# #     """Test linearisation of longwave radiation fluxes."""

# #     from virtual_ecosystem.models.abiotic.energy_balance import (
# #         longwave_radiation_flux_linearisation,
# #     )

# #     a_R, b_R = longwave_radiation_flux_linearisation(
# #         a_A=np.full((3, 4), fill_value=29.677419),
# #         b_A=np.full((3, 4), fill_value=0.04193548),
# #         air_temperature_ref=np.full((3, 4), 30.0),
# #         leaf_emissivity=0.8,
# #         stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
# #     )

# #     exp_a = np.full((3, 4), fill_value=0.035189)
# #     exp_b = np.full((3, 4), fill_value=0.005098)
# #     np.testing.assert_allclose(a_R, exp_a, rtol=1e-04, atol=1e-04)
# #     np.testing.assert_allclose(b_R, exp_b, rtol=1e-04, atol=1e-04)


# # def test_vapour_pressure_linearisation():
# #     """Test linearisation of vapour pressure."""

# #     from virtual_ecosystem.models.abiotic.energy_balance import (
# #         vapour_pressure_linearisation,
# #     )

# #     a_E, b_E = vapour_pressure_linearisation(
# #         vapour_pressure_ref=np.full((3, 4), 0.14),
# #         saturated_vapour_pressure_ref=np.full((3, 4), 0.5),
# #         soil_vapour_pressure=np.full((3, 4), 0.14),
# #         conductivity_from_soil=np.repeat(0.1, 4),
# #         leaf_vapour_conductivity=np.full((3, 4), 0.2),
# #         conductivity_from_ref_height=np.full((3, 4), 3),
# #         delta_v_ref=np.full((3, 4), 0.14474),
# #     )

# #     exp_a = np.full((3, 4), fill_value=0.161818)
# #     exp_b = np.full((3, 4), fill_value=0.043861)
# #     np.testing.assert_allclose(a_E, exp_a, rtol=1e-04, atol=1e-04)
# #     np.testing.assert_allclose(b_E, exp_b, rtol=1e-04, atol=1e-04)


# # def test_latent_heat_flux_linearisation():
# #     """Test latent heat flux linearisation."""

# #     from virtual_ecosystem.models.abiotic.energy_balance import (
# #         latent_heat_flux_linearisation,
# #     )

# #     a_L, b_L = latent_heat_flux_linearisation(
# #         latent_heat_vapourisation=np.full((3, 4), 2245.0),
# #         leaf_vapour_conductivity=np.full((3, 4), 0.2),
# #         atmospheric_pressure_ref=np.repeat(96.0, 4),
# #         saturated_vapour_pressure_ref=np.full((3, 4), 0.5),
# #         a_E=np.full((3, 4), fill_value=0.161818),
# #         b_E=np.full((3, 4), fill_value=0.043861),
# #         delta_v_ref=np.full((3, 4), 0.14474),
# #     )

# #     exp_a = np.full((3, 4), fill_value=13.830078)
# #     exp_b = np.full((3, 4), fill_value=46.3633)
# #     np.testing.assert_allclose(a_L, exp_a, rtol=1e-04, atol=1e-04)
# #     np.testing.assert_allclose(b_L, exp_b, rtol=1e-04, atol=1e-04)


# # def test_calculate_delta_canopy_temperature():
# #     """Test calculate delta canopy temperature."""

# #     from virtual_ecosystem.models.abiotic.energy_balance import (
# #         calculate_delta_canopy_temperature,
# #     )

# #     delta_t = calculate_delta_canopy_temperature(
# #         absorbed_radiation=np.full((3, 4), 10),
# #         a_R=np.full((3, 4), fill_value=0.035189),
# #         a_L=np.full((3, 4), fill_value=13.830078),
# #         b_R=np.full((3, 4), fill_value=0.005098),
# #         b_L=np.full((3, 4), fill_value=46.3633),
# #         b_H=np.full((3, 4), fill_value=46.3633),
# #     )

# #     exp_delta_t = np.full((3, 4), fill_value=-0.041238)
# #     np.testing.assert_allclose(delta_t, exp_delta_t, rtol=1e-04, atol=1e-04)

# """Test module for abiotic.radiation.py."""

# import numpy as np
# import pytest

# # from virtual_ecosystem.core.constants import CoreConsts
# # from virtual_ecosystem.models.abiotic.constants import AbioticConsts
# # from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts


# @pytest.mark.parametrize(
#     "year, month, day, expected_jd",
#     [
#         (2000, 1, 1, 2451545),  # Known Julian day for January 1, 2000
#         (2023, 9, 4, 2460192),  # A more recent date
#         (1582, 10, 4, 2299160),  # Day before the Gregorian calendar reform
#         (1582, 10, 15, 2299161),  # Day after the Gregorian calendar reform
#     ],
# )
# def test_calculate_julian_day(year, month, day, expected_jd) -> None:
#     """Test Julian day calculation."""

#     from virtual_ecosystem.models.abiotic.radiation import calculate_julian_day

#     result = calculate_julian_day(year=year, month=month, day=day)
#     assert result == expected_jd


# @pytest.mark.parametrize(
#     "julian_day, local_time, longitude, expected_solar_time",
#     [
#         (
#             2460192,
#             12.0,
#             np.repeat(-74.0060, 3),
#             np.repeat(7.08467, 3),
#         ),  # September 4, 2023, New York City
#         (
#             2451545,
#             12.0,
#             np.repeat(0.0, 3),
#             np.repeat(11.946, 3),
#         ),  # Noon UTC at Prime Meridian on January 1, 2000
#         (
#             2455197,
#             12.0,
#             np.repeat(100.0, 3),
#             np.repeat(18.618, 3),
#         ),  # Example case with positive longitude
#         (
#             2455197,
#             12.0,
#             np.repeat(-100.0, 3),
#             np.repeat(5.285, 3),
#         ),  # Example case with negative longitude
#     ],
# )
# def test_calculate_solar_time(
#     julian_day, local_time, longitude, expected_solar_time
# ) -> None:
#     """Test calculation of solar time."""

#     from virtual_ecosystem.models.abiotic.radiation import calculate_solar_time

#     result = calculate_solar_time(julian_day, local_time, longitude)
#     np.testing.assert_allclose(result, expected_solar_time, atol=1e-3)


# def test_calculate_solar_position():
#     """Test calculation of solar position."""

#     from virtual_ecosystem.models.abiotic.radiation import calculate_solar_position

#     # Test Case 1: New York City, September 4, 2024
#     lat = np.repeat(40.7128, 3)
#     lon = np.repeat(-74.0060, 3)
#     year = 2024
#     month = 9
#     day = 4
#     lt = -4  # Local time offset for New York City (UTC-4)

#     # Expected values
#     expected_zenith = np.repeat(62.11, 3)
#     expected_azimuth = np.repeat(174.22, 3)

#     result = calculate_solar_position(lat, lon, year, month, day, lt)

#     np.testing.assert_allclose(result[0], expected_zenith, atol=0.5)
#     np.testing.assert_allclose(result[1], expected_azimuth, atol=0.5)


# @pytest.mark.parametrize(
#     "slope, aspect, zenith, azimuth, shadowmask, expected_solar_index",
#     [
#         # Test Case 1: Basic test with no shadowmask
#         (
#             np.repeat(30.0, 3),
#             np.repeat(90.0, 3),
#             np.repeat(45.0, 3),
#             np.repeat(180.0, 3),
#             False,
#             np.repeat(0.612372, 3),
#         ),
#         # Test Case 2: Zen > 90 with shadowmask
#         (
#             np.repeat(30.0, 3),
#             np.repeat(90.0, 3),
#             np.repeat(95.0, 3),
#             np.repeat(180.0, 3),
#             True,
#             np.repeat(0.0, 3),
#         ),
#         # Test Case 3: Zen > 90 without shadowmask
#         (
#             np.repeat(30.0, 3),
#             np.repeat(90.0, 3),
#             np.repeat(95.0, 3),
#             np.repeat(180.0, 3),
#             False,
#             np.repeat(0.866025, 3),
#         ),
#         # Test Case 4: Slope = 0
#         (
#             np.repeat(0.0, 3),
#             np.repeat(90.0, 3),
#             np.repeat(45.0, 3),
#             np.repeat(180.0, 3),
#             False,
#             np.repeat(0.70710, 3),
#         ),
#     ],
# )
# def test_solar_index(
# slope, aspect, zenith, azimuth,shadowmask,expected_solar_index
# ):
#     """Test calculation of solar index."""

#     from virtual_ecosystem.models.abiotic.radiation import calculate_solar_index

#     result = calculate_solar_index(
#         slope=slope,
#         aspect=aspect,
#         zenith=zenith,
#         azimuth=azimuth,
#         shadowmask=shadowmask,
#     )
#     np.testing.assert_allclose(result, expected_solar_index, atol=1e-5)


# @pytest.mark.parametrize(
#     "solar_zenith_angle, temperature, relative_humidity, atm_pressure, expected",
#     [
#         (
#             np.repeat(45.0, 3),
#             np.repeat(25.0, 3),
#             np.repeat(60.0, 3),
#             np.repeat(1013.0, 3),
#             np.repeat(635.166, 3),
#         ),
#         (
#             np.repeat(30.0, 3),
#             np.repeat(20.0, 3),
#             np.repeat(70.0, 3),
#             np.repeat(1000.0, 3),
#             np.repeat(781.271, 3),
#         ),
#         (
#             np.repeat(60.0, 3),
#             np.repeat(15.0, 3),
#             np.repeat(80.0, 3),
#             np.repeat(950.0, 3),
#             np.repeat(455.525, 3),
#         ),
#         (
#             np.repeat(85.0, 3),
#             np.repeat(30.0, 3),
#             np.repeat(50.0, 3),
#             np.repeat(1020.0, 3),
#             np.repeat(74.968, 3),
#         ),
#     ],
# )
# def test_calculate_clear_sky_radiation(
#     solar_zenith_angle,
#     temperature,
#     relative_humidity,
#     atm_pressure,
#     expected,
# ):
#     """Test calculation of clear sky radiation."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_clear_sky_radiation,
#     )

#     computed_clear_sky_radiation = calculate_clear_sky_radiation(
#         solar_zenith_angle=solar_zenith_angle,
#         temperature=temperature,
#         relative_humidity=relative_humidity,
#         atmospheric_pressure=atm_pressure,
#     )
#     np.testing.assert_allclose(computed_clear_sky_radiation, expected, atol=1e-2)


# @pytest.mark.parametrize(
#     "solar_zenith_angle, leaf_incl_coefficient, solar_index, expected_coefficients",
#     [
#         (
#             np.repeat(45.0, 3),
#             1.0,
#             np.repeat(0.5, 3),
#             (np.array([[0.70, 0.7, 0.7], [1.0, 1.0, 1.0], [0.5, 0.5, 0.5]])),
#         ),
#         (
#             np.repeat(30.0, 3),
#             2.0,
#             np.repeat(1.0, 3),
#             (np.array([[0.75, 0.75, 0.75], [0.65, 0.65, 0.65], [0.72, 0.72, 0.72]])),
#         ),
#         (
#             np.repeat(85.0, 3),
#             5.0,
#             np.repeat(0.2, 3),
#             (np.array([[2.28, 2.28, 2.28], [0.99, 0.99, 0.99], [0.91, 0.91, 0.91]])),
#         ),
#     ],
# )
# def test_calculate_canopy_extinction_coefficients(
#     solar_zenith_angle,
#     leaf_incl_coefficient,
#     solar_index,
#     expected_coefficients,
# ):
#     """Test calculation of canopy extinction coefficients."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_canopy_extinction_coefficients,
#     )

#     computed_coefficients = calculate_canopy_extinction_coefficients(
#         solar_zenith_angle, leaf_incl_coefficient, solar_index
#     )
#     for computed, expected in zip(computed_coefficients, expected_coefficients):
#         np.testing.assert_allclose(computed, expected, atol=1e-2)


# @pytest.mark.parametrize(
#     "adj_pai, scatter_coeff, backward_coeff, diffuse_coeff, ground_refl, expected",
#     [
#         (
#             np.array([0.5, 1.0, 1.5]),
#             0.2,
#             0.3,
#             0.4,
#             0.6,
#             [
#                 np.array([0.310228, 0.317483, 0.322539]),
#                 np.array([0.207952, 0.142654, 0.097147]),
#                 np.array([0.930683, 0.952449, 0.967618]),
#                 np.array([0.069317, 0.047551, 0.032382]),
#             ],
#         ),
#         (
#             np.array([0.1, 0.2, 0.3]),
#             0.5,
#             0.2,
#             0.3,
#             0.8,
#             [
#                 np.array([-0.226365, -0.258451, -0.298267]),
#                 np.array([1.065912, 1.146128, 1.245667]),
#                 np.array([1.368131, 1.339416, 1.313454]),
#                 np.array([-0.368131, -0.339416, -0.313454]),
#             ],
#         ),
#     ],
# )
# def test_calculate_diffuse_radiation_parameters(
#     adj_pai, scatter_coeff, backward_coeff, diffuse_coeff, ground_refl, expected
# ):
#     """Test calculation of diffuse radiation parameters."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_diffuse_radiation_parameters,
#     )

#     result = calculate_diffuse_radiation_parameters(
#         adjusted_plant_area_index=adj_pai,
#         scatter_absorption_coefficient=scatter_coeff,
#         backward_scattering_coefficient=backward_coeff,
#         diffuse_scattering_coefficient=diffuse_coeff,
#         ground_reflectance=ground_refl,
#     )

#     np.testing.assert_allclose(result[0], expected[0], rtol=1e-5)
#     np.testing.assert_allclose(result[1], expected[1], rtol=1e-5)
#     np.testing.assert_allclose(result[2], expected[2], rtol=1e-5)
#     np.testing.assert_allclose(result[3], expected[3], rtol=1e-5)


# @pytest.mark.parametrize(
#     "apai, scat_alb, scat_abs, back_c, diff_c, gref, incl, delt, k, kd, sg, exp",
#     [
#         (
#             np.repeat(1.0, 3),
#             0.3,
#             0.5,
#             0.1,
#             0.2,
#             0.7,
#             1.0,
#             0.3,
#             np.repeat(0.5, 3),
#             np.repeat(0.4, 3),
#             5.67e-8,
#             [
#                 np.repeat(-0.0375, 3),
#                 np.repeat(1545642.023, 3),
#                 np.repeat(-1437844.330, 3),
#                 np.repeat(-0.0974, 3),
#                 np.repeat(2226060.190, 3),
#                 np.repeat(-506483.471, 3),
#             ],
#         ),
#         (
#             np.repeat(0.0, 3),
#             0.35,
#             0.55,
#             0.18,
#             0.25,
#             0.75,
#             1.1,
#             0.35,
#             np.repeat(0.55, 3),
#             np.repeat(0.45, 3),
#             5.67e-8,
#             [
#                 np.repeat(-0.063, 3),
#                 np.repeat(1568518.376, 3),
#                 np.repeat(-448147.255, 3),
#                 np.repeat(-0.165, 3),
#                 np.repeat(4087654.243, 3),
#                 np.repeat(-1167901.157, 3),
#             ],
#         ),
#     ],
# )
# def test_calculate_direct_radiation_parameters(
#     apai,
#     scat_alb,
#     scat_abs,
#     back_c,
#     diff_c,
#     gref,
#     incl,
#     delt,
#     k,
#     kd,
#     sg,
#     exp,
# ):
#     """Test calculation of direct radiation parameters."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_direct_radiation_parameters,
#     )

#     computed_parameters = calculate_direct_radiation_parameters(
#         adjusted_plant_area_index=apai,
#         scattering_albedo=scat_alb,
#         scatter_absorption_coefficient=scat_abs,
#         backward_scattering_coefficient=back_c,
#         diffuse_scattering_coefficient=diff_c,
#         ground_reflectance=gref,
#         inclination_distribution=incl,
#         delta_reflectance_transmittance=delt,
#         extinction_coefficient_k=k,
#         extinction_coefficient_kd=kd,
#         sigma=sg,
#     )
#     for computed, expected in zip(computed_parameters, exp):
#         np.testing.assert_allclose(computed, expected, atol=1e-2)


# def test_calculate_absorbed_shortwave_radiation():
#     """Test calculation of ground and canopy absorption, very basic."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_absorbed_shortwave_radiation,
#     )

#     # Define input parameters
#     plant_area_index_sum = np.repeat(2.0, 3)
#     leaf_orientation_coefficient = 0.5
#     leaf_reluctance_shortwave = 0.15
#     leaf_transmittance_shortwave = 0.05
#     clumping_factor = 0.9
#     ground_reflectance = 0.3
#     slope = np.repeat(5.0, 3)
#     aspect = np.repeat(180.0, 3)
#     latitude = np.repeat(45.0, 3)
#     longitude = np.repeat(-123.0, 3)
#     year = np.array([2023], dtype=np.int32)
#     month = np.array([6], dtype=np.int32)
#     day = np.array([21], dtype=np.int32)
#     local_time = np.array([12.0], dtype=np.float32)
#     topofcanopy_shortwave_radiation = np.repeat(800.0, 3)
#     topofcanopy_diffuse_radiation = np.repeat(200.0, 3)
#     leaf_inclination_angle_coefficient = 5.0

#     # Call the function to test
#     result = calculate_absorbed_shortwave_radiation(
#         plant_area_index_sum=plant_area_index_sum,
#         leaf_orientation_coefficient=leaf_orientation_coefficient,
#         leaf_reluctance_shortwave=leaf_reluctance_shortwave,
#         leaf_transmittance_shortwave=leaf_transmittance_shortwave,
#         clumping_factor=clumping_factor,
#         ground_reflectance=ground_reflectance,
#         slope=slope,
#         aspect=aspect,
#         latitude=latitude,
#         longitude=longitude,
#         year=year,
#         month=month,
#         day=day,
#         local_time=local_time,
#         topofcanopy_shortwave_radiation=topofcanopy_shortwave_radiation,
#         topofcanopy_diffuse_radiation=topofcanopy_diffuse_radiation,
#         leaf_inclination_angle_coefficient=leaf_inclination_angle_coefficient,
#     )

#     # Define expected output values
#     expected_ground_absorption = np.repeat(551.561586, 3)
#     expected_canopy_absorption = np.repeat(647.24574, 3)
#     expected_albedo = np.repeat(0.190943, 3)

#     # Assert the results
#     np.testing.assert_allclose(
#         result["ground_shortwave_absorption"],
#         expected_ground_absorption,
#         atol=1e-3,
#     )
#     np.testing.assert_allclose(
#         result["canopy_shortwave_absorption"],
#         expected_canopy_absorption,
#         atol=1e-3,
#     )
#     np.testing.assert_allclose(
#         result["albedo"],
#         expected_albedo,
#         atol=1e-3,
#     )


# def test_calculate_canopy_longwave_emission():
#     """Test calculation of canopy longwave emission."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_canopy_longwave_emission,
#     )

#     expected_emission = np.array(
#         [[425.643415, 437.179768, 431.382669], [454.922015, 460.954381, 448.949052]]
#     )

#     # Calculate the actual emission
#     result = calculate_canopy_longwave_emission(
#         leaf_emissivity=0.95,
#         canopy_temperature=np.array([[25, 27, 26], [30, 31, 29]]),
#         stefan_boltzmann_constant=5.67e-8,
#         zero_Celsius=273.15,
#     )

#     # Compare the result with the expected value
#     np.testing.assert_allclose(result, expected_emission, rtol=1e-6)


# def test_calculate_longwave_emission_ground():
#     """Test calculation of ground longwave emission."""

#     from virtual_ecosystem.models.abiotic.radiation import (
#         calculate_longwave_emission_ground,
#     )

#     expected_emission = np.array([349.6, 389.16])

#     # Calculate the actual emission
#     result = calculate_longwave_emission_ground(
#         ground_emissivity=0.92,
#         radiation_transmission_coefficient=np.array([0.6, 0.7]),
#         longwave_downward_radiation_sky=np.array([400, 450]),
#         canopy_longwave_emission=np.array([350, 360]),
#     )

#     # Compare the result with the expected value
#     np.testing.assert_allclose(result, expected_emission, rtol=1e-6)

# """Test module for abiotic.abiotic_model.energy_balance.py."""

# import numpy as np
# import pytest
# from xarray import DataArray

# from virtual_ecosystem.core.constants import CoreConsts
# from virtual_ecosystem.models.abiotic.constants import AbioticConsts


# def test_calculate_soil_absorption():
#     """Test that soil absorption is calculated correctly."""

#     from virtual_ecosystem.models.abiotic.soil_energy_balance import (
#         calculate_soil_absorption,
#     )

#     result = calculate_soil_absorption(
#         shortwave_radiation_surface=np.array([100, 10, 0]),
#         surface_albedo=np.array([0.2, 0.2, 0.2]),
#     )

#     np.testing.assert_allclose(result, np.array([80, 8, 0]), rtol=1e-04, atol=1e-04)


# def test_calculate_sensible_heat_flux_soil():
#     """Test sensible heat from soil is calculated correctly."""

#     from virtual_ecosystem.models.abiotic.soil_energy_balance import (
#         calculate_sensible_heat_flux_soil,
#     )

#     result = calculate_sensible_heat_flux_soil(
#         air_temperature_surface=np.array([290, 290, 290]),
#         topsoil_temperature=np.array([295, 290, 285]),
#         molar_density_air=np.array([38, 38, 38]),
#         specific_heat_air=np.array([29, 29, 29]),
#         aerodynamic_resistance=np.array([1250.0, 1250.0, 1250.0]),
#     )
#     np.testing.assert_allclose(
#         result,
#         np.array([4.408, 0.0, -4.408]),
#         rtol=1e-04,
#         atol=1e-04,
#     )


# def test_calculate_latent_heat_flux_from_soil_evaporation():
#     """Test evaporation to latent heat flux conversion works correctly."""

#     from virtual_ecosystem.models.abiotic.soil_energy_balance import (
#         calculate_latent_heat_flux_from_soil_evaporation,
#     )

#     result = calculate_latent_heat_flux_from_soil_evaporation(
#         soil_evaporation=np.array([0.001, 0.01, 0.1]),
#         latent_heat_vapourisation=np.array([2254.0, 2254.0, 2254.0]),
#     )
#     np.testing.assert_allclose(result, np.array([2.254, 22.54, 225.4]))


# def test_update_surface_temperature():
#     """Test surface temperature with positive and negative radiation flux."""

#     from virtual_ecosystem.models.abiotic.soil_energy_balance import (
#         update_surface_temperature,
#     )

#     result = update_surface_temperature(
#         topsoil_temperature=np.array([297, 297, 297]),
#         surface_net_radiation=np.array([100, 0, -100]),
#         surface_layer_depth=np.array([0.1, 0.1, 0.1]),
#         grid_cell_area=100,
#         update_interval=43200,
#         specific_heat_capacity_soil=AbioticConsts.specific_heat_capacity_soil,
#         volume_to_weight_conversion=1000.0,
#     )

#     np.testing.assert_allclose(result, np.array([297.00016, 297.0, 296.99984]))


# def test_calculate_ground_heat_flux():
#     """Test graound heat flux is calculated correctly."""

#     from virtual_ecosystem.models.abiotic.soil_energy_balance import (
#         calculate_ground_heat_flux,
#     )

#     result = calculate_ground_heat_flux(
#         soil_absorbed_radiation=np.array([100, 50, 0]),
#         topsoil_longwave_emission=np.array([10, 10, 10]),
#         topsoil_sensible_heat_flux=np.array([10, 10, 10]),
#         topsoil_latent_heat_flux=np.array([10, 10, 10]),
#     )
#     np.testing.assert_allclose(result, np.array([70, 20, -30]))


# @pytest.mark.skip("Possible bug - not switching in values")
# def test_calculate_soil_heat_balance(fixture_core_components, dummy_climate_data):
#     """Test full surface heat balance is run correctly."""

#     from virtual_ecosystem.models.abiotic.soil_energy_balance import (
#         calculate_soil_heat_balance,
#     )

#     data = dummy_climate_data
#     data["soil_evaporation"] = DataArray(
#         np.array([0.001, 0.01, 0.1, 0.1]), dims="cell_id"
#     )
#     data["molar_density_air"] = DataArray(
#         np.full((14, 4), 38), dims=["layers", "cell_id"]
#     )
#     data["specific_heat_air"] = DataArray(
#         np.full((14, 4), 29), dims=["layers", "cell_id"]
#     )
#     data["aerodynamic_resistance_surface"] = DataArray(np.repeat(1250.0, 4))
#     data["latent_heat_vapourisation"] = DataArray(
#         np.full((14, 4), 2254.0), dims=["layers", "cell_id"]
#     )

#     result = calculate_soil_heat_balance(
#         data=data,
#         time_index=0,
#         layer_structure=fixture_core_components.layer_structure,
#         update_interval=43200,
#         abiotic_consts=AbioticConsts(),
#         core_consts=CoreConsts(),
#     )

#     # Check if all variables were created
#     var_list = [
#         "soil_absorption",
#         "longwave_emission_soil",
#         "sensible_heat_flux_soil",
#         "latent_heat_flux_soil",
#         "ground_heat_flux",
#     ]

#     variables = [var for var in result if var not in var_list]
#     assert variables

#   # VIVI - I can't get these to work. I think there is a bug in the function, that was
#    # getting the total canopy absorption across all cells, not the per cell sum across
#    # layers, so not sure what the right answer is here.
#     test_values = {
#         "soil_absorption": np.repeat(79.625, 4),
#         "longwave_emission_soil": np.repeat(0.007258, 4),
#         "sensible_heat_flux_soil": np.repeat(3.397735, 4),
#         "latent_heat_flux_soil": np.array([2.254, 22.54, 225.4, 225.4]),
#        "ground_heat_flux": np.array([73.966007, 53.680007, -149.179993, -149.179993]),
#     }

#     for var, values in test_values.items():
#         assert np.allclose(result[var], values, rtol=1e-04, atol=1e-04)

# """Test module for abiotic.wind.py."""

# from contextlib import nullcontext as does_not_raise

# import numpy as np
# import pytest


# def test_calculate_zero_plane_displacement(dummy_climate_data):
#     """Test if calculated correctly and set to zero without vegetation."""

#   from virtual_ecosystem.models.abiotic.wind import calculate_zero_plane_displacement

#     result = calculate_zero_plane_displacement(
#         canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
#         leaf_area_index=np.array([0.0, np.nan, 7.0, 7.0]),
#         zero_plane_scaling_parameter=7.5,
#     )

#     np.testing.assert_allclose(result, np.array([0.0, 0.0, 25.86256, 25.86256]))


# def test_calculate_roughness_length_momentum(dummy_climate_data):
#     """Test roughness length governing momentum transfer."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_roughness_length_momentum,
#     )

#     result = calculate_roughness_length_momentum(
#         canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
#         plant_area_index=np.array([np.nan, 0.0, 7, 7]),
#         zero_plane_displacement=np.array([0.0, 0.0, 27.58673, 27.58673]),
#         diabatic_correction_heat=np.array([0.0, 0.0, 0.0, 0.0]),
#         substrate_surface_drag_coefficient=0.003,
#         drag_coefficient=0.2,
#         von_karman_constant=0.4,
#         min_roughness_length=0.01,
#     )

#     np.testing.assert_allclose(
#         result, np.array([0.01, 0.020206, 1.497673, 1.497673]), rtol=1e-3, atol=1e-3
#     )


# @pytest.mark.parametrize(
#     "air_temperature, friction_velocity, sensible_heat_flux, raises, expected",
#     [
#         (
#             np.repeat(25.0, 3),
#             np.repeat(0.5, 3),
#             np.repeat(100.0, 3),
#             does_not_raise(),
#             np.repeat(-114.541571, 3),
#         ),
#         (
#             np.repeat(15.0, 3),
#             np.repeat(0.1, 3),
#             np.repeat(-50.0, 3),
#             does_not_raise(),
#             np.repeat(1.771197, 3),
#         ),
#         (
#             np.repeat(10.0, 3),
#             np.repeat(0.3, 3),
#             np.repeat(0.0, 3),
#             pytest.raises(ValueError),
#             (),
#         ),
#         (
#             np.repeat(-10.0, 3),
#             np.repeat(0.6, 3),
#             np.repeat(150.0, 3),
#             does_not_raise(),
#             np.repeat(-116.461982, 3),
#         ),
#     ],
# )
# def test_calculate_monin_obukov_length(
#     air_temperature,
#     friction_velocity,
#     sensible_heat_flux,
#     raises,
#     expected,
# ):
#     """Test calculation of Monin-Obukov length."""
#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_monin_obukov_length,
#     )

#     with raises:
#         result = calculate_monin_obukov_length(
#             air_temperature=air_temperature,
#             friction_velocity=friction_velocity,
#             sensible_heat_flux=sensible_heat_flux,
#             specific_heat_air=np.repeat(1005, 3),
#             density_air=np.repeat(1.2, 3),
#             zero_degree=273.15,
#             von_karman_constant=0.4,
#             gravity=9.81,
#         )
#         np.testing.assert_allclose(result, expected, atol=1e-3)


# @pytest.mark.parametrize(
#     "reference_height, zero_plane_displacement, monin_obukov_length, expected",
#     [
#         (  # Typical case with positive zeta
#             np.repeat(10.0, 3),
#             np.repeat(10, 3),
#             np.repeat(50.0, 3),
#             np.repeat(0.0, 3),
#         ),
#         (  # Typical case with positive zeta
#             np.repeat(50.0, 3),
#             np.repeat(30, 3),
#             np.repeat(60.0, 3),
#             np.repeat(0.333, 3),
#         ),
#         (  # Case with zero zeta
#             np.repeat(10.0, 3),
#             np.repeat(10, 3),
#             np.repeat(1.0, 3),
#             np.repeat(0.0, 3),
#         ),
#         (  # Case with negative Monin-Obukov length
#             np.repeat(10.0, 3),
#             np.repeat(5, 3),
#             np.repeat(-5.0, 3),
#             np.repeat(-1.0, 3),
#         ),
#     ],
# )
# def test_calculate_stability_parameter(
#     reference_height, zero_plane_displacement, monin_obukov_length, expected
# ):
#     """Test calculation of stability parameter zeta."""
#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_stability_parameter,
#     )

#     result = calculate_stability_parameter(
#         reference_height, zero_plane_displacement, monin_obukov_length
#     )
#     np.testing.assert_allclose(result, expected, atol=1e-3)


# @pytest.mark.parametrize(
#     "stability_parameter, stability_formulation, expected_psi_h, expected_psi_m",
#     [
#         (
#             np.repeat(0.5, 3),
#             "Businger_1971",
#             np.repeat(-3.9, 3),
#             np.repeat(-3.0, 3),
#         ),  # Example for stable conditions, Businger_1971
#         (
#             np.repeat(0.5, 3),
#             "Dyer_1970",
#             np.repeat(-2.5, 3),
#             np.repeat(-2.5, 3),
#         ),  # Example for stable conditions, Dyer_1970
#         (
#             np.repeat(-0.5, 3),
#             "Businger_1971",
#             np.repeat(1.106216, 3),
#             np.repeat(0.87485, 3),
#         ),  # Unstable conditions, Businger_1971
#         (
#             np.repeat(-0.5, 3),
#             "Dyer_1970",
#             np.repeat(1.38629, 3),
#             np.repeat(0.793359, 3),
#         ),  # Unstable conditions, Dyer_1970
#         (
#             np.repeat(0.0, 3),
#             "Businger_1971",
#             np.repeat(0.0, 3),
#             np.repeat(0.0, 3),
#         ),  # Edge case for zero stability parameter, Businger_1971
#         (
#             np.repeat(0.0, 3),
#             "Dyer_1970",
#             np.repeat(0.0, 3),
#             np.repeat(0.0, 3),
#         ),  # Edge case for zero stability parameter, Dyer_1970
#     ],
# )
# def test_calculate_diabatic_correction_factors(
#     stability_parameter, stability_formulation, expected_psi_h, expected_psi_m
# ):
#     """Test calculation of diabatic correction factors."""

#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_diabatic_correction_factors,
#     )

#     result = calculate_diabatic_correction_factors(
#         stability_parameter, stability_formulation
#     )
#     np.testing.assert_allclose(result["psi_h"], expected_psi_h, rtol=1e-5)
#     np.testing.assert_allclose(result["psi_m"], expected_psi_m, rtol=1e-5)


# @pytest.mark.parametrize(
#     "stability_parameter, expected_phih",
#     [
#         (np.repeat(-0.5, 3), np.repeat(0.5, 3)),  # Unstable case
#         (np.repeat(0.0, 3), np.repeat(1.0, 3)),  # Neutral case
#         (np.repeat(1.0, 3), np.repeat(1.5, 3)),  # Stable case
#     ],
# )
# def test_calculate_diabatic_influence_heat(stability_parameter, expected_phih):
#     """Test calculation of diabatic influencing factor for heat."""
#     from virtual_ecosystem.models.abiotic.wind import (
#         calculate_diabatic_influence_heat,
#     )

#    result = calculate_diabatic_influence_heat(stability_parameter=stability_parameter)
#     np.testing.assert_allclose(result, expected_phih, atol=1e-6)


# # def test_calculate_diabatic_correction_above(dummy_climate_data):
# #     """Test diabatic correction factors for heat and momentum."""

# #     from virtual_ecosystem.models.abiotic.wind import (
# #         calculate_diabatic_correction_above,
# #     )

# #     abiotic_consts = AbioticConsts()
# #     core_const = CoreConsts()
# #     result = calculate_diabatic_correction_above(
# #         molar_density_air=np.repeat(28.96, 4),
# #         specific_heat_air=np.repeat(1.0, 4),
# #         temperature=dummy_climate_data["air_temperature"][0].to_numpy(),
# #         sensible_heat_flux=(
# #             dummy_climate_data["sensible_heat_flux_topofcanopy"].to_numpy()
# #         ),
# #         friction_velocity=dummy_climate_data["friction_velocity"].to_numpy(),
# #         wind_heights=dummy_climate_data["layer_heights"][0].to_numpy(),
# #         zero_plane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
# #         celsius_to_kelvin=core_const.zero_Celsius,
# #         von_karmans_constant=core_const.von_karmans_constant,
# #         yasuda_stability_parameters=abiotic_consts.yasuda_stability_parameters,
# #         diabatic_heat_momentum_ratio=abiotic_consts.diabatic_heat_momentum_ratio,
# #     )

# #     exp_result_h = np.array([0.105164, 0.024834, 0.008092, 0.008092])
# #     exp_result_m = np.array([0.063098, 0.0149, 0.004855, 0.004855])
# #     np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
# #     np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


# # @pytest.mark.parametrize(
# #     "air_temperature, wind_speed, expected_phi_m, expected_phi_h",
# #     [
# #         # Stable conditions (temperature increasing with height)
# #         (
# #             np.array([[15.0, 16.0], [14.5, 15.5]]),
# #             np.array([[2.1, 2.1], [2.0, 2.0]]),
# #             np.array([1.000389, 1.000388]),
# #             np.array([1.000389, 1.000388]),
# #         ),
# #         # Unstable conditions (temperature decreasing with height)
# #         (
# #             np.array([[15.0, 16.0], [16.0, 17.0]]),
# #             np.array([[2.0, 2.0], [3.0, 3.0]]),
# #             np.array([0.999685, 0.999686]),
# #             np.array([0.999685, 0.999686]),
# #         ),
# #     ],
# # )
# # def test_canopy_correction_conditions(
# #     air_temperature, wind_speed, expected_phi_m, expected_phi_h
# # ):
# #     """Test diabatic correction canopy for stable and unstable conditions."""

# #     from virtual_ecosystem.models.abiotic.wind import (
# #         calculate_diabatic_correction_canopy,
# #     )

# #     results = calculate_diabatic_correction_canopy(
# #         air_temperature,
# #         wind_speed,
# #         layer_heights=np.array([[20, 20], [10, 10]]),
# #         mean_mixing_length=np.array([[1.6, 1.6], [1.5, 1.5]]),
# #         stable_temperature_gradient_intercept=0.5,
# #         stable_wind_shear_slope=0.1,
# #         yasuda_stability_parameters=[0.2, 0.3, 0.4],
# #         richardson_bounds=[0.1, -0.1],
# #         gravity=9.81,
# #         celsius_to_kelvin=273.15,
# #     )

# #     # Assert results
# #   np.testing.assert_allclose(results["phi_m"], expected_phi_m, rtol=1e-4, atol=1e-4)
# #   np.testing.assert_allclose(results["phi_h"], expected_phi_h, rtol=1e-4, atol=1e-4)


# # def test_calculate_mean_mixing_length(dummy_climate_data):
# #     """Test mixing length with and without vegetation."""

# #     from virtual_ecosystem.models.abiotic.wind import calculate_mean_mixing_length

# #     result = calculate_mean_mixing_length(
# #         canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
# #         zero_plane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
# #         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
# #         mixing_length_factor=AbioticConsts.mixing_length_factor,
# #     )

# #     np.testing.assert_allclose(
# #         result, np.array([1.284154, 1.280886, 0.836903, 0.836903]), rtol=1e-4,
# # atol=1e-4
# #     )


# # def test_generate_relative_turbulence_intensity(
# #     dummy_climate_data_varying_canopy, fixture_core_components
# # ):
# #     """Test relative turbulence intensity for different true layers."""

# #     from virtual_ecosystem.models.abiotic.wind import (
# #         generate_relative_turbulence_intensity,
# #     )

# #     layer_heights = dummy_climate_data_varying_canopy["layer_heights"][
# #         fixture_core_components.layer_structure.index_filled_atmosphere
# #     ]

# #     result_t = generate_relative_turbulence_intensity(
# #         layer_heights=layer_heights,
# #         min_relative_turbulence_intensity=0.36,
# #         max_relative_turbulence_intensity=0.9,
# #         increasing_with_height=True,
# #     )

# #     exp_result_t = np.array(
# #         [
# #             [17.64, 17.64, 17.64, 17.64],
# #             [16.56, 16.56, 16.56, 16.56],
# #             [11.16, 11.16, np.nan, np.nan],
# #             [5.76, np.nan, np.nan, np.nan],
# #             [0.414, 0.414, 0.414, 0.414],
# #         ]
# #     )
# #     result_f = generate_relative_turbulence_intensity(
# #         layer_heights=layer_heights,
# #         min_relative_turbulence_intensity=0.36,
# #         max_relative_turbulence_intensity=0.9,
# #         increasing_with_height=False,
# #     )

# #     exp_result_f = np.array(
# #         [
# #             [-16.92, -16.92, -16.92, -16.92],
# #             [-15.84, -15.84, -15.84, -15.84],
# #             [-10.44, -10.44, np.nan, np.nan],
# #             [-5.04, np.nan, np.nan, np.nan],
# #             [0.306, 0.306, 0.306, 0.306],
# #         ]
# #     )
# #     np.testing.assert_allclose(result_t, exp_result_t, rtol=1e-3, atol=1e-3)
# #     np.testing.assert_allclose(result_f, exp_result_f, rtol=1e-3, atol=1e-3)


# # def test_calculate_wind_attenuation_coefficient(
# #     dummy_climate_data_varying_canopy, fixture_core_components
# # ):
# #     """Test wind attenuation coefficient with different canopy layers."""

# #     from virtual_ecosystem.models.abiotic.wind import (
# #         calculate_wind_attenuation_coefficient,
# #     )

# #     # TODO: Occupied canopies - the plants model should populate the filled_canopies
# #     #       index in the data at some point.

# #     # VIVI - this function was being used in two ways. One with the true aboveground
# #     # rows and one with only the true canopy rows, adding the rows for above and
# # surface
# #     # My updates assume the former approach, so I've updated this test to match. The
# #     # results have changed.

# #     lyr_strct = fixture_core_components.layer_structure

# #     leaf_area_index = dummy_climate_data_varying_canopy["leaf_area_index"][
# #         lyr_strct.index_filled_atmosphere
# #     ].to_numpy()

# #     relative_turbulence_intensity = dummy_climate_data_varying_canopy[
# #         "relative_turbulence_intensity"
# #     ][lyr_strct.index_filled_atmosphere].to_numpy()

# #     # TODO - create a scalar index for this canopy top layer [1]
# #     canopy_height = (
# #         dummy_climate_data_varying_canopy.data["layer_heights"][1].to_numpy(),
# #     )

# #     result = calculate_wind_attenuation_coefficient(
# #         canopy_height=canopy_height,
# #         leaf_area_index=leaf_area_index,
# #         mean_mixing_length=np.array([1.35804, 1.401984, 0.925228, 0.925228]),
# #         drag_coefficient=AbioticConsts.drag_coefficient,
# #         relative_turbulence_intensity=relative_turbulence_intensity,
# #     )

# #     exp_result = np.array(
# #         # [
# #         #     [0.0, 0.0, 0.0, 0.0],
# #         #     [0.12523, 0.121305, 0.183812, 0.183812],
# #         #     [0.133398, 0.129216, np.nan, np.nan],
# #         #     [0.197945, np.nan, np.nan, np.nan],
# #         #     # [0.197945, 0.129216, 0.183812, 0.183812],
# #         #     [0.197945, 0.129216, 0.183812, 0.183812],
# #         # ]
# #         [
# #             [0.0, 0.0, 0.0, 0.0],
# #             [0.13339771, 0.12921647, 0.19579976, 0.19579976],
# #             [0.19794498, 0.19174057, np.nan, np.nan],
# #             [0.3835184, np.nan, np.nan, np.nan],
# #             [0.3835184, 0.19174057, 0.19579976, 0.19579976],
# #         ]
# #     )
# #     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# # def test_wind_log_profile(fixture_core_components, dummy_climate_data):
# #     """Test log wind profile."""

# #     from virtual_ecosystem.models.abiotic.wind import wind_log_profile

# #     layer_heights = dummy_climate_data["layer_heights"][
# #         fixture_core_components.layer_structure.index_filled_atmosphere
# #     ].to_numpy()

# #     result = wind_log_profile(
# #         height=layer_heights,
# #         zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
# #         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
# #         diabatic_correction_momentum=np.array([0.105164, 0.024834, 0.008092,
# # 0.008092]),
# #     )

# #     exp_result = np.array(
# #         [
# #             [7.645442, 1.551228, 1.534468, 1.534468],
# #             [7.580903, 1.195884, 0.930835, 0.930835],
# #             [7.175438, np.nan, np.nan, np.nan],
# #             [6.482291, np.nan, np.nan, np.nan],
# #             [1.877121, np.nan, np.nan, np.nan],
# #         ]
# #     )

# #     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# # def test_calculate_friction_velocity_reference_height(dummy_climate_data):
# #     """Calculate friction velocity."""

# #     from virtual_ecosystem.models.abiotic.wind import (
# #         calculate_friction_velocity_reference_height,
# #     )

# #     result = calculate_friction_velocity_reference_height(
# #         wind_speed_ref=(
# #             dummy_climate_data.data["wind_speed_ref"].isel(time_index=0).to_numpy()
# #         ),
# #         reference_height=(dummy_climate_data["layer_heights"][1] + 10).to_numpy(),
# #         zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
# #         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
# #       diabatic_correction_momentum=np.array([0.063098, 0.0149, 0.004855, 0.004855]),
# #         von_karmans_constant=CoreConsts.von_karmans_constant,
# #         min_friction_velocity=0.001,
# #     )
# #     exp_result = np.array([0.051108, 0.171817, 0.155922, 0.155922])
# #     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# # def test_calculate_wind_above_canopy():
# #     """Wind speed above canopy."""

# #     from virtual_ecosystem.models.abiotic.wind import calculate_wind_above_canopy

# #     result = calculate_wind_above_canopy(
# #         friction_velocity=np.array([0.0, 0.819397, 1.423534, 1.423534]),
# #         wind_height_above=np.array(
# #             [[2.0, 32.0, 32.0, 32.0], [np.nan, 30.0, 30.0, 30.0]]
# #         ),
# #         zeroplane_displacement=np.array([0.0, 25.312559, 27.58673, 27.58673]),
# #         roughness_length_momentum=np.array([0.017, 1.4533, 0.9591, 0.9591]),
# #         diabatic_correction_momentum=np.array([0.003, 0.026, 0.013, 0.013]),
# #         von_karmans_constant=CoreConsts.von_karmans_constant,
# #         min_wind_speed_above_canopy=0.55,
# #     )

# #     exp_result = np.array(
# #       [[0.55, 3.180068, 5.478385, 5.478385], [np.nan, 2.452148, 3.330154, 3.330154]]
# #     )
# #     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# # def test_calculate_wind_canopy(
# #     dummy_climate_data_varying_canopy, fixture_core_components
# # ):
# #     """Test below canopy wind profile."""

# #     from virtual_ecosystem.models.abiotic.wind import calculate_wind_canopy

# #     lyr_strct = fixture_core_components.layer_structure

#      # TODO we want to use fixture here, but there is a conflict with expected results
# #     # in conductivities (attenuation coefficient two orders of magnitude different,
# # and
# #     # test fixture does not include gradient.) FIX in separate PR.
# #     attenuation_coeff = np.array(
# #         [
# #             [0.12523, 0.121305, 0.183812, 0.183812],
# #             [0.133398, 0.129216, np.nan, np.nan],
# #             [0.197945, np.nan, np.nan, np.nan],
# #             [0.197945, 0.129216, 0.183812, 0.183812],
# #         ]
# #     )

# #     layer_heights_np = dummy_climate_data_varying_canopy["layer_heights"].to_numpy()
# #     layer_heights = layer_heights_np[
# #         np.logical_or(lyr_strct.index_filled_canopy, lyr_strct.index_surface)
# #     ]
# #     canopy_height = layer_heights_np[1]

# #     result = calculate_wind_canopy(
# #         top_of_canopy_wind_speed=np.array([0.5, 5.590124, 10.750233, 10.750233]),
# #         wind_layer_heights=layer_heights,
# #         canopy_height=canopy_height,
# #         attenuation_coefficient=attenuation_coeff,
# #     )

# #     exp_result = np.array(
# #         [
# #             [0.5, 5.590124, 10.750233, 10.750233],
# #             [0.478254, 5.354458, np.nan, np.nan],
# #             [0.438187, np.nan, np.nan, np.nan],
# #             [0.410478, 4.914629, 8.950668, 8.950668],
# #         ]
# #     )
# #     np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


# # def test_calculate_wind_profile(
# #     dummy_climate_data_varying_canopy, fixture_core_components
# # ):
# #     """Test full update of wind profile."""

# #     from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile

# #     lyr_strct = fixture_core_components.layer_structure

# #     # VIVI - same deal here. Feeding the full true aboveground rows into this, not
# # just
# #     # the true canopy rows. Seeing minor test value changes as a result.
# #     leaf_area_index = dummy_climate_data_varying_canopy["leaf_area_index"][
# #         lyr_strct.index_filled_atmosphere
# #     ].to_numpy()
# #     layer_heights = dummy_climate_data_varying_canopy["layer_heights"][
# #         lyr_strct.index_filled_atmosphere
# #     ].to_numpy()
# #     air_temperature = dummy_climate_data_varying_canopy["air_temperature"][
# #         lyr_strct.index_filled_atmosphere
# #     ].to_numpy()

# #     wind_update = calculate_wind_profile(
# #         canopy_height=layer_heights[1],
# #         wind_height_above=layer_heights[0:2],
# #         wind_layer_heights=layer_heights,
# #         leaf_area_index=leaf_area_index,
# #         air_temperature=air_temperature,
# #         atmospheric_pressure=np.repeat(96.0, 4),
# #         sensible_heat_flux_topofcanopy=np.array([100.0, 50.0, 10.0, 10.0]),
# #         wind_speed_ref=np.array([0.1, 5.0, 10.0, 10.0]),
# #         wind_reference_height=(layer_heights[1] + 10),
# #         abiotic_constants=AbioticConsts(),
# #         core_constants=CoreConsts(),
# #     )

# #     friction_velocity_exp = np.array([0.012793, 0.84372, 1.811774, 1.811774])
# #     wind_speed_exp = np.array(
# #         # [
# #         #     [0.1, 3.719967, 7.722811, 7.722811],
# #         #     [0.1, 3.226327, 6.915169, 6.915169],
# #         #     [0.09551, 3.106107, np.nan, np.nan],
# #         #     [0.087254, np.nan, np.nan, np.nan],
# #         #     [0.08156, 2.880031, 6.39049, 6.39049],
# #         # ]
# #         [
# #             [0.1, 3.7199665, 7.72281114, 7.72281114],
# #             [0.1, 3.22632714, 6.91516866, 6.91516866],
# #             [0.09341001, 3.04955397, np.nan, np.nan],
# #             [0.07678466, np.nan, np.nan, np.nan],
# #             [0.06737292, 2.7260693, 6.35768904, 6.35768904],
# #         ]
# #     )

# #     np.testing.assert_allclose(
#          wind_update["friction_velocity"], friction_velocity_exp, rtol=1e-3, atol=1e-3
# #     )
# #     np.testing.assert_allclose(
# #         wind_update["wind_speed"], wind_speed_exp, rtol=1e-3, atol=1e-3
# #     )
