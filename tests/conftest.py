"""Collection of fixtures to assist the testing scripts."""

from logging import DEBUG

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
def fixture_config():
    """Simple configuration fixture for use in tests."""

    from virtual_ecosystem.core.config import Config

    cfg_string = """
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
        a_plant_integer = 12
        [[plants.ftypes]]
        pft_name = "shrub"
        max_height = 1.0
        [[plants.ftypes]]
        pft_name = "broadleaf"
        max_height = 50.0

    [[animal.functional_groups]]
    name = "carnivorous_bird"
    taxa = "bird"
    diet = "carnivore"
    metabolic_type = "endothermic"
    reproductive_type = "iteroparous"
    development_type = "direct"
    development_status = "adult"
    offspring_functional_group = "carnivorous_bird"
    excretion_typ = "uricotelic"
    birth_mass = 0.1
    adult_mass = 1.0
    [[animal.functional_groups]]
    name = "herbivorous_bird"
    taxa = "bird"
    diet = "herbivore"
    metabolic_type = "endothermic"
    reproductive_type = "iteroparous"
    development_type = "direct"
    development_status = "adult"
    offspring_functional_group = "herbivorous_bird"
    excretion_typ = "uricotelic"
    birth_mass = 0.05
    adult_mass = 0.5
    [[animal.functional_groups]]
    name = "carnivorous_mammal"
    taxa = "mammal"
    diet = "carnivore"
    metabolic_type = "endothermic"
    reproductive_type = "iteroparous"
    development_type = "direct"
    development_status = "adult"
    offspring_functional_group = "carnivorous_mammal"
    excretion_typ = "ureotelic"
    birth_mass = 4.0
    adult_mass = 40.0
    [[animal.functional_groups]]
    name = "herbivorous_mammal"
    taxa = "mammal"
    diet = "herbivore"
    metabolic_type = "endothermic"
    reproductive_type = "iteroparous"
    development_type = "direct"
    development_status = "adult"
    offspring_functional_group = "herbivorous_mammal"
    excretion_typ = "ureotelic"
    birth_mass = 1.0
    adult_mass = 10.0
    [[animal.functional_groups]]
    name = "carnivorous_insect"
    taxa = "insect"
    diet = "carnivore"
    metabolic_type = "ectothermic"
    reproductive_type = "iteroparous"
    development_type = "direct"
    development_status = "adult"
    offspring_functional_group = "carnivorous_insect"
    excretion_typ = "uricotelic"
    birth_mass = 0.001
    adult_mass = 0.01
    [[animal.functional_groups]]
    name = "herbivorous_insect"
    taxa = "insect"
    diet = "herbivore"
    metabolic_type = "ectothermic"
    reproductive_type = "semelparous"
    development_type = "direct"
    development_status = "adult"
    offspring_functional_group = "herbivorous_insect"
    excretion_typ = "uricotelic"
    birth_mass = 0.0005
    adult_mass = 0.005
    [[animal.functional_groups]]
    name = "butterfly"
    taxa = "insect"
    diet = "herbivore"
    metabolic_type = "ectothermic"
    reproductive_type = "semelparous"
    development_type = "indirect"
    development_status = "adult"
    offspring_functional_group = "caterpillar"
    excretion_typ = "uricotelic"
    birth_mass = 0.0005
    adult_mass = 0.005
    [[animal.functional_groups]]
    name = "caterpillar"
    taxa = "insect"
    diet = "herbivore"
    metabolic_type = "ectothermic"
    reproductive_type = "nonreproductive"
    development_type = "indirect"
    development_status = "larval"
    offspring_functional_group = "butterfly"
    excretion_typ = "uricotelic"
    birth_mass = 0.0005
    adult_mass = 0.005

        [hydrology]
    """

    return Config(cfg_strings=cfg_string)


@pytest.fixture
def fixture_core_components(fixture_config):
    """A CoreComponents instance for use in testing."""
    from virtual_ecosystem.core.core_components import CoreComponents

    return CoreComponents(fixture_config)


