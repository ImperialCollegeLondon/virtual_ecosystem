"""The exporter module provides the
:class:`~virtual_ecosystem.models.animal.model_config.AnimalExportConfig`,
which is used to control the output of animal cohort data at each time step. An instance
of the class is required by the
:class:`~virtual_ecosystem.models.animal.animal_cohorts.AnimalCohort`, which calls the
``dump()`` method within the setup and update steps to export data continuously during
the model run.
"""  # noqa: D205

from __future__ import annotations

from collections.abc import Iterable, Mapping
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
    }
    """Mapping from output key to (filename, path-attribute-name)."""

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
        self._output_mode: str = "w"
        """Switches the exporter between write and append mode."""
        self._write_header: bool = True
        """Stops headers being duplicated in append mode."""
        self._active: bool = True
        """Has any data export has been requested."""
        self._cohort_path: Path | None = None

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
            exporter.output_directory = output_directory
            exporter.cohort_attributes = set()
            exporter.float_format = config.float_format
            exporter._output_mode = "w"
            exporter._write_header = True
            exporter._active = False
            exporter._cohort_path = None
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
            ConfigurationError: If the directory does not exist or the file
                already exists.
        """
        if not (self.output_directory.exists() and self.output_directory.is_dir()):
            msg = (
                "The animal cohort data output directory does not exist or is not "
                f"a directory: {self.output_directory}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        fname, attr_name = self._outputs["cohorts"]
        data_path = self.output_directory / fname

        if data_path.exists():
            msg = f"An output file for animal cohort data already exists: {fname}"
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        setattr(self, attr_name, data_path)

    def _check_attribute_subsets(self) -> None:
        """Validate that requested attribute subset is available.

        Raises:
            ConfigurationError: If any requested attribute is unknown.
        """
        available = self.available_attributes

        if not self.cohort_attributes:
            return

        not_found = self.cohort_attributes.difference(available)
        if not_found:
            msg = (
                "The cohort exporter configuration contains unknown attributes: "
                f"{', '.join(sorted(not_found))}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

    @property
    def available_attributes(self) -> set[str]:
        """Return the set of valid attribute names for cohort export."""
        return {
            "cell_id",
            "time",
            "cohort_id",
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

    def dump(
        self,
        communities: Mapping[int, Iterable[AnimalCohort]],
        time: np.datetime64,
    ) -> None:
        """Write animal cohort data to CSV.

        Args:
            communities: Mapping from cell id to iterable of AnimalCohort instances in
                the cell.
            time: Timestamp to associate with this snapshot.
        """
        if not self._active:
            return

        if self._cohort_path is None:
            LOGGER.debug("Animal cohort exporter called with no output path.")
            return

        rows: list[dict[str, object]] = []

        for cell_id, cohorts in communities.items():
            for cohort in cohorts:
                rows.append(self._build_row(cell_id=cell_id, cohort=cohort, time=time))

        if not rows:
            LOGGER.info("Animal cohort exporter called with no cohorts present.")
            return

        df = pd.DataFrame(rows)

        if self.cohort_attributes:
            df = df[list(self.cohort_attributes)]

        df.to_csv(
            self._cohort_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )

        LOGGER.info("Animal model cohort data dumped at time: %s", time)

        self._output_mode = "a"
        self._write_header = False

    def _build_row(
        self,
        cell_id: int,
        cohort: AnimalCohort,
        time: np.datetime64,
    ) -> dict[str, object]:
        """Build a single output row for a cohort.

        Args:
            cell_id: Grid cell identifier.
            cohort: Cohort to serialise.
            time: Timestamp for this snapshot.

        Returns:
            Dictionary mapping column name to value.
        """
        fg = cohort.functional_group
        mass_cnp = cohort.mass_cnp
        repro_cnp = cohort.reproductive_mass_cnp

        return {
            "cell_id": cell_id,
            "time": time,
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
