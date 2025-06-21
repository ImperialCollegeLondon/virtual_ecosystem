"""The exporter module provides the CommunityDataExporter, which is used to control the
output of plant community data at each time step.

TODO - Why not the data object?
"""  # noqa: D205

from __future__ import annotations

from pathlib import Path

from virtual_ecosystem.core.config import Config


class CommunityDataExporter:
    """CommunityDataExporter."""

    def __init__(
        self,
        cohort_data_path: Path,
        layer_data_path: Path,
        cohort_attributes: tuple[str, ...],
        canopy_attributes: tuple[str, ...],
        active: bool = False,
    ) -> None:
        # Set the class attributes
        self.cohort_data_path: Path = cohort_data_path
        """Attribute."""
        self.layer_data_path: Path = layer_data_path
        """Attribute."""
        self.cohort_attributes: tuple[str, ...] = cohort_attributes
        """Attribute."""
        self.canopy_attributes: tuple[str, ...] = canopy_attributes
        """Attribute."""
        self.active: bool = active
        """Attribute."""

        if self.active:
            self._check_configuration()

    def _check_configuration(self):
        """Check the configured settings."""

        # TODO - check the paths do not exist but are writeable.
        # TODO - check the export attributes.
        pass

    @classmethod
    def from_config(cls, config: Config) -> CommunityDataExporter:
        """Factory class to create a CommunityDataExporter from a configuration."""

        exporter_config = config["plants"]["community_data_export"]

        return cls(
            active=exporter_config["active"],
            cohort_data_path=exporter_config["cohort_data_path"],
            layer_data_path=exporter_config["layer_data_path"],
            cohort_attributes=exporter_config["cohort_attributes"],
            canopy_attributes=exporter_config["canopy_attributes"],
        )

    def dump(self, communities, canopies) -> None:
        """Dump community data to the configured files."""

        if not self.active:
            return

        pass
