"""The exporter module provides the CommunityDataExporter, which is used to control the
output of plant community data at each time step.

TODO - Why not the data object?
"""  # noqa: D205

from __future__ import annotations

import os
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
        # Set the path attributes but only do any validation if the exporter is actually
        # active
        self.cohort_data_path: Path = cohort_data_path
        """Attribute."""
        self.layer_data_path: Path = layer_data_path
        """Attribute."""

        # Need to validate these but maybe delay until first dump and interogate
        # instances rather than hardcoding allowable attributes in __init__.
        self.cohort_attributes: tuple[str, ...] = cohort_attributes
        """Attribute."""
        self.canopy_attributes: tuple[str, ...] = canopy_attributes
        """Attribute."""

        self.active: bool = active
        """Attribute."""

        if self.active:
            self._check_paths()

    def _check_paths(self) -> None:
        """Check paths do not exist and are in existing writeable locations."""

        for arg, fname in (
            ("cohort_data_path", self.cohort_data_path),
            ("layer_data_path", self.layer_data_path),
        ):
            if fname.exists():
                raise ValueError(
                    f"The {arg} exporter path must not be an existing file: {fname}"
                )

            if not (fname.parent.exists() and os.access(fname.parent, os.W_OK)):
                raise ValueError(
                    f"The {arg} exporter path must be in an existing "
                    f"writeable directory: {fname}"
                )

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

        # TODO - check the export attributes. These probably are checked dynamically
        #        against object attributes, so need to be delayed until those objects
        #        are provided to dump. Unless we can import and interrogate the class
        #        objects themselves and not instances

        if not self.active:
            return

        with open(self.cohort_data_path, "a") as cohort_out:
            cohort_out.write("Hello")

        with open(self.layer_data_path, "a") as layer_out:
            layer_out.write("World")
