"""Tests the models.animals.exporter.AnimalCohortDataExporter class."""

import pytest


@pytest.fixture
def dummy_cohort_factory():
    """Provide a factory for minimal AnimalCohort stand-ins.

    Returns:
        Callable that creates dummy cohort instances with the attributes
        required by the AnimalCohortDataExporter.
    """

    class DummyFunctionalGroup:
        """Simple stand-in for FunctionalGroup."""

        def __init__(self, name: str) -> None:
            """Initialize DummyFunctionalGroup.

            Args:
                name: Name of the functional group.
            """
            self.name = name
            self.development_type = "direct"
            self.diet = "herbivore"
            self.reproductive_environment = "terrestrial"

    class DummyCNP:
        """Simple stand-in for CNP."""

        def __init__(self, carbon: float, nitrogen: float, phosphorus: float):
            """Initialize DummyCNP.

            Args:
                carbon: Carbon mass.
                nitrogen: Nitrogen mass.
                phosphorus: Phosphorus mass.
            """
            self.carbon = carbon
            self.nitrogen = nitrogen
            self.phosphorus = phosphorus

    class DummyCohort:
        """Simple stand-in for AnimalCohort with required attributes."""

        def __init__(self, cohort_id: str, fg_name: str, age: float):
            """Initialize DummyCohort.

            Args:
                cohort_id: Identifier for the cohort.
                fg_name: Functional group name.
                age: Cohort age.
            """
            self.id = cohort_id
            self.functional_group = DummyFunctionalGroup(fg_name)
            self.age = age
            self.individuals = 10.0
            self.is_alive = True
            self.is_mature = False
            self.time_to_maturity = 5.0
            self.time_since_maturity = 0.0
            self.location_status = "resident"
            self.centroid_key = 0
            self.territory_size = 1.0
            self.occupancy_proportion = 1.0
            self.largest_mass_achieved = 2.0
            self.mass_cnp = DummyCNP(1.0, 0.1, 0.01)
            self.reproductive_mass_cnp = DummyCNP(0.2, 0.02, 0.002)

    def factory(cohort_id: str, fg_name: str = "fg", age: float = 1.0) -> DummyCohort:
        """Create a dummy cohort instance.

        Args:
            cohort_id: Identifier for the cohort.
            fg_name: Functional group name.
            age: Cohort age.

        Returns:
            A dummy cohort instance.
        """
        return DummyCohort(cohort_id=cohort_id, fg_name=fg_name, age=age)

    return factory


