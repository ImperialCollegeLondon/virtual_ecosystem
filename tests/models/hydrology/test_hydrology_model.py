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

        xr.testing.assert_allclose(
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
                    [[0.512498, 0.518842, 0.626396], [0.512498, 0.518842, 0.626396]],
                    dims=["layers", "cell_id"],
                ),
            ],
            dim="layers",
        ).assign_coords(model.data["layer_heights"].coords)

        exp_runoff = DataArray(
            [0, 0, 0],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )

        exp_vertical_flow = DataArray(
            [0.252134, 0.273622, 0.964253],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_soil_evap = DataArray(
            [0.393653, 0.393653, 0.393653],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        exp_stream_flow = DataArray(
            [0, 0, 80.126915],
            dims=["cell_id"],
            coords={"cell_id": [0, 1, 2]},
        )
        xr.testing.assert_allclose(model.data["soil_moisture"], exp_soil_moisture)
        xr.testing.assert_allclose(model.data["vertical_flow"], exp_vertical_flow)
        xr.testing.assert_allclose(model.data["surface_runoff"], exp_runoff)
        xr.testing.assert_allclose(model.data["soil_evaporation"], exp_soil_evap)
        xr.testing.assert_allclose(model.data["stream_flow"], exp_stream_flow)


@pytest.mark.parametrize(
    "soilm_cap, soilm_res, hydr_con, hydr_grad, nonlin_par",
    [
        (
            HydroConsts.soil_moisture_capacity,
            HydroConsts.soil_moisture_residual,
            HydroConsts.hydraulic_conductivity,
            HydroConsts.hydraulic_gradient,
            HydroConsts.nonlinearily_parameter,
        ),
        (
            DataArray([0.9, 0.9, 0.9], dims=["cell_id"]),
            DataArray([0.1, 0.1, 0.1], dims=["cell_id"]),
            DataArray([0.001, 0.001, 0.001], dims=["cell_id"]),
            DataArray([0.01, 0.01, 0.01], dims=["cell_id"]),
            DataArray([2, 2, 2], dims=["cell_id"]),
        ),
    ],
)
def test_calculate_vertical_flow(soilm_cap, soilm_res, hydr_con, hydr_grad, nonlin_par):
    """Test vertical flow with float or DataArray input."""

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_vertical_flow,
    )

    soil_moisture = DataArray([0.3, 0.6, 0.9], dims=["cell_id"])
    soil_depth = DataArray([1100, 1100, 1100], dims=["cell_id"])

    result = calculate_vertical_flow(
        soil_moisture,
        soil_depth,
        soilm_cap,
        soilm_res,
        hydr_con,
        hydr_grad,
        HydroConsts.seconds_to_month,
        nonlin_par,
        HydroConsts.meters_to_millimeters,
    )
    exp_flow = DataArray([6.022462e-03, 7.186012e-01, 2.389091e01], dims=["cell_id"])
    xr.testing.assert_allclose(result, exp_flow)


@pytest.mark.parametrize(
    "wind, dens_air, latvap",
    [
        (
            0.1,
            HydroConsts.density_air,
            HydroConsts.latent_heat_vapourisation,
        ),
        (
            DataArray([0.1, 0.1, 0.1], dims=["cell_id"]),
            DataArray([1.225, 1.225, 1.225], dims=["cell_id"]),
            DataArray([2.45, 2.45, 2.45], dims=["cell_id"]),
        ),
    ],
)
def test_calculate_soil_evaporation(wind, dens_air, latvap):
    """Test soil evaporation with float and DataArray."""

    from virtual_rainforest.models.hydrology.hydrology_model import (
        calculate_soil_evaporation,
    )

    result = calculate_soil_evaporation(
        temperature=DataArray([10.0, 20.0, 30.0], dims=["cell_id"]),
        wind_speed=wind,
        relative_humidity=DataArray([70, 80, 90], dims=["cell_id"]),
        atmospheric_pressure=DataArray([90, 90, 90], dims=["cell_id"]),
        soil_moisture=DataArray([0.3, 0.6, 0.9], dims=["cell_id"]),
        celsius_to_kelvin=HydroConsts.celsius_to_kelvin,
        density_air=dens_air,
        latent_heat_vapourisation=latvap,
        gas_constant_water_vapour=HydroConsts.gas_constant_water_vapour,
        heat_transfer_coefficient=HydroConsts.heat_transfer_coefficient,
        flux_to_mm_conversion=HydroConsts.flux_to_mm_conversion,
        timestep_conversion_factor=HydroConsts.seconds_to_month,
    )
    xr.testing.assert_allclose(
        result,
        DataArray([0.263425, 0.340108, 0.39365], dims=["cell_id"]),
    )
