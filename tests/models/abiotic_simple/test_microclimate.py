"""Test module for abiotic_simple.microclimate.py."""

import numpy as np
import xarray as xr
from xarray import DataArray


def test_log_interpolation(dummy_climate_data, fixture_core_components):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import log_interpolation

    data = dummy_climate_data

    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_output = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.844995, 29.844995, 29.844995],
                    [28.87117, 28.87117, 28.87117],
                    [27.206405, 27.206405, 27.206405],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [16.145945, 16.145945, 16.145945],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": (
                "layers",
                fixture_core_components.layer_structure.layer_roles[0:15],
            ),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result, exp_output)

    # relative humidity
    result_hum = log_interpolation(
        data=data,
        reference_data=data["relative_humidity_ref"].isel(time_index=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        layer_heights=data["layer_heights"],
        upper_bound=100,
        lower_bound=0,
        gradient=5.4,
    )
    exp_humidity = xr.concat(
        [
            DataArray(
                [
                    [90.0, 90.0, 90.0],
                    [90.341644, 90.341644, 90.341644],
                    [92.488034, 92.488034, 92.488034],
                    [96.157312, 96.157312, 96.157312],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [100, 100, 100],
                    [100, 100, 100],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": (
                "layers",
                fixture_core_components.layer_structure.layer_roles[0:15],
            ),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result_hum, exp_humidity)


def test_calculate_saturation_vapour_pressure(dummy_climate_data):
    """Test calculation of saturation vapour pressure."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_saturation_vapour_pressure,
    )

    data = dummy_climate_data

    # Extract saturation factors from constants
    constants = AbioticSimpleConsts()

    result = calculate_saturation_vapour_pressure(
        data["air_temperature_ref"].isel(time_index=0),
        factor1=constants.saturation_vapour_pressure_factor1,
        factor2=constants.saturation_vapour_pressure_factor2,
        factor3=constants.saturation_vapour_pressure_factor3,
    )

    exp_output = DataArray(
        [1.41727, 1.41727, 1.41727],
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2]},
    )
    xr.testing.assert_allclose(result, exp_output)


def test_calculate_vapour_pressure_deficit():
    """Test calculation of VPD."""

    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        calculate_vapour_pressure_deficit,
    )

    temperature = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.844995, 29.844995, 29.844995],
                    [28.87117, 28.87117, 28.87117],
                    [27.206405, 27.206405, 27.206405],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [16.145945, 16.145945, 16.145945],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    rel_humidity = xr.concat(
        [
            DataArray(
                [
                    [90.0, 90.0, 90.0],
                    [88.5796455, 88.5796455, 88.5796455],
                    [79.65622765, 79.65622765, 79.65622765],
                    [64.40154408, 64.40154408, 64.40154408],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [0, 0, 0],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )

    result = calculate_vapour_pressure_deficit(
        temperature, rel_humidity, constants=AbioticSimpleConsts()
    )
    exp_output = xr.concat(
        [
            DataArray(
                [
                    [0.141727, 0.141727, 0.141727],
                    [0.161233, 0.161233, 0.161233],
                    [0.280298, 0.280298, 0.280298],
                    [0.470266, 0.470266, 0.470266],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [[0.90814, 0.90814, 0.90814], [0.984889, 0.984889, 0.984889]],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    xr.testing.assert_allclose(result["vapour_pressure_deficit"], exp_output)


def test_run_microclimate(dummy_climate_data, fixture_core_components):
    """Test interpolation of all variables."""

    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )
    from virtual_ecosystem.models.abiotic_simple.microclimate import run_microclimate

    data = dummy_climate_data

    result = run_microclimate(
        data=data,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        time_index=0,
        constants=AbioticSimpleConsts(),
        bounds=AbioticSimpleBounds(),
    )

    exp_air_temperature = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.91965, 29.91965, 29.91965],
                    [29.414851, 29.414851, 29.414851],
                    [28.551891, 28.551891, 28.551891],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [26.19, 26.19, 26.19],
                    [22.81851, 22.81851, 22.81851],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(data["layer_heights"].coords)
    xr.testing.assert_allclose(result["air_temperature"], exp_air_temperature)

    exp_atmospheric_pressure = xr.concat(
        [
            DataArray(
                np.full((13, 3), 96.0),
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(data["layer_heights"].coords)
    xr.testing.assert_allclose(result["atmospheric_pressure"], exp_atmospheric_pressure)


def test_interpolate_soil_temperature(dummy_climate_data):
    """Test soil temperature interpolation."""

    from virtual_ecosystem.models.abiotic_simple.microclimate import (
        interpolate_soil_temperature,
    )

    data = dummy_climate_data

    surface_temperature = DataArray(
        [22.0, 22, 22],
        dims="cell_id",
    )
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"],
        upper_bound=50.0,
        lower_bound=-10.0,
    )

    exp_output = DataArray(
        [
            [20.505557, 20.505557, 20.505557],
            [20.0, 20.0, 20.0],
        ],
        dims=["layers", "cell_id"],
        coords={
            "layers": [13, 14],
            "layer_roles": ("layers", ["soil", "soil"]),
            "cell_id": [0, 1, 2],
        },
    )

    xr.testing.assert_allclose(result, exp_output)
