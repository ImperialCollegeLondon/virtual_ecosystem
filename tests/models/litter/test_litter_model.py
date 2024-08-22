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

    end_above_meta = [0.32007287, 0.154675362857, 0.0811650671, 0.0735392571]
    end_above_struct = [0.50535881033, 0.25073819641, 0.102511783092, 0.118837593092]
    end_woody = [4.7745168, 11.89872931, 7.3614112, 7.3314112]
    end_below_meta = [0.40675878, 0.37049895, 0.0690151, 0.07907648]
    end_below_struct = [0.610809585, 0.32254423676, 0.0201472076513, 0.0346858276513]
    end_lignin_above_struct = [0.49790843, 0.10067782, 0.70495536, 0.71045831]
    end_lignin_woody = [0.49580586, 0.79787834, 0.35224223, 0.35012603]
    end_lignin_below_struct = [0.50313573, 0.26585915, 0.7499951, 0.82142798]
    end_c_n_above_metabolic = [7.42828416, 8.93702901, 11.13974239, 10.28862956]
    end_c_n_above_structural = [37.56983094, 43.34654437, 49.02060275, 54.44715499]
    end_c_n_woody = [55.581683655, 63.25507083, 47.520800061, 59.08199528]
    end_c_n_below_metabolic = [10.90350592, 11.4669011, 15.20703826, 12.66163681]
    end_c_n_below_structural = [50.77558203, 56.38787769, 73.18371555, 64.0424462]
    c_mineral = [0.02652423, 0.02033658, 0.00746131, 0.00746131]
    n_mineral = [0.00595963, 0.00379074, 0.00085095, 0.0009043]

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
    assert np.allclose(dummy_litter_data["litter_C_mineralisation_rate"], c_mineral)
    assert np.allclose(dummy_litter_data["litter_N_mineralisation_rate"], n_mineral)
