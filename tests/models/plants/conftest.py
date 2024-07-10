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

    # TODO - This elevation data is created so that the PlantsModel.calculate_turnover
    # function works in testing. Once that function has been replaced with something
    # more realistic this should be deleted
    data["elevation"] = DataArray(
        data=np.full((n_cells), fill_value=437.5),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
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


@pytest.fixture
def fixture_canopy_layer_data(fixture_core_components):
    """Shared canopy layer data.

    The fixture supplies tuples of layer name, test values and the indices of the
    vertical layer dimension to insert test values.

    TODO: This is currently convoluted because of the way in which layer_heights is set
    within the plants model.
    """
    lyr_strct = fixture_core_components.layer_structure

    return {
        "layer_heights_full": (
            "layer_heights",
            np.array([32, 30, 20, 10, 0.1, -0.5, -1]),
            np.logical_or(lyr_strct.index_filled_atmosphere, lyr_strct.index_all_soil),
        ),
        "layer_heights_canopy": (
            "layer_heights",
            np.array([32, 30, 20, 10]),
            np.logical_or(lyr_strct.index_above, lyr_strct.index_filled_canopy),
        ),
        "leaf_area_index": (
            "leaf_area_index",
            np.array([1, 1, 1]),
            lyr_strct.index_filled_canopy,
        ),
        "layer_fapar": (
            "layer_fapar",
            np.array([0.4, 0.2, 0.1]),
            lyr_strct.index_filled_canopy,
        ),
        "layer_absorbed_irradiation": (
            "layer_absorbed_irradiation",
            np.array([400, 200, 100, 300]),
            np.logical_or(lyr_strct.index_filled_canopy, lyr_strct.index_surface),
        ),
        "layer_leaf_mass": (
            "layer_leaf_mass",
            np.array([10000, 10000, 10000]),
            lyr_strct.index_filled_canopy,
        ),
    }
