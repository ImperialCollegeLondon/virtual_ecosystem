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
    (DEBUG, "soil model: required var 'soil_enzyme_pom_bacteria' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_maom_bacteria' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_pom_fungi' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_maom_fungi' checked"),
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
POST_SETUP_LOG = (
    *REQUIRED_INIT_VAR_LOG,
    (INFO, "Adding data array for 'dissolved_nitrate'"),
    (INFO, "Adding data array for 'dissolved_ammonium'"),
    (INFO, "Adding data array for 'dissolved_phosphorus'"),
)


def test_soil_model_initialization(
    caplog,
    dummy_carbon_data,
    fixture_soil_core_components,
    functional_groups,
    enzyme_classes,
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
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
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
        expected_log=POST_SETUP_LOG,
    )


def test_soil_model_initialization_no_data(
    caplog,
    dummy_carbon_data,
    fixture_core_components,
    enzyme_classes,
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
    caplog,
    dummy_carbon_data,
    fixture_core_components,
    functional_groups,
    enzyme_classes,
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
            microbial_groups=functional_groups,
            enzyme_classes=enzyme_classes,
            soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (INFO, "Replacing data array for 'soil_c_pool_lmwc'"),
            *POST_SETUP_LOG,
            (ERROR, "Initial carbon pools contain at least one negative value!"),
        ),
    )


