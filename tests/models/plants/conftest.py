"""Fixtures for plants model testing."""

import io

import numpy as np
import pandas as pd
import pytest
from xarray import DataArray


@pytest.fixture
def flora(fixture_config):
    """Construct a minimal Flora object."""
    from virtual_ecosystem.models.plants.functional_types import get_flora_from_config

    flora = get_flora_from_config(fixture_config)

    return flora


@pytest.fixture
def plants_data(fixture_core_components):
    """Construct a minimal data object with plant cohort data."""
    from virtual_ecosystem.core.data import Data

    data = Data(grid=fixture_core_components.grid)
    n_cells = fixture_core_components.grid.n_cells

    # Add cohort configuration - this adds varying numbers of cohorts with different
    # canopy profiles to the four cells.
    cohort_csv = io.StringIO("""cell_id,n,pft,dbh
    0,400,broadleaf,1.0
    0,100,broadleaf,0.1
    0,100,shrub,0.01
    1,300,broadleaf,1.0
    1,100,broadleaf,0.1
    2,200,broadleaf,1.0
    2,100,shrub,0.01
    3,100,broadleaf,1.0
    3,100,broadleaf,0.1
    3,100,shrub,0.01""")

    cohorts = pd.read_csv(cohort_csv).to_xarray()

    for var in cohorts:
        data["plant_cohorts_" + var] = cohorts[var]

    # Spatio-temporal data - DSR here is maintaining an earlier test value
    # of PPFD = 1000
    data["downward_shortwave_radiation"] = DataArray(
        data=np.full((n_cells, 12), fill_value=1000 / 2.04),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
            "time_index": np.arange(12),
        },
    )

    # Subcanopy vegetation masses kg C m2
    data["subcanopy_vegetation_biomass"] = DataArray(
        data=np.array([0.07] * n_cells),
        coords={"cell_id": fixture_core_components.grid.cell_id},
    )
    data["subcanopy_seedbank_biomass"] = DataArray(
        data=np.array([0.07] * n_cells),
        coords={"cell_id": fixture_core_components.grid.cell_id},
    )

    # Adding soil variables
    data["dissolved_ammonium"] = DataArray(np.array([5.0e-2] * n_cells))
    data["dissolved_nitrate"] = DataArray(np.array([7.5e-1] * n_cells))
    data["dissolved_phosphorus"] = DataArray(np.array([3.0e-3] * n_cells))

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
def fixture_canopy_layer_data():
    """Shared canopy layer data.

    The fixture supplies a dictionary of data values expected from the canopy cohort
    data and subcanopy biomasses in the plants_data fixture.

    Each entry provides a tuple of the variable name to be tested, the data itself and
    then the vertical layer indices into which to insert the data. For the subcanopy
    masses, which only have a single layer, the vertical layer indices is set to None.
    """

    return {
        "layer_heights_full": (
            "layer_heights",
            np.array(
                [
                    [31.66797952, 31.66797952, 31.66797952, 31.66797952],
                    [29.66797952, 29.66797952, 29.66797952, 29.66797952],
                    [28.57219268, 28.34012822, 27.87517919, 1.02256003],
                    [27.87517997, 27.35745311, np.nan, np.nan],
                    [27.05144791, np.nan, np.nan, np.nan],
                    [0.1, 0.1, 0.1, 0.1],
                    [-0.5, -0.5, -0.5, -0.5],
                    [-1.0, -1.0, -1.0, -1.0],
                ]
            ),
            [0, 1, 2, 3, 4, 11, 12, 13],
            # index_filled_atmosphere, index_surface, index_all_soil
        ),
        "layer_heights_canopy": (
            "layer_heights",
            np.array(
                [
                    [31.66797952, 31.66797952, 31.66797952, 31.66797952],
                    [29.66797952, 29.66797952, 29.66797952, 29.66797952],
                    [28.57219268, 28.34012822, 27.87517919, 1.02256003],
                    [27.87517997, 27.35745311, np.nan, np.nan],
                    [27.05144791, np.nan, np.nan, np.nan],
                ],
            ),
            [0, 1, 2, 3, 4],
            # index_above, index_filled_canopy),
        ),
        "leaf_area_index": (
            "leaf_area_index",
            np.array(
                [
                    [1.76395258e00, 1.76394186e00, 1.76400479e00, 1.79998897e00],
                    [1.76405508e00, 1.76443550e00, 1.72228517e00, 1.14824589e-04],
                    [1.76388228e00, 1.75668428e00, np.nan, np.nan],
                    [1.73664971e00, np.nan, np.nan, np.nan],
                ]
            ),
            [1, 2, 3, 4],
            # index_filled_canopy,
        ),
        "layer_fapar": (
            "layer_fapar",
            np.array(
                [
                    [5.86036011e-01, 5.86033790e-01, 5.86046818e-01, 5.93428098e-01],
                    [2.42606587e-01, 2.42640479e-01, 2.38983923e-01, 2.33415558e-05],
                    [1.00419115e-01, 1.00144835e-01, np.nan, np.nan],
                    [4.11687555e-02, np.nan, np.nan, np.nan],
                ]
            ),
            [1, 2, 3, 4],
            # index_filled_canopy,
        ),
        "shortwave_absorption": (
            # So identical to the fapar but converted through to the DSR
            # values and adding the remaining radiation absorbed by subcanopy vegetation
            # and reaching the topsoil
            "shortwave_absorption",
            np.array(
                [
                    [5.86036011e-01, 5.86033790e-01, 5.86046818e-01, 5.93428098e-01],
                    [2.42606587e-01, 2.42640479e-01, 2.38983923e-01, 2.33415558e-05],
                    [1.00419115e-01, 1.00144835e-01, np.nan, np.nan],
                    [4.11687555e-02, np.nan, np.nan, np.nan],
                    [1.82376010e-02, 4.36072953e-02, 1.07190786e-01, 2.49062378e-01],
                    [1.15319309e-02, 2.75736001e-02, 6.77784728e-02, 1.57486182e-01],
                ]
            )
            * 1000
            / 2.04,
            [1, 2, 3, 4, 11, 12],
            # index_filled_canopy, index_topsoil
        ),
        "layer_leaf_mass": (
            "layer_leaf_mass",
            np.array(
                [
                    [1.02057257e03, 1.02056636e03, 1.02060277e03, 1.04142219e03],
                    [1.02063187e03, 1.02085197e03, 9.96464992e02, 6.64342267e-02],
                    [1.02053189e03, 1.01636733e03, np.nan, np.nan],
                    [1.00477590e03, np.nan, np.nan, np.nan],
                ]
            ),
            [1, 2, 3, 4],
            # index_filled_canopy,
        ),
        "subcanopy_leaf_area_index": (
            "subcanopy_leaf_area_index",
            np.repeat([0.07 * 14], 4),
            None,
        ),
        "subcanopy_fapar": (
            "subcanopy_fapar",
            np.repeat(np.exp(-0.5 * 0.07 * 14), 4),
            None,
        ),
    }
