"""The exporter module provides the
:class:`~virtual_ecosystem.models.animal.model_config.AnimalExportConfig`,
which is used to control the output of animal cohort data at each time step. An instance
of the class is required by the
:class:`~virtual_ecosystem.models.animal.animal_cohorts.AnimalCohort`, which calls the
``dump()`` method within the setup and update steps to export data continuously during
the model run.
"""  # noqa: D205

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd

from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
from virtual_ecosystem.models.animal.model_config import AnimalExportConfig


class AnimalCohortDataExporter:
    """Exporter for detailed animal cohort data.

    This class writes one CSV file containing a row for every cohort at every
    time step. The file is opened in write mode on the first call to ``dump``
    (including the header) and subsequently appended to.

    The exporter mirrors the design of
    :class:`virtual_ecosystem.models.plants.exporter.CommunityDataExporter`
    but is simplified to a single ``cohorts`` output stream.

    Args:
        output_directory: Directory where the CSV file will be created.
        cohort_attributes: Optional subset of cohort attributes to export. If an
            empty set is provided, all available attributes are written.
        float_format: Float format string used when writing numeric data.
    """

    _outputs: ClassVar[dict[str, tuple[str, str]]] = {
        "cohorts": ("animal_cohort_data.csv", "_cohort_path"),
        "trophic": ("animal_trophic_interactions.csv", "_trophic_path"),
    }
    """Mapping from output key to (filename, path-attribute-name)."""

    required_attributes: ClassVar[tuple[str, ...]] = (
        "cohort_id",
        "time",
        "time_index",
    )
    """A set of output fields that are always included in cohort export."""

    available_attributes: ClassVar[set[str]] = {
        "functional_group",
        "development_type",
        "diet_type",
        "reproductive_environment",
        "age",
        "individuals",
        "is_alive",
        "is_mature",
        "time_to_maturity",
        "time_since_maturity",
        "location_status",
        "centroid_key",
        "territory_size",
        "territory",
        "occupancy_proportion",
        "largest_mass_achieved",
        "mass_carbon",
        "mass_nitrogen",
        "mass_phosphorus",
        "reproductive_mass_carbon",
        "reproductive_mass_nitrogen",
        "reproductive_mass_phosphorus",
    }

    """The set of valid attribute names that can be selected for cohort export."""

    def __init__(
        self,
        output_directory: Path,
        cohort_attributes: set[str] | None = None,
        float_format: str = "%0.5f",
    ) -> None:
        # Public configuration
        self.output_directory: Path = output_directory
        """The directory in which to save animal cohort data."""
        self.cohort_attributes: set[str] = cohort_attributes or set()
        """The set of animal cohort attributes to be exported."""
        self.float_format: str = float_format
        """The float format for data export."""

        # Internal state
        self._cohort_output_mode: str = "w"
        """Switches the cohort exporter between write and append mode."""
        self._trophic_output_mode: str = "w"
        """Switches the trophic exporter between write and append mode."""
        self._write_cohort_header: bool = True
        """Stops cohort headers being duplicated in append mode."""
        self._write_trophic_header: bool = True
        """Stops trophic headers being duplicated in append mode."""
        self._active: bool = True
        """Has any data export has been requested."""
        self._cohort_path: Path | None = None
        """Sets the output path for the cohort csv."""
        self._trophic_path: Path | None = None
        """Sets the output path for the trophic csv."""

        # Remove any required headers from the cohort attributes so that the attribute
        # subset validation only checks the optional available values
        self.cohort_attributes -= set(self.required_attributes)

        self._check_and_set_paths()
        self._check_attribute_subsets()

    @classmethod
    def from_config(
        cls,
        output_directory: Path,
        config: AnimalExportConfig,
    ) -> AnimalCohortDataExporter:
        """Create an exporter from an AnimalExportConfig instance.

        Args:
            output_directory: Directory where the CSV file will be created.
            config: Configuration section controlling animal cohort export.

        Returns:
            Initialised AnimalCohortDataExporter instance.
        """
        if not config.enabled:
            LOGGER.info("Animal cohort data exporter not active.")
            exporter = cls.__new__(cls)

            # Public configuration
            exporter.output_directory = output_directory
            exporter.cohort_attributes = set()
            exporter.float_format = config.float_format

            # Internal state
            exporter._cohort_output_mode = "w"
            exporter._trophic_output_mode = "w"
            exporter._write_cohort_header = True
            exporter._write_trophic_header = True

            exporter._active = False
            exporter._cohort_path = None
            exporter._trophic_path = None

            return exporter

        cohort_attributes = set(config.cohort_attributes)

        return cls(
            output_directory=output_directory,
            cohort_attributes=cohort_attributes,
            float_format=config.float_format,
        )

    def _check_and_set_paths(self) -> None:
        """Check and set the output paths to be used by the exporter.

        Raises:
            ConfigurationError: If the directory does not exist or is not a directory,
                or if any output file already exists.
        """
        if not (self.output_directory.exists() and self.output_directory.is_dir()):
            msg = (
                "The animal cohort data output directory does not exist or is not "
                f"a directory: {self.output_directory}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        for output_key, (fname, attr_name) in self._outputs.items():
            data_path = self.output_directory / fname

            if data_path.exists():
                msg = (
                    "An output file for animal cohort export already exists: "
                    f"{output_key} -> {fname}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

            setattr(self, attr_name, data_path)

    def _check_attribute_subsets(self) -> None:
        """Validate that requested attribute subset is available.

        Raises:
            ConfigurationError: If any requested attribute is unknown.
        """

        if not self.cohort_attributes:
            return

        not_found = self.cohort_attributes.difference(self.available_attributes)
        if not_found:
            msg = (
                "The cohort exporter configuration contains unknown attributes: "
                f"{', '.join(sorted(not_found))}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

    def _dump_cohorts(
        self,
        cohorts: Iterable[AnimalCohort],
        time: np.datetime64,
        time_index: int,
    ) -> None:
        """Write animal cohort data to CSV.

        Args:
            cohorts: Iterable of animal cohort objects.
            time: Timestamp to associate with this snapshot.
            time_index: The index of the datatime within the model updates.
        """
        if not self._active:
            return

        if self._cohort_path is None:
            LOGGER.debug("Animal cohort exporter called with no output path.")
            return

        rows: list[dict[str, object]] = []

        for cohort in cohorts:
            rows.append(
                self._build_cohort_row(cohort=cohort, time=time, time_index=time_index)
            )

        if not rows:
            LOGGER.info("Animal cohort exporter called with no cohorts present.")
            return

        df = pd.DataFrame(rows)

        if self.cohort_attributes:
            df = df[list(self.required_attributes) + sorted(self.cohort_attributes)]

        df.to_csv(
            self._cohort_path,
            mode=self._cohort_output_mode,
            header=self._write_cohort_header,
            index=False,
            float_format=self.float_format,
        )

        LOGGER.info("Animal model cohort data dumped at time: %s", time)

        # Flip cohort state because we actually wrote a file.
        self._cohort_output_mode = "a"
        self._write_cohort_header = False

    def _dump_trophic(
        self,
        cohorts: Iterable[AnimalCohort],
        territory_by_id: dict[str, list[int]],
        time: np.datetime64,
        time_index: int,
    ) -> None:
        """Write trophic interaction data to CSV.

        Args:
            cohorts: List of animal cohort objects.
            territory_by_id: Dictionary of str(uuid),territory pairs for lookup.
            time: Timestamp to associate with this snapshot.
            time_index: The index of the datatime within the model updates.
        """
        if not self._active:
            return

        if self._trophic_path is None:
            LOGGER.debug("Trophic exporter called with no output path.")
            return

        rows: list[dict[str, object]] = []

        for cohort in cohorts:
            rows.extend(
                self._build_trophic_rows(
                    cohort=cohort,
                    time=time,
                    territory_by_id=territory_by_id,
                    time_index=time_index,
                )
            )

        if not rows:
            LOGGER.info("Trophic exporter called with no interactions present.")
            return

        df = pd.DataFrame(rows)
        df.to_csv(
            self._trophic_path,
            mode=self._trophic_output_mode,
            header=self._write_trophic_header,
            index=False,
            float_format=self.float_format,
        )

        # Flip trophic state because we actually wrote a file.
        self._trophic_output_mode = "a"
        self._write_trophic_header = False

    def dump(
        self, cohorts: Iterable[AnimalCohort], time: np.datetime64, time_index: int
    ) -> None:
        """Write animal cohort and trophic interaction data to CSV.

        Args:
            cohorts: List of animal cohort objects.
            time: Timestamp to associate with this snapshot.
            time_index: The index of the datatime within the model updates.

        """
        if not self._active:
            return

        if self._cohort_path is None and self._trophic_path is None:
            LOGGER.debug("Animal exporter called with no output path.")
            return

        cohort_list = list(cohorts)
        territory_by_id = {str(cohort.id): cohort.territory for cohort in cohort_list}
        self._dump_cohorts(cohorts=cohort_list, time=time, time_index=time_index)
        self._dump_trophic(
            cohorts=cohort_list,
            territory_by_id=territory_by_id,
            time=time,
            time_index=time_index,
        )

    def _build_cohort_row(
        self,
        cohort: AnimalCohort,
        time: np.datetime64,
        time_index: int,
    ) -> dict[str, object]:
        """Build a single output row for a cohort.

        Args:
            cohort: Cohort to serialise.
            time: Timestamp for this snapshot.
            time_index: The index of the datatime within the model updates.

        Returns:
            Dictionary mapping column name to value.
        """
        fg = cohort.functional_group
        mass_cnp = cohort.mass_cnp
        repro_cnp = cohort.reproductive_mass_cnp

        return {
            "time": time,
            "time_index": time_index,
            "cohort_id": str(cohort.id),
            "functional_group": fg.name,
            "development_type": str(fg.development_type),
            "diet_type": str(fg.diet),
            "reproductive_environment": str(fg.reproductive_environment),
            "age": cohort.age,
            "individuals": cohort.individuals,
            "is_alive": cohort.is_alive,
            "is_mature": cohort.is_mature,
            "time_to_maturity": cohort.time_to_maturity,
            "time_since_maturity": cohort.time_since_maturity,
            "location_status": cohort.location_status,
            "centroid_key": cohort.centroid_key,
            "territory_size": cohort.territory_size,
            "territory": cohort.territory,
            "occupancy_proportion": cohort.occupancy_proportion,
            "largest_mass_achieved": cohort.largest_mass_achieved,
            "mass_carbon": mass_cnp.carbon,
            "mass_nitrogen": mass_cnp.nitrogen,
            "mass_phosphorus": mass_cnp.phosphorus,
            "reproductive_mass_carbon": repro_cnp.carbon,
            "reproductive_mass_nitrogen": repro_cnp.nitrogen,
            "reproductive_mass_phosphorus": repro_cnp.phosphorus,
        }

    def _build_trophic_rows(
        self,
        cohort: AnimalCohort,
        territory_by_id: dict[str, list[int]],
        time: np.datetime64,
        time_index: int,
    ) -> list[dict[str, object]]:
        """Build trophic interaction rows for a single cohort.

        Args:
            cohort: Consumer cohort containing a trophic_record for the timestep.
            territory_by_id: Dictionary of str(uuid),territory pairs for lookup.
            time: Timestamp for this snapshot.
            time_index: The index of the datatime within the model updates.

        Returns:
            List of dictionaries, one per resource consumed, with C/N/P removed.
        """
        rows: list[dict[str, object]] = []
        for (resource_kind, resource_id), cnp in cohort.trophic_record.items():
            prey_territory: list[int] | None = None
            resource_cell_id: int | None = None

            if resource_kind == "cohort":
                # Prey is another animal cohort
                prey_territory = territory_by_id.get(resource_id)

            else:
                # Resource pools are keyed by cell id
                resource_cell_id = int(resource_id)

            rows.append(
                {
                    "time": time,
                    "time_index": time_index,
                    "consumer_cohort_id": str(cohort.id),
                    "consumer_territory": cohort.territory,
                    "resource_kind": resource_kind,
                    "resource_id": resource_id,
                    "resource_cell_id": resource_cell_id,
                    "prey_territory": prey_territory,
                    "carbon": cnp["carbon"],
                    "nitrogen": cnp["nitrogen"],
                    "phosphorus": cnp["phosphorus"],
                }
            )

        return rows
