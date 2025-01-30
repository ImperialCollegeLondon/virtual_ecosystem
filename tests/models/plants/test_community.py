"""Tests the plant community model code."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import numpy as np
import pytest
from xarray import DataArray

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames="vars,raises,exp_log, exp_n_cohorts",
    argvalues=[
        pytest.param(
            (("plant_cohorts_n", DataArray(np.array([5] * 4))),),
            pytest.raises(ValueError),
            (
                (
                    CRITICAL,
                    "Cannot initialise plant communities. Missing variables: "
                    "plant_cohorts_pft, plant_cohorts_cell_id, plant_cohorts_dbh",
                ),
            ),
            None,
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
            (
                (
                    CRITICAL,
                    "Cannot initialise plant communities. Variables of "
                    "unequal length: 4, 9",
                ),
            ),
            None,
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
            (
                (
                    CRITICAL,
                    "Cannot initialise plant communities. Variables not one "
                    "dimensional: plant_cohorts_n, plant_cohorts_pft, "
                    "plant_cohorts_cell_id, plant_cohorts_dbh",
                ),
            ),
            None,
            id="not 1D",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4))),
                ("plant_cohorts_pft", DataArray(np.array(["shrub"] * 4))),
                ("plant_cohorts_cell_id", DataArray(np.arange(2, 6))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort cell ids not in grid cell ids"),),
            None,
            id="bad cell ids",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4))),
                ("plant_cohorts_pft", DataArray(np.array(["tree"] * 4))),
                ("plant_cohorts_cell_id", DataArray(np.arange(4))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            pytest.raises(ValueError),
            ((CRITICAL, "Plant cohort PFTs ids not in configured PFTs"),),
            None,
            id="bad pfts",
        ),
        pytest.param(
            (
                ("plant_cohorts_n", DataArray(np.array([5] * 4))),
                ("plant_cohorts_pft", DataArray(np.array(["shrub"] * 4))),
                ("plant_cohorts_cell_id", DataArray(np.arange(4))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 4))),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data loaded"),),
            (1, 1, 1, 1),
            id="all good",
        ),
        pytest.param(
            (
                (
                    "plant_cohorts_cell_id",
                    DataArray(np.repeat(np.arange(4), np.arange(1, 5))),
                ),
                ("plant_cohorts_n", DataArray(np.array([5] * 10))),
                ("plant_cohorts_pft", DataArray(np.array(["shrub", "broadleaf"] * 5))),
                ("plant_cohorts_dbh", DataArray(np.array([0.1] * 10))),
            ),
            does_not_raise(),
            ((INFO, "Plant cohort data loaded"),),
            (1, 2, 3, 4),
            id="all good more complex",
        ),
    ],
)
def test_PlantCommunities__init__(caplog, flora, vars, raises, exp_log, exp_n_cohorts):
    """Test the data handling of the plants __init__."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.plants.community import PlantCommunities

    data = Data(grid=Grid(cell_ny=2, cell_nx=2))

    for var, value in vars:
        data[var] = value

    # Clear any data loading log entries
    caplog.clear()

    with raises:
        plants_obj = PlantCommunities(data, flora=flora, grid=data.grid)

        if isinstance(raises, does_not_raise):
            # Check the expected contents of plants_obj
            assert len(plants_obj) == 4
            cids = {0, 1, 2, 3}
            assert set(plants_obj.keys()) == cids
            for cid in cids:
                assert plants_obj[cid].cohorts.n_cohorts == exp_n_cohorts[cid]

    log_check(caplog, expected_log=exp_log)
