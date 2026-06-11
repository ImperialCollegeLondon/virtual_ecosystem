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

    # Array resource pools
    pfts = np.array(["pioneer", "canopy", "emergent"])
    cell_ids = np.arange(data.grid.n_cells)
    elements = np.array(["C", "N", "P"])

    # Populate plant biomass pools
    vegetation_biomass = DataArray(
        np.ones((data.grid.n_cells, elements.size, pfts.size)),
        dims=("cell_id", "element", "pft"),
        coords=dict(
            cell_id=cell_ids,
            element=elements,
            pft=pfts,
        ),
    ) * DataArray([20, 2, 1], dims="element", coords=dict(element=elements))

    # Populate non- PFT structured ArrayResource pools
    for pool in ["subcanopy_vegetation_cnp", "subcanopy_seedbank_cnp"]:
        data[pool] = vegetation_biomass.sel(pft="pioneer").drop_vars("pft").copy()
        data[pool + "_consumed"] = xarray.zeros_like(
            vegetation_biomass.sel(pft="pioneer").drop_vars("pft")
        )

    # Populate pft structured ArrayResource pools
    plant_model_pools = [
        "canopy_foliage_cnp",
        "canopy_seed_cnp",
        "canopy_fruit_cnp",
        "foliage_turnover_cnp",
        "seed_turnover_cnp",
        "fruit_turnover_cnp",
    ]
    for pool in plant_model_pools:
        data[pool] = vegetation_biomass.copy()
        data[pool + "_consumed"] = xarray.zeros_like(vegetation_biomass)

    litter_pools = DataArray(np.full(data.grid.n_cells, fill_value=1.5), dims="cell_id")
    litter_ratios = DataArray(
        np.full(data.grid.n_cells, fill_value=25.5), dims="cell_id"
    )

    litter_cnp_template = DataArray(
        np.stack(
            [
                litter_pools,
                litter_pools / litter_ratios,
                litter_pools / litter_ratios,
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    data["litter_pool_above_metabolic_cnp"] = litter_cnp_template
    data["litter_pool_above_structural_cnp"] = litter_cnp_template
    data["litter_pool_woody_cnp"] = litter_cnp_template
    data["litter_pool_below_metabolic_cnp"] = litter_cnp_template
    data["litter_pool_below_structural_cnp"] = litter_cnp_template

    return data


@pytest.fixture
def animal_fixture_core_components(animal_fixture_configuration):
    """A CoreComponents instance for use in testing."""

    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.model_config import CoreConfiguration

    core_cfg = animal_fixture_configuration.get_subconfiguration(
        "core", CoreConfiguration
    )
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
    # Also need to add soil pools that animals consume from
    soil_pools = DataArray(np.full(data.grid.n_cells, fill_value=0.15), dims="cell_id")
    data["soil_c_pool_bacteria"] = soil_pools
    data["soil_c_pool_saprotrophic_fungi"] = soil_pools
    data["soil_c_pool_arbuscular_mycorrhiza"] = soil_pools
    data["soil_c_pool_ectomycorrhiza"] = soil_pools

    # Also need to add a pool to track the amount of fungal fruiting bodies
    data["fungal_fruiting_bodies"] = litter_pools
    data["production_of_fungal_fruiting_bodies"] = DataArray(
        np.zeros(data.grid.n_cells), dims="cell_id"
    )

    # Array resource pools
    pfts = np.array(["pioneer", "canopy", "emergent"])
    cell_ids = np.arange(data.grid.n_cells)
    elements = np.array(["C", "N", "P"])

    data["soil_cnp_pool_pom"] = DataArray(
        np.stack(
            [
                soil_pools,
                soil_pools,
                soil_pools,
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    litter_cnp_template = DataArray(
        np.stack(
            [
                litter_pools,
                litter_pools / litter_ratios,
                litter_pools / litter_ratios,
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    data["litter_pool_above_metabolic_cnp"] = litter_cnp_template
    data["litter_pool_above_structural_cnp"] = litter_cnp_template
    data["litter_pool_woody_cnp"] = litter_cnp_template
    data["litter_pool_below_metabolic_cnp"] = litter_cnp_template
    data["litter_pool_below_structural_cnp"] = litter_cnp_template

    # Populate plant biomass pools
    vegetation_biomass = DataArray(
        np.ones((data.grid.n_cells, pfts.size, elements.size)),
        dims=("cell_id", "pft", "element"),
        coords=dict(
            cell_id=cell_ids,
            pft=pfts,
            element=elements,
        ),
    ) * DataArray([20, 2, 1], dims="element", coords=dict(element=elements))

    # Populate non- PFT structured ArrayResource pools
    subcanopy_pools = ["subcanopy_vegetation_cnp", "subcanopy_seedbank_cnp"]
    for pool in subcanopy_pools:
        data[pool] = vegetation_biomass.sel(pft="pioneer").drop_vars("pft").copy()
        data[pool + "_consumed"] = xarray.zeros_like(
            vegetation_biomass.sel(pft="pioneer").drop_vars("pft")
        )

    # Populate pft structured ArrayResource pools
    plant_model_pools = [
        "canopy_foliage_cnp",
        "canopy_seed_cnp",
        "canopy_fruit_cnp",
        "foliage_turnover_cnp",
        "seed_turnover_cnp",
        "fruit_turnover_cnp",
    ]
    for pool in plant_model_pools:
        data[pool] = vegetation_biomass.copy()
        data[pool + "_consumed"] = xarray.zeros_like(vegetation_biomass)

    data["diurnal_temperature_range"] = from_template()
    data["diurnal_temperature_range"][lyr_str.index_surface_scalar] = 10.0

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
    from virtual_ecosystem.models.animal.model_config import AnimalConstants

    return AnimalConstants(density_scaling_method="madingley")


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
def microbial_c_n_p_ratios(fixture_configuration):
    """Fixture containing the microbial C:N:P ratios for use in animal model testing."""
    from virtual_ecosystem.models.animal.cnp import find_microbial_stoichiometries

    return find_microbial_stoichiometries(config=fixture_configuration)


@pytest.fixture
def dummy_animal_exporter():
    """Provide a no-op exporter for AnimalModel tests.

    Returns:
        An object with a ``dump`` method matching the AnimalCohortDataExporter
        interface but performing no output.
    """

    class DummyAnimalExporter:
        """No-op stand-in for AnimalCohortDataExporter."""

        def dump(self, cohorts, time, time_index):
            """Ignore export calls in tests that do not check CSV output.

            Args:
                cohorts: Iterable of AnimalCohort objects.
                time: Export timestamp.
                time_index: Index of update.
            """
            return None

    return DummyAnimalExporter()


@pytest.fixture
def dummy_resource_pool_exporter():
    """Provide a no-op exporter for resource pool data in AnimalModel tests.

    Returns:
        An object with a ``dump`` method matching the ResourcePoolDataExporter
        interface but performing no output.
    """

    class DummyResourcePoolExporter:
        """No-op stand-in for ResourcePoolDataExporter."""

        def dump(
            self,
            carcass_pools,
            excrement_pools,
            fungal_fruiting_pools,
            soil_pools,
            resource_pools,
            time,
            time_index,
        ):
            """Ignore export calls in tests that do not check CSV output.

            Args:
                carcass_pools: Carcass pools keyed by cell id.
                excrement_pools: Excrement pools keyed by cell id.
                fungal_fruiting_pools: Fungal fruiting body pools keyed by cell id.
                soil_pools: Soil pools keyed by cell id and pool-type string.
                resource_pools: Flat list of ResourcePool instances.
                time: Export timestamp.
                time_index: Index of update.
            """
            return None

    return DummyResourcePoolExporter()


@pytest.fixture
def animal_model_instance(
    dummy_animal_data,
    fixture_core_components,
    functional_group_list_instance,
    microbial_c_n_p_ratios,
    dummy_animal_exporter,
    dummy_resource_pool_exporter,
):
    """Fixture for an animal model object used in tests."""
    from copy import deepcopy

    from virtual_ecosystem.models.animal.animal_model import AnimalModel
    from virtual_ecosystem.models.animal.model_config import AnimalConstants

    # Make sure each call gets a fresh copy
    clean_data = deepcopy(dummy_animal_data)

    return AnimalModel(
        data=clean_data,
        core_components=fixture_core_components,
        animal_cohort_exporter=dummy_animal_exporter,
        resource_pool_exporter=dummy_resource_pool_exporter,
        model_constants=AnimalConstants(density_scaling_method="madingley"),
        functional_groups=functional_group_list_instance,
        microbial_c_n_p_ratios=microbial_c_n_p_ratios,
    )


@pytest.fixture
def animal_model_damuth_instance(
    dummy_animal_data,
    fixture_core_components,
    functional_group_list_instance,
    microbial_c_n_p_ratios,
    dummy_animal_exporter,
    dummy_resource_pool_exporter,
):
    """Fixture for an animal model object used in tests."""
    from copy import deepcopy

    from virtual_ecosystem.models.animal.animal_model import AnimalModel
    from virtual_ecosystem.models.animal.model_config import AnimalConstants

    # Make sure each call gets a fresh copy
    clean_data = deepcopy(dummy_animal_data)

    return AnimalModel(
        data=clean_data,
        core_components=fixture_core_components,
        animal_cohort_exporter=dummy_animal_exporter,
        resource_pool_exporter=dummy_resource_pool_exporter,
        model_constants=AnimalConstants(density_scaling_method="damuth"),
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
def thermophilic_lizard_cohort_instance(
    shared_datadir,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for a thermophilic lizard cohort with CSV thermal tolerances."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)
    return AnimalCohort(
        fg_list[19],
        0.1,
        1,
        10,
        1,
        animal_data_for_cohorts_instance.grid,
        constants_instance,
    )


@pytest.fixture
def excrement_pool_instance():
    """Fixture for an excrement pool used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import ExcrementPool

    return ExcrementPool(
        scavengeable_cnp=CNP(C=500.0, N=100.0, P=50.0),
        decomposed_cnp=CNP(C=0.0, N=0.0, P=0.0),
    )


@pytest.fixture
def excrement_pools_by_cell_instance():
    """Fixture for excrement pools used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import ExcrementPool

    return {
        1: [
            ExcrementPool(
                scavengeable_cnp=CNP(C=500.0, N=100.0, P=50.0),
                decomposed_cnp=CNP(C=0.0, N=0.0, P=0.0),
            )
        ]
    }


@pytest.fixture
def array_plant_list_instance(animal_data_for_model_instance):
    """Return a list of CellResource objects usable as plant_list."""
    import numpy as np

    from virtual_ecosystem.models.animal.animal_traits import (
        DietType,
        VerticalOccupancy,
    )
    from virtual_ecosystem.models.animal.array_resources import (
        ArrayResource,
        ArrayResourceDefinition,
        CellResource,
    )

    resource = ArrayResource(
        definition=ArrayResourceDefinition(
            pool_array="subcanopy_vegetation_cnp",
            consumed_array="subcanopy_vegetation_cnp_consumed",
            vertical_occupancy=VerticalOccupancy.GROUND,
            diet_type=DietType.FOLIAGE,
        ),
        data=animal_data_for_model_instance,
    )

    return [
        CellResource(
            resource=resource,
            available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
            consumed_total_mass=np.zeros(3, dtype=float),
            vertical_occupancy=VerticalOccupancy.GROUND,
            cell_id=0,
        ),
        CellResource(
            resource=resource,
            available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
            consumed_total_mass=np.zeros(3, dtype=float),
            vertical_occupancy=VerticalOccupancy.GROUND,
            cell_id=1,
        ),
    ]


@pytest.fixture
def array_litter_list_instance(animal_data_for_model_instance):
    """Return a list of CellResource objects usable as litter_list."""
    import numpy as np

    from virtual_ecosystem.models.animal.animal_traits import (
        DietType,
        VerticalOccupancy,
    )
    from virtual_ecosystem.models.animal.array_resources import (
        ArrayResource,
        ArrayResourceDefinition,
        CellResource,
    )

    resource = ArrayResource(
        ArrayResourceDefinition(
            pool_array="litter_pool_woody_cnp",
            consumed_array="litter_consumed_woody_cnp",
            vertical_occupancy=VerticalOccupancy.GROUND,
            diet_type=DietType.DETRITUS,
            density=True,
        ),
        data=animal_data_for_model_instance,
    )

    return [
        CellResource(
            resource=resource,
            available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
            consumed_total_mass=np.zeros(3, dtype=float),
            vertical_occupancy=VerticalOccupancy.GROUND,
            cell_id=0,
        ),
        CellResource(
            resource=resource,
            available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
            consumed_total_mass=np.zeros(3, dtype=float),
            vertical_occupancy=VerticalOccupancy.GROUND,
            cell_id=1,
        ),
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
        scavengeable_cnp=CNP(C=500.0, N=100.0, P=50.0),
        decomposed_cnp=CNP(C=0.0, N=0.0, P=0.0),
    )


@pytest.fixture
def carcass_pools_by_cell_instance():
    """Fixture for carcass pools used in tests."""
    from virtual_ecosystem.models.animal.cnp import CNP
    from virtual_ecosystem.models.animal.decay import CarcassPool

    return {
        cell_id: [
            CarcassPool(
                scavengeable_cnp=CNP(C=500.0, N=100.0, P=50.0),
                decomposed_cnp=CNP(C=0.0, N=0.0, P=0.0),
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
        "soil_c_pool_bacteria": [5.8, 2.3, 11.3, 1.0],
        "soil_c_pool_saprotrophic_fungi": [0.89, 8.55, 2.21, 4.54],
        "soil_c_pool_arbuscular_mycorrhiza": [0.65, 1.47, 3.92, 9.04],
        "soil_c_pool_ectomycorrhiza": [0.47, 1.32, 4.2, 3.77],
        "fungal_fruiting_bodies": [0.1, 0.2, 0.3, 0.4],
        "production_of_fungal_fruiting_bodies": [0.05, 0.04, 0.025, 0.0125],
    }

    for var_name, var_values in data_values.items():
        data[var_name] = DataArray(var_values, dims=["cell_id"])

    # Array resource pools
    pfts = np.array(["pioneer", "canopy", "emergent"])
    cell_ids = np.arange(data.grid.n_cells)
    elements = np.array(["C", "N", "P"])

    data["soil_cnp_pool_pom"] = DataArray(
        np.stack(
            [
                [0.1, 1.0, 0.7, 0.35],
                [0.00714285, 0.00071425, 0.00285714, 0.01428571],
                [2.857e-5, 2.85714e-4, 1.142856e-4, 5.714284e-4],
            ],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    vegetation_biomass = DataArray(
        np.ones((data.grid.n_cells, elements.size, pfts.size)),
        dims=("cell_id", "element", "pft"),
        coords=dict(
            cell_id=cell_ids,
            element=elements,
            pft=pfts,
        ),
    ) * DataArray([20, 2, 1], dims="element", coords=dict(element=elements))

    # Populate non- PFT structured ArrayResource pools
    for pool in [
        "subcanopy_vegetation_cnp",
        "subcanopy_seedbank_cnp",
        "subcanopy_seedbank_cnp_consumed",
        "subcanopy_vegetation_cnp_consumed",
    ]:
        data[pool] = vegetation_biomass.sel(pft="pioneer").drop_vars("pft").copy()

    # Populate pft structured ArrayResource pools
    plant_model_pools = [
        "canopy_foliage_cnp",
        "canopy_seed_cnp",
        "canopy_fruit_cnp",
        "seed_turnover_cnp",
        "fruit_turnover_cnp",
    ]
    for pool in plant_model_pools:
        data[pool] = vegetation_biomass.copy()

    # Populate pft structured consumption pools with empty zeros
    plant_model_consumption_pools = [
        "canopy_foliage_cnp_consumed",
        "canopy_seed_cnp_consumed",
        "canopy_fruit_cnp_consumed",
        "seed_turnover_cnp_consumed",
        "fruit_turnover_cnp_consumed",
    ]
    for pool in plant_model_consumption_pools:
        data[pool] = xarray.zeros_like(vegetation_biomass)

    data["litter_pool_above_metabolic_cnp"] = DataArray(
        np.stack(
            [[0.3, 0.15, 0.07, 0.07], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    data["litter_pool_above_structural_cnp"] = DataArray(
        np.stack(
            [[0.5, 0.25, 0.09, 0.09], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    data["litter_pool_woody_cnp"] = DataArray(
        np.stack(
            [[4.7, 11.8, 7.3, 7.3], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    data["litter_pool_below_metabolic_cnp"] = DataArray(
        np.stack(
            [[0.4, 0.37, 0.07, 0.07], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    data["litter_pool_below_structural_cnp"] = DataArray(
        np.stack(
            [[0.6, 0.31, 0.02, 0.02], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]],
            axis=1,
        ),
        dims=("cell_id", "element"),
        coords=dict(cell_id=cell_ids, element=elements),
    )

    return data


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
        "bacteria": {"N": 5.0, "P": 30.0},
        "saprotrophic_fungi": {"N": 10.0, "P": 80.0},
        "arbuscular_mycorrhiza": {"N": 12.0, "P": 90.0},
        "ectomycorrhiza": {"N": 8.0, "P": 70.0},
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
