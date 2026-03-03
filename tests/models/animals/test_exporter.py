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

        exporter.dump(cohorts={}, time=np.datetime64("2000-01-01"), time_index=0)

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
        assert set(exporter.required_attributes) == {"time", "cohort_id", "time_index"}

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

        attrs = exporter.available_attributes | set(exporter.required_attributes)

        for field in [
            "time",
            "cohort_id",
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
            cohort_attributes=(
                "time",
                "is_alive",
            ),
        )

        exporter = AnimalCohortDataExporter.from_config(
            output_directory=output_dir,
            config=config,
        )

        cohorts = [herbivore_cohort_instance, predator_cohort_instance]

        time_1 = np.datetime64("2001-01-01")
        time_2 = np.datetime64("2001-01-02")

        exporter.dump(cohorts=cohorts, time=time_1, time_index=0)
        exporter.dump(cohorts=cohorts, time=time_2, time_index=1)

        output_path = output_dir / "animal_cohort_data.csv"
        assert output_path.exists()

        df = pd.read_csv(output_path)

        assert set(df.columns) == {
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

        assert exporter._cohort_output_mode == "w"
        assert exporter._write_cohort_header

        assert exporter._trophic_output_mode == "w"
        assert exporter._write_trophic_header

        cohorts = [herbivore_cohort_instance]

        time_1 = np.datetime64("2001-01-01")
        time_2 = np.datetime64("2001-01-02")

        exporter.dump(cohorts=cohorts, time=time_1, time_index=0)

        assert exporter._cohort_output_mode == "a"
        assert exporter._write_cohort_header is False

        exporter.dump(cohorts=cohorts, time=time_2, time_index=1)

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
        assert exporter._cohort_output_mode == "w"
        assert exporter._write_cohort_header

        assert exporter._trophic_output_mode == "w"
        assert exporter._write_trophic_header

        cohorts = [herbivore_cohort_instance, predator_cohort_instance]

        time_val = np.datetime64("2001-01-01")

        exporter.dump(cohorts=cohorts, time=time_val, time_index=0)

        assert exporter._cohort_output_mode == "a"
        assert exporter._write_cohort_header is False

        out_path = output_dir / "animal_cohort_data.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert set(df.columns) == {
            "time",
            "cohort_id",
            "time_index",
            "is_alive",
        }

        assert len(df) == 2

        # Two distinct cohorts written once each.
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

        assert exporter._cohort_output_mode == "w"
        assert exporter._write_cohort_header

        assert exporter._trophic_output_mode == "w"
        assert exporter._write_trophic_header

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

        assert exporter._cohort_output_mode == "a"
        assert exporter._write_cohort_header is False

        df_initial = pd.read_csv(out_path)
        initial_rows = len(df_initial)
        assert initial_rows > 0

        model.update(time_index=0)

        df_updated = pd.read_csv(out_path)
        updated_rows = len(df_updated)

        assert updated_rows > initial_rows

    def test_check_and_set_paths_sets_paths_for_all_outputs(self, tmp_path):
        """Test _check_and_set_paths sets cohort and trophic paths.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter

        exporter = AnimalCohortDataExporter.__new__(AnimalCohortDataExporter)
        exporter.output_directory = Path(tmp_path)

        exporter._cohort_path = None
        exporter._trophic_path = None

        exporter._check_and_set_paths()

        assert exporter._cohort_path == Path(tmp_path) / "animal_cohort_data.csv"
        assert (
            exporter._trophic_path == Path(tmp_path) / "animal_trophic_interactions.csv"
        )

    def test_check_attribute_subsets_raises_on_unknown_optional_attribute(
        self, tmp_path
    ):
        """Test _check_attribute_subsets raises for unknown attributes.

        Args:
            tmp_path: Temporary directory provided by pytest.
        """
        from pathlib import Path

        import pytest

        from virtual_ecosystem.core.exceptions import ConfigurationError
        from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter

        exporter = AnimalCohortDataExporter.__new__(AnimalCohortDataExporter)
        exporter.output_directory = Path(tmp_path)
        exporter.cohort_attributes = {"not_a_real_field"}

        with pytest.raises(ConfigurationError, match="unknown attributes"):
            exporter._check_attribute_subsets()

    def test_build_cohort_row_includes_required_and_selected_fields(self, mocker):
        """Test _build_cohort_row serialises expected fields.

        Args:
            mocker: Pytest mocker fixture.
        """
        import numpy as np

        from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter

        exporter = AnimalCohortDataExporter.__new__(AnimalCohortDataExporter)

        fg = mocker.Mock()
        fg.name = "Herbivore"
        fg.development_type = "direct"
        fg.diet = "foliage"
        fg.reproductive_environment = "terrestrial"

        mass_cnp = mocker.Mock(C=1.0, N=2.0, P=3.0)
        repro_cnp = mocker.Mock(C=0.1, N=0.2, P=0.3)

        cohort = mocker.Mock()
        cohort.id = "abc"
        cohort.functional_group = fg
        cohort.mass_cnp = mass_cnp
        cohort.reproductive_mass_cnp = repro_cnp

        cohort.age = 10
        cohort.individuals = 5
        cohort.is_alive = True
        cohort.is_mature = False
        cohort.time_to_maturity = 123
        cohort.time_since_maturity = 0
        cohort.location_status = "settled"
        cohort.centroid_key = 7
        cohort.territory_size = 1
        cohort.territory = [7]
        cohort.occupancy_proportion = 1.0
        cohort.largest_mass_achieved = 99.0

        t = np.datetime64("2001-01-01")
        row = exporter._build_cohort_row(cohort=cohort, time=t, time_index=42)

        assert row["time"] == t
        assert row["time_index"] == 42
        assert row["cohort_id"] == "abc"
        assert row["functional_group"] == "Herbivore"
        assert row["mass_carbon"] == 1.0
        assert row["reproductive_mass_phosphorus"] == 0.3
        assert row["is_alive"] is True

    def test_build_trophic_rows_handles_cohort_and_pool_resources(self, mocker):
        """Test _build_trophic_rows builds rows for cohort prey and pools.

        Args:
            mocker: Pytest mocker fixture.
        """
        import numpy as np

        from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter

        exporter = AnimalCohortDataExporter.__new__(AnimalCohortDataExporter)

        cohort = mocker.Mock()
        cohort.id = "pred"
        cohort.territory = [1, 2]

        cohort.trophic_record = {
            ("cohort", "prey-1"): {"C": 1.0, "N": 2.0, "P": 3.0},
            ("carcass_pool", "60"): {"C": 4.0, "N": 5.0, "P": 6.0},
        }
        territory_by_id = {"prey-1": [9]}

        t = np.datetime64("2013-01-01")
        rows = exporter._build_trophic_rows(
            cohort=cohort,
            territory_by_id=territory_by_id,
            time=t,
            time_index=7,
        )

        assert len(rows) == 2

        cohort_row = next(r for r in rows if r["resource_kind"] == "cohort")
        assert cohort_row["time"] == t
        assert cohort_row["time_index"] == 7
        assert cohort_row["consumer_cohort_id"] == "pred"
        assert cohort_row["prey_territory"] == [9]
        assert cohort_row["resource_cell_id"] is None
        assert cohort_row["C"] == 1.0

        pool_row = next(r for r in rows if r["resource_kind"] == "carcass_pool")
        assert pool_row["resource_id"] == "60"
        assert pool_row["resource_cell_id"] == 60
        assert pool_row["prey_territory"] is None
        assert pool_row["P"] == 6.0

    def test_dump_cohorts_writes_file_and_flips_cohort_state(self, tmp_path, mocker):
        """Test _dump_cohorts writes cohort CSV and flips cohort write state.

        Args:
            tmp_path: Temporary directory provided by pytest.
            mocker: Pytest mocker fixture.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter

        exporter = AnimalCohortDataExporter(
            output_directory=Path(tmp_path),
            cohort_attributes={"is_alive"},
        )

        cohort = mocker.Mock()
        cohort.id = "c1"
        cohort.functional_group = mocker.Mock(
            name="X", development_type="d", diet="e", reproductive_environment="r"
        )
        cohort.mass_cnp = mocker.Mock(C=1.0, N=1.0, P=1.0)
        cohort.reproductive_mass_cnp = mocker.Mock(C=0.0, N=0.0, P=0.0)
        cohort.age = 0
        cohort.individuals = 1
        cohort.is_alive = True
        cohort.is_mature = False
        cohort.time_to_maturity = 0
        cohort.time_since_maturity = 0
        cohort.location_status = "s"
        cohort.centroid_key = 0
        cohort.territory_size = 0
        cohort.territory = [1]
        cohort.occupancy_proportion = 1.0
        cohort.largest_mass_achieved = 0.0

        assert exporter._cohort_output_mode == "w"
        assert exporter._write_cohort_header is True

        exporter._dump_cohorts(
            cohorts=[cohort],
            time=np.datetime64("2000-01-01"),
            time_index=0,
        )

        out_path = Path(tmp_path) / "animal_cohort_data.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert set(df.columns) == {"time", "cohort_id", "time_index", "is_alive"}
        assert len(df) == 1

        assert exporter._cohort_output_mode == "a"
        assert exporter._write_cohort_header is False

    def test_dump_trophic_writes_file_and_flips_trophic_state(self, tmp_path, mocker):
        """Test _dump_trophic writes trophic CSV and flips trophic write state.

        Args:
            tmp_path: Temporary directory provided by pytest.
            mocker: Pytest mocker fixture.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        from virtual_ecosystem.models.animal.exporter import AnimalCohortDataExporter

        exporter = AnimalCohortDataExporter(
            output_directory=Path(tmp_path), cohort_attributes=None
        )

        cohort = mocker.Mock()
        cohort.id = "c1"
        cohort.territory = [10]
        cohort.trophic_record = {("carcass_pool", "60"): {"C": 1.0, "N": 2.0, "P": 3.0}}

        assert exporter._trophic_output_mode == "w"
        assert exporter._write_trophic_header is True

        exporter._dump_trophic(
            cohorts=[cohort],
            territory_by_id={},
            time=np.datetime64("2000-01-01"),
            time_index=0,
        )

        out_path = Path(tmp_path) / "animal_trophic_interactions.csv"
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert len(df) == 1
        assert set(df.columns) >= {
            "time",
            "time_index",
            "consumer_cohort_id",
            "resource_kind",
            "resource_id",
            "resource_cell_id",
            "C",
            "N",
            "P",
        }

        assert exporter._trophic_output_mode == "a"
        assert exporter._write_trophic_header is False