@pytest.fixture
def dummy_carbon_data(fixture_core_components):
    """Creates a dummy carbon data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # The required data is now added. This includes the four carbon pools: mineral
    # associated organic matter, low molecular weight carbon, microbial carbon and
    # particulate organic matter. It also includes various factors of the physical
    # environment: pH, bulk density, soil moisture, soil temperature, percentage clay in
    # soil.
    data_values = {
        "soil_c_pool_lmwc": [0.05, 0.02, 0.1, 0.005],
        "soil_c_pool_maom": [2.5, 1.7, 4.5, 0.5],
        "soil_c_pool_microbe": [5.8, 2.3, 11.3, 1.0],
        "soil_c_pool_pom": [0.1, 1.0, 0.7, 0.35],
        "soil_enzyme_pom": [0.022679, 0.009576, 0.050051, 0.003010],
        "soil_enzyme_maom": [0.0356, 0.0117, 0.02509, 0.00456],
        "pH": [3.0, 7.5, 9.0, 5.7],
        "bulk_density": [1350.0, 1800.0, 1000.0, 1500.0],
        "clay_fraction": [0.8, 0.3, 0.1, 0.9],
        "litter_C_mineralisation_rate": [0.00212106, 0.00106053, 0.00049000, 0.0055],
        "vertical_flow": [0.1, 0.5, 2.5, 1.59],
    }

    for var_name, var_values in data_values.items():
        data[var_name] = DataArray(var_values, dims=["cell_id"])

    # The layer dependant data has to be handled separately - at present all of these
    # are defined only for the topsoil layer
    data["soil_moisture"] = fixture_core_components.layer_structure.from_template()
    data["soil_moisture"].loc[
        {"layers": fixture_core_components.layer_structure.role_indices["topsoil"]}
    ] = [232.61550125, 196.88733175, 126.065797, 75.63195175]

    data["matric_potential"] = fixture_core_components.layer_structure.from_template()
    data["matric_potential"].loc[
        {"layers": fixture_core_components.layer_structure.role_indices["topsoil"]}
    ] = [-3.0, -10.0, -250.0, -10000.0]

    data["soil_temperature"] = fixture_core_components.layer_structure.from_template()
    data["soil_temperature"].loc[
        {"layers": fixture_core_components.layer_structure.role_indices["topsoil"]}
    ] = [35.0, 37.5, 40.0, 25.0]
    data["soil_temperature"].loc[
        {"layers": fixture_core_components.layer_structure.role_indices["subsoil"]}
    ] = [22.5, 22.5, 22.5, 22.5]

    return data


@pytest.fixture
def top_soil_layer_index(fixture_core_components):
    """The index of the top soil layer in the data fixtures.

    Convert from array to scalar using item.
    """
    return fixture_core_components.layer_structure.role_indices["topsoil"].item()


@pytest.fixture
def surface_layer_index(fixture_core_components):
    """The index of the top soil layer in the data fixtures.

    Convert from array to scalar using item.
    """
    return fixture_core_components.layer_structure.role_indices["surface"].item()


@pytest.fixture
def dummy_climate_data(fixture_core_components):
    """Creates a dummy climate data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # Shorten syntax to function
    from_template = fixture_core_components.layer_structure.from_template

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
        "topofcanopy_radiation": 100.0,
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
        "surface_runoff": [10, 50, 100, 100],
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
        "zero_displacement_height": 20.0,
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
    data["leaf_area_index"][[1, 2, 3]] = 1.0

    data["canopy_absorption"] = from_template()
    data["canopy_absorption"][[1, 2, 3]] = 1.0

    data["layer_heights"] = from_template()
    data["layer_heights"][[0, 1, 2, 3, 11, 12, 13]] = np.concatenate(
        [
            [32.0, 30.0, 20.0, 10.0],
            [fixture_core_components.layer_structure.surface_layer_height],
            fixture_core_components.layer_structure.soil_layers,
        ]
    )[:, None]

    # Microclimate and energy balance
    # - Vertically structured
    data["wind_speed"] = from_template()
    data["wind_speed"][[0, 1, 2, 3, 11]] = 0.1

    data["atmospheric_pressure"] = from_template()
    data["atmospheric_pressure"][[0, 1, 2, 3, 11]] = 96.0

    data["air_temperature"] = from_template()
    data["air_temperature"][[0, 1, 2, 3, 11]] = np.array(
        [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    )[:, None]

    data["soil_temperature"] = from_template()
    data["soil_temperature"][[12, 13]] = 20.0

    data["relative_humidity"] = from_template()
    data["relative_humidity"][[0, 1, 2, 3, 11]] = np.array(
        [90.0, 90.341644, 92.488034, 96.157312, 100]
    )[:, None]

    data["absorbed_radiation"] = from_template()
    data["absorbed_radiation"][[1, 2, 3]] = 10.0

    data["sensible_heat_flux"] = from_template()
    data["sensible_heat_flux"][[0, 1, 2, 3, 12]] = 0.0

    data["latent_heat_flux"] = from_template()
    data["latent_heat_flux"][[0, 1, 2, 3, 12]] = 0.0

    data["molar_density_air"] = from_template()
    data["molar_density_air"][[0, 1, 2, 3, 11]] = 38.0

    data["specific_heat_air"] = from_template()
    data["specific_heat_air"][[0, 1, 2, 3, 11]] = 29.0

    data["attenuation_coefficient"] = from_template()
    data["attenuation_coefficient"][[0, 1, 2, 3, 11]] = np.array(
        [13.0, 13.0, 13.0, 13.0, 2.0]
    )[:, None]

    data["relative_turbulence_intensity"] = from_template()
    data["relative_turbulence_intensity"][[0, 1, 2, 3, 11]] = np.array(
        [17.64, 16.56, 11.16, 5.76, 0.414]
    )[:, None]

    data["latent_heat_vapourisation"] = from_template()
    data["latent_heat_vapourisation"][[0, 1, 2, 3, 11]] = 2254.0

    data["canopy_temperature"] = from_template()
    data["canopy_temperature"][[1, 2, 3]] = 25.0

    data["leaf_air_heat_conductivity"] = from_template()
    data["leaf_air_heat_conductivity"][[1, 2, 3]] = 0.13

    data["leaf_vapour_conductivity"] = from_template()
    data["leaf_vapour_conductivity"][[1, 2, 3]] = 0.2

    data["conductivity_from_ref_height"] = from_template()
    data["conductivity_from_ref_height"][[1, 2, 3, 11]] = 3.0

    data["stomatal_conductance"] = from_template()
    data["stomatal_conductance"][[1, 2, 3]] = 15.0

    # Hydrology
    data["evapotranspiration"] = from_template()
    data["evapotranspiration"][[1, 2, 3]] = 20.0

    data["soil_moisture"] = from_template()
    data["soil_moisture"][[12, 13]] = np.array([5.0, 500.0])[:, None]

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
    number of canopy layers within the different cells.
    """

    # Structural variables
    dummy_climate_data["leaf_area_index"][[1, 2, 3], :] = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, np.nan, np.nan],
        [1.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["layer_heights"][[1, 2, 3], :] = [
        [30.0, 30.0, 30.0, 30.0],
        [20.0, 20.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
    ]

    # Microclimate and energy balance
    dummy_climate_data["wind_speed"][[1, 2, 3], :] = [
        [0.1, 0.1, 0.1, 0.1],
        [0.1, 0.1, np.nan, np.nan],
        [0.1, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["air_temperature"][[1, 2, 3], :] = [
        [29.844995, 29.844995, 29.844995, 29.844995],
        [28.87117, 28.87117, np.nan, np.nan],
        [27.206405, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_humidity"][[1, 2, 3], :] = [
        [90.341644, 90.341644, 90.341644, 90.341644],
        [92.488034, 92.488034, np.nan, np.nan],
        [96.157312, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["absorbed_radiation"][[1, 2, 3], :] = [
        [10.0, 10.0, 10.0, 10.0],
        [10.0, 10.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["sensible_heat_flux"][[1, 2, 3], :] = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, np.nan, np.nan],
        [0.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["latent_heat_flux"][[1, 2, 3], :] = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, np.nan, np.nan],
        [0.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["attenuation_coefficient"][[1, 2, 3], :] = [
        [13.0, 13.0, 13.0, 13.0],
        [13.0, 13.0, np.nan, np.nan],
        [13.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_turbulence_intensity"][[1, 2, 3], :] = [
        [16.56, 16.56, 16.56, 16.56],
        [11.16, 11.16, np.nan, np.nan],
        [5.76, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["canopy_temperature"][[1, 2, 3], :] = [
        [25.0, 25.0, 25.0, 25.0],
        [25.0, 25.0, np.nan, np.nan],
        [25.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["leaf_air_heat_conductivity"][[1, 2, 3], :] = [
        [0.13, 0.13, 0.13, 0.13],
        [0.13, 0.13, np.nan, np.nan],
        [0.13, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["leaf_vapour_conductivity"][[1, 2, 3], :] = [
        [0.2, 0.2, 0.2, 0.2],
        [0.2, 0.2, np.nan, np.nan],
        [0.2, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["conductivity_from_ref_height"][[1, 2, 3], :] = [
        [3.0, 3.0, 3.0, 3.0],
        [3.0, 3.0, np.nan, np.nan],
        [3.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["stomatal_conductance"][[1, 2, 3], :] = [
        [15.0, 15.0, 15.0, 15.0],
        [15.0, 15.0, np.nan, np.nan],
        [15.0, np.nan, np.nan, np.nan],
    ]

    # Hydrology
    dummy_climate_data["evapotranspiration"][[1, 2, 3], :] = [
        [20.0, 20.0, 20.0, 20.0],
        [20.0, 20.0, np.nan, np.nan],
        [20.0, np.nan, np.nan, np.nan],
    ]

    return dummy_climate_data
