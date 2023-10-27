"""Test module for wind.py."""


import numpy as np
import pytest
from xarray import DataArray

from virtual_rainforest.models.abiotic.constants import AbioticConsts


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in wind tests.

    One grid cell has no vegetation, two grid cells represent a range of values.
    """

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=3, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["canopy_height"] = DataArray([0, 10, 50], dims=["cell_id"])
    data["wind_layer_heights"] = DataArray(
        [[0.1, 5, 15], [1, 15, 25], [5, 25, 55]], dims=["cell_id", "layers"]
    )
    data["leaf_area_index"] = DataArray(
        [
            [0, 1, 5],
            [0, 2, 5],
            [0, 3, 5],
        ],
        dims=["cell_id", "layers"],
    )
    data["air_temperature"] = DataArray([30, 20, 30], dims=["cell_id"])
    data["atmospheric_pressure"] = DataArray([101, 102, 103], dims=["cell_id"])
    data["sensible_heat_flux_topofcanopy"] = DataArray([100, 50, 10], dims=["cell_id"])
    data["friction_velocity"] = DataArray([12, 5, 2], dims=["cell_id"])
    data["wind_speed_ref"] = DataArray([0, 5, 10], dims=["cell_id"])

    return data


def test_calculate_zero_plane_displacement(dummy_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_zero_plane_displacement

    plant_area_index = dummy_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_zero_plane_displacement(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        plant_area_index=plant_area_index.to_numpy(),
        zero_plane_scaling_parameter=AbioticConsts.zero_plane_scaling_parameter,
    )

    np.testing.assert_allclose(result, np.array([0.0, 8.620853, 43.547819]))


def test_calculate_roughness_length_momentum(dummy_data):
    """Test roughness length governing momentum transfer."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    plant_area_index = dummy_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_roughness_length_momentum(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        plant_area_index=plant_area_index.to_numpy(),
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
        von_karman_constant=AbioticConsts.von_karmans_constant,
    )

    np.testing.assert_allclose(
        result, np.array([0.003, 0.434662, 1.521318]), rtol=1e-3, atol=1e-3
    )


def test_calculate_diabatic_correction_above(dummy_data):
    """Test diabatic correction factors for heat and momentum."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_diabatic_correction_above,
    )

    result = calculate_diabatic_correction_above(
        temperature=dummy_data["air_temperature"].to_numpy(),
        atmospheric_pressure=dummy_data["atmospheric_pressure"].to_numpy(),
        sensible_heat_flux=dummy_data["sensible_heat_flux_topofcanopy"].to_numpy(),
        friction_velocity=dummy_data["friction_velocity"].to_numpy(),
        wind_heights_above_canopy=np.array([1, 15, 50]),
        zero_plane_displacement=np.array([0, 8, 43]),
        celsius_to_kelvin=AbioticConsts.celsius_to_kelvin,
        standard_pressure=AbioticConsts.standard_pressure,
        standard_mole=AbioticConsts.standard_mole,
        molar_heat_capacity_air=AbioticConsts.molar_heat_capacity_air,
        specific_heat_equ_factor_1=AbioticConsts.specific_heat_equ_factor_1,
        specific_heat_equ_factor_2=AbioticConsts.specific_heat_equ_factor_2,
        von_karmans_constant=AbioticConsts.von_karmans_constant,
    )

    exp_result_h = np.array([7.5154e-05, 6.2562e-04, 3.0957e-04])
    exp_result_m = np.array([4.5093e-05, 3.7534e-04, 1.857e-04])
    np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


def test_calculate_wind_attenuation_coefficient(dummy_data):
    """Test wind attenuation coefficient with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_wind_attenuation_coefficient,
    )

    plant_area_index = dummy_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_wind_attenuation_coefficient(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        plant_area_index=plant_area_index,
        mixing_length=np.array([0, 0.4, 1.5]),
        drag_coefficient=AbioticConsts.drag_coefficient,
        relative_turbulence_intensity=AbioticConsts.relative_turbulence_intensity,
        diabatic_correction_factor_below=AbioticConsts.diabatic_correction_factor_below,
    )

    np.testing.assert_allclose(result, np.array([0.0, 5.91608, 7.302967]))


