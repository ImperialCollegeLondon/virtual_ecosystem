"""Tests the plant community model code."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import numpy as np
import pytest
from xarray import DataArray

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames="vars,raises,exp_log",
    argvalues=[
        pytest.param(
            (("plant_cohorts_n", DataArray(np.array([5] * 4))),),
            pytest.raises(ValueError),
            ((CRITICAL, "Missing plant cohort variables"),),
            id="missing var",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 9), dims="toolong")),
                ("plant_cohorts_pft", DataArray(np.array(["shrub"] * 4))),
                ("plant_cohorts_cell_id", DataArray(np.arange(4))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Unequal plant cohort variable dimensions"),),
            id="unequal sizes",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4).reshape(2, 2))),
                ("plant_cohorts_pft", DataArray(np.array(["shrub"] * 4).reshape(2, 2))),
                ("plant_cohorts_cell_id", DataArray(np.arange(4).reshape(2, 2))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4).reshape(2, 2))),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort variable data is not one dimensional"),),
            id="not 1D",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4))),
                ("plant_cohorts_pft", DataArray(np.array(["shrub"] * 4))),
                ("plant_cohorts_cell_id", DataArray(DataArray(np.arange(2, 6)))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort cell ids not in grid cell ids"),),
            id="bad cell ids",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4))),
                ("plant_cohorts_pft", DataArray(np.array(["tree"] * 4))),
                ("plant_cohorts_cell_id", DataArray(DataArray(np.arange(4)))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort PFTs ids not in configured PFTs"),),
            id="bad pfts",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4))),
                ("plant_cohorts_pft", DataArray(np.array(["shrub"] * 4))),
                ("plant_cohorts_cell_id", DataArray(DataArray(np.arange(4)))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data loaded"),),
            id="all good",
        ),
    ],
)
def test_PlantCommunities__init__(caplog, flora, vars, raises, exp_log):
    """Test the data handling of the plants __init__."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.plants.community import PlantCommunities

    data = Data(grid=Grid(cell_ny=2, cell_nx=2))

    for var, value in vars:
        data[var] = value

    # Clear any data loading log entries
    caplog.clear()

    with raises:
        plants_obj = PlantCommunities(data, flora=flora)

        if isinstance(raises, does_not_raise):
            # Check the expected contents of plants_obj
            assert len(plants_obj.communities) == 4
            cids = set([0, 1, 2, 3])
            assert set(plants_obj.communities.keys()) == cids
            for cid in cids:
                assert len(plants_obj[cid]) == 1

    log_check(caplog, expected_log=exp_log)
