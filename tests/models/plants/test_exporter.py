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
    argnames=("required"),
    argvalues=(
        pytest.param(
            {"cohorts", "community_canopy", "stem_canopy"},
            id="all_required",
        ),
        pytest.param(
            {"community_canopy", "stem_canopy"},
            id="two_required",
        ),
        pytest.param(
            {"cohorts"},
            id="one_required",
        ),
        pytest.param(
            set(),
            id="none_required",
        ),
    ),
)
def test_CommunityDataExporter_check_and_set_paths(
    tmp_path,
    required,
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(output_directory=tmp_path, required_data=required)

    # Check the populated attributes
    for opt, (fname, attr) in exporter._outputs.items():
        attr_value = getattr(exporter, attr)
        if opt in required:
            assert attr_value == tmp_path / fname
        else:
            assert attr_value is None

    # Now create files that would be overwritten and check it raises - this does not
    # work for the case with no required files, because there are no files being
    # written, so exit early for that case

    if not required:
        return

    for opt, (fname, attr) in exporter._outputs.items():
        if opt in required:
            existing_file = tmp_path / fname
            existing_file.touch(exist_ok=False)

    with pytest.raises(ConfigurationError) as excep:
        exporter = CommunityDataExporter(
            output_directory=tmp_path, required_data=required
        )

    assert str(excep.value).startswith("An output file for ")


@pytest.mark.parametrize(
    argnames="cohort_attr, community_canopy_attr, stem_canopy_attr, outcome, msg",
    argvalues=(
        pytest.param(
            set(),
            set(),
            set(),
            does_not_raise(),
            None,
            id="all_unset",
        ),
        pytest.param(
            set(["dbh", "crown_area"]),
            set(["average_layer_fapar", "transmission_profile"]),
            set(["stem_leaf_area"]),
            does_not_raise(),
            None,
            id="all_valid",
        ),
        pytest.param(
            set(["dbh", "crow_narea"]),
            set(),
            set(),
            pytest.raises(ConfigurationError),
            "The cohort_attributes exporter configuration contains "
            "unknown attributes: crow_narea",
            id="invalid cohort attr",
        ),
        pytest.param(
            set(),
            set(["mean_layer_fapar"]),
            set(),
            pytest.raises(ConfigurationError),
            "The community_canopy_attributes exporter configuration contains "
            "unknown attributes: mean_layer_fapar",
            id="invalid community canopy attr",
        ),
        pytest.param(
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
    cohort_attr,
    community_canopy_attr,
    stem_canopy_attr,
    outcome,
    msg,
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    with outcome as excep:
        _ = CommunityDataExporter(
            output_directory=tmp_path,
            required_data={"cohorts", "community_canopy", "stem_canopy"},
            cohort_attributes=cohort_attr,
            community_canopy_attributes=community_canopy_attr,
            stem_canopy_attributes=stem_canopy_attr,
        )

    if excep:
        assert str(excep.value).startswith(msg)


@pytest.mark.parametrize(
    argnames="inputs,outcome,msg",
    argvalues=(
        pytest.param(
            dict(
                path="",
                required=["cohorts", "community_canopy", "stem_canopy"],
                cohort_attrs=[],
                ccan_attrs=[],
                scan_attrs=[],
            ),
            does_not_raise(),
            None,
            id="all_good",
        ),
        pytest.param(
            dict(
                path="bad/path/",
                required=["cohorts", "community_canopy", "stem_canopy"],
                cohort_attrs=[],
                ccan_attrs=[],
                scan_attrs=[],
            ),
            pytest.raises(ConfigurationError),
            "The plant community data output directory does not exist or",
            id="bad_path",
        ),
        pytest.param(
            dict(
                path="",
                required=["cohorts", "community_canopies", "stem_canopy"],
                cohort_attrs=[],
                ccan_attrs=[],
                scan_attrs=[],
            ),
            pytest.raises(ConfigurationError),
            "The required_data setting contains unknown data output options",
            id="bad required",
        ),
        pytest.param(
            dict(
                path="",
                required=["cohorts", "community_canopy", "stem_canopy"],
                cohort_attrs=["dbh", "crown_area"],
                ccan_attrs=["average_layer_fapar", "transmission_profile"],
                scan_attrs=["stem_leaf_area"],
            ),
            does_not_raise(),
            None,
            id="all_good_with_subset",
        ),
        pytest.param(
            dict(
                path="",
                required=["cohorts", "community_canopy", "stem_canopy"],
                cohort_attrs=["dbh", "crow_narea"],
                ccan_attrs=["average_layer_fapar", "transmission_profile"],
                scan_attrs=["stem_leaf_area"],
            ),
            pytest.raises(ConfigurationError),
            "The cohort_attributes exporter configuration contains unknown attributes",
            id="bad_subset",
        ),
    ),
)
def test_CommunityDataExporter_from_config(tmp_path, inputs, outcome, msg):
    """Test the from_config factory method."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    toml = f"""[core.data_output_options]
    out_path = "{tmp_path / inputs["path"]}"
    [plants]
    pft_definitions_path = "does/not/need/to/exist"
    [plants.community_data_export]
    required_data = {inputs["required"]}
    cohort_attributes = {inputs["cohort_attrs"]}
    community_canopy_attributes = {inputs["ccan_attrs"]}
    stem_canopy_attributes ={inputs["scan_attrs"]}
    """

    print(toml)

    config = Config(cfg_strings=toml)

    with outcome as excep:
        CommunityDataExporter.from_config(config=config)

    if excep:
        assert str(excep.value).startswith(msg)


def csv_row_check(path: Path | None, n_rows: int, attr: list[str] = []) -> None:
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
    argnames="required,attributes",
    argvalues=(
        pytest.param(set(), [], id="no_cohort"),
        pytest.param({"cohorts"}, set(), id="all_cohort"),
        pytest.param({"cohorts"}, {"dbh", "cell_id"}, id="some_cohort"),
    ),
)
def test_CommunityDataExporter_dump_cohort_data(
    tmp_path, fixture_exporter_components, required, attributes
):
    """Test CommunityDataExporter _dump_cohort_data method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        required_data=required,
        cohort_attributes=attributes,
    )

    # First dump in write mode with no allocations: expected behaviour in setup
    communities, canopies, stem_allocations = fixture_exporter_components
    exporter._dump_cohort_data(
        communities=communities,
        canopies=canopies,
        stem_allocations={},
        time=np.datetime64("2000-01-01"),
    )

    out_path = tmp_path / "plants_cohort_data.csv"

    # Check the output file does not exist if the output is not required
    if not required:
        assert not out_path.exists()
        return

    # Otherwise check it exists and has the requested attributes
    assert out_path.exists()
    cell_n_cohorts = np.array([cmty.n_cohorts for _, cmty in communities.items()])
    csv_row_check(path=out_path, n_rows=cell_n_cohorts.sum(), attr=attributes)


@pytest.mark.parametrize(
    argnames="required,attributes",
    argvalues=(
        pytest.param(set(), [], id="no_ccan"),
        pytest.param({"community_canopy"}, set(), id="all_ccan"),
        pytest.param(
            {"community_canopy"}, {"transmission_profile", "cell_id"}, id="some_ccan"
        ),
    ),
)
def test_CommunityDataExporter_dump_community_canopy_data(
    tmp_path, fixture_exporter_components, required, attributes
):
    """Test CommunityDataExporter _dump_community_canopy_data method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        required_data=required,
        community_canopy_attributes=attributes,
    )

    # First dump in write mode with no allocations: expected behaviour in setup
    _, canopies, _ = fixture_exporter_components
    exporter._dump_community_canopy_data(
        canopies=canopies,
        time=np.datetime64("2000-01-01"),
    )

    out_path = tmp_path / "plants_community_canopy_data.csv"

    # Check the output file does not exist if the output is not required
    if not required:
        assert not out_path.exists()
        return

    # Otherwise check it exists and has the requested attributes
    assert out_path.exists()
    cell_n_layers = np.array([len(cpy.heights) for cpy in canopies.values()])
    csv_row_check(path=out_path, n_rows=cell_n_layers.sum(), attr=attributes)


@pytest.mark.parametrize(
    argnames="required,attributes",
    argvalues=(
        pytest.param(set(), [], id="no_scan"),
        pytest.param({"stem_canopy"}, set(), id="all_scan"),
        pytest.param({"stem_canopy"}, {"fapar", "cell_id"}, id="some_scan"),
    ),
)
def test_CommunityDataExporter_dump_stem_canopy_data(
    tmp_path, fixture_exporter_components, required, attributes
):
    """Test CommunityDataExporter _dump_stem_canopy_data method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        required_data=required,
        stem_canopy_attributes=attributes,
    )

    # Run the dump
    communities, canopies, _ = fixture_exporter_components
    exporter._dump_stem_canopy_data(
        communities=communities,
        canopies=canopies,
        time=np.datetime64("2000-01-01"),
    )

    out_path = tmp_path / "plants_stem_canopy_data.csv"

    # Check the output file does not exist if the output is not required
    if not required:
        assert not out_path.exists()
        return

    # Otherwise check it exists and has the requested attributes
    assert out_path.exists()
    cell_n_cohorts = np.array([cmty.n_cohorts for _, cmty in communities.items()])
    cell_n_layers = np.array([len(cpy.heights) for cpy in canopies.values()])
    cell_n_stem_layers = (cell_n_cohorts * cell_n_layers).sum()
    csv_row_check(path=out_path, n_rows=cell_n_stem_layers, attr=attributes)


@pytest.mark.parametrize(
    argnames=("required"),
    argvalues=(
        pytest.param(
            {"cohorts", "community_canopy", "stem_canopy"},
            id="all_required",
        ),
        pytest.param(
            {"community_canopy", "stem_canopy"},
            id="two_required",
        ),
        pytest.param(
            {"cohorts"},
            id="one_required",
        ),
        pytest.param(
            set(),
            id="none_required",
        ),
    ),
)
class TestExporterDump:
    """Common testing of the dump method by various routes.

    This class uses combinations of settings for each of the three files and then uses
    those to check the exporter created directly and running outside of a model,
    through an exporter created from config, and then through a model.
    """

    @staticmethod
    def calculate_expected_n(communities, canopies):
        """Calculate expected numbers of rows in the three data files."""
        cht_by_cell = np.array([c.n_cohorts for c in communities.values()])
        lyrs_by_cell = np.array([len(cpy.heights) for cpy in canopies.values()])

        return dict(
            cohorts=cht_by_cell.sum(),
            community_canopy=lyrs_by_cell.sum(),
            stem_canopy=(cht_by_cell * lyrs_by_cell).sum(),
        )

    def check_output(self, path, exporter, required, expected_n):
        """Shared validation function."""
        # Loop over the possible values in required_data and check the file paths are
        # set and then that the file exists and has the expected number of rows. If the
        # file is not required, just check the attribute is set.
        for opt, (fname, attr) in exporter._outputs.items():
            attr_value = getattr(exporter, attr)

            if opt in required:
                data_path = path / fname
                assert attr_value == data_path
                csv_row_check(path=data_path, n_rows=expected_n[opt])

            else:
                assert attr_value is None

    def test_CommunityDataExporter_dump(
        self,
        tmp_path,
        fixture_exporter_components,
        required,
    ):
        """Test the from_config factory method."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

        # Create the exporter
        exporter = CommunityDataExporter(
            output_directory=tmp_path,
            required_data=required,
        )

        if required:
            assert exporter._active

        assert exporter._output_mode == "w"
        assert exporter._write_header

        # First dump in write mode with no allocations: expected behaviour in setup
        communities, canopies, stem_allocations = fixture_exporter_components
        exporter.dump(
            communities=communities,
            canopies=canopies,
            stem_allocations={},
            time=np.datetime64("2000-01-01"),
        )

        if required:
            assert exporter._output_mode == "a"
            assert not exporter._write_header

        expected_n = self.calculate_expected_n(communities, canopies)
        self.check_output(tmp_path, exporter, required, expected_n)

        # Second dump to check mode switching from write to append and provided stem
        # allocations: expected behaviour in update
        exporter.dump(
            communities=communities,
            canopies=canopies,
            stem_allocations=stem_allocations,
            time=np.datetime64("2001-01-01"),
        )

        # Check the files are ok and have doubled the number of rows
        self.check_output(
            tmp_path, exporter, required, {k: v * 2 for k, v in expected_n.items()}
        )

    def test_CommunityDataExporter_in_model(
        self,
        tmp_path,
        plants_data,
        flora,
        fixture_core_components,
        fixture_canopy_layer_data,
        required,
    ):
        """Test the exporter runs as expected from within a PlantsModel."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
        from virtual_ecosystem.models.plants.plants_model import PlantsModel

        exporter = CommunityDataExporter(
            output_directory=tmp_path,
            required_data=required,
        )

        if required:
            assert exporter._active

        assert exporter._output_mode == "w"
        assert exporter._write_header

        # Create plant model to run PlantsModel._setup and hence the dump method
        model = PlantsModel(
            data=plants_data,
            core_components=fixture_core_components,
            flora=flora,
            exporter=exporter,
        )

        if required:
            assert exporter._output_mode == "a"
            assert not exporter._write_header

        # Simple checks - files exists, can be read, have the right number of rows.
        expected_n = self.calculate_expected_n(model.communities, model.canopies)
        self.check_output(tmp_path, exporter, required, expected_n)

        # Update the model to trigger a second dump
        model.update(time_index=0)

        # Check the files are ok and have doubled the number of rows
        self.check_output(
            tmp_path, exporter, required, {k: v * 2 for k, v in expected_n.items()}
        )

    def test_CommunityDataExporter_through_config(
        self,
        tmp_path,
        fixture_exporter_components,
        required,
    ):
        """Test the from_config factory method."""

        from virtual_ecosystem.core.config import Config
        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

        toml = f"""
        [core.data_output_options]
        out_path = "{tmp_path!s}"
        [plants]
        pft_definitions_path = "does/not/need/to/exist"
        [plants.community_data_export]
        required_data = {list(required)}
        """

        config = Config(cfg_strings=toml)
        exporter = CommunityDataExporter.from_config(config=config)

        if required:
            assert exporter._active

        assert exporter._output_mode == "w"
        assert exporter._write_header

        # First dump in write mode with no allocations: expected behaviour in setup
        communities, canopies, stem_allocations = fixture_exporter_components
        exporter.dump(
            communities=communities,
            canopies=canopies,
            stem_allocations={},
            time=np.datetime64("2000-01-01"),
        )

        if required:
            assert exporter._output_mode == "a"
            assert not exporter._write_header
