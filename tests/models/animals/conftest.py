"""Collection of fixtures to assist the animal model testing scripts."""

import numpy as np
import pytest
import xarray
from xarray import DataArray

# FIXME: Need to reconcile these data instances - a lot of overlap and some
#        inconsistency with fixture_core_components


@pytest.fixture
def data_instance():
    """Creates an empty data instance."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    grid = Grid()
    return Data(grid)


@pytest.fixture
def plant_data_instance():
    """Fixture returning a simple data instance containing plant resource data."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Populate data with a layers x cell id layer_leaf_mass array
    data = Data(grid=Grid(cell_nx=3, cell_ny=3))
    leaf_mass = np.full((15, 9), fill_value=np.nan)
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    return data


@pytest.fixture
def animal_data_for_model_instance(fixture_core_components):
    """Fixture returning a combination of plant and air temperature data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(
        grid_type="square",
        cell_nx=3,
        cell_ny=3,
    )
    data = Data(grid)

    leaf_mass = np.full(
        (fixture_core_components.layer_structure.n_layers, grid.n_cells),
        fill_value=np.nan,
    )
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    # Populate the fungal fruiting bodies
    data["fungal_fruiting_bodies"] = xarray.DataArray(
        np.full(grid.n_cells, 0.1), dims=["cell_id"]
    )

    # grid.cell_id gives the spatial dimension, and we want a single "time" or "layer"
    air_temperature_values = np.full(
        (1, grid.n_cells), 25.0
    )  # All cells at 25.0 for one time step or layer
    air_temperature = DataArray(
        air_temperature_values,
        dims=[
            "time_or_layer",
            "cell_id",
        ],  # Adjust dimension names as appropriate for your model
        coords={
            "time_or_layer": [0],  # Assuming a single time step or layer for simplicity
            "cell_id": grid.cell_id,
        },
    )
    data["air_temperature"] = air_temperature

    return data


@pytest.fixture
def animal_fixture_config(fixture_root_data_dir, microbial_groups_cfg):
    """Simple configuration fixture for use in tests."""

    from virtual_ecosystem.core.config import Config

    cfg_string = f"""
        [core]
        [core.grid]
        cell_nx = 3
        cell_ny = 3
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
        pft_definitions_path = "{(fixture_root_data_dir / "plant_pfts.csv")!s}"
        
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
        taxa = "invertebrate"
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
        taxa = "invertebrate"
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
        taxa = "invertebrate"
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
        taxa = "invertebrate"
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
        taxa = "invertebrate"
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
def animal_fixture_core_components(animal_fixture_config):
    """A CoreComponents instance for use in testing."""
    from virtual_ecosystem.core.core_components import CoreComponents

    core_components = CoreComponents(animal_fixture_config)

    # Setup three filled canopy layers
    canopy_array = np.full(
        (core_components.layer_structure.n_canopy_layers, core_components.grid.n_cells),
        np.nan,
    )
    canopy_array[np.array([0, 1, 2])] = 1.0
    core_components.layer_structure.set_filled_canopy(canopy_array)

    return core_components


