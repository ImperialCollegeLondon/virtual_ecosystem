"""Collection of fixtures to assist the testing scripts."""

from logging import DEBUG
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from xarray import DataArray

# An import of LOGGER is required for INFO logging events to be visible to tests
# This can be removed as soon as a script that imports logger is imported
from virtual_ecosystem.core.logger import LOGGER

# Class uses DEBUG
LOGGER.setLevel(DEBUG)


def log_check(
    caplog: pytest.LogCaptureFixture,
    expected_log: tuple[tuple],
    subset: slice | None = None,
) -> None:
    """Helper function to check that the captured log is as expected.

    Arguments:
        caplog: An instance of the caplog fixture
        expected_log: An iterable of 2-tuples containing the log level and message.
        subset: Only check a specified subset of the captured log.
    """

    # caplog.records is just a list of LogRecord objects, so can use a slice to drop
    # down to a subset of the records.
    if subset is None:
        captured_records = caplog.records
    else:
        captured_records = caplog.records[subset]

    assert len(expected_log) == len(captured_records)

    assert all(
        [exp[0] == rec.levelno for exp, rec in zip(expected_log, captured_records)]
    )
    assert all(
        [exp[1] in rec.message for exp, rec in zip(expected_log, captured_records)]
    )


def record_found_in_log(
    caplog: pytest.LogCaptureFixture,
    find: tuple[int, str],
) -> bool:
    """Helper function to look for a specific logging record in the captured log.

    Arguments:
        caplog: An instance of the caplog fixture
        find: A tuple giving the logging level and message to look for
    """

    try:
        # Iterate over the record tuples, ignoring the leading element
        # giving the logger name
        _ = next(msg for msg in caplog.record_tuples if msg[1:] == find)
        return True
    except StopIteration:
        return False


@pytest.fixture(autouse=True)
def reset_module_registry():
    """Reset the module registry.

    The register_module function updates the MODULE_REGISTRY, which persists between
    tests. This autouse fixture is used to ensure that the registry is always cleared
    before tests start, so that the correct registration of modules within tests is
    enforced.
    """
    from virtual_ecosystem.core.registry import MODULE_REGISTRY

    MODULE_REGISTRY.clear()


# Shared fixtures


@pytest.fixture
def fixture_root_data_dir():
    """Provides the absolute path of the root data directory.

    Ideally we'd use something like pytest-datadir here, but it doesn't yet support
    nested directories: https://github.com/gabrielcnr/pytest-datadir/issues/28
    """

    return Path(__file__).parent / "data"


