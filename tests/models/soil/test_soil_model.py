"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
from scipy.optimize import OptimizeResult  # type: ignore
from xarray import DataArray, Dataset

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.models.soil.soil_model import IntegrationError


@pytest.fixture
def soil_model_fixture(dummy_carbon_data):
    """Create a soil model fixture based on the dummy carbon data."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.soil.soil_model import SoilModel

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic_simple")
    # Build the config object
    config = Config(
        cfg_strings="[core]\n[core.timing]\nupdate_interval = '12 hours'\n[soil]\n"
    )

    return SoilModel.from_config(
        data=dummy_carbon_data, config=config, update_interval=pint.Quantity("12 hours")
    )


def test_soil_model_initialization(caplog, dummy_carbon_data):
    """Test `SoilModel` initialization with good data."""
    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.models.soil.constants import SoilConsts
    from virtual_rainforest.models.soil.soil_model import SoilModel

    model = SoilModel(
        dummy_carbon_data,
        pint.Quantity("1 week"),
        [-0.5, -1.0],
        10,
        model_constants=SoilConsts,
        core_constants=CoreConsts,
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert hasattr(model, "integrate")
    assert model.model_name == "soil"
    assert str(model) == "A soil model instance"
    assert repr(model) == "SoilModel(update_interval = 1 week)"

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
            (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
            (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
            (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
            (DEBUG, "soil model: required var 'pH' checked"),
            (DEBUG, "soil model: required var 'bulk_density' checked"),
            (DEBUG, "soil model: required var 'percent_clay' checked"),
            (DEBUG, "soil model: required var 'clay_fraction' checked"),
        ),
    )


def test_soil_model_initialization_no_data(caplog, dummy_carbon_data):
    """Test `SoilModel` initialization with no data."""

    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.soil.constants import SoilConsts
    from virtual_rainforest.models.soil.soil_model import SoilModel

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        empty_data = Data(grid)

        # Try and initialise model with empty data object
        _ = SoilModel(
            empty_data,
            pint.Quantity("1 week"),
            [-0.5, -1.0],
            10,
            model_constants=SoilConsts,
            core_constants=CoreConsts,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (ERROR, "soil model: init data missing required var 'soil_c_pool_maom'"),
            (ERROR, "soil model: init data missing required var 'soil_c_pool_lmwc'"),
            (ERROR, "soil model: init data missing required var 'soil_c_pool_microbe'"),
            (ERROR, "soil model: init data missing required var 'soil_c_pool_pom'"),
            (ERROR, "soil model: init data missing required var 'pH'"),
            (ERROR, "soil model: init data missing required var 'bulk_density'"),
            (ERROR, "soil model: init data missing required var 'percent_clay'"),
            (ERROR, "soil model: init data missing required var 'clay_fraction'"),
            (ERROR, "soil model: error checking required_init_vars, see log."),
        ),
    )


def test_soil_model_initialization_bounds_error(caplog, dummy_carbon_data):
    """Test `SoilModel` initialization."""

    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.models.soil.constants import SoilConsts
    from virtual_rainforest.models.soil.soil_model import SoilModel

    with pytest.raises(InitialisationError):
        # Put incorrect data in for lmwc
        dummy_carbon_data["soil_c_pool_lmwc"] = DataArray(
            [0.05, 0.02, 0.1, -0.005], dims=["cell_id"]
        )

        # Initialise model with bad data object
        _ = SoilModel(
            dummy_carbon_data,
            pint.Quantity("1 week"),
            [-0.5, -1.0],
            10,
            model_constants=SoilConsts,
            core_constants=CoreConsts,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (INFO, "Replacing data array for 'soil_c_pool_lmwc'"),
            (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
            (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
            (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
            (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
            (DEBUG, "soil model: required var 'pH' checked"),
            (DEBUG, "soil model: required var 'bulk_density' checked"),
            (DEBUG, "soil model: required var 'percent_clay' checked"),
            (DEBUG, "soil model: required var 'clay_fraction' checked"),
            (ERROR, "Initial carbon pools contain at least one negative value!"),
        ),
    )


@pytest.mark.parametrize(
    "cfg_string,time_interval,max_decomp,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n[soil]\n",
            pint.Quantity("12 hours"),
            60.0,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
                (INFO, "Initialised core.CoreConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
                (DEBUG, "soil model: required var 'pH' checked"),
                (DEBUG, "soil model: required var 'bulk_density' checked"),
                (DEBUG, "soil model: required var 'percent_clay' checked"),
                (DEBUG, "soil model: required var 'clay_fraction' checked"),
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[soil.constants.SoilConsts]\nmax_decomp_rate_pom = 0.05\n",
            pint.Quantity("12 hours"),
            0.05,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
                (INFO, "Initialised core.CoreConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
                (DEBUG, "soil model: required var 'pH' checked"),
                (DEBUG, "soil model: required var 'bulk_density' checked"),
                (DEBUG, "soil model: required var 'percent_clay' checked"),
                (DEBUG, "soil model: required var 'clay_fraction' checked"),
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[soil.constants.SoilConsts]\nmax_decomp_rate = 0.05\n",
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Unknown names supplied for SoilConsts: max_decomp_rate"),
                (INFO, "Valid names are: "),
                (CRITICAL, "Could not initialise soil.SoilConsts from config"),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_soil_model(
    caplog,
    dummy_carbon_data,
    cfg_string,
    time_interval,
    max_decomp,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the soil model behaves as expected."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.soil.soil_model import SoilModel

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.soil")

    # Build the config object
    config = Config(cfg_strings=cfg_string)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(
            dummy_carbon_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.update_interval == time_interval
        assert model.model_constants.max_decomp_rate_pom == max_decomp

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
                        [0.0366784, 0.01370983, 0.09813822, 0.00504219], dims="cell_id"
                    ),
                    maom=DataArray(
                        [2.49755121, 1.69965727, 4.42458918, 0.5000198], dims="cell_id"
                    ),
                    microbe=DataArray(
                        [5.77991878, 2.29291625, 11.26764116, 0.99644925],
                        dims="cell_id",
                    ),
                    pom=DataArray(
                        [0.12398595, 1.00509301, 0.73903078, 0.35583213], dims="cell_id"
                    ),
                    enzyme_pom=DataArray(
                        [0.02267854, 0.00957584, 0.05005016, 0.00300993], dims="cell_id"
                    ),
                    enzyme_maom=DataArray(
                        [0.03544542, 0.0116745, 0.02538689, 0.00454144], dims="cell_id"
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
        assert np.allclose(new_pools["soil_enzyme_maom"], final_pools["enzyme_maom"])

    # Check that integrator is called once (and once only)
    if mock_output:
        mock_integrate.assert_called_once()

    log_check(caplog, expected_log)


def test_order_independance(dummy_carbon_data, soil_model_fixture):
    """Check that pool order in the data object doesn't change integration result."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.soil.soil_model import SoilModel

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic_simple")

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
        "vertical_flow",
        "soil_temperature",
        "percent_clay",
        "clay_fraction",
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
    config = Config(
        cfg_strings="[core]\n[core.timing]\nupdate_interval = '12 hours'\n[soil]\n"
    )
    new_soil_model = SoilModel.from_config(new_data, config, pint.Quantity("12 hours"))

    # Integrate using both data objects
    output = soil_model_fixture.integrate()
    output_reversed = new_soil_model.integrate()

    # Compare each final pool
    for pool_name in pool_names:
        assert np.allclose(output[pool_name], output_reversed[pool_name])


