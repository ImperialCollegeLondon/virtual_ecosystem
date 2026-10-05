"""The :mod:`~virtual_ecosystem.models.plants.communities` submodule  provides the
:class:`~virtual_ecosystem.models.plants.communities.PlantCommunities` class. This
provides a dictionary mapping each grid cell id to the  plant community growing within
the cell.

There is a one-to-one mapping of grid cells to plant communities, with the individual
community for a grid cell being represented as a :class:`Community` instance. The
community is then made up of size-structured plant cohorts using
:class:`pyrealm.demography.cohorts.Cohorts` instances.
"""  # noqa: D205

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pyrealm.demography.cohorts import Cohorts, create_cohorts
from pyrealm.demography.flora import Flora
from pyrealm.demography.tmodel import StemAllometry

from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER


def validate_cohort_data(
    cohort_data: pd.DataFrame,
    flora: Flora,
    grid: Grid,
) -> pd.DataFrame:
    """Validate the input plant cohort data.

    This function validates the data in the plant cohort definitions dataframe. It
    checks that:

    * Cohort x and y coordinates fall within the simulation grid and fall within a
      single cell rather than on cell boundaries.
    * The cohort PFT names are all included in the simulation flora
    * That the number of individuals are positive integers
    * That diameter at breast height (DBH) values are strictly positive numbers.

    Args:
        cohort_data: A pandas dataframe of cohort data.
        flora: A flora object.
        grid: A grid object
    """

    # Validate the data being used to generate the Plants object form a dataframe
    cohort_data_vars = {
        "plant_cohorts_n",
        "plant_cohorts_pft",
        "plant_cohorts_x",
        "plant_cohorts_y",
        "plant_cohorts_dbh",
    }
    missing_vars = cohort_data_vars.difference(cohort_data.columns)

    if missing_vars:
        msg = (
            f"Cannot initialise plant communities from cohort data. Missing "
            f"variables: {', '.join(sorted(list(missing_vars)))}"
        )
        LOGGER.critical(msg)
        raise InitialisationError(msg)

    # Canary variable for validation failure - might as well run all tests
    validation_ok = True

    # Map coordinates onto grid ids.
    cell_ids = grid.map_xy_to_cell_id(
        x_coords=cohort_data["plant_cohorts_x"].to_numpy(),
        y_coords=cohort_data["plant_cohorts_y"].to_numpy(),
    )

    # Test for 1 to 1 mapping of XY coords to cell ids
    n_cell_ids: set[int] = {len(x) for x in cell_ids}

    if 0 in n_cell_ids:
        validation_ok = False
        LOGGER.error("XY coordinates in plant cohort data fall outside grid bounds")

    if any([v > 1 for v in n_cell_ids]):
        validation_ok = False
        LOGGER.error("XY coordinates in plant cohort data fall on cell boundaries")

    if validation_ok:
        # Add unique cell ids to data frame
        cohort_data["plant_cohorts_cell_id"] = [id for row in cell_ids for id in row]

    # Check the PFTs are known
    bad_pfts = set(cohort_data["plant_cohorts_pft"]).difference(flora.pft_name)
    if bad_pfts:
        validation_ok = False
        LOGGER.error(
            "Plant cohort data includes PFT names not in flora: " + ",".join(bad_pfts)
        )

    # Check n_individuals is positive integer
    if (not np.issubdtype(cohort_data["plant_cohorts_n"].dtype, np.integer)) or (
        np.any(cohort_data["plant_cohorts_n"] <= 0)
    ):
        validation_ok = False
        LOGGER.error("Plant cohort data individual counts must be positive integers")

    # Check DBH is strictly positive - could be integer but would be odd.
    if (not np.issubdtype(cohort_data["plant_cohorts_dbh"].dtype, np.number)) or (
        np.any(cohort_data["plant_cohorts_dbh"] <= 0)
    ):
        validation_ok = False
        LOGGER.error("Plant cohort DBH data must be strictly positive")

    if not validation_ok:
        LOGGER.critical("Validation errors in plant cohort data: see above")
        raise InitialisationError("Validation errors in plant cohort data: check log")

    LOGGER.info("Plant cohort data validated")

    return cohort_data


@dataclass
class Community:
    """A representation of a community.

    This replaces the now deprecated pyrealm Community class and is a temporary
    placeholder as we move the plants model over to adopt pyrealm 3.

    """

    # pyrealm 3 HACK - temporary stand-in. The plan is to remove Community completely,
    # have all cohorts at the simulation level and only move to communities for canopy
    # and GPP calculations

    cell_id: int
    cell_area: float
    flora: Flora
    cohorts: Cohorts
    stem_allometry: StemAllometry = field(init=False)

    def __post_init__(self):
        """Populates the stem allometry."""
        self.stem_allometry = StemAllometry(self.cohorts)


class PlantCommunities(dict, Mapping[int, Community]):
    """Records the plant community with each grid cell across a simulation.

    A ``PlantCommunities`` instance provides a dictionary mapping each grid cell onto a
    single :class:`Community` instance, containing a set of
    :class:`pyrealm.demography.cohorts.Cohorts` instances.

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
        flora: Flora,
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

        # Validate the inputs
        cohort_data = validate_cohort_data(
            cohort_data=cohort_data, flora=flora, grid=grid
        )

        # Group data by cell id
        cohort_data_grouped = cohort_data.groupby("plant_cohorts_cell_id")

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