@pytest.fixture
def microbial_groups_cfg():
    """Configuration string containing full set of required microbial groups."""
    return """
        [[soil.microbial_group_definition]]
        name = "bacteria"
        taxonomic_group = "bacteria"
        max_uptake_rate_labile_C = 0.04
        activation_energy_uptake_rate = 47000
        half_sat_labile_C_uptake = 0.364
        activation_energy_uptake_saturation = 30000
        max_uptake_rate_ammonium = 5e-3
        half_sat_ammonium_uptake = 0.02275
        max_uptake_rate_nitrate = 5e-4
        half_sat_nitrate_uptake = 0.02275
        max_uptake_rate_labile_p = 0.0025
        half_sat_labile_p_uptake = 0.02275
        turnover_rate = 0.005
        activation_energy_turnover = 20000
        reference_temperature = 12.0
        c_n_ratio = 5.2
        c_p_ratio = 16
        enzyme_production.pom = 0.005
        enzyme_production.maom = 0.005
        reproductive_allocation = 0.0

        [[soil.microbial_group_definition]]
        name = "saprotrophic_fungi"
        taxonomic_group = "fungi"
        max_uptake_rate_labile_C = 0.04
        activation_energy_uptake_rate = 47000
        half_sat_labile_C_uptake = 0.364
        activation_energy_uptake_saturation = 30000
        max_uptake_rate_ammonium = 5e-3
        half_sat_ammonium_uptake = 0.02275
        max_uptake_rate_nitrate = 5e-4
        half_sat_nitrate_uptake = 0.02275
        max_uptake_rate_labile_p = 0.0025
        half_sat_labile_p_uptake = 0.02275
        turnover_rate = 0.005
        activation_energy_turnover = 20000
        reference_temperature = 12.0
        c_n_ratio = 6.5
        c_p_ratio = 40.0
        enzyme_production.pom = 0.005
        enzyme_production.maom = 0.005
        reproductive_allocation = 0.1

        [[soil.microbial_group_definition]]
        name = "arbuscular_mycorrhiza"
        taxonomic_group = "fungi"
        max_uptake_rate_labile_C = 0.04
        activation_energy_uptake_rate = 47000
        half_sat_labile_C_uptake = 0.364
        activation_energy_uptake_saturation = 30000
        max_uptake_rate_ammonium = 5e-3
        half_sat_ammonium_uptake = 0.02275
        max_uptake_rate_nitrate = 5e-4
        half_sat_nitrate_uptake = 0.02275
        max_uptake_rate_labile_p = 0.0025
        half_sat_labile_p_uptake = 0.02275
        turnover_rate = 0.005
        activation_energy_turnover = 20000
        reference_temperature = 12.0
        c_n_ratio = 18.0
        c_p_ratio = 120.0
        enzyme_production.pom = 0.0
        enzyme_production.maom = 0.0
        reproductive_allocation = 0.1

        [[soil.microbial_group_definition]]
        name = "ectomycorrhiza"
        taxonomic_group = "fungi"
        max_uptake_rate_labile_C = 0.04
        activation_energy_uptake_rate = 47000
        half_sat_labile_C_uptake = 0.364
        activation_energy_uptake_saturation = 30000
        max_uptake_rate_ammonium = 5e-3
        half_sat_ammonium_uptake = 0.02275
        max_uptake_rate_nitrate = 5e-4
        half_sat_nitrate_uptake = 0.02275
        max_uptake_rate_labile_p = 0.0025
        half_sat_labile_p_uptake = 0.02275
        turnover_rate = 0.005
        activation_energy_turnover = 20000
        reference_temperature = 12.0
        c_n_ratio = 18.0
        c_p_ratio = 120.0
        enzyme_production.pom = 0.02
        enzyme_production.maom = 0.02
        reproductive_allocation = 0.1

        [[soil.enzyme_class_definition]]
        source = "bacteria"
        substrate = "pom"
        maximum_rate = 60.0
        half_saturation_constant = 70.0
        activation_energy_rate = 37000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2
        c_n_ratio = 5.2
        c_p_ratio = 16

        [[soil.enzyme_class_definition]]
        source = "bacteria"
        substrate = "maom"
        maximum_rate = 24.0
        half_saturation_constant = 350.0
        activation_energy_rate = 47000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2
        c_n_ratio = 5.2
        c_p_ratio = 16

        [[soil.enzyme_class_definition]]
        source = "fungi"
        substrate = "pom"
        maximum_rate = 120.0
        half_saturation_constant = 35.0
        activation_energy_rate = 37000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2
        c_n_ratio = 6.5
        c_p_ratio = 40.0

        [[soil.enzyme_class_definition]]
        source = "fungi"
        substrate = "maom"
        maximum_rate = 48.0
        half_saturation_constant = 175.0
        activation_energy_rate = 47000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2
        c_n_ratio = 6.5
        c_p_ratio = 40.0
        """