def test_soil_model_all_pools_positive(
    dummy_carbon_data, fixture_core_components, functional_groups, enzyme_classes
):
    """Test `SoilModel` initialization."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Initialise model with bad data object
    soil_model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_core_components,
        model_constants=SoilConsts(),
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
    )

    assert soil_model._all_pools_positive()

    # Change data to be incorrect for necromass
    dummy_carbon_data["soil_c_pool_necromass"] = DataArray(
        [0.05, -0.02, 0.1, 0.005], dims=["cell_id"]
    )

    assert not soil_model._all_pools_positive()


@pytest.mark.parametrize(
    "cfg_string,solub_coeff,raises,expected_log_entries",
    [
        pytest.param(
            "",
            0.005,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                *POST_SETUP_LOG,
            ),
            id="default_config",
        ),
        pytest.param(
            "[soil.constants.SoilConsts]\nsolubility_coefficient_labile_p = 0.05",
            0.05,
            does_not_raise(),
            (
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                *POST_SETUP_LOG,
            ),
            id="modified_config_correct",
        ),
        pytest.param(
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
    microbial_groups_cfg,
    cfg_string,
    solub_coeff,
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
    config = Config(
        cfg_strings=[
            "[core]\n[core.timing]\nupdate_interval = '12 hours'",
            microbial_groups_cfg,
            cfg_string,
        ]
    )
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(
            data=dummy_carbon_data,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.solubility_coefficient_labile_p == solub_coeff

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


# Check that mocked function is called
def test_update(mocker, fixture_soil_model, dummy_carbon_data):
    """Test to check that the update step works and increments the update step."""

    # Set of pools to be returned to test that update does use (mocked) integrator
    end_lmwc = [0.04980117, 0.01999411, 0.09992829, 0.00499986]
    end_maom = [2.50019883, 1.70000589, 4.50007171, 0.50000014]
    end_microbe = [5.8, 2.3, 11.3, 1.0]
    end_pom = [0.25, 2.34, 0.746, 0.3467]
    end_necromass = [0.058, 0.015, 0.093, 0.105]

    # Set nutrient values to test the dissolved nutrient values calculation step
    end_nitrate = [0.05, 0.075, 0.09, 0.002]
    end_ammonium = [0.1, 0.2, 0.3, 0.4]
    end_phosphorus = [4e-3, 3e-3, 2e-3, 1e-3]
    dissolved_nitrate = [0.05, 0.075, 0.09, 0.002]
    dissolved_ammonium = [0.005, 0.01, 0.015, 0.02]
    dissolved_phosphorus = [2.0e-5, 1.5e-5, 1.0e-5, 5.0e-6]

    mock_integrate = mocker.patch.object(fixture_soil_model, "integrate")

    mock_integrate.return_value = Dataset(
        data_vars=dict(
            soil_c_pool_lmwc=DataArray(end_lmwc, dims="cell_id"),
            soil_c_pool_maom=DataArray(end_maom, dims="cell_id"),
            soil_c_pool_microbe=DataArray(end_microbe, dims="cell_id"),
            soil_c_pool_pom=DataArray(end_pom, dims="cell_id"),
            soil_c_pool_necromass=DataArray(end_necromass, dims="cell_id"),
            soil_n_pool_nitrate=DataArray(end_nitrate, dims="cell_id"),
            soil_n_pool_ammonium=DataArray(end_ammonium, dims="cell_id"),
            soil_p_pool_labile=DataArray(end_phosphorus, dims="cell_id"),
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

    # Check that dissolved values are populated based on values supplied by (mocked)
    # integrator
    assert np.allclose(dummy_carbon_data["dissolved_nitrate"], dissolved_nitrate)
    assert np.allclose(dummy_carbon_data["dissolved_ammonium"], dissolved_ammonium)
    assert np.allclose(dummy_carbon_data["dissolved_phosphorus"], dissolved_phosphorus)


@pytest.mark.parametrize(
    argnames=["mock_output", "raises", "final_pools", "expected_log"],
    argvalues=[
        pytest.param(
            False,
            does_not_raise(),
            Dataset(
                data_vars=dict(
                    soil_c_pool_lmwc=DataArray(
                        [0.10865825, 0.05329372, 0.2206471, 0.02045373], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.51943826, 1.70859259, 4.53271067, 0.53208277], dims="cell_id"
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77301845, 2.28884539, 11.24102147, 0.99642359],
                        dims="cell_id",
                    ),
                    soil_c_pool_fungi=DataArray(
                        [0.88589888, 8.51025597, 2.19873561, 4.52379402],
                        dims="cell_id",
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.10011147, 0.9851898, 0.69082832, 0.35260191], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.06200223, 0.05221315, 0.11560307, 0.08195386], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02267837, 0.00957573, 0.05004943, 0.00300993], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.03544525, 0.01167439, 0.02538618, 0.00454144], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02580045, 0.00610504, 0.00649941, 0.00452008], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00860701, 0.00716821, 0.00387805, 0.00229989], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00169365, 0.00383974, 0.00294508, 0.00394796], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.0070931, 0.00073832, 0.00290946, 0.01428801], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.0065757, 0.01819928, 0.02332773, 0.00957007], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86657283, 0.48601413, 0.33422871, 0.099723], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.0004275, 0.01509396, 0.00035874, 0.00524329], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [0.00056245, 0.00203824, -0.00016233, 0.01271296],
                        dims="cell_id",
                    ),
                    soil_p_pool_dop=DataArray(
                        [0.00017829, 0.00017471, 0.00033654, 0.00018269], dims="cell_id"
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.19431193e-5, 2.82033889e-4, 1.14152879e-4, 5.71520842e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.0019653, 0.00148675, 0.00366575, 0.00078505], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.01356543, 0.03483871, 0.02001331, 0.00406402], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733096], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [-6.65834883e-6, -1.33255769e-4, 2.35622831e-7, 1.91333142e-4],
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
        "air_temperature",
        "clay_fraction",
        "litter_C_mineralisation_rate",
        "litter_N_mineralisation_rate",
        "litter_P_mineralisation_rate",
        "nitrogen_fixation_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
    ]
    for not_pool in not_pools:
        new_data[not_pool] = dummy_carbon_data[not_pool]

    # Then extract soil carbon pool names from the fixture (in order)
    pool_names = [
        name
        for name in dummy_carbon_data.data.keys()
        if name in SoilModel.vars_updated
        and name not in SoilModel.vars_populated_by_init
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


def test_calculate_dissolved_nutrient_concentrations(fixture_soil_model):
    """Test that the dissolved nutrient concentrations are calculated correctly."""

    expected_concs = {
        "dissolved_ammonium": [3.4809819e-6, 0.0002495731, 1.145335e-5, 0.000259776695],
        "dissolved_nitrate": [0.0024219014, 0.0044442996, 0.0003428348, 0.0131405173],
        "dissolved_phosphorus": [5.2911965e-8, 1.6264805e-7, 3.4033725e-7, 9.728175e-7],
    }

    actual_concs = fixture_soil_model.calculate_dissolved_nutrient_concentrations()

    assert expected_concs.keys() == actual_concs.keys()

    for nutrient in expected_concs.keys():
        assert np.allclose(actual_concs[nutrient], expected_concs[nutrient])


def test_calculate_dissolved_nutrient_concentrations_negative(fixture_soil_model):
    """Test that the dissolved nutrient concentrations handles negative values."""

    # Overwrite specific data values with negative values
    fixture_soil_model.data["soil_n_pool_ammonium"][1] = -6.9619638e-5
    fixture_soil_model.data["soil_n_pool_nitrate"][2] = -0.0024219014
    fixture_soil_model.data["soil_p_pool_labile"][0] = -1.0582393e-5

    expected_concs = {
        "dissolved_ammonium": [3.4809819e-6, 0.0, 1.145335e-5, 0.000259776695],
        "dissolved_nitrate": [0.0024219014, 0.0044442996, 0.0, 0.0131405173],
        "dissolved_phosphorus": [0.0, 1.6264805e-7, 3.4033725e-7, 9.728175e-7],
    }

    actual_concs = fixture_soil_model.calculate_dissolved_nutrient_concentrations()

    assert expected_concs.keys() == actual_concs.keys()

    for nutrient in expected_concs.keys():
        assert np.allclose(actual_concs[nutrient], expected_concs[nutrient])


def test_construct_full_soil_model(
    dummy_carbon_data, fixture_core_components, functional_groups, enzyme_classes
):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import (
        SoilModel,
        construct_full_soil_model,
    )

    delta_pools = [
        0.1178918,
        0.06892161,
        0.24201873,
        0.03425211,
        0.03734787,
        0.00340136,
        0.05698608,
        0.07275546,
        -0.054361097,
        -0.022606231,
        -0.118911406,
        -0.007195167,
        -0.0083255777,
        -0.0819293436,
        -0.022969005,
        -0.032666056,
        0.00021589,
        -0.02918772,
        -0.01844761,
        0.00520792,
        0.010156477,
        0.093205884,
        0.056842818,
        -0.057486698,
        1.18e-8,
        1.67e-8,
        1.78e-9,
        -1.12e-8,
        -0.0003101,
        -5.0959e-5,
        0.00059907,
        -3.7211e-5,
        -0.00054216,
        0.000716408,
        7.989000e-5,
        0.000222079,
        -0.00012453,
        0.000690584,
        0.000143562,
        0.00027601,
        0.00180422,
        0.00529461,
        0.00528487,
        0.00240583,
        -1.005585e-4,
        4.899227e-5,
        1.05432e-4,
        4.723906e-6,
        0.00924867,
        0.00082919,
        0.00790357,
        -0.00394389,
        0.00099458,
        0.01041398,
        0.01344595,
        0.00772835,
        0.00075125671,
        0.02001151359,
        0.00039745,
        0.000172988,
        -0.003295899,
        -0.003990944,
        -0.001045921,
        -0.000642911,
        2.02317351e-4,
        1.64662024e-4,
        1.97339686e-4,
        9.62312501e-5,
        6.77587e-6,
        -7.228e-6,
        -2.639346e-7,
        1.898709e-7,
        0.002900315,
        0.003433899,
        0.007390806,
        0.000848771,
        5.44660113e-4,
        -6.28584725e-5,
        4.635421e-4,
        3.0913116e-4,
        -4.473516e-10,
        -1.222973e-9,
        -6.33411e-10,
        -1.3674e-10,
        -5.050797e-7,
        -2.77311e-6,
        -7.40324e-7,
        -2.187697e-7,
        -1.643259e-5,
        -0.000295103,
        -9.270421e-5,
        -1.313285e-6,
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
        layer_structure=fixture_core_components.layer_structure,
        delta_pools_ordered=delta_pools_ordered,
        model_constants=SoilConsts,
        functional_groups=functional_groups,
        enzyme_classes=enzyme_classes,
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
