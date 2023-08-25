"""Fixtures for plants model testing."""

import numpy as np
import pytest
from xarray import DataArray


@pytest.fixture()
def plant_config(shared_datadir):
    """Simple configuration fixture for use in tests."""

    from virtual_rainforest.core.config import Config

    return Config(shared_datadir / "all_config.toml")


@pytest.fixture()
def pfts(plant_config):
    """Construct a minimal PlantFunctionalType object."""
    from virtual_rainforest.models.plants.functional_types import PlantFunctionalTypes

    pfts = PlantFunctionalTypes.from_config(plant_config)

    return pfts


@pytest.fixture()
def plants_data():
    """Construct a minimal data object with plant cohort data."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    data = Data(grid=Grid(cell_ny=2, cell_nx=2))
    data["plant_cohort_n"] = DataArray(np.array([5] * 4))
    data["plant_cohort_pft"] = DataArray(np.array(["tree"] * 4))
    data["plant_cohort_cell_id"] = DataArray(np.arange(4))
    data["plant_cohort_dbh"] = DataArray(np.array([0.1] * 4))

    return data
