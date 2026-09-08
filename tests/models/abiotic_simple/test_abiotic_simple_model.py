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
                "diurnal_temperature_range",
                "net_radiation",
            )
        ),
    )


@pytest.fixture
def fixture_abiotic_simple_init_data(dummy_climate_data):
    """Returns a reduced dataset suitable for initialising an Abiotic Model."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Reduce to data to initialise model
    init_data = Data(grid=dummy_climate_data.grid)
    for var in AbioticSimpleModel.vars_required_for_init:
        init_data[var] = dummy_climate_data[var]

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
    dummy_climate_data,
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
        [20.131051, 21.591324, 23.142502, 24.505557],
        [22.0, 22.5, 23.0, 24.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    exp_vpdref = DataArray(
        [
            [0.280251, 0.280251, 0.280251],
            [0.535786, 0.535786, 0.535786],
            [0.884816, 0.884816, 0.884816],
            [1.341337, 1.341337, 1.341337],
        ],
        dims=["cell_id", "time_index"],
        coords={"cell_id": [0, 1, 2, 3]},
    )
    xr.testing.assert_allclose(model.data["vapour_pressure_deficit_ref"], exp_vpdref)

    # Add update data to the model data
    for var in AbioticSimpleModel.vars_required_for_update:
        model.data[var] = dummy_climate_data[var]

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
        [23.0, 24.0, 25.0, 26.0],
        [22.737281, 23.786638, 24.87785, np.nan],
        [21.039147, 22.270679, np.nan, np.nan],
        [18.463956, np.nan, np.nan, np.nan],
        [14.606371, 18.905246, 23.563744, 26.0],
    ]

    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    exp_air_temp_range = lyr_strct.from_template()
    exp_air_temp_range[lyr_strct.index_filled_atmosphere] = [
        [6, 7, 9, 11],
        [6, 7, 9, np.nan],
        [6, 7, np.nan, np.nan],
        [6, np.nan, np.nan, np.nan],
        [6, 7, 9, 11],
    ]
    exp_air_temp_range[lyr_strct.index_all_soil] = [[6, 7, 9, 11], [6, 7, 9, 11]]
    xr.testing.assert_allclose(
        model.data["diurnal_temperature_range"], exp_air_temp_range
    )

    exp_wind = lyr_strct.from_template()
    exp_wind[lyr_strct.index_filled_atmosphere] = [
        [5.000000e-01, 8.000000e-01, 1.200000e00, 1.800000e00],
        [4.871356e-01, 7.887022e-01, 1.192109e00, np.nan],
        [4.063148e-01, 7.100000e-01, np.nan, np.nan],
        [2.681506e-01, np.nan, np.nan, np.nan],
        [1.000000e-03, 8.837985e-02, 9.927933e-01, 1.800000e00],
    ]
    xr.testing.assert_allclose(model.data["wind_speed"], exp_wind)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.131051, 21.591324, 23.142502, 24.505557],
        [22.0, 22.5, 23.0, 24.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    exp_netrad = lyr_strct.from_template()
    exp_netrad[lyr_strct.index_flux_layers] = [
        [9.985148, 17.98221, 21.978714, np.nan],
        [6.989112, 7.98633, np.nan, np.nan],
        [2.993541, np.nan, np.nan, np.nan],
        [9.997471, 11.992901, 13.982868, 17.974606],
        [1.991153, 2.988293, 3.984548, 5.980574],
    ]

    xr.testing.assert_allclose(model.data["net_radiation"], exp_netrad)
