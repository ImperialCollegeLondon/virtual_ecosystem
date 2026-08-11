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
                [0.31292847, 0.1477193, 0.07847686, 0.0712382],
                [0.04164068, 0.01683533, 0.00720338, 0.00710534],
                [0.00513782, 0.00212742, 0.00071441, 0.00072071],
            ],
            axis=1,
        ),
        "litter_pool_above_structural_cnp": np.stack(
            [
                [0.50477412, 0.24966296, 0.10312207, 0.11937046],
                [0.01340754, 0.0057693, 0.00208167, 0.00228176],
                [0.00148339, 0.00052657, 0.00022537, 0.00023009],
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
                [0.39768853, 0.36369883, 0.06830231, 0.07781341],
                [0.03646412, 0.0317839, 0.00448212, 0.00597295],
                [0.00126491, 0.0009009, 0.00021935, 0.00021592],
            ],
            axis=1,
        ),
        "litter_pool_below_structural_cnp": np.stack(
            [
                [0.61051725, 0.32260976, 0.02192288, 0.03499666],
                [0.01197869, 0.00567217, 0.0002915, 0.00047729],
                [1.09386195e-3, 5.30764789e-4, 2.94140868e-5, 4.95474953e-5],
            ],
            axis=1,
        ),
        "lignin_above_structural": [0.4976432, 0.10184581, 0.6793591, 0.668817],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974115, 0.26255194, 0.73336051, 0.71623416],
        "litter_mineralisation_rate_cnp": np.stack(
            [
                [0.02666707, 0.0202096, 0.0075679, 0.00760535],
                [0.00600377, 0.0037609, 0.00087329, 0.00092908],
                [4.46467671e-4, 2.12275106e-4, 6.64913876e-5, 6.66880931e-5],
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
