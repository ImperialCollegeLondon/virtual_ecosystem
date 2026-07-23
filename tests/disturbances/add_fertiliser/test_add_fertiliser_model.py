"""Test module for add_fertiliser.py."""

from logging import INFO

import numpy as np
import pytest

from tests.conftest import log_check


@pytest.mark.parametrize(
    "cfg_string,nitrate_fraction",
    [
        pytest.param(
            "[disturbance.add_fertiliser]\n",
            0.5,
            id="default_config",
        ),
        pytest.param(
            "[disturbance.add_fertiliser]\nrun_at=0",
            0.5,
            id="run_at_config",
        ),
        pytest.param(
            "[disturbance.add_fertiliser.constants]\nnitrate_fraction=0.75",
            0.75,
            id="modified_config_correct",
        ),
    ],
)
def test_generate_add_fertiliser_disturbance(
    caplog,
    fixture_fertiliser_init_data,
    cfg_string,
    nitrate_fraction,
):
    """Test that fertiliser addition disturbance initialisation works as expected."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.disturbances.add_fertiliser.add_fertiliser_model import (
        AddFertiliserModel,
    )

    config_data = ConfigurationLoader(cfg_strings=cfg_string)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    caplog.clear()

    # Check whether disturbance is initialised (or not) as expected
    disturbance = AddFertiliserModel.from_config(
        data=fixture_fertiliser_init_data,
        configuration=configuration,
        core_components=core_components,
        models={},
    )
    assert disturbance.constants.nitrate_fraction == nitrate_fraction

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        (
            (
                INFO,
                "Information required to initialise the fertiliser addition disturbance"
                " successfully extracted.",
            ),
            (
                INFO,
                "Fertiliser addition disturbance instance generated from "
                "configuration.",
            ),
        ),
    )


def test_disturb(fixture_add_fertiliser_model):
    """Test that fertiliser addition disturbance works as expected."""

    # Defaults to running at every step (so run twice and check it adds both times)
    fixture_add_fertiliser_model._disturb(time_index=0)

    assert np.allclose(
        fixture_add_fertiliser_model.data["soil_n_pool_nitrate"],
        np.array([0.0042969014, 0.0063192996, 0.0022178348, 0.0150155173]),
    )
    assert np.allclose(
        fixture_add_fertiliser_model.data["soil_n_pool_ammonium"],
        np.array([0.000694619638, 0.0056164624, 0.000854067, 0.0058205339]),
    )

    fixture_add_fertiliser_model._disturb(time_index=1)

    assert np.allclose(
        fixture_add_fertiliser_model.data["soil_n_pool_nitrate"],
        np.array([0.0061719014, 0.0081942996, 0.0040928348, 0.0168905173]),
    )
    assert np.allclose(
        fixture_add_fertiliser_model.data["soil_n_pool_ammonium"],
        np.array([0.001319619638, 0.0062414624, 0.001479067, 0.0064455339]),
    )
