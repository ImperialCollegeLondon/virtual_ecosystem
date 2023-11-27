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

    leaf_area_index = dummy_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_zero_plane_displacement(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        leaf_area_index=leaf_area_index.to_numpy(),
        zero_plane_scaling_parameter=AbioticConsts.zero_plane_scaling_parameter,
    )

    np.testing.assert_allclose(result, np.array([0.0, 8.620853, 43.547819]))


def test_calculate_roughness_length_momentum(dummy_data):
    """Test roughness length governing momentum transfer."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    leaf_area_index = dummy_data.data["leaf_area_index"].sum(dim="layers")
    result = calculate_roughness_length_momentum(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
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
        molar_density_air=np.repeat(28.96, 3),
        specific_heat_air=np.repeat(1, 3),
        temperature=dummy_data["air_temperature"].to_numpy(),
        sensible_heat_flux=dummy_data["sensible_heat_flux_topofcanopy"].to_numpy(),
        friction_velocity=dummy_data["friction_velocity"].to_numpy(),
        wind_heights=np.array([1, 15, 50]),
        zero_plane_displacement=np.array([0, 8, 43]),
        celsius_to_kelvin=AbioticConsts.celsius_to_kelvin,
        von_karmans_constant=AbioticConsts.von_karmans_constant,
        yasuda_stability_parameter1=AbioticConsts.yasuda_stability_parameter1,
        yasuda_stability_parameter2=AbioticConsts.yasuda_stability_parameter2,
        yasuda_stability_parameter3=AbioticConsts.yasuda_stability_parameter3,
        diabatic_heat_momentum_ratio=AbioticConsts.diabatic_heat_momentum_ratio,
    )

    exp_result_h = np.array([0.003044, 0.026923, 0.012881])
    exp_result_m = np.array([0.001827, 0.016154, 0.007729])
    np.testing.assert_allclose(result["psi_h"], exp_result_h, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(result["psi_m"], exp_result_m, rtol=1e-4, atol=1e-4)


def test_calculate_mean_mixing_length(dummy_data):
    """Test mixing length with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import calculate_mean_mixing_length

    result = calculate_mean_mixing_length(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        zero_plane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        mixing_length_factor=AbioticConsts.mixing_length_factor,
    )

    np.testing.assert_allclose(
        result, np.array([0, 0.419, 1.467]), rtol=1e-3, atol=1e-3
    )


def test_generate_relative_turbulence_intensity(dummy_data):
    """Test relative turbulence intensity."""

    from virtual_rainforest.models.abiotic.wind import (
        generate_relative_turbulence_intensity,
    )

    result = generate_relative_turbulence_intensity(
        layer_heights=dummy_data["wind_layer_heights"].to_numpy(),
        min_relative_turbulence_intensity=(
            AbioticConsts.min_relative_turbulence_intensity
        ),
        max_relative_turbulence_intensity=(
            AbioticConsts.max_relative_turbulence_intensity
        ),
        increasing_with_height=True,
    )

    exp_result = np.array(
        [[0.414, 3.06, 8.46], [0.9, 8.46, 13.86], [3.06, 13.86, 30.06]]
    )
    np.testing.assert_allclose(result, exp_result)


def test_calculate_wind_attenuation_coefficient(dummy_data):
    """Test wind attenuation coefficient with and without vegetation."""

    from virtual_rainforest.models.abiotic.wind import (
        calculate_wind_attenuation_coefficient,
    )

    leaf_area_index = dummy_data.data["leaf_area_index"].to_numpy()
    relative_turbulence_intensity = np.array(
        [[0.414, 3.06, 8.46], [0.9, 8.46, 13.86], [3.06, 13.86, 30.06]]
    )
    result = calculate_wind_attenuation_coefficient(
        canopy_height=dummy_data.data["canopy_height"].to_numpy(),
        leaf_area_index=leaf_area_index,
        mean_mixing_length=np.array([0, 0.4, 1.5]),
        drag_coefficient=AbioticConsts.drag_coefficient,
        relative_turbulence_intensity=relative_turbulence_intensity,
    )

    exp_result = np.array(
        [[0.0, 0.816, 1.970], [0.0, 0.591, 1.202], [0.0, 0.541, 0.554]]
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


def test_calculate_friction_velocity(dummy_data):
    """Calculate friction velocity."""

    from virtual_rainforest.models.abiotic.wind import calculate_fricition_velocity

    result = calculate_fricition_velocity(
        wind_speed_ref=dummy_data["wind_speed_ref"],
        reference_height=10.0,
        zeroplane_displacement=np.array([0, 8, 43]),
        roughness_length_momentum=np.array([0.003, 0.435, 1.521]),
        diabatic_correction_momentum=np.array([-0.1, 0.0, 0.1]),
        von_karmans_constant=AbioticConsts.von_karmans_constant,
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
        von_karmans_constant=AbioticConsts.von_karmans_constant,
        min_wind_speed_above_canopy=AbioticConsts.min_wind_speed_above_canopy,
    )

    exp_result = np.array([0.0, 7.211, 18.779])
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)


def test_calculate_wind_canopy(dummy_data):
    """Test below canopy wind profile."""

    from virtual_rainforest.models.abiotic.wind import calculate_wind_canopy

    atten_coeff = np.array(
        [[0.0, 0.816, 1.970], [0.0, 0.591, 1.202], [0.0, 0.541, 0.554]]
    )
    result = calculate_wind_canopy(
        top_of_canopy_wind_speed=np.array([2, 5, 7]),
        wind_layer_heights=dummy_data["wind_layer_heights"],
        canopy_height=dummy_data["canopy_height"],
        attenuation_coefficient=atten_coeff,
    )
    exp_result = np.array(
        [
            [0.000000e000, 1.797693e308, 1.797693e308],
            [2.000000e000, 6.718990e000, 4.247477e001],
            [2.000000e000, 3.814989e000, 7.398743e000],
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-3, atol=1e-3)