@pytest.fixture
def fixture_config(fixture_root_data_dir, microbial_groups_cfg):
    """Simple configuration fixture for use in tests."""

    from virtual_ecosystem.core.config import Config

    cfg_string = f"""
        [core]
        [core.grid]
        cell_nx = 2
        cell_ny = 2
        [core.timing]
        start_date = "2020-01-01"
        update_interval = "2 weeks"
        run_length = "50 years"
        [core.data_output_options]
        save_initial_state = true
        save_final_state = true
        out_initial_file_name = "model_at_start.nc"
        out_final_file_name = "model_at_end.nc"

        [core.layers]
        canopy_layers = 10
        soil_layers = [-0.5, -1.0]
        above_canopy_height_offset = 2.0
        surface_layer_height = 0.1

        [plants]
        # Deliberately using single quote to provide TOML literal string for path
        pft_definitions_path = '{(fixture_root_data_dir / "plant_pfts.csv")!s}'

        [[animal.functional_groups]]
        name = "carnivorous_bird"
        taxa = "bird"
        diet = "carnivore"
        metabolic_type = "endothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "carnivorous_bird"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "ground_canopy"
        birth_mass = 0.1
        adult_mass = 1.0

        [[animal.functional_groups]]
        name = "herbivorous_bird"
        taxa = "bird"
        diet = "herbivore"
        metabolic_type = "endothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "herbivorous_bird"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "ground_canopy"
        birth_mass = 0.05
        adult_mass = 0.5

        [[animal.functional_groups]]
        name = "carnivorous_mammal"
        taxa = "mammal"
        diet = "carnivore"
        metabolic_type = "endothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "carnivorous_mammal"
        excretion_type = "ureotelic"
        migration_type = "none"
        vertical_occupancy = "ground"
        birth_mass = 4.0
        adult_mass = 40.0

        [[animal.functional_groups]]
        name = "herbivorous_mammal"
        taxa = "mammal"
        diet = "herbivore"
        metabolic_type = "endothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "herbivorous_mammal"
        excretion_type = "ureotelic"
        migration_type = "none"
        vertical_occupancy = "ground"
        birth_mass = 1.0
        adult_mass = 10.0

        [[animal.functional_groups]]
        name = "carnivorous_insect"
        taxa = "insect"
        diet = "carnivore"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "carnivorous_insect"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "soil_ground_canopy"
        birth_mass = 0.001
        adult_mass = 0.01

        [[animal.functional_groups]]
        name = "herbivorous_insect"
        taxa = "insect"
        diet = "herbivore"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "semelparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "herbivorous_insect"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "soil_ground_canopy"
        birth_mass = 0.0005
        adult_mass = 0.005

        [[animal.functional_groups]]
        name = "butterfly"
        taxa = "insect"
        diet = "herbivore"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "semelparous"
        development_type = "indirect"
        development_status = "adult"
        offspring_functional_group = "caterpillar"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "ground_canopy"
        birth_mass = 0.0005
        adult_mass = 0.005

        [[animal.functional_groups]]
        name = "caterpillar"
        taxa = "insect"
        diet = "herbivore"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "nonreproductive"
        development_type = "indirect"
        development_status = "larval"
        offspring_functional_group = "butterfly"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "canopy"
        birth_mass = 0.0005
        adult_mass = 0.005

        [[animal.functional_groups]]
        name = "frog"
        taxa = "amphibian"
        diet = "carnivore"
        metabolic_type = "ectothermic"
        reproductive_environment = "aquatic"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "frog"
        excretion_type = "ureotelic"
        migration_type = "none"
        vertical_occupancy = "ground"
        birth_mass = 0.005
        adult_mass = 0.5

        [[animal.functional_groups]]
        name = "swallow"
        taxa = "bird"
        diet = "carnivore"
        metabolic_type = "endothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "swallow"
        excretion_type = "uricotelic"
        migration_type = "seasonal"
        vertical_occupancy = "canopy"
        birth_mass = 0.005
        adult_mass = 0.2

        [[animal.functional_groups]]
        name = "earthworm"
        taxa = "insect"
        diet = "herbivore"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "earthworm"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "soil"
        birth_mass = 0.0005
        adult_mass = 0.005

        [[animal.functional_groups]]
        name = "dung_beetle"
        taxa = "invertebrate"
        diet = "waste"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "dung_beetle"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "soil_ground"
        birth_mass = 0.0003
        adult_mass = 0.003

        [[animal.functional_groups]]
        name = "scavenging_mammal"
        taxa = "mammal"
        diet = "carcasses"
        metabolic_type = "endothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "scavenging_mammal"
        excretion_type = "ureotelic"
        migration_type = "none"
        vertical_occupancy = "ground"
        birth_mass = 2.0
        adult_mass = 20.0

        [[animal.functional_groups]]
        name = "detritivorous_insect"
        taxa = "invertebrate"
        diet = "detritus"
        metabolic_type = "ectothermic"
        reproductive_environment = "terrestrial"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "detritivorous_insect"
        excretion_type = "uricotelic"
        migration_type = "none"
        vertical_occupancy = "soil_ground"
        birth_mass = 0.0004
        adult_mass = 0.004

        [hydrology]
    """

    return Config(cfg_strings=[cfg_string, microbial_groups_cfg])


