"""Test module for abiotic.conductivities.py."""

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts


def test_initialise_conductivities(dummy_climate_data, fixture_core_components):
    """Test conductivities are initialised correctly."""

    from virtual_ecosystem.models.abiotic.conductivities import (
        initialise_conductivities,
    )

    lyr_strct = fixture_core_components.layer_structure

    result = initialise_conductivities(
        layer_structure=lyr_strct,
        layer_heights=dummy_climate_data["layer_heights"],
        initial_air_conductivity=50.0,
        top_leaf_vapour_conductivity=0.32,
        bottom_leaf_vapour_conductivity=0.25,
        top_leaf_air_conductivity=0.19,
        bottom_leaf_air_conductivity=0.13,
    )

    exp_air_cond = lyr_strct.from_template()
    exp_air_cond[lyr_strct.index_atmosphere] = np.repeat(
        a=[4.166667, 3.33333333, 6.66666667], repeats=[1, 10, 1]
    )[:, None]

    exp_leaf_vap_cond = lyr_strct.from_template()
    exp_leaf_vap_cond[lyr_strct.index_filled_canopy] = np.array(
        [0.254389, 0.276332, 0.298276]
    )[:, None]

    exp_leaf_air_cond = lyr_strct.from_template()
    exp_leaf_air_cond[lyr_strct.index_filled_canopy] = np.array(
        [0.133762, 0.152571, 0.171379]
    )[:, None]

    np.testing.assert_allclose(
        result["air_heat_conductivity"], exp_air_cond, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_vapour_conductivity"], exp_leaf_vap_cond, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_air_heat_conductivity"], exp_leaf_air_cond, rtol=1e-04, atol=1e-04
    )


def test_interpolate_along_heights(dummy_climate_data, fixture_core_components):
    """Test linear interpolation along heights."""

    from virtual_ecosystem.models.abiotic.conductivities import (
        interpolate_along_heights,
    )

    lyr_strct = fixture_core_components.layer_structure

    layer_heights = dummy_climate_data["layer_heights"].to_numpy()

    result = interpolate_along_heights(
        start_height=layer_heights[lyr_strct.index_surface],
        end_height=layer_heights[lyr_strct.index_above],
        target_heights=layer_heights[lyr_strct.index_filled_atmosphere],
        start_value=50.0,
        end_value=20.0,
    )

    # Get layer structure and reduce to only atmospheric layers
    exp_result = lyr_strct.from_template()
    exp_result[lyr_strct.index_filled_atmosphere] = np.array(
        [20.0, 21.88087774, 31.28526646, 40.68965517, 50.0]
    )[:, None]
    exp_result = exp_result[lyr_strct.index_filled_atmosphere]

    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_interpolate_along_heights_arrays(fixture_core_components, dummy_climate_data):
    """Test linear interpolation along heights with arrays of boundary values."""

    # TODO - I don't think this differs from the test above.

    from virtual_ecosystem.models.abiotic.conductivities import (
        interpolate_along_heights,
    )

    lyr_strct = fixture_core_components.layer_structure

    # Extract the block of atmospheric layer heights.
    layer_heights = dummy_climate_data["layer_heights"][
        lyr_strct.index_atmosphere
    ].to_numpy()

    # Interpolate from the top to bottom across the atmosphere
    result = interpolate_along_heights(
        start_height=layer_heights[-1],
        end_height=layer_heights[0],
        target_heights=layer_heights,
        start_value=np.repeat(50.0, 4),
        end_value=np.repeat(20.0, 4),
    )

    # The function only returns values for the atmospheric layers, so fill the template
    # and then truncate to the atmosphere.
    exp_result = lyr_strct.from_template()
    exp_result[lyr_strct.index_filled_atmosphere] = np.array(
        [20.0, 21.88087774, 31.28526646, 40.68965517, 50.0]
    )[:, None]
    exp_result = exp_result[lyr_strct.index_atmosphere]

    np.testing.assert_allclose(
        result, exp_result, rtol=1e-04, atol=1e-04, equal_nan=True
    )


def test_calculate_air_heat_conductivity_above(dummy_climate_data):
    """Test heat conductivity above canopy."""

    from virtual_ecosystem.models.abiotic.conductivities import (
        calculate_air_heat_conductivity_above,
    )

    result = calculate_air_heat_conductivity_above(
        height_above_canopy=dummy_climate_data["layer_heights"][0],
        zero_displacement_height=(
            dummy_climate_data["zero_displacement_height"].to_numpy()
        ),
        canopy_height=dummy_climate_data["layer_heights"][1],
        friction_velocity=dummy_climate_data["friction_velocity"].to_numpy(),
        molar_density_air=dummy_climate_data["molar_density_air"][0].to_numpy(),
        diabatic_correction_heat=(
            dummy_climate_data["diabatic_correction_heat_above"].to_numpy()
        ),
        von_karmans_constant=CoreConsts.von_karmans_constant,
    )
    np.testing.assert_allclose(
        result,
        np.array([523.39996, 218.083317, 87.233327, 87.233327]),
        rtol=1e-04,
        atol=1e-04,
    )


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
    from virtual_ecosystem.models.abiotic.conductivities import (
        calculate_free_convection,
    )

    result = calculate_free_convection(
        leaf_dimension=leaf_dimension, sensible_heat_flux=sensible_heat_flux
    )
    np.testing.assert_allclose(result, expected_gha, atol=1e-6)


