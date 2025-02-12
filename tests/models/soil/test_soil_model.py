"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
from scipy.optimize import OptimizeResult  # type: ignore
from xarray import DataArray, Dataset

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.models.soil.soil_model import IntegrationError

# Shared log entries from model initialisation
REQUIRED_INIT_VAR_LOG = (
    (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_necromass' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_pom' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_maom' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_don' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_particulate' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_necromass' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_maom' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_ammonium' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_nitrate' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_dop' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_particulate' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_necromass' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_maom' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_primary' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_secondary' checked"),
    (DEBUG, "soil model: required var 'soil_p_pool_labile' checked"),
    (DEBUG, "soil model: required var 'pH' checked"),
    (DEBUG, "soil model: required var 'bulk_density' checked"),
    (DEBUG, "soil model: required var 'clay_fraction' checked"),
)


def test_soil_model_initialization(
    caplog, dummy_carbon_data, fixture_soil_core_components
):
    """Test `SoilModel` initialization with good data."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_soil_core_components,
        model_constants=SoilConsts(),
        soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
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
        expected_log=REQUIRED_INIT_VAR_LOG,
    )


def test_soil_model_initialization_no_data(
    caplog, dummy_carbon_data, fixture_core_components
):
    """Test `SoilModel` initialization with no data."""
    from virtual_ecosystem.core.constants import CoreConsts
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
            soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
        )

    # Final check that expected logging entries are produced: modify shared
    # REQUIRED_INIT_VAR_LOG to use shared list of variables
    missing_log = list(
        (
            (
                ERROR,
                log_str.replace(":", ": init data missing").removesuffix(" checked"),
            )
            for _, log_str in REQUIRED_INIT_VAR_LOG
        ),
    )
    missing_log.append(
        (ERROR, "soil model: error checking vars_required_for_init, see log."),
    )

    log_check(
        caplog,
        expected_log=missing_log,
    )


def test_soil_model_initialization_bounds_error(
    caplog, dummy_carbon_data, fixture_core_components
):
    """Test `SoilModel` initialization."""
    from virtual_ecosystem.core.constants import CoreConsts
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
            soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (INFO, "Replacing data array for 'soil_c_pool_lmwc'"),
            *REQUIRED_INIT_VAR_LOG,
            (ERROR, "Initial carbon pools contain at least one negative value!"),
        ),
    )


def test_soil_model_all_pools_positive(dummy_carbon_data, fixture_core_components):
    """Test `SoilModel` initialization."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Initialise model with bad data object
    soil_model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_core_components,
        model_constants=SoilConsts(),
        soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
    )

    assert soil_model._all_pools_positive()

    # Change data to be incorrect for necromass
    dummy_carbon_data["soil_c_pool_necromass"] = DataArray(
        [0.05, -0.02, 0.1, 0.005], dims=["cell_id"]
    )

    assert not soil_model._all_pools_positive()


