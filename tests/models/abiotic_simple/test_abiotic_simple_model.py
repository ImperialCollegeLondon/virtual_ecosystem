"""Test module for abiotic_simple.abiotic_simple_model.py."""

from logging import INFO

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check


@pytest.fixture
def fixture_abiotic_simple_init_log():
    """Helper function to generate expected log messages."""

    return (
        (
            INFO,
            "Information required to initialise the abiotic simple model "
            "successfully extracted.",
        ),
        (INFO, "abiotic_simple model: required initial data variables checked"),
        *(
            (INFO, f"Adding data array for '{v}'")
            for v in (
                # vars_populated_by_init is not currently guaranteed to be in the order
                # in which the variables are populated
                "vapour_pressure_deficit_ref",
                "vapour_pressure_ref",
                "air_temperature",
                "relative_humidity",
                "vapour_pressure_deficit",
                "wind_speed",
                "vapour_pressure",
                "atmospheric_pressure",
                "atmospheric_co2",
                "soil_temperature",
                "canopy_temperature",
                "net_radiation",
                "diurnal_temperature_range",
            )
        ),
    )


@pytest.fixture
def fixture_abiotic_simple_init_data(dummy_climate_data_varying_canopy):
    """Returns a reduced dataset suitable for initialising an Abiotic Model."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Reduce to data to initialise model
    init_data = Data(grid=dummy_climate_data_varying_canopy.grid)
    for var in AbioticSimpleModel.vars_required_for_init:
        init_data[var] = dummy_climate_data_varying_canopy[var]

    return init_data


def test_abiotic_simple_model_initialization(
    caplog,
    fixture_abiotic_simple_init_data,
    fixture_core_components,
    fixture_pyrealm_config,
    fixture_abiotic_simple_init_log,
):
    """Test `AbioticSimpleModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_ecosystem.models.abiotic_simple.model_config import (
        AbioticSimpleConfiguration,
    )

    default_config = AbioticSimpleConfiguration()

    # Initialize model
    model = AbioticSimpleModel(
        data=fixture_abiotic_simple_init_data,
        core_components=fixture_core_components,
        model_configuration=default_config,
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    # In cases where it passes then checks that the object has the right
    # properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "abiotic_simple"
    assert repr(model) == "AbioticSimpleModel(update_interval=1209600 seconds)"
    assert model.bounds == default_config.bounds

    # Final check that expected logging entries are produced
    log_check(caplog, fixture_abiotic_simple_init_log[1:])


@pytest.mark.parametrize(
    "cfg_string",
    [
        pytest.param(
            (
                "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
                "[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n"
            ),
            id="default_config",
        ),
        pytest.param(
            (
                "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
                "[core.timing]\nupdate_interval = '1 week'\n"
                "[abiotic_simple.constants]\nplaceholder = 20\n"
            ),
            id="modified_config_correct",
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog,
    fixture_abiotic_simple_init_data,
    cfg_string,
    fixture_abiotic_simple_init_log,
):
    """Test that the initialisation of the simple abiotic model works as expected."""
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    config_data = ConfigurationLoader(cfg_strings=cfg_string)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    caplog.clear()

    # Check whether model is initialised (or not) as expected
    AbioticSimpleModel.from_config(
        data=fixture_abiotic_simple_init_data,
        configuration=configuration,
        core_components=core_components,
    )

    # Final check that expected logging entries are produced
    log_check(caplog, fixture_abiotic_simple_init_log)


def test_setup_and_update_abiotic_simple_model(
    fixture_abiotic_simple_init_data,
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_pyrealm_config,
):
    """Test set up and update."""

    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_ecosystem.models.abiotic_simple.model_config import (
        AbioticSimpleConfiguration,
    )

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    model = AbioticSimpleModel(
        data=fixture_abiotic_simple_init_data,
        core_components=fixture_core_components,
        model_configuration=AbioticSimpleConfiguration(),
        pyrealm_core_constants=fixture_pyrealm_config.core,
    )

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [21.48431, 21.832134, 22.179959, 22.527783],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((4, 3), 0.423372),
            dims=["cell_id", "time_index"],
            coords={"cell_id": [0, 1, 2, 3]},
        ),
    )

    # Add update data to the model data
    for var in AbioticSimpleModel.vars_required_for_update:
        model.data[var] = dummy_climate_data_varying_canopy[var]

    # Run the update step
    model.update(time_index=0)

    for var in [
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
        "wind_speed",
        "net_radiation",
    ]:
        assert var in model.data

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.870794, 29.913863, 29.956931, np.nan],
        [29.035646, 29.357097, np.nan, np.nan],
        [27.769159, np.nan, np.nan, np.nan],
        [25.871986, 27.247991, 28.623995, 30.0],
    ]
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    exp_wind = lyr_strct.from_template()
    exp_wind[lyr_strct.index_filled_atmosphere] = [
        [1.0, 1.0, 1.0, 1.0],
        [0.993673, 0.995782, 0.997891, np.nan],
        [0.953925, 0.969284, np.nan, np.nan],
        [0.885976, np.nan, np.nan, np.nan],
        [0.434528, 0.623019, 0.811509, 1.0],
    ]
    xr.testing.assert_allclose(model.data["wind_speed"], exp_wind)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [21.48431, 21.832134, 22.179959, 22.527783],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    exp_netrad = lyr_strct.from_template()
    exp_netrad[lyr_strct.index_filled_canopy] = [
        [179.955, 179.955, 179.955, np.nan],
        [159.960, 159.958, np.nan, np.nan],
        [119.966, np.nan, np.nan, np.nan],
    ]
    exp_netrad[lyr_strct.index_surface_scalar] = [179.975, 179.969, 179.962, 179.954]
    exp_netrad[lyr_strct.index_topsoil_scalar] = [179.988, 179.987, 179.986, 179.986]

    xr.testing.assert_allclose(model.data["net_radiation"], exp_netrad)