@pytest.fixture
def dummy_animal_data(animal_fixture_core_components):
    """Creates a dummy climate data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    # Setup the data object with nine cells.
    data = Data(animal_fixture_core_components.grid)

    # Shorten syntax
    lyr_str = animal_fixture_core_components.layer_structure
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
        "topofcanopy_radiation": 100.0,
    }

    for var, value in ref_values.items():
        data[var] = DataArray(
            np.full((9, 3), value),  # Update to 9 grid cells
            dims=["cell_id", "time_index"],
        )

    # Spatially varying but not vertically structured
    spatially_variable = {
        "shortwave_radiation_surface": [
            100,
            10,
            0,
            0,
            50,
            30,
            20,
            15,
            5,
        ],  # Updated to 9 values
        "sensible_heat_flux_topofcanopy": [
            100,
            50,
            10,
            10,
            40,
            20,
            15,
            12,
            6,
        ],  # Updated
        "friction_velocity": [12, 5, 2, 2, 7, 4, 3, 2.5, 1.5],  # Updated
        "soil_evaporation": [
            0.001,
            0.01,
            0.1,
            0.1,
            0.05,
            0.03,
            0.02,
            0.015,
            0.008,
        ],  # Updated
        "surface_runoff_accumulated": [0, 10, 300, 300, 100, 50, 20, 15, 5],  # Updated
        "subsurface_flow_accumulated": [10, 10, 30, 30, 20, 15, 12, 10, 8],  # Updated
        "elevation": [200, 100, 10, 10, 80, 60, 40, 30, 15],  # Updated
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
        data[var] = DataArray(
            np.repeat(val, 9), dims=["cell_id"]
        )  # Update to 9 grid cells

    # Structural variables - assign values to vertical layer indices across grid id
    data["leaf_area_index"] = from_template()
    data["leaf_area_index"][lyr_str.index_filled_canopy] = 1.0

    data["shortwave_absorption"] = from_template()
    data["shortwave_absorption"][lyr_str.index_filled_canopy] = 1.0

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
        [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    )[:, None]

    data["soil_temperature"] = from_template()
    data["soil_temperature"][lyr_str.index_all_soil] = 20.0

    data["relative_humidity"] = from_template()
    data["relative_humidity"][lyr_str.index_filled_atmosphere] = np.array(
        [90.0, 90.341644, 92.488034, 96.157312, 100]
    )[:, None]

    data["absorbed_radiation"] = from_template()
    data["absorbed_radiation"][lyr_str.index_filled_canopy] = 10.0

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
        np.full((2, 9), 450.0),
        dims=("groundwater_layers", "cell_id"),
    )

    # Adding in litter variables as these are also needed now
    litter_pools = DataArray(np.full(data.grid.n_cells, fill_value=1.5), dims="cell_id")
    litter_ratios = DataArray(
        np.full(data.grid.n_cells, fill_value=25.5), dims="cell_id"
    )
    data["litter_pool_above_metabolic"] = litter_pools
    data["litter_pool_above_structural"] = litter_pools
    data["litter_pool_woody"] = litter_pools
    data["litter_pool_below_metabolic"] = litter_pools
    data["litter_pool_below_structural"] = litter_pools
    data["c_n_ratio_above_metabolic"] = litter_ratios
    data["c_n_ratio_above_structural"] = litter_ratios
    data["c_n_ratio_woody"] = litter_ratios
    data["c_n_ratio_below_metabolic"] = litter_ratios
    data["c_n_ratio_below_structural"] = litter_ratios
    data["c_p_ratio_above_metabolic"] = litter_ratios
    data["c_p_ratio_above_structural"] = litter_ratios
    data["c_p_ratio_woody"] = litter_ratios
    data["c_p_ratio_below_metabolic"] = litter_ratios
    data["c_p_ratio_below_structural"] = litter_ratios

    # Also need to add soil pools that animals consume from
    soil_pools = DataArray(np.full(data.grid.n_cells, fill_value=0.15), dims="cell_id")
    data["soil_c_pool_pom"] = soil_pools
    data["soil_n_pool_particulate"] = soil_pools
    data["soil_p_pool_particulate"] = soil_pools
    data["soil_c_pool_bacteria"] = soil_pools
    data["soil_c_pool_saprotrophic_fungi"] = soil_pools
    data["soil_c_pool_arbuscular_mycorrhiza"] = soil_pools
    data["soil_c_pool_ectomycorrhiza"] = soil_pools

    # Also need to add a pool to track the amount of fungal fruiting bodies
    data["fungal_fruiting_bodies"] = litter_pools
    data["production_of_fungal_fruiting_bodies"] = DataArray(
        np.zeros(data.grid.n_cells), dims="cell_id"
    )

    return data


@pytest.fixture
def animal_data_for_cohorts_instance(fixture_core_components):
    """Fixture returning a combination of plant and air temperature data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(
        grid_type="square",
        cell_nx=3,
        cell_ny=3,
    )
    data = Data(grid)

    leaf_mass = np.full(
        (fixture_core_components.layer_structure.n_layers, grid.n_cells),
        fill_value=np.nan,
    )
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    # grid.cell_id gives the spatial dimension, and we want a single "time" or "layer"
    air_temperature_values = np.full(
        (1, grid.n_cells), 25.0
    )  # All cells at 25.0 for one time step or layer
    air_temperature = DataArray(
        air_temperature_values,
        dims=[
            "time_or_layer",
            "cell_id",
        ],  # Adjust dimension names as appropriate for your model
        coords={
            "time_or_layer": [0],  # Assuming a single time step or layer for simplicity
            "cell_id": grid.cell_id,
        },
    )
    data["air_temperature"] = air_temperature

    # Initialize total_animal_respiration with zeros for each cell
    total_animal_respiration = np.zeros(len(grid.cell_id))
    data["total_animal_respiration"] = DataArray(
        total_animal_respiration, dims=["cell_id"], coords={"cell_id": grid.cell_id}
    )

    return data


