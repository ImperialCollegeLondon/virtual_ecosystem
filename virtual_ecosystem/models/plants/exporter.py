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

from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd
from pyrealm.demography.canopy import Canopy, CohortCanopyData, CommunityCanopyData
from pyrealm.demography.community import Cohorts
from pyrealm.demography.tmodel import StemAllocation, StemAllometry

from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.communities import PlantCommunities
from virtual_ecosystem.models.plants.model_config import PlantsExportConfig


class CommunityDataExporter:
    """The CommunityDataExporter class.

    The class is used to export detailed plant community data from inside a PlantsModel
    instance to CSV files. The community data is split across three output files:

    * cohort data: details about the stems in each cohort, including the stem allometry
      and the GPP allocation of the stem. The stem GPP allocation is not defined during
      the model setup, so these attributes are set to ``np.nan`` for the initial output.
    * community canopy data: community wide data on the canopy structure, such as the
      heights of the canopy layers and the light transmission profile.
    * stem canopy data: details of contribution in leaf area and fAPAR from each stem to
      the community canopy model.

    The data are written to standard file names in the provided output directory, which
    will typically be the output directory used by the Virtual Ecosystem model run. The
    ``required_data`` attribute is used to set which data to export by providing a set
    of values from: ``cohorts``, ``community_canopy`` and ``stem_canopy``.

    In addition, the attribute arguments can be used to specify a subset of data
    attributes to be exported. If an empty attribute set is provided (which is the
    default) then the exporter will write all attributes, otherwise the exported data
    will be reduced to just the named attributes.

    Args:
        output_directory: The output directory for the files
        required_data: A set of the required data outputs.
        cohort_attributes: An optional subset of cohort attributes to export
        community_canopy_attributes: An optional subset of community canopy attributes
            to export
        stem_canopy_attributes: An optional subset of stem canopy attributes
            to export
        float_format: A float format string used when writing data.
    """

    _outputs: ClassVar[dict[str, tuple[str, str]]] = dict(
        cohorts=(
            "plants_cohort_data.csv",
            "_cohort_path",
        ),
        community_canopy=(
            "plants_community_canopy_data.csv",
            "_community_canopy_path",
        ),
        stem_canopy=(
            "plants_stem_canopy_data.csv",
            "_stem_canopy_path",
        ),
    )
    """Connects the export data options to a tuple of standard output file and 
    internal path attribute names."""

    available_attributes: ClassVar[dict[str, set[str]]] = {
        "cohort_attributes": set(
            [
                "cell_id",
                "time",
                *StemAllometry.array_attrs,
                *Cohorts.array_attrs,
                *StemAllocation.array_attrs,
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
    """Class variable of the available attributes that can be exported for each export
    option."""

    def __init__(
        self,
        output_directory: Path,
        required_data: set[str] = set(),
        cohort_attributes: set[str] = set(),
        community_canopy_attributes: set[str] = set(),
        stem_canopy_attributes: set[str] = set(),
        float_format: str = "%0.5f",
    ) -> None:
        # Store the argument values
        self.output_directory: Path = output_directory
        """The directory in which to save plant community data."""
        self.required_data: set[str] = required_data
        """The set of plant community data types to be exported."""
        self.cohort_attributes: set[str] = cohort_attributes
        """A subset of cohort attribute names to export."""
        self.community_canopy_attributes: set[str] = community_canopy_attributes
        """A subset of community canopy attribute names to export."""
        self.stem_canopy_attributes: set[str] = stem_canopy_attributes
        """A subset of community canopy attribute names to export."""
        self.float_format = float_format
        """The float format for data export."""

        # Type and set internal attributes
        self._output_mode: str = "w"
        """Switches the exporter between write and append mode."""
        self._write_header: bool = True
        """Stops headers being duplicated in append mode."""
        self._active: bool = True
        """Has any data export has been requested."""

        # Initialise private data output path attributes - if set in required data,
        # these are updated to provide a checked path for requested data
        self._cohort_path: Path | None = None
        self._community_canopy_path: Path | None = None
        self._stem_canopy_path: Path | None = None

        # Validate the required data argument
        unknown_options = required_data.difference(self._outputs.keys())
        if unknown_options:
            msg = (
                f"The required_data setting contains unknown data "
                f"output options: {', '.join(unknown_options)}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        # If no output files are required then set the exporter in the inactive state
        # and return the instance.
        if not self.required_data:
            self._active = False
            LOGGER.info("Plant community data exporter not active.")
            return

        self._check_and_set_paths()
        self._check_attribute_subsets()
        LOGGER.info("Plant community data exporter active.")

    def _check_and_set_paths(self) -> None:
        """Check and set the output paths to be used by the exporter.

        This method assumes that the output directory has already been checked. It sets
        the internal path attributes for each output data type as either None (to signal
        it should not be written) or to a validated output path.
        """

        # Otherwise check no data will be overwritten and export.

        if not (self.output_directory.exists() and self.output_directory.is_dir()):
            msg = (
                f"The plant community data output directory does not exist or is not "
                f"a directory: {self.output_directory}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        for out_option, (fname, attr) in self._outputs.items():
            # Leave the path attribute at initial None value
            if out_option not in self.required_data:
                continue

            # Otherwise check no data will be overwritten and export.
            data_path = self.output_directory / fname
            if data_path.exists():
                msg = f"An output file for {out_option} data already exists: {fname}"
                LOGGER.error(msg)
                raise ConfigurationError(msg)

            # Set the path attribute to the output path.
            setattr(self, attr, data_path)

    def _check_attribute_subsets(self) -> None:
        """Check attribute subsets contain available fields."""

        for subset_name, available in self.available_attributes.items():
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

        # Try and build the arguments as a dictionary from the config, substituting
        # explicit None values for empty strings
        try:
            # Get arguments and convert inputs - reduce Literals to plain strings.
            required_data = set([str(x) for x in config.required_data])
            cohort_attributes = set(config.cohort_attributes)
            community_canopy_attributes = set(config.community_canopy_attributes)
            stem_canopy_attributes = set(config.stem_canopy_attributes)
        except KeyError as excep:
            LOGGER.error(excep)
            raise

        # Return the instance
        return cls(
            output_directory=output_directory,
            required_data=required_data,
            cohort_attributes=cohort_attributes,
            community_canopy_attributes=community_canopy_attributes,
            stem_canopy_attributes=stem_canopy_attributes,
        )

    def dump(
        self,
        communities: PlantCommunities,
        canopies: dict[int, Canopy],
        stem_allocations: dict[int, StemAllocation],
        time: np.datetime64,
    ) -> None:
        """Export plant community data to file.

        The method accepts the main community components of the PlantsModel as arguments
        and compiles and writes the output data requested in the instance setup to file.

        Args:
            communities: A PlantCommunities instance.
            canopies: A dictionary of Canopy instances, keyed by cell id.
            stem_allocations: A dictionary of StemAllocations, also keyed by cell id
            time: A datetime to be used as a timestamp in the output files.
        """

        if not self._active:
            return

        # Run the dump methods for each output option.
        self._dump_cohort_data(
            communities=communities,
            canopies=canopies,
            stem_allocations=stem_allocations,
            time=time,
        )
        self._dump_community_canopy_data(
            canopies=canopies,
            time=time,
        )
        self._dump_stem_canopy_data(
            communities=communities,
            canopies=canopies,
            time=time,
        )

        # Update the output mode and header: all subsequent dump calls use append
        self._output_mode = "a"
        self._write_header = False

    def _dump_cohort_data(
        self,
        communities: PlantCommunities,
        canopies: dict[int, Canopy],
        stem_allocations: dict[int, StemAllocation],
        time: np.datetime64,
    ) -> None:
        """Dump plant cohort data to file.

        Args:
            communities: A PlantCommunities instance.
            canopies: A dictionary of Canopy instances, keyed by cell id.
            stem_allocations: A dictionary of StemAllocations, also keyed by cell id
            time: A datetime to be used as a timestamp in the output files
        """

        # If the data has not been requested - so the path is None - then exit
        if self._cohort_path is None:
            return

        # Collect cell dataframes into an list for use with row-wise pd.concat()
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
    ):
        """Dump community canopy data to file.

        Args:
            canopies: A dictionary of Canopy instances, keyed by cell id.
            time: A datetime to be used as a timestamp in the output files
        """
        # If the data has not been requested - so the path is None - then exit
        if self._community_canopy_path is None:
            return

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
    ) -> None:
        """Dump stem canopy data to file.

        Args:
            communities: A PlantCommunities instance.
            canopies: A dictionary of Canopy instances, keyed by cell id.
            time: A datetime to be used as a timestamp in the output files
        """
        # If the data has not been requested - so the path is None - then exit
        if self._stem_canopy_path is None:
            return

        stem_canopy_data = []
        for (cell_id, canopy), community in zip(canopies.items(), communities.values()):
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
            self._stem_canopy_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )
        LOGGER.info(f"Plant model stem canopy data dumped at time: {time}")
