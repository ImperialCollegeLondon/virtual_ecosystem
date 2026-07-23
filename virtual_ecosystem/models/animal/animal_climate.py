"""The ``models.animal.climate`` module provides a container for the per-cell,
per-stratum microclimate used by the animal model.

The animal model resolves the abiotic model's layered temperature outputs into a small
set of per-cell arrays once per timestep. These are consumed both by the per-cohort
activity window calculation and by the per-functional-group thermal suitability grid,
so they are bundled here rather than being threaded through as loose positional
arguments.
"""  # noqa: D205

from __future__ import annotations

from dataclasses import dataclass

from numpy.typing import NDArray


@dataclass(frozen=True)
class StratumClimate:
    """Per-cell temperature and diurnal range for each vertical stratum.

    Assembled once per timestep from the abiotic model's layered outputs by
    :meth:`~virtual_ecosystem.models.animal.animal_model.AnimalModel._build_stratum_climate`.
    Every array is one-dimensional with shape ``(n_cells,)`` and is indexed by grid
    cell id.

    Where a cell has no filled canopy layers, the canopy fields fall back to the
    corresponding ground values to avoid NaN propagation into the activity window.

    Attributes:
        canopy_temperature: Per-cell mean filled canopy temperature [°C].
        ground_temperature: Per-cell surface air temperature [°C].
        soil_temperature: Per-cell topsoil temperature [°C].
        canopy_diurnal_range: Per-cell mean filled canopy diurnal range [°C].
        ground_diurnal_range: Per-cell surface diurnal range [°C].
        soil_diurnal_range: Per-cell topsoil diurnal range [°C].
    """

    canopy_temperature: NDArray
    ground_temperature: NDArray
    soil_temperature: NDArray
    canopy_diurnal_range: NDArray
    ground_diurnal_range: NDArray
    soil_diurnal_range: NDArray
