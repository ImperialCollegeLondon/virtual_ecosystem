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
                                [2.52032293, 1.71099302, 4.53815446, 0.539065149],
                                [0.866635291, 0.486177206, 0.334537683, 0.100119097],
                                [1.357739e-2, 3.486291e-2, 2.007373e-2, 4.124445e-3],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_cnp_pool_lmwc=DataArray(
                        data=np.stack(
                            [
                                [0.124367266, 0.394515410, 0.228526990, 9.52935450e-2],
                                [2.0843248e-3, 4.2951438e-3, 3.3014081e-3, 1.565302e-2],
                                [5.3738481e-4, 2.8005139e-4, 3.2911107e-4, 4.167518e-3],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_cnp_pool_pom=DataArray(
                        data=np.stack(
                            [
                                [9.60024574e-2, 0.981299961, 0.685350224, 0.349004795],
                                [7.093183e-3, 7.385895e-4, 2.896863e-3, 1.428807e-2],
                                [3.193539e-5, 2.821069e-4, 1.136387e-4, 5.714988e-4],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_cnp_pool_necromass=DataArray(
                        data=np.stack(
                            [
                                [0.06669194, 0.06421258, 0.15120979, 0.11924888],
                                [0.00690107, 0.01895787, 0.02545451, 0.01167541],
                                [0.00202859, 0.00160796, 0.00401719, 0.00110328],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    soil_c_pool_bacteria=DataArray(
                        [5.77045533, 2.28891905, 11.24087901, 0.99629548],
                        dims="cell_id",
                    ),
                    soil_c_pool_saprotrophic_fungi=DataArray(
                        [0.88572308, 8.51096246, 2.19878325, 4.52372127], dims="cell_id"
                    ),
                    soil_c_pool_arbuscular_mycorrhiza=DataArray(
                        [0.64705435, 1.46397984, 3.90103466, 9.00941312], dims="cell_id"
                    ),
                    soil_c_pool_ectomycorrhiza=DataArray(
                        [0.4675008, 1.3144604, 4.17831672, 3.75662054], dims="cell_id"
                    ),
                    soil_enzyme_pom_bacteria=DataArray(
                        [0.02241112, 0.00946393, 0.04946033, 0.00297472], dims="cell_id"
                    ),
                    soil_enzyme_maom_bacteria=DataArray(
                        [0.035178, 0.01156259, 0.02479707, 0.00450623], dims="cell_id"
                    ),
                    soil_enzyme_pom_fungi=DataArray(
                        [0.02576334, 0.00572417, 0.0064011, 0.00437354], dims="cell_id"
                    ),
                    soil_enzyme_maom_fungi=DataArray(
                        [0.00856991, 0.00678733, 0.00377974, 0.00215334], dims="cell_id"
                    ),
                    soil_n_pool_ammonium=DataArray(
                        [0.00019027, 0.00981517, 0.00023862, 0.00490141], dims="cell_id"
                    ),
                    soil_n_pool_nitrate=DataArray(
                        [-0.00117727, -0.00160238, -0.00064369, 0.01254261],
                        dims="cell_id",
                    ),
                    soil_p_pool_primary=DataArray(
                        [0.0019594, 0.00535662, 0.00277434, 0.00059892], dims="cell_id"
                    ),
                    soil_p_pool_secondary=DataArray(
                        [0.00705642, 0.03816755, 0.0115255, 0.00733095], dims="cell_id"
                    ),
                    soil_p_pool_labile=DataArray(
                        [2.45035807e-6, -1.65691445e-4, 2.54670417e-5, 2.17387221e-4],
                        dims="cell_id",
                    ),
                    cnp_fungal_fruiting_body_production=DataArray(
                        data=np.stack(
                            [
                                [6.070803e-5, 6.414525e-4, 3.457541e-4, 3.318303e-4],
                                [4.965892e-6, 7.158910e-5, 2.478335e-5, 2.349736e-5],
                                [7.760556e-7, 1.144179e-5, 3.826575e-6, 3.623650e-6],
                            ],
                            axis=1,
                        ),
                        coords={"cell_id": np.arange(0, 4), "element": ["C", "N", "P"]},
                    ),
                    new_amf_n_supply=DataArray(
                        [4.10625930e-6, 2.32739727e-5, 3.23760816e-5, 3.23930333e-5],
                        dims="cell_id",
                    ),
                    new_amf_p_supply=DataArray(
                        [6.15938895e-7, 3.49109590e-6, 4.85641224e-6, 4.85895499e-6],
                        dims="cell_id",
                    ),
                    new_emf_n_supply=DataArray(
                        [2.96325241e-6, 2.07398974e-5, 1.29687744e-5, 1.14853767e-5],
                        dims="cell_id",
                    ),
                    new_emf_p_supply=DataArray(
                        [4.47876588e-7, 3.13470241e-6, 1.96014703e-6, 1.73594099e-6],
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
            0.00708104,
            0.63961043,
            0.03860748,
            0.29806497,
        ],
        "arbuscular_mycorrhizal_p_supply": [
            9.88358755e-05,
            3.05633750e-03,
            7.09019114e-03,
            6.54080777e-03,
        ],
        "ectomycorrhizal_n_supply": [0.00512013, 0.57434406, 0.04136516, 0.12430364],
        "ectomycorrhizal_p_supply": [
            7.14659407e-05,
            2.74446632e-03,
            7.59663337e-03,
            2.72774837e-03,
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
        1.53669162e-01,
        7.67625180e-01,
        2.60513931e-01,
        1.85545749e-01,
        3.73478679e-02,
        3.40135790e-03,
        5.44755407e-02,
        7.27554581e-02,
        -8.04411394e-03,
        -3.77977246e-02,
        -2.96999036e-02,
        -1.99207998e-03,
        2.19229049e-02,
        1.23255059e-01,
        1.46033301e-01,
        3.58387342e-02,
        2.83278132e-03,
        6.06887820e-03,
        6.40820273e-03,
        2.58992685e-02,
        9.94575443e-04,
        1.04139821e-02,
        1.32635587e-02,
        7.72834839e-03,
        -1.00607087e-04,
        4.89636674e-05,
        7.95982722e-05,
        4.67440633e-06,
        1.00676512e-02,
        2.72941209e-03,
        1.32333153e-02,
        1.32506915e-03,
        9.94241375e-04,
        5.89648666e-04,
        2.61608597e-04,
        8.16611736e-03,
        5.44660113e-04,
        -6.28584725e-05,
        4.52813305e-04,
        3.09131163e-04,
        6.75936879e-06,
        -7.30169672e-06,
        -1.32791192e-06,
        1.38770918e-07,
        3.06011879e-03,
        3.73768946e-03,
        8.27202479e-03,
        1.64523888e-03,
        -6.02217831e-02,
        -2.27086764e-02,
        -1.19510674e-01,
        -7.64474307e-03,
        -8.87422609e-03,
        -8.24263404e-02,
        -2.29985772e-02,
        -3.35347741e-02,
        -6.40040479e-03,
        -1.38016121e-02,
        -3.97750057e-02,
        -6.27059305e-02,
        -5.33499914e-03,
        -1.25084008e-02,
        -4.34819211e-02,
        -2.71133069e-02,
        -5.43951037e-04,
        -2.27953510e-04,
        -1.19322945e-03,
        -7.21042991e-05,
        -8.54055037e-04,
        -2.78929510e-04,
        -5.94165452e-04,
        -1.09304299e-04,
        -6.25004175e-04,
        -1.00853524e-04,
        -1.21044666e-04,
        -8.40801622e-05,
        -2.07380175e-04,
        -1.26677524e-04,
        -5.73726662e-05,
        -3.01521622e-05,
        1.29345703e-04,
        6.27144326e-03,
        -2.40053245e-04,
        -1.27696447e-04,
        -5.63890898e-03,
        -5.77860437e-03,
        -2.04456199e-03,
        -1.78870844e-03,
        -4.47351598e-10,
        -1.22297260e-09,
        -6.33410959e-10,
        -1.36739726e-10,
        -5.05079715e-07,
        -2.77311435e-06,
        -7.40323880e-07,
        -2.18769722e-07,
        -1.83486608e-05,
        -4.73259240e-04,
        -1.20248620e-04,
        -3.21100538e-05,
        9.44491405e-06,
        5.54712673e-04,
        4.66767176e-04,
        3.99101273e-04,
        7.61426696e-07,
        6.19111888e-05,
        3.21181525e-05,
        2.32742859e-05,
        1.18845272e-07,
        9.89503562e-06,
        4.93876588e-06,
        3.51270361e-06,
        6.50771197e-07,
        2.01240329e-05,
        3.81308482e-05,
        4.30670470e-05,
        9.76156795e-08,
        3.01860493e-06,
        5.71962723e-06,
        6.46005705e-06,
        4.66997299e-07,
        1.79338346e-05,
        2.59375488e-05,
        1.78245904e-05,
        7.05836452e-08,
        2.71058402e-06,
        3.92029406e-06,
        2.69407247e-06,
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

    expected_n_supply = [5.05692202e-06, 5.67253393e-04, 4.08544802e-05, 1.22769029e-04]
    expected_p_supply = [7.05836452e-08, 2.71058402e-06, 7.50284777e-06, 2.69407247e-06]

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
