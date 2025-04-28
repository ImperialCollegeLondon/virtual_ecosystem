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


def test_soil_model_initialization_no_data(caplog, fixture_core_components):
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
                        [0.10828621, 0.05492146, 0.22333439, 0.02039486], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.51878747, 1.70762064, 4.53007411, 0.53180235], dims="cell_id"
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77888792, 2.29150361, 11.25660944, 0.996833],
                        dims="cell_id",
                    ),
                    soil_c_pool_fungi=DataArray(
                        [0.88678846, 8.51959122, 2.2017577, 4.52566274],
                        dims="cell_id",
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.10019111, 0.98701374, 0.68908282, 0.35261025], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.05703629, 0.04266299, 0.10173659, 0.08044387], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02240909, 0.00946283, 0.04945813, 0.00297422], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.03517596, 0.01156149, 0.02479487, 0.00450574], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02575926, 0.00569118, 0.00638497, 0.00435818], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00856583, 0.00675434, 0.00376362, 0.00213799], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00153904, 0.00386884, 0.0028133, 0.0039439], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.00709876, 0.00073966, 0.00290222, 0.01428835], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.00564613, 0.01665236, 0.02074835, 0.00932728], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86649472, 0.4859555, 0.33374338, 0.09967796], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00056153, 0.01973523, 0.00044013, 0.00524491], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [0.00027728, 0.00049583, -0.0001823, 0.01241204],
                        dims="cell_id",
                    ),
                    soil_p_pool_dop=DataArray(
                        [0.00015938, 0.00015181, 0.00029053, 0.0001802], dims="cell_id"
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.19672137e-5, 2.82555559e-4, 1.13866204e-4, 5.71534407e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.0016797, 0.00117208, 0.00288416, 0.00073708], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.01351353, 0.03479647, 0.01986707, 0.00405508], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733096], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [-3.64956738e-6, -1.18679784e-4, 4.19911975e-6, 1.90983100e-4],
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
        1.17290490e-01,
        6.96565834e-02,
        2.47627966e-01,
        3.42642831e-02,
        3.78943223e-02,
        4.87054950e-03,
        5.67937268e-02,
        7.27579158e-02,
        -4.24905130e-02,
        -1.71526872e-02,
        -8.74103820e-02,
        -6.36843794e-03,
        -6.50731332e-03,
        -6.21196757e-02,
        -1.68034651e-02,
        -2.89127083e-02,
        3.73447584e-04,
        -2.62977207e-02,
        -2.21424903e-02,
        5.21989741e-03,
        -2.29628428e-03,
        6.92559124e-02,
        2.20519888e-02,
        -6.12680088e-02,
        -5.44018325e-04,
        -2.28350229e-04,
        -1.19517352e-03,
        -7.21027994e-05,
        -8.54122325e-04,
        -2.79326229e-04,
        -5.96109522e-04,
        -1.09302799e-04,
        -6.25573478e-04,
        -1.24303545e-04,
        -1.52397478e-04,
        -1.05217109e-04,
        -2.07949478e-04,
        -1.50127545e-04,
        -8.87254781e-05,
        -5.12891092e-05,
        1.60497812e-03,
        5.24091991e-03,
        5.31638796e-03,
        2.42006926e-03,
        -8.93041038e-05,
        5.10564526e-05,
        9.03510809e-05,
        5.21277917e-06,
        6.91762714e-03,
        -3.05068744e-03,
        1.43191295e-03,
        -4.55188686e-03,
        1.18373272e-03,
        1.08294774e-02,
        1.34319739e-02,
        7.72882103e-03,
        9.34367748e-04,
        2.71514869e-02,
        5.28290282e-04,
        1.58922359e-04,
        -3.15054208e-03,
        -3.99710605e-03,
        -1.05165327e-03,
        -9.35738020e-04,
        1.99425697e-04,
        1.39742546e-04,
        1.99748943e-04,
        9.68009312e-05,
        6.82088411e-06,
        -6.40228214e-06,
        -8.67179571e-07,
        2.09425832e-07,
        2.18414128e-03,
        2.64476509e-03,
        5.42979929e-03,
        7.28643187e-04,
        5.47518489e-04,
        -3.29428103e-05,
        4.62720084e-04,
        3.09150069e-04,
        -4.47351598e-10,
        -1.22297260e-09,
        -6.33410959e-10,
        -1.36739726e-10,
        -5.05079715e-07,
        -2.77311435e-06,
        -7.40323880e-07,
        -2.18769722e-07,
        -1.54645996e-05,
        -2.77300640e-04,
        -9.46853893e-05,
        -2.06219796e-06,
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
