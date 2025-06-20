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
        cohort_data_path: Path | None,
        layer_data_path: Path | None,
        cohort_attributes: tuple[str, ...],
        canopy_attributes: tuple[str, ...],
    ) -> None:
        # Set the class attributes
        self.cohort_data_path: Path | None = cohort_data_path
        """Attribute."""
        self.layer_data_path: Path | None = layer_data_path
        """Attribute."""
        self.cohort_attributes: tuple[str, ...] = cohort_attributes
        """Attribute."""
        self.canopy_attributes: tuple[str, ...] = canopy_attributes
        """Attribute."""
        self.active: bool = True
        """Attribute."""

        # Is the exporter active - at least one of the paths is defined
        if self.cohort_data_path is None and self.layer_data_path is None:
            self.active = False
            return

        # TODO - check the paths do not exist but are writeable.
        # TODO - check the export attributes.

    @classmethod
    def from_config(cls, config: Config) -> CommunityDataExporter:
        """Factory class to create a CommunityDataExporter from a configuration."""

        exporter_config = config["plants"]["community_data_export"]

        return cls(
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
