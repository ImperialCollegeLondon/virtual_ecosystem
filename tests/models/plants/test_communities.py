"""Tests the plant community model code."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import numpy as np
import pytest
from pandas import DataFrame

from tests.conftest import log_check


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
    caplog, flora, cohort_data, raises, exp_log, exp_n_cohorts
):
    """Test the data handling of the PlantCommunities __init__."""

    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.plants.communities import PlantCommunities

    grid = Grid(cell_ny=2, cell_nx=2)

    # Clear any data loading log entries
    caplog.clear()

    with raises:
        plants_obj = PlantCommunities(cohort_data=cohort_data, flora=flora, grid=grid)

        if isinstance(raises, does_not_raise):
            # Check the expected contents of plants_obj
            assert len(plants_obj) == 4
            cids = {0, 1, 2, 3}
            assert set(plants_obj.keys()) == cids
            for cid in cids:
                assert plants_obj[cid].cohorts.n_cohorts == exp_n_cohorts[cid]

    log_check(caplog, expected_log=exp_log)
