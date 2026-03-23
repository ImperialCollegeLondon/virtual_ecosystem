"""Collection of fixtures to assist the testing scripts."""

from logging import DEBUG
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from numpy.typing import NDArray
from xarray import DataArray

# An import of LOGGER is required for INFO logging events to be visible to tests
# This can be removed as soon as a script that imports logger is imported
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic import abiotic_tools
from virtual_ecosystem.models.abiotic.microclimate import (
    compute_weights_from_absorbed_radiation,
)

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
        _ = next(
            _
            for _, level, message in caplog.record_tuples
            if level == find[0] and message.startswith(find[1])
        )
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

FIXTURE_ROOT_DATA_DIR = Path(__file__).parent / "data"
"""Provides the absolute path of the root data directory.

Ideally we'd use something like pytest-datadir here, but it doesn't yet support
nested directories: https://github.com/gabrielcnr/pytest-datadir/issues/28
"""


MICROBE_CONFIG_TOML = """
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
symbiote_nitrogen_uptake_fraction = 0.0
symbiote_phosphorus_uptake_fraction = 0.0

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
symbiote_nitrogen_uptake_fraction = 0.0
symbiote_phosphorus_uptake_fraction = 0.0

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
symbiote_nitrogen_uptake_fraction = 0.2
symbiote_phosphorus_uptake_fraction = 0.2

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
symbiote_nitrogen_uptake_fraction = 0.2
symbiote_phosphorus_uptake_fraction = 0.2

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
def microbial_groups_cfg():
    """Configuration string containing full set of required microbial groups."""
    return MICROBE_CONFIG_TOML


def generate_config_strings(
    nx: int = 2,
    ny: int = 2,
    additional_toml: str = MICROBE_CONFIG_TOML,
    fixture_root_data_dir: Path = FIXTURE_ROOT_DATA_DIR,
):
    """Configuration generator.

    The different model testing uses configurations on different grids - most tests stay
    on a 2x2 grid, but animal testing needs more cells and so uses 3x3. This function
    centralises the code to generate the config from the shared elements and so
    coordinates the contents of parallel configuration fixtures that can use different
    grid sizes.

    Args:
        nx: Number of cells in x axis
        ny: Number of cells in y axis
        additional_toml: Any additional TOML to append to the core string
        fixture_root_data_dir: The path of the root data directory
    """

    cfg_string = f"""
        [core]
        [core.grid]
        cell_nx = {nx}
        cell_ny = {ny}
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
        cohort_data_path = '{(fixture_root_data_dir / "plant_cohort_data.csv")!s}'

        [animal]
        functional_group_definitions_path = '''
{(fixture_root_data_dir / "animal_functional_groups.csv")!s}'''

        [hydrology]
        [litter]
        [abiotic]
    """

    return [cfg_string, additional_toml]


@pytest.fixture
def fixture_configuration():
    """Default configuration with 2x2 grid."""
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )

    config_data = ConfigurationLoader(cfg_strings=generate_config_strings())

    return generate_configuration(config_data.data)


@pytest.fixture
def animal_fixture_configuration():
    """Default configuration with 3x3 grid."""
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )

    config_data = ConfigurationLoader(cfg_strings=generate_config_strings(nx=3, ny=3))

    return generate_configuration(config_data.data)


@pytest.fixture
def fixture_core_constants(fixture_configuration):
    """Get the core constants instance from the config."""

    return fixture_configuration.core.constants


@pytest.fixture
def fixture_pyrealm_config(fixture_configuration):
    """Get the pyrealm config instance from the config."""

    return fixture_configuration.core.pyrealm


@pytest.fixture
def fixture_soil_constants(fixture_configuration):
    """Get the soil constants instance from the config."""

    return fixture_configuration.soil.constants


@pytest.fixture
def fixture_hydrology_constants(fixture_configuration):
    """Get the hydrology constants instance from the config."""

    return fixture_configuration.hydrology.constants


@pytest.fixture
def fixture_abiotic_constants(fixture_configuration):
    """Get the abiotic constants instance from the config."""

    return fixture_configuration.abiotic.constants


@pytest.fixture
def fixture_plants_constants(fixture_configuration):
    """Get the abiotic constants instance from the config."""

    return fixture_configuration.plants.constants


@pytest.fixture
def fixture_litter_constants(fixture_configuration):
    """Get the abiotic constants instance from the config."""

    return fixture_configuration.litter.constants


@pytest.fixture
def fixture_abiotic_simple_configuration():
    """Get an abiotic_simple configuration instance to provide bounds and constants.

    The abiotic simple model is not used in the fixture_configuration so this fixture
    creates one from scratch.
    """

    from virtual_ecosystem.models.abiotic_simple.model_config import (
        AbioticSimpleConfiguration,
    )

    return AbioticSimpleConfiguration()


@pytest.fixture
def fixture_core_components(fixture_configuration):
    """A CoreComponents instance for use in testing."""
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.model_config import CoreConfiguration

    core_cfg = fixture_configuration.get_subconfiguration("core", CoreConfiguration)
    core_components = CoreComponents(core_cfg)

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
        "lignin_above_structural": [0.5, 0.1, 0.7, 0.7],
        "lignin_woody": [0.5, 0.8, 0.35, 0.35],
        "lignin_below_structural": [0.5, 0.25, 0.75, 0.75],
        "fallen_non_propagule_c_mass": [0.003, 0.0075, 0.00255, 0.00375],
        "stem_lignin": [0.233, 0.545, 0.612, 0.378],
        "senesced_leaf_lignin": [0.05, 0.25, 0.3, 0.57],
        "plant_reproductive_tissue_lignin": [0.01, 0.03, 0.04, 0.02],
        "root_lignin": [0.2, 0.35, 0.27, 0.4],
        "plant_reproductive_tissue_turnover_c_n_ratio": [12.5, 23.8, 15.7, 18.2],
        "plant_reproductive_tissue_turnover_c_p_ratio": [125.5, 105.0, 145.0, 189.2],
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

    # Stoichiometric variables
    data["litter_pool_above_metabolic_cnp"] = DataArray(
        data=np.stack(
            [
                [0.319785, 0.161631, 0.086129, 0.093456],
                [0.0438062, 0.0185783, 0.0085276, 0.0095363],
                [0.00558089, 0.00235271, 0.00086043, 0.00097553],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_pool_above_structural_cnp"] = DataArray(
        data=np.stack(
            [
                [0.52097, 0.26609, 0.10019, 0.09988],
                [0.0138925, 0.0061595, 0.0021876, 0.0019896],
                [0.00154361, 0.00056232, 0.00024096, 0.00017517],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_pool_woody_cnp"] = DataArray(
        data=np.stack(
            [
                [5.1773833, 12.185701, 7.673456, 7.462192],
                [0.0932862, 0.1925071, 0.1622295, 0.1262638],
                [0.00932022, 0.01596450, 0.00905636, 0.01245567],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_pool_below_metabolic_cnp"] = DataArray(
        data=np.stack(
            [
                [0.410373, 0.375794, 0.080181, 0.083494],
                [0.0383526, 0.0332561, 0.0052751, 0.0067334],
                [0.0013208014, 0.0009136737, 0.0002543813, 0.0002024588],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_pool_below_structural_cnp"] = DataArray(
        data=np.stack(
            [
                [0.613547, 0.321674, 0.032738, 0.029168],
                [0.0121494, 0.0057855, 0.0004479, 0.0004766],
                [0.00111453, 0.00054008, 4.23464e-5, 4.47912e-5],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_consumed_above_metabolic_cnp"] = DataArray(
        data=np.stack(
            [
                [160.2585, 94.2111, 130.6449, 189.9936],
                [21.953187, 10.82727, 12.935133, 19.387107],
                [2.7968328, 1.3713381, 1.3051449, 1.9832283],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_consumed_above_structural_cnp"] = DataArray(
        data=np.stack(
            [
                [169.857, 130.329, 82.539, 80.028],
                [4.52952, 3.0168774, 1.8021609, 1.5941853],
                [0.5032799973, 0.2754205416, 0.1985064975, 0.1403507574],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_consumed_woody_cnp"] = DataArray(
        data=np.stack(
            [
                [3866.80473, 3124.1781, 3024.9936, 1313.7552],
                [69.67215, 49.35492, 63.95355, 22.22964],
                [6.9609456, 4.0929867, 3.570156, 2.1928806],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_consumed_below_metabolic_cnp"] = DataArray(
        data=np.stack(
            [
                [84.0213, 46.9314, 82.4661, 109.3014],
                [7.852464, 4.153194, 5.42538, 8.814663],
                [0.27042579, 0.1141047, 0.26163081, 0.26503767],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["litter_consumed_below_structural_cnp"] = DataArray(
        data=np.stack(
            [
                [109.7307, 94.5594, 103.1778, 74.2608],
                [2.1728817, 1.7007084, 1.4114574, 1.2134124],
                [0.199329174, 0.15876324, 0.133459812, 0.114036822],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["stem_turnover_cnp"] = DataArray(
        data=[
            [607.5, 10.00823, 0.70928196],
            [801.9, 13.84974, 1.187296],
            [510.3, 6.98085, 0.546828],
            [267.3, 4.85118, 0.3007426],
        ],
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["root_turnover_cnp"] = DataArray(
        data=[
            [218.7, 7.2178, 0.333029],
            [170.1, 3.73026, 0.377497],
            [2.43, 0.05612, 0.0055568],
            [201.69, 5.43639, 0.5423232],
        ],
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["foliage_turnover_cnp"] = DataArray(
        data=[
            [218.7, 14.58, 0.52698795],
            [2.43, 0.09529412, 0.00742211],
            [170.1, 3.94663573, 0.3067628],
            [230.85, 4.021777, 0.6060646],
        ],
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["herbivory_waste_leaf_cnp"] = DataArray(
        data=[
            [0.243, 0.010519, 0.00114353],
            [17.01, 0.507761, 0.0493329],
            [
                23.085,
                0.999351,
                0.0689516,
            ],
            [21.87, 1.264162, 0.052059],
        ],
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

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
        "air_temperature_ref": 30.0,  # °C
        "wind_speed_ref": 1.0,  # m s-1
        "relative_humidity_ref": 90.0,  # %
        "vapour_pressure_deficit_ref": 0.14,  # kPa
        "vapour_pressure_ref": 3.7,  # kPa (consistent with 30C, 90% RH)
        "atmospheric_pressure_ref": 96.0,  # kPa
        "atmospheric_co2_ref": 400.0,  # ppm
        "precipitation": 200.0,  # mm month-1
        "downward_shortwave_radiation": 220.0,  # W m-2 (24h monthly mean)
        "downward_longwave_radiation": 400.0,  # W m-2 (24h monthly mean)
    }

    for var, value in ref_values.items():
        data[var] = DataArray(
            np.full((4, 3), value),
            dims=["cell_id", "time_index"],
        )

    # Spatially varying but not vertically structured
    spatially_variable = {
        "shortwave_radiation_surface": [120, 80, 30, 10],  # W m-2
        "friction_velocity": [0.35, 0.25, 0.15, 0.15],  # m s-1
        "soil_evaporation": [30.0, 40.0, 60.0, 60.0],  # mm month-1
        "elevation": [200, 100, 10, 10],  # m
    }
    for var, vals in spatially_variable.items():
        data[var] = DataArray(vals, dims=["cell_id"])

    # Spatially constant and not vertically structured
    spatially_constant = {
        "sensible_heat_flux_soil": 20.0,  # W m-2
        "latent_heat_flux_soil": 40.0,  # W m-2
        "zero_plane_displacement": 20.0,  # m
        "mean_mixing_length": 1.3,  # m
        "aerodynamic_resistance_soil": 50.0,  # s m-1
        "aerodynamic_resistance_canopy": 30.0,  # s m-1
        "mean_annual_temperature": 20.0,  # C
        "ground_heat_flux": 20.0,
        "conductive_flux_understorey": 50.0,
    }
    for var, val in spatially_constant.items():
        data[var] = DataArray(np.repeat(val, 4), dims=["cell_id"])

    # Structural variables - assign values to vertical layer indices across grid id
    data["leaf_area_index"] = from_template()
    data["leaf_area_index"][lyr_str.index_filled_canopy] = 1.0
    data["leaf_area_index"][lyr_str.index_surface_scalar] = 1.0

    data["layer_heights"] = from_template()
    data["layer_heights"][lyr_str.index_filled_atmosphere] = np.array(
        [32.0, 30.0, 20.0, 10.0, lyr_str.surface_layer_height]
    )[:, None]

    data["layer_heights"][lyr_str.index_all_soil] = lyr_str.soil_layer_depths[:, None]

    # Microclimate and energy balance
    # - Vertically structured
    data["wind_speed"] = from_template()
    data["wind_speed"][lyr_str.index_filled_atmosphere] = 0.1

    data["atmospheric_pressure"] = from_template()
    data["atmospheric_pressure"][lyr_str.index_filled_atmosphere] = 96.0

    data["air_temperature"] = from_template()
    data["air_temperature"][lyr_str.index_filled_atmosphere] = np.array(
        [30.0, 29.8, 28.9, 27.2, 22.0]
    )[:, None]

    data["soil_temperature"] = from_template()
    data["soil_temperature"][lyr_str.index_all_soil] = 20.0

    data["matric_potential"] = from_template()
    data["matric_potential"][lyr_str.index_all_soil] = np.array(
        [[-3.0, -10.0, -250.0, -10000.0], [-3.0, -10.0, -250.0, -10000.0]]
    )

    data["relative_humidity"] = from_template()
    data["relative_humidity"][lyr_str.index_filled_atmosphere] = np.array(
        [90.0, 91.0, 93.0, 96.0, 98.0]
    )[:, None]

    data["vapour_pressure"] = from_template()
    data["vapour_pressure"][lyr_str.index_filled_atmosphere] = np.array(
        [3.82, 3.82, 3.70, 3.46, 2.59]
    )[:, None]

    data["vapour_pressure_deficit"] = from_template()
    data["vapour_pressure_deficit"][lyr_str.index_filled_atmosphere] = np.array(
        [0.42, 0.37, 0.27, 0.14, 0.05]
    )[:, None]

    data["shortwave_absorption"] = from_template()
    data["shortwave_absorption"][lyr_str.index_flux_layers] = 180.0

    data["longwave_emission"] = from_template()
    data["longwave_emission"][lyr_str.index_flux_layers] = 450.0

    data["sensible_heat_flux"] = from_template()
    data["sensible_heat_flux"][lyr_str.index_flux_layers] = 20.0

    data["latent_heat_flux"] = from_template()
    data["latent_heat_flux"][lyr_str.index_flux_layers] = 40.0

    data["net_radiation"] = from_template()
    data["net_radiation"][lyr_str.index_flux_layers] = 20.0

    data["molar_density_air"] = from_template()
    data["molar_density_air"][lyr_str.index_filled_atmosphere] = 38.0

    data["density_air"] = from_template()
    data["density_air"][lyr_str.index_filled_atmosphere] = 1.255

    data["specific_heat_air"] = from_template()
    data["specific_heat_air"][lyr_str.index_filled_atmosphere] = 1006.0

    data["latent_heat_vapourisation"] = from_template()
    data["latent_heat_vapourisation"][lyr_str.index_filled_atmosphere] = 2442.0

    data["canopy_temperature"] = from_template()
    data["canopy_temperature"][lyr_str.index_filled_canopy] = np.array(
        [29.8, 28.9, 27.2]
    )[:, None]
    data["canopy_temperature"][lyr_str.index_surface_scalar] = 22.0

    data["canopy_evaporation"] = from_template()
    data["canopy_evaporation"][lyr_str.index_filled_canopy] = 40.0
    data["canopy_evaporation"][lyr_str.index_surface_scalar] = 40.0

    data["stomatal_conductance"] = from_template()
    data["stomatal_conductance"][lyr_str.index_filled_canopy] = 12.0
    data["stomatal_conductance"][lyr_str.index_surface_scalar] = 12.0

    # Hydrology
    data["transpiration"] = from_template()
    data["transpiration"][lyr_str.index_filled_canopy] = 80.0
    data["transpiration"][lyr_str.index_surface_scalar] = 80.0

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
        [0.3, 0.3, 0.3, np.nan],
        [0.25, 0.25, np.nan, np.nan],
        [0.1, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["air_temperature"][index_filled_canopy] = [
        [29.8, 29.8, 29.8, np.nan],
        [28.9, 28.9, np.nan, np.nan],
        [27.2, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_humidity"][index_filled_canopy] = [
        [91.0, 91.0, 91.0, np.nan],
        [93.0, 93.0, np.nan, np.nan],
        [96.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["shortwave_absorption"][index_filled_canopy] = [
        [180.0, 180.0, 180.0, np.nan],
        [160.0, 160.0, np.nan, np.nan],
        [120.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["longwave_emission"][index_filled_canopy] = [
        [450.0, 450.0, 450.0, np.nan],
        [450.0, 450.0, np.nan, np.nan],
        [450.0, np.nan, np.nan, np.nan],
    ]
    dummy_climate_data["vapour_pressure"][index_filled_atmosphere] = [
        [3.82, 3.82, 3.82, 3.82],
        [3.82, 3.82, 3.82, np.nan],
        [3.7, 3.7, np.nan, np.nan],
        [3.46, np.nan, np.nan, np.nan],
        [2.59, 2.59, 2.59, 2.59],
    ]
    dummy_climate_data["vapour_pressure_deficit"][index_filled_atmosphere] = [
        [0.42, 0.42, 0.42, 0.42],
        [0.37, 0.37, 0.37, np.nan],
        [0.27, 0.27, np.nan, np.nan],
        [0.14, np.nan, np.nan, np.nan],
        [0.05, 0.05, 0.05, 0.05],
    ]
    dummy_climate_data["sensible_heat_flux"][index_filled_canopy] = [
        [25.0, 25.0, 25.0, np.nan],
        [20.0, 20.0, np.nan, np.nan],
        [15.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["latent_heat_flux"][index_filled_canopy] = [
        [45.0, 45.0, 45.0, np.nan],
        [40.0, 40.0, np.nan, np.nan],
        [30.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["net_radiation"][lyr_str.index_filled_canopy] = [
        [70.0, 70.0, 70.0, np.nan],
        [60.0, 60.0, np.nan, np.nan],
        [45.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["canopy_temperature"][index_filled_canopy] = [
        [29.8, 29.8, 29.8, np.nan],
        [28.9, 28.9, np.nan, np.nan],
        [27.2, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["canopy_evaporation"][index_filled_canopy] = [
        [40.0, 40.0, 40.0, np.nan],
        [30.0, 30.0, np.nan, np.nan],
        [20.0, np.nan, np.nan, np.nan],
    ]
    dummy_climate_data["canopy_evaporation"][lyr_str.index_surface_scalar] = 20.0

    dummy_climate_data["stomatal_conductance"][index_filled_canopy] = [
        [15.0, 15.0, 15.0, np.nan],
        [15.0, 15.0, np.nan, np.nan],
        [15.0, np.nan, np.nan, np.nan],
    ]

    # Hydrology
    dummy_climate_data["transpiration"][index_filled_canopy] = [
        [30.0, 30.0, 30.0, np.nan],
        [20.0, 20.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
    ]
    dummy_climate_data["transpiration"][lyr_str.index_surface_scalar] = 20.0

    return dummy_climate_data


@pytest.fixture
def fixture_abiotic_indices(
    dummy_climate_data_varying_canopy, fixture_core_components
) -> SimpleNamespace:
    """Build indices for different layers and variables for easier access."""

    layer_structure = fixture_core_components.layer_structure
    data = dummy_climate_data_varying_canopy

    return SimpleNamespace(
        above=layer_structure.index_above,
        canopy=layer_structure.index_filled_canopy,
        surface=layer_structure.index_surface_scalar,
        atm=layer_structure.index_filled_atmosphere,
        flux=layer_structure.index_flux_layers,
        soil=layer_structure.index_all_soil,
        topsoil=layer_structure.index_topsoil_scalar,
        layers=layer_structure.n_layers,
        cell_id=data.grid.n_cells,
    )


@pytest.fixture
def fixture_static_inputs(
    dummy_climate_data_varying_canopy,
    fixture_abiotic_indices,
    fixture_core_components,
    fixture_abiotic_constants,
) -> dict[str, NDArray[np.floating]]:
    """Prepare static inputs for microclimate model."""

    data = dummy_climate_data_varying_canopy
    indices = fixture_abiotic_indices
    layer_structure = fixture_core_components.layer_structure
    abiotic_constants = fixture_abiotic_constants
    time_index = 0

    canopy_height = np.nan_to_num(data["layer_heights"][1].to_numpy())

    leaf_area_index_sum = np.nan_to_num(
        np.nansum(data["leaf_area_index"][indices.canopy].to_numpy(), axis=0)
    )

    evapotranspiration = (data["canopy_evaporation"] + data["transpiration"]).to_numpy()

    atmospheric_pressure = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_pressure_ref"],
        time_index=time_index,
    )
    atmospheric_pressure_true = atmospheric_pressure.to_numpy()

    atmospheric_co2 = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_co2_ref"],
        time_index=time_index,
    )
    atmospheric_co2_true = atmospheric_co2.to_numpy()

    atmospheric_layer_geometry = abiotic_tools.calculate_atmospheric_layer_geometry(
        data=data,
        layer_structure=layer_structure,
    )

    # Absorbed longwave radiation by canopy, [W m-2]
    weights = compute_weights_from_absorbed_radiation(
        radiation=data["shortwave_absorption"].to_numpy(),
    )
    absorbed_longwave_radiation = (
        data["downward_longwave_radiation"].isel(time_index=time_index).to_numpy()
        * weights
        * abiotic_constants.leaf_emissivity  # TODO needs to be soil too
    )
    cell_area = data.grid.cell_area

    mixing_coefficient = fixture_core_components.layer_structure.from_template()
    mixing_coefficient[indices.atm] = np.array(
        [
            [0.1, 0.1, 0.1, 0.1],
            [0.1, 0.1, 0.1, np.nan],
            [0.1, 0.1, np.nan, np.nan],
            [0.1, np.nan, np.nan, np.nan],
            [0.1, 0.1, 0.1, 0.1],
        ]
    )
    zero_plane_displacement = np.ones(data.grid.n_cells) * 2.0
    ventilation_rate = np.ones(data.grid.n_cells) * 2.0
    wind_speed = data["wind_speed"].to_numpy()

    return {
        "canopy_height": canopy_height,
        "lai_sum": leaf_area_index_sum,
        "evapotranspiration": evapotranspiration,
        "atmospheric_pressure": atmospheric_pressure_true,
        "atmospheric_co2": atmospheric_co2_true,
        "geometry": atmospheric_layer_geometry,
        "absorbed_longwave_radiation": absorbed_longwave_radiation,
        "cell_area": cell_area,
        "mixing_coefficient": mixing_coefficient,
        "zero_plane_displacement": zero_plane_displacement,
        "wind_speed": wind_speed,
        "ventialtion_rate": ventilation_rate,
    }


@pytest.fixture
def fixture_state_inputs(
    dummy_climate_data_varying_canopy,
) -> dict[str, NDArray[np.floating]]:
    """Prepare static inputs for microclimate model."""

    data = dummy_climate_data_varying_canopy
    n_layers, n_cells = data["air_temperature"].shape

    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]

    return {
        "air_temperature": data["air_temperature"].to_numpy(),
        "relative_humidity": data["relative_humidity"].to_numpy(),
        "atmospheric_pressure": data["atmospheric_pressure"].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
        "canopy_temperature": data["canopy_temperature"].to_numpy(),
        "evapotranspiration": evapotranspiration.to_numpy(),
        "shortwave_absorption": data["shortwave_absorption"].to_numpy(),
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "aerodynamic_resistance_canopy": (
            data["aerodynamic_resistance_canopy"].to_numpy()
        ),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"].to_numpy(),
        "soil_temperature": data["soil_temperature"].to_numpy(),
        "soil_evaporation": data["soil_evaporation"].to_numpy(),
        "sensible_heat_flux": np.ones((n_layers, n_cells)) * 5.0,
        "sensible_heat_flux_soil": np.ones(n_cells) * 2.0,
        "latent_heat_flux": np.ones((n_layers, n_cells)) * 5.0,
        "latent_heat_flux_soil": np.ones(n_cells) * 2.0,
        "ground_heat_flux": np.ones(n_cells) * 2.0,
        "ventilation_rate": np.repeat(0.05, n_cells),
        "longwave_emission": data["longwave_emission"].to_numpy(),
    }