def test_calculate_stomatal_conductance():
    """Test calculation of stomatal conductance."""

    from virtual_ecosystem.models.abiotic.conductivities import (
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


# def test_calculate_air_heat_conductivity_canopy(dummy_climate_data):
#     """Test calculate air heat conductivity in canopy."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_air_heat_conductivity_canopy,
#     )

#     result = calculate_air_heat_conductivity_canopy(
#         attenuation_coefficient=(
#             dummy_climate_data["attenuation_coefficient"][1].to_numpy()
#         ),
#         mean_mixing_length=dummy_climate_data["mean_mixing_length"].to_numpy(),
#         molar_density_air=dummy_climate_data["molar_density_air"][1].to_numpy(),
#         upper_height=np.repeat(10.0, 4),
#         lower_height=np.repeat(5.0, 4),
#         relative_turbulence_intensity=(
#             dummy_climate_data["relative_turbulence_intensity"][1].to_numpy()
#         ),
#         top_of_canopy_wind_speed=np.repeat(1.0, 4),
#         diabatic_correction_momentum=(
#             dummy_climate_data["diabatic_correction_momentum_canopy"].to_numpy()
#         ),
#         canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
#     )
#     exp_result = np.repeat(0.236981, 4)
#     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


# def test_calculate_leaf_air_heat_conductivity(
#     dummy_climate_data, fixture_core_components
# ):
#     """Test calculation of leaf air heat conductivity."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_leaf_air_heat_conductivity,
#     )

#     lyr_strct = fixture_core_components.layer_structure
#     abiotic_consts = AbioticConsts()

#     result = calculate_leaf_air_heat_conductivity(
#         temperature=dummy_climate_data["air_temperature"].to_numpy(),
#         wind_speed=dummy_climate_data["wind_speed"].to_numpy(),
#         characteristic_dimension_leaf=0.1,
#         temperature_difference=(
#             dummy_climate_data["canopy_temperature"]
#             - dummy_climate_data["air_temperature"]
#         ).to_numpy(),
#         molar_density_air=dummy_climate_data["molar_density_air"].to_numpy(),
#         kinematic_viscosity_parameters=abiotic_consts.kinematic_viscosity_parameters,
#         thermal_diffusivity_parameters=abiotic_consts.thermal_diffusivity_parameters,
#         grashof_parameter=abiotic_consts.grashof_parameter,
#         forced_conductance_parameter=abiotic_consts.forced_conductance_parameter,
#         positive_free_conductance_parameter=(
#             abiotic_consts.positive_free_conductance_parameter
#         ),
#         negative_free_conductance_parameter=(
#             abiotic_consts.negative_free_conductance_parameter
#         ),
#     )
#     exp_result = lyr_strct.from_template()
#     exp_result[lyr_strct.index_filled_canopy] = np.array(
#         [0.065242, 0.065062, 0.064753]
#     )[:, None]

#     np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


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
# :
#     """Test update current conductivities."""

#     from virtual_ecosystem.models.abiotic.conductivities import (
#         calculate_current_conductivities,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     result = calculate_current_conductivities(
#         data=dummy_climate_data,
#         characteristic_dimension_leaf=0.01,
#         von_karmans_constant=CoreConsts.von_karmans_constant,
#         abiotic_constants=AbioticConsts(),
#     )

#     exp_gt = lyr_strct.from_template()
#     exp_gt[lyr_strct.index_above] = np.array(
#         [1.460964e02, 6.087350e01, 2.434940e01, 2.434940e01]
#     )
#     exp_gt[lyr_strct.index_flux_layers] = np.array(
#         [1.95435e03, 1.414247e01, 0.125081, 13.654908]
#     )[:, None]

#     exp_gv = lyr_strct.from_template()
#     exp_gv[lyr_strct.index_filled_canopy] = np.array([0.203513, 0.202959, 0.202009])[
#         :, None
#     ]

#     exp_gha = lyr_strct.from_template()
#     exp_gha[lyr_strct.index_filled_canopy] = np.array([0.206312, 0.205743, 0.204766])[
#         :, None
#     ]

#     exp_gtr = lyr_strct.from_template()
#     exp_gtr[lyr_strct.index_flux_layers] = np.array(
#         [1.954354e03, 1.403429e01, 0.123447, 0.604689]
#     )[:, None]

#     np.testing.assert_allclose(
#         result["air_heat_conductivity"], exp_gt, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["leaf_air_heat_conductivity"], exp_gha, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["conductivity_from_ref_height"], exp_gtr, rtol=1e-04, atol=1e-04
#     )
