"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
from scipy.optimize import OptimizeResult  # type: ignore
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.models.soil.soil_model import IntegrationError
from xarray import DataArray, Dataset

from tests.conftest import log_check


def test_soil_model_initialization(
    caplog, dummy_carbon_data, fixture_soil_core_components
):
    """Test `SoilModel` initialization with good data."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_soil_core_components,
        model_constants=SoilConsts(),
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert hasattr(model, "integrate")
    assert model.model_name == "soil"
    assert str(model) == "A soil model instance"
    assert repr(model) == "SoilModel(update_interval=43200 seconds)"

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
            (DEBUG, "soil model: required var 'clay_fraction' checked"),
        ),
    )


def test_soil_model_initialization_no_data(
    caplog, dummy_carbon_data, fixture_core_components
):
    """Test `SoilModel` initialization with no data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        empty_data = Data(grid)

        # Try and initialise model with empty data object
        _ = SoilModel(
            data=empty_data,
            core_components=fixture_core_components,
            model_constants=SoilConsts(),
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
            (ERROR, "soil model: init data missing required var 'clay_fraction'"),
            (ERROR, "soil model: error checking required_init_vars, see log."),
        ),
    )


def test_soil_model_initialization_bounds_error(
    caplog, dummy_carbon_data, fixture_core_components
):
    """Test `SoilModel` initialization."""

    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    with pytest.raises(InitialisationError):
        # Put incorrect data in for lmwc
        dummy_carbon_data["soil_c_pool_lmwc"] = DataArray(
            [0.05, 0.02, 0.1, -0.005], dims=["cell_id"]
        )

        # Initialise model with bad data object
        _ = SoilModel(
            data=dummy_carbon_data,
            core_components=fixture_core_components,
            model_constants=SoilConsts(),
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
            (DEBUG, "soil model: required var 'clay_fraction' checked"),
            (ERROR, "Initial carbon pools contain at least one negative value!"),
        ),
    )


@pytest.mark.parametrize(
    "cfg_string,max_decomp,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n[soil]\n",
            60.0,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
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
                (DEBUG, "soil model: required var 'clay_fraction' checked"),
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[soil.constants.SoilConsts]\nmax_decomp_rate_pom = 0.05\n",
            0.05,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
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
                (DEBUG, "soil model: required var 'clay_fraction' checked"),
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[soil.constants.SoilConsts]\nmax_decomp_rate = 0.05\n",
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
    max_decomp,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the soil model behaves as expected."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.registry import register_module
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Register the module components to access constants classes
    register_module("virtual_ecosystem.models.soil")

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(
            data=dummy_carbon_data,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.max_decomp_rate_pom == max_decomp

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


# Check that mocked function is called
def test_update(mocker, fixture_soil_model, dummy_carbon_data):
    """Test to check that the update step works and increments the update step."""

    end_lmwc = [0.04980117, 0.01999411, 0.09992829, 0.00499986]
    end_maom = [2.50019883, 1.70000589, 4.50007171, 0.50000014]
    end_microbe = [5.8, 2.3, 11.3, 1.0]
    end_pom = [0.25, 2.34, 0.746, 0.3467]

    mock_integrate = mocker.patch.object(fixture_soil_model, "integrate")

    mock_integrate.return_value = Dataset(
        data_vars=dict(
            soil_c_pool_lmwc=DataArray(end_lmwc, dims="cell_id"),
            soil_c_pool_maom=DataArray(end_maom, dims="cell_id"),
            soil_c_pool_microbe=DataArray(end_microbe, dims="cell_id"),
            soil_c_pool_pom=DataArray(end_pom, dims="cell_id"),
        )
    )

    fixture_soil_model.update(time_index=0)

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
                        [0.04826774, 0.02126701, 0.09200601, 0.00544793], dims="cell_id"
                    ),
                    maom=DataArray(
                        [2.49936689, 1.70118553, 4.50085129, 0.50000614], dims="cell_id"
                    ),
                    microbe=DataArray(
                        [5.77512315, 2.2899636, 11.24827514, 0.99640928], dims="cell_id"
                    ),
                    pom=DataArray(
                        [0.12397575, 1.00508662, 0.7389913, 0.35583206], dims="cell_id"
                    ),
                    enzyme_pom=DataArray(
                        [0.02267842, 0.00957576, 0.05004963, 0.00300993], dims="cell_id"
                    ),
                    enzyme_maom=DataArray(
                        [0.0354453, 0.01167442, 0.02538637, 0.00454144], dims="cell_id"
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
    mocker, caplog, fixture_soil_model, mock_output, raises, final_pools, expected_log
):
    """Test that function to integrate the soil model works as expected."""

    if mock_output:
        mock_integrate = mocker.patch(
            "virtual_ecosystem.models.soil.soil_model.solve_ivp"
        )
        mock_integrate.return_value = mock_output

    with raises:
        new_pools = fixture_soil_model.integrate()
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


def test_order_independance(
    dummy_carbon_data,
    fixture_soil_model,
    fixture_soil_config,
    fixture_soil_core_components,
):
    """Check that pool order in the data object doesn't change integration result."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.core.registry import register_module
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Register the module components to access constants classes
    register_module("virtual_ecosystem.models.abiotic_simple")

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
    new_soil_model = SoilModel.from_config(
        data=new_data,
        core_components=fixture_soil_core_components,
        config=fixture_soil_config,
    )

    # Integrate using both data objects
    output = fixture_soil_model.integrate()
    output_reversed = new_soil_model.integrate()

    # Compare each final pool
    for pool_name in pool_names:
        assert np.allclose(output[pool_name], output_reversed[pool_name])


def test_construct_full_soil_model(dummy_carbon_data, top_soil_layer_index):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import construct_full_soil_model

    delta_pools = [
        -0.00371115,
        0.00278502,
        -0.01849181,
        0.00089995,
        -1.28996257e-3,
        2.35822401e-3,
        1.5570399e-3,
        1.2082886e-5,
        -0.04978105,
        -0.02020101,
        -0.10280967,
        -0.00719517,
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

    rate_of_change = construct_full_soil_model(
        0.0,
        pools=pools,
        data=dummy_carbon_data,
        no_cells=4,
        top_soil_layer_index=top_soil_layer_index,
        delta_pools_ordered=delta_pools_ordered,
        model_constants=SoilConsts,
        core_constants=CoreConsts,
    )

    assert np.allclose(delta_pools, rate_of_change)


def test_make_slices():
    """Test that function to make slices works as expected."""
    from virtual_ecosystem.models.soil.soil_model import make_slices

    no_cells = 4
    no_pools = 2

    slices = make_slices(no_cells, no_pools)

    assert len(slices) == no_pools
    assert slices[0] == slice(0, 4)
    assert slices[1] == slice(4, 8)
