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
    }

    for var, vals in pool_values.items():
        data[var] = DataArray(vals, dims=["cell_id"])

    # Vertically structured variables
    data["soil_temperature"] = fixture_core_components.layer_structure.from_template()
    data["soil_temperature"].loc[
        {"layers": fixture_core_components.layer_structure.index_all_soil}
    ] = np.full((2, 4), 20)

    # At present the soil model only uses the top soil layer, so this is the
    # only one with real test values in
    data["matric_potential"] = fixture_core_components.layer_structure.from_template()
    data["matric_potential"].loc[
        {"layers": fixture_core_components.layer_structure.index_topsoil}
    ] = [-10.0, -25.0, -100.0, -100.0]

    data["air_temperature"] = fixture_core_components.layer_structure.from_template()
    data["air_temperature"].loc[{"layers": [0, 1, 2, 3, 11]}] = np.array(
        [
            [30.0, 30.0, 30.0, 30.0],  # closed canopy
            [29.844995, 29.844995, 29.844995, 29.844995],
            [28.87117, 28.87117, 28.87117, 28.87117],
            [27.206405, 27.206405, 27.206405, 27.206405],
            # [22.65, 22.65, 22.65, 22.65],  # subcanopy layer removed
            [16.145945, 16.145945, 16.145945, 16.145945],  # surface
        ]
    )

    return data
