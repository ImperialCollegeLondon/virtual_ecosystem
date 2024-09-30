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
                "litter model: init data missing required var " "'litter_pool_woody'",
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
                "litter model: init data missing required var " "'lignin_woody'",
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
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config=config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = LitterModel.from_config(
            data=dummy_litter_data,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.litter_decomp_temp_response == temp_response

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update(fixture_litter_model, dummy_litter_data):
    """Test to check that the update step works and increments the update step."""

    end_above_meta = [0.3154561, 0.15193439, 0.07892301, 0.0712972]
    end_above_struct = [0.50519138, 0.25011962, 0.10250070, 0.11882651]
    end_woody = [4.77403361, 11.89845863, 7.3598224, 7.3298224]
    end_below_meta = [0.3976309, 0.3630269, 0.06787947, 0.07794085]
    end_below_struct = [0.61050583, 0.32205947352, 0.02014514530, 0.03468376530]
    end_lignin_above_struct = [0.49726219, 0.10065698, 0.67693666, 0.6673972]
    end_lignin_woody = [0.49580543, 0.7978783, 0.35224272, 0.35012606]
    end_lignin_below_struct = [0.49974338, 0.26270806, 0.74846367, 0.71955592]
    end_c_n_above_metabolic = [7.3918226, 8.9320212, 10.413317, 9.8624367]
    end_c_n_above_structural = [37.5547150, 43.3448492, 48.0974058, 52.0359678]
    end_c_n_woody = [55.5816919, 63.2550698, 47.5208477, 59.0819914]
    end_c_n_below_metabolic = [10.7299421, 11.3394567, 15.1984024, 12.2222413]
    end_c_n_below_structural = [50.6228215, 55.9998994, 73.0948342, 58.6661277]
    end_c_p_above_metabolic = [69.965838, 68.549282, 107.38423, 96.583573]
    end_c_p_above_structural = [346.048307, 472.496124, 465.834123, 525.882608]
    end_c_p_woody = [560.22870571, 762.56863636, 848.03530307, 600.40427444]
    end_c_p_below_metabolic = [308.200782, 405.110726, 314.824814, 372.870229]
    end_c_p_below_structural = [563.06464, 597.68324, 772.78968, 609.82810]
    c_mineral = [0.02652423, 0.02033658, 0.00746131, 0.00746131]
    n_mineral = [0.00595963, 0.00379074, 0.00085095, 0.0009043]
    p_mineral = [4.39937479e-4, 2.13832149e-4, 6.40698004e-5, 6.56405873e-5]

    fixture_litter_model.update(time_index=0)

    # Check that data fixture has been updated correctly
    assert np.allclose(dummy_litter_data["litter_pool_above_metabolic"], end_above_meta)
    assert np.allclose(
        dummy_litter_data["litter_pool_above_structural"], end_above_struct
    )
    assert np.allclose(dummy_litter_data["litter_pool_woody"], end_woody)
    assert np.allclose(dummy_litter_data["litter_pool_below_metabolic"], end_below_meta)
    assert np.allclose(
        dummy_litter_data["litter_pool_below_structural"], end_below_struct
    )
    assert np.allclose(
        dummy_litter_data["lignin_above_structural"], end_lignin_above_struct
    )
    assert np.allclose(dummy_litter_data["lignin_woody"], end_lignin_woody)
    assert np.allclose(
        dummy_litter_data["lignin_below_structural"], end_lignin_below_struct
    )
    assert np.allclose(
        dummy_litter_data["c_n_ratio_above_metabolic"], end_c_n_above_metabolic
    )
    assert np.allclose(
        dummy_litter_data["c_n_ratio_above_structural"], end_c_n_above_structural
    )
    assert np.allclose(dummy_litter_data["c_n_ratio_woody"], end_c_n_woody)
    assert np.allclose(
        dummy_litter_data["c_n_ratio_below_metabolic"], end_c_n_below_metabolic
    )
    assert np.allclose(
        dummy_litter_data["c_n_ratio_below_structural"], end_c_n_below_structural
    )
    assert np.allclose(
        dummy_litter_data["c_p_ratio_above_metabolic"], end_c_p_above_metabolic
    )
    assert np.allclose(
        dummy_litter_data["c_p_ratio_above_structural"], end_c_p_above_structural
    )
    assert np.allclose(dummy_litter_data["c_p_ratio_woody"], end_c_p_woody)
    assert np.allclose(
        dummy_litter_data["c_p_ratio_below_metabolic"], end_c_p_below_metabolic
    )
    assert np.allclose(
        dummy_litter_data["c_p_ratio_below_structural"], end_c_p_below_structural
    )
    assert np.allclose(dummy_litter_data["litter_C_mineralisation_rate"], c_mineral)
    assert np.allclose(dummy_litter_data["litter_N_mineralisation_rate"], n_mineral)
    assert np.allclose(dummy_litter_data["litter_P_mineralisation_rate"], p_mineral)
