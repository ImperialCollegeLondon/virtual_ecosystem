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
]


@pytest.mark.parametrize(
    "raises,expected_log_entries",
    [
        (does_not_raise(), tuple(MODEL_VAR_CHECK_LOG)),
    ],
)
def test_abiotic_simple_model_initialization(
    caplog,
    dummy_climate_data,
    fixture_core_components,
    raises,
    expected_log_entries,
):
    """Test `AbioticSimpleModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
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
            data=dummy_climate_data,
            core_components=fixture_core_components,
            constants=AbioticSimpleConsts(),
        )

        # In cases where it passes then checks that the object has the right properties
        assert isinstance(model, BaseModel)
        assert model.model_name == "abiotic_simple"
        assert repr(model) == "AbioticSimpleModel(update_interval=1209600 seconds)"
        assert model.bounds == AbioticSimpleBounds()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,relative_humid,raises,expected_log_entries",
    [
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n",
            5.4,
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
                ]
                + MODEL_VAR_CHECK_LOG,
            ),
            id="default_config",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "relative_humidity_gradient = 10.2\n",
            10.2,
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
                ]
                + MODEL_VAR_CHECK_LOG,
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "relative_humidity_grad = 10.2\n",
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for AbioticSimpleConsts: "
                    "relative_humidity_grad",
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
    dummy_climate_data,
    cfg_string,
    relative_humid,
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
            data=dummy_climate_data,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.relative_humidity_gradient == relative_humid

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup(
    dummy_climate_data,
):
    """Test set up and update."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Build the config object and core components
    config = Config(
        cfg_strings="[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n"
    )
    core_components = CoreComponents(config)

    # initialise model
    model = AbioticSimpleModel.from_config(
        data=dummy_climate_data,
        core_components=core_components,
        config=config,
    )

    model.setup()

    xr.testing.assert_allclose(
        model.data["soil_temperature"],
        DataArray(
            np.full((15, 3), np.nan),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, 15),
                "layer_roles": (
                    "layers",
                    core_components.layer_structure.layer_roles,
                ),
                "cell_id": [0, 1, 2],
            },
        ),
    )
    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((3, 3), 0.141727),
            dims=["cell_id", "time_index"],
            coords={
                "cell_id": [0, 1, 2],
            },
        ),
    )

    # Run the update step
    model.update(time_index=0)

    exp_temperature = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.91965, 29.91965, 29.91965],
                    [29.414851, 29.414851, 29.414851],
                    [28.551891, 28.551891, 28.551891],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [26.19, 26.19, 26.19],
                    [22.81851, 22.81851, 22.81851],
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
                core_components.layer_structure.layer_roles,
            ),
            "cell_id": [0, 1, 2],
        },
    )

    xr.testing.assert_allclose(dummy_climate_data["air_temperature"], exp_temperature)
