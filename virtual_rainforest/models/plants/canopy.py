"""The :mod:`~virtual_rainforest.models.plants.canopy` submodule provides the core
functions used to estimate the canopy model, productivity and growth.

NOTE - much of this will be outsourced to pyrealm.

"""  # noqa: D205, D415

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.plants.community import PlantCohort, PlantCommunities


def generate_canopy_model(community: list[PlantCohort]) -> tuple[NDArray, NDArray]:
    """Generate the canopy structure for a plant community.

    This function takes a list of plant cohorts present in a community and uses the T
    Model to estimate the heights and crown areas of the individuals. It then uses the
    perfect plasticity approximation to calculate the closure heights of the canopy
    layers and the leaf area indices of each layer.

    Warning:
        This function defines the API for generating canopy models but currently returns
        constant values for all inputs.

    Args:
        community: A list of plant cohorts.

    Returns:
        A tuple of one dimensional numpy arrays giving the canopy layer heights and leaf
        area indices.
    """

    # TODO - actually calculate these
    layer_hght = np.array([30.0, 20.0, 10.0])
    layer_lai = np.array([1.0, 1.0, 1.0])

    return layer_hght, layer_lai


def build_canopy_arrays(
    communities: PlantCommunities, n_canopy_layers: int
) -> tuple[DataArray, DataArray]:
    """Converts the PlantCommunities data into canopy layer data arrays.

    This function takes a list of plant cohorts present in a community and uses the T
    Model to estimate the heights and crown areas of the individuals. It then uses the
    perfect plasticity approximation to calculate the closure heights of the canopy
    layers and the leaf area indices of each layer.

    Args:
        communities: The PlantCommunities object to convert
        n_canopy_layers: The maximum number of permitted canopy layers.

    Returns:
        A tuple of two dimensional numpy arrays giving the canopy layer heights and leaf
        area indices by cell id.
    """

    # TODO - this could be a method of PlantCommunities but creates circular import of
    #        PlantCohorts

    # Initialise list of arrays
    layer_heights: list = []
    layer_lai: list = []
    cell_has_too_many_layers: list = []

    # Loop over the communities in each cell
    for cell_id, community in communities.items():
        # Calculate the canopy model for the cell and pad as needed
        this_lyr_hght, this_lyr_lai = generate_canopy_model(community)
        n_pad = n_canopy_layers - len(this_lyr_hght)

        if n_pad < 0:
            cell_has_too_many_layers.append(cell_id)
            continue

        if n_pad > 0:
            this_lyr_hght = np.pad(
                this_lyr_hght, (0, n_pad), "constant", constant_values=np.nan
            )
            this_lyr_lai = np.pad(
                this_lyr_lai, (0, n_pad), "constant", constant_values=np.nan
            )

        layer_heights.append(this_lyr_hght)
        layer_lai.append(this_lyr_lai)

    # Bail if any cells had too many canopy layers
    if cell_has_too_many_layers:
        msg = (
            f"Generated canopy has more layers than the configured maximum in "
            f"cells: {','.join([str(v) for v in cell_has_too_many_layers])}."
        )
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # Combine into arrays
    return np.stack(layer_heights, axis=1), np.stack(layer_lai, axis=1)


def initialise_canopy_layers(
    data: Data, n_canopy_layers: int, n_soil_layers: int
) -> Data:
    """Initialise the canopy layer height and leaf area index data.

    This function initialises ``layer_heights`` and ``leaf_area_index`` data arrays
    describing the plant canopy structure and soil layer structure within a Data object.

    Args:
        data: A Data object to update.
        n_canopy_layers: The maximum number of permitted canopy layers.
        n_soil_layers: The number of soil layers to be used.

    Returns:
        A data object with the layers added.

    Raises:
        InitialisationError: if the layers already exist in the data object
    """

    # TODO - maybe this should happen somewhere before models start to be defined?
    #        The other models rely on it

    # Check that layers do not already exist
    if ("leaf_area_index" in data) or ("layer_heights" in data):
        msg = "Cannot initialise canopy layers, already present"
        LOGGER.critical(msg)
        raise InitialisationError(msg)

    # TODO - These layer roles desperately need to be set up in _one_ place!
    layer_roles = set_layer_roles(n_canopy_layers, n_soil_layers)
    layer_shape = (len(layer_roles), data.grid.n_cells)

    # Set the layers
    data["leaf_area_index"] = DataArray(
        data=np.full(layer_shape, fill_value=np.nan),
        coords={
            "layer": np.arange(len(layer_roles)),
            "cell_id": data.grid.cell_id,
        },
    )
    data["layer_heights"] = DataArray(
        data=np.full(layer_shape, fill_value=np.nan),
        coords={
            "layer": np.arange(len(layer_roles)),
            "cell_id": data.grid.cell_id,
        },
    )

    return data


# # Estimate
# self.gpp = estimate_gpp(
#     temperature=self.data["temperature"],
#     atmospheric_co2=self.data["atmospheric_co2"],
#     vapour_pressure_deficit=self.data["vapour_pressure_deficit"],
#     atmospheric_pressure=self.data["atmospheric_pressure"],
#     ppfd=self.data["ppfd"],
#     canopy_model=self.canopy_model,
#     pfts=self.pfts,
# )

# self.delta_dbh = estimate_growth(
#     gpp=self.gpp, cohort_dbh=self.dbh, pfts=self.pfts
# )
