"""Test module for litter_model.py."""

from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError


def test_litter_model_initialization(
    caplog, dummy_litter_data, fixture_core_components
):
    """Test `LitterModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.litter.constants import LitterConsts
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    model = LitterModel(
        data=dummy_litter_data,
        core_components=fixture_core_components,
        model_constants=LitterConsts(),
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "litter"
    assert str(model) == "A litter model instance"
    assert repr(model) == "LitterModel(update_interval=1209600 seconds)"

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (DEBUG, "litter model: required var 'litter_pool_above_metabolic' checked"),
            (
                DEBUG,
                "litter model: required var 'litter_pool_above_structural' checked",
            ),
            (DEBUG, "litter model: required var 'litter_pool_woody' checked"),
            (DEBUG, "litter model: required var 'litter_pool_below_metabolic' checked"),
            (
                DEBUG,
                "litter model: required var 'litter_pool_below_structural' checked",
            ),
            (DEBUG, "litter model: required var 'lignin_above_structural' checked"),
            (DEBUG, "litter model: required var 'lignin_woody' checked"),
            (DEBUG, "litter model: required var 'lignin_below_structural' checked"),
            (DEBUG, "litter model: required var 'c_n_ratio_above_metabolic' checked"),
            (DEBUG, "litter model: required var 'c_n_ratio_above_structural' checked"),
            (DEBUG, "litter model: required var 'c_n_ratio_woody' checked"),
            (DEBUG, "litter model: required var 'c_n_ratio_below_metabolic' checked"),
            (DEBUG, "litter model: required var 'c_n_ratio_below_structural' checked"),
            (DEBUG, "litter model: required var 'c_p_ratio_above_metabolic' checked"),
            (DEBUG, "litter model: required var 'c_p_ratio_above_structural' checked"),
            (DEBUG, "litter model: required var 'c_p_ratio_woody' checked"),
            (DEBUG, "litter model: required var 'c_p_ratio_below_metabolic' checked"),
            (DEBUG, "litter model: required var 'c_p_ratio_below_structural' checked"),
        ),
    )


def test_litter_model_initialization_no_data(caplog, fixture_core_components):
    """Test `LitterModel` initialization fails when all data is missing."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.litter.constants import LitterConsts
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    caplog.clear()

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        litter_data = Data(grid)

        LitterModel(
            data=litter_data,
            core_components=fixture_core_components,
            model_constants=LitterConsts(),
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (
                ERROR,
                "litter model: init data missing required var "
                "'litter_pool_above_metabolic'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'litter_pool_above_structural'",
            ),
            (
                ERROR,
                "litter model: init data missing required var 'litter_pool_woody'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'litter_pool_below_metabolic'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'litter_pool_below_structural'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'lignin_above_structural'",
            ),
            (
                ERROR,
                "litter model: init data missing required var 'lignin_woody'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'lignin_below_structural'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_n_ratio_above_metabolic'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_n_ratio_above_structural'",
            ),
            (ERROR, "litter model: init data missing required var 'c_n_ratio_woody'"),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_n_ratio_below_metabolic'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_n_ratio_below_structural'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_p_ratio_above_metabolic'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_p_ratio_above_structural'",
            ),
            (ERROR, "litter model: init data missing required var 'c_p_ratio_woody'"),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_p_ratio_below_metabolic'",
            ),
            (
                ERROR,
                "litter model: init data missing required var "
                "'c_p_ratio_below_structural'",
            ),
            (ERROR, "litter model: error checking vars_required_for_init, see log."),
        ),
    )


def test_litter_model_initialization_bad_pool_bounds(
    caplog, dummy_litter_data, fixture_core_components
):
    """Test `LitterModel` initialization fails when litter pools are out of bounds."""
    from virtual_ecosystem.models.litter.constants import LitterConsts
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    with pytest.raises(InitialisationError):
        # Put incorrect data in for lmwc
        dummy_litter_data["litter_pool_above_metabolic"] = DataArray(
            [0.05, 0.02, -0.1, -0.1], dims=["cell_id"]
        )

        LitterModel(
            data=dummy_litter_data,
            core_components=fixture_core_components,
            model_constants=LitterConsts,
        )

    # Final check that the last log entry is as expected
    log_check(
        caplog,
        expected_log=((ERROR, "Negative pool sizes found in: "),),
        subset=slice(-1, None, None),
    )


def test_litter_model_initialization_bad_lignin_bounds(
    caplog, dummy_litter_data, fixture_core_components
):
    """Test `LitterModel` initialization fails for lignin proportions not in bounds."""
    from virtual_ecosystem.models.litter.constants import LitterConsts
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    with pytest.raises(InitialisationError):
        # Make four cell grid
        litter_data = deepcopy(dummy_litter_data)
        # Put incorrect data in for woody lignin
        litter_data["lignin_woody"] = DataArray([0.5, 0.4, 1.1, 1.1], dims=["cell_id"])

        LitterModel(
            data=litter_data,
            core_components=fixture_core_components,
            model_constants=LitterConsts,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=((ERROR, "Lignin proportions not between 0 and 1 found in: "),),
        subset=slice(-1, None, None),
    )


def test_litter_model_initialization_bad_nutrient_ratio_bounds(
    caplog, dummy_litter_data, fixture_core_components
):
    """Test `LitterModel` initialization fails for nutrient ratios not in bounds."""
    from virtual_ecosystem.models.litter.constants import LitterConsts
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    with pytest.raises(InitialisationError):
        # Make four cell grid
        litter_data = deepcopy(dummy_litter_data)
        # Put incorrect data in for woody lignin
        litter_data["c_n_ratio_woody"] = DataArray(
            [23.3, 45.6, -23.4, -11.1], dims=["cell_id"]
        )

        LitterModel(
            data=litter_data,
            core_components=fixture_core_components,
            model_constants=LitterConsts,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=((ERROR, "Negative nutrient ratios found in: "),),
        subset=slice(-1, None, None),
    )


