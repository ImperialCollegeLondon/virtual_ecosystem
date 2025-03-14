"""Collection of fixtures to assist the testing scripts."""

from logging import DEBUG
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
def microbial_groups_cfg():
    """Configuration string containing full set of required microbial groups."""
    return """
        [[soil.microbial_group_definition]]
        name = "bacteria"
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

        [[soil.microbial_group_definition]]
        name = "fungi"
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

        [[soil.enzyme_class_definition]]
        source = "bacteria"
        substrate = "pom"
        maximum_rate = 60.0
        half_saturation_constant = 70.0
        activation_energy_rate = 37000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2

        [[soil.enzyme_class_definition]]
        source = "bacteria"
        substrate = "maom"
        maximum_rate = 24.0
        half_saturation_constant = 350.0
        activation_energy_rate = 47000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2

        [[soil.enzyme_class_definition]]
        source = "fungi"
        substrate = "pom"
        maximum_rate = 120.0
        half_saturation_constant = 35.0
        activation_energy_rate = 37000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2

        [[soil.enzyme_class_definition]]
        source = "fungi"
        substrate = "maom"
        maximum_rate = 48.0
        half_saturation_constant = 175.0
        activation_energy_rate = 47000
        activation_energy_saturation = 30000
        reference_temperature = 12.0
        turnover_rate = 2.4e-2
        """


