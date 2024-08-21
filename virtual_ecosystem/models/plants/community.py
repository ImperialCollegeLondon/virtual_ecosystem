"""The :mod:`~virtual_ecosystem.models.plants.community` submodule provides a simple
dataclass to hold plant cohort information and then the ``PlantCommunities`` class that
is used to hold list of plant cohorts by grid cell and generate those lists from
variables provided in the data object.

NOTE - much of this will be outsourced to pyrealm.

"""  # noqa: D205

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.functional_types import Flora, PlantFunctionalType


@dataclass
class PlantCohort:
    """A dataclass describing a plant cohort.

    The cohort is defined by the plant functional type, the number of individuals in the
    cohort and the diameter at breast height for the cohort.

    Instances also have a ``canopy_area`` and ``gpp`` attributes that are used to track
    the canopy structure of a cohort within the wider community and record gross primary
    productivity. These should not be updated by users.
    """

    pft: PlantFunctionalType
    """The plant functional type of the cohort."""
    dbh: float
    """The diameter at breast height (m) of cohort members."""
    n: int
    """The number of individuals in the cohort."""
    canopy_area: NDArray[np.float32] = field(
        init=False, default_factory=lambda: np.array([])
    )
    """The canopy area within canopy layers of each individual."""
    gpp: float = field(init=False, default=0)
    """The gross primary productivity for each individual."""


class PlantCommunities(dict, Mapping[int, PlantCohort]):
    """A dictionary of plant cohorts keyed by grid cell id.

    An instance of this class is initialised from a
    :class:`~virtual_ecosystem.core.data.Data` object that must contain the variables
    ``plant_cohorts_cell_id``, ``plant_cohorts_pft``, ``plant_cohorts_n`` and
    ``plant_cohorts_dbh``. These are required to be equal length, one-dimensional arrays
    that provide the data to initialise each plant cohort. The data are validated and
    then compiled into lists of cohorts keyed by grid cell id. The class provides a
    __getitem__ method to allow the list of cohorts for a grid cell to be accessed using
    ``plants_inst[cell_id]``.

    Args:
        data: A data instance containing the required plant cohort data.
        flora: A flora containing the plant functional types used in the cohorts.
    """

    def __init__(self, data: Data, flora: Flora):
        # Validate the data being used to generate the Plants object
        cohort_data_vars = [
            "plant_cohorts_n",
            "plant_cohorts_pft",
            "plant_cohorts_cell_id",
            "plant_cohorts_dbh",
        ]

        # All vars present
        missing_var = [v for v in cohort_data_vars if v not in data]

        if missing_var:
            msg = f"Missing plant cohort variables: {', '.join(missing_var)}"
            LOGGER.critical(msg)
            raise ValueError(msg)

        # All vars identically sized and 1D
        data_shapes = [data[var].shape for var in cohort_data_vars]

        if len(set(data_shapes)) != 1:
            msg = (
                f"Unequal plant cohort variable dimensions:"
                f" {','.join([str(v) for v in set(data_shapes)])}"
            )
            LOGGER.critical(msg)
            raise ValueError(msg)

        if len(data_shapes[0]) != 1:
            msg = "Plant cohort variable data is not one dimensional"
            LOGGER.critical(msg)
            raise ValueError(msg)

        # Check the grid cell id and pft values are all known
        bad_cid = set(data["plant_cohorts_cell_id"].data).difference(data.grid.cell_id)
        if bad_cid:
            msg = (
                f"Plant cohort cell ids not in grid cell "
                f"ids: {','.join([str(c) for c in bad_cid])}"
            )
            LOGGER.critical(msg)
            raise ValueError(msg)

        bad_pft = set(data["plant_cohorts_pft"].data).difference(flora.keys())
        if bad_pft:
            msg = f"Plant cohort PFTs ids not in configured PFTs: {','.join(bad_pft)}"
            LOGGER.critical(msg)
            raise ValueError(msg)

        # TODO - think about mechanisms to keep cohort data as arrays either within
        #        cells or across the whole simulation, to make it more efficient with
        #        using pyrealm.

        # Now compile the plant cohorts adding each cohort to a list keyed by cell id
        for cid in data.grid.cell_id:
            self[cid] = []

        for cid, chrt_pft, chrt_dbh, chrt_n in zip(
            data["plant_cohorts_cell_id"].data,
            data["plant_cohorts_pft"].data,
            data["plant_cohorts_dbh"].data,
            data["plant_cohorts_n"].data,
        ):
            self[cid].append(PlantCohort(pft=flora[chrt_pft], dbh=chrt_dbh, n=chrt_n))

        LOGGER.info("Plant cohort data loaded")
