"""The exporter module provides the CommunityDataExporter, which is used to control the
output of plant community data at each time step.

TODO - Why not the data object?
"""  # noqa: D205

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from pyrealm.demography.canopy import Canopy
from pyrealm.demography.community import Cohorts
from pyrealm.demography.tmodel import StemAllocation, StemAllometry

from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.communities import PlantCommunities


class CommunityDataExporter:
    """CommunityDataExporter.

    TODO - write docstring and add logging.
    """

    def __init__(
        self,
        cohort_data_path: Path,
        layer_data_path: Path,
        cohort_attribute_subset: set[str] = set(),
        canopy_attribute_subset: set[str] = set(),
        active: bool = False,
    ) -> None:
        self.active: bool = active
        """Sets if the exporter is actually active."""

        # Set the path attributes
        self.cohort_data_path: Path = cohort_data_path
        """The output path for cohort level data."""
        self.layer_data_path: Path = layer_data_path
        """The output path for layer level data."""

        # Only bother to validate paths if the exporter is actually active - avoids
        # trying to validate default empty strings.
        if self.active:
            self._check_paths()

        self._output_mode: str = "w"
        """Private attribute recording the write/append status of the exporter."""

        # Store the attribute subset arguments. Validation is delayed until the first
        # attempt to write - simpler to check against available variables and avoids the
        # need to tesNeed to validate these but maybe delay until first dump and
        # interogate
        # instances rather than hardcoding allowable attributes in __init__.

        self.cohort_attribute_subset: set[str] = cohort_attribute_subset
        """An optional list providing a subset of cohort attributes to export."""
        self.canopy_attribute_subset: set[str] = canopy_attribute_subset
        """An optional list providing a subset of layer attributes to export."""

        if self.active:
            self._check_attribute_subsets()
            LOGGER.info("Plant community data exporter active.")

    def _check_paths(self) -> None:
        """Check paths do not exist and are in existing writeable locations."""

        for arg, fname in (
            ("cohort_data_path", self.cohort_data_path),
            ("layer_data_path", self.layer_data_path),
        ):
            if fname.exists():
                msg = f"The {arg} exporter path must not be an existing file: {fname}"
                LOGGER.error(msg)
                raise ConfigurationError(msg)

            if not (fname.parent.exists() and os.access(fname.parent, os.W_OK)):
                msg = (
                    f"The {arg} exporter path must be in an existing "
                    f"writeable directory: {fname}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

    def _check_attribute_subsets(self) -> None:
        """Check attribute subsets contain available fields."""

        # If a cohort attribute subset is requested check they are all valid
        if self.cohort_attribute_subset:
            # Available attributes
            cohort_attributes = set(
                [
                    "cell_id",
                    *StemAllometry.array_attrs,
                    *Cohorts.array_attrs,
                    StemAllocation.array_attrs,
                ]
            )

            not_found = self.cohort_attribute_subset.difference(cohort_attributes)
            if not_found:
                msg = (
                    f"The cohort_attribute_subset exporter configuration contains "
                    f"unknown columns: {', '.join(not_found)}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

    @classmethod
    def from_config(cls, config: Config) -> CommunityDataExporter:
        """Factory class to create a CommunityDataExporter from a configuration."""

        # Try and build the arguments as a dictionary from the config
        try:
            exporter_config = config["plants"]["community_data_export"]
            args = dict(
                active=exporter_config["active"],
                cohort_data_path=exporter_config["cohort_data_path"],
                layer_data_path=exporter_config["layer_data_path"],
                cohort_attribute_subset=set(exporter_config["cohort_attribute_subset"]),
                canopy_attribute_subset=set(exporter_config["canopy_attribute_subset"]),
            )
        except KeyError as excep:
            LOGGER.error(excep)
            raise

        # Return the instance
        return cls(**args)

    def dump(
        self,
        communities: PlantCommunities,
        canopies: dict[int, Canopy],
        stem_allocations: dict[int, StemAllocation],
        time: np.datetime64,
    ) -> None:
        """Dump community data to the configured files."""

        if not self.active:
            return

        # Export cohort data if requested
        if self.cohort_data_path:
            # If a cohort data path is provided then compile cohort data - collect per
            # cell pandas dataframes into an list for use with row-wise pd.concat()
            cohort_data = []

            for cell_id, community in communities.items():
                # The stem allocations are only defined after update so at setup, the
                # stem allocations are defined as an empty dictionary. In this case,
                # provide an empty data frame of np.nan values for each cohort.
                if stem_allocations:
                    allocation = stem_allocations[cell_id].to_pandas()
                else:
                    allocation = pd.DataFrame(
                        {
                            key: np.full(community.n_cohorts, np.nan)
                            for key in StemAllocation.array_attrs
                        }
                    )

                # Concatenate the cohort data, stem allometry and stem allocation by
                # column
                community_data = pd.concat(
                    [
                        community.cohorts.to_pandas(),
                        community.stem_allometry.to_pandas(),
                        allocation,
                    ],
                    axis=1,
                )

                # Add the cell id and append the cohorts in this community to the list
                community_data["cell_id"] = cell_id
                cohort_data.append(community_data)

            # Concatenate the cells by row and add time
            cohort_data_compiled = pd.concat(cohort_data)
            cohort_data_compiled["time"] = time

            # Reduce to requested attributes
            if self.cohort_attribute_subset:
                cohort_data_compiled = cohort_data_compiled[
                    list(self.cohort_attribute_subset)
                ]

            # Export cohort data - this switches from write mode with headers to append
            # mode without headers after the first call to dump.
            cohort_data_compiled.to_csv(
                self.cohort_data_path,
                mode=self._output_mode,
                header=self._output_mode == "w",
                index=False,
                float_format="%0.5g",  # TODO - make this configurable
            )
            LOGGER.info(f"Plant model cohort data dumped at time: {time}")

        # Export community level canopy layer data if requested
        if self.layer_data_path:
            community_layer_data = []
            for cell_id, canopy in canopies.items():
                canopy_layer_data = canopy.community_data.to_pandas()
                canopy_layer_data["heights"] = canopy.heights
                canopy_layer_data["cell_id"] = cell_id
                community_layer_data.append(canopy_layer_data)

            # Concatenate the cells into a single data frame
            community_layer_data_compiled = pd.concat(community_layer_data)

            # Export community layer data
            community_layer_data_compiled.to_csv(
                self.layer_data_path,
                mode=self._output_mode,
                header=self._output_mode == "w",
                index=False,
                float_format="%0.5g",  # TODO - make this configurable
            )
            LOGGER.info(
                f"Plant model community canopy layer data dumped at time: {time}"
            )

        # Update the output mode, so that all subsequent dump calls use append
        self._output_mode = "a"
