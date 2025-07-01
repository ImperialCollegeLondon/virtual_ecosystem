"""Tests the models.plants.exporter.CommunityDataExporter class."""

from contextlib import nullcontext as does_not_raise
from pathlib import Path

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

    data = Data(grid=Grid(cell_ny=2, cell_nx=2, cell_area=625))
    cohort_data = (
        (
            "plant_cohorts_cell_id",
            DataArray(np.repeat(np.arange(4), np.arange(1, 5))),
        ),
        ("plant_cohorts_n", DataArray(np.array([5] * 10))),
        ("plant_cohorts_pft", DataArray(np.array(["shrub", "broadleaf"] * 5))),
        ("plant_cohorts_dbh", DataArray(np.array([1] * 10))),
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
    argnames=(
        "active, cohort_data_path, community_canopy_data_path, "
        "stem_canopy_data_path, outcome, msg"
    ),
    argvalues=(
        pytest.param(
            False, "any_old", "rubbish", "passes", does_not_raise(), None, id="inactive"
        ),
        pytest.param(
            True,
            "cde_test/cohort_data.csv",
            "cde_test/community_canopy_data.csv",
            "cde_test/stem_canopy_data.csv",
            does_not_raise(),
            None,
            id="all_good",
        ),
        pytest.param(
            True,
            "cde_test/existing_file.csv",
            "cde_test/community_canopy_data.csv",
            "cde_test/stem_canopy_data.csv",
            pytest.raises(ConfigurationError),
            "The cohort_data_path exporter path must not be an existing file",
            id="cohort_exists",
        ),
        pytest.param(
            True,
            "cde_test/cohort_data.csv",
            "cde_test/existing_file.csv",
            "cde_test/stem_canopy_data.csv",
            pytest.raises(ConfigurationError),
            "The community_canopy_data_path exporter path must not be an existing file",
            id="community_canopy_exists",
        ),
        pytest.param(
            True,
            "cde_test/cohort_data.csv",
            "cde_test/community_canopy_data.csv",
            "cde_test/existing_file.csv",
            pytest.raises(ConfigurationError),
            "The stem_canopy_data_path exporter path must not be an existing file",
            id="stem_canopy_exists",
        ),
        pytest.param(
            True,
            "no_such_directory/cohort_data.csv",
            "no_such_directory/community_canopy_data.csv",
            "no_such_directory/stem_canopy_data.csv",
            pytest.raises(ConfigurationError),
            "The cohort_data_path exporter path must be in an existing writeable",
            id="directory does not exist",
        ),
        pytest.param(
            True,
            "cde_test_read_only/cohort_data.csv",
            "cde_test_read_only/community_canopy_data.csv",
            "cde_test_read_only/stem_canopy_data.csv",
            pytest.raises(ConfigurationError),
            "The cohort_data_path exporter path must be in an existing writeable",
            id="directory not writeable",
        ),
    ),
)
def test_CommunityDataExporter_check_paths(
    tmp_path,
    active,
    cohort_data_path,
    community_canopy_data_path,
    stem_canopy_data_path,
    outcome,
    msg,
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create writeable and read only output directories
    w_dir = tmp_path / "cde_test"
    w_dir.mkdir(exist_ok=False)
    r_dir = tmp_path / "cde_test_read_only"
    r_dir.mkdir(mode=0o555, exist_ok=False)  # readable and executable but not writeable
    r_dir.chmod(mode=0o555)  # Attempt to make Windows listen...

    # Create a file in the writeable directory
    existing_file = w_dir / "existing_file.csv"
    existing_file.touch(exist_ok=False)

    # Create the exporter
    with outcome as excep:
        exporter = CommunityDataExporter(
            cohort_data_path=tmp_path / cohort_data_path,
            community_canopy_data_path=tmp_path / community_canopy_data_path,
            stem_canopy_data_path=tmp_path / stem_canopy_data_path,
            cohort_attributes={},
            community_canopy_attributes={},
            stem_canopy_attributes={},
            active=active,
        )

        # Double check property set when the creation succeeds
        assert exporter.active == active

    if excep:
        assert str(excep.value).startswith(msg)


@pytest.mark.parametrize(
    argnames=(
        "active, cohort_attributes, community_canopy_attributes, "
        "stem_canopy_attributes, outcome, msg"
    ),
    argvalues=(
        pytest.param(
            False, "any_old", "rubbish", "passes", does_not_raise(), None, id="inactive"
        ),
        pytest.param(
            True,
            set(),
            set(),
            set(),
            does_not_raise(),
            None,
            id="all_unset",
        ),
        pytest.param(
            True,
            set(["dbh", "crown_area"]),
            set(["average_layer_fapar", "transmission_profile"]),
            set(["stem_leaf_area"]),
            does_not_raise(),
            None,
            id="all_valid",
        ),
        pytest.param(
            True,
            set(["dbh", "crow_narea"]),
            set(),
            set(),
            pytest.raises(ConfigurationError),
            "The cohort_attributes exporter configuration contains "
            "unknown attributes: crow_narea",
            id="invalid cohort attr",
        ),
        pytest.param(
            True,
            set(),
            set(["mean_layer_fapar"]),
            set(),
            pytest.raises(ConfigurationError),
            "The community_canopy_attributes exporter configuration contains "
            "unknown attributes: mean_layer_fapar",
            id="invalid community canopy attr",
        ),
        pytest.param(
            True,
            set(),
            set(),
            set(["steam_leaf_are"]),
            pytest.raises(ConfigurationError),
            "The stem_canopy_attributes exporter configuration contains "
            "unknown attributes: steam_leaf_are",
            id="invalid stem community attr",
        ),
    ),
)
def test_CommunityDataExporter_check_attribute_subsets(
    tmp_path,
    active,
    cohort_attributes,
    community_canopy_attributes,
    stem_canopy_attributes,
    outcome,
    msg,
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    with outcome as excep:
        exporter = CommunityDataExporter(
            cohort_data_path=tmp_path / "cohort_data.csv",
            community_canopy_data_path=tmp_path / "community_canopy_data.csv",
            stem_canopy_data_path=tmp_path / "stem_canopy_data.csv",
            cohort_attributes=cohort_attributes,
            community_canopy_attributes=community_canopy_attributes,
            stem_canopy_attributes=stem_canopy_attributes,
            active=active,
        )

        # Double check property set when the creation succeeds
        assert exporter.active == active

    if excep:
        assert str(excep.value).startswith(msg)


def test_CommunityDataExporter_from_config():
    """Test the from_config factory method."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    toml = """
    [plants]
    pft_definitions_path = "does/not/need/to/exist"
    [plants.community_data_export]
    active = true
    cohort_data_path = ""
    community_canopy_data_path = ""
    stem_canopy_data_path = ""
    cohort_attributes = []
    community_canopy_attributes = []
    stem_canopy_attributes = []
    """

    config = Config(cfg_strings=toml)

    CommunityDataExporter.from_config(config=config)


def csv_row_check(path: Path | None, n_rows: int, attr: list[str]) -> None:
    """Shared test function for exported CSV.

    Assert a file exists, can be loaded, has the right number of rows and - if the
    attribute subset is specified - that the field subset has been saved.
    """

    if path is None:
        return

    assert path.exists()
    content = pd.read_csv(path)

    assert len(content) == n_rows

    if attr:
        assert set(content.columns) == set(attr)


@pytest.mark.parametrize(
    argnames="cohort_data_path,cohort_attributes",
    argvalues=(
        pytest.param("", [], id="no_cohort"),
        pytest.param("cohort_data.csv", [], id="all_cohort"),
        pytest.param("cohort_data.csv", ["dbh", "cell_id"], id="some_cohort"),
    ),
)
@pytest.mark.parametrize(
    argnames="ccan_data_path,ccan_attributes",
    argvalues=(
        pytest.param("", [], id="no_ccan"),
        pytest.param("ccan_data.csv", [], id="all_ccan"),
        pytest.param(
            "ccan_data.csv", ["transmission_profile", "cell_id"], id="some_ccan"
        ),
    ),
)
@pytest.mark.parametrize(
    argnames="scan_data_path,scan_attributes",
    argvalues=(
        pytest.param("", [], id="no_scan"),
        pytest.param("scan_data.csv", [], id="all_scan"),
        pytest.param("scan_data.csv", ["fapar", "cell_id"], id="some_scan"),
    ),
)
class TestExporterInUse:
    """Common testing of various setup options.

    This class uses all combinations of settings for each of the three files - which is
    arguably overkill, could use fewer representative configurations - and then uses
    those to check the exporter running outside of a model, inside of a model and then
    the creation of the exporter from configurations.
    """

    def test_CommunityDataExporter_dump(
        self,
        tmp_path,
        fixture_exporter_components,
        cohort_data_path,
        cohort_attributes,
        ccan_data_path,
        ccan_attributes,
        scan_data_path,
        scan_attributes,
    ):
        """Test the from_config factory method."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

        # Convert path strings to Path or None
        cht_path = (tmp_path / cohort_data_path) if cohort_data_path else None
        ccan_path = (tmp_path / ccan_data_path) if ccan_data_path else None
        scan_path = (tmp_path / scan_data_path) if scan_data_path else None

        # Create the exporter
        exporter = CommunityDataExporter(
            cohort_data_path=cht_path,
            community_canopy_data_path=ccan_path,
            stem_canopy_data_path=scan_path,
            cohort_attributes=set(cohort_attributes),
            community_canopy_attributes=set(ccan_attributes),
            stem_canopy_attributes=set(scan_attributes),
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

        # Simple checks - files exists, can be read, have the right number of rows.
        cell_n_cohorts = np.array([cmty.n_cohorts for _, cmty in communities.items()])
        cell_n_layers = np.array([len(cpy.heights) for cpy in canopies.values()])
        cell_n_stem_layers = (cell_n_cohorts * cell_n_layers).sum()

        csv_row_check(
            path=cht_path, n_rows=cell_n_cohorts.sum(), attr=cohort_attributes
        )
        csv_row_check(path=ccan_path, n_rows=cell_n_layers.sum(), attr=ccan_attributes)
        csv_row_check(path=scan_path, n_rows=cell_n_stem_layers, attr=scan_attributes)

        # Second dump to check mode switching from write to append and provided stem
        # allocations: expected behaviour in update
        exporter.dump(
            communities=communities,
            canopies=canopies,
            stem_allocations=stem_allocations,
            time=np.datetime64("2001-01-01"),
        )

        # Repeat row count check - should now be doubled.
        # Check the files are ok and have doubled the number of rows
        csv_row_check(
            path=cht_path, n_rows=cell_n_cohorts.sum() * 2, attr=cohort_attributes
        )
        csv_row_check(
            path=ccan_path, n_rows=cell_n_layers.sum() * 2, attr=ccan_attributes
        )
        csv_row_check(
            path=scan_path, n_rows=cell_n_stem_layers * 2, attr=scan_attributes
        )

    def test_CommunityDataExporter_in_model(
        self,
        tmp_path,
        plants_data,
        flora,
        fixture_core_components,
        fixture_canopy_layer_data,
        cohort_data_path,
        cohort_attributes,
        ccan_data_path,
        ccan_attributes,
        scan_data_path,
        scan_attributes,
    ):
        """Test the exporter runs as expected from within a PlantsModel."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
        from virtual_ecosystem.models.plants.plants_model import PlantsModel

        # Convert path strings to Path or None
        cht_path = (tmp_path / cohort_data_path) if cohort_data_path else None
        ccan_path = (tmp_path / ccan_data_path) if ccan_data_path else None
        scan_path = (tmp_path / scan_data_path) if scan_data_path else None

        exporter = CommunityDataExporter(
            cohort_data_path=cht_path,
            community_canopy_data_path=ccan_path,
            stem_canopy_data_path=scan_path,
            cohort_attributes=set(cohort_attributes),
            community_canopy_attributes=set(ccan_attributes),
            stem_canopy_attributes=set(scan_attributes),
            active=True,
        )

        model = PlantsModel(
            data=plants_data,
            core_components=fixture_core_components,
            flora=flora,
            exporter=exporter,
        )

        # Simple checks - files exists, can be read, have the right number of rows.
        cell_n_cohorts = np.array(
            [cmty.n_cohorts for _, cmty in model.communities.items()]
        )
        cell_n_layers = np.array([len(cpy.heights) for cpy in model.canopies.values()])
        cell_n_stem_layers = (cell_n_cohorts * cell_n_layers).sum()

        csv_row_check(
            path=cht_path, n_rows=cell_n_cohorts.sum(), attr=cohort_attributes
        )
        csv_row_check(path=ccan_path, n_rows=cell_n_layers.sum(), attr=ccan_attributes)
        csv_row_check(path=scan_path, n_rows=cell_n_stem_layers, attr=scan_attributes)

        # Update the model to trigger a second dump
        model.update(time_index=0)

        # Check the files are ok and have doubled the number of rows
        csv_row_check(
            path=cht_path, n_rows=cell_n_cohorts.sum() * 2, attr=cohort_attributes
        )
        csv_row_check(
            path=ccan_path, n_rows=cell_n_layers.sum() * 2, attr=ccan_attributes
        )
        csv_row_check(
            path=scan_path, n_rows=cell_n_stem_layers * 2, attr=scan_attributes
        )

    def test_CommunityDataExporter_from_config(
        self,
        cohort_data_path,
        cohort_attributes,
        ccan_data_path,
        ccan_attributes,
        scan_data_path,
        scan_attributes,
    ):
        """Test the from_config factory method."""

        from virtual_ecosystem.core.config import Config
        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

        toml = f"""
        [plants]
        pft_definitions_path = "does/not/need/to/exist"
        [plants.community_data_export]
        active = true
        cohort_data_path = "{cohort_data_path}"
        community_canopy_data_path = "{ccan_data_path}"
        stem_canopy_data_path = "{scan_data_path}"
        cohort_attributes = {cohort_attributes!r}
        community_canopy_attributes = {ccan_attributes!r}
        stem_canopy_attributes = {scan_attributes!r}
        """

        config = Config(cfg_strings=toml)

        CommunityDataExporter.from_config(config=config)
