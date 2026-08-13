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
from virtual_ecosystem.models.abiotic.abiotic_tools import (
    compute_weights_from_absorbed_radiation,
)

# Class uses DEBUG
LOGGER.setLevel(DEBUG)


def log_check(
    caplog: pytest.LogCaptureFixture,
    expected_log: tuple[tuple],
    subset: slice | None = None,
    match_message_start: bool = False,
) -> None:
    """Helper function to check that the captured log is as expected.

    Arguments:
        caplog: An instance of the caplog fixture
        expected_log: An iterable of 2-tuples containing the log level and message.
        subset: Only check a specified subset of the captured log.
        match_message_start: Allow log matching to only match the start of the expected
            message to allow for appended log information.
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

    if match_message_start:
        assert all(
            [
                rec.message.startswith(exp[1])
                for exp, rec in zip(expected_log, captured_records)
            ]
        )
    else:
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


@pytest.fixture(autouse=True)
def reset_disturbance_registry():
    """Reset the disturbance registry.

    The register_disturbance function updates the DISTURBANCE_REGISTRY, which persists
    between tests. This autouse fixture is used to ensure that the registry is always
    cleared before tests start, so that the correct registration of disturbances within
    tests is enforced.
    """
    from virtual_ecosystem.core.registry import DISTURBANCE_REGISTRY

    DISTURBANCE_REGISTRY.clear()


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
        "subcanopy_vegetation_litter_lignin": [0.05, 0.43, 0.84, 0.01],
        "plant_reproductive_tissue_turnover_c_n_ratio": [12.5, 23.8, 15.7, 18.2],
        "plant_reproductive_tissue_turnover_c_p_ratio": [125.5, 105.0, 145.0, 189.2],
        "herbivory_waste_above_lignin": [0.13, 0.08, 0.27, 0.22],
        "herbivory_waste_below_lignin": [0.33, 0.089, 0.46, 0.35],
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
        [
            30.0,
            29.844995,
            28.87117,
            27.206405,
            16.145945,
        ]
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
        data=np.stack(
            [
                [607.5, 801.9, 510.3, 267.3],
                [10.00823, 13.84974, 6.98085, 4.85118],
                [0.70928196, 1.187296, 0.546828, 0.3007426],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["root_turnover_cnp"] = DataArray(
        data=np.stack(
            [
                [218.7, 170.1, 2.43, 201.69],
                [7.2178, 3.73026, 0.05612, 5.43639],
                [0.333029, 0.377497, 0.0055568, 0.5423232],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )
    data["subcanopy_vegetation_litter_cnp"] = DataArray(
        data=np.stack(
            [
                [1.771, 5.296, 0.0392, 11.652],
                [0.6592, 0.3446, 0.001371, 0.1192],
                [0.005292, 0.02255, 2.843e-5, 0.02516],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    # Split the foliage turnover 80/20 between two PFTs to give the expected
    # dimensionality
    total_foliage_turnover_cnp = np.stack(
        [
            [218.7, 2.43, 170.1, 230.85],
            [14.58, 0.09529412, 3.94663573, 4.021777],
            [0.52698795, 0.00742211, 0.3067628, 0.6060646],
        ],
        axis=1,
    )

    data["foliage_turnover_cnp"] = DataArray(
        data=np.stack(
            [total_foliage_turnover_cnp * 0.8, total_foliage_turnover_cnp * 0.2], axis=1
        ),
        coords={
            "cell_id": data["cell_id"],
            "pft": ["broadleaf", "shrub"],
            "element": ["C", "N", "P"],
        },
    )

    data["herbivory_waste_above_cnp"] = DataArray(
        data=np.stack(
            [
                [0.243, 17.01, 23.085, 21.87],
                [0.010519, 0.507761, 0.999351, 1.264162],
                [0.00114353, 0.0493329, 0.0689516, 0.052059],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["herbivory_waste_below_cnp"] = DataArray(
        data=np.stack(
            [
                [0.172, 9.022, 17.602, 2.547],
                [0.0059, 0.04534, 0.28681, 0.00532],
                [0.0001417, 0.021695, 0.058766, 0.031481],
            ],
            axis=1,
        ),
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    return data


@pytest.fixture
def dummy_climate_data(fixture_core_components):
    """Create a consistent dummy climate dataset for tests.

    Assumptions:
    - 4 grid cells
    - 1 above-canopy layer
    - 3 canopy layers
    - 1 vegetated surface layer
    - 2 soil layers

    All vertically structured variables share the same layer ordering and are
    populated through grouped update loops so values remain consistent across
    variables and easier to maintain.
    """

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # Shorten syntax
    lyr_str = fixture_core_components.layer_structure
    from_template = lyr_str.from_template

    n_cells = fixture_core_components.grid.n_cells
    time_steps = 3

    # Helper functions to fill profiles
    def repeat_profile(profile: list[float] | NDArray[np.floating]) -> np.ndarray:
        """Repeat a 1D vertical profile across all cells."""
        return np.repeat(np.asarray(profile, dtype=float)[:, None], n_cells, axis=1)

    def set_from_template(
        var: str,
        values: list[float] | NDArray[np.floating],
        layer_index,
    ) -> None:
        """Create a layer-structured variable and assign repeated values."""
        data[var] = from_template()
        data[var][layer_index] = repeat_profile(values)

    def set_from_template_with_surface(
        var: str,
        canopy_values: list[float] | NDArray[np.floating],
        surface_value: float,
    ) -> None:
        """Create a canopy variable and assign canopy plus surface values."""
        data[var] = from_template()
        data[var][lyr_str.index_filled_canopy] = repeat_profile(canopy_values)
        data[var][lyr_str.index_surface_scalar] = float(surface_value)

    # Time-varying reference meteorology
    reference_fields = {
        "air_temperature_ref": 23.0,
        "wind_speed_ref": 0.5,
        "relative_humidity_ref": 90.0,
        "vapour_pressure_deficit_ref": 0.14,
        "vapour_pressure_ref": 2.2,
        "atmospheric_pressure_ref": 96.0,
        "atmospheric_co2_ref": 400.0,
        "precipitation": 300.0,
        "downward_shortwave_radiation": 220.0,
        "downward_longwave_radiation": 400.0,
        "mean_annual_temperature": 22.0,
        "diurnal_temperature_range_ref": 6.0,
    }

    for var, value in reference_fields.items():
        data[var] = DataArray(
            np.full((n_cells, time_steps), value, dtype=float),
            dims=["cell_id", "time_index"],
        )

    # Spatially varying but not vertically structured
    cell_variable_fields = {
        "friction_velocity": [0.35, 0.25, 0.15, 0.15],
        "soil_evaporation": [5.0, 10.0, 12.0, 12.0],
        "elevation": [200.0, 100.0, 10.0, 10.0],
    }
    for var, values in cell_variable_fields.items():
        data[var] = DataArray(np.asarray(values, dtype=float), dims=["cell_id"])

    # Spatially constant and not vertically structured
    cell_constant_fields = {
        "sensible_heat_flux_soil": -5.0,
        "latent_heat_flux_soil": -5.0,
        "zero_plane_displacement": 20.0,
        "mean_mixing_length": 1.3,
        "aerodynamic_resistance_soil": 50.0,
        "aerodynamic_resistance_canopy": 400.0,
        "ground_heat_flux": -5.0,
        "ventilation_rate": 0.1,
    }
    for var, value in cell_constant_fields.items():
        data[var] = DataArray(np.full(n_cells, value, dtype=float), dims=["cell_id"])

    # Canonical profiles
    # Layer ordering:
    # - atmosphere-facing / flux layers: above, canopy_1, canopy_2, canopy_3, surface
    # - canopy-only layers: canopy_1, canopy_2, canopy_3
    # - soil layers: topsoil, subsoil
    atmosphere_profiles = {
        "layer_heights": [32.0, 30.0, 20.0, 10.0, 0.1],
        "wind_speed": [0.50, 0.25, 0.12, 0.06, 0.02],
        "mixing_coefficient": [0.15, 0.10, 0.08, 0.05, 0.03],
        "atmospheric_pressure": [96.0, 96.0, 96.1, 96.1, 96.2],
        "air_temperature": [22.0, 21.8, 20.6, 19.2, 18.5],
        "diurnal_temperature_range": [5.0, 4.0, 3.0, 2.0, 1.0],
        "relative_humidity": [90.0, 92.0, 94.0, 96.0, 99.0],
        "vapour_pressure": [2.20, 2.15, 2.05, 1.95, 1.85],
        "vapour_pressure_deficit": [0.60, 0.30, 0.18, 0.08, 0.01],
        "molar_density_air": [38.0, 38.2, 38.5, 38.7, 39.0],
        "density_air": [1.18, 1.19, 1.20, 1.22, 1.24],
        "specific_heat_air": [1006.0, 1006.0, 1006.0, 1006.0, 1006.0],
        "latent_heat_vapourisation": [2445.0, 2444.0, 2443.0, 2442.0, 2441.0],
    }

    flux_profiles = {
        "shortwave_absorption": [150.0, 10.0, 7.0, 3.0, 10.0],
        "absorbed_longwave_radiation": [180, 180, 180, 180, 180],
        "longwave_emission": [458.0, 453.0, 443.0, 413.0, 402.0],
        "sensible_heat_flux": [-12.0, -10.0, -8.0, -5.0, -3.0],
        "latent_heat_flux": [-8.0, -6.0, -5.0, -4.0, -2.0],
        "net_radiation": [35.0, 18.0, 10.0, 5.0, 2.0],
    }

    canopy_profiles = {
        "leaf_area_index": {
            "canopy": [4.4, 1.2, 0.5],
            "surface": 0.07,
        },
        "canopy_temperature": {
            "canopy": [29.8, 28.9, 27.2],
            "surface": 22.0,
        },
        "canopy_evaporation": {
            "canopy": [2.5, 2.0, 1.5],
            "surface": 1.0,
        },
        "stomatal_conductance": {
            "canopy": [15.0, 12.0, 9.0],
            "surface": 6.0,
        },
        "condensation": {
            "canopy": [0.5, 0.8, 1.0],
            "surface": 1.2,
        },
        "transpiration": {
            "canopy": [90.0, 70.0, 45.0],
            "surface": 20.0,
        },
    }

    soil_profiles = {
        "soil_temperature": [22.0, 20.0],
        "matric_potential": [-20.0, -100.0],
        "soil_moisture": [5.0, 500.0],
    }

    # Structural variables
    set_from_template(
        "layer_heights",
        atmosphere_profiles["layer_heights"],
        lyr_str.index_filled_atmosphere,
    )
    data["layer_heights"][lyr_str.index_all_soil] = repeat_profile(
        np.asarray(lyr_str.soil_layer_depths, dtype=float)
    )

    for var in (
        "wind_speed",
        "mixing_coefficient",
        "atmospheric_pressure",
        "air_temperature",
        "diurnal_temperature_range",
        "relative_humidity",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "molar_density_air",
        "density_air",
        "specific_heat_air",
        "latent_heat_vapourisation",
    ):
        set_from_template(
            var, atmosphere_profiles[var], lyr_str.index_filled_atmosphere
        )

    for var in (
        "shortwave_absorption",
        "longwave_emission",
        "sensible_heat_flux",
        "latent_heat_flux",
        "net_radiation",
    ):
        set_from_template(var, flux_profiles[var], lyr_str.index_flux_layers)

    for var, values in canopy_profiles.items():
        set_from_template_with_surface(
            var,
            canopy_values=values["canopy"],
            surface_value=values["surface"],
        )

    for var, values in soil_profiles.items():
        set_from_template(var, values, lyr_str.index_all_soil)

    # Hydrology
    data["groundwater_storage"] = DataArray(
        np.full((2, n_cells), 450.0, dtype=float),
        dims=("groundwater_layers", "cell_id"),
    )

    return data


@pytest.fixture
def dummy_climate_data_varying_canopy(fixture_core_components, dummy_climate_data):
    """Create dummy climate data with varying canopy occupancy by cell.

    The four cells have:
    - cell 0: 3 canopy layers + vegetated surface layer
    - cell 1: 2 canopy layers + vegetated surface layer
    - cell 2: 1 canopy layer + vegetated surface layer
    - cell 3: no canopy + vegetated surface layer

    All affected profile variables are updated consistently using shared masks and
    grouped loops.
    """

    lyr_str = fixture_core_components.layer_structure
    canopy_idx = lyr_str.index_filled_canopy
    atmosphere_idx = lyr_str.index_filled_atmosphere
    flux_idx = lyr_str.index_flux_layers
    surface_idx = lyr_str.index_surface_scalar

    canopy_present = np.array(
        [
            [True, True, True, False],
            [True, True, False, False],
            [True, False, False, False],
        ],
        dtype=bool,
    )
    surface_present = np.array([True, True, True, True], dtype=bool)

    filled_atmosphere_present = np.vstack(
        [
            np.ones((1, canopy_present.shape[1]), dtype=bool),
            canopy_present,
            surface_present[None, :],
        ]
    )

    atmosphere_profiles = {
        "layer_heights": [32.0, 30.0, 20.0, 10.0, lyr_str.surface_layer_height],
        "wind_speed": [0.50, 0.25, 0.12, 0.06, 0.02],
        "mixing_coefficient": [0.15, 0.10, 0.08, 0.05, 0.03],
        "atmospheric_pressure": [96.0, 96.0, 96.1, 96.1, 96.2],
        "air_temperature": [22.0, 21.8, 20.6, 19.2, 18.5],
        "diurnal_temperature_range": [5.0, 4.0, 3.0, 2.0, 1.0],
        "relative_humidity": [90.0, 92.0, 94.0, 96.0, 99.0],
        "vapour_pressure": [2.20, 2.15, 2.05, 1.95, 1.85],
        "vapour_pressure_deficit": [0.60, 0.30, 0.18, 0.08, 0.01],
        "molar_density_air": [38.0, 38.2, 38.5, 38.7, 39.0],
        "density_air": [1.18, 1.19, 1.20, 1.22, 1.24],
        "specific_heat_air": [1006.0, 1006.0, 1006.0, 1006.0, 1006.0],
        "latent_heat_vapourisation": [2445.0, 2444.0, 2443.0, 2442.0, 2441.0],
    }

    flux_profiles = {
        "shortwave_absorption": [150.0, 10.0, 7.0, 3.0, 10.0],
        "absorbed_longwave_radiation": [180, 180, 180, 180, 180],
        "longwave_emission": [458.0, 453.0, 443.0, 413.0, 402.0],
        "sensible_heat_flux": [-12.0, -10.0, -8.0, -5.0, -3.0],
        "latent_heat_flux": [-8.0, -6.0, -5.0, -4.0, -2.0],
        "net_radiation": [35.0, 18.0, 10.0, 5.0, 2.0],
    }

    canopy_profiles = {
        "leaf_area_index": {
            "canopy": [4.4, 1.2, 0.5],
            "surface": 0.07,
        },
        "canopy_temperature": {
            "canopy": [29.8, 28.9, 27.2],
            "surface": 22.0,
        },
        "canopy_evaporation": {
            "canopy": [2.5, 2.0, 1.5],
            "surface": 1.0,
        },
        "stomatal_conductance": {
            "canopy": [15.0, 12.0, 9.0],
            "surface": 6.0,
        },
        "condensation": {
            "canopy": [0.5, 0.8, 1.0],
            "surface": 1.2,
        },
        "transpiration": {
            "canopy": [90.0, 70.0, 45.0],
            "surface": 20.0,
        },
    }

    def masked_profile(
        values: list[float] | NDArray[np.floating], mask: np.ndarray
    ) -> np.ndarray:
        profile = np.asarray(values, dtype=float)[:, None]
        return np.where(mask, profile, np.nan)

    # Structural variables
    dummy_climate_data["layer_heights"][atmosphere_idx] = masked_profile(
        atmosphere_profiles["layer_heights"],
        filled_atmosphere_present,
    )

    # Atmosphere-facing variables
    for var in (
        "wind_speed",
        "mixing_coefficient",
        "atmospheric_pressure",
        "air_temperature",
        "diurnal_temperature_range",
        "relative_humidity",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "molar_density_air",
        "density_air",
        "specific_heat_air",
        "latent_heat_vapourisation",
    ):
        dummy_climate_data[var][atmosphere_idx] = masked_profile(
            atmosphere_profiles[var],
            filled_atmosphere_present,
        )

    # Flux variables
    for var in (
        "shortwave_absorption",
        "absorbed_longwave_radiation",
        "longwave_emission",
        "sensible_heat_flux",
        "latent_heat_flux",
        "net_radiation",
    ):
        dummy_climate_data[var][flux_idx] = masked_profile(
            flux_profiles[var],
            filled_atmosphere_present,
        )

    # Canopy-only + surface variables
    for var, values in canopy_profiles.items():
        dummy_climate_data[var][canopy_idx] = masked_profile(
            values["canopy"], canopy_present
        )
        dummy_climate_data[var][surface_idx] = float(values["surface"])

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
    """Prepare static inputs for the microclimate model."""

    data = dummy_climate_data_varying_canopy
    indices = fixture_abiotic_indices
    layer_structure = fixture_core_components.layer_structure
    abiotic_constants = fixture_abiotic_constants
    time_index = 0
    hours = 30 * 24

    canopy_height = np.nan_to_num(data["layer_heights"][1].to_numpy())
    leaf_area_index = data["leaf_area_index"].to_numpy()
    leaf_area_index_sum = np.nan_to_num(
        np.nansum(leaf_area_index[indices.canopy], axis=0)
    )

    evapotranspiration = (
        data["canopy_evaporation"].to_numpy() + data["transpiration"].to_numpy()
    ) / hours

    atmospheric_pressure = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_pressure_ref"],
        time_index=time_index,
    ).to_numpy()

    atmospheric_co2 = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_co2_ref"],
        time_index=time_index,
    ).to_numpy()

    atmospheric_layer_geometry = abiotic_tools.calculate_atmospheric_layer_geometry(
        data=data,
        idx=indices,
        minimum_mixing_depth=abiotic_constants.minimum_mixing_depth,
    )

    weights = compute_weights_from_absorbed_radiation(
        radiation=data["shortwave_absorption"].to_numpy(),
    )
    absorbed_longwave_radiation = (
        data["downward_longwave_radiation"].isel(time_index=time_index).to_numpy()
        * weights
        * abiotic_constants.leaf_emissivity
    )

    return {
        "canopy_height": canopy_height,
        "leaf_area_index": leaf_area_index,
        "lai_sum": leaf_area_index_sum,
        "evapotranspiration": evapotranspiration,
        "atmospheric_pressure": atmospheric_pressure,
        "atmospheric_co2": atmospheric_co2,
        "geometry": atmospheric_layer_geometry,
        "absorbed_longwave_radiation": absorbed_longwave_radiation,
        "cell_area": data.grid.cell_area,
        "mixing_coefficient": data["mixing_coefficient"].to_numpy(),
        "zero_plane_displacement": data["zero_plane_displacement"].to_numpy(),
        "wind_speed": data["wind_speed"].to_numpy(),
        "ventilation_rate": data["ventilation_rate"].to_numpy(),
        "roughness_length": np.ones(data.grid.n_cells, dtype=float),
    }


@pytest.fixture
def fixture_state_inputs(
    dummy_climate_data_varying_canopy,
) -> dict[str, NDArray[np.floating]]:
    """Prepare state inputs for the microclimate model."""

    data = dummy_climate_data_varying_canopy
    hours = 30 * 24

    evapotranspiration = (
        data["canopy_evaporation"].to_numpy() + data["transpiration"].to_numpy()
    ) / hours

    return {
        "air_temperature": data["air_temperature"].to_numpy(),
        "relative_humidity": data["relative_humidity"].to_numpy(),
        "atmospheric_pressure": data["atmospheric_pressure"].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
        "canopy_temperature": data["canopy_temperature"].to_numpy(),
        "evapotranspiration": evapotranspiration,
        "shortwave_absorption": data["shortwave_absorption"].to_numpy(),
        "specific_heat_air": data["specific_heat_air"].to_numpy(),
        "density_air": data["density_air"].to_numpy(),
        "aerodynamic_resistance_canopy": data[
            "aerodynamic_resistance_canopy"
        ].to_numpy(),
        "latent_heat_vapourisation": data["latent_heat_vapourisation"].to_numpy(),
        "soil_temperature": data["soil_temperature"].to_numpy(),
        "soil_evaporation": data["soil_evaporation"].to_numpy() / hours,
        "sensible_heat_flux": np.nan_to_num(
            data["sensible_heat_flux"].to_numpy(),
            nan=0.0,
        ),
        "sensible_heat_flux_soil": data["sensible_heat_flux_soil"].to_numpy(),
        "latent_heat_flux": np.nan_to_num(
            data["latent_heat_flux"].to_numpy(),
            nan=0.0,
        ),
        "latent_heat_flux_soil": data["latent_heat_flux_soil"].to_numpy(),
        "ground_heat_flux": data["ground_heat_flux"].to_numpy(),
        "ventilation_rate": data["ventilation_rate"].to_numpy(),
        "longwave_emission": data["longwave_emission"].to_numpy(),
    }
