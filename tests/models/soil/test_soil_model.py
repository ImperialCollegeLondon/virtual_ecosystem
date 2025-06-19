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
    (DEBUG, "soil model: required var 'soil_c_pool_saprotrophic_fungi' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_arbuscular_mycorrhiza' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_ectomycorrhiza' checked"),
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
    (INFO, "Adding data array for 'ecto_supply_limit_n'"),
    (INFO, "Adding data array for 'ecto_supply_limit_p'"),
    (INFO, "Adding data array for 'arbuscular_supply_limit_n'"),
    (INFO, "Adding data array for 'arbuscular_supply_limit_p'"),
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
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_soil_core_components,
        model_constants=SoilConsts(),
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        soil_moisture_saturation=HydroConsts.soil_moisture_saturation,
        soil_moisture_residual=HydroConsts.soil_moisture_residual,
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


def test_soil_model_initialization_no_data(caplog, fixture_core_components):
    """Test `SoilModel` initialization with no data."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
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
            soil_moisture_saturation=HydroConsts.soil_moisture_saturation,
            soil_moisture_residual=HydroConsts.soil_moisture_residual,
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
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
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
            soil_moisture_saturation=HydroConsts.soil_moisture_saturation,
            soil_moisture_residual=HydroConsts.soil_moisture_residual,
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
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Initialise model with bad data object
    soil_model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_core_components,
        model_constants=SoilConsts(),
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        soil_moisture_saturation=HydroConsts.soil_moisture_saturation,
        soil_moisture_residual=HydroConsts.soil_moisture_residual,
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
                (INFO, "Initialised hydrology.HydroConsts from config"),
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
                (INFO, "Initialised hydrology.HydroConsts from config"),
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
            "[hydrology]",
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
                        [0.11130987, 0.10952013, 0.22503828, 0.02241626], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.51940087, 1.70920775, 4.53482025, 0.53791706], dims="cell_id"
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77889227, 2.29145481, 11.25658092, 0.99683258],
                        dims="cell_id",
                    ),
                    soil_c_pool_saprotrophic_fungi=DataArray(
                        [0.88679013, 8.51913763, 2.20174378, 4.52566622],
                        dims="cell_id",
                    ),
                    soil_c_pool_arbuscular_mycorrhiza=DataArray(
                        [0.64717766, 1.45307082, 3.9062627, 9.01256406],
                        dims="cell_id",
                    ),
                    soil_c_pool_ectomycorrhiza=DataArray(
                        [0.46739377, 1.3021928, 4.18468398, 3.75846787],
                        dims="cell_id",
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.10019111, 0.98701484, 0.6890763, 0.35261012], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.06031718, 0.05107944, 0.12718463, 0.11319455], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02240911, 0.00946258, 0.04945798, 0.00297422], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.03517598, 0.01156125, 0.02479473, 0.00450573], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02575927, 0.00568891, 0.00640723, 0.00436826], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00856584, 0.00675208, 0.00378588, 0.00214806], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00150084, 0.0050075, 0.00265, 0.00405533], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.00709876, 0.00073966, 0.0029022, 0.01428834], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.0058284, 0.01711988, 0.02216215, 0.01114677], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86652874, 0.48604324, 0.33400692, 0.10001766], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00017843, 0.01031858, 0.00024426, 0.00482445], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [0.00010727, 0.0002677, -0.00017899, 0.01262905], dims="cell_id"
                    ),
                    soil_p_pool_dop=DataArray(
                        [0.00015755, 0.00011028, 0.00024629, 0.00018744], dims="cell_id"
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.19672137e-5, 2.82555874e-4, 1.13865131e-4, 5.71534199e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.00170704, 0.00124221, 0.00309624, 0.00101001], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.01351864, 0.03480957, 0.01990663, 0.00410603], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733095], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [3.95099648e-6, -7.05836282e-5, 3.40484629e-5, 1.78656777e-4],
                        dims="cell_id",
                    ),
                ),
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
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "plant_n_uptake_arbuscular",
        "plant_n_uptake_ecto",
        "plant_p_uptake_arbuscular",
        "plant_p_uptake_ecto",
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


@pytest.mark.parametrize(
    argnames=["expected_limits", "init"],
    argvalues=[
        pytest.param(
            {
                "ecto_supply_limit_n": [0.0, 0.00040386, 0.0, 0.0],
                "ecto_supply_limit_p": [0.0, 0.0, 0.0, 0.0],
                "arbuscular_supply_limit_n": [0.0, 0.000449755, 0.0, 0.0],
                "arbuscular_supply_limit_p": [0.0, 0.0, 0.0, 0.0],
            },
            False,
            id="update",
        ),
        pytest.param(
            {
                "ecto_supply_limit_n": [0.0, 0.0004152, 0.0, 0.00160258],
                "ecto_supply_limit_p": [0.0, 0.0, 0.0, 0.0],
                "arbuscular_supply_limit_n": [0.0, 0.00046239, 0.0, 0.00384278],
                "arbuscular_supply_limit_p": [0.0, 0.0, 0.0, 0.0],
            },
            True,
            id="init",
        ),
    ],
)
def test_calculate_symbiotic_supply_limits(fixture_soil_model, expected_limits, init):
    """Test that the function to calculate the symbiotic supply limits works."""

    actual_limits = fixture_soil_model.calculate_symbiotic_supply_limits(init=init)

    assert expected_limits.keys() == actual_limits.keys()

    for nutrient in expected_limits.keys():
        assert np.allclose(actual_limits[nutrient], expected_limits[nutrient])


def test_construct_full_soil_model(
    dummy_carbon_data, fixture_core_components, functional_groups, enzyme_classes
):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.hydrology.constants import HydroConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.soil_model import (
        SoilModel,
        construct_full_soil_model,
    )

    delta_pools = [
        0.123334821,
        0.176185829,
        0.247644774,
        3.42642831e-2,
        3.7894322e-2,
        4.8705495e-3,
        5.67937268e-2,
        7.27579158e-2,
        -4.24905130e-02,
        -1.71526872e-02,
        -8.74103820e-02,
        -6.36922124e-03,
        -6.50731332e-03,
        -6.21196757e-02,
        -1.68034651e-02,
        -2.89162644e-02,
        -5.75698095e-3,
        -3.40601643e-2,
        -2.85852046e-2,
        -5.51963071e-2,
        -5.29546622e-3,
        -3.58039027e-2,
        -3.06921307e-2,
        -2.31935960e-2,
        3.73447584e-4,
        -2.62977207e-2,
        -2.214249e-2,
        5.219897e-3,
        0.0059195,
        0.09042042,
        0.08573325,
        0.02066319,
        -5.44018e-4,
        -2.2835e-4,
        -1.19517e-3,
        -7.21028e-5,
        -8.54122e-4,
        -2.79326e-4,
        -5.9611e-4,
        -1.0930e-4,
        -6.25573478e-4,
        -1.24303545e-4,
        -1.07468399e-4,
        -8.68576041e-5,
        -2.07949478e-4,
        -1.50127545e-4,
        -4.37963990e-5,
        -3.29296041e-5,
        1.56848141e-3,
        7.28019864e-3,
        5.18532940e-3,
        2.42006926e-3,
        -8.93041e-5,
        5.105645e-5,
        9.035108e-5,
        5.212779e-6,
        7.37406e-3,
        -1.87488e-3,
        4.96976e-3,
        -1.53633e-7,
        1.183733e-3,
        1.082948e-2,
        1.343197e-2,
        7.72882e-3,
        1.5830537e-4,
        8.4427055e-3,
        -1.5198907e-4,
        -4.2969999e-4,
        -3.0391349e-3,
        -3.9332566e-3,
        -1.0843233e-3,
        -1.4534738e-3,
        2.08332995e-4,
        1.02602825e-4,
        1.44074015e-4,
        8.15796967e-5,
        6.820884e-6,
        -6.40228e-6,
        -8.6718e-7,
        2.094258e-7,
        0.00225261,
        0.00282114,
        0.00596048,
        0.0014114,
        5.47518e-4,
        -3.2943e-5,
        4.6272e-4,
        3.0915e-4,
        -4.473516e-10,
        -1.222973e-9,
        -6.33411e-10,
        -1.3674e-10,
        -5.050797e-7,
        -2.77311e-6,
        -7.40324e-7,
        -2.187697e-7,
        -1.41330755e-5,
        -2.62731235e-4,
        -8.97710314e-5,
        -2.79283683e-5,
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
        soil_moisture_saturation=HydroConsts.soil_moisture_saturation,
        soil_moisture_residual=HydroConsts.soil_moisture_residual,
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


def test_to_per_area(fixture_soil_model):
    """Test that the SoilModel.to_per_area method converts correctly."""

    # Test that it works for both floats and numpy arrays
    assert np.isclose(fixture_soil_model.to_per_area(40.0), 10.0)
    assert np.allclose(
        fixture_soil_model.to_per_area(np.array([40.0, 100.0, 396.0, 138.8])),
        [10.0, 25.0, 99.0, 34.7],
    )


def test_find_maximum_mycorrhizal_supply(
    dummy_carbon_data, averaged_soil_temp, functional_groups, environmental_factors
):
    """Test that the function to calculate the maximum mycorrhizal supply works."""
    from virtual_ecosystem.models.soil.soil_model import find_maximum_mycorrhizal_supply

    expected_maximum_n = [-0.00017139, 0.001615443, -0.00167385, -0.00079816]
    expected_maximum_p = [-2.844675e-5, -7.276582e-5, -0.000246096, -0.000188804]

    actual_maximum_n, actual_maximum_p = find_maximum_mycorrhizal_supply(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        microbe_pool_size=dummy_carbon_data["soil_c_pool_ectomycorrhiza"],
        soil_temp=averaged_soil_temp,
        microbial_group=functional_groups["ectomycorrhiza"],
        env_factors=environmental_factors,
    )

    assert np.allclose(actual_maximum_n, expected_maximum_n)
    assert np.allclose(actual_maximum_p, expected_maximum_p)
