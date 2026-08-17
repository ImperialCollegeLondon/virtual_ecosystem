"""Test module for hydrology.above_ground.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check


def test_potential_evaporation_leaf():
    """Test potential evaporation from leaf."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        potential_evaporation_leaf,
    )

    # Expected shape should match input (2x2)
    result = potential_evaporation_leaf(
        net_radiation=np.array([[100.0, 120.0], [110.0, np.nan]]),
        vapour_pressure_deficit=np.array([[0.8, 0.850], [0.82, np.nan]]),
        air_temperature=np.array([[25.0, 26.0], [24.5, np.nan]]),
        density_air_kg=np.array([[1.2, 1.2], [1.2, np.nan]]),
        specific_heat_air=np.array([[1.005, 1.005], [1.005, np.nan]]),
        aerodynamic_resistance_canopy=np.array([[50.0, 55.0]]),
        stomatal_resistance=np.array([[200.0, 220.0], [210.0, np.nan]]),
        latent_heat_vapourisation=np.array([[2268.0, 2268.0], [2268.0, np.nan]]),
        psychrometric_constant=np.array([[66.0, 66.0], [66.0, np.nan]]),
        saturated_pressure_slope_parameters=[4098.0, 0.6108, 17.27, 237.3],
    )

    assert result.shape == (2, 2)
    mask = ~np.isnan(result)
    assert np.all(result[mask] >= 0)
    assert np.all(np.isfinite(result[mask]))
    exp_evap = np.array([[2.522137e-05, 3.186381e-05], [2.599098e-05, np.nan]])
    np.testing.assert_allclose(result, exp_evap, rtol=1e-3)


