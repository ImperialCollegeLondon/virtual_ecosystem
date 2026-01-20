"""Tests the models.animal.exporter.AnimalCohortDataExporter class."""

import pytest


def csv_row_check(path, n_rows, expected_columns=None):
    """Check that a CSV exists and has expected properties.

    Args:
        path: Path-like object for the CSV file or None.
        n_rows: Expected number of rows in the CSV.
        expected_columns: Optional iterable of required column names.
    """
    if path is None:
        return

    import pandas as pd

    assert path.exists()
    content = pd.read_csv(path)
    assert len(content) == n_rows

    if expected_columns is not None:
        assert set(content.columns) >= set(expected_columns)


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
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=False,
            cohort_attributes=(),
            float_format="%0.3f",
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        assert exporter._active is False
        assert exporter._cohort_path is None
        assert exporter.float_format == "%0.3f"

        exporter.dump(communities={}, time=np.datetime64("2000-01-01"), time_index=0)

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
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("is_alive",),
            float_format="%0.4f",
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        expected_path = output_dir / "animal_cohort_data.csv"
        assert exporter._active is True
        assert exporter._cohort_path == expected_path
        assert exporter.cohort_attributes == {"is_alive"}
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
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

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

    def test_from_config_raises_if_output_directory_missing(self, tmp_path):
        """Test that a missing output directory raises ConfigurationError.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        from virtual_ecosystem.core.exceptions import ConfigurationError
        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

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
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

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
            "mass_carbon",
            "mass_nitrogen",
            "mass_phosphorus",
        ]:
            assert field in attrs

    def test_dump_writes_rows_and_respects_attribute_subset(
        self,
        tmp_path,
        herbivore_cohort_instance,
        predator_cohort_instance,
    ):
        """Test dump writes expected rows and respects attribute subset.

        This uses real AnimalCohort instances from fixtures rather than dummies.

        Args:
            tmp_path: Temporary directory provided by pytest.
            herbivore_cohort_instance: Herbivore cohort fixture.
            predator_cohort_instance: Predator cohort fixture.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("is_alive",),
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        communities = {
            1: [herbivore_cohort_instance],
            2: [predator_cohort_instance],
        }

        time_1 = np.datetime64("2001-01-01")
        time_2 = np.datetime64("2001-01-02")

        exporter.dump(communities=communities, time=time_1, time_index=0)
        exporter.dump(communities=communities, time=time_2, time_index=1)

        output_path = output_dir / "animal_cohort_data.csv"
        assert output_path.exists()

        df = pd.read_csv(output_path)

        assert set(df.columns) == {
            "cell_id",
            "time",
            "cohort_id",
            "time_index",
            "is_alive",
        }
        # two cohorts, two time steps
        assert len(df) == 4

        expected_times = {str(time_1), str(time_2)}
        assert set(df["time"].astype(str).unique()) == expected_times

        # We do not check exact cohort ids here, just that there are two distinct ones.
        assert len(set(df["cohort_id"].unique())) == 2

    def test_mode_and_header_toggling(
        self,
        tmp_path,
        herbivore_cohort_instance,
    ):
        """Test mode and header flags switch from write to append.

        Args:
            tmp_path: Temporary directory provided by pytest.
            herbivore_cohort_instance: Herbivore cohort fixture.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

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

        communities = {1: [herbivore_cohort_instance]}

        time_1 = np.datetime64("2001-01-01")
        time_2 = np.datetime64("2001-01-02")

        exporter.dump(communities=communities, time=time_1, time_index=0)

        assert exporter._output_mode == "a"
        assert exporter._write_header is False

        exporter.dump(communities=communities, time=time_2, time_index=1)

        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        # Same cohort written twice at two times
        assert len(df) == 2

    def test_from_config_then_dump_creates_expected_file(
        self,
        tmp_path,
        herbivore_cohort_instance,
        predator_cohort_instance,
    ):
        """Test exporter from config dumps data and flips mode/header.

        Args:
            tmp_path: Temporary directory provided by pytest.
            herbivore_cohort_instance: Herbivore cohort fixture.
            predator_cohort_instance: Predator cohort fixture.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import (
            AnimalCohortDataExporter,
        )
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        output_dir = Path(tmp_path)

        config = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("is_alive",),
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        assert exporter._active
        assert exporter._output_mode == "w"
        assert exporter._write_header

        communities = {
            1: [herbivore_cohort_instance],
            2: [predator_cohort_instance],
        }

        time_val = np.datetime64("2001-01-01")

        exporter.dump(communities=communities, time=time_val, time_index=0)

        assert exporter._output_mode == "a"
        assert exporter._write_header is False

        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert set(df.columns) == {
            "cell_id",
            "time",
            "cohort_id",
            "time_index",
            "is_alive",
        }
        assert len(df) == 2

        # Two distinct cohorts written once each.
        assert len(set(df["cell_id"].unique())) == 2
        assert len(set(df["cohort_id"].unique())) == 2

    def test_exporter_runs_inside_animal_model(
        self,
        tmp_path,
        dummy_animal_data,
        fixture_core_components,
        functional_group_list_instance,
        microbial_c_n_p_ratios,
    ):
        """Test that the exporter runs correctly inside an AnimalModel.

        Args:
            tmp_path: Temporary directory provided by pytest.
            dummy_animal_data: Data fixture for the animal model.
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
        from virtual_ecosystem.models.animal.model_config import (
            AnimalConstants,
        )

        clean_data = deepcopy(dummy_animal_data)

        output_dir = Path(tmp_path)
        exporter = AnimalCohortDataExporter(
            output_directory=output_dir,
            cohort_attributes=None,
        )

        assert exporter._output_mode == "w"
        assert exporter._write_header

        model = AnimalModel(
            data=clean_data,
            core_components=fixture_core_components,
            model_constants=AnimalConstants(density_scaling_method="madingley"),
            functional_groups=functional_group_list_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
            exporter=exporter,
        )

        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        assert exporter._output_mode == "a"
        assert exporter._write_header is False

        df_initial = pd.read_csv(out_path)
        initial_rows = len(df_initial)
        assert initial_rows > 0

        model.update(time_index=0)

        df_updated = pd.read_csv(out_path)
        updated_rows = len(df_updated)

        assert updated_rows > initial_rows
