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
    argnames="cohort_data,raises,exp_log,expected_cids,n_cohorts",
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
            {0: 1, 1: 1, 2: 1, 3: 1},
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
            {0: 1, 1: 2, 2: 3, 3: 4},
            id="all good more complex",
        ),
    ],
)
class TestCohortData:
    """Shared inputs into testing of cohort data validation and PlantCommunities."""

    def test_validate_cohort_data(
        self,
        caplog,
        fixture_flora,
        fixture_core_components,
        cohort_data,
        raises,
        exp_log,
        expected_cids,
        n_cohorts,
    ):
        """Test validate_cohort_data."""

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
            assert_allclose(
                validated["plant_cohorts_cell_id"].to_numpy(), expected_cids
            )

        log_check(caplog, expected_log=exp_log)

    def test_PlantCommunities__init__(
        self,
        caplog,
        fixture_flora,
        fixture_core_components,
        cohort_data,
        raises,
        exp_log,
        expected_cids,
        n_cohorts,
    ):
        """Test the data handling of the PlantCommunities __init__."""

        from pyrealm.demography.cohorts import cohort_id_generator

        from virtual_ecosystem.models.plants.communities import PlantCommunities

        # Clear any data loading log entries
        caplog.clear()

        with raises:
            plants_obj = PlantCommunities(
                cohort_data=cohort_data,
                flora=fixture_flora,
                grid=fixture_core_components.grid,
                cohort_id_generator=cohort_id_generator(),
            )

            # Check the expected contents of plants_obj
            assert len(plants_obj) == 4
            cids = {0, 1, 2, 3}
            assert set(plants_obj.keys()) == cids
            # Check the number of cohorts per community
            assert {k: len(v.cohorts) for k, v in plants_obj.items()} == n_cohorts

            # Plant communities adds a log message on success
            exp_log = (exp_log[0], (INFO, "Plant cohort data loaded"))

        log_check(caplog, expected_log=exp_log)
