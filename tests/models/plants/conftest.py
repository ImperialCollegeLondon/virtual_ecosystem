"""Fixtures for plants model testing."""

import numpy as np
import pytest
from xarray import DataArray


@pytest.fixture
def plants_config(shared_datadir):
    """Simple configuration fixture for use in tests."""

    from virtual_rainforest.core.config import Config

    return Config(shared_datadir / "all_config.toml")


@pytest.fixture
def flora(plants_config):
    """Construct a minimal Flora object."""
    from virtual_rainforest.models.plants.functional_types import Flora

    flora = Flora.from_config(plants_config)

    return flora


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
            "time": np.arange("2000-01", "2001-01", dtype="datetime64[M]"),
        },
    )

    # Canopy layer specific forcing variables from abiotic model
    layer_roles = set_layer_roles(10, 3)
    layer_shape = (len(layer_roles), data.grid.n_cells)

    # Setup the layers
    forcing_vars = [
        ("air_temperature", 20),
        ("vapour_pressure_deficit", 1000),
        ("atmospheric_pressure", 101325),
        ("atmospheric_co2", 400),
    ]

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
def fxt_plants_model(plants_data, flora):
    """Return a simple PlantsModel instance."""
    from pint import Quantity

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    return PlantsModel(
        data=plants_data,
        update_interval=Quantity("1 month"),
        flora=flora,
        canopy_layers=10,
        soil_layers=3,
    )
