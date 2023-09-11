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

    data = Data(grid=Grid(cell_ny=2, cell_nx=2))
    data["plant_cohorts_n"] = DataArray(np.array([5] * 4))
    data["plant_cohorts_pft"] = DataArray(np.array(["broadleaf"] * 4))
    data["plant_cohorts_cell_id"] = DataArray(np.arange(4))
    data["plant_cohorts_dbh"] = DataArray(np.array([0.1] * 4))

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
        soil_layers=[-0.5, -1.0],
    )
