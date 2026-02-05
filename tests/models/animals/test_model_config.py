"""Test the custom validation and serialisation on the animals.model_config module."""

import pytest

from virtual_ecosystem.models.animal.animal_traits import DietType


@pytest.mark.parametrize(
    argnames="deserialised,serialised",
    argvalues=(
        (DietType.CARNIVORE, "CARNIVORE"),
        (DietType.FRUIT | DietType.NECTAR, "FRUIT|NECTAR"),
    ),
)
def test_DietType_serialisation(deserialised, serialised):
    """Check the DietType serialisation functions."""
    from virtual_ecosystem.models.animal.model_config import (
        deserialise_diet_type,
        serialise_diet_type,
    )

    as_json = serialise_diet_type(deserialised)
    as_diet_type = deserialise_diet_type(serialised)

    assert as_json == serialised
    assert as_diet_type == deserialised


def test_AnimalConstants_dump_and_load():
    """Test the AnimalConstants writes and reads as expected."""

    from virtual_ecosystem.models.animal.model_config import AnimalConstants

    model = AnimalConstants()

    json_data = model.model_dump_json()

    # Check a DietType has been correctly serialised as text
    assert "CARNIVORE" in json_data

    new_model = AnimalConstants.model_validate_json(json_data)

    assert model == new_model


class TestAnimalExportConfig:
    """Tests for the AnimalExportConfig configuration model."""

    def test_default_values(self):
        """Test default values for AnimalExportConfig.

        Checks that the configuration initialises with the documented default
        values.
        """
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        cfg = AnimalExportConfig()

        assert cfg.enabled is False
        assert cfg.cohort_attributes == ()
        assert cfg.float_format == "%0.5f"

    def test_cohort_attributes_coerce_to_tuple(self):
        """Test cohort_attributes are stored as a tuple of strings.

        This ensures that initialising with a list produces the expected
        tuple-valued field.
        """
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        cfg = AnimalExportConfig(cohort_attributes=["cell_id", "time"])

        assert isinstance(cfg.cohort_attributes, tuple)
        assert cfg.cohort_attributes == ("cell_id", "time")

    def test_serialisation_round_trip(self):
        """Test AnimalExportConfig serialises and deserialises correctly.

        The nested fields should survive a JSON round trip without change.
        """
        from virtual_ecosystem.models.animal.model_config import (
            AnimalExportConfig,
        )

        original = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("cell_id", "time", "cohort_id"),
            float_format="%0.3f",
        )

        json_str = original.model_dump_json()
        restored = AnimalExportConfig.model_validate_json(json_str)

        assert restored == original


class TestAnimalConfiguration:
    """Tests for the AnimalConfiguration root model."""

    def test_default_nested_export_config(self, tmp_path):
        """Test AnimalConfiguration creates a default export config.

        Verifies that the nested AnimalExportConfig is initialised with its
        documented defaults.
        """
        from pathlib import Path

        from virtual_ecosystem.models.animal.model_config import (
            AnimalConfiguration,
        )

        fg_path = Path(tmp_path / "functional_groups.csv")
        fg_path.touch()

        cfg = AnimalConfiguration(
            functional_group_definitions_path=fg_path,
        )

        export_cfg = cfg.cohort_data_export

        assert export_cfg.enabled is False
        assert export_cfg.cohort_attributes == ()
        assert export_cfg.float_format == "%0.5f"

    def test_override_export_config_at_initialisation(self, tmp_path):
        """Test cohort_data_export can be overridden at initialisation.

        Ensures that providing a custom AnimalExportConfig instance is respected
        and not replaced by the default factory.
        """
        from pathlib import Path

        from virtual_ecosystem.models.animal.model_config import (
            AnimalConfiguration,
            AnimalExportConfig,
        )

        fg_path = Path(tmp_path / "functional_groups.csv")
        fg_path.touch()

        custom_export = AnimalExportConfig(
            enabled=True,
            cohort_attributes=("cell_id",),
            float_format="%0.4f",
        )

        cfg = AnimalConfiguration(
            functional_group_definitions_path=fg_path,
            cohort_data_export=custom_export,
        )

        assert cfg.cohort_data_export is custom_export
        assert cfg.cohort_data_export.enabled is True
        assert cfg.cohort_data_export.cohort_attributes == ("cell_id",)
        assert cfg.cohort_data_export.float_format == "%0.4f"

    def test_serialisation_round_trip(self, tmp_path):
        """Test AnimalConfiguration serialises and deserialises correctly.

        Ensures that nested AnimalConstants and AnimalExportConfig are preserved
        across a JSON round trip.
        """
        from pathlib import Path

        from virtual_ecosystem.models.animal.model_config import (
            AnimalConfiguration,
            AnimalExportConfig,
        )

        fg_path = Path(tmp_path / "functional_groups.csv")
        fg_path.touch()

        cfg = AnimalConfiguration(
            functional_group_definitions_path=fg_path,
            cohort_data_export=AnimalExportConfig(
                enabled=True,
                cohort_attributes=("cell_id", "time"),
                float_format="%0.2f",
            ),
        )

        json_str = cfg.model_dump_json()
        restored = AnimalConfiguration.model_validate_json(json_str)

        assert restored == cfg
