"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import numpy as np
import pytest
from scipy.optimize import OptimizeResult  # type: ignore
from xarray import DataArray, Dataset

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import InitialisationError
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
    (DEBUG, "soil model: required var 'clay_fraction' checked"),
    (DEBUG, "soil model: required var 'matric_potential' checked"),
    (DEBUG, "soil model: required var 'mean_annual_temperature' checked"),
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
    (INFO, "Adding data array for 'production_of_fungal_fruiting_bodies'"),
)


def test_soil_model_initialization(
    caplog,
    dummy_carbon_data,
    fixture_soil_core_components,
    fixture_soil_constants,
    fixture_hydrology_constants,
    functional_groups,
    enzyme_classes,
):
    """Test `SoilModel` initialization with good data."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_soil_core_components,
        model_constants=fixture_soil_constants,
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation,
        soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual,
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
    fixture_soil_constants,
    fixture_hydrology_constants,
    fixture_core_components,
    functional_groups,
    enzyme_classes,
):
    """Test `SoilModel` initialization with no data."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        empty_data = Data(grid)

        # Try and initialise model with empty data object
        _ = SoilModel(
            data=empty_data,
            core_components=fixture_core_components,
            model_constants=fixture_soil_constants,
            microbial_groups=functional_groups,
            enzyme_classes=enzyme_classes,
            soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation,
            soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual,
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
    fixture_soil_constants,
    fixture_hydrology_constants,
    functional_groups,
    enzyme_classes,
):
    """Test `SoilModel` initialization."""
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
            model_constants=fixture_soil_constants,
            microbial_groups=functional_groups,
            enzyme_classes=enzyme_classes,
            soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation,
            soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual,
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
    dummy_carbon_data,
    fixture_core_components,
    fixture_soil_constants,
    fixture_hydrology_constants,
    functional_groups,
    enzyme_classes,
):
    """Test `SoilModel` initialization."""
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Initialise model with bad data object
    soil_model = SoilModel(
        data=dummy_carbon_data,
        core_components=fixture_core_components,
        model_constants=fixture_soil_constants,
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation,
        soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual,
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
            "[soil.constants]\nsolubility_coefficient_labile_p = 0.05",
            0.05,
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                *POST_SETUP_LOG,
            ),
            id="modified_config_correct",
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

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    # Build the config object and core components
    cfg_strings = [
        "[core]\n[core.timing]\nupdate_interval = '12 hours'",
        "[hydrology]",
        microbial_groups_cfg,
        cfg_string,
    ]

    config_data = ConfigurationLoader(cfg_strings=cfg_strings)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = SoilModel.from_config(
            data=dummy_carbon_data,
            configuration=configuration,
            core_components=core_components,
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

    # And fungal fruiting body production to test that step
    fruiting_body_production = [2.0235824e-6, 2.6018971e-4, 4.7134783e-4, 3.9772191e-4]
    production_rate = [1.01179122e-6, 0.000130094855, 0.000235673915, 0.00019886095475]

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
            new_fungal_fruiting_body_production=DataArray(
                fruiting_body_production, dims="cell_id"
            ),
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

    # Check that the fungal rate is populated based on on values supplied by (mocked)
    # integrator
    assert np.allclose(
        dummy_carbon_data["production_of_fungal_fruiting_bodies"], production_rate
    )


@pytest.mark.parametrize(
    argnames=["mock_output", "raises", "final_pools", "expected_log"],
    argvalues=[
        pytest.param(
            False,
            does_not_raise(),
            Dataset(
                data_vars=dict(
                    soil_c_pool_lmwc=DataArray(
                        [0.11178218, 0.11014931, 0.22560475, 0.02752463], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.51940026, 1.70920791, 4.53482052, 0.53791812], dims="cell_id"
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77597083, 2.29141379, 11.2560934, 0.99661124],
                        dims="cell_id",
                    ),
                    soil_c_pool_saprotrophic_fungi=DataArray(
                        [0.88651637, 8.51906044, 2.20165899, 4.52525138], dims="cell_id"
                    ),
                    soil_c_pool_arbuscular_mycorrhiza=DataArray(
                        [0.64699164, 1.45289622, 3.90575332, 9.01240459], dims="cell_id"
                    ),
                    soil_c_pool_ectomycorrhiza=DataArray(
                        [0.46690783, 1.30203656, 4.18439671, 3.75797075], dims="cell_id"
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.09607891, 0.98273885, 0.68662647, 0.34901083], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.06031107, 0.05107849, 0.12718234, 0.11319268], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02240912, 0.00946262, 0.04945801, 0.00297424], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.035176, 0.01156129, 0.02479475, 0.00450575], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02575926, 0.0056889, 0.00640517, 0.00436779], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00856583, 0.00675207, 0.00378381, 0.00214759], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00154434, 0.0050889, 0.00269656, 0.00456648], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.00709874, 0.00073964, 0.00290216, 0.01428832], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.00582739, 0.0171198, 0.02216189, 0.01114657], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86652863, 0.48604326, 0.33400693, 0.10001777], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00016898, 0.01029679, 0.0002293, 0.00475862], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [-0.00091917, -0.0004919, -0.00063804, 0.0125369],
                        dims="cell_id",
                    ),
                    soil_p_pool_dop=DataArray(
                        [0.00016343, 0.00012056, 0.00025246, 0.00025337], dims="cell_id"
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.19589948e-5, 2.82519250e-4, 1.13848638e-4, 5.71508667e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.00170673, 0.0012422, 0.00309617, 0.00100997], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.0135186, 0.03480958, 0.01990662, 0.00410604], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733095], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [2.52800215e-6, -1.65026722e-4, 3.11246209e-5, 1.77905251e-4],
                        dims="cell_id",
                    ),
                    new_fungal_fruiting_body_production=DataArray(
                        [4.72647034e-6, 1.50518467e-4, 2.79621626e-4, 2.03771721e-4],
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


def test_integrate_with_nans(caplog, fixture_soil_model):
    """Test that integration fails if NaN values are in the input data."""

    # Add Nan value to data and then clean up caplog
    fixture_soil_model.data["pH"] = DataArray([3.3, np.nan, 5.6, 7.9], dims=["cell_id"])
    caplog.clear()

    with pytest.raises(ValueError):
        _ = fixture_soil_model.integrate()

    expected_log = (
        (
            ERROR,
            "Soil model integration cannot proceed because the following variables "
            "have unexpected NaN values: {'pH'}",
        ),
    )

    log_check(caplog, expected_log)


def test_order_independance(
    dummy_carbon_data,
    fixture_soil_model,
    fixture_soil_configuration,
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
        "subcanopy_ammonium_uptake",
        "subcanopy_nitrate_uptake",
        "subcanopy_phosphorus_uptake",
        "animal_pom_consumption_carbon",
        "animal_pom_consumption_nitrogen",
        "animal_pom_consumption_phosphorus",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
        "decay_of_fungal_fruiting_bodies",
        "mean_annual_temperature",
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
        configuration=fixture_soil_configuration,
        core_components=fixture_soil_core_components,
    )

    # Integrate using both data objects
    output = fixture_soil_model.integrate()
    output_reversed = new_soil_model.integrate()

    # Compare each final pool
    for pool_name in pool_names:
        assert np.allclose(output[pool_name], output_reversed[pool_name])


@pytest.mark.parametrize(
    argnames=["unexpected_nans", "variable_name", "input_data"],
    argvalues=[
        pytest.param(
            False,
            "pH",
            DataArray([3.3, 4.3, 5.6, 7.9], dims=["cell_id"]),
            id="no NaNs",
        ),
        pytest.param(
            True,
            "pH",
            DataArray([3.3, np.nan, 5.6, 7.9], dims=["cell_id"]),
            id="NaN",
        ),
    ],
)
def test_check_for_unexpected_nan_value_flat(
    fixture_soil_model, unexpected_nans, variable_name, input_data
):
    """Test unexpected NaN checking values works for variables without layers."""

    fixture_soil_model.data[variable_name] = input_data

    assert unexpected_nans == fixture_soil_model.check_for_unexpected_nan_values(
        var=variable_name
    )


@pytest.mark.parametrize(
    argnames=["unexpected_nans", "variable_name", "layer_name", "input_data"],
    argvalues=[
        pytest.param(
            False,
            "air_temperature",
            "index_surface",
            np.array([3.3, 4.3, 5.6, 7.9]),
            id="surface, good",
        ),
        pytest.param(
            True,
            "air_temperature",
            "index_surface",
            np.array([3.3, np.nan, 5.6, 7.9]),
            id="surface, bad",
        ),
        pytest.param(
            False,
            "soil_temperature",
            "index_all_soil",
            np.array([[3.3, 4.3, 5.6, 7.9], [23.4, 26.1, 24.4, 29.8]]),
            id="soil, good",
        ),
        pytest.param(
            True,
            "soil_temperature",
            "index_all_soil",
            np.array([[3.3, 4.3, 5.6, 7.9], [np.nan, 26.1, 24.4, 29.8]]),
            id="soil, bad",
        ),
    ],
)
def test_check_for_unexpected_nan_value_layered(
    fixture_soil_model,
    fixture_core_components,
    unexpected_nans,
    variable_name,
    layer_name,
    input_data,
):
    """Test unexpected NaN checking values works for variables without layers."""

    lyr_str = fixture_core_components.layer_structure
    fixture_soil_model.data[variable_name] = lyr_str.from_template()
    fixture_soil_model.data[variable_name][getattr(lyr_str, layer_name)] = input_data

    assert unexpected_nans == fixture_soil_model.check_for_unexpected_nan_values(
        var=variable_name
    )


def test_convert_fruiting_body_production_to_rate(fixture_soil_model):
    """Test that conversion of fruiting body production to a rate works."""

    total_production = np.array(
        [2.02358244e-6, 0.00026018971, 0.00047134783, 0.0003977219095]
    )

    expected_rate = [1.01179122e-6, 0.000130094855, 0.000235673915, 0.00019886095475]

    actual_rate = fixture_soil_model.convert_fruiting_body_production_to_rate(
        total_production=total_production
    )

    assert np.allclose(
        actual_rate["production_of_fungal_fruiting_bodies"], expected_rate
    )


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
                "ecto_supply_limit_n": [0.0, 0.00033416, 0.0, 0.0],
                "ecto_supply_limit_p": [0.0, 0.0, 0.0, 0.0],
                "arbuscular_supply_limit_n": [0.0, 0.00037213, 0.0, 0.0],
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
    dummy_carbon_data,
    fixture_core_components,
    fixture_core_constants,
    fixture_soil_constants,
    fixture_hydrology_constants,
    functional_groups,
    enzyme_classes,
):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.models.soil.soil_model import (
        SoilModel,
        construct_full_soil_model,
    )

    delta_pools = [
        0.12423276789810479,
        0.17824690353363165,
        0.24889312020519574,
        0.04461268311156227,
        0.03789432226121193,
        0.0048705495045138604,
        0.05679372684410118,
        0.07275791584131786,
        -0.048350512953900526,
        -0.017251387205083662,
        -0.08839738199974588,
        -0.006818221242128573,
        -0.007054381881973864,
        -0.062406069562776195,
        -0.016970421222328322,
        -0.029782167319928037,
        -0.006099980945117987,
        -0.03448916431713757,
        -0.029482787236391438,
        -0.05578802168235312,
        -0.0062474662218545435,
        -0.03618790265212354,
        -0.031363428955056026,
        -0.02428923629007954,
        -0.007886552416349007,
        -0.03490772073159405,
        -0.02708249030566494,
        -0.001980102593152352,
        0.005919504291669271,
        0.09042041729288817,
        0.08573325241740355,
        0.020663189212488817,
        -0.0005440183248982889,
        -0.00022835022939807217,
        -0.00119517352162211,
        -7.210671588615208e-05,
        -0.000854122324898289,
        -0.0002793262293980722,
        -0.0005961095216221099,
        -0.00010930671588615208,
        -0.0006255788208779072,
        -0.0001249905144817899,
        -0.00011351414512076786,
        -8.99649242347219e-05,
        -0.0002079548208779072,
        -0.0001508145144817899,
        -4.9842145120767855e-05,
        -3.6036924234721896e-05,
        0.0016584234296920736,
        0.0074950304404597795,
        0.005305079816810536,
        0.0034549092570503354,
        -8.935270377987001e-05,
        5.1027852640287704e-05,
        9.028158092281784e-05,
        5.163279168507174e-06,
        0.007374059842314254,
        -0.001874881616071234,
        0.00496976092581884,
        -1.536330357454832e-07,
        0.001183732724349199,
        0.010829477443235935,
        0.01343197389737877,
        0.00772882102985433,
        0.00014092,
        0.00838896,
        -0.00018991,
        -0.00054167,
        -0.00564313,
        -0.00582794,
        -0.00202432,
        -0.00163434,
        0.00022033246159142047,
        0.00013362575874243532,
        0.0001603979712690391,
        0.00021955836334496687,
        6.80438411291209e-06,
        -6.4759821411240326e-06,
        -9.005795710872872e-07,
        1.5832583154028685e-07,
        0.0022526061841475044,
        0.0028211359615132703,
        0.005960476482892584,
        0.001411403170040861,
        0.0005475184888330325,
        -3.2942810279703953e-05,
        0.0004627200836890926,
        0.0003091500688257559,
        -4.47351598173516e-10,
        -1.2229726027397262e-09,
        -6.334109589041096e-10,
        -1.3673972602739725e-10,
        -5.050797153703703e-07,
        -2.773114353703704e-06,
        -7.403238796296297e-07,
        -2.187697222222222e-07,
        -1.71650755e-5,
        -0.000455931235,
        -9.74662048e-5,
        -2.9763896e-5,
        2.023582441855903e-06,
        0.0002601897103642022,
        0.0004308595717737112,
        0.000313705913362231,
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
    delta_pools_ordered["new_fungal_fruiting_body_production"] = np.array([])

    rate_of_change = construct_full_soil_model(
        0.0,
        pools=pools,
        data=dummy_carbon_data,
        no_cells=4,
        layer_structure=fixture_core_components.layer_structure,
        delta_pools_ordered=delta_pools_ordered,
        model_constants=fixture_soil_constants,
        functional_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        core_constants=fixture_core_constants,
        soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation,
        soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual,
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
