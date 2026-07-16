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
from virtual_ecosystem.models.animal.array_resources import ResourcePool
from virtual_ecosystem.models.animal.decay import (
    CarcassPool,
    ExcrementPool,
    FungalFruitPool,
    SoilPool,
)
from virtual_ecosystem.models.animal.model_config import (
    AnimalExportConfig,
    ResourcePoolExportConfig,
)


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
        "activity_window_proportion",
        "reference_temp",
        "current_temperature",
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
            "mass_carbon": mass_cnp.C,
            "mass_nitrogen": mass_cnp.N,
            "mass_phosphorus": mass_cnp.P,
            "reproductive_mass_carbon": repro_cnp.C,
            "reproductive_mass_nitrogen": repro_cnp.N,
            "reproductive_mass_phosphorus": repro_cnp.P,
            "activity_window_proportion": cohort.sigma_f_t,
            "reference_temp": cohort.reference_temp,
            "current_temperature": cohort.current_temperature,
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
                    "functional_group": cohort.functional_group.name,
                    "consumer_cohort_id": str(cohort.id),
                    "consumer_territory": cohort.territory,
                    "resource_kind": resource_kind,
                    "resource_id": resource_id,
                    "resource_cell_id": resource_cell_id,
                    "prey_territory": prey_territory,
                    "activity_window_proportion": cohort.sigma_f_t,
                    "C": cnp["C"],
                    "N": cnp["N"],
                    "P": cnp["P"],
                }
            )

        return rows


