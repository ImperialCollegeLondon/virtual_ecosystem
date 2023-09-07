"""Test module for hydrology.hydrology_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.models.hydrology.constants import HydroConsts
from virtual_rainforest.models.hydrology.hydrology_model import HydrologyModel


@pytest.mark.parametrize(
    "ini_soil_moisture,raises,expected_log_entries",
    [
        (
            0.5,
            does_not_raise(),
            (
                (
                    DEBUG,
                    "hydrology model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'relative_humidity_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'atmospheric_pressure_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'evapotranspiration' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'elevation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'surface_runoff' checked",
                ),
            ),
        ),
        (
            -0.5,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The initial soil moisture has to be between 0 and 1!",
                ),
            ),
        ),
        (
            DataArray([50, 30, 20]),
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The initial soil moisture must be a float!",
                ),
            ),
        ),
    ],
)
def test_hydrology_model_initialization(
    caplog,
    dummy_climate_data,
    ini_soil_moisture,
    raises,
    expected_log_entries,
    layer_roles_fixture,
    soil_layers=2,
    canopy_layers=10,
):
    """Test `HydrologyModel` initialization."""

    with raises:
        # Initialize model
        model = HydrologyModel(
            dummy_climate_data,
            pint.Quantity("1 month"),
            soil_layers,
            canopy_layers,
            ini_soil_moisture,
            constants=HydroConsts,
        )

        # In cases where it passes then checks that the object has the right properties
        assert set(
            [
                "setup",
                "spinup",
                "update",
                "cleanup",
            ]
        ).issubset(dir(model))
        assert model.model_name == "hydrology"
        assert repr(model) == "HydrologyModel(update_interval = 1 month)"
        assert model.layer_roles == layer_roles_fixture
        assert model.initial_soil_moisture == ini_soil_moisture
        assert model.drainage_map == {0: [], 1: [0], 2: [1, 2]}

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval,sm_capacity,raises,expected_log_entries",
    [
        (
            {},
            None,
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 month"),
            0.9,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'relative_humidity_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'atmospheric_pressure_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'evapotranspiration' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'elevation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'surface_runoff' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                    "constants": {"HydroConsts": {"soil_moisture_capacity": 0.7}},
                },
            },
            pint.Quantity("1 month"),
            0.7,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the hydrology model "
                    "successfully extracted.",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'precipitation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'leaf_area_index' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'air_temperature_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'relative_humidity_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'atmospheric_pressure_ref' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'evapotranspiration' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'elevation' checked",
                ),
                (
                    DEBUG,
                    "hydrology model: required var 'surface_runoff' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                    "constants": {"HydroConsts": {"soilm_cap": 0.7}},
                },
            },
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for HydroConsts: " "soilm_cap",
                ),
                (
                    INFO,
                    "Valid names are as follows: ",
                ),
            ),
        ),
    ],
)
def test_generate_hydrology_model(
    caplog,
    dummy_climate_data,
    config,
    time_interval,
    sm_capacity,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test that the initialisation of the hydrology model works as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = HydrologyModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval
        assert model.constants.soil_moisture_capacity == sm_capacity

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval, raises",
    [
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 month"),
            does_not_raise(),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 week",
                    },
                    "layers": {
                        "soil_layers": 2,
                        "canopy_layers": 10,
                    },
                },
                "hydrology": {
                    "initial_soil_moisture": 0.5,
                },
            },
            pint.Quantity("1 week"),
            pytest.raises(NotImplementedError),
        ),
    ],
)
def test_setup(
    dummy_climate_data,
    config,
    layer_roles_fixture,
    time_interval,
    raises,
):
    """Test set up and update."""

    with raises:
        # initialise model
        model = HydrologyModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval

        model.setup()

        soil_moisture_values = np.repeat(a=[np.nan, 0.5], repeats=[13, 2])

        np.testing.assert_allclose(
            dummy_climate_data["soil_moisture"],
            DataArray(
                np.broadcast_to(soil_moisture_values, (3, 15)).T,
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(15),
                    "layer_roles": ("layers", layer_roles_fixture),
                    "cell_id": [0, 1, 2],
                },
                name="soil_moisture",
            ),
            rtol=1e-3,
            atol=1e-3,
        )

        # Run the update step
        model.update(time_index=1)

        exp_soil_moisture = xr.concat(
            [
                DataArray(
                    np.full((13, 3), np.nan),
                    dims=["layers", "cell_id"],
                ),
                DataArray(
                    [[0.5375, 0.5375, 0.5375], [0.4989, 0.4989, 0.4989]],
                    dims=["layers", "cell_id"],
                ),
            ],
            dim="layers",
        ).assign_coords(model.data["layer_heights"].coords)

        exp_surf_prec = DataArray(
            [177.113493, 177.113493, 177.113493],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_runoff = DataArray(
            [0.0, 0.0, 0.0],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_vertical_flow = DataArray(
            [66.273792, 66.273792, 66.273792],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_soil_evap = DataArray(
            [134.195781, 134.195781, 134.195781],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_stream_flow = DataArray(
            [117.113509, 117.113509, 117.113509],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_runoff_acc = DataArray(
            [0, 10, 150],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )

        np.testing.assert_allclose(model.data["precipitation_surface"], exp_surf_prec)
        np.testing.assert_allclose(
            model.data["soil_moisture"],
            exp_soil_moisture,
            rtol=1e-1,
            atol=1e-1,
        )
        np.testing.assert_allclose(
            model.data["vertical_flow"],
            exp_vertical_flow,
            rtol=1e-3,
            atol=1e-3,
        )
        np.testing.assert_allclose(model.data["surface_runoff"], exp_runoff)
        np.testing.assert_allclose(model.data["soil_evaporation"], exp_soil_evap)
        np.testing.assert_allclose(model.data["stream_flow"], exp_stream_flow)
        np.testing.assert_allclose(
            model.data["surface_runoff_accumulated"], exp_runoff_acc
        )


@pytest.mark.parametrize(
    "soilm_cap, soilm_res, hydr_con, hydr_grad, nonlin_par, gw_cap",
    [
        (
            HydroConsts.soil_moisture_capacity,
            HydroConsts.soil_moisture_residual,
            HydroConsts.hydraulic_conductivity,
            HydroConsts.hydraulic_gradient,
            HydroConsts.nonlinearily_parameter,
            HydroConsts.groundwater_capacity,
        ),
        (
            np.array([[0.9, 0.9, 0.9], [0.9, 0.9, 0.9]]),
            np.array([[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]),
            np.array([[0.001, 0.001, 0.001], [0.001, 0.001, 0.001]]),
            np.array([[0.01, 0.01, 0.01], [0.01, 0.01, 0.01]]),
            np.array([2, 2, 2]),
            np.array([0.9, 0.9, 0.9]),
        ),
    ],
)
def test_calculate_vertical_flow(
    soilm_cap,
    soilm_res,
    hydr_con,
    hydr_grad,
    nonlin_par,
    gw_cap,
):
    """Test vertical flow with float or DataArray input."""

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_vertical_flow,
    )

    soil_moisture = np.array([[0.3, 0.6, 0.9], [0.3, 0.6, 0.9]])
    layer_thickness = np.array([[100, 100, 100], [900, 900, 900]])

    result = calculate_vertical_flow(
        soil_moisture,
        layer_thickness,
        soilm_cap,
        soilm_res,
        hydr_con,
        hydr_grad,
        nonlin_par,
        gw_cap,
        2.628e6,
    )
    exp_flow = np.array(
        [
            [1.311692, 98.98647, 2601.720],
            [1.31169, 98.986, 2601.720],
        ]
    )
    np.testing.assert_allclose(result, exp_flow, rtol=0.001)


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

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_soil_evaporation,
    )

    result = calculate_soil_evaporation(
        temperature=np.array([10.0, 20.0, 30.0]),
        wind_speed=wind,
        relative_humidity=np.array([70, 80, 90]),
        atmospheric_pressure=np.array([90, 90, 90]),
        soil_moisture=np.array([0.1, 0.5, 0.9]),
        celsius_to_kelvin=HydroConsts.celsius_to_kelvin,
        density_air=dens_air,
        latent_heat_vapourisation=latvap,
        gas_constant_water_vapour=HydroConsts.gas_constant_water_vapour,
        heat_transfer_coefficient=HydroConsts.heat_transfer_coefficient,
    )

    exp_result = np.array([1.523354, 3.86474, 4.473155])
    np.testing.assert_allclose(result, exp_result, rtol=0.01)


def test_find_lowest_neighbour(dummy_climate_data):
    """Test finding lowest neighbours."""

    from math import sqrt

    from virtual_rainforest.models.hydrology.hydrology_model import (
        find_lowest_neighbour,
    )

    data = dummy_climate_data
    data.grid.set_neighbours(distance=sqrt(data.grid.cell_area))

    neighbours = data.grid.neighbours
    elevation = np.array(data["elevation"])
    result = find_lowest_neighbour(neighbours, elevation)

    exp_result = [1, 2, 2]
    assert result == exp_result


def test_find_upstream_cells():
    """Test that upstream cells are ientified correctly."""

    from virtual_rainforest.models.hydrology.hydrology_model import find_upstream_cells

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

    from virtual_rainforest.models.hydrology.hydrology_model import (
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
    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_drainage_map,
    )

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
    from virtual_rainforest.models.hydrology.constants import HydroConsts
    from virtual_rainforest.models.hydrology.hydrology_model import (
        estimate_interception,
    )

    precip = np.array([0, 20, 100])
    lai = np.array([0, 2, 10])

    result = estimate_interception(
        leaf_area_index=lai,
        precipitation=precip,
        intercept_param_1=HydroConsts.intercept_param_1,
        intercept_param_2=HydroConsts.intercept_param_2,
        intercept_param_3=HydroConsts.intercept_param_3,
        veg_density_param=HydroConsts.veg_density_param,
    )

    exp_result = np.array([0.0, 1.180619, 5.339031])

    np.testing.assert_allclose(result, exp_result)


def test_update_soil_moisture():
    """Test soil moisture update."""

    from virtual_rainforest.models.hydrology.hydrology_model import update_soil_moisture

    soil_moisture = np.array([[30, 60, 50], [300, 600, 500]])
    vertical_flow = np.array([[10, 2, 3], [10, 2, 3]])
    layer_thickness = np.array([[100, 100, 100], [900, 900, 900]])
    exp_result = np.array([[20, 58, 47], [300, 600, 500]])

    result = update_soil_moisture(
        soil_moisture,
        vertical_flow,
        HydroConsts.soil_moisture_capacity * layer_thickness,
        HydroConsts.soil_moisture_residual * layer_thickness,
    )

    np.testing.assert_allclose(result, exp_result, rtol=0.001)