@pytest.fixture
def constants_instance():
    """Fixture for an instance of animal constants."""
    from virtual_ecosystem.models.animal.constants import AnimalConsts

    return AnimalConsts(density_scaling_method="madingley")


@pytest.fixture
def functional_group_list_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list


@pytest.fixture
def microbial_c_n_p_ratios(fixture_config):
    """Fixture containing the microbial C:N:P ratios for use in animal model testing."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        find_microbial_stoichiometries,
    )

    return find_microbial_stoichiometries(config=fixture_config)


@pytest.fixture
def animal_model_instance(
    dummy_animal_data,
    fixture_core_components,
    functional_group_list_instance,
    microbial_c_n_p_ratios,
):
    """Fixture for an animal model object used in tests."""
    from copy import deepcopy

    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    # Make sure each call gets a fresh copy
    clean_data = deepcopy(dummy_animal_data)

    return AnimalModel(
        data=clean_data,
        core_components=fixture_core_components,
        density_scaling_method="madingley",
        functional_groups=functional_group_list_instance,
        microbial_c_n_p_ratios=microbial_c_n_p_ratios,
    )


@pytest.fixture
def animal_model_damuth_instance(
    dummy_animal_data,
    fixture_core_components,
    functional_group_list_instance,
    microbial_c_n_p_ratios,
):
    """Fixture for an animal model object used in tests."""
    from copy import deepcopy

    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    # Make sure each call gets a fresh copy
    clean_data = deepcopy(dummy_animal_data)

    return AnimalModel(
        data=clean_data,
        core_components=fixture_core_components,
        density_scaling_method="damuth",
        functional_groups=functional_group_list_instance,
        microbial_c_n_p_ratios=microbial_c_n_p_ratios,
    )


@pytest.fixture
def herbivore_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[3]


@pytest.fixture
def herbivore_cohort_instance(
    herbivore_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        herbivore_functional_group_instance,
        10000.0,
        1,
        10,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


@pytest.fixture
def fungivore_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[16]


@pytest.fixture
def fungivore_cohort_instance(
    fungivore_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        fungivore_functional_group_instance,
        10000.0,
        1,
        10,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


@pytest.fixture
def predator_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[2]


@pytest.fixture
def predator_cohort_instance(
    predator_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        predator_functional_group_instance,  # functional group
        10000.0,  # mass
        1,  # age
        10,  # individuals
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


@pytest.fixture
def earthworm_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[12]


@pytest.fixture
def earthworm_cohort_instance(
    earthworm_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        earthworm_functional_group_instance,
        1.0,
        1,
        100,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,
        constants_instance,
    )


@pytest.fixture
def caterpillar_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[9]


@pytest.fixture
def caterpillar_cohort_instance(
    caterpillar_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        caterpillar_functional_group_instance,
        1.0,
        1,
        100,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


@pytest.fixture
def butterfly_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[8]


@pytest.fixture
def butterfly_cohort_instance(
    butterfly_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        butterfly_functional_group_instance,
        1.0,
        1,
        100,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


@pytest.fixture
def excrement_pool_instance():
    """Fixture for an excrement pool used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import ExcrementPool

    return ExcrementPool(
        scavengeable_cnp=CNP(carbon=500.0, nitrogen=100.0, phosphorus=50.0),
        decomposed_cnp=CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0),
    )