def test_construct_full_soil_model(dummy_carbon_data, top_soil_layer_index):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.models.soil.constants import SoilConsts
    from virtual_rainforest.models.soil.soil_model import construct_full_soil_model

    delta_pools = [
        -3.16893813e-2,
        -1.69743479e-2,
        8.89094764e-3,
        7.00110385e-4,
        -5.23864573e-3,
        -1.35947690e-3,
        -0.153741246,
        3.89316909e-5,
        -3.82877348e-2,
        -1.24543917e-2,
        -6.44638512e-2,
        -7.11457978e-3,
        4.80916464e-2,
        1.02354410e-2,
        7.85372753e-2,
        1.16756409e-2,
        1.17571917e-8,
        1.67442231e-8,
        1.83311362e-9,
        -1.11675865e-08,
        -0.00031009,
        -5.09593e-5,
        0.0005990658,
        -3.72112e-5,
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

    # Find rate of flow per day
    vertical_flow_per_day = (
        dummy_carbon_data["vertical_flow"][top_soil_layer_index].to_numpy() / 30.0
    )

    rate_of_change = construct_full_soil_model(
        0.0,
        pools=pools,
        data=dummy_carbon_data,
        vertical_flow_per_day=vertical_flow_per_day,
        no_cells=4,
        top_soil_layer_index=top_soil_layer_index,
        delta_pools_ordered=delta_pools_ordered,
        model_constants=SoilConsts,
        core_constants=CoreConsts,
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
