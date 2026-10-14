"""Tests for palm community cohort data validation and loading."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pyrealm.demography.cohorts import cohort_id_generator
from pyrealm.demography.flora import load_flora_from_csv

from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.models.palms.communities import (
    PalmCommunities,
    validate_cohort_data,
)
from virtual_ecosystem.models.palms.functional_types import PalmFloraValidator


@pytest.fixture
def palm_flora():
    """Load the canonical palm flora used by the model tests."""
    pft_path = Path(__file__).parents[2] / "data" / "palm_pfts.csv"
    return load_flora_from_csv(
        path=pft_path,
        strict=True,
        validator=PalmFloraValidator,
    )


@pytest.fixture
def palm_cohort_data():
    """Create one palm cohort at the centre of each cell in the fixture grid."""
    return pd.DataFrame(
        {
            "palm_cohorts_x": [0, 90, 0, 90],
            "palm_cohorts_y": [90, 90, 0, 0],
            "palm_cohorts_n": [20, 20, 20, 20],
            "palm_cohorts_pft": ["palm"] * 4,
            "palm_cohorts_dbh": [0.35] * 4,
            "palm_cohorts_stem_height": [6.5] * 4,
        }
    )


def test_validate_cohort_data_maps_coordinates_to_cell_ids(
    palm_cohort_data,
    palm_flora,
    fixture_core_components,
):
    """Coordinates are converted to the same internal cell IDs used by communities."""
    validated = validate_cohort_data(
        cohort_data=palm_cohort_data,
        flora=palm_flora,
        grid=fixture_core_components.grid,
    )

    np.testing.assert_array_equal(validated["palm_cohorts_cell_id"], [0, 1, 2, 3])


def test_palm_communities_load_xy_cohorts(
    palm_cohort_data,
    palm_flora,
    fixture_core_components,
):
    """Palm communities are grouped by the cell IDs derived from XY coordinates."""
    communities = PalmCommunities(
        cohort_data=palm_cohort_data,
        flora=palm_flora,
        grid=fixture_core_components.grid,
        cohort_id_generator=cohort_id_generator(),
    )

    assert set(communities) == {0, 1, 2, 3}
    assert [len(community.cohorts) for community in communities.values()] == [1] * 4
    assert [
        community.cohorts["stem_height_value"][0] for community in communities.values()
    ] == [6.5] * 4


@pytest.mark.parametrize(
    ("x_coordinate", "y_coordinate"),
    [(-100, 90), (45, 90)],
    ids=["outside-grid", "on-cell-boundary"],
)
def test_validate_cohort_data_rejects_invalid_coordinates(
    palm_cohort_data,
    palm_flora,
    fixture_core_components,
    x_coordinate,
    y_coordinate,
):
    """Coordinates outside the grid or on a boundary are rejected."""
    palm_cohort_data.loc[0, "palm_cohorts_x"] = x_coordinate
    palm_cohort_data.loc[0, "palm_cohorts_y"] = y_coordinate

    with pytest.raises(InitialisationError):
        validate_cohort_data(
            cohort_data=palm_cohort_data,
            flora=palm_flora,
            grid=fixture_core_components.grid,
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("palm_cohorts_pft", "unknown"),
        ("palm_cohorts_n", -1),
        ("palm_cohorts_n", 2.5),
        ("palm_cohorts_dbh", 0),
        ("palm_cohorts_stem_height", 0),
    ],
    ids=[
        "unknown-pft",
        "negative-count",
        "non-integer-count",
        "zero-dbh",
        "zero-height",
    ],
)
def test_validate_cohort_data_rejects_invalid_cohort_values(
    palm_cohort_data,
    palm_flora,
    fixture_core_components,
    column,
    value,
):
    """Invalid PFTs, counts, DBH, and stem heights are rejected."""
    palm_cohort_data[column] = value

    with pytest.raises(InitialisationError):
        validate_cohort_data(
            cohort_data=palm_cohort_data,
            flora=palm_flora,
            grid=fixture_core_components.grid,
        )