class TestAnimalCohortDataExporter:
    """Tests for AnimalCohortDataExporter."""

    def test_from_config_disabled_creates_inactive_exporter(self, tmp_path):
        """Test that a disabled config creates an inactive exporter.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        import numpy as np

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=False,
            cohort_attributes=(),
            float_format="%0.3f",
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir, config=config
        )

        assert exporter._active is False
        assert exporter._cohort_path is None
        assert exporter.float_format == "%0.3f"

        exporter.dump(communities={}, time=np.datetime64("2000-01-01"))

        output_path = output_dir / "animal_cohort_data.csv"
        assert output_path.exists() is False

    def test_from_config_enabled_sets_path_and_attributes(self, tmp_path):
        """Test enabled config sets up path and attribute subset correctly.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("cell_id", "time", "cohort_id"),
            float_format="%0.4f",
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        expected_path = output_dir / "animal_cohort_data.csv"
        assert exporter._active is True
        assert exporter._cohort_path == expected_path
        assert exporter.cohort_attributes == {"cell_id", "time", "cohort_id"}
        assert exporter.float_format == "%0.4f"

    def test_from_config_raises_if_output_file_exists(self, tmp_path):
        """Test that an existing output file raises a ConfigurationError.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        from virtual_ecosystem.core.exceptions import ConfigurationError
        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)
        existing = output_dir / "animal_cohort_data.csv"
        existing.touch()

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=(),
        )

        with pytest.raises(ConfigurationError):
            AnimalCohortDataExporter.from_config(
                output_directory=output_dir,
                config=config,
            )

    def test_from_config_raises_on_unknown_attribute(self, tmp_path):
        """Test that unknown cohort attributes raise a ConfigurationError.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        from virtual_ecosystem.core.exceptions import ConfigurationError
        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("not_a_real_field",),
        )

        with pytest.raises(ConfigurationError):
            AnimalCohortDataExporter.from_config(
                output_directory=output_dir,
                config=config,
            )

    def test_dump_writes_rows_and_respects_attribute_subset(
        self,
        tmp_path,
        dummy_cohort_factory,
    ):
        """Test dump writes expected rows and respects attribute subset.

        Args:
            tmp_path: Temporary directory provided by pytest.
            dummy_cohort_factory: Factory for dummy cohort instances.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("cell_id", "time", "cohort_id"),
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        communities = {
            1: [dummy_cohort_factory("cohort-1", "fg1", age=1.0)],
            2: [dummy_cohort_factory("cohort-2", "fg2", age=2.0)],
        }

        time_1 = np.datetime64("2001-01-01")
        time_2 = np.datetime64("2001-01-02")

        exporter.dump(communities=communities, time=time_1)
        exporter.dump(communities=communities, time=time_2)

        output_path = output_dir / "animal_cohort_data.csv"
        assert output_path.exists()

        df = pd.read_csv(output_path)

        assert set(df.columns) == {"cell_id", "time", "cohort_id"}
        assert len(df) == 4

        expected_times = {str(time_1), str(time_2)}
        assert set(df["time"].astype(str).unique()) == expected_times

        assert set(df["cell_id"].unique()) == {1, 2}
        assert set(df["cohort_id"].unique()) == {"cohort-1", "cohort-2"}

    def test_mode_and_header_toggling(self, tmp_path, dummy_cohort_factory):
        """Test mode and header flags switch from write to append.

        Args:
            tmp_path: Temporary directory provided by pytest.
            dummy_cohort_factory: Factory for dummy cohort instances.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=(),
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        assert exporter._output_mode == "w"
        assert exporter._write_header

        communities = {1: [dummy_cohort_factory("cohort-1")]}

        time_1 = np.datetime64("2001-01-01")
        time_2 = np.datetime64("2001-01-02")

        exporter.dump(communities=communities, time=time_1)

        assert exporter._output_mode == "a"
        assert not exporter._write_header

        exporter.dump(communities=communities, time=time_2)

        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert len(df) == 2
        assert set(df["cohort_id"].unique()) == {"cohort-1"}

    def test_from_config_then_dump_creates_expected_file(
        self,
        tmp_path,
        dummy_cohort_factory,
    ):
        """Test exporter built from config dumps data and flips mode/header.

        Args:
            tmp_path: Temporary directory provided by pytest.
            dummy_cohort_factory: Factory for dummy cohort instances.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("cell_id", "time", "cohort_id"),
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        assert exporter._active
        assert exporter._output_mode == "w"
        assert exporter._write_header

        communities = {
            1: [dummy_cohort_factory("cohort-1")],
            2: [dummy_cohort_factory("cohort-2")],
        }

        time_val = np.datetime64("2001-01-01")

        exporter.dump(communities=communities, time=time_val)

        assert exporter._output_mode == "a"
        assert not exporter._write_header

        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert set(df.columns) == {"cell_id", "time", "cohort_id"}
        assert len(df) == 2
        assert set(df["cell_id"].unique()) == {1, 2}
        assert set(df["cohort_id"].unique()) == {"cohort-1", "cohort-2"}

    def test_from_config_raises_if_output_directory_missing(self, tmp_path):
        """Test that a missing output directory raises ConfigurationError.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        import pytest

        from virtual_ecosystem.core.exceptions import ConfigurationError
        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalExportConfig

        bad_dir = Path(tmp_path / "does_not_exist")

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=(),
        )

        with pytest.raises(ConfigurationError):
            AnimalCohortDataExporter.from_config(
                output_directory=bad_dir,
                config=config,
            )

    def test_available_attributes_contains_core_fields(self, tmp_path):
        """Test that available_attributes exposes key cohort fields.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )

        output_dir = Path(tmp_path)

        exporter = AnimalCohortDataExporter(
            output_directory=output_dir,
            cohort_attributes=None,
        )

        attrs = exporter.available_attributes

        for field in [
            "cell_id",
            "time",
            "cohort_id",
            "mass_carbon",
            "mass_nitrogen",
            "mass_phosphorus",
        ]:
            assert field in attrs

    def test_exporter_runs_inside_animal_model(
        self,
        tmp_path,
        dummy_animal_data,
        fixture_core_components,
        functional_group_list_instance,
        microbial_c_n_p_ratios,
    ):
        """Test that the exporter runs correctly inside an AnimalModel.

        This mirrors the plant exporter integration test. The Exporter should:
        * perform one dump during AnimalModel._setup
        * perform additional dumps during update()
        * flip from write/header mode to append/no-header mode

        Args:
            tmp_path: Temporary directory provided by pytest.
            dummy_animal_data: Fixture producing Data for the animal model.
            fixture_core_components: CoreComponents fixture.
            functional_group_list_instance: List of animal functional groups.
            microbial_c_n_p_ratios: Microbial stoichiometry ratios.
        """

        from copy import deepcopy
        from pathlib import Path

        import pandas as pd

        from virtual_ecosystem.models.animal.animal_model import AnimalModel
        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import AnimalConstants

        # --- Prepare fresh data so we do not mutate shared fixtures ---
        clean_data = deepcopy(dummy_animal_data)

        # --- Create the exporter we will inject into the AnimalModel ---
        output_dir = Path(tmp_path)
        exporter = AnimalCohortDataExporter(
            output_directory=output_dir,
            cohort_attributes=None,
        )

        # Sanity: exporter starts in write + header mode
        assert exporter._output_mode == "w"
        assert exporter._write_header

        # --- Construct a minimal but valid AnimalModel with the exporter ---
        model = AnimalModel(
            data=clean_data,
            core_components=fixture_core_components,
            model_constants=AnimalConstants(density_scaling_method="madingley"),
            functional_groups=functional_group_list_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
            exporter=exporter,
        )

        # After _setup, initial export should have occurred
        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        # Exporter should now be in append mode
        assert exporter._output_mode == "a"
        assert exporter._write_header is False

        # Row count after setup
        df_initial = pd.read_csv(out_path)
        initial_rows = len(df_initial)
        assert initial_rows > 0

        # --- Trigger an update to generate the second export ---
        model.update(time_index=0)

        df_updated = pd.read_csv(out_path)
        updated_rows = len(df_updated)

        # Should append new rows (one per cohort)
        assert updated_rows > initial_rows