@pytest.fixture
def excrement_pools_by_cell_instance():
    """Fixture for excrement pools used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import ExcrementPool

    return {
        1: [
            ExcrementPool(
                scavengeable_cnp=CNP(carbon=500.0, nitrogen=100.0, phosphorus=50.0),
                decomposed_cnp=CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0),
            )
        ]
    }


@pytest.fixture
def plant_instance(plant_data_instance, constants_instance):
    """Fixture for a plant community used in tests."""
    from virtual_ecosystem.models.animal.plant_resources import PlantResources

    return PlantResources(
        data=plant_data_instance, cell_id=4, constants=constants_instance
    )


@pytest.fixture
def plant_list_instance(plant_data_instance, constants_instance):
    """Fixture providing a list of plant resources."""
    from virtual_ecosystem.models.animal.plant_resources import PlantResources

    return [
        PlantResources(
            data=plant_data_instance, cell_id=4, constants=constants_instance
        )
        for idx in range(3)
    ]


@pytest.fixture
def animal_list_instance(
    herbivore_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture providing a list of animal cohorts."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return [
        AnimalCohort(
            herbivore_functional_group_instance,
            10000.0,
            1,
            10,
            1,  # centroid
            animal_data_for_cohorts_instance.grid,  # grid
            constants_instance,
        )
        for idx in range(3)
    ]


@pytest.fixture
def carcass_pool_instance():
    """Fixture for a carcass pool used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import CarcassPool

    return CarcassPool(
        scavengeable_cnp=CNP(carbon=500.0, nitrogen=100.0, phosphorus=50.0),
        decomposed_cnp=CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0),
    )


