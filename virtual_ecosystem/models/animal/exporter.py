"""The exporter module provides the CohortDataExporter, which is used to control the
output of animal cohort data at each time step. An instance of the class is required
by the AnimalModel, which calls the ``dump()`` method within the setup and update steps
to export data continuously during the model run.
"""  # noqa: D205

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd

from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort


class AnimalCohortDataExporter:
    """The AnimalCohortDataExporter class.

    The exporter appends per-cell cohort rows into a single CSV file. Callers supply
    a mapping from ``cell_id`` to a pandas ``DataFrame`` with cohort attributes for
    that cell. The exporter adds ``cell_id`` and ``time`` columns, performs optional
    column subsetting, and writes or appends to the configured output path.

    Note:
        This minimal version only supports a single table, ``cohorts``. Extend
        :attr:`_outputs` and add new ``_dump_*`` methods to grow functionality.

    Args:
        output_directory: Directory in which to create output CSV files.
        required_data: Set of table names to export. Only ``{"cohorts"}`` is valid
            for now. If empty, the exporter becomes inactive and ``dump`` is a no-op.
        cohort_attributes: Optional whitelist of cohort column names to export. If
            empty, all provided columns are written. Missing names are ignored with
            a warning.
        float_format: Format string for floating-point export, e.g., ``"%0.6f"``.

    Attributes:
        active: Whether any export has been requested (derived from ``required_data``).
    """

    # Map logical table names to (filename, private path attribute)
    _outputs: ClassVar[dict[str, tuple[str, str]]] = dict(
        cohorts=("animals_cohort_data.csv", "_cohort_path"),
    )

    def __init__(
        self,
        output_directory: Path,
        required_data: set[str] = set(),
        cohort_attributes: set[str] = set(),
        float_format: str = "%0.5f",
    ) -> None:
        # Store arguments
        self.output_directory = Path(output_directory)
        """The directory in which to save animal cohort data."""
        self.required_data: set[str] = required_data
        """The set of animal data types to be exported."""
        self.cohort_attributes: set[str] = set(cohort_attributes or set())
        """A subset of cohort attribute names to export."""
        self.float_format = float_format
        """The float format for data export."""

        # Internal state for write/append control
        self._output_mode: str = "w"
        """Switches the exporter between write and append mode."""
        self._write_header: bool = True
        """Stops headers being duplicated in append mode."""
        self._active: bool = bool(self.required_data)
        """Has any data export has been requested."""

        # Private path attributes (set during path validation)
        self._cohort_path: Path | None = None

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
            LOGGER.info("Animal cohort data exporter not active.")
            return

        self._check_and_set_paths()
        self._check_attribute_subsets()
        LOGGER.info("Animal cohort data exporter active.")

    def _check_and_set_paths(self) -> None:
        """Check and set the output paths to be used by the exporter.

        This method assumes that the output directory has already been checked. It sets
        the internal path attributes for each output data type as either None (to signal
        it should not be written) or to a validated output path.
        """

        # Otherwise check no data will be overwritten and export.

        if not (self.output_directory.exists() and self.output_directory.is_dir()):
            msg = (
                f"The animal cohort data output directory does not exist or is not "
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

        available_attributes = {
            "cohort_attributes": set(
                [
                    "cell_id",
                    "time",
                    "cohort_name",
                    "individuals",
                    "age_days",
                    "is_alive",
                    "is_mature",
                    "time_to_maturity_days",
                    "largest_mass_achieved_kg",
                    "centroid_key",
                    "territory_size",
                    "territory_n_cells",
                    "mass_total_kg",
                    "mass_c_kg",
                    "mass_n_kg",
                    "mass_p_kg",
                    "repro_c_kg",
                    "repro_n_kg",
                    "repro_p_kg",
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
    def from_config(cls, config: Config) -> AnimalCohortDataExporter:
        """Factory class to create a AnimalCohortDataExporter from a configuration.

        The configuration requires that the following details are present in the animal
        model section of the configuration;

        .. code-block:: toml

            [animals.animal_cohort_data_export]
            required_data = ["cohorts"]
            cohort_attributes = []

        The ``required_data`` section specifies which community data files are to be
        exported. If the "attributes" sections are empty arrays, then all attributes are
        written to file, but specific fields may be named here to reduce the amount of
        data exported.
        """

        # Try and build the arguments as a dictionary from the config, substituting
        # explicit None values for empty strings
        try:
            out_path = config["core"]["data_output_options"]["out_path"]
            xcfg = config["animals"]["animal_cohort_data_export"]

            # Get arguments and convert inputs
            output_directory = Path(out_path)
            required_data = set(xcfg["required_data"])
            cohort_attributes = set(xcfg["cohort_attributes"])

        except KeyError as excep:
            LOGGER.error(excep)
            raise

        # Return the instance
        return cls(
            output_directory=output_directory,
            required_data=required_data,
            cohort_attributes=cohort_attributes,
        )

    def dump(
        self,
        communities: dict[int, list[AnimalCohort]],
        time: np.datetime64,
    ) -> None:
        """Export animal community data to file.

        The method accepts the main animal community component of the AnimalModel as
        arguments and compiles and writes the output data requested in the instance
        setup to file.

        Args:
            communities: A dictionary of grid location and animal cohort objects.
            time: A datetime to be used as a timestamp in the output files.
        """

        if not self._active:
            return

        # Run the dump methods for each output option.
        self._dump_cohort_data(
            communities=communities,
            time=time,
        )

        # Update the output mode and header: all subsequent dump calls use append
        self._output_mode = "a"
        self._write_header = False

    def _dump_cohort_data(
        self,
        communities: dict[int, list[AnimalCohort]],
        time: np.datetime64,
    ) -> None:
        """Dump animal cohort rows to CSV.

        Flattens cohort scalars into one row per cohort, adds ``cell_id`` and ``time``,
        optionally subsets columns, and writes/appends to CSV.
        """
        # Not requested
        if self._cohort_path is None:
            return

        rows: list[dict] = []

        for cell_id, cohorts in communities.items():
            for cohort in cohorts:
                # Core identity / status
                row = {
                    "cell_id": cell_id,
                    "time": time,
                    "cohort_name": getattr(cohort, "name", None),
                    "individuals": getattr(cohort, "individuals", None),
                    "age_days": getattr(cohort, "age", None),
                    "is_alive": getattr(cohort, "is_alive", None),
                    "is_mature": getattr(cohort, "is_mature", None),
                    "time_to_maturity_days": getattr(cohort, "time_to_maturity", None),
                    "largest_mass_achieved_kg": getattr(
                        cohort, "largest_mass_achieved", None
                    ),
                    "centroid_key": getattr(cohort, "centroid_key", None),
                    "territory_size": getattr(cohort, "territory_size", None),
                    "territory_n_cells": len(getattr(cohort, "territory", []) or []),
                    "mass_total_kg": getattr(cohort, "mass_current", None),
                }

                # Stoichiometry: cohort.mass_cnp and reproductive_mass_cnp (if present)
                mass_cnp = getattr(cohort, "mass_cnp", None)
                if mass_cnp is not None:
                    row["mass_c_kg"] = getattr(mass_cnp, "carbon", None)
                    row["mass_n_kg"] = getattr(mass_cnp, "nitrogen", None)
                    row["mass_p_kg"] = getattr(mass_cnp, "phosphorus", None)

                repro_cnp = getattr(cohort, "reproductive_mass_cnp", None)
                if repro_cnp is not None:
                    row["repro_c_kg"] = getattr(repro_cnp, "carbon", None)
                    row["repro_n_kg"] = getattr(repro_cnp, "nitrogen", None)
                    row["repro_p_kg"] = getattr(repro_cnp, "phosphorus", None)

                rows.append(row)

        if not rows:
            return

        df = pd.DataFrame.from_records(rows)

        # Optional whitelist
        if self.cohort_attributes:
            keep = [c for c in self.cohort_attributes if c in df.columns]
            # Always keep join keys
            for k in ("cell_id", "time"):
                if k not in keep and k in df.columns:
                    keep.append(k)
            if keep:
                df = df[keep]

        df.to_csv(
            self._cohort_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )
        LOGGER.info(f"Animal cohort data dumped at time: {time}")
