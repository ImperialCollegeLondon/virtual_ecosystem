"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
from scipy.optimize import OptimizeResult  # type: ignore
from xarray import DataArray, Dataset

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.models.soil.constants import SoilConsts
from virtual_rainforest.models.soil.soil_model import IntegrationError, SoilModel


@pytest.fixture
def soil_model_fixture(dummy_carbon_data):
    """Create a soil model fixture based on the dummy carbon data."""

    from virtual_rainforest.models.soil.soil_model import SoilModel

    config = {
        "core": {
            "timing": {"start_date": "2020-01-01", "update_interval": "12 hours"},
            "layers": {"soil_layers": [-0.5, -1.0], "canopy_layers": 10},
        },
    }
    return SoilModel.from_config(dummy_carbon_data, config, pint.Quantity("12 hours"))


@pytest.mark.parametrize(
    "bad_data,raises,expected_log_entries",
    [
        (
            [],
            does_not_raise(),
            (
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_maom' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_lmwc' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_microbe' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_pom' checked",
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
                    "soil model: init data missing required var " "'soil_c_pool_maom'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var " "'soil_c_pool_lmwc'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var "
                    "'soil_c_pool_microbe'",
                ),
                (
                    ERROR,
                    "soil model: init data missing required var " "'soil_c_pool_pom'",
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
                    "Replacing data array for 'soil_c_pool_lmwc'",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_maom' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_lmwc' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_microbe' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_pom' checked",
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
                carbon_data["soil_c_pool_lmwc"] = DataArray(
                    [0.05, 0.02, 0.1, -0.005], dims=["cell_id"]
                )
            # Initialise model with bad data object
            model = SoilModel(
                carbon_data,
                pint.Quantity("1 week"),
                [-0.5, -1.0],
                10,
                constants=SoilConsts,
            )
        else:
            model = SoilModel(
                dummy_carbon_data,
                pint.Quantity("1 week"),
                [-0.5, -1.0],
                10,
                constants=SoilConsts,
            )

        # In cases where it passes then checks that the object has the right properties
        assert set(["setup", "spinup", "update", "cleanup", "integrate"]).issubset(
            dir(model)
        )
        assert model.model_name == "soil"
        assert str(model) == "A soil model instance"
        assert repr(model) == "SoilModel(update_interval = 1 week)"

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,time_interval,max_decomp,raises,expected_log_entries",
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
                        "update_interval": "12 hours",
                    },
                    "layers": {"soil_layers": [-0.5, -1.0], "canopy_layers": 10},
                },
            },
            pint.Quantity("12 hours"),
            0.2,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_maom' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_lmwc' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_microbe' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_pom' checked",
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
                    "soil model: required var 'percent_clay' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 hours",
                    },
                    "layers": {"soil_layers": [-0.5, -1.0], "canopy_layers": 10},
                },
                "soil": {"constants": {"SoilConsts": {"max_decomp_rate_pom": 0.05}}},
            },
            pint.Quantity("12 hours"),
            0.05,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_maom' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_lmwc' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_microbe' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_pom' checked",
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
                    "soil model: required var 'percent_clay' checked",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 hours",
                    },
                    "layers": {"soil_layers": [-0.5, -1.0], "canopy_layers": 10},
                },
                "soil": {"constants": {"SoilConsts": {"max_decomp_rate": 0.05}}},
            },
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for SoilConsts: max_decomp_rate",
                ),
                (
                    INFO,
                    "Valid names are as follows: ",
                ),
            ),
        ),
    ],
)
def test_generate_soil_model(
    caplog,
    dummy_carbon_data,
    config,
    time_interval,
    max_decomp,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the soil model behaves as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(
            dummy_carbon_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.update_interval == time_interval
        assert model.constants.max_decomp_rate_pom == max_decomp

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


# Check that mocked function is called
def test_update(mocker, soil_model_fixture, dummy_carbon_data):
    """Test to check that the update step works and increments the update step."""

    end_lmwc = [0.04980117, 0.01999411, 0.09992829, 0.00499986]
    end_maom = [2.50019883, 1.70000589, 4.50007171, 0.50000014]
    end_microbe = [5.8, 2.3, 11.3, 1.0]
    end_pom = [0.25, 2.34, 0.746, 0.3467]

    mock_integrate = mocker.patch.object(soil_model_fixture, "integrate")

    mock_integrate.return_value = Dataset(
        data_vars=dict(
            soil_c_pool_lmwc=DataArray(end_lmwc, dims="cell_id"),
            soil_c_pool_maom=DataArray(end_maom, dims="cell_id"),
            soil_c_pool_microbe=DataArray(end_microbe, dims="cell_id"),
            soil_c_pool_pom=DataArray(end_pom, dims="cell_id"),
        )
    )

    soil_model_fixture.update(time_index=0)

    # Check that integrator is called once (and once only)
    mock_integrate.assert_called_once()

    # Check that data fixture has been updated correctly
    assert np.allclose(dummy_carbon_data["soil_c_pool_lmwc"], end_lmwc)
    assert np.allclose(dummy_carbon_data["soil_c_pool_maom"], end_maom)
    assert np.allclose(dummy_carbon_data["soil_c_pool_microbe"], end_microbe)
    assert np.allclose(dummy_carbon_data["soil_c_pool_pom"], end_pom)


@pytest.mark.parametrize(
    argnames=["mock_output", "raises", "final_pools", "expected_log"],
    argvalues=[
        pytest.param(
            False,
            does_not_raise(),
            Dataset(
                data_vars=dict(
                    lmwc=DataArray(
                        [0.1502544, 0.30981779, 0.54905976, 0.01720145], dims="cell_id"
                    ),
                    maom=DataArray(
                        [2.49626565, 1.69807102, 4.27549122, 0.50013555], dims="cell_id"
                    ),
                    microbe=DataArray(
                        [5.77621702, 2.29382118, 11.24667052, 0.99641455],
                        dims="cell_id",
                    ),
                    pom=DataArray(
                        [0.02799626, 0.71863676, 0.52836946, 0.34396149], dims="cell_id"
                    ),
                    enzyme_pom=DataArray(
                        [0.02267844, 0.00957582, 0.05004954, 0.00300993], dims="cell_id"
                    ),
                )
            ),
            (),
            id="successful integration",
        ),
        pytest.param(
            OptimizeResult(success=False, message="Example error message"),
            pytest.raises(IntegrationError),
            None,
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
    mocker, caplog, soil_model_fixture, mock_output, raises, final_pools, expected_log
):
    """Test that function to integrate the soil model works as expected."""

    if mock_output:
        mock_integrate = mocker.patch(
            "virtual_rainforest.models.soil.soil_model.solve_ivp"
        )
        mock_integrate.return_value = mock_output

    with raises:
        new_pools = soil_model_fixture.integrate()
        # Check returned pools matched (mocked) integrator output
        assert np.allclose(new_pools["soil_c_pool_lmwc"], final_pools["lmwc"])
        assert np.allclose(new_pools["soil_c_pool_maom"], final_pools["maom"])
        assert np.allclose(new_pools["soil_c_pool_microbe"], final_pools["microbe"])
        assert np.allclose(new_pools["soil_c_pool_pom"], final_pools["pom"])
        assert np.allclose(new_pools["soil_enzyme_pom"], final_pools["enzyme_pom"])

    # Check that integrator is called once (and once only)
    if mock_output:
        mock_integrate.assert_called_once()

    log_check(caplog, expected_log)


def test_order_independance(dummy_carbon_data, soil_model_fixture):
    """Check that pool order in the data object doesn't change integration result."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.soil.soil_model import SoilModel

    # Create new data object with same size as dummy_carbon_data fixture
    grid = Grid(
        cell_nx=dummy_carbon_data.grid.cell_nx, cell_ny=dummy_carbon_data.grid.cell_ny
    )
    new_data = Data(grid)

    # Add all the non-pool data into the new data object
    not_pools = [
        "pH",
        "bulk_density",
        "soil_moisture",
        "matric_potential",
        "soil_temperature",
        "percent_clay",
        "litter_C_mineralisation_rate",
    ]
    for not_pool in not_pools:
        new_data[not_pool] = dummy_carbon_data[not_pool]

    # Then extract soil carbon pool names from the fixture (in order)
    pool_names = [
        str(name)
        for name in dummy_carbon_data.data.keys()
        if str(name).startswith("soil_c_pool_") or str(name).startswith("soil_enzyme_")
    ]

    # Add pool values from object in reversed order
    for pool_name in reversed(pool_names):
        new_data[pool_name] = dummy_carbon_data[pool_name]

    # Use this new data to make a new soil model object
    config = {
        "core": {
            "timing": {"start_date": "2020-01-01", "update_interval": "12 hours"},
            "layers": {"soil_layers": [-0.5, -1.0], "canopy_layers": 10},
        },
    }
    new_soil_model = SoilModel.from_config(new_data, config, pint.Quantity("12 hours"))

    # Integrate using both data objects
    output = soil_model_fixture.integrate()
    output_reversed = new_soil_model.integrate()

    # Compare each final pool
    for pool_name in pool_names:
        assert np.allclose(output[pool_name], output_reversed[pool_name])


def test_construct_full_soil_model(dummy_carbon_data, top_soil_layer_index):
    """Test that the function that creates the object to integrate exists and works."""

    from virtual_rainforest.models.soil.soil_model import construct_full_soil_model

    delta_pools = [
        0.285312441,
        0.604139906,
        0.628571415,
        2.47404600e-02,
        -5.40856802e-3,
        -5.81942847e-3,
        -0.159994002,
        1.82192909e-5,
        -5.12729145e-2,
        -2.17193460e-2,
        -0.115733902,
        -7.20535616e-3,
        -0.227106777,
        -0.575786938,
        -0.353592292,
        -1.21264202e-2,
        1.17571917e-8,
        1.67442231e-8,
        1.83311362e-9,
        -1.11675865e-08,
    ]

    # make pools
    pools = np.concatenate(
        [
            dummy_carbon_data[str(name)].to_numpy()
            for name in dummy_carbon_data.data.keys()
            if str(name).startswith("soil_c_pool_")
            or str(name).startswith("soil_enzyme_")
        ]
    )

    # Find and store order of pools
    delta_pools_ordered = {
        str(name): np.array([])
        for name in dummy_carbon_data.data.keys()
        if str(name).startswith("soil_c_pool_") or str(name).startswith("soil_enzyme_")
    }

    rate_of_change = construct_full_soil_model(
        0.0,
        pools,
        dummy_carbon_data,
        4,
        top_soil_layer_index,
        delta_pools_ordered=delta_pools_ordered,
        constants=SoilConsts,
    )

    assert np.allclose(delta_pools, rate_of_change)


def test_make_slices():
    """Test that function to make slices works as expected."""
    from virtual_rainforest.models.soil.soil_model import make_slices

    no_cells = 4
    no_pools = 2

    slices = make_slices(no_cells, no_pools)

    assert len(slices) == no_pools
    assert slices[0] == slice(0, 4)
    assert slices[1] == slice(4, 8)
