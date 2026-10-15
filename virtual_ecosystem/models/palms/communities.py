"""The :mod:`~virtual_ecosystem.models.palms.communities` submodule  provides the
:class:`~virtual_ecosystem.models.palms.communities.PalmCommunities` class. This
provides a dictionary mapping each grid cell id to the palm community growing within
the cell.

There is a one-to-one mapping of grid cells to palm communities, with the individual
community for a grid cell being represented as a :class:`PalmCommunity` instance. The
community is then made up of size-structured palm cohorts using
:class:`pyrealm.demography.cohorts.Cohorts` instances.

Unlike the tree communities in :mod:`~virtual_ecosystem.models.plants.communities`,
palm cohorts take both a diameter at breast height (DBH) and a stem height as initial
cohort inputs. Growth in mature palms is expressed almost entirely as an increase in
stem height, so ``dbh_value`` is expected to remain fixed for a cohort once set here,
while ``stem_height_value`` is the value updated by growth. Both are stored as
ordinary columns on the :class:`pyrealm.demography.cohorts.Cohorts` instance, since
:func:`pyrealm.demography.cohorts.create_cohorts` already requires a strictly positive
``dbh_value`` for every cohort.
"""  # noqa: D205

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pyrealm.demography.cohorts import Cohorts, create_cohorts
from pyrealm.demography.flora import Flora

from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.palms.palms import StemAllometry


def validate_cohort_data(
    cohort_data: pd.DataFrame,
    flora: Flora,
    grid: Grid,
) -> pd.DataFrame:
    """Validate input palm cohort data and map coordinates onto grid cells.

    Cohort coordinates must fall within exactly one grid cell. PFT names must be
    present in the configured flora, individual counts must be non-negative integers,
    and DBH and stem height values must be strictly positive numbers.

    Args:
        cohort_data: A pandas dataframe of palm cohort data.
        flora: A flora object.
        grid: A grid object.

    Returns:
        The validated cohort data with an internal ``palm_cohorts_cell_id`` column.

    Raises:
        InitialisationError: If required fields or cohort values are invalid.
    """

    cohort_data_vars = {
        "palm_cohorts_n",
        "palm_cohorts_pft",
        "palm_cohorts_x",
        "palm_cohorts_y",
        "palm_cohorts_dbh",
        "palm_cohorts_stem_height",
    }
    missing_vars = cohort_data_vars.difference(cohort_data.columns)

    if missing_vars:
        msg = (
            f"Cannot initialise palm communities from cohort data. Missing "
            f"variables: {', '.join(sorted(missing_vars))}"
        )
        LOGGER.critical(msg)
        raise InitialisationError(msg)

    validation_ok = True

    cell_ids = grid.map_xy_to_cell_id(
        x_coords=cohort_data["palm_cohorts_x"].to_numpy(),
        y_coords=cohort_data["palm_cohorts_y"].to_numpy(),
    )
    n_cell_ids = {len(cell_id) for cell_id in cell_ids}

    if 0 in n_cell_ids:
        validation_ok = False
        LOGGER.error("XY coordinates in palm cohort data fall outside grid bounds")

    if any(n_cells > 1 for n_cells in n_cell_ids):
        validation_ok = False
        LOGGER.error("XY coordinates in palm cohort data fall on cell boundaries")

    if validation_ok:
        cohort_data["palm_cohorts_cell_id"] = [
            cell_id for mapped_cells in cell_ids for cell_id in mapped_cells
        ]

    bad_pfts = set(cohort_data["palm_cohorts_pft"]).difference(flora.pft_name)
    if bad_pfts:
        validation_ok = False
        LOGGER.error(
            "Palm cohort data includes PFT names not in flora: " + ",".join(bad_pfts)
        )

    if (not np.issubdtype(cohort_data["palm_cohorts_n"].dtype, np.integer)) or (
        np.any(cohort_data["palm_cohorts_n"] < 0)
    ):
        validation_ok = False
        LOGGER.error("Palm cohort data individual counts must be positive integers")

    if (not np.issubdtype(cohort_data["palm_cohorts_dbh"].dtype, np.number)) or (
        np.any(cohort_data["palm_cohorts_dbh"] <= 0)
    ):
        validation_ok = False
        LOGGER.error("Palm cohort DBH data must be strictly positive")

    if (
        not np.issubdtype(cohort_data["palm_cohorts_stem_height"].dtype, np.number)
    ) or np.any(cohort_data["palm_cohorts_stem_height"] <= 0):
        validation_ok = False
        LOGGER.error("Palm cohort stem height data must be strictly positive")

    if not validation_ok:
        LOGGER.critical("Validation errors in palm cohort data: see above")
        raise InitialisationError("Validation errors in palm cohort data: check log")

    LOGGER.info("Palm cohort data validated")
    return cohort_data


