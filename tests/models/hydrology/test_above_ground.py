"""Test module for hydrology.above_ground.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest
from pyrealm.constants import CoreConst as PyrealmConst

from tests.conftest import log_check
from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.hydrology.constants import HydroConsts


def test_potential_evaporation_leaf():
    """Test potential evaporation from leaf."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        potential_evaporation_leaf,
    )

    # Expected shape should match input (2x2)
    result = potential_evaporation_leaf(
        net_radiation=np.array([[100.0, 120.0], [110.0, 130.0]]),
        vapour_pressure_deficit=np.array([[0.8, 0.850], [0.82, 0.87]]),
        air_temperature=np.array([[25.0, 26.0], [24.5, 27.0]]),
        density_air_kg=np.array([[1.2, 1.2], [1.2, 1.2]]),
        specific_heat_air=np.array([[1.005, 1.005], [1.005, 1.005]]),
        aerodynamic_resistance=np.array([[50.0, 55.0], [52.0, 58.0]]),
        stomatal_resistance=np.array([[200.0, 220.0], [210.0, 230.0]]),
        latent_heat_vapourisation=np.array([[2268.0, 2268.0], [2268.0, 2268.0]]),
        psychrometric_constant=np.array([[66.0, 66.0], [66.0, 66.0]]),
        saturated_pressure_slope_parameters=[4098.0, 0.6108, 17.27, 237.3],
    )

    assert result.shape == (2, 2)
    assert np.all(result >= 0)
    assert np.all(np.isfinite(result))
    exp_evap = np.array([[2.522137e-05, 3.186381e-05], [2.682281e-05, 3.658325e-05]])
    np.testing.assert_allclose(result, exp_evap, rtol=1e-3)


def test_calculate_canopy_evaporation():
    """Test canopy evaporation."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        calculate_canopy_evaporation,
    )

    interception = np.array([0.5, 1.0])
    # Run function
    output = calculate_canopy_evaporation(
        leaf_area_index=np.array([[1.0, 2.0], [1.0, np.nan]]),
        interception=interception,
        net_radiation=np.array([[100, 200], [80, 60]]),
        vapour_pressure_deficit=np.array([[1.0, 2.0], [1.0, 2.0]]),
        air_temperature=np.array([[21.0, 22.0], [18.0, 20.0]]),
        density_air_kg=np.full((2, 2), 1.2),
        specific_heat_air=np.full((2, 2), 1.005),
        aerodynamic_resistance=np.array([[50.0, 60.0], [50.0, 60.0]]),
        stomatal_resistance=np.array([[150.0, 160.0], [150.0, 160.0]]),
        latent_heat_vapourisation=np.full((2, 2), 2268.0),
        psychrometric_constant=np.array([0.066, 0.067]),
        saturated_pressure_slope_parameters=[4098.0, 0.6108, 17.27, 237.3],
        time_interval=86400.0,  # 1 day in seconds
        intercept_residence_time=86400.0,  # 1 day in seconds
        extinction_coefficient_global_radiation=0.5,
    )

    # Check value constraints
    assert np.all(output["leaf_drainage"] >= 0)
    assert np.all(output["leaf_drainage"] <= interception)
    assert output["canopy_evaporation"].shape == (2, 2)
    assert output["leaf_drainage"].shape == (2,)
    np.testing.assert_allclose(
        output["canopy_evaporation"],
        np.array([[0.290727, 1.0], [0.209273, np.nan]]),
        rtol=1e-4,
        atol=1e-4,
    )
    np.testing.assert_allclose(
        output["leaf_drainage"],
        np.array([0.0, 0.0]),
        rtol=1e-4,
        atol=1e-4,
    )


@pytest.mark.parametrize(
    "dens_air, latvap",
    [
        (
            1.225,
            2442.0,
        ),
        (
            np.repeat(1.225, 3),
            np.repeat(2442.0, 3),
        ),
    ],
)
def test_calculate_soil_evaporation(dens_air, latvap):
    """Test soil evaporation with float and DataArray."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        calculate_soil_evaporation,
    )

    result = calculate_soil_evaporation(
        temperature=np.array([20.0, 20.0, 30.0]),
        wind_speed_surface=np.array([1.0, 0.5, 0.1]),
        relative_humidity=np.array([80.0, 80.0, 90.0]),
        atmospheric_pressure=np.array([101.0, 101.0, 101.0]),
        soil_moisture=np.array([1.0, 2.0, 5.0]),
        soil_moisture_residual=0.1,
        soil_moisture_saturation=0.9,
        leaf_area_index=np.array([3.0, 4.0, 5.0]),
        density_air=dens_air,
        latent_heat_vapourisation=latvap,
        gas_constant_water_vapour=CoreConsts.gas_constant_water_vapour / 1000.0,
        drag_coefficient_evaporation=HydroConsts.drag_coefficient_evaporation,
        extinction_coefficient_global_radiation=(
            HydroConsts.extinction_coefficient_global_radiation
        ),
        time_interval=86400,
        pyrealm_const=PyrealmConst,
    )

    exp_evap = np.array([2.18791, 0.521941, 0.090352])
    np.testing.assert_allclose(result["soil_evaporation"], exp_evap, rtol=0.01)
    exp_ra = np.array([5.0, 10.0, 50.0])
    np.testing.assert_allclose(
        result["aerodynamic_resistance_surface"], exp_ra, rtol=0.01
    )


