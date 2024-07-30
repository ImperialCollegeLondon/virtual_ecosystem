"""Collection of fixtures to assist the testing of the litter model."""

import numpy as np
import pytest
from xarray import DataArray


@pytest.fixture
def fixture_litter_model(dummy_litter_data, fixture_core_components):
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

    lyr_strct = fixture_core_components.layer_structure

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # These values are taken from SAFE Project data, albeit in a very unsystematic
    # manner. The repeated fourth value is simply to adapt three hand validated examples
    # to the shared fixture core components grid
    pool_values = {
        "litter_pool_above_metabolic": [0.3, 0.15, 0.07, 0.07],
        "litter_pool_above_structural": [0.5, 0.25, 0.09, 0.09],
        "litter_pool_woody": [4.7, 11.8, 7.3, 7.3],
        "litter_pool_below_metabolic": [0.4, 0.37, 0.07, 0.07],
        "litter_pool_below_structural": [0.6, 0.31, 0.02, 0.02],
        "lignin_above_structural": [0.5, 0.1, 0.7, 0.7],
        "lignin_woody": [0.5, 0.8, 0.35, 0.35],
        "lignin_below_structural": [0.5, 0.25, 0.75, 0.75],
        "decomposed_excrement": [8e-07, 8.42857e-07, 3.28571e-05, 3.28571e-05],
        "decomposed_carcasses": [1.0714e-4, 4.8571e-4, 1.15714e-3, 1.15714e-3],
        "deadwood_production": [0.075, 0.099, 0.063, 0.033],
        "leaf_turnover": [0.027, 0.0003, 0.021, 0.0285],
        "plant_reproductive_tissue_turnover": [0.003, 0.0075, 0.00255, 0.00375],
        "root_turnover": [0.027, 0.021, 0.0003, 0.0249],
        "deadwood_lignin": [0.233, 0.545, 0.612, 0.378],
        "leaf_turnover_lignin": [0.05, 0.25, 0.3, 0.57],
        "plant_reproductive_tissue_turnover_lignin": [0.01, 0.03, 0.04, 0.02],
        "root_turnover_lignin": [0.2, 0.35, 0.27, 0.4],
        "leaf_turnover_c_n_ratio": [15.0, 25.5, 43.1, 57.4],
        "plant_reproductive_tissue_turnover_c_n_ratio": [12.5, 23.8, 15.7, 18.2],
        "root_turnover_c_n_ratio": [30.3, 45.6, 43.3, 37.1],
    }

    for var, vals in pool_values.items():
        data[var] = DataArray(vals, dims=["cell_id"])

    # Vertically structured variables
    data["soil_temperature"] = lyr_strct.from_template()
    data["soil_temperature"][lyr_strct.index_topsoil] = 20
    data["soil_temperature"][lyr_strct.index_subsoil] = [19.5, 18.7, 18.7, 17.6]

    # At present the soil model only uses the top soil layer, so this is the
    # only one with real test values in
    data["matric_potential"] = lyr_strct.from_template()
    data["matric_potential"][lyr_strct.index_topsoil] = [-10.0, -25.0, -100.0, -100.0]
    data["matric_potential"][lyr_strct.index_subsoil] = [-11.0, -29.5, -123.0, -154.1]

    data["air_temperature"] = lyr_strct.from_template()
    data["air_temperature"][lyr_strct.index_filled_atmosphere] = np.array(
        [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    )[:, None]

    return data