@dataclass
class PalmCommunity:
    """A representation of a palm community.

    This mirrors :class:`virtual_ecosystem.models.plants.communities.Community`, but
    is kept as a distinct class so that palm-specific behaviour can diverge from the
    tree community representation without affecting the plants model.
    """

    cell_id: int
    cell_area: float
    flora: Flora
    cohorts: Cohorts
    stem_allometry: StemAllometry = field(init=False)

    def __post_init__(self):
        """Populates the stem allometry."""
        self.stem_allometry = StemAllometry(self.cohorts)


class PalmCommunities(dict, Mapping[int, PalmCommunity]):
    """Records the palm community with each grid cell across a simulation.

    A ``PalmCommunities`` instance provides a dictionary mapping each grid cell onto a
    single :class:`PalmCommunity` instance, containing a set of
    :class:`pyrealm.demography.cohorts.Cohorts` instances.

    A class instance must be initialised using :class:`pandas.DataFrame` instance
    containing the required cohort data. Each row in the data frame defines a cohort
    located in one of the cells, so required data frame fields are:

        * the x and y coordinates of the cohort (``palm_cohorts_x`` and
            ``palm_cohorts_y``),
    * the plant functional type of the cohort (``palm_cohorts_pft``),
    * the number of individuals within the cohort (``palm_cohorts_n``),
    * the diameter at breast height of the individuals (``palm_cohorts_dbh``), and
    * the stem height of the individuals (``palm_cohorts_stem_height``).

    The data are validated and then compiled into lists of cohorts keyed by grid cell
    id. The class is a subclass of dictionary, so has the ``__get_item__`` method,
    allowing access to the community for a given cell id using ``palms_inst[cell_id]``.

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

        cohort_data = validate_cohort_data(
            cohort_data=cohort_data,
            flora=flora,
            grid=grid,
        )

        cohort_data_grouped = cohort_data.groupby("palm_cohorts_cell_id")

        # Now build the pyrealm community objects for each cell
        communities = {k: v for k, v in cohort_data_grouped}

        for cell_id in grid.cell_id:
            if cell_id in communities:
                # Build cohorts object with provided data
                cell_cohort_data = communities[cell_id]
                cohorts = create_cohorts(
                    flora=flora,
                    cid_generator=cohort_id_generator,
                    dbh_value=cell_cohort_data["palm_cohorts_dbh"].to_numpy(),
                    pft_name=cell_cohort_data["palm_cohorts_pft"].to_numpy(),
                    n_individuals=cell_cohort_data["palm_cohorts_n"].to_numpy(),
                )
                cohorts["stem_height_value"] = cell_cohort_data[
                    "palm_cohorts_stem_height"
                ].to_numpy()
            else:
                # Empty cohorts object
                cohorts = create_cohorts(
                    flora=flora,
                    cid_generator=cohort_id_generator,
                    dbh_value=np.array([]),
                    pft_name=np.array([]),
                    n_individuals=np.array([]),
                )
                cohorts["stem_height_value"] = np.array([])

            self[cell_id] = PalmCommunity(
                cell_id=cell_id,
                cell_area=grid.cell_area,  # Note this is constant
                flora=flora,
                cohorts=cohorts,
            )

        LOGGER.info("Palm cohort data loaded")