class ResourcePoolDataExporter:
    """Exporter for resource pool state data.

    Writes one CSV file containing a row for every resource pool sub-pool at
    every time step. The file is opened in write mode on the first call to
    ``dump`` (including the header) and subsequently appended to.

    The exporter covers all animal-model resource pools: carcass, excrement,
    fungal fruiting body, soil, and plant/litter array pools. Each row
    identifies the pool by ``pool_type``, ``pool_name``, ``sub_pool``, ``pft``,
    and ``cell_id``, and records the carbon, nitrogen, and phosphorus masses at
    the time of the snapshot.

    For plant and litter array pools the snapshot reflects the pre-foraging
    available masses, because ``ResourcePool.elemental_masses`` is populated by
    ``set_resources`` at the start of each update step and is not modified
    in-place during foraging.

    Args:
        output_directory: Directory where the CSV file will be created.
        float_format: Float format string used when writing numeric data.
    """

    _outputs: ClassVar[dict[str, tuple[str, str]]] = {
        "resource_pools": ("resource_pool_data.csv", "_pool_path"),
    }
    """Mapping from output key to (filename, path-attribute-name)."""

    def __init__(
        self,
        output_directory: Path,
        float_format: str = "%0.5f",
    ) -> None:
        self.output_directory: Path = output_directory
        """The directory in which to save resource pool data."""
        self.float_format: str = float_format
        """The float format for data export."""

        self._output_mode: str = "w"
        """Switches the exporter between write and append mode."""
        self._write_header: bool = True
        """Stops headers being duplicated in append mode."""
        self._active: bool = True
        """Whether any data export has been requested."""
        self._pool_path: Path | None = None
        """Sets the output path for the resource pool csv."""

        self._check_and_set_paths()

    @classmethod
    def from_config(
        cls,
        output_directory: Path,
        config: ResourcePoolExportConfig,
    ) -> ResourcePoolDataExporter:
        """Create an exporter from a ResourcePoolExportConfig instance.

        If the config has ``enabled=False``, returns an inactive exporter that
        silently no-ops on all ``dump`` calls.

        Args:
            output_directory: Directory where the CSV file will be created.
            config: Configuration section controlling resource pool export.

        Returns:
            Initialised ResourcePoolDataExporter instance.
        """
        if not config.enabled:
            LOGGER.info("Resource pool data exporter not active.")
            exporter = cls.__new__(cls)
            exporter.output_directory = output_directory
            exporter.float_format = config.float_format
            exporter._output_mode = "w"
            exporter._write_header = True
            exporter._active = False
            exporter._pool_path = None
            return exporter

        return cls(
            output_directory=output_directory,
            float_format=config.float_format,
        )

    def _check_and_set_paths(self) -> None:
        """Check and set the output paths to be used by the exporter.

        Raises:
            ConfigurationError: If the directory does not exist or is not a
                directory, or if any output file already exists.
        """
        if not (self.output_directory.exists() and self.output_directory.is_dir()):
            msg = (
                "The resource pool data output directory does not exist or is not "
                f"a directory: {self.output_directory}"
            )
            LOGGER.error(msg)
            raise ConfigurationError(msg)

        for output_key, (fname, attr_name) in self._outputs.items():
            data_path = self.output_directory / fname

            if data_path.exists():
                msg = (
                    "An output file for resource pool export already exists: "
                    f"{output_key} -> {fname}"
                )
                LOGGER.error(msg)
                raise ConfigurationError(msg)

            setattr(self, attr_name, data_path)

    def dump(
        self,
        carcass_pools: dict[int, list[CarcassPool]],
        excrement_pools: dict[int, list[ExcrementPool]],
        fungal_fruiting_pools: dict[int, FungalFruitPool],
        soil_pools: dict[int, dict[str, SoilPool]],
        resource_pools: list[ResourcePool],
        time: np.datetime64,
        time_index: int,
    ) -> None:
        """Write resource pool state data to CSV.

        This method is a no-op if the exporter is inactive.

        Args:
            carcass_pools: Carcass pools keyed by cell id, each containing one
                or more CarcassPool instances.
            excrement_pools: Excrement pools keyed by cell id, each containing
                one or more ExcrementPool instances.
            fungal_fruiting_pools: Fungal fruiting body pools keyed by cell id.
            soil_pools: Soil pools keyed by cell id and then by pool-type string
                (e.g. ``"bacteria"``, ``"saprotrophic_fungi"``).
            resource_pools: Flat list of plant and litter ResourcePool
                instances. Each pool's ``elemental_masses`` array holds
                pre-foraging available masses set by the most recent
                ``set_resources`` call.
            time: Timestamp to associate with this snapshot.
            time_index: The index of the datetime within the model updates.
        """
        if not self._active:
            return

        if self._pool_path is None:
            LOGGER.debug("Resource pool exporter called with no output path.")
            return

        rows: list[dict[str, object]] = []
        rows.extend(self._build_carcass_rows(carcass_pools, time, time_index))
        rows.extend(self._build_excrement_rows(excrement_pools, time, time_index))
        rows.extend(self._build_fungal_rows(fungal_fruiting_pools, time, time_index))
        rows.extend(self._build_soil_rows(soil_pools, time, time_index))
        rows.extend(self._build_resource_pool_rows(resource_pools, time, time_index))

        if not rows:
            LOGGER.info("Resource pool exporter called with no pool data present.")
            return

        pd.DataFrame(rows).to_csv(
            self._pool_path,
            mode=self._output_mode,
            header=self._write_header,
            index=False,
            float_format=self.float_format,
        )

        LOGGER.info("Resource pool data dumped at time: %s", time)

        self._output_mode = "a"
        self._write_header = False

    def _build_carcass_rows(
        self,
        carcass_pools: dict[int, list[CarcassPool]],
        time: np.datetime64,
        time_index: int,
    ) -> list[dict[str, object]]:
        """Build output rows for all carcass pools.

        Emits two rows per pool instance: one for the scavengeable fraction and
        one for the decomposed fraction.

        Args:
            carcass_pools: Carcass pools keyed by cell id.
            time: Timestamp for this snapshot.
            time_index: The index of the datetime within the model updates.

        Returns:
            List of row dictionaries, two per CarcassPool instance.
        """
        rows = []
        for cell_id, pools in carcass_pools.items():
            for pool in pools:
                for sub_pool, cnp in (
                    ("scavengeable", pool.scavengeable_cnp),
                    ("decomposed", pool.decomposed_cnp),
                ):
                    rows.append(
                        {
                            "time": time,
                            "time_index": time_index,
                            "pool_type": "carcass",
                            "pool_name": "",
                            "sub_pool": sub_pool,
                            "pft": "",
                            "cell_id": cell_id,
                            "C": cnp.C,
                            "N": cnp.N,
                            "P": cnp.P,
                        }
                    )
        return rows

    def _build_excrement_rows(
        self,
        excrement_pools: dict[int, list[ExcrementPool]],
        time: np.datetime64,
        time_index: int,
    ) -> list[dict[str, object]]:
        """Build output rows for all excrement pools.

        Emits two rows per pool instance: one for the scavengeable fraction and
        one for the decomposed fraction.

        Args:
            excrement_pools: Excrement pools keyed by cell id.
            time: Timestamp for this snapshot.
            time_index: The index of the datetime within the model updates.

        Returns:
            List of row dictionaries, two per ExcrementPool instance.
        """
        rows = []
        for cell_id, pools in excrement_pools.items():
            for pool in pools:
                for sub_pool, cnp in (
                    ("scavengeable", pool.scavengeable_cnp),
                    ("decomposed", pool.decomposed_cnp),
                ):
                    rows.append(
                        {
                            "time": time,
                            "time_index": time_index,
                            "pool_type": "excrement",
                            "pool_name": "",
                            "sub_pool": sub_pool,
                            "pft": "",
                            "cell_id": cell_id,
                            "C": cnp.C,
                            "N": cnp.N,
                            "P": cnp.P,
                        }
                    )
        return rows

    def _build_fungal_rows(
        self,
        fungal_fruiting_pools: dict[int, FungalFruitPool],
        time: np.datetime64,
        time_index: int,
    ) -> list[dict[str, object]]:
        """Build output rows for all fungal fruiting body pools.

        Emits one row per pool instance.

        Args:
            fungal_fruiting_pools: Fungal fruiting body pools keyed by cell id.
            time: Timestamp for this snapshot.
            time_index: The index of the datetime within the model updates.

        Returns:
            List of row dictionaries, one per FungalFruitPool instance.
        """
        rows = []
        for cell_id, pool in fungal_fruiting_pools.items():
            rows.append(
                {
                    "time": time,
                    "time_index": time_index,
                    "pool_type": "fungal_fruiting",
                    "pool_name": "",
                    "sub_pool": "",
                    "pft": "",
                    "cell_id": cell_id,
                    "C": pool.mass_cnp.C,
                    "N": pool.mass_cnp.N,
                    "P": pool.mass_cnp.P,
                }
            )
        return rows

    def _build_soil_rows(
        self,
        soil_pools: dict[int, dict[str, SoilPool]],
        time: np.datetime64,
        time_index: int,
    ) -> list[dict[str, object]]:
        """Build output rows for all soil pools.

        Emits one row per (cell, pool-type) combination.

        Args:
            soil_pools: Soil pools keyed by cell id and pool-type string (e.g.
                ``"bacteria"``, ``"saprotrophic_fungi"``).
            time: Timestamp for this snapshot.
            time_index: The index of the datetime within the model updates.

        Returns:
            List of row dictionaries, one per SoilPool instance.
        """
        rows = []
        for cell_id, pools_by_type in soil_pools.items():
            for pool_name, pool in pools_by_type.items():
                rows.append(
                    {
                        "time": time,
                        "time_index": time_index,
                        "pool_type": "soil",
                        "pool_name": pool_name,
                        "sub_pool": "",
                        "pft": "",
                        "cell_id": cell_id,
                        "C": pool.mass_cnp.C,
                        "N": pool.mass_cnp.N,
                        "P": pool.mass_cnp.P,
                    }
                )
        return rows

    def _build_resource_pool_rows(
        self,
        resource_pools: list[ResourcePool],
        time: np.datetime64,
        time_index: int,
    ) -> list[dict[str, object]]:
        """Build output rows for all plant and litter array resource pools.

        Emits one row per (pool, cell) combination. The C, N, and P masses are
        taken from ``ResourcePool.elemental_masses``, which holds pre-foraging
        available masses populated by the most recent ``set_resources`` call.

        Args:
            resource_pools: Flat list of ResourcePool instances.
            time: Timestamp for this snapshot.
            time_index: The index of the datetime within the model updates.

        Returns:
            List of row dictionaries, one per (ResourcePool, cell) pair.
        """
        rows = []
        for pool in resource_pools:
            pool_name = pool.resource.pool_array
            pft = pool.pft or ""
            for cell_id, (C, N, P) in enumerate(pool.elemental_masses):
                rows.append(
                    {
                        "time": time,
                        "time_index": time_index,
                        "pool_type": "resource_array",
                        "pool_name": pool_name,
                        "sub_pool": "",
                        "pft": pft,
                        "cell_id": cell_id,
                        "C": C,
                        "N": N,
                        "P": P,
                    }
                )
        return rows
