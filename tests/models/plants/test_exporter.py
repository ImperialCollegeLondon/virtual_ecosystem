"""Tests the models.plants.exporter.CommunityDataExporter class."""

from contextlib import nullcontext as does_not_raise
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from virtual_ecosystem.core.exceptions import ConfigurationError


@pytest.fixture
def fixture_exporter_components(
    fixture_flora, plants_cohort_data, fixture_core_components
):
    """Plant models components for testing exporter.

    Provides a set of PlantCommunities, their Canopy instances and a matching
    StemAllocation instance.
    """

    from pyrealm.demography.canopy import Canopy
    from pyrealm.demography.cohorts import cohort_id_generator
    from pyrealm.demography.tmodel import GrowthIncrements, StemAllocation

    from virtual_ecosystem.models.plants.biomasses import (
        Biomasses,
    )
    from virtual_ecosystem.models.plants.communities import PlantCommunities

    communities = PlantCommunities(
        cohort_id_generator=cohort_id_generator(mode="str"),
        cohort_data=plants_cohort_data,
        flora=fixture_flora,
        grid=fixture_core_components.grid,
    )

    # HACK pyrealm3: Adding additional allometry values onto stem allometry. Could be
    #      formalised in subclass
    for cmty in communities.values():
        cmty.stem_allometry.fruit_mass = np.full_like(cmty.stem_allometry.dbh, 10)
        cmty.stem_allometry.seed_mass = np.full_like(cmty.stem_allometry.dbh, 10)

    canopies = {
        cell_id: Canopy(
            cohorts=cmty.cohorts,
            allometry=cmty.stem_allometry,
            canopy_area=fixture_core_components.grid.cell_area,
            fit_ppa=True,
        )
        for cell_id, cmty in communities.items()
    }

    stem_allocations = {
        cell_id: StemAllocation(
            cohorts=cmty.cohorts,
            allometry=cmty.stem_allometry,
            whole_crown_gpp=np.full(len(cmty.cohorts), 25.0),
        )
        for cell_id, cmty in communities.items()
    }

    growth_increments = {
        cell_id: GrowthIncrements(
            cohorts=cmty.cohorts,
            allometry=cmty.stem_allometry,
            stem_allocation=stem_allocations[cell_id],
            biomass_production=np.full(len(cmty.cohorts), 10.0),
        )
        for cell_id, cmty in communities.items()
    }

    biomasses = {
        cell_id: Biomasses.from_cohorts(
            cohorts=cmty.cohorts,
            allometry=cmty.stem_allometry,
        )
        for cell_id, cmty in communities.items()
    }

    return communities, canopies, stem_allocations, growth_increments, biomasses


