"""Fixtures for add-Fertiliser tests."""

import pytest


@pytest.fixture
def fixture_fertiliser_init_data(fixture_core_components):
    """Creates a dummy data object for use in fertiliser addition tests."""
    from xarray import DataArray

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    data_values = {
        "soil_n_pool_ammonium": [6.9619638e-5, 0.0049914624, 0.000229067, 0.0051955339],
        "soil_n_pool_nitrate": [0.0024219014, 0.0044442996, 0.0003428348, 0.0131405173],
    }

    for var_name, var_values in data_values.items():
        data[var_name] = DataArray(var_values, dims=["cell_id"])

    return data


@pytest.fixture
def fixture_add_fertiliser_model(fixture_fertiliser_init_data):
    """Create an add_fertiliser disturbance fixture based on the dummy data."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.disturbances.add_fertiliser.add_fertiliser_model import (
        AddFertiliserModel,
    )

    # Build the config object
    cfg_strings = (
        "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
        "[disturbance.add_fertiliser]\nrun_at=[0,1]\n"
        "[disturbance.add_fertiliser.constants]\n"
        "nitrate_fraction=0.75\ninorganic_nitrogen_addition=2.5e-3"
    )

    config_data = ConfigurationLoader(cfg_strings=cfg_strings)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    return AddFertiliserModel.from_config(
        data=fixture_fertiliser_init_data,
        configuration=configuration,
        core_components=core_components,
        models={},
    )
