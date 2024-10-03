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
def animal_fixture_config():
    """Simple configuration fixture for use in tests."""

    from virtual_ecosystem.core.config import Config

    cfg_string = """
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

    return Config(cfg_strings=cfg_string)


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

    data["canopy_absorption"] = from_template()
    data["canopy_absorption"][lyr_str.index_filled_canopy] = 1.0

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

    # Initialize total_animal_respiration with zeros for each cell
    total_animal_respiration = np.zeros(
        len(animal_fixture_core_components.grid.cell_id)
    )
    data["total_animal_respiration"] = DataArray(
        total_animal_respiration,
        dims=["cell_id"],
        coords={"cell_id": animal_fixture_core_components.grid.cell_id},
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

    return AnimalConsts()


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
def animal_model_instance(
    dummy_animal_data,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Fixture for an animal model object used in tests."""

    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    return AnimalModel(
        data=dummy_animal_data,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
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
    """Fixture for a soil pool used in tests."""
    from virtual_ecosystem.models.animal.decay import ExcrementPool

    return ExcrementPool(100000.0, 0.0)


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
    """Fixture for an carcass pool used in tests."""
    from virtual_ecosystem.models.animal.decay import CarcassPool

    return CarcassPool(0.0, 0.0)


@pytest.fixture
def carcass_pools_instance():
    """Fixture for carcass pools used in tests."""
    from virtual_ecosystem.models.animal.decay import CarcassPool

    return {1: [CarcassPool(scavengeable_energy=500.0, decomposed_energy=0.0)]}
