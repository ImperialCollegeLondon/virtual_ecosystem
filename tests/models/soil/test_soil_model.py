"""Test module for soil_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import numpy as np
import pytest
from scipy.optimize import OptimizeResult  # type: ignore
from xarray import DataArray, Dataset

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.models.soil.soil_model import IntegrationError

# Shared log entries from model initialisation
REQUIRED_INIT_VAR_LOG = ((INFO, "soil model: required initial data variables checked"),)
POST_SETUP_LOG = (
    *REQUIRED_INIT_VAR_LOG,
    (INFO, "Adding data array for 'dissolved_nitrate'"),
    (INFO, "Adding data array for 'dissolved_ammonium'"),
    (INFO, "Adding data array for 'dissolved_phosphorus'"),
    (INFO, "Adding data array for 'ectomycorrhizal_n_supply'"),
    (INFO, "Adding data array for 'ectomycorrhizal_p_supply'"),
    (INFO, "Adding data array for 'arbuscular_mycorrhizal_n_supply'"),
    (INFO, "Adding data array for 'arbuscular_mycorrhizal_p_supply'"),
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

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (
                ERROR,
                "soil model: input data is missing required initialisation variables:",
            ),
            (ERROR, "soil model: Problems with initial model data: check log."),
        ),
        match_message_start=True,
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
        dummy_carbon_data["soil_cnp_pool_lmwc"].loc[dict(element="C")] = DataArray(
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
            *POST_SETUP_LOG,
            (ERROR, "Initial soil pools contain at least one negative value!"),
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
    dummy_carbon_data["soil_cnp_pool_necromass"].loc[dict(element="C")] = DataArray(
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
        "[core.grid]\ncell_nx = 2\ncell_ny=2\n"
        "[core.timing]\nupdate_interval = '12 hours'",
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
    # As the test is mocked, I'm only really test that the update function calls the
    # integrator, and can handle both types of data arrays I use (triplet + non-triplet)
    # So many variables are missing, and only one triplet variable is used
    end_lmwc = DataArray(
        np.stack(
            [
                [0.04980117, 0.01999411, 0.09992829, 0.00499986],
                [0.04159959, 0.016532336, 0.094526484, 0.002470021],
                [0.037097363, 0.013122614, 0.011499752, 0.001997491],
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(element=np.array(["C", "N", "P"])),
    )
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

    # Do the same for the mycorrhizal nutrient supplies
    new_amf_n_supply = [2.07e-5, 3.12e-5, 3.57e-6, 6.98e-5]
    new_emf_n_supply = [3.07e-5, 4.20e-5, 4.02e-6, 2.98e-5]
    new_amf_p_supply = [1.57e-6, 5.07e-5, 2.13e-6, 1.81e-6]
    new_emf_p_supply = [1.78e-6, 5.64e-5, 1.07e-6, 9.90e-7]
    arbuscular_mycorrhizal_n_supply = [0.0419175, 0.06318, 0.00722925, 0.141345]
    arbuscular_mycorrhizal_p_supply = [0.00317925, 0.1026675, 0.00431325, 0.00366525]
    ectomycorrhizal_n_supply = [0.0621675, 0.08505, 0.0081405, 0.060345]
    ectomycorrhizal_p_supply = [0.0036045, 0.11421, 0.00216675, 0.00200475]
    cnp_fungal_fruiting_body_production = DataArray(
        np.stack(
            [
                [0.04980117, 0.01999411, 0.09992829, 0.00499986],
                [0.04159959, 0.016532336, 0.094526484, 0.002470021],
                [0.037097363, 0.013122614, 0.011499752, 0.001997491],
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(element=np.array(["C", "N", "P"])),
    )

    mock_integrate = mocker.patch.object(fixture_soil_model, "integrate")

    mock_integrate.return_value = Dataset(
        data_vars=dict(
            soil_cnp_pool_lmwc=end_lmwc,
            soil_cnp_pool_maom=DataArray(end_maom, dims="cell_id"),
            soil_c_pool_bacteria=DataArray(end_bacteria, dims="cell_id"),
            soil_cnp_pool_pom=DataArray(end_pom, dims="cell_id"),
            soil_cnp_pool_necromass=DataArray(end_necromass, dims="cell_id"),
            soil_n_pool_nitrate=DataArray(end_nitrate, dims="cell_id"),
            soil_n_pool_ammonium=DataArray(end_ammonium, dims="cell_id"),
            soil_p_pool_labile=DataArray(end_phosphorus, dims="cell_id"),
            new_amf_n_supply=DataArray(new_amf_n_supply, dims="cell_id"),
            new_emf_n_supply=DataArray(new_emf_n_supply, dims="cell_id"),
            new_amf_p_supply=DataArray(new_amf_p_supply, dims="cell_id"),
            new_emf_p_supply=DataArray(new_emf_p_supply, dims="cell_id"),
            cnp_fungal_fruiting_body_production=cnp_fungal_fruiting_body_production,
        )
    )

    fixture_soil_model.update(time_index=0)

    # Check that integrator is called once (and once only)
    mock_integrate.assert_called_once()

    # Check that data fixture has been updated correctly
    assert np.allclose(dummy_carbon_data["soil_cnp_pool_lmwc"], end_lmwc)
    assert np.allclose(dummy_carbon_data["soil_cnp_pool_maom"], end_maom)
    assert np.allclose(dummy_carbon_data["soil_c_pool_bacteria"], end_bacteria)
    assert np.allclose(dummy_carbon_data["soil_cnp_pool_pom"], end_pom)
    assert np.allclose(dummy_carbon_data["soil_cnp_pool_necromass"], end_necromass)

    # Check that dissolved values are populated based on values supplied by (mocked)
    # integrator
    assert np.allclose(dummy_carbon_data["dissolved_nitrate"], dissolved_nitrate)
    assert np.allclose(dummy_carbon_data["dissolved_ammonium"], dissolved_ammonium)
    assert np.allclose(dummy_carbon_data["dissolved_phosphorus"], dissolved_phosphorus)

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
    # Check that fungal fruiting bodies update correctly based on what the integrator
    # returns
    fungal_fruiting_body_final = DataArray(
        np.stack(
            [
                [0.23955402809, 0.087603390365, 0.4107861413241, 0.039394536436],
                [0.1679019020381, 0.0681492941357, 0.394461176307, 0.0166380784314],
                [0.1489216006137, 0.0525304875585, 0.0461457175544, 0.0081695945706],
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(element=np.array(["C", "N", "P"])),
    )
    assert np.allclose(
        dummy_carbon_data["fungal_fruiting_bodies_cnp"], fungal_fruiting_body_final
    )


@pytest.mark.parametrize(
    argnames=["mock_output", "raises", "final_pools", "expected_log"],
    argvalues=[
        pytest.param(
            False,
            does_not_raise(),
            Dataset(
                data_vars=dict(
                    soil_cnp_pool_maom=DataArray(
                        data=np.stack(
                            [
                                [2.51940387, 1.70928337, 4.53482183, 0.53793535],
                                [0.86652874, 0.4860426, 0.33400704, 0.10002057],
                                [0.0135187, 0.03480961, 0.01990663, 0.00410703],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_cnp_pool_lmwc=DataArray(
                        data=np.stack(
                            [
                                [0.12485747, 0.40077089, 0.23007142, 0.09513328],
                                [0.00195816, 0.00422618, 0.00310929, 0.01565043],
                                [0.000526, 0.00028609, 0.00029134, 0.00416462],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_cnp_pool_pom=DataArray(
                        data=np.stack(
                            [
                                [0.09607888, 0.98272334, 0.68662643, 0.34901073],
                                [0.00709873, 0.00073963, 0.00290216, 0.01428832],
                                [3.195898e-5, 2.825148e-4, 1.138486e-4, 5.715085e-4],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_cnp_pool_necromass=DataArray(
                        data=np.stack(
                            [
                                [0.06031411, 0.05112291, 0.12718296, 0.11319489],
                                [0.00582761, 0.01712246, 0.02216194, 0.01114674],
                                [0.00170678, 0.00124261, 0.00309618, 0.00101],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77624811, 2.29155609, 11.25617531, 0.99670336],
                        dims="cell_id",
                    ),
                    soil_c_pool_saprotrophic_fungi=DataArray(
                        [0.88659015, 8.5202008, 2.20167979, 4.52557488], dims="cell_id"
                    ),
                    soil_c_pool_arbuscular_mycorrhiza=DataArray(
                        [0.64765054, 1.46532161, 3.90605506, 9.01330621], dims="cell_id"
                    ),
                    soil_c_pool_ectomycorrhiza=DataArray(
                        [0.46793618, 1.31570236, 4.18439622, 3.75823478], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02241051, 0.00946333, 0.04945842, 0.0029747], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.03517738, 0.011562, 0.02479516, 0.00450621], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02576226, 0.00571235, 0.00640526, 0.00437466], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00856883, 0.00677552, 0.00378391, 0.00215446], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00016685, 0.01003131, 0.00023277, 0.0048897], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [-0.0009318, -0.00049214, -0.00063802, 0.01255959],
                        dims="cell_id",
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733095], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [2.57911698e-6, -1.65141657e-4, 3.11223620e-5, 2.12518261e-4],
                        dims="cell_id",
                    ),
                    cnp_fungal_fruiting_body_production=DataArray(
                        data=np.stack(
                            [
                                [4.550128e-5, 4.642166e-4, 3.118837e-4, 3.529220e-4],
                                [3.718613e-6, 5.180961e-5, 2.122754e-5, 2.449893e-5],
                                [5.810895e-7, 8.280525e-6, 3.260449e-6, 3.770555e-6],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    new_amf_n_supply=DataArray(
                        [3.08131365e-6, 1.68424350e-5, 2.59507315e-5, 3.49527576e-5],
                        dims="cell_id",
                    ),
                    new_amf_p_supply=DataArray(
                        [4.62197047e-7, 2.52636524e-6, 3.89260973e-6, 5.24291364e-6],
                        dims="cell_id",
                    ),
                    new_emf_n_supply=DataArray(
                        [2.22276162e-6, 1.50088390e-5, 1.72096104e-5, 1.25059027e-5],
                        dims="cell_id",
                    ),
                    new_emf_p_supply=DataArray(
                        [3.35956156e-7, 2.26848971e-6, 2.60112218e-6, 1.89018695e-6],
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
    mocker,
    caplog,
    fixture_soil_model,
    fungal_fruiting_body_decay_rate,
    mock_output,
    raises,
    final_pools,
    expected_log,
):
    """Test that function to integrate the soil model works as expected."""

    if mock_output:
        mock_integrate = mocker.patch(
            "virtual_ecosystem.models.soil.soil_model.solve_ivp"
        )
        mock_integrate.return_value = mock_output

    with raises:
        new_pools = fixture_soil_model.integrate(
            fungal_fruit_decay_rate=fungal_fruiting_body_decay_rate
        )

        # Check returned pools matched (mocked) integrator output
        assert set(new_pools.keys()) == set(final_pools.keys())

        for key in new_pools.keys():
            assert np.allclose(new_pools[key], final_pools[key])

    # Check that integrator is called once (and once only)
    if mock_output:
        mock_integrate.assert_called_once()

    log_check(caplog, expected_log)


def test_integrate_with_nans(
    caplog, fixture_soil_model, fungal_fruiting_body_decay_rate
):
    """Test that integration fails if NaN values are in the input data."""

    # Add Nan value to data and then clean up caplog
    fixture_soil_model.data["pH"] = DataArray([3.3, np.nan, 5.6, 7.9], dims=["cell_id"])
    caplog.clear()

    with pytest.raises(ValueError):
        _ = fixture_soil_model.integrate(
            fungal_fruit_decay_rate=fungal_fruiting_body_decay_rate
        )

    expected_log = (
        (
            ERROR,
            "Soil model integration cannot proceed because the following variables "
            "contain invalid values (e.g. NaN or Inf): {'pH'}",
        ),
    )

    log_check(caplog, expected_log)


def test_order_independance(
    dummy_carbon_data,
    fixture_soil_model,
    fixture_soil_configuration,
    fixture_soil_core_components,
    fungal_fruiting_body_decay_rate,
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
        "fungal_fruiting_bodies_consumed_cnp",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
        "decomposed_excrement_cnp",
        "decomposed_carcasses_cnp",
        "fallen_fruit_decay_cnp",
    ]
    for not_pool in not_pools:
        new_data[not_pool] = dummy_carbon_data[not_pool]

    # Some pools are not updated by the integration (everything populated by the soil
    # init + the fungal fruiting bodies) so shouldn't be checked
    var_updated_outside_integration = ["fungal_fruiting_bodies_cnp"] + [
        name
        for name in map(str, dummy_carbon_data.data.keys())
        if name in SoilModel.vars_populated_by_init
    ]

    # Then extract soil carbon pool names from the fixture (in order)
    pool_names = [
        name
        for name in dummy_carbon_data.data.keys()
        if name in SoilModel.vars_updated
        and name not in var_updated_outside_integration
    ]

    # Add pool values from object in reversed order
    for pool_name in reversed(pool_names):
        new_data[pool_name] = dummy_carbon_data[pool_name]

    # fungal fruiting bodies need to be added in separately as they are not included in
    # the (checked) pool names
    new_data["fungal_fruiting_bodies_cnp"] = dummy_carbon_data[
        "fungal_fruiting_bodies_cnp"
    ]

    # Use this new data to make a new soil model object
    new_soil_model = SoilModel.from_config(
        data=new_data,
        configuration=fixture_soil_configuration,
        core_components=fixture_soil_core_components,
    )

    # Integrate using both data objects
    output = fixture_soil_model.integrate(
        fungal_fruit_decay_rate=fungal_fruiting_body_decay_rate
    )
    output_reversed = new_soil_model.integrate(
        fungal_fruit_decay_rate=fungal_fruiting_body_decay_rate
    )

    # Compare each final pool
    for pool_name in pool_names:
        assert np.allclose(output[pool_name], output_reversed[pool_name])


@pytest.mark.parametrize(
    argnames=["invalid_values", "variable_name", "input_data"],
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
        pytest.param(
            True,
            "pH",
            DataArray([3.3, np.inf, 5.6, 7.9], dims=["cell_id"]),
            id="Inf",
        ),
        pytest.param(
            True,
            "pH",
            DataArray([3.3, -np.inf, 5.6, 7.9], dims=["cell_id"]),
            id="negative inf",
        ),
    ],
)
def test_check_for_invalid_input_values_flat(
    fixture_soil_model, invalid_values, variable_name, input_data
):
    """Test unexpected NaN checking values works for variables without layers."""

    fixture_soil_model.data[variable_name] = input_data

    assert invalid_values == fixture_soil_model.check_for_invalid_input_values(
        var=variable_name
    )


@pytest.mark.parametrize(
    argnames=["invalid_values", "variable_name", "layer_name", "input_data"],
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
            True,
            "air_temperature",
            "index_surface",
            np.array([3.3, np.inf, 5.6, 7.9]),
            id="surface, inf",
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
            id="soil, nan",
        ),
        pytest.param(
            True,
            "soil_temperature",
            "index_all_soil",
            np.array([[3.3, 4.3, 5.6, 7.9], [np.inf, 26.1, 24.4, 29.8]]),
            id="soil, inf",
        ),
    ],
)
def test_check_for_invalid_input_values_layered(
    fixture_soil_model,
    fixture_core_components,
    invalid_values,
    variable_name,
    layer_name,
    input_data,
):
    """Test unexpected NaN checking values works for variables without layers."""

    lyr_str = fixture_core_components.layer_structure
    fixture_soil_model.data[variable_name] = lyr_str.from_template()
    fixture_soil_model.data[variable_name][getattr(lyr_str, layer_name)] = input_data

    assert invalid_values == fixture_soil_model.check_for_invalid_input_values(
        var=variable_name
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


def test_calculate_fungal_fruiting_body_decay(fixture_soil_model, dummy_carbon_data):
    """Test that the function to calculate fungal fruit decay works correctly."""

    post_consumption_fungal_fruit = (
        dummy_carbon_data["fungal_fruiting_bodies_cnp"]
        - dummy_carbon_data["fungal_fruiting_bodies_consumed_cnp"]
    )

    expected_decay = DataArray(
        data=np.stack(
            [
                [2.80651910e-4, 5.30496350e-5, 7.70186759e-5, 1.34903564e-4],
                [1.04579619e-5, 1.40498643e-5, 1.13759693e-4, 4.70055686e-5],
                [3.70138632e-6, 2.78441509e-7, 1.02044565e-6, 1.24942943e-6],
            ],
            axis=1,
        ),
        coords={"cell_id": dummy_carbon_data["cell_id"], "element": ["C", "N", "P"]},
    )

    actual_decay = fixture_soil_model.calculate_fungal_fruiting_body_decay(
        fungal_fruit_cnp=post_consumption_fungal_fruit
    )

    assert np.allclose(actual_decay, expected_decay)


def test_construct_full_soil_model(
    dummy_carbon_data,
    fixture_core_components,
    fixture_core_constants,
    fixture_soil_constants,
    fixture_soil_model,
    fixture_hydrology_constants,
    functional_groups,
    enzyme_classes,
    fungal_fruiting_body_decay_rate,
):
    """Test that the function that creates the object to integrate exists and works."""
    from virtual_ecosystem.models.soil.soil_model import (
        construct_full_soil_model,
    )

    delta_pools = [
        0.15312579528,
        0.77032795708,
        0.26251882941,
        0.18714513851,
        3.7894322e-2,
        4.8705495e-3,
        5.67937268e-2,
        7.27579158e-2,
        -0.007886552416,
        -0.0349077207,
        -0.02708249,
        -0.001980103,
        0.0059195,
        0.09042042,
        0.08573325,
        0.02066319,
        0.0026366837,
        0.0060125609,
        0.0062434815,
        0.0259165145,
        1.183733e-3,
        1.082948e-2,
        1.343197e-2,
        7.72882e-3,
        -8.93527e-5,
        5.102785e-5,
        9.028158e-5,
        5.163279e-6,
        7.37406e-3,
        -1.87488e-3,
        4.96976e-3,
        -1.53633e-7,
        0.00099175109,
        0.00057127753,
        0.00026006357,
        0.00816849544,
        5.47518e-4,
        -3.2943e-5,
        4.6272e-4,
        3.0915e-4,
        6.804384e-6,
        -6.47598e-6,
        -9.0058e-7,
        1.583258e-7,
        0.00225261,
        0.00282114,
        0.00596048,
        0.0014114,
        -0.048350513,
        -0.0172513872,
        -0.088397382,
        -0.00681822124,
        -7.05523264e-3,
        -6.25154586e-2,
        -1.69860782e-2,
        -2.97821673e-2,
        -5.07680437e-3,
        -1.05423533e-2,
        -2.94358128e-2,
        -5.55096609e-2,
        -4.37734328e-3,
        -9.55704432e-3,
        -3.14594275e-2,
        -2.41007280e-02,
        -5.44018e-4,
        -2.2835e-4,
        -1.19517e-3,
        -7.21028e-5,
        -8.54122e-4,
        -2.79326e-4,
        -5.9611e-4,
        -1.0930e-4,
        -6.25136000e-4,
        -1.08732063e-4,
        -1.15512400e-4,
        -8.61947588e-5,
        -2.07512000e-4,
        -1.34556063e-4,
        -5.18403999e-5,
        -3.22667588e-5,
        1.45780297e-4,
        8.23956439e-3,
        -1.89909067e-4,
        -2.71537385e-4,
        -5.62710718e-3,
        -5.84164570e-3,
        -2.02432331e-3,
        -1.57775072e-3,
        -4.473516e-10,
        -1.222973e-9,
        -6.33411e-10,
        -1.3674e-10,
        -5.050797e-7,
        -2.77311e-6,
        -7.40324e-7,
        -2.187697e-7,
        -1.76159741e-5,
        -4.55931235e-4,
        -9.76110314e-5,
        -2.98923683e-5,
        7.60259952e-6,
        4.37061529e-4,
        4.24391470e-4,
        3.60392817e-4,
        6.12904e-7,
        4.87802e-5,
        2.83040e-5,
        2.11042e-5,
        9.5663e-8,
        7.7964e-6,
        4.3381e-6,
        3.1868e-6,
        5.23832484e-7,
        1.58558494e-5,
        2.91326775e-5,
        3.87914510e-5,
        7.85748725e-8,
        2.37837741e-6,
        4.36990162e-6,
        5.81871765e-6,
        3.75905320e-7,
        1.41301787e-5,
        3.12135830e-5,
        1.60550066e-5,
        5.68156771e-8,
        2.13568583e-6,
        4.71773278e-6,
        2.42661123e-06,
    ]
    elements = {"C": "carbon", "N": "nitrogen", "P": "phosphorus"}

    var_updated_outside_integration = ["fungal_fruiting_bodies_cnp"] + [
        name
        for name in map(str, dummy_carbon_data.data.keys())
        if name in fixture_soil_model.vars_populated_by_init
    ]

    # Find all variables that get updated, and then subset this into singlets and
    # biomass triplets
    updated_variable_names = [
        name
        for name in map(str, dummy_carbon_data.data.keys())
        if name in fixture_soil_model.vars_updated
        and name not in var_updated_outside_integration
    ]
    updated_biomass_triplets = [
        name for name in updated_variable_names if name.startswith("soil_cnp_")
    ]
    updated_singlets = [
        name for name in updated_variable_names if not name.startswith("soil_cnp_")
    ]
    refreshed_biomass_triplets = [
        name
        for name in fixture_soil_model.refreshed_variables
        if name.startswith("cnp_")
    ]
    refreshed_singlets = [
        name
        for name in fixture_soil_model.refreshed_variables
        if not name.startswith("cnp_")
    ]

    # Construct vector of initial values y0. Zeros are added to the end for all the
    # non-data object variables
    pools = np.concatenate(
        (
            np.concatenate(
                [
                    dummy_carbon_data[name].sel(element=element).to_numpy()
                    for element in elements.keys()
                    for name in updated_biomass_triplets
                ]
            ),
            np.concatenate(
                [dummy_carbon_data[name].to_numpy() for name in updated_singlets]
            ),
            np.zeros(
                len(refreshed_biomass_triplets)
                * len(elements.keys())
                * dummy_carbon_data.grid.n_cells
            ),
            np.zeros(len(refreshed_singlets) * dummy_carbon_data.grid.n_cells),
        )
    )
    # Find and store order of pools
    delta_pools_ordered = {
        **{
            f"{name}_{element}": np.array([])
            for element in elements.values()
            for name in updated_biomass_triplets
        },
        **{name: np.array([]) for name in updated_singlets},
        **{
            f"{name}_{element}": np.array([])
            for element in elements.values()
            for name in refreshed_biomass_triplets
        },
        **{name: np.array([]) for name in refreshed_singlets},
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
        fungal_fruit_decay_rate=fungal_fruiting_body_decay_rate,
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
        soil_c_pool_lmwc=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
        soil_n_pool_don=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_dop=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        microbe_pool_size=dummy_carbon_data["soil_c_pool_ectomycorrhiza"],
        soil_temp=averaged_soil_temp,
        microbial_group=functional_groups["ectomycorrhiza"],
        env_factors=environmental_factors,
    )

    assert np.allclose(actual_n_supply, expected_n_supply)
    assert np.allclose(actual_p_supply, expected_p_supply)
