"""Tests the plant community model code."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO

import numpy as np
import pytest
from numpy.testing import assert_allclose
from pandas import DataFrame

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import InitialisationError


@pytest.mark.parametrize(
    argnames="cohort_data,raises,exp_log,expected_cids",
    argvalues=[
        pytest.param(
            DataFrame(
                dict(plant_cohorts_n=np.array([5] * 4)),
            ),
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Cannot initialise plant communities from cohort data. Missing "
                    "variables: plant_cohorts_dbh, plant_cohorts_pft, "
                    "plant_cohorts_x, plant_cohorts_y",
                ),
            ),
            None,
            id="missing vars",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([-100, 0, 0, 200]),
                    plant_cohorts_y=np.array([-100, 0, 0, 200]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (ERROR, "XY coordinates in plant cohort data fall outside grid bounds"),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="xy outside grid",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 45, 45, 90]),
                    plant_cohorts_y=np.array([0, 0, 45, 90]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (ERROR, "XY coordinates in plant cohort data fall on cell boundaries"),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="xy on cell boundaries",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data validated"),),
            np.array([0, 1, 2, 3]),
            id="xy ok",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["tree"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (ERROR, "Plant cohort data includes PFT names not in flora"),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="unknown PFTs",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([-5] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "Plant cohort data individual counts must be positive integers",
                ),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="negative individual counts",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([0] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "Plant cohort data individual counts must be positive integers",
                ),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="zero individual counts",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([3.2] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "Plant cohort data individual counts must be positive integers",
                ),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="float individual counts",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([3] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([-0.5] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (ERROR, "Plant cohort DBH data must be strictly positive"),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="negative DBH",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([3] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_x=np.array([0, 90, 0, 90]),
                    plant_cohorts_y=np.array([90, 90, 0, 0]),
                    plant_cohorts_dbh=np.array([0] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (ERROR, "Plant cohort DBH data must be strictly positive"),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="zero DBH",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([0] * 4),
                    plant_cohorts_pft=np.array(["tree"] * 4),
                    plant_cohorts_x=np.array([-100, 0, 45, 200]),
                    plant_cohorts_y=np.array([-100, 0, 45, 200]),
                    plant_cohorts_dbh=np.array([-0.5] * 4),
                ),
            ),
            pytest.raises(InitialisationError),
            (
                (ERROR, "XY coordinates in plant cohort data fall outside grid bounds"),
                (ERROR, "XY coordinates in plant cohort data fall on cell boundaries"),
                (ERROR, "Plant cohort data includes PFT names not in flora"),
                (
                    ERROR,
                    "Plant cohort data individual counts must be positive integers",
                ),
                (ERROR, "Plant cohort DBH data must be strictly positive"),
                (CRITICAL, "Validation errors in plant cohort data: see above"),
            ),
            None,
            id="all sorts of wrong",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 10),
                    plant_cohorts_pft=np.array(["shrub", "broadleaf"] * 5),
                    plant_cohorts_x=np.repeat(
                        np.array([0, 90, 0, 90]), np.arange(1, 5)
                    ),
                    plant_cohorts_y=np.repeat(
                        np.array([90, 90, 0, 0]), np.arange(1, 5)
                    ),
                    plant_cohorts_dbh=np.array([0.1] * 10),
                ),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data validated"),),
            np.array([0, 1, 1, 2, 2, 2, 3, 3, 3, 3]),
            id="all good more complex",
        ),
    ],
)
def test_validate_cohort_data(
    caplog,
    fixture_flora,
    fixture_core_components,
    cohort_data,
    raises,
    exp_log,
    expected_cids,
):
    """Test the data handling of the PlantCommunities __init__."""

    from virtual_ecosystem.models.plants.communities import validate_cohort_data

    # Clear any data loading log entries
    caplog.clear()

    with raises:
        validated = validate_cohort_data(
            cohort_data=cohort_data,
            flora=fixture_flora,
            grid=fixture_core_components.grid,
        )

        # Check the assigned cell_ids
        assert_allclose(validated["plant_cohorts_cell_id"].to_numpy(), expected_cids)

    log_check(caplog, expected_log=exp_log)


@pytest.mark.parametrize(
    argnames="cohort_data,raises,exp_log, exp_n_cohorts",
    argvalues=[
        pytest.param(
            DataFrame(
                dict(plant_cohorts_n=np.array([5] * 4)),
            ),
            pytest.raises(ValueError),
            (
                (
                    CRITICAL,
                    "Cannot initialise plant communities from cohort data. Missing "
                    "variables: plant_cohorts_cell_id, plant_cohorts_dbh, "
                    "plant_cohorts_pft",
                ),
            ),
            None,
            id="missing vars",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_cell_id=np.arange(2, 6),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort data includes cell ids not in grid definition"),),
            None,
            id="bad cell ids",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["tree"] * 4),
                    plant_cohorts_cell_id=np.arange(4),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort data includes PFT names not in flora"),),
            None,
            id="bad pfts",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 4),
                    plant_cohorts_pft=np.array(["shrub"] * 4),
                    plant_cohorts_cell_id=np.arange(4),
                    plant_cohorts_dbh=np.array([0.1] * 4),
                ),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data loaded"),),
            (1, 1, 1, 1),
            id="all good",
        ),
        pytest.param(
            DataFrame(
                dict(
                    plant_cohorts_n=np.array([5] * 10),
                    plant_cohorts_pft=np.array(["shrub", "broadleaf"] * 5),
                    plant_cohorts_cell_id=np.repeat(np.arange(4), np.arange(1, 5)),
                    plant_cohorts_dbh=np.array([0.1] * 10),
                ),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data loaded"),),
            (1, 2, 3, 4),
            id="all good more complex",
        ),
    ],
)
def test_PlantCommunities__init__(
    caplog, fixture_flora, cohort_data, raises, exp_log, exp_n_cohorts
):
    """Test the data handling of the PlantCommunities __init__."""

    from pyrealm.demography.cohorts import cohort_id_generator

    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.plants.communities import PlantCommunities

    grid = Grid(cell_ny=2, cell_nx=2)

    # Clear any data loading log entries
    caplog.clear()

    with raises:
        plants_obj = PlantCommunities(
            cohort_data=cohort_data,
            flora=fixture_flora,
            grid=grid,
            cohort_id_generator=cohort_id_generator(),
        )

        if isinstance(raises, does_not_raise):
            # Check the expected contents of plants_obj
            assert len(plants_obj) == 4
            cids = {0, 1, 2, 3}
            assert set(plants_obj.keys()) == cids
            for cid in cids:
                assert len(plants_obj[cid].cohorts) == exp_n_cohorts[cid]

    log_check(caplog, expected_log=exp_log)