@pytest.fixture
def fixture_core_components(fixture_config):
    """A CoreComponents instance for use in testing."""
    from virtual_ecosystem.core.core_components import CoreComponents

    core_components = CoreComponents(fixture_config)

    # Setup three filled canopy layers
    canopy_array = np.full(
        (core_components.layer_structure.n_canopy_layers, core_components.grid.n_cells),
        np.nan,
    )
    canopy_array[np.array([0, 1, 2])] = 1.0
    core_components.layer_structure.set_filled_canopy(canopy_array)

    return core_components


@pytest.fixture
def dummy_litter_data(fixture_core_components):
    """Creates a dummy litter data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    lyr_strct = fixture_core_components.layer_structure

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # These values are taken from SAFE Project data, albeit in a very unsystematic
    # manner. The repeated fourth value is simply to adapt three hand validated examples
    # to the shared fixture core components grid
    pool_values = {
        "litter_pool_above_metabolic": [0.319785, 0.161631, 0.086129, 0.093456],
        "litter_pool_above_structural": [0.52097, 0.26609, 0.10019, 0.09988],
        "litter_pool_woody": [5.1773833, 12.185701, 7.673456, 7.462192],
        "litter_pool_below_metabolic": [0.410373, 0.375794, 0.080181, 0.083494],
        "litter_pool_below_structural": [0.613547, 0.321674, 0.032738, 0.029168],
        "lignin_above_structural": [0.5, 0.1, 0.7, 0.7],
        "lignin_woody": [0.5, 0.8, 0.35, 0.35],
        "lignin_below_structural": [0.5, 0.25, 0.75, 0.75],
        "c_n_ratio_above_metabolic": [7.3, 8.7, 10.1, 9.8],
        "c_n_ratio_above_structural": [37.5, 43.2, 45.8, 50.2],
        "c_n_ratio_woody": [55.5, 63.3, 47.3, 59.1],
        "c_n_ratio_below_metabolic": [10.7, 11.3, 15.2, 12.4],
        "c_n_ratio_below_structural": [50.5, 55.6, 73.1, 61.2],
        "c_p_ratio_above_metabolic": [57.3, 68.7, 100.1, 95.8],
        "c_p_ratio_above_structural": [337.5, 473.2, 415.8, 570.2],
        "c_p_ratio_woody": [555.5, 763.3, 847.3, 599.1],
        "c_p_ratio_below_metabolic": [310.7, 411.3, 315.2, 412.4],
        "c_p_ratio_below_structural": [550.5, 595.6, 773.1, 651.2],
        "deadwood_production": [0.075, 0.099, 0.063, 0.033],
        "leaf_turnover": [0.027, 0.0003, 0.021, 0.0285],
        "fallen_non_propagule_c_mass": [0.003, 0.0075, 0.00255, 0.00375],
        "root_turnover": [0.027, 0.021, 0.0003, 0.0249],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "senesced_leaf_lignin": [0.05, 0.25, 0.3, 0.57],
        "plant_reproductive_tissue_lignin": [0.01, 0.03, 0.04, 0.02],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "deadwood_c_n_ratio": [60.7, 57.9, 73.1, 55.1],
        "leaf_turnover_c_n_ratio": [15.0, 25.5, 43.1, 57.4],
        "plant_reproductive_tissue_turnover_c_n_ratio": [12.5, 23.8, 15.7, 18.2],
        "root_turnover_c_n_ratio": [30.3, 45.6, 43.3, 37.1],
        "deadwood_c_p_ratio": [856.5, 675.4, 933.2, 888.8],
        "leaf_turnover_c_p_ratio": [415.0, 327.4, 554.5, 380.9],
        "plant_reproductive_tissue_turnover_c_p_ratio": [125.5, 105.0, 145.0, 189.2],
        "root_turnover_c_p_ratio": [656.7, 450.6, 437.3, 371.9],
        "litter_consumption_above_metabolic": [0.019785, 0.011631, 0.016129, 0.023456],
        "litter_consumption_above_structural": [0.02097, 0.01609, 0.01019, 0.00988],
        "litter_consumption_woody": [0.4773833, 0.385701, 0.373456, 0.162192],
        "litter_consumption_below_metabolic": [0.010373, 0.005794, 0.010181, 0.013494],
        "litter_consumption_below_structural": [0.013547, 0.011674, 0.012738, 0.009168],
        "herbivory_waste_leaf_carbon": [3e-5, 2.1e-3, 2.85e-3, 2.7e-3],
        "herbivory_waste_leaf_nitrogen": [23.1, 33.5, 23.1, 17.3],
        "herbivory_waste_leaf_phosphorus": [212.5, 344.8, 334.8, 420.1],
        "herbivory_waste_leaf_lignin": [0.13, 0.08, 0.27, 0.22],
    }

    for var, vals in pool_values.items():
        data[var] = DataArray(vals, dims=["cell_id"])

    # Vertically structured variables
    data["soil_temperature"] = lyr_strct.from_template()
    data["soil_temperature"][lyr_strct.index_topsoil] = 20
    data["soil_temperature"][lyr_strct.index_subsoil] = [19.5, 18.7, 18.7, 17.6]

    # At present the soil model only uses the top soil layer, so this is the
    # only one with real test values in
    data["matric_potential"] = lyr_strct.from_template()
    data["matric_potential"][lyr_strct.index_topsoil] = [-10.0, -25.0, -100.0, -100.0]
    data["matric_potential"][lyr_strct.index_subsoil] = [-11.0, -29.5, -123.0, -154.1]

    data["air_temperature"] = lyr_strct.from_template()
    data["air_temperature"][lyr_strct.index_filled_atmosphere] = np.array(
        [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    )[:, None]

    return data


@pytest.fixture
def dummy_climate_data(fixture_core_components):
    """Creates a dummy climate data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # Shorten syntax
    lyr_str = fixture_core_components.layer_structure
    from_template = lyr_str.from_template

    # Reference data with a time series
    ref_values = {
        "air_temperature_ref": 30.0,
        "wind_speed_ref": 1.0,
        "relative_humidity_ref": 90.0,
        "vapour_pressure_deficit_ref": 0.14,
        "vapour_pressure_ref": 0.14,
        "atmospheric_pressure_ref": 96.0,
        "atmospheric_co2_ref": 400.0,
        "precipitation": 200.0,
        "downward_shortwave_radiation": 500.0,
    }

    for var, value in ref_values.items():
        data[var] = DataArray(
            np.full((4, 3), value),
            dims=["cell_id", "time_index"],
        )

    # Spatially varying but not vertically structured
    spatially_variable = {
        "shortwave_radiation_surface": [100, 10, 0, 0],
        "sensible_heat_flux_topofcanopy": [100, 50, 10, 10],
        "friction_velocity": [12, 5, 2, 2],
        "soil_evaporation": [0.001, 0.01, 0.1, 0.1],
        # "surface_runoff": [10, 50, 100, 100],
        "surface_runoff_accumulated": [0, 10, 300, 300],
        "subsurface_flow_accumulated": [10, 10, 30, 30],
        "elevation": [200, 100, 10, 10],
    }
    for var, vals in spatially_variable.items():
        data[var] = DataArray(vals, dims=["cell_id"])

    # Spatially constant and not vertically structured
    spatially_constant = {
        "sensible_heat_flux_soil": 1,
        "latent_heat_flux_soil": 1,
        "zero_plane_displacement": 20.0,
        "diabatic_correction_heat_above": 0.1,
        "diabatic_correction_heat_canopy": 1.0,
        "diabatic_correction_momentum_above": 0.1,
        "diabatic_correction_momentum_canopy": 1.0,
        "mean_mixing_length": 1.3,
        "aerodynamic_resistance_surface": 12.5,
        "mean_annual_temperature": 20.0,
    }
    for var, val in spatially_constant.items():
        data[var] = DataArray(np.repeat(val, 4), dims=["cell_id"])

    # Structural variables - assign values to vertical layer indices across grid id
    data["leaf_area_index"] = from_template()
    data["leaf_area_index"][lyr_str.index_filled_canopy] = 1.0

    data["layer_heights"] = from_template()
    data["layer_heights"][lyr_str.index_filled_atmosphere] = np.array(
        [32.0, 30.0, 20.0, 10.0, lyr_str.surface_layer_height]
    )[:, None]

    data["layer_heights"][lyr_str.index_all_soil] = lyr_str.soil_layer_depths[:, None]

    # Microclimate and energy balance
    # - Vertically structured
    data["wind_speed"] = from_template()
    data["wind_speed"][lyr_str.index_filled_atmosphere] = 0.1

    data["aerodynamic_resistance_canopy"] = from_template()
    data["aerodynamic_resistance_canopy"][lyr_str.index_filled_canopy] = 12.5

    data["atmospheric_pressure"] = from_template()
    data["atmospheric_pressure"][lyr_str.index_filled_atmosphere] = 96.0

    data["air_temperature"] = from_template()
    data["air_temperature"][lyr_str.index_filled_atmosphere] = np.array(
        [30.0, 29.844995, 28.87117, 27.206405, 21.145945]
    )[:, None]

    data["soil_temperature"] = from_template()
    data["soil_temperature"][lyr_str.index_all_soil] = 20.0

    data["matric_potential"] = from_template()
    data["matric_potential"][lyr_str.index_topsoil] = np.array(
        [-3.0, -10.0, -250.0, -10000.0]
    )

    data["relative_humidity"] = from_template()
    data["relative_humidity"][lyr_str.index_filled_atmosphere] = np.array(
        [90.0, 90.341644, 92.488034, 96.157312, 100]
    )[:, None]

    data["vapour_pressure_deficit"] = from_template()
    data["vapour_pressure_deficit"][lyr_str.index_filled_atmosphere] = np.array(
        [0.14, 0.2, 0.2, 0.2, 0.14]
    )[:, None]

    flux_index = np.logical_or(lyr_str.index_above, lyr_str.index_flux_layers)

    data["shortwave_absorption"] = from_template()
    data["shortwave_absorption"][flux_index] = 450.0

    data["sensible_heat_flux"] = from_template()
    data["sensible_heat_flux"][flux_index] = 0.0

    data["latent_heat_flux"] = from_template()
    data["latent_heat_flux"][flux_index] = 0.0

    data["net_radiation"] = from_template()
    data["net_radiation"][lyr_str.index_flux_layers] = 20.0

    data["molar_density_air"] = from_template()
    data["molar_density_air"][lyr_str.index_filled_atmosphere] = 38.0

    data["density_air"] = from_template()
    data["density_air"][lyr_str.index_filled_atmosphere] = 1.255

    data["specific_heat_air"] = from_template()
    data["specific_heat_air"][lyr_str.index_filled_atmosphere] = 1.006

    data["attenuation_coefficient"] = from_template()
    data["attenuation_coefficient"][lyr_str.index_filled_atmosphere] = np.array(
        [13.0, 13.0, 13.0, 13.0, 2.0]
    )[:, None]

    data["relative_turbulence_intensity"] = from_template()
    data["relative_turbulence_intensity"][lyr_str.index_filled_atmosphere] = np.array(
        [17.64, 16.56, 11.16, 5.76, 0.414]
    )[:, None]

    data["latent_heat_vapourisation"] = from_template()
    data["latent_heat_vapourisation"][lyr_str.index_filled_atmosphere] = 2442.0

    data["canopy_temperature"] = from_template()
    data["canopy_temperature"][lyr_str.index_filled_canopy] = 25.0

    data["canopy_evaporation"] = from_template()
    data["canopy_evaporation"][lyr_str.index_filled_canopy] = 10.0

    data["leaf_air_heat_conductivity"] = from_template()
    data["leaf_air_heat_conductivity"][lyr_str.index_filled_canopy] = 0.13

    data["leaf_vapour_conductivity"] = from_template()
    data["leaf_vapour_conductivity"][lyr_str.index_filled_canopy] = 0.2

    data["conductivity_from_ref_height"] = from_template()
    data["conductivity_from_ref_height"][
        np.logical_or(lyr_str.index_filled_canopy, lyr_str.index_surface)
    ] = 3.0

    data["stomatal_conductance"] = from_template()
    data["stomatal_conductance"][lyr_str.index_filled_canopy] = 15.0

    # Hydrology
    data["transpiration"] = from_template()
    data["transpiration"][lyr_str.index_filled_canopy] = 20.0

    data["soil_moisture"] = from_template()
    data["soil_moisture"][lyr_str.index_all_soil] = np.array([5.0, 500.0])[:, None]

    data["groundwater_storage"] = DataArray(
        np.full((2, 4), 450.0),
        dims=("groundwater_layers", "cell_id"),
    )

    return data