@pytest.mark.parametrize(
    "cfg_string,temp_response,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '24 hours'\n[litter]\n",
            3.36,
            does_not_raise(),
            (
                (INFO, "Initialised litter.LitterConsts from config"),
                (
                    INFO,
                    "Information required to initialise the litter model successfully "
                    "extracted.",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_woody' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_above_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_woody' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'lignin_below_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_above_structural' checked",
                ),
                (DEBUG, "litter model: required var 'c_n_ratio_woody' checked"),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_below_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_above_structural' checked",
                ),
                (DEBUG, "litter model: required var 'c_p_ratio_woody' checked"),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_below_structural' checked",
                ),
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '24 hours'\n"
            "[litter.constants.LitterConsts]\nlitter_decomp_temp_response = 4.44\n",
            4.44,
            does_not_raise(),
            (
                (INFO, "Initialised litter.LitterConsts from config"),
                (
                    INFO,
                    "Information required to initialise the litter model successfully "
                    "extracted.",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_above_structural' checked",
                ),
                (DEBUG, "litter model: required var 'litter_pool_woody' checked"),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'litter_pool_below_structural' checked",
                ),
                (DEBUG, "litter model: required var 'lignin_above_structural' checked"),
                (DEBUG, "litter model: required var 'lignin_woody' checked"),
                (DEBUG, "litter model: required var 'lignin_below_structural' checked"),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_above_structural' checked",
                ),
                (DEBUG, "litter model: required var 'c_n_ratio_woody' checked"),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_n_ratio_below_structural' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_above_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_above_structural' checked",
                ),
                (DEBUG, "litter model: required var 'c_p_ratio_woody' checked"),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_below_metabolic' checked",
                ),
                (
                    DEBUG,
                    "litter model: required var 'c_p_ratio_below_structural' checked",
                ),
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '24 hours'\n"
            "[litter.constants.LitterConsts]\ndecomp_rate = 4.44\n",
            None,
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Unknown names supplied for LitterConsts: decomp_rate"),
                (INFO, "Valid names are: "),
                (CRITICAL, "Could not initialise litter.LitterConsts from config"),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_litter_model(
    caplog,
    dummy_litter_data,
    cfg_string,
    temp_response,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the litter model behaves as expected."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)

    # TODO - This test is currently mixing the old AbioticSimpleConsts validation with
    # what will be replaced by configuration.abiotic_simple.constants. So for now, fake
    # it with a hardcoded config and let the errors run through to the old system

    config_data = ConfigurationLoader(
        cfg_strings="[core.timing]\nupdate_interval = '24 hours'\n[litter]"
    )

    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = LitterModel.from_config(
            data=dummy_litter_data,
            configuration=configuration,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.litter_decomp_temp_response == temp_response

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update(fixture_litter_model, dummy_litter_data):
    """Test to check that the update step works and increments the update step."""

    expected_output = {
        "litter_pool_above_metabolic": [0.31524887, 0.15349194, 0.08093312, 0.07547912],
        "litter_pool_above_structural": [0.50519653, 0.25060783, 0.1031738, 0.11725847],
        "litter_pool_woody": [4.774026, 11.89845637, 7.35980938, 7.32981591],
        "litter_pool_below_metabolic": [0.39768414, 0.36316585, 0.06791351, 0.07781341],
        "litter_pool_below_structural": [0.6105005, 0.32204064, 0.02014513, 0.03468225],
        "lignin_above_structural": [0.49726312, 0.10113065, 0.67996749, 0.68136766],
        "lignin_woody": [0.4958054, 0.7978783, 0.3522427, 0.350126],
        "lignin_below_structural": [0.49974337, 0.26270880, 0.74846363, 0.71955458],
        "c_n_ratio_above_metabolic": [7.5450184, 8.9814418, 10.998779, 10.175958],
        "c_n_ratio_above_structural": [37.6666294, 43.3945275, 49.4785666, 54.4562879],
        "c_n_ratio_woody": [55.57479, 63.250918, 47.44333, 59.08069],
        "c_n_ratio_below_metabolic": [10.90629, 11.42741, 15.21408, 13.02765],
        "c_n_ratio_below_structural": [50.96669, 56.78504, 73.33861, 72.76419],
        "c_p_ratio_above_metabolic": [61.099543, 70.015298, 110.68070, 98.767703],
        "c_p_ratio_above_structural": [340.38278, 473.84604, 456.99901, 579.00396],
        "c_p_ratio_woody": [558.58393, 762.474347, 847.96815, 599.98045],
        "c_p_ratio_below_metabolic": [314.40006, 404.09534, 315.06196, 360.38398],
        "c_p_ratio_below_structural": [558.1202, 607.2732, 775.4709, 759.5603],
        "litter_C_mineralisation_rate": [0.02669867, 0.02028009, 0.0075954, 0.0076627],
        "litter_N_mineralisation_rate": [0.00601335, 0.0037791, 0.0008798, 0.00094215],
        "litter_P_mineralisation_rate": [0.0004477, 0.00021477, 6.7192e-5, 6.80253e-5],
    }

    fixture_litter_model.update(time_index=0)

    # Check that data fixture has been updated correctly
    for output in expected_output.keys():
        assert np.allclose(dummy_litter_data[output], expected_output[output])
