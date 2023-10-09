"""Test module for hydrology.above_ground.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_rainforest.models.hydrology.constants import HydroConsts


@pytest.mark.parametrize(
    "wind, dens_air, latvap",
    [
        (
            0.1,
            HydroConsts.density_air,
            HydroConsts.latent_heat_vapourisation,
        ),
        (
            np.array([0.1, 0.1, 0.1]),
            np.array([1.225, 1.225, 1.225]),
            np.array([2.45, 2.45, 2.45]),
        ),
    ],
)
def test_calculate_soil_evaporation(wind, dens_air, latvap):
    """Test soil evaporation with float and DataArray."""

    from virtual_rainforest.models.hydrology.above_ground import (
        calculate_soil_evaporation,
    )

    result = calculate_soil_evaporation(
        temperature=np.array([20.0, 20.0, 30.0]),
        wind_speed=wind,
        relative_humidity=np.array([80, 80, 90]),
        atmospheric_pressure=np.array([90, 90, 90]),
        soil_moisture=np.array([0.01, 0.1, 0.5]),
        soil_moisture_residual=0.1,
        soil_moisture_capacity=0.9,
        leaf_area_index=np.array([3, 4, 5]),
        celsius_to_kelvin=HydroConsts.celsius_to_kelvin,
        density_air=dens_air,
        latent_heat_vapourisation=latvap,
        gas_constant_water_vapour=HydroConsts.gas_constant_water_vapour,
        heat_transfer_coefficient=HydroConsts.heat_transfer_coefficient,
        extinction_coefficient_global_radiation=(
            HydroConsts.extinction_coefficient_global_radiation
        ),
    )

    exp_result = np.array([0.007452, 0.003701, 0.135078])
    np.testing.assert_allclose(result, exp_result, rtol=0.01)


def test_find_lowest_neighbour(dummy_climate_data):
    """Test finding lowest neighbours."""

    from math import sqrt

    from virtual_rainforest.models.hydrology.above_ground import find_lowest_neighbour

    data = dummy_climate_data
    data.grid.set_neighbours(distance=sqrt(data.grid.cell_area))

    neighbours = data.grid.neighbours
    elevation = np.array(data["elevation"])
    result = find_lowest_neighbour(neighbours, elevation)

    exp_result = [1, 2, 2]
    assert result == exp_result


def test_find_upstream_cells():
    """Test that upstream cells are ientified correctly."""

    from virtual_rainforest.models.hydrology.above_ground import find_upstream_cells

    lowest = [1, 2, 2, 5, 7, 7, 7, 7]
    exp_result = [[], [0], [1, 2], [], [], [3], [], [4, 5, 6, 7]]
    result = find_upstream_cells(lowest)
    assert result == exp_result


@pytest.mark.parametrize(
    "acc_runoff,raises,expected_log_entries",
    [
        (
            np.array([100, 100, 100, 100, 100, 100, 100, 100]),
            does_not_raise(),
            {},
        ),
        (
            np.array([-100, 100, 100, 100, 100, 100, 100, 100]),
            pytest.raises(ValueError),
            (
                (
                    ERROR,
                    "The accumulated surface runoff should not be negative!",
                ),
            ),
        ),
    ],
)
def test_accumulate_surface_runoff(caplog, acc_runoff, raises, expected_log_entries):
    """Test."""

    from virtual_rainforest.models.hydrology.above_ground import (
        accumulate_surface_runoff,
    )

    upstream_ids = {
        0: [],
        1: [0],
        2: [1, 2],
        3: [],
        4: [],
        5: [3],
        6: [],
        7: [4, 5, 6, 7],
    }
    surface_runoff = np.array([100, 100, 100, 100, 100, 100, 100, 100])
    exp_result = np.array([100, 200, 300, 100, 100, 200, 100, 500])

    with raises:
        result = accumulate_surface_runoff(upstream_ids, surface_runoff, acc_runoff)
        np.testing.assert_array_equal(result, exp_result)

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "grid_type,raises,expected_log_entries",
    [
        (
            "square",
            does_not_raise(),
            {},
        ),
        (
            "hexagon",
            pytest.raises(ValueError),
            (
                (
                    ERROR,
                    "This grid type is currently not supported!",
                ),
            ),
        ),
    ],
)
def test_calculate_drainage_map(caplog, grid_type, raises, expected_log_entries):
    """Test that function gets correct neighbours."""

    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.hydrology.above_ground import calculate_drainage_map

    elevation = np.array(
        [
            1,
            2,
            3,
            4,
            5,
            11,
            22,
            33,
            44,
            55,
            111,
            222,
            333,
            111,
            80,
            66,
            88,
            99,
            88,
            66,
            11,
            5,
            4,
            3,
            2,
        ]
    )

    with raises:
        grid = Grid(grid_type, cell_nx=5, cell_ny=5)
        result = calculate_drainage_map(grid, elevation)

        assert len(result) == grid.n_cells
        assert result[1] == [2, 6]

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_estimate_interception():
    """Test."""
    from virtual_rainforest.models.hydrology.above_ground import calculate_interception
    from virtual_rainforest.models.hydrology.constants import HydroConsts

    precip = np.array([0, 20, 100])
    lai = np.array([0, 2, 10])

    result = calculate_interception(
        leaf_area_index=lai,
        precipitation=precip,
        intercept_param_1=HydroConsts.intercept_param_1,
        intercept_param_2=HydroConsts.intercept_param_2,
        intercept_param_3=HydroConsts.intercept_param_3,
        veg_density_param=HydroConsts.veg_density_param,
    )

    exp_result = np.array([0.0, 1.180619, 5.339031])

    np.testing.assert_allclose(result, exp_result)


def test_distribute_monthly_rainfall():
    """Test that randomly generated numbers are reproducible."""
    from virtual_rainforest.models.hydrology.above_ground import (
        distribute_monthly_rainfall,
    )

    monthly_rain = np.array([0.0, 20.0, 200.0])
    result = distribute_monthly_rainfall(monthly_rain, 10, 42)
    result1 = distribute_monthly_rainfall(monthly_rain, 10, 42)

    assert result.shape == (3, 10)
    np.testing.assert_allclose(result.sum(axis=1), monthly_rain)
    np.testing.assert_allclose(result, result1)


def test_calculate_bypass_flow():
    """Test."""

    from virtual_rainforest.models.hydrology.above_ground import calculate_bypass_flow

    top_sm = np.array([20, 50, 80])
    top_sm_sat = np.array([100, 100, 100])
    av_water = np.array([20, 20, 20])

    result = calculate_bypass_flow(top_sm, top_sm_sat, av_water, 1.0)
    exp_result = np.array([4.0, 10.0, 16.0])

    np.testing.assert_allclose(result, exp_result)


def test_convert_mm_flow_to_m3_per_second():
    """Test channel flow conversion."""

    from virtual_rainforest.models.hydrology.above_ground import (
        convert_mm_flow_to_m3_per_second,
    )

    channel_flow = np.array([100, 1000, 10000])
    exp_result = np.array([0.0003858, 0.003858, 0.0385802])
    result = convert_mm_flow_to_m3_per_second(
        river_discharge_mm=channel_flow,
        area=np.array([10000, 10000, 10000]),
        days=30,
        seconds_to_day=HydroConsts.seconds_to_day,
        meters_to_millimeters=1000,
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-4, atol=1e-4)
