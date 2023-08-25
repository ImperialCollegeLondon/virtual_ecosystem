"""The :mod:`~virtual_rainforest.models.plants.community` submodule provides a simple
dataclass to hold plant cohort information and then the ``PlantCommunities`` class that
is used to hold list of plant cohorts by grid cell and generate those lists from
variables provided in the data object.

NOTE - much of this will be outsourced to pyrealm.

"""  # noqa: D205, D415


from dataclasses import dataclass

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.plants.functional_types import (
    PlantFunctionalType,
    PlantFunctionalTypes,
)


@dataclass
class PlantCohort:
    """A dataclass describing a plant cohort.

    The cohort is defined by the plant functional type, the number of individuals in the
    cohort and the diameter at breast height for the cohort.
    """

    pft: PlantFunctionalType
    dbh: float
    n: int


class PlantCommunities:
    """A dictionary of plant cohorts keyed by grid cell id.

    An instance of this class is initialised from a
    :class:`~virtual_rainforest.core.data.Data` object that must contain the variables
    ``plant_cohort_cell_id``, ``plant_cohort_pft``, ``plant_cohort_n`` and
    ``plant_cohort_dbh``. These are required to be equal length, one-dimensional arrays
    that provide the data to initialise each plant cohort. The data are validated and
    then compiled into lists of cohorts keyed by grid cell id. The class provides a
    __getitem__ method to allow the list of cohorts for a grid cell to be accessed using
    ``plants_inst[cell_id]``.

    Args:
        data: A data instance containing the required plant cohort data.
        pfts: The plant functional types to be used.
    """

    def __init__(self, data: Data, pfts: PlantFunctionalTypes):
        self.communities: dict = dict()
        """A dictionary holding the lists of plant cohorts keyed by cell id."""

        # Validate the data being used to generate the Plants object
        cohort_data_vars = [
            "plant_cohort_n",
            "plant_cohort_pft",
            "plant_cohort_cell_id",
            "plant_cohort_dbh",
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
        bad_cid = set(data["plant_cohort_cell_id"].data).difference(data.grid.cell_id)
        if bad_cid:
            msg = (
                f"Plant cohort cell ids not in grid cell "
                f"ids: {','.join([str(c) for c in bad_cid])}"
            )
            LOGGER.critical(msg)
            raise ValueError(msg)

        bad_pft = set(data["plant_cohort_pft"].data).difference(pfts.keys())
        if bad_pft:
            msg = f"Plant cohort PFTs ids not in configured PFTs: {','.join(bad_pft)}"
            LOGGER.critical(msg)
            raise ValueError(msg)

        # Now compile the plant cohorts adding each cohort to a list keyed by cell id
        for cid in data.grid.cell_id:
            self.communities[cid] = []

        for cid, chrt_pft, chrt_dbh, chrt_n in zip(
            data["plant_cohort_cell_id"].data,
            data["plant_cohort_pft"].data,
            data["plant_cohort_dbh"].data,
            data["plant_cohort_n"].data,
        ):
            self.communities[cid].append(
                PlantCohort(pft=pfts[chrt_pft], dbh=chrt_dbh, n=chrt_n)
            )

        LOGGER.info("Plant cohort data loaded")

    def __getitem__(self, key: int) -> list[PlantCohort]:
        """Extracts the cohort list for a given cell id."""
        return self.communities[key]
