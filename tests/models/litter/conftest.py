"""Collection of fixtures to assist the testing of the litter model."""

import numpy as np
import pytest
from xarray import DataArray, concat


@pytest.fixture
def fixture_litter_model(dummy_litter_data):
    """Create a litter model fixture based on the dummy litter data."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    # Build the config object
    config = Config(
        cfg_strings="[core]\n[core.timing]\nupdate_interval = '24 hours'\n[litter]\n"
    )
    core_components = CoreComponents(config)

    return LitterModel.from_config(
        data=dummy_litter_data, core_components=core_components, config=config
    )


@pytest.fixture
def dummy_litter_data(fixture_core_components):
    """Creates a dummy litter data object for use in tests."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(cell_nx=3, cell_ny=1)
    data = Data(grid)

    # These values are taken from SAFE Project data, albeit in a very unsystematic
    # manner
    data["litter_pool_above_metabolic"] = DataArray([0.3, 0.15, 0.07], dims=["cell_id"])
    """Above ground metabolic litter pool (kg C m^-2)"""
    data["litter_pool_above_structural"] = DataArray(
        [0.5, 0.25, 0.09], dims=["cell_id"]
    )
    """Above ground structural litter pool (kg C m^-2)"""
    data["litter_pool_woody"] = DataArray([4.7, 11.8, 7.3], dims=["cell_id"])
    """Woody litter pool (kg C m^-2)"""
    data["litter_pool_below_metabolic"] = DataArray([0.4, 0.37, 0.07], dims=["cell_id"])
    """Below ground metabolic litter pool (kg C m^-2)"""
    data["litter_pool_below_structural"] = DataArray(
        [0.6, 0.31, 0.02], dims=["cell_id"]
    )
    """Below ground structural litter pool (kg C m^-2)"""
    data["lignin_above_structural"] = DataArray([0.5, 0.1, 0.7], dims=["cell_id"])
    """Proportion of above ground structural pool which is lignin [unitless]"""
    data["lignin_woody"] = DataArray([0.5, 0.8, 0.35], dims=["cell_id"])
    """Proportion of dead wood pool which is lignin [unitless]"""
    data["lignin_below_structural"] = DataArray([0.5, 0.25, 0.75], dims=["cell_id"])
    """Proportion of below ground structural pool which is lignin [unitless]"""
    data["decomposed_excrement"] = DataArray(
        [8e-07, 8.42857e-07, 3.28571e-05], dims=["cell_id"]
    )
    """Rate of excrement input from the animal model [kg C m^-2 day^-1].

    These values are completely made up, so you should not read anything into them.
    """
    data["decomposed_carcasses"] = DataArray(
        [1.0714e-4, 4.8571e-4, 1.15714e-3], dims=["cell_id"]
    )
    """Rate of carcass biomass input from the animal model [kg C m^-2 day^-1].

    These values are completely made up, so you should not read anything into them.
    """
    data["soil_temperature_mean"] = (
        concat(
            [DataArray(np.full((13, 3), np.nan)), DataArray(np.full((2, 3), 20))],
            dim="dim_0",
        )
        .rename({"dim_0": "layers", "dim_1": "cell_id"})
        .assign_coords(
            {
                "layers": np.arange(0, 15),
                "layer_roles": (
                    "layers",
                    fixture_core_components.layer_structure.layer_roles,
                ),
                "cell_id": data.grid.cell_id,
            }
        )
    )

    # The layer dependant data has to be handled separately
    data["matric_potential_mean"] = concat(
        [
            DataArray(np.full((13, 3), np.nan), dims=["layers", "cell_id"]),
            # At present the soil model only uses the top soil layer, so this is the
            # only one with real test values in
            DataArray(
                [[-10.0, -25.0, -100.0]],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((1, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": (
                "layers",
                fixture_core_components.layer_structure.layer_roles,
            ),
            "cell_id": data.grid.cell_id,
        }
    )

    data["air_temperature_mean"] = concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.844995, 29.844995, 29.844995],
                    [28.87117, 28.87117, 28.87117],
                    [27.206405, 27.206405, 27.206405],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [16.145945, 16.145945, 16.145945],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": (
                "layers",
                fixture_core_components.layer_structure.layer_roles,
            ),
            "cell_id": data.grid.cell_id,
        }
    )

    return data
