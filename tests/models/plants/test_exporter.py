"""Tests the models.plants.exporter.CommunityDataExporter class."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pandas as pd
import pytest
from xarray import DataArray

from virtual_ecosystem.core.exceptions import ConfigurationError


@pytest.fixture
def fixture_exporter_components(flora):
    """Plant models components for testing exporter.

    Provides a set of PlantCommunities, their Canopy instances and a matching
    StemAllocation instance.
    """

    from pyrealm.demography.canopy import Canopy
    from pyrealm.demography.tmodel import StemAllocation

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.plants.communities import PlantCommunities

    data = Data(grid=Grid(cell_ny=2, cell_nx=2))
    cohort_data = (
        (
            "plant_cohorts_cell_id",
            DataArray(np.repeat(np.arange(4), np.arange(1, 5))),
        ),
        ("plant_cohorts_n", DataArray(np.array([5] * 10))),
        ("plant_cohorts_pft", DataArray(np.array(["shrub", "broadleaf"] * 5))),
        ("plant_cohorts_dbh", DataArray(np.array([0.1] * 10))),
    )

    for var, value in cohort_data:
        data[var] = value

    communities = PlantCommunities(data, flora=flora, grid=data.grid)
    canopies = {
        cell_id: Canopy(cmty, fit_ppa=True) for cell_id, cmty in communities.items()
    }

    stem_allocations = {
        cell_id: StemAllocation(
            stem_traits=cmty.stem_traits,
            stem_allometry=cmty.stem_allometry,
            whole_crown_gpp=np.full(cmty.n_cohorts, 25.0),
        )
        for cell_id, cmty in communities.items()
    }

    return communities, canopies, stem_allocations


@pytest.mark.parametrize(
    argnames="active, cohort_data_path, layer_data_path, outcome, msg",
    argvalues=(
        pytest.param(
            False, "any_old", "rubbish_passes", does_not_raise(), None, id="inactive"
        ),
        pytest.param(
            True,
            "cde_test/cohort_data.csv",
            "cde_test/layer_data.csv",
            does_not_raise(),
            None,
            id="both_good",
        ),
        pytest.param(
            True,
            "cde_test/existing_cohort_data.csv",
            "cde_test/layer_data.csv",
            pytest.raises(ConfigurationError),
            "The cohort_data_path exporter path must not be an existing file:",
            id="cohort_exists",
        ),
        pytest.param(
            True,
            "cde_test/cohort_data.csv",
            "cde_test/existing_layer_data.csv",
            pytest.raises(ConfigurationError),
            "The layer_data_path exporter path must not be an existing file:",
            id="layer_exists",
        ),
        pytest.param(
            True,
            "no_such_directory/cohort_data.csv",
            "no_such_directory/layer_data.csv",
            pytest.raises(ConfigurationError),
            "The cohort_data_path exporter path must be in an existing writeable",
            id="directory does not exist",
        ),
        pytest.param(
            True,
            "cde_test_read_only/cohort_data.csv",
            "cde_test_read_only/layer_data.csv",
            pytest.raises(ConfigurationError),
            "The cohort_data_path exporter path must be in an existing writeable",
            id="directory not writeable",
        ),
    ),
)
def test_CommunityDataExporter_check_paths(
    tmp_path, active, cohort_data_path, layer_data_path, outcome, msg
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create an output directory and touch some existing paths
    writeable_dir = tmp_path / "cde_test"
    readable_dir = tmp_path / "cde_test_read_only"
    cohort_path = writeable_dir / "existing_cohort_data.csv"
    layer_path = writeable_dir / "existing_layer_data.csv"

    writeable_dir.mkdir(exist_ok=False)
    readable_dir.mkdir(mode=0o555)  # readable and executable but not writeable
    cohort_path.touch(exist_ok=False)
    layer_path.touch(exist_ok=False)

    # Create the exporter
    with outcome as excep:
        exporter = CommunityDataExporter(
            cohort_data_path=tmp_path / cohort_data_path,
            layer_data_path=tmp_path / layer_data_path,
            cohort_attribute_subset=[],
            canopy_attribute_subset=[],
            active=active,
        )

        # Double check property set when the creation succeeds
        assert exporter.active == active

    if excep:
        assert str(excep.value).startswith(msg)


@pytest.mark.parametrize(
    argnames="active, cohort_attributes, layer_attributes, outcome, msg",
    argvalues=(
        pytest.param(
            False, "any_old", "rubbish_passes", does_not_raise(), None, id="inactive"
        ),
        pytest.param(
            True,
            set(),
            set(),
            does_not_raise(),
            None,
            id="both_good",
        ),
        pytest.param(
            True,
            set(["dbh", "crown_area"]),
            set(),
            does_not_raise(),
            None,
            id="valid_cohort_subset",
        ),
        pytest.param(
            True,
            set(["dbh", "crow_narea"]),
            set(),
            pytest.raises(ConfigurationError),
            "The cohort_attribute_subset exporter configuration contains "
            "unknown columns: crow_narea",
            id="valid_cohort_subset",
        ),
    ),
)
def test_CommunityDataExporter_check_attribute_subsets(
    tmp_path, active, cohort_attributes, layer_attributes, outcome, msg
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    with outcome as excep:
        exporter = CommunityDataExporter(
            cohort_data_path=tmp_path / "cohort_data.csv",
            layer_data_path=tmp_path / "layer_data.csv",
            cohort_attribute_subset=cohort_attributes,
            canopy_attribute_subset=layer_attributes,
            active=active,
        )

        # Double check property set when the creation succeeds
        assert exporter.active == active

    if excep:
        assert str(excep.value).startswith(msg)


def test_CommunityDataExporter_from_config():
    """Test the from_config factory method."""
    pass


def test_CommunityDataExporter_dump(tmp_path, fixture_exporter_components):
    """Test the from_config factory method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create an output directory and the output file names
    writeable_dir = tmp_path / "cde_test"
    cohort_path = writeable_dir / "cohort_data.csv"
    layer_path = writeable_dir / "layer_data.csv"
    writeable_dir.mkdir(exist_ok=False)

    # Create the exporter
    exporter = CommunityDataExporter(
        cohort_data_path=tmp_path / cohort_path,
        layer_data_path=tmp_path / layer_path,
        cohort_attribute_subset={},
        canopy_attribute_subset={},
        active=True,
    )

    # First dump in write mode with no allocations: expected behaviour in setup
    communities, canopies, stem_allocations = fixture_exporter_components
    exporter.dump(
        communities=communities,
        canopies=canopies,
        stem_allocations={},
        time=np.datetime64("2000-01-01"),
    )

    # Simple checks - file exists, can be read, has right number of rows.
    expected_n_rows = sum([cmty.n_cohorts for _, cmty in communities.items()])
    assert cohort_path.exists()
    content = pd.read_csv(cohort_path)
    assert len(content) == expected_n_rows

    # Second dump to check mode switching from write to append and provided stem
    # allocations: expected behaviour in update
    exporter.dump(
        communities=communities,
        canopies=canopies,
        stem_allocations=stem_allocations,
        time=np.datetime64("2001-01-01"),
    )

    # Repeat row count check - should now be doubled.
    content = pd.read_csv(cohort_path)
    assert len(content) == expected_n_rows * 2

    assert layer_path.exists()


def test_CommunityDataExporter_in_model(
    tmp_path,
    plants_data,
    flora,
    fixture_core_components,
    fixture_canopy_layer_data,
):
    """Test the exporter runs in the context of a PlantsModel."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    cohort_data_path = tmp_path / "cohort_data.csv"
    layer_data_path = tmp_path / "layer_data.csv"

    exporter = CommunityDataExporter(
        cohort_data_path=cohort_data_path,
        layer_data_path=layer_data_path,
        cohort_attribute_subset={},
        canopy_attribute_subset={},
        active=True,
    )

    plants_model = PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=flora,
        exporter=exporter,
    )

    # Simple checks - file exists, can be read, has right number of rows.
    expected_n_rows = sum(
        [cmty.n_cohorts for _, cmty in plants_model.communities.items()]
    )
    assert cohort_data_path.exists()
    content = pd.read_csv(cohort_data_path)
    assert len(content) == expected_n_rows

    plants_model.update(time_index=0)

    # Simple checks - file can be read, has right number of rows.
    content = pd.read_csv(cohort_data_path)
    assert len(content) == expected_n_rows * 2