def test_calculate_canopy_evaporation():
    """Test canopy evaporation."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        calculate_canopy_evaporation,
    )

    interception = np.array([[5.0, 10.0, np.nan], [2.0, np.nan, np.nan]])

    result = calculate_canopy_evaporation(
        leaf_area_index=np.array([[1.0, 2.0, np.nan], [1.0, np.nan, np.nan]]),
        interception=interception,
        net_radiation=np.array([[100, 200, np.nan], [80, np.nan, np.nan]]),
        vapour_pressure_deficit=np.array([[1.0, 2.0, np.nan], [1.0, np.nan, np.nan]]),
        air_temperature=np.array([[21.0, 22.0, np.nan], [18.0, np.nan, np.nan]]),
        density_air_kg=np.array([[1.2, 1.2, np.nan], [1.2, np.nan, np.nan]]),
        specific_heat_air=np.array([[1.005, 1.005, np.nan], [1.005, np.nan, np.nan]]),
        aerodynamic_resistance_canopy=np.array([50.0, 60.0, np.nan]),
        stomatal_resistance=np.array([[150.0, 160.0, np.nan], [150.0, np.nan, np.nan]]),
        latent_heat_vapourisation=np.array(
            [[2268.0, 2268.0, np.nan], [2268.0, np.nan, np.nan]]
        ),
        psychrometric_constant=np.array([0.066, 0.067, np.nan]),
        saturated_pressure_slope_parameters=[4098.0, 0.6108, 17.27, 237.3],
        time_interval=86400.0,  # 1 day in seconds
        extinction_coefficient_global_radiation=0.5,
    )

    # Check value constraints
    mask = ~np.isnan(interception)

    canopy_evaporation = result["canopy_evaporation"]
    canopy_intercept = result["remaining_interception"]
    assert np.all(canopy_evaporation[mask] >= 0)
    assert np.all(np.isfinite(canopy_evaporation[mask]))
    assert np.all(canopy_evaporation[mask] <= interception[mask])
    assert canopy_evaporation.shape == (2, 3)

    assert np.all(canopy_intercept[mask] >= 0)
    assert np.all(np.isfinite(canopy_intercept[mask]))
    assert np.all(canopy_intercept[mask] <= interception[mask])
    assert canopy_intercept.shape == (2, 3)

    total_interception = np.nansum(interception, axis=0)
    remaining_total = np.nansum(result["remaining_interception"], axis=0)
    assert np.all(remaining_total <= total_interception + 1e-12)


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
def test_calculate_soil_evaporation(
    dens_air,
    latvap,
    fixture_hydrology_constants,
    fixture_core_constants,
    fixture_pyrealm_config,
):
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
        gas_constant_water_vapour=fixture_core_constants.gas_constant_water_vapour
        / 1000.0,
        drag_coefficient_evaporation=fixture_hydrology_constants.drag_coefficient_evaporation,
        extinction_coefficient_global_radiation=(
            fixture_hydrology_constants.extinction_coefficient_global_radiation
        ),
        time_interval=86400,
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    assert np.all(result["soil_evaporation"] >= 0)
    assert np.all(np.isfinite(result["soil_evaporation"]))
    assert np.all(result["aerodynamic_resistance_soil"] >= 0)
    assert np.all(np.isfinite(result["aerodynamic_resistance_soil"]))

    exp_evap = np.array([2.18791, 0.521941, 0.090352])
    np.testing.assert_allclose(result["soil_evaporation"], exp_evap, rtol=0.01)
    exp_ra = np.array([5.0, 10.0, 50.0])
    np.testing.assert_allclose(result["aerodynamic_resistance_soil"], exp_ra, rtol=0.01)


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


def test_route_horizontal_flow_basic():
    """Test horizontal flow routing."""

    from virtual_ecosystem.models.hydrology.above_ground import route_horizontal_flow

    drainage_map = {
        0: [],
        1: [0],
        2: [1, 2],
        3: [],
        4: [],
        5: [3],
        6: [],
        7: [4, 5, 6],
    }

    surface_runoff = np.array([1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 2.0, 1.0])
    subsurface_runoff = np.array([0.5, 0.0, 1.0, 0.5, 0.0, 1.0, 0.5, 1.0])

    result = route_horizontal_flow(drainage_map, surface_runoff, subsurface_runoff)

    expected_channel_inflow = np.array([1.5, 3.5, 10.0, 1.5, 2.0, 5.5, 2.5, 10.5])

    np.testing.assert_array_almost_equal(result, expected_channel_inflow)


def test_route_horizontal_flow_no_upstream():
    """Test horizontal flow routing with no upstream cells."""
    from virtual_ecosystem.models.hydrology.above_ground import route_horizontal_flow

    # Single cell with no upstream
    drainage_map = {0: []}
    surface_runoff = np.array([5.0])
    subsurface_runoff = np.array([2.0])

    result = route_horizontal_flow(drainage_map, surface_runoff, subsurface_runoff)
    expected = np.array([7.0])  # 5 + 2
    np.testing.assert_array_equal(result, expected)


def test_route_horizontal_flow_raises_on_negative():
    """Test horizontal flow routing raises on negative input."""
    from virtual_ecosystem.models.hydrology.above_ground import route_horizontal_flow

    drainage_map = {0: [], 1: [0]}
    surface_runoff = np.array([-1.0, 0.0])
    subsurface_runoff = np.array([0.0, 0.0])

    with pytest.raises(ValueError, match="The river discharge should not be negative"):
        route_horizontal_flow(drainage_map, surface_runoff, subsurface_runoff)


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

    caplog.clear()

    with raises:
        grid = Grid(grid_type, cell_nx=5, cell_ny=5)
        result = calculate_drainage_map(grid, elevation)

        assert len(result) == grid.n_cells
        assert result[1] == [2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14]

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_calculate_interception(
    fixture_hydrology_constants,
    fixture_core_components,
    dummy_climate_data_varying_canopy,
):
    """Test interception."""
    from virtual_ecosystem.models.hydrology.above_ground import calculate_interception

    data = dummy_climate_data_varying_canopy
    lyr_str = fixture_core_components.layer_structure

    result = calculate_interception(
        leaf_area_index=data["leaf_area_index"].to_numpy(),
        precipitation=data["precipitation"].isel(time_index=1).to_numpy(),
        intercept_parameters=fixture_hydrology_constants.intercept_parameters,
        veg_density_param=fixture_hydrology_constants.veg_density_param,
    )

    exp_canopy = np.array(
        [
            [1.424985, 1.424985, 1.424985, np.nan],
            [1.424879, 1.424879, np.nan, np.nan],
            [1.424767, np.nan, np.nan, np.nan],
        ]
    )
    exp_understorey = np.array([1.424651, 1.424767, 1.424879, 1.424985])
    np.testing.assert_allclose(
        result[lyr_str.index_filled_canopy], exp_canopy, rtol=1e-4, atol=1e-4
    )
    np.testing.assert_allclose(
        result[lyr_str.index_surface_scalar], exp_understorey, rtol=1e-4, atol=1e-4
    )


def test_distribute_monthly_rainfall():
    """Test the stochastic rainfall generator, including invalid inputs."""

    from virtual_ecosystem.models.hydrology.above_ground import (
        distribute_monthly_rainfall,
    )

    # Valid input tests
    monthly = np.array([0.0, 50.0, 80.0, 120.0])
    num_days = 30
    shape = 1.0
    scale = 2.0
    seed = 42
    p_wet_wet = 0.6
    p_wet_dry = 0.3

    result = distribute_monthly_rainfall(
        total_monthly_rainfall=monthly,
        num_days=num_days,
        p_wet_wet=p_wet_wet,
        p_wet_dry=p_wet_dry,
        shape_parameter=shape,
        scale_parameter=scale,
        seed=seed,
    )

    # Shape check
    assert result.shape == (len(monthly), num_days), "Output shape mismatch"

    # Monthly totals preserved
    np.testing.assert_allclose(
        result.sum(axis=1), monthly, rtol=1e-6, err_msg="Monthly totals not preserved"
    )

    # Non-negative rainfall
    assert np.all(result >= 0), "Negative rainfall found"

    # Reproducibility
    result2 = distribute_monthly_rainfall(
        total_monthly_rainfall=monthly,
        num_days=num_days,
        p_wet_wet=p_wet_wet,
        p_wet_dry=p_wet_dry,
        shape_parameter=shape,
        scale_parameter=scale,
        seed=seed,
    )
    np.testing.assert_allclose(result, result2, err_msg="Results differ for same seed")

    # Zero-month check
    assert np.all(result[0] == 0), "Zero-month should produce all zeros"

    # Some dry days for positive months
    for i in range(1, len(monthly)):
        wet_days = np.sum(result[i] > 0)
        assert 0 < wet_days < num_days, f"Month {i} has unrealistic wet/dry pattern"

    # Invalid input tests (raises)

    # Negative rainfall
    with pytest.raises(ValueError):
        distribute_monthly_rainfall(
            total_monthly_rainfall=np.array([-10.0]),
            num_days=num_days,
            p_wet_wet=p_wet_wet,
            p_wet_dry=p_wet_dry,
            shape_parameter=shape,
            scale_parameter=scale,
        )

    # num_days <= 0
    with pytest.raises(ValueError):
        distribute_monthly_rainfall(
            total_monthly_rainfall=np.array([50.0]),
            num_days=0,
            p_wet_wet=p_wet_wet,
            p_wet_dry=p_wet_dry,
            shape_parameter=shape,
            scale_parameter=scale,
        )

    # Invalid probabilities
    with pytest.raises(ValueError):
        distribute_monthly_rainfall(
            total_monthly_rainfall=np.array([50.0]),
            num_days=num_days,
            p_wet_wet=1.5,
            p_wet_dry=0.3,
            shape_parameter=shape,
            scale_parameter=scale,
        )
    with pytest.raises(ValueError):
        distribute_monthly_rainfall(
            total_monthly_rainfall=np.array([50.0]),
            num_days=num_days,
            p_wet_wet=0.6,
            p_wet_dry=-0.2,
            shape_parameter=shape,
            scale_parameter=scale,
        )

    # Invalid shape
    with pytest.raises(ValueError):
        distribute_monthly_rainfall(
            total_monthly_rainfall=np.array([50.0]),
            num_days=num_days,
            p_wet_wet=p_wet_wet,
            p_wet_dry=p_wet_dry,
            shape_parameter=0.0,
            scale_parameter=scale,
        )

    # Invalid scale
    with pytest.raises(ValueError):
        distribute_monthly_rainfall(
            total_monthly_rainfall=np.array([50.0]),
            num_days=num_days,
            p_wet_wet=p_wet_wet,
            p_wet_dry=p_wet_dry,
            shape_parameter=shape,
            scale_parameter=0.0,
        )


def test_calculate_bypass_flow():
    """Test bypass flow."""

    from virtual_ecosystem.models.hydrology.above_ground import calculate_bypass_flow

    top_sm = np.array([20, 50, 80])
    top_sm_sat = np.array([100, 100, 100])
    av_water = np.array([20, 20, 20])

    result = calculate_bypass_flow(top_sm, top_sm_sat, av_water, 1.0)
    exp_result = np.array([4.0, 10.0, 16.0])

    np.testing.assert_allclose(result, exp_result)


def test_convert_mm_flow_to_m3_per_second(fixture_core_constants):
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
        seconds_to_day=fixture_core_constants.seconds_to_day,
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