@pytest.mark.parametrize(
    "cfg_string,max_decomp,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n[soil]",
            60.0,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                *REQUIRED_INIT_VAR_LOG,
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[soil.constants.SoilConsts]\nmax_decomp_rate_pom = 0.05",
            0.05,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                *REQUIRED_INIT_VAR_LOG,
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
    end_necromass = [0.058, 0.015, 0.093, 0.105]

    mock_integrate = mocker.patch.object(fixture_soil_model, "integrate")

    mock_integrate.return_value = Dataset(
        data_vars=dict(
            soil_c_pool_lmwc=DataArray(end_lmwc, dims="cell_id"),
            soil_c_pool_maom=DataArray(end_maom, dims="cell_id"),
            soil_c_pool_microbe=DataArray(end_microbe, dims="cell_id"),
            soil_c_pool_pom=DataArray(end_pom, dims="cell_id"),
            soil_c_pool_necromass=DataArray(end_necromass, dims="cell_id"),
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
    assert np.allclose(dummy_carbon_data["soil_c_pool_necromass"], end_necromass)


@pytest.mark.parametrize(
    argnames=["mock_output", "raises", "final_pools", "expected_log"],
    argvalues=[
        pytest.param(
            False,
            does_not_raise(),
            Dataset(
                data_vars=dict(
                    soil_c_pool_lmwc=DataArray(
                        [0.05713222, 0.02665739, 0.11689175, 0.01486035], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.5194618, 1.70483236, 4.53238116, 0.52968038], dims="cell_id"
                    ),
                    soil_c_pool_microbe=DataArray(
                        [5.77303027, 2.2888041, 11.24109943, 0.9964216],
                        dims="cell_id",
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.10088826, 0.99607827, 0.69401858, 0.35272508], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.05840102, 0.01864856, 0.10631116, 0.06904722], dims="cell_id"
                    ),
                    soil_enzyme_pom=DataArray(
                        [0.02267842, 0.00957576, 0.05004963, 0.00300993], dims="cell_id"
                    ),
                    soil_enzyme_maom=DataArray(
                        [0.0354453, 0.01167442, 0.02538637, 0.00454144], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00135906, 0.00340964, 0.00273513, 0.00390386], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.00714836, 0.00074629, 0.00292269, 0.01429302], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.00602168, 0.01303568, 0.02189821, 0.00758444], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86671423, 0.48576345, 0.33406677, 0.09935391], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.0005364, 0.01499882, 0.00044842, 0.00538707],
                        dims="cell_id",
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [0.00189682, 0.0038413, 0.00031329, 0.01290568], dims="cell_id"
                    ),
                    soil_p_pool_dop=DataArray(
                        [1.68559250e-4, 9.03050817e-5, 3.15038568e-4, 1.66029558e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.21780215e-5, 2.85147941e-4, 1.14676885e-4, 5.71721209e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.00187527, 0.00064763, 0.00343346, 0.00046239], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.01355237, 0.03473323, 0.01997613, 0.00400384], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705643, 0.03816757, 0.01152552, 0.00733096], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [8.87006017e-7, 1.92559822e-5, 1.37908411e-5, 1.93794964e-4],
                        dims="cell_id",
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
        assert set(new_pools.keys()) == set(final_pools.keys())

        for key in new_pools.keys():
            assert np.allclose(new_pools[key], final_pools[key])

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
        "litter_N_mineralisation_rate",
        "litter_P_mineralisation_rate",
        "nitrogen_fixation_carbon_supply",
    ]
    for not_pool in not_pools:
        new_data[not_pool] = dummy_carbon_data[not_pool]

    # Then extract soil carbon pool names from the fixture (in order)
    pool_names = [
        name for name in dummy_carbon_data.data.keys() if name in SoilModel.vars_updated
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


def test_construct_full_soil_model(dummy_carbon_data, fixture_core_components):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import (
        SoilModel,
        construct_full_soil_model,
    )

    delta_pools = [
        0.014984117633,
        0.0133384581,
        0.03449812333,
        0.02425546,
        0.038767651,
        0.00829848,
        0.05982197,
        0.07277182,
        -0.054361097,
        -0.022606231,
        -0.118911406,
        -0.007195167,
        0.00177803841,
        -0.007860960795,
        -0.012016245,
        0.00545032,
        0.001137474,
        0.009172067,
        0.033573266,
        -0.08978050,
        1.17571917e-8,
        1.67442231e-8,
        1.83311362e-9,
        -1.11675865e-08,
        -0.00031009,
        -5.09593e-5,
        0.0005990658,
        -3.72112e-5,
        0.00120201,
        0.004654495,
        0.005055088,
        0.002542567,
        1.102338e-5,
        6.422491e-5,
        0.000131687,
        1.461799e-5,
        0.00786114,
        -0.01209909,
        0.00432363,
        -0.00891218,
        0.00148604,
        0.01179891,
        0.01365197,
        0.0077315,
        0.000952008,
        0.019913667,
        0.000505414,
        0.000455603,
        -0.000293386,
        -1.292735e-5,
        -3.576543e-5,
        -0.000255954,
        0.000194453,
        7.1014337e-5,
        0.0001851685,
        0.0001017010,
        7.22218e-6,
        -1.13464e-6,
        7.86083e-7,
        5.85634364e-7,
        2.674836e-3,
        1.333056e-3,
        6.8090685e-3,
        4.1429847e-5,
        5.52086672e-4,
        3.68566732e-5,
        4.7566130e-4,
        3.09257058e-4,
        -4.473516e-10,
        -1.222973e-9,
        -6.33411e-10,
        -1.3674e-10,
        -5.050797e-7,
        -2.77311e-6,
        -7.40324e-7,
        -2.187697e-7,
        -3.772779e-6,
        -1.947773e-5,
        -7.260241e-5,
        -1.591909e-7,
    ]

    # make pools
    pools = np.concatenate(
        [
            dummy_carbon_data[name].to_numpy()
            for name in dummy_carbon_data.data.keys()
            if name in SoilModel.vars_updated
        ]
    )

    # Find and store order of pools
    delta_pools_ordered = {
        name: np.array([])
        for name in dummy_carbon_data.data.keys()
        if name in SoilModel.vars_updated
    }

    rate_of_change = construct_full_soil_model(
        0.0,
        pools=pools,
        data=dummy_carbon_data,
        no_cells=4,
        top_soil_layer_index=fixture_core_components.layer_structure.index_topsoil_scalar,
        delta_pools_ordered=delta_pools_ordered,
        model_constants=SoilConsts,
        max_depth_of_microbial_activity=CoreConsts.max_depth_of_microbial_activity,
        soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
        top_soil_layer_thickness=fixture_core_components.layer_structure.soil_layer_thickness[
            0
        ],
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
