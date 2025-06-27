"""The exporter module provides the CommunityDataExporter, which is used to control the
output of plant community data at each time step.

TODO - Why not the data object?
"""  # noqa: D205

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.models.plants.communities import PlantCommunities


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
        self._output_mode: str = "w"
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
                raise ConfigurationError(
                    f"The {arg} exporter path must not be an existing file: {fname}"
                )

            if not (fname.parent.exists() and os.access(fname.parent, os.W_OK)):
                raise ConfigurationError(
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

    def dump(
        self, communities: PlantCommunities, canopies, time: np.datetime64
    ) -> None:
        """Dump community data to the configured files."""

        # TODO - check the export attributes. These probably are checked dynamically
        #        against object attributes, so need to be delayed until those objects
        #        are provided to dump. Unless we can import and interrogate the class
        #        objects themselves and not instances

        if not self.active:
            return

        # Compile cohort data - collect per cell pandas dataframes into an list for use
        # with row-wise pd.concat()
        cohort_data = []

        for cell_id, community in communities.items():
            # Concatenate the cohort data with the stem allometry by column
            community_data = pd.concat(
                [
                    community.cohorts.to_pandas(),
                    community.stem_allometry.to_pandas(),
                ],
                axis=1,
            )
            # Add the cell id and append
            community_data["cell_id"] = cell_id

            cohort_data.append(community_data)

        # Concatenate the cells by row and add time
        cohort_data_compiled = pd.concat(cohort_data)
        cohort_data_compiled["time"] = time

        # Reduce to requested attributes
        if self.cohort_attributes:
            # Check that all requested attributes are present in the compiled data
            not_found = [
                col for col in self.cohort_attributes if col not in cohort_data_compiled
            ]
            if not_found:
                raise ConfigurationError(
                    f"The cohort_attributes exporter configuration contains "
                    f"unknown columns: {', '.join(not_found)}"
                )
            # Subset compiled data
            cohort_data_compiled = cohort_data_compiled[self.cohort_attributes]

        # Export cohort data - this switches from write mode with headers to append mode
        # without headers after the first call to dump.
        cohort_data_compiled.to_csv(
            self.cohort_data_path,
            mode=self._output_mode,
            header=self._output_mode == "w",
            index=False,
            float_format="%0.5g",  # TODO - make this configurable
        )

        # TODO - actual layer data
        with open(self.layer_data_path, "a") as layer_out:
            layer_out.write("World")

        # Update the output mode, so that all subsequent dump calls use append
        self._output_mode = "a"
