"""Test module for litter_model.py."""

from logging import ERROR, INFO

import numpy as np
import pytest
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import InitialisationError

# Define expected init log messages for all data present and no data present
LITTER_INIT_CHECKS = ((INFO, "litter model: required initial data variables checked"),)

LITTER_ERROR_CHECKS = (
    (
        ERROR,
        "litter model: input data is missing required initialisation variables:",
    ),
    (ERROR, "litter model: Problems with initial model data: check log."),
)


def test_litter_model_initialization(
    caplog, fixture_litter_init_data, fixture_core_components, fixture_litter_constants
):
    """Test `LitterModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    model = LitterModel(
        data=fixture_litter_init_data,
        core_components=fixture_core_components,
        model_constants=fixture_litter_constants,
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "litter"
    assert str(model) == "A litter model instance"
    assert repr(model) == "LitterModel(update_interval=1209600 seconds)"

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=LITTER_INIT_CHECKS,
    )


def test_litter_model_initialization_no_data(
    caplog, fixture_core_components, fixture_litter_constants
):
    """Test `LitterModel` initialization fails when all data is missing."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    caplog.clear()

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        litter_data = Data(grid)

        LitterModel(
            data=litter_data,
            core_components=fixture_core_components,
            model_constants=fixture_litter_constants,
        )

    # Final check that expected logging entries are produced, do not match list of
    # missing variables.
    log_check(caplog, expected_log=LITTER_ERROR_CHECKS, match_message_start=False)


@pytest.mark.parametrize(
    argnames="var,values,msg",
    argvalues=(
        pytest.param(
            "litter_pool_above_metabolic_cnp",
            DataArray(
                np.stack(
                    [
                        [0.05, 0.02, -0.1, -0.1],
                        [0.05, 0.02, 0.02, 0.02],
                        [0.05, 0.02, 0.02, 0.02],
                    ],
                    axis=1,
                ),
                dims=["cell_id", "element"],
            ),
            "Negative pool sizes found in: ",
            id="bad pool bounds",
        ),
        pytest.param(
            "lignin_woody",
            DataArray([0.5, 0.4, 1.1, 1.1], dims=["cell_id"]),
            "Lignin proportions not between 0 and 1 found in: ",
            id="bad lignin bounds",
        ),
    ),
)
def test_litter_model_initialization_errors(
    caplog,
    fixture_litter_init_data,
    fixture_core_components,
    fixture_litter_constants,
    var,
    values,
    msg,
):
    """Test `LitterModel` initialization fails when litter pools are out of bounds."""
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    with pytest.raises(InitialisationError):
        # Put incorrect data in for lmwc
        fixture_litter_init_data[var] = values

        LitterModel(
            data=fixture_litter_init_data,
            core_components=fixture_core_components,
            model_constants=fixture_litter_constants,
        )

    # Final check that the last log entry is as expected
    log_check(caplog, expected_log=((ERROR, msg),), subset=slice(-1, None, None))


@pytest.mark.parametrize(
    "cfg_string,temp_response",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '24 hours'\n[litter]\n",
            3.36,
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '24 hours'\n"
            "[litter.constants]\nlitter_decomp_temp_response = 4.44\n",
            4.44,
            id="modified_config_correct",
        ),
    ],
)
def test_generate_litter_model(
    caplog,
    fixture_litter_init_data,
    cfg_string,
    temp_response,
):
    """Test that the function to initialise the litter model behaves as expected."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    config_data = ConfigurationLoader(cfg_strings=cfg_string)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    caplog.clear()

    # Check whether model is initialised (or not) as expected
    model = LitterModel.from_config(
        data=fixture_litter_init_data,
        configuration=configuration,
        core_components=core_components,
    )
    assert model.model_constants.litter_decomp_temp_response == temp_response

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        (
            (
                INFO,
                "Information required to initialise the litter model successfully "
                "extracted.",
            ),
            *LITTER_INIT_CHECKS,
        ),
    )


def test_update(fixture_litter_model, dummy_litter_data):
    """Test to check that the update step works and increments the update step."""

    expected_output = {
        "litter_pool_above_metabolic_cnp": np.stack(
            [
                [0.31274778, 0.14733378, 0.07884319, 0.07237949],
                [0.04155601, 0.01679779, 0.00720536, 0.00722372],
                [0.0051371875, 0.0021249325, 0.0007146426, 0.0007456092],
            ],
            axis=1,
        ),
        "litter_pool_above_structural_cnp": np.stack(
            [
                [0.50473556, 0.24936209, 0.10274537, 0.11665499],
                [0.01340387, 0.00576308, 0.00207896, 0.00214561],
                [0.0014833637, 0.0005261425, 0.0002250811, 0.0002017854],
            ],
            axis=1,
        ),
        "litter_pool_woody_cnp": np.stack(
            [
                [4.774026, 11.89845637, 7.35980938, 7.32981591],
                [0.08590272676, 0.1881151570, 0.15512843175, 0.1240644940],
                [0.00854665833, 0.01560505795, 0.00867934648, 0.01221675791],
            ],
            axis=1,
        ),
        "litter_pool_below_metabolic_cnp": np.stack(
            [
                [0.39768414, 0.36316585, 0.06791351, 0.07781341],
                [0.036463742, 0.031780242, 0.004463859, 0.005972943],
                [0.00126489842, 0.00089871328, 0.00021555604, 0.00021591806],
            ],
            axis=1,
        ),
        "litter_pool_below_structural_cnp": np.stack(
            [
                [0.6105005, 0.32204064, 0.02014513, 0.03468225],
                [0.01197838, 0.00567122, 0.00027473, 0.00047664],
                [0.0010938513, 0.0005303060, 2.5977932e-5, 4.5660957e-5],
            ],
            axis=1,
        ),
        "lignin_above_structural": [0.49765798, 0.10073481, 0.68181057, 0.68425001],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974337, 0.26270880, 0.74846363, 0.71955458],
        "litter_mineralisation_rate_cnp": np.stack(
            [
                [0.0266645, 0.02019299, 0.00756695, 0.00762047],
                [0.006003, 0.00375757, 0.00087354, 0.00093259],
                [4.46372e-4, 2.12047e-4, 6.6561e-5, 6.70468e-5],
            ],
            axis=1,
        ),
    }

    # Add the data required for update
    for var in fixture_litter_model.vars_required_for_update:
        fixture_litter_model.data[var] = dummy_litter_data[var]

    fixture_litter_model.update(time_index=0)

    # Check that data fixture has been updated correctly
    for output in expected_output.keys():
        assert np.allclose(fixture_litter_model.data[output], expected_output[output])