@pytest.mark.parametrize(
    argnames=("cohort,community_canopy,stem_canopy"),
    argvalues=(
        pytest.param("ALL", "ALL", "ALL", id="all_required"),
        pytest.param(set(), "ALL", "ALL", id="two_required"),
        pytest.param("ALL", set(), set(), id="one_required"),
        pytest.param(set(), set(), set(), id="none_required"),
    ),
)
def test_CommunityDataExporter_check_and_set_paths(
    request, tmp_path, cohort, community_canopy, stem_canopy
):
    """Test the path validation of CommunityDataExporter."""
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        cohort_attributes=cohort,
        community_canopy_attributes=community_canopy,
        stem_canopy_attributes=stem_canopy,
    )

    # Check the populated attributes
    for type, path in exporter._output_files.items():
        attr_value = getattr(exporter, f"_{type}_path")
        assert attr_value == tmp_path / path

    # Now create files that would be overwritten and check it raises - this does not
    # work for the case with no required files, because there are no files being
    # written, so exit early for that case

    if request.node.callspec.id == "none_required":
        return

    for type, attr in exporter._output_files.items():
        if eval(type) == "ALL":
            existing_file = tmp_path / attr
            existing_file.touch(exist_ok=False)

    with pytest.raises(ConfigurationError) as excep:
        exporter = CommunityDataExporter(
            output_directory=tmp_path,
            cohort_attributes=cohort,
            community_canopy_attributes=community_canopy,
            stem_canopy_attributes=stem_canopy,
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
                cohort_attrs="ALL",
                ccan_attrs="ALL",
                scan_attrs="ALL",
            ),
            does_not_raise(),
            None,
            id="all_good",
        ),
        pytest.param(
            dict(
                path="",
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
                cohort_attrs=["dbh", "crow_narea"],
                ccan_attrs=["average_layer_fapar", "transmission_profile"],
                scan_attrs=["stem_leaf_area"],
            ),
            pytest.raises(ConfigurationError),
            "The cohort_attributes exporter configuration contains unknown attributes",
            id="bad_subset",
        ),
        pytest.param(
            dict(
                path="",
                cohort_attrs="ALLY",
                ccan_attrs="ALLLL",
                scan_attrs="EVERY_LAST_ONE",
            ),
            pytest.raises(ValidationError),
            "6 validation errors for PlantsExportConfig",
            id="bad_kw_to_config",
        ),
    ),
)
def test_CommunityDataExporter_from_config(tmp_path, inputs, outcome, msg):
    """Test the from_config factory method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
    from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

    # Note that the single quotes around the out_path are _required_ here: TOML uses
    # single quotes to indicate raw strings and hence protect the backslashes in Windows
    # path names from being interpreted as escape sequences.

    cfg_data = dict(
        cohort_attributes=inputs["cohort_attrs"],
        community_canopy_attributes=inputs["ccan_attrs"],
        stem_canopy_attributes=inputs["scan_attrs"],
    )

    with outcome as excep:
        config = PlantsExportConfig().model_validate(cfg_data)
        CommunityDataExporter.from_config(output_directory=tmp_path, config=config)

    if excep:
        assert str(excep.value).startswith(msg)


def csv_check(
    path: Path, n_rows: int, attr: str | set[str], expected: set[str] | None = None
) -> None:
    """Shared test function for exported CSV.

    Assert the file does not exist if no file requested, otherwise assert that a file
    exists, can be loaded, and has the right number of rows.

    Optionally can also check the columns are as expected, which checks the mechanism
    but also tests the definition of available attributes in __init__ against the
    reality of exporting.
    """

    if not attr:
        assert not path.exists()
        return

    assert path.exists()
    content = pd.read_csv(path)

    assert len(content) == n_rows

    if expected is not None:
        assert set(content.columns) == expected


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
@pytest.mark.parametrize(
    argnames="attributes",
    argvalues=(
        pytest.param(set(), id="no_cohort"),
        pytest.param("ALL", id="all_cohort"),
        pytest.param({"dbh", "cell_id"}, id="some_cohort"),
    ),
)
def test_CommunityDataExporter_dump_cohort_data(
    tmp_path,
    fixture_exporter_components,
    tricky_plant_cohorts,  # Set that the straightforward cohort data gets used
    attributes,
):
    """Test CommunityDataExporter _dump_cohort_data method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        cohort_attributes=attributes,
    )

    # First dump in write mode with no allocations: expected behaviour in setup
    communities, _, stem_allocations, growth_increments, biomasses = (
        fixture_exporter_components
    )
    exporter._dump_cohort_data(
        communities=communities,
        biomasses=biomasses,
        stem_allocations=stem_allocations,
        growth_increments=growth_increments,
        time=np.datetime64("2000-01-01"),
        time_index=0,
    )

    out_path = tmp_path / "plants_cohort_data.csv"

    # Check the output CSV file.
    cell_n_cohorts = np.array(
        [len(cmty.cohorts) for _, cmty in communities.items()]
    ).sum()

    # This needs access to instance so not defined in parameterisation. These
    # definitions also check the definitions of the mandatory export fields and the
    # available fields.
    match attributes:
        case _ if attributes == set():
            expected = set()
        case "ALL":
            expected = exporter.available_attributes["cohort_attributes"]
        case _:
            expected = set(
                [
                    *exporter._mandatory_attributes["cohort_attributes"],
                    *attributes,
                ]
            )

    csv_check(path=out_path, n_rows=cell_n_cohorts, attr=attributes, expected=expected)


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
@pytest.mark.parametrize(
    argnames="attributes",
    argvalues=(
        pytest.param([], id="no_ccan"),
        pytest.param("ALL", id="all_ccan"),
        pytest.param({"transmission_profile", "cell_id"}, id="some_ccan"),
    ),
)
def test_CommunityDataExporter_dump_community_canopy_data(
    tmp_path,
    fixture_exporter_components,
    tricky_plant_cohorts,  # Set that the straightforward cohort data gets used
    attributes,
):
    """Test CommunityDataExporter _dump_community_canopy_data method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        community_canopy_attributes=attributes,
    )

    # First dump in write mode with no allocations: expected behaviour in setup
    _, canopies, _, _, _ = fixture_exporter_components
    exporter._dump_community_canopy_data(
        canopies=canopies,
        time=np.datetime64("2000-01-01"),
        time_index=0,
    )

    out_path = tmp_path / "plants_community_canopy_data.csv"

    # Check the output CSV file.
    cell_n_layers = np.array([len(cpy.heights) for cpy in canopies.values()]).sum()

    # This needs access to instance so not defined in parameterisation. These
    # definitions also check the definitions of the mandatory export fields and the
    # available fields.
    match attributes:
        case _ if attributes == set():
            expected = set()
        case "ALL":
            expected = exporter.available_attributes["community_canopy_attributes"]
        case _:
            expected = set(
                [
                    *exporter._mandatory_attributes["community_canopy_attributes"],
                    *attributes,
                ]
            )

    csv_check(path=out_path, n_rows=cell_n_layers, attr=attributes, expected=expected)


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
@pytest.mark.parametrize(
    argnames="attributes",
    argvalues=(
        pytest.param([], id="no_scan"),
        pytest.param("ALL", id="all_scan"),
        pytest.param({"fapar", "cell_id"}, id="some_scan"),
    ),
)
def test_CommunityDataExporter_dump_stem_canopy_data(
    tmp_path,
    fixture_exporter_components,
    tricky_plant_cohorts,  # Set that the straightforward cohort data gets used
    attributes,
):
    """Test CommunityDataExporter _dump_stem_canopy_data method."""

    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    # Create the exporter
    exporter = CommunityDataExporter(
        output_directory=tmp_path,
        stem_canopy_attributes=attributes,
    )

    # Run the dump
    communities, canopies, _, _, _ = fixture_exporter_components
    exporter._dump_stem_canopy_data(
        communities=communities,
        canopies=canopies,
        time=np.datetime64("2000-01-01"),
        time_index=0,
    )

    out_path = tmp_path / "plants_stem_canopy_data.csv"

    # Check the output CSV file.
    cell_n_cohorts = np.array([len(cmty.cohorts) for _, cmty in communities.items()])
    cell_n_layers = np.array([len(cpy.heights) for cpy in canopies.values()])
    cell_n_stem_layers = (cell_n_cohorts * cell_n_layers).sum()

    # This needs access to instance so not defined in parameterisation. These
    # definitions also check the definitions of the mandatory export fields and the
    # available fields.
    match attributes:
        case _ if attributes == set():
            expected = set()
        case "ALL":
            expected = exporter.available_attributes["stem_canopy_attributes"]
        case _:
            expected = set(
                [
                    *exporter._mandatory_attributes["stem_canopy_attributes"],
                    *attributes,
                ]
            )

    csv_check(
        path=out_path, n_rows=cell_n_stem_layers, attr=attributes, expected=expected
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
@pytest.mark.parametrize(
    argnames=("cohort, community_canopy, stem_canopy"),
    argvalues=(
        pytest.param("ALL", "ALL", "ALL", id="all_required"),
        pytest.param(set(), "ALL", "ALL", id="two_required"),
        pytest.param("ALL", set(), set(), id="one_required"),
        pytest.param(set(), set(), set(), id="none_required"),
    ),
)
class TestExporterDump:
    """Common testing of the dump method by various routes.

    This class uses combinations of settings for each of the three files and then uses
    those to check the exporter created directly and running outside of a model,
    through an exporter created from config, and then through a model.
    """

    def setup_method(self):
        """Initialise counters on expected row counts."""
        self.expected_n = dict(cohort=0, community_canopy=0, stem_canopy=0)

    def increment_expected_n(self, communities, canopies) -> None:
        """Increment expected numbers of rows in the three data files."""
        cht_by_cell = np.array([len(c.cohorts) for c in communities.values()])
        lyrs_by_cell = np.array([len(cpy.heights) for cpy in canopies.values()])

        self.expected_n["cohort"] += cht_by_cell.sum()
        self.expected_n["community_canopy"] += lyrs_by_cell.sum()
        self.expected_n["stem_canopy"] += (cht_by_cell * lyrs_by_cell).sum()

    def check_output(self, path, exporter):
        """Shared validation function."""
        # Loop over the possible data types, check the file exists if data requested and
        # that it has the expected number of rows.
        for type, file in exporter._output_files.items():
            attr_value = getattr(exporter, f"{type}_attributes")
            csv_check(path=path / file, n_rows=self.expected_n[type], attr=attr_value)

    def test_CommunityDataExporter_dump(
        self,
        tmp_path,
        fixture_exporter_components,
        cohort,
        community_canopy,
        stem_canopy,
    ):
        """Test the from_config factory method."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

        # Create the exporter
        exporter = CommunityDataExporter(
            output_directory=tmp_path,
            cohort_attributes=cohort,
            community_canopy_attributes=community_canopy,
            stem_canopy_attributes=stem_canopy,
        )

        if any(cohort or community_canopy or stem_canopy):
            assert exporter._active
        else:
            assert not exporter._active

        assert exporter._output_mode == "w"
        assert exporter._write_header

        # First dump in write mode with no allocations: expected behaviour in setup
        communities, canopies, stem_allocations, growth_increments, biomasses = (
            fixture_exporter_components
        )
        exporter.dump(
            communities=communities,
            biomasses=biomasses,
            canopies=canopies,
            stem_allocations={},
            growth_increments={},
            time=np.datetime64("2000-01-01"),
            time_index=0,
        )

        if exporter._active:
            assert exporter._output_mode == "a"
            assert not exporter._write_header

        self.increment_expected_n(communities, canopies)
        self.check_output(tmp_path, exporter)

        # Second dump to check mode switching from write to append and provided stem
        # allocations: expected behaviour in update
        exporter.dump(
            communities=communities,
            biomasses=biomasses,
            canopies=canopies,
            stem_allocations=stem_allocations,
            growth_increments=growth_increments,
            time=np.datetime64("2001-01-01"),
            time_index=0,
        )

        # Check the files are ok and have increased their number of row
        self.increment_expected_n(communities, canopies)
        self.check_output(tmp_path, exporter)

    def test_CommunityDataExporter_in_model(
        self,
        tmp_path,
        plants_data,
        fixture_flora,
        plants_cohort_data,
        fixture_core_components,
        fixture_canopy_layer_data,
        cohort,
        community_canopy,
        stem_canopy,
    ):
        """Test the exporter runs as expected from within a PlantsModel."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
        from virtual_ecosystem.models.plants.plants_model import PlantsModel

        exporter = CommunityDataExporter(
            output_directory=tmp_path,
            cohort_attributes=cohort,
            community_canopy_attributes=community_canopy,
            stem_canopy_attributes=stem_canopy,
        )

        if any(cohort or community_canopy or stem_canopy):
            assert exporter._active

        assert exporter._output_mode == "w"
        assert exporter._write_header

        # Create plant model to run PlantsModel._setup and hence the dump method
        model = PlantsModel(
            data=plants_data,
            core_components=fixture_core_components,
            flora=fixture_flora,
            cohort_data=plants_cohort_data,
            exporter=exporter,
        )

        if exporter._active:
            assert exporter._output_mode == "a"
            assert not exporter._write_header

        # Simple checks - files exists, can be read, have the right number of rows.
        self.increment_expected_n(model.communities, model.canopies)
        self.check_output(tmp_path, exporter)

        # Update the model to trigger a second dump
        model.update(time_index=0)

        # Recalculate the expected number of cohorts - recruitment and mortality affect
        # the exporter within the model and then recheck the files
        self.increment_expected_n(model.communities, model.canopies)
        self.check_output(tmp_path, exporter)

    def test_CommunityDataExporter_through_config(
        self,
        tmp_path,
        fixture_exporter_components,
        cohort,
        community_canopy,
        stem_canopy,
    ):
        """Test the from_config factory method."""

        from virtual_ecosystem.models.plants.exporter import CommunityDataExporter
        from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

        # Note that the single quotes around the out_path are _required_ here: TOML uses
        # single quotes to indicate raw strings and hence protect the backslashes in
        # Windows path names from being interpreted as escape sequences.

        config = PlantsExportConfig(
            cohort_attributes=cohort,
            community_canopy_attributes=community_canopy,
            stem_canopy_attributes=stem_canopy,
        )

        exporter = CommunityDataExporter.from_config(
            output_directory=tmp_path, config=config
        )

        if any(cohort or community_canopy or stem_canopy):
            assert exporter._active

        assert exporter._output_mode == "w"
        assert exporter._write_header

        # First dump in write mode with no allocations: expected behaviour in setup
        communities, canopies, _, _, biomasses = fixture_exporter_components
        exporter.dump(
            communities=communities,
            biomasses=biomasses,
            canopies=canopies,
            stem_allocations={},
            growth_increments={},
            time=np.datetime64("2000-01-01"),
            time_index=0,
        )

        if exporter._active:
            assert exporter._output_mode == "a"
            assert not exporter._write_header
