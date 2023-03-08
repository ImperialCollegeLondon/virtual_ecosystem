"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import DEBUG, ERROR, INFO

import numpy as np
import pytest
from dotmap import DotMap  # type: ignore
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.base_model import InitialisationError
from virtual_rainforest.models.soil.soil_model import IntegrationError, SoilModel


@pytest.fixture
def soil_model_fixture(dummy_carbon_data):
    """Create a soil model fixture based on the dummy carbon data."""

    from virtual_rainforest.models.soil.soil_model import SoilModel

    config = {
        "core": {"timing": {"start_time": "2020-01-01"}},
        "soil": {"model_time_step": "12 hours"},
    }
    return SoilModel.from_config(dummy_carbon_data, config)


@pytest.mark.parametrize(
    "bad_data,raises,expected_log_entries",
    [
        (
            [],
            does_not_raise(),
            (
                (
                    DEBUG,
                    "soil model: required var 'mineral_associated_om' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'low_molecular_weight_c' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'pH' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'bulk_density' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_moisture' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_temperature' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'percent_clay' checked",
                ),
            ),
        ),
        (
            1,
            pytest.raises(ValueError),
            (
                (
                    ERROR,
                    "soil model: init data missing required var "
                    "'mineral_associated_om'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var "
                    "'low_molecular_weight_c'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'pH'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'bulk_density'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'soil_moisture'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'soil_temperature'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var 'percent_clay'",
                ),
                (
                    ERROR,
                    "soil model: error checking required_init_vars, see log.",
                ),
            ),
        ),
        (
            2,
            pytest.raises(InitialisationError),
            (
                (
                    INFO,
                    "Replacing data array for 'low_molecular_weight_c'",
                ),
                (
                    DEBUG,
                    "soil model: required var 'mineral_associated_om' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'low_molecular_weight_c' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'pH' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'bulk_density' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_moisture' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_temperature' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'percent_clay' checked",
                ),
                (
                    ERROR,
                    "Initial carbon pools contain at least one negative value!",
                ),
            ),
        ),
    ],
)
def test_soil_model_initialization(
    caplog, dummy_carbon_data, bad_data, raises, expected_log_entries
):
    """Test `SoilModel` initialization."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    with raises:
        # Initialize model
        if bad_data:
            # Make four cell grid
            grid = Grid(cell_nx=4, cell_ny=1)
            carbon_data = Data(grid)
            # On second test actually populate this data to test bounds
            if bad_data == 2:
                carbon_data = deepcopy(dummy_carbon_data)
                # Put incorrect data in for lmwc
                carbon_data["low_molecular_weight_c"] = DataArray(
                    [0.05, 0.02, 0.1, -0.005], dims=["cell_id"]
                )
            # Initialise model with bad data object
            model = SoilModel(
                carbon_data, np.timedelta64(1, "W"), np.datetime64("2022-11-01")
            )
        else:
            model = SoilModel(
                dummy_carbon_data, np.timedelta64(1, "W"), np.datetime64("2022-11-01")
            )

        # In cases where it passes then checks that the object has the right properties
        assert set(
            [
                "setup",
                "spinup",
                "update",
                "cleanup",
                "replace_soil_pools",
                "integrate_soil_model",
            ]
        ).issubset(dir(model))
        assert model.model_name == "soil"
        assert str(model) == "A soil model instance"
        assert (
            repr(model)
            == "SoilModel(update_interval = 1 weeks, next_update = 2022-11-08)"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval,raises,expected_log_entries,end_carbon",
    [
        (
            {},
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
            [],
        ),
        (
            {
                "core": {"timing": {"start_time": "2020-01-01"}},
                "soil": {"model_time_step": "12 hours"},
            },
            np.timedelta64(12, "h"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (
                    DEBUG,
                    "soil model: required var 'mineral_associated_om' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'low_molecular_weight_c' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'pH' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'bulk_density' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_moisture' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_temperature' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'percent_clay' checked",
                ),
                (INFO, "Replacing data array for 'low_molecular_weight_c'"),
                (INFO, "Replacing data array for 'mineral_associated_om'"),
            ),
            [
                [2.50019883, 1.70000589, 4.50007171, 0.50000014],
                [0.04980117, 0.01999411, 0.09992829, 0.00499986],
            ],
        ),
    ],
)
def test_generate_soil_model(
    caplog,
    dummy_carbon_data,
    config,
    time_interval,
    raises,
    expected_log_entries,
    end_carbon,
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(dummy_carbon_data, config)
        assert model.update_interval == time_interval
        assert (
            model.next_update
            == np.datetime64(config["core"]["timing"]["start_time"]) + time_interval
        )
        # Run the update step and check that next_update has incremented properly
        model.update()
        assert (
            model.next_update
            == np.datetime64(config["core"]["timing"]["start_time"]) + 2 * time_interval
        )
        # Check that updates to data fixture are correct
        assert np.allclose(dummy_carbon_data["mineral_associated_om"], end_carbon[0])
        assert np.allclose(dummy_carbon_data["low_molecular_weight_c"], end_carbon[1])

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_replace_soil_pools(dummy_carbon_data, soil_model_fixture):
    """Test function to update soil pools."""

    end_lmwc = [0.04980117, 0.01999411, 0.09992829, 0.00499986]
    end_maom = [2.50019883, 1.70000589, 4.50007171, 0.50000014]

    new_pools = np.concatenate([end_lmwc, end_maom])

    # Use this update to update the soil carbon pools
    soil_model_fixture.replace_soil_pools(new_pools)

    # Then check that pools are correctly incremented based on update
    assert np.allclose(dummy_carbon_data["mineral_associated_om"], end_maom)
    assert np.allclose(dummy_carbon_data["low_molecular_weight_c"], end_lmwc)


@pytest.mark.parametrize(
    argnames=["output", "raises", "expected_log"],
    argvalues=[
        pytest.param(
            DotMap(
                success=True,
                y=np.array(
                    [
                        [5.000e-02, 3.210e-02],
                        [2.000e-02, 1.921e-02],
                        [4.500e00, 4.509e00],
                        [5.000e-01, 5.000e-01],
                        [3.210e-02, 5.000e-02],
                        [1.921e-02, 2.000e-02],
                        [4.509e00, 4.500e00],
                        [5.000e-01, 5.000e-01],
                    ]
                ),
            ),
            does_not_raise(),
            (),
            id="successful integration",
        ),
        pytest.param(
            DotMap(success=False, message="Example error message"),
            pytest.raises(IntegrationError),
            (
                (
                    ERROR,
                    "Integration of soil module failed with following message: Example "
                    "error message",
                ),
            ),
            id="unsuccessful integration",
        ),
    ],
)
def test_integrate_soil_model(
    mocker, caplog, soil_model_fixture, output, raises, expected_log
):
    """Test that function to integrate the soil model works as expected."""

    mock_integrate = mocker.patch("virtual_rainforest.models.soil.soil_model.solve_ivp")
    mock_integrate.return_value = output

    with raises:
        new_pools = soil_model_fixture.integrate_soil_model()
        # Check returned pools matched (mocked) integrator output
        assert np.allclose(new_pools["new_lmwc"], output.y[:4, -1])
        assert np.allclose(new_pools["new_maom"], output.y[4:, -1])

    # Check that integrator is called once (and once only)
    mock_integrate.assert_called_once()

    log_check(caplog, expected_log)


def test_construct_full_soil_model(dummy_carbon_data):
    """Test that the function that creates the object to integrate exists and works."""

    from virtual_rainforest.models.soil.soil_model import construct_full_soil_model

    delta_pools = [
        -3.976666e-4,
        -1.1783424e-5,
        -1.434178e-4,
        -2.80362e-7,
        3.976666e-4,
        1.1783424e-5,
        1.434178e-4,
        2.80362e-7,
    ]

    # make pools
    pools = np.concatenate(
        [
            dummy_carbon_data["low_molecular_weight_c"].to_numpy(),
            dummy_carbon_data["mineral_associated_om"].to_numpy(),
        ]
    )

    rate_of_change = construct_full_soil_model(0.0, pools, dummy_carbon_data, 4)

    assert np.allclose(delta_pools, rate_of_change)
