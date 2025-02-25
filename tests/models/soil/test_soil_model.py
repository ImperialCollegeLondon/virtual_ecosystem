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
    (DEBUG, "soil model: required var 'soil_c_pool_bacteria' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_fungi' checked"),
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
                        [0.05714338, 0.02206952, 0.11592186, 0.01538873], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.52007289, 1.71105702, 4.5340965, 0.53207841], dims="cell_id"
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77302395, 2.28877945, 11.24105325, 0.99642196],
                        dims="cell_id",
                    ),
                    soil_c_pool_fungi=DataArray(
                        [0.88590099, 8.509643, 2.19875113, 4.52376326],
                        dims="cell_id",
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.10088811, 0.99597975, 0.69401136, 0.35272452], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.06167057, 0.05209252, 0.11550511, 0.08189107], dims="cell_id"
                    ),
                    soil_enzyme_pom=DataArray(
                        [0.02271979, 0.00999937, 0.0501659, 0.00317262], dims="cell_id"
                    ),
                    soil_enzyme_maom=DataArray(
                        [0.03548666, 0.01209803, 0.02550264, 0.00470413], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00138664, 0.00297325, 0.00279915, 0.00393828], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.00714835, 0.00074622, 0.00292266, 0.014293], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.0065247, 0.01818108, 0.02331271, 0.00956047], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86680802, 0.4867186, 0.33433055, 0.09972284], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00053212, 0.01537305, 0.00040683, 0.00544821],
                        dims="cell_id",
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [0.00189446, 0.00388282, 0.00030788, 0.01291297], dims="cell_id"
                    ),
                    soil_p_pool_dop=DataArray(
                        [0.00017326, 0.00012043, 0.00032658, 0.00018222],
                        dims="cell_id",
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.21779733e-5, 2.85119757e-4, 1.14675695e-4, 5.71720292e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.00195702, 0.00148389, 0.00366335, 0.00078355], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.01356763, 0.03488897, 0.02001905, 0.0040638], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705643, 0.03816757, 0.01152552, 0.00733096], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [-5.39902139e-7, -1.35782323e-5, 4.95128072e-6, 1.94311546e-4],
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


def test_construct_full_soil_model(
    dummy_carbon_data, fixture_core_components, functional_groups
):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import (
        SoilModel,
        construct_full_soil_model,
    )

    delta_pools = [
        0.014909863,
        0.0026977357,
        0.03275147271,
        0.023993336945,
        0.038767651,
        0.00829848,
        0.05982197,
        0.07277182,
        -0.054361097,
        -0.022606231,
        -0.118911406,
        -0.007195167,
        -0.0083255777,
        -0.0819293436,
        -0.022969005,
        -0.032666056,
        0.00177803841,
        -0.007860960795,
        -0.012016245,
        0.00545032,
        0.00932274,
        0.09290406,
        0.05659641,
        -0.05764445,
        8.3534893e-5,
        0.0008544245,
        0.0002349318,
        0.0003279076,
        -0.000226569,
        0.0008034485,
        0.0008339958,
        0.0002907076,
        0.00120116138,
        0.00389444416,
        0.00505259291,
        0.00239278244,
        1.102338e-5,
        6.422491e-5,
        0.000131687,
        1.461799e-5,
        0.00912041,
        0.000782751,
        0.007865652,
        -0.00396817,
        0.00148604,
        0.01179891,
        0.01365197,
        0.0077315,
        0.00095125671,
        0.02011151359,
        0.00043745,
        0.000572988,
        -0.000295899,
        9.0556049e-6,
        -4.592098e-5,
        -0.000242911,
        0.0001944445,
        5.8853523e-5,
        0.0001841704,
        9.5709618e-5,
        7.22218e-6,
        -1.13464e-6,
        7.86083e-7,
        5.85634364e-7,
        0.002879471,
        0.003426353,
        0.007384646,
        0.000844827,
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
        -4.432585e-6,
        -9.510288e-5,
        -8.470421e-5,
        2.6867148e-6,
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
        functional_groups=functional_groups,
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
