"""Fixtures for plants model testing."""

import numpy as np
import pytest
from xarray import DataArray


@pytest.fixture
def plants_config():
    """Simple configuration fixture for use in tests."""

    from virtual_rainforest.core.config import Config

    cfg_string = """
        [core]
        [core.grid]
        cell_nx = 10
        cell_ny = 10
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
        subcanopy_layer_height = 1.5

        [plants]
        a_plant_integer = 12
        [[plants.ftypes]]
        pft_name = "shrub"
        max_height = 1.0
        [[plants.ftypes]]
        pft_name = "broadleaf"
        max_height = 50.0

        [[animals.functional_groups]]
        name = "carnivorous_bird"
        taxa = "bird"
        diet = "carnivore"
        metabolic_type = "endothermic"
        birth_mass = 0.1
        adult_mass = 1.0
        [[animals.functional_groups]]
        name = "herbivorous_bird"
        taxa = "bird"
        diet = "herbivore"
        metabolic_type = "endothermic"
        birth_mass = 0.05
        adult_mass = 0.5
        [[animals.functional_groups]]
        name = "carnivorous_mammal"
        taxa = "mammal"
        diet = "carnivore"
        metabolic_type = "endothermic"
        birth_mass = 4.0
        adult_mass = 40.0
        [[animals.functional_groups]]
        name = "herbivorous_mammal"
        taxa = "mammal"
        diet = "herbivore"
        metabolic_type = "endothermic"
        birth_mass = 1.0
        adult_mass = 10.0
        [[animals.functional_groups]]
        name = "carnivorous_insect"
        taxa = "insect"
        diet = "carnivore"
        metabolic_type = "ectothermic"
        birth_mass = 0.001
        adult_mass = 0.01
        [[animals.functional_groups]]
        name = "herbivorous_insect"
        taxa = "insect"
        diet = "herbivore"
        metabolic_type = "ectothermic"
        birth_mass = 0.0005
        adult_mass = 0.005
        """

    return Config(cfg_strings=cfg_string)


@pytest.fixture
def flora(plants_config):
    """Construct a minimal Flora object."""
    from virtual_rainforest.models.plants.functional_types import Flora

    flora = Flora.from_config(plants_config)

    return flora


@pytest.fixture
def layer_structure(plants_config):
    """Construct a minimal LayerStructure object."""
    from virtual_rainforest.models.plants.plants_model import LayerStructure

    layer_structure = LayerStructure.from_config(plants_config)

    return layer_structure


@pytest.fixture
def plants_data():
    """Construct a minimal data object with plant cohort data."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.core.utils import set_layer_roles

    data = Data(grid=Grid(cell_ny=2, cell_nx=2))

    # Add cohort configuration
    data["plant_cohorts_n"] = DataArray(np.array([5] * 4))
    data["plant_cohorts_pft"] = DataArray(np.array(["broadleaf"] * 4))
    data["plant_cohorts_cell_id"] = DataArray(np.arange(4))
    data["plant_cohorts_dbh"] = DataArray(np.array([0.1] * 4))

    # Spatio-temporal data
    data["photosynthetic_photon_flux_density"] = DataArray(
        data=np.full((4, 12), fill_value=1000),
        coords={
            "cell_id": np.arange(4),
            # "time": np.arange("2000-01", "2001-01", dtype="datetime64[M]"),
            "time_index": np.arange(12),
        },
    )

    # Canopy layer specific forcing variables from abiotic model
    layer_roles = set_layer_roles(10, [-0.5, -1.0])
    layer_shape = (len(layer_roles), data.grid.n_cells)

    # Setup the layers
    forcing_vars = (
        ("air_temperature", 20),
        ("vapour_pressure_deficit", 1000),
        ("atmospheric_pressure", 101325),
        ("atmospheric_co2", 400),
    )

    for var, value in forcing_vars:
        data[var] = DataArray(
            data=np.full(layer_shape, fill_value=value),
            dims=("layers", "cell_id"),
            coords={
                "layers": np.arange(len(layer_roles)),
                "layer_roles": ("layers", layer_roles),
                "cell_id": data.grid.cell_id,
            },
        )

    return data


@pytest.fixture
def fxt_plants_model(plants_data, flora, layer_structure):
    """Return a simple PlantsModel instance."""
    from pint import Quantity

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    return PlantsModel(
        data=plants_data,
        update_interval=Quantity("1 month"),
        flora=flora,
        layer_structure=layer_structure,
    )