def test_calculate_mixing_length(dummy_data):
    """Test mixing length with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_mixing_length

    result = calculate_mixing_length(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        zero_plane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        mixing_length_factor=AbioticConsts.mixing_length_factor,
    )

    np.testing.assert_allclose(
        result, np.array([0, 0.419, 1.467]), rtol=1e-3, atol=1e-3
    )


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


def test_calculate_wind_profile(dummy_data):
    """Test if wind profile is calculated correctly for different height."""

    from virtual_rainforest.models.abiotic.wind import calculate_wind_profile

    plant_area_index = dummy_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_wind_profile(
        wind_speed_ref=dummy_data["wind_speed_ref"].to_numpy(),
        wind_layer_heights=np.array([[5, 12, 60], [0.1, 8, 10]]),
        reference_height=10.0,
        attenuation_coefficient=np.array([0, 4, 7]),
        plant_area_index=plant_area_index,
        canopy_height=dummy_data["canopy_height"].to_numpy(),
        diabatic_correction_momentum=np.array([0, 0, 0]),
        ground_layer_vegetation_height=0.1,
        roughness_sublayer_depth_parameter=(
            AbioticConsts.roughness_sublayer_depth_parameter
        ),
        zero_plane_scaling_parameter=AbioticConsts.zero_plane_scaling_parameter,
        substrate_surface_drag_coefficient=(
            AbioticConsts.substrate_surface_drag_coefficient
        ),
        roughness_element_drag_coefficient=(
            AbioticConsts.roughness_element_drag_coefficient
        ),
        max_ratio_wind_to_friction_velocity=(
            AbioticConsts.max_ratio_wind_to_friction_velocity
        ),
        von_karmans_constant=AbioticConsts.von_karmans_constant,
    )

    np.testing.assert_allclose(
        result,
        np.array([[0, 7.935657, 24.623732], [0, 1.471923, 0.036979]]),
        rtol=1e-3,
        atol=1e-3,
    )


# def test_calculate_wind_above_canopy(dummy_data):
#     """Test wind above canopy."""

#     from virtual_rainforest.models.abiotic import wind

#     result = wind.calculate_wind_above_canopy(
#         wind_heights=DataArray(
#             [[10, 20, 30], [20, 30, 40], [40, 50, 60]], dims=["heights", "cell_id"]
#         ),
#         zero_plane_displacement=DataArray([0, 10, 10], dims="cell_id"),
#         roughness_length_momentum=DataArray([0.003, 0.4, 1.5], dims="cell_id"),
#         diabatic_correction_momentum_above=DataArray(
#             [[1, 1, 1], [1, 1, 1], [1, 1, 1]], dims=["heights", "cell_id"]
#         ),
#         friction_velocity=dummy_data["friction_velocity"],
#     )

#     xr.testing.assert_allclose(
#         result,
#         DataArray(
#             [
#                 [244.3518425, 265.14625792, 285.94067333],
#                 [41.23594781, 49.90028757, 58.56462732],
#                 [13.95133583, 15.97866137, 18.53278949],
#             ],
#             dims=["cell_id", "heights"],
#         ),
#     )


# def test_calculate_wind_below_canopy(dummy_data):
#     """Test wind within canopy."""

#     from virtual_rainforest.models.abiotic import wind

#     result = wind.calculate_wind_below_canopy(
#         canopy_node_heights=dummy_data.data["canopy_node_heights"],
#         wind_profile_above=DataArray(
#             [
#                 [244.0, 265.0, 285.0],
#                 [41.0, 49.0, 58.0],
#                 [13.0, 15.0, 18.0],
#             ],
#             dims=["cell_id", "heights"],
#         ),
#         wind_attenuation_coefficient=DataArray([0, 0.1, 0.3], dims=["cell_id"]),
#         canopy_height=dummy_data.data["canopy_height"],
#     )

#     xr.testing.assert_allclose(
#         result,
#         DataArray(
#             [
#                 [0.0, 0.0, 0.0],
#                 [52.48057, 60.973724, 67.386386],
#                 [13.334728, 15.492744, 16.450761],
#             ],
#             dims=["cell_id", "canopy_layers"],
#         ),
#     )


# def test_calculate_wind_profile(dummy_data):
#     """Test wind profile above and within canopy."""

#     from virtual_rainforest.models.abiotic import wind

#     result = wind.calculate_wind_profile(
#         wind_heights=DataArray(
#             [[10, 20, 30], [20, 30, 40], [40, 50, 60]], dims=["heights", "cell_id"]
#         ),
#         canopy_node_heights=dummy_data.data["canopy_node_heights"],
#         data=dummy_data,
#     )

#     # check wind above canopy
#     xr.testing.assert_allclose(
#         result[0],
#         DataArray(
#             DataArray(
#                 [
#                     [244.351842, 265.146258, 285.940673],
#                     [46.458135, 54.341054, 62.595567],
#                     [0.0, 0.0, 13.311866],
#                 ],
#                 dims=["cell_id", "heights"],
#             ),
#         ),
#     )
#     # check wind below canopy
#     xr.testing.assert_allclose(
#         result[1],
#         DataArray(
#             [
#                 [0.0, 0.0, 0.0],
#                 [5.950523e-02, 2.030195e03, 2.135631e06],
#                 [6.086929e-03, 2.846548e-01, 1.325216e00],
#             ],
#             dims=["cell_id", "canopy_layers"],
#         ),
#     )
