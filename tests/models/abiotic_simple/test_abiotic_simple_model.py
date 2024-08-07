"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (DEBUG, "abiotic_simple model: required var 'air_temperature_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'relative_humidity_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'atmospheric_pressure_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'atmospheric_co2_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'leaf_area_index' checked"),
    (DEBUG, "abiotic_simple model: required var 'layer_heights' checked"),
    (DEBUG, "abiotic_simple model: required var 'wind_speed_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'mean_annual_temperature' checked"),
]


@pytest.mark.parametrize(
    "raises,expected_log_entries",
    [
        (does_not_raise(), tuple(MODEL_VAR_CHECK_LOG)),
    ],
)
def test_abiotic_simple_model_initialization(
    caplog,
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    raises,
    expected_log_entries,
):
    """Test `AbioticSimpleModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic.constants import AbioticConsts
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            data=dummy_climate_data_varying_canopy,
            core_components=fixture_core_components,
            constants=AbioticSimpleConsts(),
        )

        # In cases where it passes then checks that the object has the right properties
        assert isinstance(model, BaseModel)
        assert model.model_name == "abiotic_simple"
        assert repr(model) == "AbioticSimpleModel(update_interval=1209600 seconds)"
        assert model.bounds == AbioticSimpleBounds()
        assert model.abiotic_constants == AbioticConsts()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,satvap1,raises,expected_log_entries",
    [
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n",
            [0.61078, 7.5, 237.3],
            does_not_raise(),
            tuple(
                [
                    (
                        INFO,
                        "Initialised abiotic_simple.AbioticSimpleConsts from config",
                    ),
                    (
                        INFO,
                        "Information required to initialise the abiotic simple model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG,
                ],
            ),
            id="default_config",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "saturation_vapour_pressure_factors = [1.0, 2.0, 3.0]\n",
            [1.0, 2.0, 3.0],
            does_not_raise(),
            tuple(
                [
                    (
                        INFO,
                        "Initialised abiotic_simple.AbioticSimpleConsts from config",
                    ),
                    (
                        INFO,
                        "Information required to initialise the abiotic simple model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG,
                ],
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "saturation_vapour_pressure_factorx = [1.0, 2.0, 3.0]\n",
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for AbioticSimpleConsts: "
                    "saturation_vapour_pressure_factorx",
                ),
                (INFO, "Valid names are: "),
                (
                    CRITICAL,
                    "Could not initialise abiotic_simple.AbioticSimpleConsts "
                    "from config",
                ),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog,
    dummy_climate_data_varying_canopy,
    cfg_string,
    satvap1,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the simple abiotic model works as expected."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticSimpleModel.from_config(
            data=dummy_climate_data_varying_canopy,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.saturation_vapour_pressure_factors == satvap1

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup(dummy_climate_data_varying_canopy, fixture_core_components):
    """Test set up and update."""

    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    model = AbioticSimpleModel(
        data=dummy_climate_data_varying_canopy,
        core_components=fixture_core_components,
    )

    model.setup()

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.712458, 21.317566, 21.922674, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.712458, 21.317566, 21.922674, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((4, 3), 0.141727),
            dims=["cell_id", "time_index"],
            coords={"cell_id": [0, 1, 2, 3]},
        ),
    )
    exp_wind_speed = lyr_strct.from_template()
    exp_wind_speed[lyr_strct.index_filled_atmosphere] = [
        [0.727122, 0.743643, 0.772241, 0.772241],
        [0.615474, 0.64478, 0.691463, 0.691463],
        [0.574914, 0.609452, np.nan, np.nan],
        [0.47259, np.nan, np.nan, np.nan],
        [0.414663, 0.544804, 0.635719, 0.635719],
    ]
    xr.testing.assert_allclose(model.data["wind_speed"], exp_wind_speed)

    exp_sens_heat_flux = lyr_strct.from_template()
    exp_sens_heat_flux[1] = [0, 0, 0, 0]
    xr.testing.assert_allclose(model.data["sensible_heat_flux"], exp_sens_heat_flux)

    for var in [
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
        "sensible_heat_flux",
        "wind_speed",
        "molar_density_air",
        "specific_heat_air",
    ]:
        assert var in model.data

    # Run the update step
    model.update(time_index=0)

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.91965, 29.946434, 29.973217, 29.973217],
        [29.414851, 29.609901, np.nan, np.nan],
        [28.551891, np.nan, np.nan, np.nan],
        [22.81851, 25.21234, 27.60617, 27.60617],
    ]
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.712458, 21.317566, 21.922674, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    exp_wind_speed = lyr_strct.from_template()
    exp_wind_speed[lyr_strct.index_filled_atmosphere] = [
        [0.727122, 0.743643, 0.772241, 0.772241],
        [0.615474, 0.64478, 0.691463, 0.691463],
        [0.574914, 0.609452, np.nan, np.nan],
        [0.47259, np.nan, np.nan, np.nan],
        [0.414663, 0.544804, 0.635719, 0.635719],
    ]
    xr.testing.assert_allclose(model.data["wind_speed"], exp_wind_speed)


def test_update_wind(dummy_climate_data_varying_canopy, fixture_core_components):
    """Test wind update for abiotic simple model."""

    from virtual_ecosystem.models.abiotic.constants import AbioticConsts
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import update_wind

    data = dummy_climate_data_varying_canopy
    lyr_strct = fixture_core_components.layer_structure

    microclimate_data = {}
    microclimate_data["air_temperature"] = data["air_temperature"]
    microclimate_data["atmospheric_pressure"] = data["atmospheric_pressure"]
    microclimate_data["sensible_heat_flux"] = data["sensible_heat_flux"]

    result = update_wind(
        data=data,
        microclimate_data=microclimate_data,
        layer_structure=lyr_strct,
        time_index=0,
        abiotic_constants=AbioticConsts(),
        core_constants=fixture_core_components.core_constants,
    )

    exp_wind_speed = lyr_strct.from_template()
    exp_wind_speed[lyr_strct.index_filled_atmosphere] = [
        [0.727122, 0.743643, 0.772241, 0.772241],
        [0.615474, 0.64478, 0.691463, 0.691463],
        [0.574914, 0.609452, np.nan, np.nan],
        [0.47259, np.nan, np.nan, np.nan],
        [0.414663, 0.544804, 0.635719, 0.635719],
    ]
    xr.testing.assert_allclose(result["wind_speed"], exp_wind_speed)

    exp_molar_density = lyr_strct.from_template()
    exp_molar_density[lyr_strct.index_filled_atmosphere] = [
        [38.110259, 38.110259, 38.110259, 38.110259],
        [38.129755, 38.129755, 38.129755, 38.129755],
        [38.252699, 38.252699, np.nan, np.nan],
        [38.46472, np.nan, np.nan, np.nan],
        [39.935316, 39.935316, 39.935316, 39.935316],
    ]
    xr.testing.assert_allclose(result["molar_density_air"], exp_molar_density)

    exp_spec_heat = lyr_strct.from_template()
    exp_spec_heat[lyr_strct.index_filled_atmosphere] = [
        [29.214, 29.214, 29.214, 29.214],
        [29.213783, 29.213783, 29.213783, 29.213783],
        [29.212445, 29.212445, np.nan, np.nan],
        [29.210245, np.nan, np.nan, np.nan],
        [29.198443, 29.198443, 29.198443, 29.198443],
    ]
    xr.testing.assert_allclose(result["specific_heat_air"], exp_spec_heat)
