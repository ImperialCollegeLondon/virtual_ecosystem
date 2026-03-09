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
    (DEBUG, "soil model: required var 'soil_temperature' checked"),
    (DEBUG, "soil model: required var 'air_temperature' checked"),
)
POST_SETUP_LOG = (
    *REQUIRED_INIT_VAR_LOG,
    (INFO, "Adding data array for 'dissolved_nitrate'"),
    (INFO, "Adding data array for 'dissolved_ammonium'"),
    (INFO, "Adding data array for 'dissolved_phosphorus'"),
    (INFO, "Adding data array for 'ectomycorrhizal_n_supply'"),
    (INFO, "Adding data array for 'ectomycorrhizal_p_supply'"),
    (INFO, "Adding data array for 'arbuscular_mycorrhizal_n_supply'"),
    (INFO, "Adding data array for 'arbuscular_mycorrhizal_p_supply'"),
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
    end_bacteria = [5.8, 2.3, 11.3, 1.0]
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

    # Do the same for the mycorrhizal nutrient supplies
    new_amf_n_supply = [2.07e-5, 3.12e-5, 3.57e-6, 6.98e-5]
    new_emf_n_supply = [3.07e-5, 4.20e-5, 4.02e-6, 2.98e-5]
    new_amf_p_supply = [1.57e-6, 5.07e-5, 2.13e-6, 1.81e-6]
    new_emf_p_supply = [1.78e-6, 5.64e-5, 1.07e-6, 9.90e-7]
    arbuscular_mycorrhizal_n_supply = [0.0419175, 0.06318, 0.00722925, 0.141345]
    arbuscular_mycorrhizal_p_supply = [0.00317925, 0.1026675, 0.00431325, 0.00366525]
    ectomycorrhizal_n_supply = [0.0621675, 0.08505, 0.0081405, 0.060345]
    ectomycorrhizal_p_supply = [0.0036045, 0.11421, 0.00216675, 0.00200475]

    mock_integrate = mocker.patch.object(fixture_soil_model, "integrate")

    mock_integrate.return_value = Dataset(
        data_vars=dict(
            soil_c_pool_lmwc=DataArray(end_lmwc, dims="cell_id"),
            soil_c_pool_maom=DataArray(end_maom, dims="cell_id"),
            soil_c_pool_bacteria=DataArray(end_bacteria, dims="cell_id"),
            soil_c_pool_pom=DataArray(end_pom, dims="cell_id"),
            soil_c_pool_necromass=DataArray(end_necromass, dims="cell_id"),
            soil_n_pool_nitrate=DataArray(end_nitrate, dims="cell_id"),
            soil_n_pool_ammonium=DataArray(end_ammonium, dims="cell_id"),
            soil_p_pool_labile=DataArray(end_phosphorus, dims="cell_id"),
            new_fungal_fruiting_body_production=DataArray(
                fruiting_body_production, dims="cell_id"
            ),
            new_amf_n_supply=DataArray(new_amf_n_supply, dims="cell_id"),
            new_emf_n_supply=DataArray(new_emf_n_supply, dims="cell_id"),
            new_amf_p_supply=DataArray(new_amf_p_supply, dims="cell_id"),
            new_emf_p_supply=DataArray(new_emf_p_supply, dims="cell_id"),
        )
    )

    fixture_soil_model.update(time_index=0)

    # Check that integrator is called once (and once only)
    mock_integrate.assert_called_once()

    # Check that data fixture has been updated correctly
    assert np.allclose(dummy_carbon_data["soil_c_pool_lmwc"], end_lmwc)
    assert np.allclose(dummy_carbon_data["soil_c_pool_maom"], end_maom)
    assert np.allclose(dummy_carbon_data["soil_c_pool_bacteria"], end_bacteria)
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

    # Check that nutrient supplies are populated based on values supplied by (mocked)
    # integrator
    assert np.allclose(
        dummy_carbon_data["arbuscular_mycorrhizal_n_supply"],
        arbuscular_mycorrhizal_n_supply,
    )
    assert np.allclose(
        dummy_carbon_data["arbuscular_mycorrhizal_p_supply"],
        arbuscular_mycorrhizal_p_supply,
    )
    assert np.allclose(
        dummy_carbon_data["ectomycorrhizal_n_supply"], ectomycorrhizal_n_supply
    )
    assert np.allclose(
        dummy_carbon_data["ectomycorrhizal_p_supply"], ectomycorrhizal_p_supply
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
                        [0.12324074, 0.40624134, 0.23074348, 0.04374807], dims="cell_id"
                    ),
                    soil_c_pool_maom=DataArray(
                        [2.51940338, 1.70928575, 4.53482197, 0.53792231], dims="cell_id"
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.7759712, 2.29140027, 11.25613092, 0.99661487],
                        dims="cell_id",
                    ),
                    soil_c_pool_saprotrophic_fungi=DataArray(
                        [0.88651651, 8.51894111, 2.20167628, 4.52533503], dims="cell_id"
                    ),
                    soil_c_pool_arbuscular_mycorrhiza=DataArray(
                        [0.6475252, 1.4647442, 3.90588435, 9.01256566], dims="cell_id"
                    ),
                    soil_c_pool_ectomycorrhiza=DataArray(
                        [0.467854, 1.31523705, 4.18439291, 3.75807565], dims="cell_id"
                    ),
                    soil_c_pool_pom=DataArray(
                        [0.09607891, 0.98273313, 0.68662648, 0.3490108], dims="cell_id"
                    ),
                    soil_c_pool_necromass=DataArray(
                        [0.06031341, 0.05111967, 0.12718265, 0.11319312], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02240913, 0.00946256, 0.0494582, 0.00297425], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.035176, 0.01156122, 0.02479494, 0.00450577], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02576026, 0.00569679, 0.00640518, 0.0043703], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00856682, 0.00675996, 0.00378383, 0.0021501], dims="cell_id"
                    ),
                    soil_n_pool_don=DataArray(
                        [0.00156622, 0.00439449, 0.00268103, 0.00556602], dims="cell_id"
                    ),
                    soil_n_pool_particulate=DataArray(
                        [0.00709874, 0.00073964, 0.00290216, 0.01428832], dims="cell_id"
                    ),
                    soil_n_pool_necromass=DataArray(
                        [0.00582752, 0.01712208, 0.02216192, 0.0111466], dims="cell_id"
                    ),
                    soil_n_pool_maom=DataArray(
                        [0.86652865, 0.48604307, 0.33400693, 0.10001802], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00016957, 0.01008935, 0.0002286, 0.00487271], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [-0.00093066, -0.00049545, -0.00063842, 0.01256253],
                        dims="cell_id",
                    ),
                    soil_p_pool_dop=DataArray(
                        [0.00016547, 0.00014088, 0.00027078, 0.00033433], dims="cell_id"
                    ),
                    soil_p_pool_particulate=DataArray(
                        [3.19589918e-5, 2.82517608e-4, 1.13848640e-4, 5.71508620e-4],
                        dims="cell_id",
                    ),
                    soil_p_pool_necromass=DataArray(
                        [0.00170675, 0.00124254, 0.00309618, 0.00100997], dims="cell_id"
                    ),
                    soil_p_pool_maom=DataArray(
                        [0.0135186, 0.0348096, 0.01990663, 0.00410606], dims="cell_id"
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733095], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [2.40213931e-6, -1.65094948e-4, 3.11266283e-5, 1.76524136e-4],
                        dims="cell_id",
                    ),
                    new_fungal_fruiting_body_production=DataArray(
                        [1.73450986e-5, 2.33647556e-4, 2.94101986e-4, 2.38779611e-4],
                        dims="cell_id",
                    ),
                    new_amf_n_supply=DataArray(
                        [1.24825719e-6, 8.59052210e-6, 2.50358419e-5, 2.53364588e-5],
                        dims="cell_id",
                    ),
                    new_amf_p_supply=DataArray(
                        [1.84065044e-7, 1.26673801e-6, 3.69172584e-6, 3.73605410e-6],
                        dims="cell_id",
                    ),
                    new_emf_n_supply=DataArray(
                        [8.94317870e-7, 7.64686838e-6, 1.82871956e-5, 1.04737865e-5],
                        dims="cell_id",
                    ),
                    new_emf_p_supply=DataArray(
                        [1.33028451e-7, 1.13746028e-6, 2.72019310e-6, 1.55796014e-6],
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
        "litter_mineralisation_rate_cnp",
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "subcanopy_ammonium_uptake",
        "subcanopy_nitrate_uptake",
        "subcanopy_phosphorus_uptake",
        "animal_pom_consumption_cnp",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
        "decay_of_fungal_fruiting_bodies",
        "decomposed_excrement_cnp",
        "decomposed_carcasses_cnp",
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


def test_convert_mycorrhizal_supplies_to_mass(fixture_soil_model):
    """Test that mycorrhizal supplies are correctly converted to mass units."""

    supplies = {
        "new_amf_n_supply": DataArray([2.07e-5, 3.12e-5, 3.57e-6, 6.98e-5]),
        "new_emf_n_supply": DataArray([3.07e-5, 4.20e-5, 4.02e-6, 2.98e-5]),
        "new_amf_p_supply": DataArray([1.57e-6, 5.07e-5, 2.13e-6, 1.81e-6]),
        "new_emf_p_supply": DataArray([1.78e-6, 5.64e-5, 1.07e-6, 9.90e-7]),
    }

    expected_masses = {
        "arbuscular_mycorrhizal_n_supply": [0.0419175, 0.06318, 0.00722925, 0.141345],
        "arbuscular_mycorrhizal_p_supply": [
            0.00317925,
            0.1026675,
            0.00431325,
            0.00366525,
        ],
        "ectomycorrhizal_n_supply": [0.0621675, 0.08505, 0.0081405, 0.060345],
        "ectomycorrhizal_p_supply": [0.0036045, 0.11421, 0.00216675, 0.00200475],
    }

    actual_masses = fixture_soil_model.convert_mycorrhizal_supplies_to_mass(supplies)

    assert expected_masses.keys() == actual_masses.keys()

    for nutrient in expected_masses.keys():
        assert np.allclose(actual_masses[nutrient], expected_masses[nutrient])


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


def test_calculate_initial_symbiotic_supply(fixture_soil_model):
    """Test that the function to calculate the symbiotic supply limits works."""

    expected_supply = {
        "arbuscular_mycorrhizal_n_supply": [
            0.00564199467525,
            0.4897515879,
            0.02949683596875,
            0.26289689265,
        ],
        "arbuscular_mycorrhizal_p_supply": [
            7.955705840625001e-5,
            0.002408107127625,
            0.005366038093875,
            0.005891451620625,
        ],
        "ectomycorrhizal_n_supply": [
            0.004079596154625,
            0.4397769358875,
            0.0316037527875,
            0.1096373100375,
        ],
        "ectomycorrhizal_p_supply": [
            5.752587306375e-5,
            0.002162381902875,
            0.005749326529875,
            0.002456943870375,
        ],
    }

    actual_supply = fixture_soil_model.calculate_initial_symbiotic_supply()

    assert expected_supply.keys() == actual_supply.keys()

    for nutrient in expected_supply.keys():
        assert np.allclose(actual_supply[nutrient], expected_supply[nutrient])


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
        0.14736524,
        0.76933205,
        0.26335729,
        0.07947176,
        3.7894322e-2,
        4.8705495e-3,
        5.67937268e-2,
        7.27579158e-2,
        -0.048350513,
        -0.0172513872,
        -0.088397382,
        -0.00681822124,
        -0.00705438,
        -0.06240607,
        -0.01697042,
        -0.02978217,
        -0.00507858,
        -0.01059603,
        -0.02956509,
        -0.05564099,
        -0.00437839,
        -0.00959643,
        -0.03157447,
        -0.02414548,
        -0.007886552416,
        -0.0349077207,
        -0.02708249,
        -0.001980103,
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
        -6.25152703e-04,
        -1.08972871e-04,
        -1.17734954e-04,
        -8.70898203e-05,
        -2.07528703e-04,
        -1.34796871e-04,
        -5.40629537e-05,
        -3.31618203e-05,
        0.00169496,
        0.0057789,
        0.00535622,
        0.00547371,
        -8.93527e-5,
        5.102785e-5,
        9.028158e-5,
        5.163279e-6,
        7.37406e-3,
        -1.87488e-3,
        4.96976e-3,
        -1.53633e-7,
        1.183733e-3,
        1.082948e-2,
        1.343197e-2,
        7.72882e-3,
        0.00014578,
        0.00824912,
        -0.00018991,
        -0.00027484,
        -0.00562716,
        -0.00584054,
        -0.00202432,
        -0.00157849,
        0.00022614,
        0.00016408,
        0.00021213,
        0.00038847,
        6.804384e-6,
        -6.47598e-6,
        -9.0058e-7,
        1.583258e-7,
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
        -1.76159741e-05,
        -4.55931235e-04,
        -9.74662048e-05,
        -2.97638960e-05,
        7.40554437e-06,
        4.38693546e-04,
        4.01525064e-04,
        3.42784354e-04,
        5.32864078e-7,
        1.612922608e-5,
        2.91326774e-5,
        3.94602692e-5,
        7.85748726e-8,
        2.3783774e-6,
        4.2958355e-6,
        5.81871764e-6,
        3.81957958e-7,
        1.435769562e-5,
        3.1213583e-5,
        1.63135162e-5,
        5.6815677e-8,
        2.13568584e-6,
        4.64297396e-6,
        2.42661124e-6,
    ]

    # make pools
    pools = np.concatenate(
        [
            dummy_carbon_data[name].to_numpy()
            for name in dummy_carbon_data.data.keys()
            if name in SoilModel.vars_updated
        ]
    )

    # List of variables that are added to the data object
    refreshed_variables = [
        "new_fungal_fruiting_body_production",
        "new_amf_n_supply",
        "new_amf_p_supply",
        "new_emf_n_supply",
        "new_emf_p_supply",
    ]
    # Find and store order of pools
    delta_pools_ordered = {
        **{
            name: np.array([])
            for name in map(str, dummy_carbon_data.data.keys())
            if name in SoilModel.vars_updated
        },
        **{name: np.array([]) for name in refreshed_variables},
    }

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


def test_to_total_mass(fixture_soil_model):
    """Test that the SoilModel.to_total_mass method converts correctly."""

    # Test that it works for both floats and numpy arrays
    assert np.isclose(fixture_soil_model.to_total_mass(40.0), 40500.0)
    assert np.allclose(
        fixture_soil_model.to_total_mass(np.array([40.0, 100.0, 396.0, 138.8])),
        [40500.0, 101250.0, 400950.0, 140535.0],
    )


def test_estimate_past_mycorrhizal_supply(
    dummy_carbon_data, averaged_soil_temp, functional_groups, environmental_factors
):
    """Test that the function to calculate the maximum mycorrhizal supply works."""
    from virtual_ecosystem.models.soil.soil_model import (
        estimate_past_mycorrhizal_supply,
    )

    expected_n_supply = [4.02923076e-6, 0.000434347592, 3.1213583e-5, 0.0001082837634]
    expected_p_supply = [5.6815677e-8, 2.13568584e-6, 5.67834718e-6, 2.42661124e-6]

    actual_n_supply, actual_p_supply = estimate_past_mycorrhizal_supply(
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

    assert np.allclose(actual_n_supply, expected_n_supply)
    assert np.allclose(actual_p_supply, expected_p_supply)
