"""The :mod:`~virtual_ecosystem.models.plants.communities` submodule  provides the
:class:`~virtual_ecosystem.models.plants.communities.PlantCommunities` class. This
provides a dictionary mapping each grid cell id to the  plant community growing within
the cell.

There is a one-to-one mapping of grid cells to plant communities, with the individual
community for a grid cell being represented as a
:class:`pyrealm.demography.community.Community` instance. The community is then made up
of size-structured plant cohorts using :class:`pyrealm.demography.community.Cohorts`
instances.
"""  # noqa: D205

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pyrealm.demography.cohorts import Cohorts, create_cohorts
from pyrealm.demography.tmodel import StemAllometry

from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.functional_types import VEFlora


@dataclass
class Community:
    """A representation of a community.

    This replaces the now deprecated pyrealm.demography.community.Community class and is
    a temporary placeholder as we move the plants model over to adopt pyrealm 3.

    """

    # pyrealm 3 HACK - temporary stand-in. The plan is to remove Community completely,
    # have all cohorts at the simulation level and only move to communities for canopy
    # and GPP calculations

    cell_id: int
    cell_area: float
    flora: VEFlora
    cohorts: Cohorts
    stem_allometry: StemAllometry = field(init=False)

    def __post_init__(self):
        """Populates the stem allometry."""
        self.stem_allometry = StemAllometry(self.cohorts)


class PlantCommunities(dict, Mapping[int, Community]):
    """Records the plant community with each grid cell across a simulation.

    A ``PlantCommunities`` instance provides a dictionary mapping each grid cell onto a
    single :class:`pyrealm.demography.community.Community` instance, containing a set of
    :class:`pyrealm.demography.community.Cohorts` instances.

    A class instance must be initialised using :class:`pandas.DataFrame` instance
    containing the required cohort data. Each row in the data frame defines a cohort
    located in one of the cells, so required data frame fields are:

    * the cell id in which the cohort is located (``plant_cohorts_cell_id``),
    * the plant functional type of the cohort (``plant_cohorts_pft``),
    * the number of individuals within the cohort (``plant_cohorts_n``), and
    * the diameter at breast height of the individuals (``plant_cohorts_dbh``).

    The data are validated and then compiled into lists of cohorts keyed by grid cell
    id. The class is a subclass of dictionary, so has the ``__get_item__`` method,
    allowing access to the community for a given cell id using ``plants_inst[cell_id]``.

    .. todo::

        This function will need updating if the grid cell area implementation is changed
        to allow variable cell area .

    Args:
        cohort_data: A data frame containing the initial cohort data.
        flora: A flora containing the plant functional types used in the cohorts.
        grid: The grid for the simulation, providing the area of the grid cells and the
                expected cell ids.
        cohort_id_generator: An iterator providing cohort IDs.
    """

    def __init__(
        self,
        cohort_data: pd.DataFrame,
        flora: VEFlora,
        grid: Grid,
        cohort_id_generator: Iterator,
    ):
        """Initialise the community object.

        Args:
            cohort_data: A pandas dataframe of cohort data.
            flora: A flora object.
            grid: A grid object
            cohort_id_generator: An iterator providing cohort IDs.
        """

        # Validate the data being used to generate the Plants object form a dataframe
        cohort_data_vars = {
            "plant_cohorts_n",
            "plant_cohorts_pft",
            "plant_cohorts_cell_id",
            "plant_cohorts_dbh",
        }
        missing_vars = cohort_data_vars.difference(cohort_data.columns)

        if missing_vars:
            msg = (
                f"Cannot initialise plant communities from cohort data. Missing "
                f"variables: {', '.join(sorted(list(missing_vars)))}"
            )
            LOGGER.critical(msg)
            raise ValueError(msg)

        # Split data into cell ids:
        cohort_data_grouped = cohort_data.groupby("plant_cohorts_cell_id")

        # Check the grid cell ids are known
        bad_cids = set(cohort_data_grouped.groups.keys()).difference(grid.cell_id)

        if bad_cids:
            msg = (
                "Plant cohort data includes cell ids not in grid definition: "
                + ",".join([str(c) for c in bad_cids])
            )
            LOGGER.critical(msg)
            raise ValueError(msg)

        # Check the PFTs are known
        bad_pfts = set(cohort_data["plant_cohorts_pft"]).difference(flora.name)
        if bad_pfts:
            msg = "Plant cohort data includes PFT names not in flora: " + ",".join(
                bad_pfts
            )
            LOGGER.critical(msg)
            raise ValueError(msg)

        # Now build the pyrealm community objects for each cell
        communities = {k: v for k, v in cohort_data_grouped}

        for cell_id in grid.cell_id:
            if cell_id in communities:
                # Build cohorts object with provided data
                cell_cohort_data = communities[cell_id]
                cohorts = create_cohorts(
                    flora=flora,
                    cid_generator=cohort_id_generator,
                    dbh_value=cell_cohort_data["plant_cohorts_dbh"].to_numpy(),
                    pft_name=cell_cohort_data["plant_cohorts_pft"].to_numpy(),
                    n_individuals=cell_cohort_data["plant_cohorts_n"].to_numpy(),
                )
            else:
                # Empty cohorts object
                cohorts = create_cohorts(
                    flora=flora,
                    cid_generator=cohort_id_generator,
                    dbh_value=np.array([]),
                    pft_name=np.array([]),
                    n_individuals=np.array([]),
                )

            self[cell_id] = Community(
                cell_id=cell_id,
                cell_area=grid.cell_area,  # Note this is constant
                flora=flora,
                cohorts=cohorts,
            )

        LOGGER.info("Plant cohort data loaded")
