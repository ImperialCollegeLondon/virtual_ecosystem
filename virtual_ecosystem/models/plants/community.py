"""The :mod:`~virtual_ecosystem.models.plants.community` submodule contains
functionality to generate a dictionary of
:class:`~pyrealm.demography.community.Community` instances for each grid cell, populated
with size-structured :class:`~pyrealm.demography.community.Cohort` instances from
initial plant cohort inventories for a simulation.
"""  # noqa: D205

from collections.abc import Mapping

from pyrealm.demography.community import Cohorts, Community
from pyrealm.demography.flora import Flora

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.utils import split_arrays_by_grouping_variable


class PlantCommunities(dict, Mapping[int, Community]):
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
        grid: The grid for the simulation, providing the area of the grid cells.
    """

    def __init__(self, data: Data, flora: Flora, grid: Grid):
        """Initialise the community object.

        Args:
            data: A data object.
            flora: A flora object.
            grid: A grid object
        """
        # Validate the data being used to generate the Plants object form a dataframe
        cohort_data_vars = [
            "plant_cohorts_n",
            "plant_cohorts_pft",
            "plant_cohorts_cell_id",
            "plant_cohorts_dbh",
        ]

        is_df, msg = data.confirm_variables_form_data_frame(cohort_data_vars)

        if not is_df:
            msg = "Cannot initialise plant communities. " + msg
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

        bad_pft = set(data["plant_cohorts_pft"].data).difference(flora.name)
        if bad_pft:
            msg = f"Plant cohort PFTs ids not in configured PFTs: {','.join(bad_pft)}"
            LOGGER.critical(msg)
            raise ValueError(msg)

        # Split data into cell ids:
        cohort_data_by_cell_id = split_arrays_by_grouping_variable(
            arrays=[
                data["plant_cohorts_n"].to_numpy(),
                data["plant_cohorts_pft"].to_numpy(),
                data["plant_cohorts_dbh"].to_numpy(),
            ],
            group_by=data["plant_cohorts_cell_id"].to_numpy(),
        )

        # Now build the pyrealm community objects for each cell
        # TODO - note that this needs fixing if cell area is not constant.
        for cell_id, cell_cohort_data in cohort_data_by_cell_id.items():
            self[cell_id] = Community(
                cell_id=cell_id,
                cell_area=grid.cell_area,
                flora=flora,
                cohorts=Cohorts(
                    n_individuals=cell_cohort_data[0],
                    pft_names=cell_cohort_data[1],
                    dbh_values=cell_cohort_data[2],
                ),
            )

        LOGGER.info("Plant cohort data loaded")
