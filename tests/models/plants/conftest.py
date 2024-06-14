"""Fixtures for plants model testing."""

import numpy as np
import pytest
from xarray import DataArray


@pytest.fixture
def flora(fixture_config):
    """Construct a minimal Flora object."""
    from virtual_ecosystem.models.plants.functional_types import Flora

    flora = Flora.from_config(fixture_config)

    return flora


@pytest.fixture
def plants_data(fixture_core_components):
    """Construct a minimal data object with plant cohort data."""
    from virtual_ecosystem.core.data import Data

    data = Data(grid=fixture_core_components.grid)
    n_cells = fixture_core_components.grid.n_cells

    # Add cohort configuration
    data["plant_cohorts_n"] = DataArray(np.array([5] * n_cells))
    data["plant_cohorts_pft"] = DataArray(np.array(["broadleaf"] * n_cells))
    data["plant_cohorts_cell_id"] = DataArray(np.arange(n_cells))
    data["plant_cohorts_dbh"] = DataArray(np.array([0.1] * n_cells))

    # Spatio-temporal data
    data["photosynthetic_photon_flux_density"] = DataArray(
        data=np.full((n_cells, 12), fill_value=1000),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
            "time_index": np.arange(12),
        },
    )

    # Canopy layer specific forcing variables from abiotic model
    layer_roles = fixture_core_components.layer_structure.layer_roles
    layer_shape = (
        fixture_core_components.layer_structure.n_layers,
        fixture_core_components.grid.n_cells,
    )

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
                "cell_id": fixture_core_components.grid.cell_id,
            },
        )

    return data


@pytest.fixture
def fxt_plants_model(plants_data, flora, fixture_core_components):
    """Return a simple PlantsModel instance."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    return PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=flora,
    )