@pytest.fixture
def fixture_config(microbial_groups_cfg):
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
        [[plants.pft_definition]]
        a_hd = 116.0
        ca_ratio = 390.43
        f_g = 0.02
        h_max = 25.33
        lai = 1.8
        m = 2
        n = 5
        name = 'shrub'
        par_ext = 0.5
        resp_f = 0.1
        resp_r = 0.913
        resp_s = 0.044
        rho_s = 200.0
        sla = 14.0
        tau_f = 4.0
        tau_r = 1.04
        yld = 0.17
        zeta = 0.17

        [[plants.pft_definition]]
        a_hd = 116.0
        ca_ratio = 390.43
        f_g = 0.02
        h_max = 30.33
        lai = 1.8
        m = 2
        n = 5
        name = 'broadleaf'
        par_ext = 0.5
        resp_f = 0.1
        resp_r = 0.913
        resp_s = 0.044
        rho_s = 200.0
        sla = 14.0
        tau_f = 4.0
        tau_r = 1.04
        yld = 0.17
        zeta = 0.17

        [[animal.functional_groups]]
        name = "carnivorous_bird"
        taxa = "bird"
        diet = "carnivore"
        metabolic_type = "endothermic"
        reproductive_type = "iteroparous"
        development_type = "direct"
        development_status = "adult"
        offspring_functional_group = "carnivorous_bird"
        excretion_type = "uricotelic"
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
        excretion_type = "uricotelic"
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
        excretion_type = "ureotelic"
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
        excretion_type = "ureotelic"
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
        excretion_type = "uricotelic"
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
        excretion_type = "uricotelic"
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
        excretion_type = "uricotelic"
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
        excretion_type = "uricotelic"
        birth_mass = 0.0005
        adult_mass = 0.005

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
def dummy_carbon_data(fixture_core_components):
    """Creates a dummy carbon data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # The required data is now added. This includes the five carbon pools: mineral
    # associated organic matter, low molecular weight carbon, microbial biomass and
    # necromass carbon and particulate organic matter. It also includes various factors
    # of the physical environment: pH, bulk density, soil moisture, soil temperature,
    # percentage clay in soil.
    data_values = {
        "soil_c_pool_lmwc": [0.05, 0.02, 0.1, 0.005],
        "soil_c_pool_maom": [2.5, 1.7, 4.5, 0.5],
        "soil_c_pool_bacteria": [5.8, 2.3, 11.3, 1.0],
        "soil_c_pool_fungi": [0.89, 8.55, 2.21, 4.54],
        "soil_c_pool_pom": [0.1, 1.0, 0.7, 0.35],
        "soil_c_pool_necromass": [0.058, 0.015, 0.093, 0.105],
        "soil_enzyme_pom_bacteria": [0.022679, 0.009576, 0.050051, 0.003010],
        "soil_enzyme_maom_bacteria": [0.0356, 0.0117, 0.02509, 0.00456],
        "soil_enzyme_pom_fungi": [0.02607, 0.00575, 0.00646, 0.00441],
        "soil_enzyme_maom_fungi": [0.008669, 0.006826, 0.003807, 0.002163],
        "soil_n_pool_don": [0.000571428, 0.00142857, 0.00014285, 0.002857142],
        "soil_n_pool_particulate": [0.00714285, 0.00071425, 0.00285714, 0.01428571],
        "soil_n_pool_necromass": [0.00288462, 0.01788462, 0.02019231, 0.01115385],
        "soil_n_pool_maom": [0.86538462, 0.48076923, 0.32692308, 0.09615385],
        "soil_n_pool_ammonium": [6.9619638e-5, 0.0049914624, 0.000229067, 0.0051955339],
        "soil_n_pool_nitrate": [0.0024219014, 0.0044442996, 0.0003428348, 0.0131405173],
        "soil_p_pool_dop": [5.714e-6, 2.2857120e-5, 5.7142800e-5, 1.1428568e-4],
        "soil_p_pool_particulate": [2.857e-5, 2.85714e-4, 1.142856e-4, 5.714284e-4],
        "soil_p_pool_necromass": [0.00080769, 0.00011538, 0.00071538, 0.00044615],
        "soil_p_pool_maom": [0.01307692, 0.03461538, 0.01923077, 0.00384615],
        "soil_p_pool_primary": [0.0019594, 0.00535662, 0.00277434, 0.00059892],
        "soil_p_pool_secondary": [0.00705668, 0.03816896, 0.01152589, 0.00733107],
        "soil_p_pool_labile": [1.0582393e-5, 3.252961e-5, 6.806745e-5, 1.945635e-4],
        "pH": [3.0, 7.5, 9.0, 5.7],
        "bulk_density": [1350.0, 1800.0, 1000.0, 1500.0],
        "clay_fraction": [0.8, 0.3, 0.1, 0.9],
        "litter_C_mineralisation_rate": [0.00212106, 0.00106053, 0.00049000, 0.0055],
        "litter_N_mineralisation_rate": [3.5351e-5, 7.0702e-5, 0.000183, 1.63333e-5],
        "litter_P_mineralisation_rate": [7.32e-6, 1.41404e-6, 2.82808e-6, 6.53332e-7],
        "vertical_flow": [0.1, 0.5, 2.5, 1.59],
        "nitrogen_fixation_carbon_supply": [0.01, 0.25, 0.0075, 0.0047],
        "root_carbohydrate_exudation": [0.025, 0.01, 0.05, 0.0025],
        "plant_ammonium_uptake": [5.0e-5, 2.5e-5, 1.0e-5, 1.0e-4],
        "plant_nitrate_uptake": [7.5e-4, 1.0e-3, 2.5e-4, 1.0e-4],
        "plant_phosphorus_uptake": [3.0e-6, 5e-5, 2.0e-6, 1.0e-6],
    }

    for var_name, var_values in data_values.items():
        data[var_name] = DataArray(var_values, dims=["cell_id"])

    # The layer dependant data has to be handled separately - at present all of these
    # are defined only for the topsoil layer
    lyr_str = fixture_core_components.layer_structure

    data["soil_moisture"] = lyr_str.from_template()
    data["soil_moisture"][lyr_str.index_topsoil] = np.array(
        [232.61550125, 196.88733175, 126.065797, 75.63195175]
    )

    data["matric_potential"] = lyr_str.from_template()
    data["matric_potential"][lyr_str.index_topsoil] = np.array(
        [-3.0, -10.0, -250.0, -10000.0]
    )

    data["soil_temperature"] = lyr_str.from_template()
    data["soil_temperature"][lyr_str.index_all_soil] = np.array(
        [[35.0, 37.5, 40.0, 25.0], [22.5, 22.5, 22.5, 22.5]]
    )

    data["air_temperature"] = lyr_str.from_template()
    data["air_temperature"][lyr_str.index_filled_atmosphere] = np.array(
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
        "downward_shortwave_radiation": 100.0,
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
    data["leaf_area_index"][lyr_str.index_filled_canopy] = 1.0

    data["shortwave_absorption"] = from_template()
    data["shortwave_absorption"][lyr_str.index_flux_layers] = 1.0

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

    data["shortwave_absorption"] = from_template()
    data["shortwave_absorption"][lyr_str.index_flux_layers] = 10.0

    flux_index = np.logical_or(lyr_str.index_above, lyr_str.index_flux_layers)

    data["sensible_heat_flux"] = from_template()
    data["sensible_heat_flux"][flux_index] = 0.0

    data["latent_heat_flux"] = from_template()
    data["latent_heat_flux"][flux_index] = 0.0

    data["molar_density_air"] = from_template()
    data["molar_density_air"][lyr_str.index_filled_atmosphere] = 38.0

    data["specific_heat_air"] = from_template()
    data["specific_heat_air"][lyr_str.index_filled_atmosphere] = 29.0

    data["attenuation_coefficient"] = from_template()
    data["attenuation_coefficient"][lyr_str.index_filled_atmosphere] = np.array(
        [13.0, 13.0, 13.0, 13.0, 2.0]
    )[:, None]

    data["relative_turbulence_intensity"] = from_template()
    data["relative_turbulence_intensity"][lyr_str.index_filled_atmosphere] = np.array(
        [17.64, 16.56, 11.16, 5.76, 0.414]
    )[:, None]

    data["latent_heat_vapourisation"] = from_template()
    data["latent_heat_vapourisation"][lyr_str.index_filled_atmosphere] = 2254.0

    data["canopy_temperature"] = from_template()
    data["canopy_temperature"][lyr_str.index_filled_canopy] = 25.0

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
    data["evapotranspiration"] = from_template()
    data["evapotranspiration"][lyr_str.index_filled_canopy] = 20.0

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
    number of canopy layers within the different cells.
    """

    index_filled_canopy = fixture_core_components.layer_structure.index_filled_canopy

    # Structural variables
    dummy_climate_data["leaf_area_index"][index_filled_canopy] = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, np.nan, np.nan],
        [1.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["layer_heights"][index_filled_canopy] = [
        [30.0, 30.0, 30.0, 30.0],
        [20.0, 20.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
    ]

    # Microclimate and energy balance
    dummy_climate_data["wind_speed"][index_filled_canopy] = [
        [0.1, 0.1, 0.1, 0.1],
        [0.1, 0.1, np.nan, np.nan],
        [0.1, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["air_temperature"][index_filled_canopy] = [
        [29.844995, 29.844995, 29.844995, 29.844995],
        [28.87117, 28.87117, np.nan, np.nan],
        [27.206405, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_humidity"][index_filled_canopy] = [
        [90.341644, 90.341644, 90.341644, 90.341644],
        [92.488034, 92.488034, np.nan, np.nan],
        [96.157312, np.nan, np.nan, np.nan],
    ]

    sw_indexes = [1, 2, 3, 13]
    dummy_climate_data["shortwave_absorption"][sw_indexes] = [
        [10.0, 10.0, 10.0, 10.0],
        [10.0, 10.0, np.nan, np.nan],
        [10.0, np.nan, np.nan, np.nan],
        [0, 0, 0, 0],
    ]
    dummy_climate_data["shortwave_absorption"][13] = np.repeat(0.0, 4)

    dummy_climate_data["sensible_heat_flux"][index_filled_canopy] = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, np.nan, np.nan],
        [0.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["latent_heat_flux"][index_filled_canopy] = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, np.nan, np.nan],
        [0.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["attenuation_coefficient"][index_filled_canopy] = [
        [13.0, 13.0, 13.0, 13.0],
        [13.0, 13.0, np.nan, np.nan],
        [13.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["relative_turbulence_intensity"][index_filled_canopy] = [
        [16.56, 16.56, 16.56, 16.56],
        [11.16, 11.16, np.nan, np.nan],
        [5.76, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["canopy_temperature"][index_filled_canopy] = [
        [25.0, 25.0, 25.0, 25.0],
        [25.0, 25.0, np.nan, np.nan],
        [25.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["leaf_air_heat_conductivity"][index_filled_canopy] = [
        [0.13, 0.13, 0.13, 0.13],
        [0.13, 0.13, np.nan, np.nan],
        [0.13, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["leaf_vapour_conductivity"][index_filled_canopy] = [
        [0.2, 0.2, 0.2, 0.2],
        [0.2, 0.2, np.nan, np.nan],
        [0.2, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["conductivity_from_ref_height"][index_filled_canopy] = [
        [3.0, 3.0, 3.0, 3.0],
        [3.0, 3.0, np.nan, np.nan],
        [3.0, np.nan, np.nan, np.nan],
    ]

    dummy_climate_data["stomatal_conductance"][index_filled_canopy] = [
        [15.0, 15.0, 15.0, 15.0],
        [15.0, 15.0, np.nan, np.nan],
        [15.0, np.nan, np.nan, np.nan],
    ]

    # Hydrology
    dummy_climate_data["evapotranspiration"][index_filled_canopy] = [
        [20.0, 20.0, 20.0, 20.0],
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
