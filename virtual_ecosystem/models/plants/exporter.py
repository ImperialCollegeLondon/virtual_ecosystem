"""The exporter module provides the CommunityDataExporter, which is used to control the
output of plant community data at each time step.

TODO - Why not the data object?
"""  # noqa: D205

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from pyrealm.demography.canopy import Canopy, CohortCanopyData, CommunityCanopyData
from pyrealm.demography.community import Cohorts
from pyrealm.demography.tmodel import StemAllocation, StemAllometry

from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.communities import PlantCommunities


class CommunityDataExporter:
    """The CommunityDataExporter class.

    An instance of this class can be configured to write detailed plant community data
    from inside a PlantsModel instance to CSV files. The community data is split across
    three output files:

    * cohort data: details about each cohort, including the stem
      allometry of cohorts and the GPP allocation of the stem.
    * community canopy data: community wide data on the canopy
      structure, such as the heights of the canopy layers and the light transmission.
    * stem canopy data: details of contribution in leaf area and fAPAR from each stem to
      the community canopy model.

    To output a particular data type, a valid path needs to be provided: this must be to
    a new, writeable filepath. If the data path is set to None, then that data file will
    not be saved. In addition, the attribute sets can be used to specify a subset of
    data attributes to be exported in each file. If an empty attribute set is provided
    (which is the default) then the exporter will write all attributes.

    Args:
        cohort_data_path: Output path for cohort data
        community_canopy_data_path: Output path for community level canopy data
        stem_canopy_data_path: Output path for stem level canopy data
        cohort_attributes: An optional subset of cohort attributes to export
        community_canopy_attributes: An optional subset of community canopy attributes
            to export
        stem_canopy_attributes: An optional subset of stem canopy attributes
            to export
        active: A logical switch to turn exporting on or off.
    """

    def __init__(
        self,
        cohort_data_path: Path | None,
        community_canopy_data_path: Path | None,
        stem_canopy_data_path: Path | None,
        cohort_attributes: set[str] = set(),
        community_canopy_attributes: set[str] = set(),
        stem_canopy_attributes: set[str] = set(),
        active: bool = False,
    ) -> None:
        self.active: bool = active
        """Sets if the exporter is actually active."""

        # Set the path attributes
        self.cohort_data_path: Path | None = cohort_data_path
        """The output path for cohort level data."""
        self.community_canopy_data_path: Path | None = community_canopy_data_path
        """The output path for community canopy data."""
        self.stem_canopy_data_path: Path | None = stem_canopy_data_path
        """The output path for stem canopy data."""

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

        self.cohort_attributes: set[str] = cohort_attributes
        """A subset of cohort attribute names to export."""
        self.community_canopy_attributes: set[str] = community_canopy_attributes
        """A subset of community canopy attribute names to export."""
        self.stem_canopy_attributes: set[str] = stem_canopy_attributes
        """A subset of community canopy attribute names to export."""

        if self.active:
            self._check_attribute_subsets()
            LOGGER.info("Plant community data exporter active.")

    def _check_paths(self) -> None:
        """Check paths do not exist and are in existing writeable locations."""

        for arg, fname in (
            ("cohort_data_path", self.cohort_data_path),
            ("community_canopy_data_path", self.community_canopy_data_path),
            ("stem_canopy_data_path", self.stem_canopy_data_path),
        ):
            if fname is None:
                continue

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

        available_attributes = {
            "cohort_attributes": set(
                [
                    "cell_id",
                    "time",
                    *StemAllometry.array_attrs,
                    *Cohorts.array_attrs,
                    StemAllocation.array_attrs,
                ]
            ),
            "community_canopy_attributes": set(
                [
                    "canopy_layer_index",
                    "heights",
                    "cell_id",
                    "time",
                    *CommunityCanopyData.array_attrs,
                ]
            ),
            "stem_canopy_attributes": set(
                [
                    "canopy_layer_index",
                    "cohort_id",
                    "cell_id",
                    "time",
                    *CohortCanopyData.array_attrs,
                ]
            ),
        }

        for subset_name, available in available_attributes.items():
            subset = getattr(self, subset_name)
            # If subset is provided, check the values are all valid
            if not subset:
                continue

            not_found = subset.difference(available)
            if not_found:
                msg = (
                    f"The {subset_name} exporter configuration contains "
                    f"unknown attributes: {', '.join(not_found)}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

    @classmethod
    def from_config(cls, config: Config) -> CommunityDataExporter:
        """Factory class to create a CommunityDataExporter from a configuration.

        The configuration requires that the following details are present in the plants
        model section of the configuration

        .. code-block:: toml

            [plants.community_data_export]
            active = true
            cohort_data_path = "path/to/cohort_data.csv"
            community_canopy_data_path = "path/to/community_canopy_data.csv"
            stem_canopy_data_path = "path/to/stem_canopy_data.csv"
            cohort_attributes = []
            community_canopy_attributes = []
            stem_canopy_attributes = []

        If the "attributes" sections are empty arrays, then all attributes are written
        to file, but specific fields may be named here to reduce the amount of data
        exported.
        """

        # Try and build the arguments as a dictionary from the config, substituting
        # explicit None values for empty strings
        try:
            cfg = config["plants"]["community_data_export"]

            # Convert path strings to Path or None
            if cfg["cohort_data_path"]:
                cohort_data_path = Path(cfg["cohort_data_path"])
            else:
                cohort_data_path = None

            if cfg["community_canopy_data_path"]:
                community_canopy_data_path = Path(cfg["community_canopy_data_path"])
            else:
                community_canopy_data_path = None

            if cfg["stem_canopy_data_path"]:
                stem_canopy_data_path = Path(cfg["stem_canopy_data_path"])
            else:
                stem_canopy_data_path = None

            args = dict(
                active=cfg["active"],
                cohort_data_path=cohort_data_path,
                community_canopy_data_path=community_canopy_data_path,
                stem_canopy_data_path=stem_canopy_data_path,
                cohort_attributes=set(cfg["cohort_attributes"]),
                community_canopy_attributes=set(cfg["community_canopy_attributes"]),
                stem_canopy_attributes=set(cfg["stem_canopy_attributes"]),
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
        """Export plant community data to file.

        The method accepts the main community components of the PlantsModel as arguments
        and compiles the configured cohort and canopy data to write to file.

        Args:
            communities: A PlantCommunities instance.
            canopies: A dictionary of Canopy instances, keyed by cell id.
            stem_allocations: A dictionary of StemAllocations, also keyed by cell id
            time: A datetime to be used as a timestamp in the output files.
        """

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
            if self.cohort_attributes:
                cohort_data_compiled = cohort_data_compiled[
                    list(self.cohort_attributes)
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

        # Export community level canopy canopy data if requested
        if self.community_canopy_data_path:
            community_canopy_data = []
            for cell_id, canopy in canopies.items():
                data = canopy.community_data.to_pandas()
                data["canopy_layer_index"] = data.index
                data["heights"] = canopy.heights
                data["cell_id"] = cell_id
                data["time"] = time
                community_canopy_data.append(data)

            # Concatenate the cells into a single data frame
            community_canopy_data_compiled = pd.concat(community_canopy_data)

            # Reduce to requested attributes
            if self.community_canopy_attributes:
                community_canopy_data_compiled = community_canopy_data_compiled[
                    list(self.community_canopy_attributes)
                ]

            # Export community canopy data
            community_canopy_data_compiled.to_csv(
                self.community_canopy_data_path,
                mode=self._output_mode,
                header=self._output_mode == "w",
                index=False,
                float_format="%0.5g",  # TODO - make this configurable
            )
            LOGGER.info(f"Plant model community canopy data dumped at time: {time}")

        if self.stem_canopy_data_path:
            stem_canopy_data = []
            for (cell_id, canopy), community in zip(
                canopies.items(), communities.values()
            ):
                data = canopy.cohort_data.to_pandas()
                data["canopy_layer_index"] = data.index
                data["cell_id"] = cell_id
                data["cohort_id"] = np.repeat(
                    community.cohorts.cohort_id, len(canopy.heights)
                )
                data["time"] = time
                stem_canopy_data.append(data)

            # Concatenate the cells into a single data frame
            stem_canopy_data_compiled = pd.concat(stem_canopy_data)

            # Reduce to requested attributes
            if self.stem_canopy_attributes:
                stem_canopy_data_compiled = stem_canopy_data_compiled[
                    list(self.stem_canopy_attributes)
                ]

            # Export stem canopy data
            stem_canopy_data_compiled.to_csv(
                self.stem_canopy_data_path,
                mode=self._output_mode,
                header=self._output_mode == "w",
                index=False,
                float_format="%0.5g",  # TODO - make this configurable
            )
            LOGGER.info(f"Plant model stem canopy data dumped at time: {time}")

        # Update the output mode, so that all subsequent dump calls use append
        self._output_mode = "a"
