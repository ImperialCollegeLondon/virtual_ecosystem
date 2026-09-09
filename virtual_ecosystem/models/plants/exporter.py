"""The exporter module provides the CommunityDataExporter, which is used to control the
output of plant community data at each time step. An instance of the class is required
by the PlantsModel, which calls the ``dump()`` method within the setup and update steps
to export data continuously during the model run.

The exporter can be configured to write three different levels of data: cohort level
data and canopy structure data at both the community and individual stem levels. The
data being exported is best structured as data frames and is highly ragged across cells,
so is less well suited for export through the central data object.
"""  # noqa: D205

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import ClassVar, Literal

import numpy as np
import pandas as pd
from pyrealm.demography.canopy import Canopy, CohortCanopyData, CommunityCanopyData
from pyrealm.demography.tmodel import GrowthIncrements, StemAllocation, StemAllometry

from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.biomasses import PLANT_BIOMASS_TISSUES, Biomasses
from virtual_ecosystem.models.plants.communities import PlantCommunities
from virtual_ecosystem.models.plants.functional_types import VEFloraValidator
from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

# Global definition of ALL keyword
ALL = Literal["ALL"]


class CommunityDataExporter:
    """The CommunityDataExporter class.

    The class is used to export detailed plant community data from inside a PlantsModel
    instance to CSV files. The community data is split across three output types, which
    are written to standard file names in the provided output directory.

    * cohort data ("plants_cohort_data.csv"): details about the stems in each cohort,
      including the stem allometry and the GPP allocation of the stem. The stem GPP
      allocation is not defined during the model setup, so these attributes are set to
      ``np.nan`` for the initial output.
    * community canopy data ("plants_community_canopy_data.csv"): community wide data on
      the canopy structure, such as the heights of the canopy layers and the light
      transmission profile.
    * stem canopy data ("plants_stem_canopy_data.csv"): details of contribution in leaf
      area and fAPAR from each stem to the community canopy model.

    The attribute arguments control which data attributes to be exported for each output
    type. The default (an empty set) turns off data export for that output type,
    otherwise the set should provide a set of the required output attributes. As a
    shortcut for including all available attributes, the keyword "ALL" can be provided
    as a string instead of a set of attribute names.

    Args:
        output_directory: The output directory for the files
        cohort_attributes: An set of cohort attributes to export or the ALL keyword.
        community_canopy_attributes: A set of community canopy attributes to export or
            the ALL keyword.
        stem_canopy_attributes: An set of stem canopy attributes to export or the ALL
            keyword.
        float_format: A float format string used when writing numeric data.
    """

    _output_files: ClassVar[dict[str, str]] = dict(
        cohort="plants_cohort_data.csv",
        community_canopy="plants_community_canopy_data.csv",
        stem_canopy="plants_stem_canopy_data.csv",
    )
    """Class variable storing the output filenames for each data type."""

    _mandatory_attributes: ClassVar[dict[str, set[str]]] = dict(
        cohort_attributes=set(["cohort_id", "cell_id", "time", "time_index"]),
        community_canopy_attributes=set(
            [
                "cell_id",
                "time",
                "time_index",
                "canopy_layer_index",
                "heights",
            ]
        ),
        stem_canopy_attributes=set(
            [
                "cohort_id",
                "cell_id",
                "time",
                "time_index",
                "canopy_layer_index",
                "heights",
            ]
        ),
    )

    def __init__(
        self,
        output_directory: Path,
        cohort_attributes: ALL | set[str] = set(),
        community_canopy_attributes: ALL | set[str] = set(),
        stem_canopy_attributes: ALL | set[str] = set(),
        float_format: str = "%0.5f",
    ) -> None:
        # Store the argument values
        self.output_directory: Path = output_directory
        """The directory in which to save plant community data."""
        self.float_format = float_format
        """The float format for data export."""

        # Set the attribute export options
        self.cohort_attributes: ALL | set[str] = cohort_attributes
        """The set of cohort attribute names to export."""
        self.community_canopy_attributes: ALL | set[str] = community_canopy_attributes
        """The set of community canopy attribute names to export."""
        self.stem_canopy_attributes: ALL | set[str] = stem_canopy_attributes
        """The subset of community canopy attribute names to export."""

        # Populate the available attributes - this is awkward for cohorts because there
        # isn't a single common API for getting at the available attributes. Some
        # objects have _array_attrs but not cohorts or biomasses.
        # - Cohorts is a dataframe that include cohort details and PFT traits
        # - Biomasses exports a dataframe with elemental masses for lots of tisses.
        #   Biomass instances provide the .to_dataframe() method which gives the
        #   available attributes but adding biomasses to __init__ just to get names is
        #   is clumsy.

        biomass_attributes = [
            f"{tissue}_{elem}_biomass"
            for tissue, elem in product(
                [*[t.tissue_name for t in PLANT_BIOMASS_TISSUES], "surplus"],
                ["C", *PLANT_BIOMASS_TISSUES[0].elements],
            )
        ]

        self.available_attributes: dict[str, set[str]] = {
            "cohort_attributes": set(
                [
                    *self._mandatory_attributes["cohort_attributes"],
                    # Cohorts is a dataframe and does not have _array_attrs but is three
                    # cohort fields and then PFT traits can be extracted from trait
                    # model.
                    "pft_name",
                    "dbh_value",
                    "n_individuals",
                    *VEFloraValidator.model_fields,
                    *VEFloraValidator.model_computed_fields,
                    # Biomass attributes
                    *biomass_attributes,
                    # Other inputs have defined _array_attrs
                    *StemAllometry._array_attrs,
                    *StemAllocation._array_attrs,
                    *GrowthIncrements._array_attrs,
                ]
            ),
            "community_canopy_attributes": set(
                [
                    *self._mandatory_attributes["community_canopy_attributes"],
                    *CommunityCanopyData._array_attrs,
                ]
            ),
            "stem_canopy_attributes": set(
                [
                    *self._mandatory_attributes["stem_canopy_attributes"],
                    *CohortCanopyData._array_attrs,
                ]
            ),
        }
        """Class variable of the available attributes that can be exported for each 
        export option."""

        # Type and set internal attributes
        self._output_mode: str = "w"
        """Switches the exporter between write and append mode."""
        self._write_header: bool = True
        """Stops headers being duplicated in append mode."""

        # Use truthiness of settings to test if _all_ are empty sets or at least one is
        # ALL or a non-empty set.
        self._active: bool = bool(
            self.cohort_attributes
            or self.stem_canopy_attributes
            or self.community_canopy_attributes
        )
        """Has any data export has been requested."""

        # Define private data output path attributes
        self._cohort_path: Path
        self._community_canopy_path: Path
        self._stem_canopy_path: Path

        self._check_and_set_paths()

        # If no output data is requested then set the exporter in the inactive state
        # and return the instance.
        if not self._active:
            LOGGER.info("Plant community data exporter not active.")
            return

        # Check the attributes subsets
        self._check_attribute_subsets()
        LOGGER.info("Plant community data exporter active.")

    def _check_and_set_paths(self) -> None:
        """Check and set the output paths to be used by the exporter.

        This method localises the output file path for each output data type to the
        provided output directory.
        """

        # Check the output directory
        if not (self.output_directory.exists() and self.output_directory.is_dir()):
            msg = (
                f"The plant community data output directory does not exist or is not "
                f"a directory: {self.output_directory}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        for attr, path in self._output_files.items():
            # Localise the path
            data_path = self.output_directory / path
            # Check if any attributes are written for this output and - if so - check no
            # existing data will be overwritten.
            if getattr(self, f"{attr}_attributes") and data_path.exists():
                msg = (
                    f"An output file for plant data export already exists: {data_path}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

            # Set the path attribute to the output path.
            setattr(self, f"_{attr}_path", data_path)

    def _check_attribute_subsets(self) -> None:
        """Check attribute subsets contain available fields."""

        for subset_name, available in self.available_attributes.items():
            subset = getattr(self, subset_name)

            # Skip validation if the set is empty or the ALL keyword.
            if (subset == "ALL") or (not subset):
                continue

            not_found = subset.difference(available)
            if not_found:
                msg = (
                    f"The {subset_name} exporter configuration contains "
                    f"unknown attributes: {', '.join(not_found)}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

            # Enforce the mandatory fields
            setattr(
                self, subset_name, self._mandatory_attributes[subset_name].union(subset)
            )

    @classmethod
    def from_config(
        cls, output_directory: Path, config: PlantsExportConfig
    ) -> CommunityDataExporter:
        """Factory class to create a CommunityDataExporter from configuration data.

        See the documentation of
        :class:`~virtual_ecosystem.models.plants.model_config.PlantsExportConfig`
        for details of the configuration settings for this method.

        Args:
            output_directory: The path to the output directory for the files
            config: An instance of ``PlantsExportConfig``

        """

        # Convert lists to sets and get the instance
        return cls(
            output_directory=output_directory,
            cohort_attributes="ALL"
            if config.cohort_attributes == "ALL"
            else set(config.cohort_attributes),
            community_canopy_attributes="ALL"
            if config.community_canopy_attributes == "ALL"
            else set(config.community_canopy_attributes),
            stem_canopy_attributes="ALL"
            if config.stem_canopy_attributes == "ALL"
            else set(config.stem_canopy_attributes),
        )

    def dump(
        self,
        communities: PlantCommunities,
        biomasses: dict[int, Biomasses],
        canopies: dict[int, Canopy],
        stem_allocations: dict[int, StemAllocation],
        growth_increments: dict[int, GrowthIncrements],
        time: np.datetime64,
        time_index: int,
    ) -> None:
        """Export plant community data to file.

        The method accepts the main community components of the PlantsModel as arguments
        and compiles and writes the output data requested in the instance setup to file.

        Args:
            communities: A PlantCommunities instance.
            biomasses: A dictionary of biomass data keyed by cell id.
            canopies: A dictionary of Canopy instances, keyed by cell id.
            stem_allocations: A dictionary of StemAllocations, also keyed by cell id
            growth_increments: A dictionary of GrowthIncrements, also keyed by cell id
            time: A datetime to be used as a timestamp in the output files.
            time_index: The index of the datatime within the model updates.
        """

        if not self._active:
            return

        # Run the dump methods for each output option.
        self._dump_cohort_data(
            communities=communities,
            biomasses=biomasses,
            stem_allocations=stem_allocations,
            growth_increments=growth_increments,
            time=time,
            time_index=time_index,
        )
        self._dump_community_canopy_data(
            canopies=canopies,
            time=time,
            time_index=time_index,
        )
        self._dump_stem_canopy_data(
            communities=communities,
            canopies=canopies,
            time=time,
            time_index=time_index,
        )

        # Update the output mode and header: all subsequent dump calls use append
        self._output_mode = "a"
        self._write_header = False

    def _dump_cohort_data(
        self,
        communities: PlantCommunities,
        biomasses: dict[int, Biomasses],
        stem_allocations: dict[int, StemAllocation],
        growth_increments: dict[int, GrowthIncrements],
        time: np.datetime64,
        time_index: int,
    ) -> None:
        """Dump plant cohort data to file.

        Args:
            communities: A PlantCommunities instance.
            biomasses: A dictionary of biomass data keyed by cell id.
            stem_allocations: A dictionary of StemAllocations, also keyed by cell id
            growth_increments: A dictionary of GrowthIncrements, also keyed by cell id
            time: A datetime to be used as a timestamp in the output files
            time_index: The index of the datatime within the model updates.
        """

        # If data has not been requested then exit immediately
        if not self.cohort_attributes:
            return

        # Collect cell dataframes into an list for use with row-wise pd.concat()
        cohort_data = []

        for cell_id, community in communities.items():
            # The stem allocations and growth increments are only populated during model
            # update so at setup are empty dictionaries. During the setup export, these
            # values are exported as dataframes of np.nan
            if stem_allocations:
                allocation = stem_allocations[cell_id].to_dataframe()
            else:
                # Empty dataframe of NaN values
                allocation = pd.DataFrame(
                    columns=StemAllocation._array_attrs,
                    index=np.arange(len(community.cohorts)),
                )

            if growth_increments:
                increments = growth_increments[cell_id].to_dataframe()
            else:
                # Empty dataframe of NaN values
                increments = pd.DataFrame(
                    columns=GrowthIncrements._array_attrs,
                    index=np.arange(len(community.cohorts)),
                )

            # Create a list of the various dataframes, starting with the key shared
            # information across all data
            frames = [
                pd.DataFrame(
                    dict(
                        cell_id=cell_id,
                        cohort_id=community.cohorts["cohort_id"],
                        time=time,
                        time_index=time_index,
                    )
                )
            ]

            # Append each of the other dataframes, dropping the repeated cohort_id field
            # and resetting the index to ensure column-wise concatenation works.
            for df in [
                community.cohorts,
                community.stem_allometry.to_dataframe(),
                allocation,
                increments,
                biomasses[cell_id].to_dataframe(),
            ]:
                frames.append(df.drop(columns="cohort_id").reset_index(drop=True))

            # Simply join frames along the rows
            community_data = pd.concat(frames, axis=1)

            cohort_data.append(community_data)

        # Concatenate the cells by row
        cohort_data_compiled = pd.concat(cohort_data)

        # If cohort attributes is a subset then reduce
        if self.cohort_attributes != "ALL":
            cohort_data_compiled = cohort_data_compiled[list(self.cohort_attributes)]

        # Export cohort data - this switches from write mode with headers to append
        # mode without headers after the first call to dump.
        cohort_data_compiled.to_csv(
            self._cohort_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )
        LOGGER.info(f"Plant model cohort data dumped at time: {time}")

    def _dump_community_canopy_data(
        self,
        canopies: dict[int, Canopy],
        time: np.datetime64,
        time_index: int,
    ):
        """Dump community canopy data to file.

        Args:
            canopies: A dictionary of Canopy instances, keyed by cell id.
            time: A datetime to be used as a timestamp in the output files
            time_index: The index of the datatime within the model updates.
        """
        # If data has not been requested then exit immediately
        if not self.community_canopy_attributes:
            return

        community_canopy_data = []
        for cell_id, canopy in canopies.items():
            data = canopy.community_data.to_dataframe()
            full_data = pd.DataFrame(
                dict(
                    cell_id=cell_id,
                    time=time,
                    time_index=time_index,
                    canopy_layer_index=data.index,
                    heights=canopy.heights,
                    **data,
                )
            )

            community_canopy_data.append(full_data)

        # Concatenate the cells into a single data frame
        community_canopy_data_compiled = pd.concat(community_canopy_data)

        # Reduce to requested attributes
        if self.community_canopy_attributes != "ALL":
            community_canopy_data_compiled = community_canopy_data_compiled[
                list(self.community_canopy_attributes)
            ]

        # Export community canopy data
        community_canopy_data_compiled.to_csv(
            self._community_canopy_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )
        LOGGER.info(f"Plant model community canopy data dumped at time: {time}")

    def _dump_stem_canopy_data(
        self,
        communities: PlantCommunities,
        canopies: dict[int, Canopy],
        time: np.datetime64,
        time_index: int,
    ) -> None:
        """Dump stem canopy data to file.

        Args:
            communities: A PlantCommunities instance.
            canopies: A dictionary of Canopy instances, keyed by cell id.
            time: A datetime to be used as a timestamp in the output files
            time_index: The index of the datatime within the model updates.
        """
        # If data has not been requested then exit immediately
        if not self.stem_canopy_attributes:
            return

        stem_canopy_data = []
        for (cell_id, canopy), community in zip(canopies.items(), communities.values()):
            data = canopy.cohort_data.to_dataframe()
            n_heights = len(canopy.heights)
            full_data = pd.DataFrame(
                dict(
                    cohort_id=np.tile(community.cohorts.cohort_id, n_heights),
                    cell_id=cell_id,
                    time=time,
                    time_index=time_index,
                    canopy_layer_index=np.repeat(
                        np.arange(n_heights), canopy.n_cohorts
                    ),
                    heights=np.repeat(canopy.heights, canopy.n_cohorts),
                    **data,
                )
            )
            stem_canopy_data.append(full_data)

        # Concatenate the cells into a single data frame
        stem_canopy_data_compiled = pd.concat(stem_canopy_data)

        # Reduce to requested attributes
        if self.stem_canopy_attributes != "ALL":
            stem_canopy_data_compiled = stem_canopy_data_compiled[
                list(self.stem_canopy_attributes)
            ]

        # Export stem canopy data
        stem_canopy_data_compiled.to_csv(
            self._stem_canopy_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )
        LOGGER.info(f"Plant model stem canopy data dumped at time: {time}")