# dummy climate data with different number of canopy layers
@pytest.fixture
def dummy_climate_data_varying_canopy(fixture_core_components, dummy_climate_data):
    """Creates a dummy climate data object for use in tests.

    This fixture modifies the parent dummy_climate_data to introduce variation in the
    number of canopy layers within the different cells, including one grid cell without
    vegetation.
    """

    lyr_str = fixture_core_components.layer_structure
    index_filled_canopy = lyr_str.index_filled_canopy
    index_filled_atmosphere = lyr_str.index_filled_atmosphere

    # Structural variables
    dummy_climate_data["leaf_area_index"][index_filled_canopy] = [
        [1.0, 1.0, 1.0, np.nan],
        [1.0, 1.0, np.nan, np.nan],
        [1.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["layer_heights"][index_filled_canopy] = [
        [30.0, 30.0, 30.0, np.nan],
        [20.0, 20.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
    ]

    # Microclimate and energy balance
    dummy_climate_data["wind_speed"][index_filled_canopy] = [
        [0.1, 0.1, 0.1, np.nan],
        [0.1, 0.1, np.nan, np.nan],
        [0.1, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["air_temperature"][index_filled_canopy] = [
        [29.844995, 29.844995, 29.844995, np.nan],
        [28.87117, 28.87117, np.nan, np.nan],
        [27.206405, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_humidity"][index_filled_canopy] = [
        [90.341644, 90.341644, 90.341644, np.nan],
        [92.488034, 92.488034, np.nan, np.nan],
        [96.157312, np.nan, np.nan, np.nan],
    ]

    sw_indexes = [1, 2, 3, 13]
    dummy_climate_data["shortwave_absorption"][sw_indexes] = [
        [450.0, 450.0, 450.0, np.nan],
        [450.0, 450.0, np.nan, np.nan],
        [450.0, np.nan, np.nan, np.nan],
        [450.0, 450.0, 450.0, 450],
    ]
    # dummy_climate_data["shortwave_absorption"][13] = np.repeat(0.0, 4)

    dummy_climate_data["aerodynamic_resistance_canopy"][index_filled_canopy] = [
        [12.5, 12.5, 12.5, np.nan],
        [12.5, 12.5, np.nan, np.nan],
        [12.5, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["vapour_pressure_deficit"][index_filled_atmosphere] = [
        [0.14, 0.14, 0.14, 0.14],
        [0.2, 0.2, 0.2, np.nan],
        [0.2, 0.2, np.nan, np.nan],
        [0.2, np.nan, np.nan, np.nan],
        [0.14, 0.14, 0.14, 0.14],
    ]
    dummy_climate_data["sensible_heat_flux"][index_filled_canopy] = [
        [0.0, 0.0, 0.0, np.nan],
        [0.0, 0.0, np.nan, np.nan],
        [0.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["latent_heat_flux"][index_filled_canopy] = [
        [0.0, 0.0, 0.0, np.nan],
        [0.0, 0.0, np.nan, np.nan],
        [0.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["net_radiation"][lyr_str.index_flux_layers] = [
        [20.0, 20.0, 20.0, np.nan],
        [20.0, 20.0, np.nan, np.nan],
        [20.0, np.nan, np.nan, np.nan],
        [20.0, 20.0, 20.0, 20.0],
    ]

    dummy_climate_data["attenuation_coefficient"][index_filled_canopy] = [
        [13.0, 13.0, 13.0, np.nan],
        [13.0, 13.0, np.nan, np.nan],
        [13.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_turbulence_intensity"][index_filled_canopy] = [
        [16.56, 16.56, 16.56, np.nan],
        [11.16, 11.16, np.nan, np.nan],
        [5.76, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["canopy_temperature"][index_filled_canopy] = [
        [25.0, 25.0, 25.0, np.nan],
        [25.0, 25.0, np.nan, np.nan],
        [25.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["canopy_evaporation"][index_filled_canopy] = [
        [10.0, 10.0, 10.0, np.nan],
        [10.0, 10.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["leaf_air_heat_conductivity"][index_filled_canopy] = [
        [0.13, 0.13, 0.13, np.nan],
        [0.13, 0.13, np.nan, np.nan],
        [0.13, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["leaf_vapour_conductivity"][index_filled_canopy] = [
        [0.2, 0.2, 0.2, np.nan],
        [0.2, 0.2, np.nan, np.nan],
        [0.2, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["conductivity_from_ref_height"][index_filled_canopy] = [
        [3.0, 3.0, 3.0, np.nan],
        [3.0, 3.0, np.nan, np.nan],
        [3.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["stomatal_conductance"][index_filled_canopy] = [
        [15.0, 15.0, 15.0, np.nan],
        [15.0, 15.0, np.nan, np.nan],
        [15.0, np.nan, np.nan, np.nan],
    ]

    # Hydrology
    dummy_climate_data["transpiration"][index_filled_canopy] = [
        [20.0, 20.0, 20.0, np.nan],
        [20.0, 20.0, np.nan, np.nan],
        [20.0, np.nan, np.nan, np.nan],
    ]

    return dummy_climate_data


def patch_run_update(model: type):
    """Patch the run update check during the init of the model."""
    return patch(
        f"{model.__module__}.{model.__name__}._run_update_due_to_static_configuration"
    )


def patch_bypass_setup(model: type):
    """Patch the bypass setup check during the init of the model."""
    return patch(
        f"{model.__module__}.{model.__name__}._bypass_setup_due_to_static_configuration"
    )


def patch_static_config(model: type):
    """Patch the check static config during the init of the model."""
    return patch(f"{model.__module__}.{model.__name__}._check_static_config")