@pytest.fixture
def carcass_pools_by_cell_instance():
    """Fixture for carcass pools used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import CarcassPool

    return {
        cell_id: [
            CarcassPool(
                scavengeable_cnp=CNP(carbon=500.0, nitrogen=100.0, phosphorus=50.0),
                decomposed_cnp=CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0),
            )
        ]
        for cell_id in range(0, 9)  # Creates carcass pools for cells 0 to 8
    }


@pytest.fixture
def litter_soil_data_instance(fixture_core_components):
    """Creates a dummy litter + soil data for use in tests."""

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # The required data is now added. This is basically the 5 litter pool sizes and
    # stoichiometric ratios
    data_values = {
        "litter_pool_above_metabolic": [0.3, 0.15, 0.07, 0.07],
        "litter_pool_above_structural": [0.5, 0.25, 0.09, 0.09],
        "litter_pool_woody": [4.7, 11.8, 7.3, 7.3],
        "litter_pool_below_metabolic": [0.4, 0.37, 0.07, 0.07],
        "litter_pool_below_structural": [0.6, 0.31, 0.02, 0.02],
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
        "soil_c_pool_pom": [0.1, 1.0, 0.7, 0.35],
        "soil_n_pool_particulate": [0.00714285, 0.00071425, 0.00285714, 0.01428571],
        "soil_p_pool_particulate": [2.857e-5, 2.85714e-4, 1.142856e-4, 5.714284e-4],
        "soil_c_pool_bacteria": [5.8, 2.3, 11.3, 1.0],
        "soil_c_pool_saprotrophic_fungi": [0.89, 8.55, 2.21, 4.54],
        "soil_c_pool_arbuscular_mycorrhiza": [0.65, 1.47, 3.92, 9.04],
        "soil_c_pool_ectomycorrhiza": [0.47, 1.32, 4.2, 3.77],
        "fungal_fruiting_bodies": [0.1, 0.2, 0.3, 0.4],
        "production_of_fungal_fruiting_bodies": [0.05, 0.04, 0.025, 0.0125],
    }

    for var_name, var_values in data_values.items():
        data[var_name] = DataArray(var_values, dims=["cell_id"])

    return data


@pytest.fixture
def litter_pool_instance(litter_soil_data_instance):
    """Fixture for a single LitterPool instance in cell 0."""
    from virtual_ecosystem.models.animal.decay import LitterPool

    return LitterPool(
        pool_name="above_metabolic",
        cell_id=0,
        data=litter_soil_data_instance,
        cell_area=10000,
    )


@pytest.fixture
def litter_pools_by_cell_instance(litter_soil_data_instance):
    """Fixture for litter pools used in tests."""
    from virtual_ecosystem.models.animal.decay import LitterPool

    return {
        cell_id: [
            LitterPool(
                pool_name="above_metabolic",
                cell_id=cell_id,
                data=litter_soil_data_instance,
                cell_area=10000,
            )
        ]
        for cell_id in range(4)  # data has 4 valid cells: 0 to 3
    }


@pytest.fixture
def litter_pools_dict_by_cell_instance(litter_soil_data_instance):
    """Fixture for litter pools with correct dict[str, Resource] structure."""
    from virtual_ecosystem.models.animal.decay import LitterPool

    pool_names = [
        "above_metabolic",
        "above_structural",
        "woody",
        "below_metabolic",
        "below_structural",
    ]

    return {
        cell_id: {
            name: LitterPool(
                pool_name=name,
                cell_id=cell_id,
                data=litter_soil_data_instance,
                cell_area=10000,
            )
            for name in pool_names
        }
        for cell_id in range(4)
    }


@pytest.fixture
def herbivory_waste_pool_instance():
    """Fixture for a herbivory waste pool class to be used in tests."""
    from virtual_ecosystem.models.animal.decay import HerbivoryWaste

    # Create an instance of HerbivoryWaste with the valid plant_matter_type
    herbivory_waste = HerbivoryWaste(plant_matter_type="leaf")

    # Manually set the additional attributes
    herbivory_waste.mass_current = 0.5  # Initial mass in kg
    herbivory_waste.c_n_ratio = 20.0  # Carbon to Nitrogen ratio [unitless]
    herbivory_waste.c_p_ratio = 150.0  # Carbon to Phosphorus ratio [unitless]
    herbivory_waste.lignin_proportion = (
        0.25  # Proportion of lignin in the mass [unitless]
    )

    return herbivory_waste


@pytest.fixture
def mushroom_instance(litter_soil_data_instance):
    """Fixture for a single FungalFruitPool object."""
    from virtual_ecosystem.models.animal.decay import (
        FungalFruitPool,
    )  # Adjust as needed

    return FungalFruitPool(
        cell_id=0,
        data=litter_soil_data_instance,
        cell_area=100.0,  # m²
        c_n_ratio=25.0,
        c_p_ratio=100.0,
    )


@pytest.fixture
def fungal_fruit_list_instance(litter_soil_data_instance):
    """Fixture for multiple FungalFruitPool objects across grid cells."""
    from virtual_ecosystem.models.animal.decay import FungalFruitPool

    return [
        FungalFruitPool(
            cell_id=cell_id,
            data=litter_soil_data_instance,
            cell_area=100.0,
            c_n_ratio=25.0,
            c_p_ratio=100.0,
        )
        for cell_id in litter_soil_data_instance.grid.cell_id
    ]


@pytest.fixture
def microbial_cnp_ratios() -> dict[str, dict[str, float]]:
    """Reusable microbial C:N:P ratios for SoilPool construction.

    Returns:
        Mapping from pool name to C:N and C:P ratios (unitless). Used by
        SoilPool for bacteria and fungi stoichiometry.
    """

    return {
        "bacteria": {"nitrogen": 5.0, "phosphorus": 30.0},
        "saprotrophic_fungi": {"nitrogen": 10.0, "phosphorus": 80.0},
        "arbuscular_mycorrhiza": {"nitrogen": 12.0, "phosphorus": 90.0},
        "ectomycorrhiza": {"nitrogen": 8.0, "phosphorus": 70.0},
    }


@pytest.fixture
def soil_fungi_instance(litter_soil_data_instance, microbial_cnp_ratios):
    """Fixture for a single SoilPool 'fungi' object."""
    from virtual_ecosystem.models.animal.decay import SoilPool

    return SoilPool(
        pool_name="fungi",
        cell_id=0,
        data=litter_soil_data_instance,
        cell_area=litter_soil_data_instance.grid.cell_area,
        max_depth_microbial_activity=0.2,
        c_n_p_ratios=microbial_cnp_ratios,
    )


@pytest.fixture
def soil_fungi_list_instance(litter_soil_data_instance, microbial_cnp_ratios):
    """Fixture for SoilPool 'fungi' objects across all grid cells."""
    from virtual_ecosystem.models.animal.decay import SoilPool

    return [
        SoilPool(
            pool_name="fungi",
            cell_id=cell_id,
            data=litter_soil_data_instance,
            cell_area=litter_soil_data_instance.grid.cell_area,
            max_depth_microbial_activity=0.2,
            c_n_p_ratios=microbial_cnp_ratios,
        )
        for cell_id in litter_soil_data_instance.grid.cell_id
    ]


@pytest.fixture
def pom_instance(litter_soil_data_instance, microbial_cnp_ratios):
    """Fixture for a single SoilPool 'pom' object."""
    from virtual_ecosystem.models.animal.decay import SoilPool

    return SoilPool(
        pool_name="pom",
        cell_id=0,
        data=litter_soil_data_instance,
        cell_area=litter_soil_data_instance.grid.cell_area,
        max_depth_microbial_activity=0.2,
        c_n_p_ratios=microbial_cnp_ratios,
    )


@pytest.fixture
def pom_list_instance(litter_soil_data_instance, microbial_cnp_ratios):
    """Fixture for SoilPool 'pom' objects across all grid cells."""
    from virtual_ecosystem.models.animal.decay import SoilPool

    return [
        SoilPool(
            pool_name="pom",
            cell_id=cell_id,
            data=litter_soil_data_instance,
            cell_area=litter_soil_data_instance.grid.cell_area,
            max_depth_microbial_activity=0.2,
            c_n_p_ratios=microbial_cnp_ratios,
        )
        for cell_id in litter_soil_data_instance.grid.cell_id
    ]


@pytest.fixture
def bacteria_instance(litter_soil_data_instance, microbial_cnp_ratios):
    """Fixture for a single SoilPool 'bacteria' object."""
    from virtual_ecosystem.models.animal.decay import SoilPool

    return SoilPool(
        pool_name="bacteria",
        cell_id=0,
        data=litter_soil_data_instance,
        cell_area=litter_soil_data_instance.grid.cell_area,
        max_depth_microbial_activity=0.2,
        c_n_p_ratios=microbial_cnp_ratios,
    )


@pytest.fixture
def bacteria_list_instance(litter_soil_data_instance, microbial_cnp_ratios):
    """Fixture for SoilPool 'bacteria' objects across all grid cells."""
    from virtual_ecosystem.models.animal.decay import SoilPool

    return [
        SoilPool(
            pool_name="bacteria",
            cell_id=cell_id,
            data=litter_soil_data_instance,
            cell_area=litter_soil_data_instance.grid.cell_area,
            max_depth_microbial_activity=0.2,
            c_n_p_ratios=microbial_cnp_ratios,
        )
        for cell_id in litter_soil_data_instance.grid.cell_id
    ]