def test_find_lowest_neighbour(fixture_core_components, dummy_climate_data):
    """Test finding lowest neighbours."""

    # FIXME: At the moment this is being tested on a 2x2 grid with these elevations and
    #        the implementation uses rook case neighbours. There is some odd behaviour
    #        with the ties.
    #
    #     200, 100
    #      10, 10

    from virtual_ecosystem.models.hydrology.above_ground import find_lowest_neighbour

    data = dummy_climate_data

    grid = fixture_core_components.grid
    grid.set_neighbours(distance=np.sqrt(grid.cell_area))
    result = find_lowest_neighbour(grid.neighbours, data["elevation"].to_numpy())

    exp_result = [2, 3, 2, 2]
    assert result == exp_result


def test_find_upstream_cells():
    """Test that upstream cells are ientified correctly."""

    from virtual_ecosystem.models.hydrology.above_ground import find_upstream_cells

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
                    "The accumulated flow should not be negative!",
                ),
            ),
        ),
    ],
)
def accumulate_horizontal_flow(caplog, acc_runoff, raises, expected_log_entries):
    """Test."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        accumulate_horizontal_flow,
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
        result = accumulate_horizontal_flow(upstream_ids, surface_runoff, acc_runoff)
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

    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.hydrology.above_ground import calculate_drainage_map

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
        drainage_map, accumulation_points = calculate_drainage_map(grid, elevation)

        assert len(drainage_map) == grid.n_cells
        assert drainage_map[1] == [2, 6]
        assert accumulation_points[0] == "corner"

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_calculate_interception():
    """Test."""
    from virtual_ecosystem.models.hydrology.above_ground import calculate_interception
    from virtual_ecosystem.models.hydrology.constants import HydroConsts

    precip = np.array([0, 20, 100])
    lai = np.array([0, 2, 10])

    result = calculate_interception(
        leaf_area_index=lai,
        precipitation=precip,
        intercept_parameters=HydroConsts.intercept_parameters,
        veg_density_param=HydroConsts.veg_density_param,
    )

    exp_result = np.array([0.0, 1.180619, 5.339031])

    np.testing.assert_allclose(result, exp_result)


def test_distribute_monthly_rainfall():
    """Test that randomly generated numbers are reproducible."""
    from virtual_ecosystem.models.hydrology.above_ground import (
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

    from virtual_ecosystem.models.hydrology.above_ground import calculate_bypass_flow

    top_sm = np.array([20, 50, 80])
    top_sm_sat = np.array([100, 100, 100])
    av_water = np.array([20, 20, 20])

    result = calculate_bypass_flow(top_sm, top_sm_sat, av_water, 1.0)
    exp_result = np.array([4.0, 10.0, 16.0])

    np.testing.assert_allclose(result, exp_result)


def test_convert_mm_flow_to_m3_per_second():
    """Test channel flow conversion."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        convert_mm_flow_to_m3_per_second,
    )

    channel_flow = np.array([100, 1000, 10000])
    exp_result = np.array([0.0003858, 0.003858, 0.0385802])
    result = convert_mm_flow_to_m3_per_second(
        river_discharge_mm=channel_flow,
        area=np.array([10000, 10000, 10000]),
        days=30,
        seconds_to_day=CoreConsts.seconds_to_day,
        meters_to_millimeters=1000,
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-4, atol=1e-4)


def test_calculate_surface_runoff():
    """Test surface runoff function."""

    from virtual_ecosystem.models.hydrology.above_ground import calculate_surface_runoff

    exp_result = np.array([50, 0, 50])
    result = calculate_surface_runoff(
        precipitation_surface=np.array([100, 200, 300]),
        top_soil_moisture=np.array([150, 150, 150]),
        top_soil_moisture_saturation=np.array([200, 400, 400]),
    )

    np.testing.assert_allclose(result, exp_result, rtol=1e-4, atol=1e-4)
