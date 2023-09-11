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
    layer_heights = np.array([30.0, 20.0, 10.0])
    layer_leaf_area_indices = np.array([1.0, 1.0, 1.0])

    return layer_heights, layer_leaf_area_indices


def build_canopy_arrays(
    communities: PlantCommunities, n_canopy_layers: int
) -> tuple[NDArray, NDArray]:
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
    layer_heights: list[NDArray[np.float32]] = []
    layer_leaf_area_index: list[NDArray[np.float32]] = []
    cell_has_too_many_layers: list[int] = []

    # Loop over the communities in each cell
    for cell_id, community in communities.items():
        # Calculate the canopy model for the community in the cell and pad as needed
        this_layer_height, this_layer_leaf_area_index = generate_canopy_model(community)
        n_pad = n_canopy_layers - len(this_layer_height)

        if n_pad < 0:
            cell_has_too_many_layers.append(cell_id)
            continue

        if n_pad > 0:
            this_layer_height = np.pad(
                this_layer_height, (0, n_pad), "constant", constant_values=np.nan
            )
            this_layer_leaf_area_index = np.pad(
                this_layer_leaf_area_index,
                (0, n_pad),
                "constant",
                constant_values=np.nan,
            )

        layer_heights.append(this_layer_height)
        layer_leaf_area_index.append(this_layer_leaf_area_index)

    # Bail if any cells had too many canopy layers
    if cell_has_too_many_layers:
        msg = (
            "Generated canopy has more layers than the configured maximum in "
            f"cells: {','.join(str(v) for v in cell_has_too_many_layers)}."
        )
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # Combine into arrays
    return np.stack(layer_heights, axis=1), np.stack(layer_leaf_area_index, axis=1)


def initialise_canopy_layers(
    data: Data, n_canopy_layers: int, soil_layers: list[float]
) -> Data:
    """Initialise the canopy layer height and leaf area index data.

    This function initialises ``layer_heights`` and ``leaf_area_index`` data arrays
    describing the plant canopy structure and soil layer structure within a Data object.

    Args:
        data: A Data object to update.
        n_canopy_layers: The maximum number of permitted canopy layers.
        soil_layers: A list of soil layer depths to be used.

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
    layer_roles = set_layer_roles(n_canopy_layers, soil_layers)
    layer_shape = (len(layer_roles), data.grid.n_cells)

    # Set the layers
    data["leaf_area_index"] = DataArray(
        data=np.full(layer_shape, fill_value=np.nan),
        dims=("layers", "cell_id"),
        coords={
            "layers": np.arange(len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
            "cell_id": data.grid.cell_id,
        },
    )
    data["layer_heights"] = DataArray(
        data=np.full(layer_shape, fill_value=np.nan),
        dims=("layers", "cell_id"),
        coords={
            "layers": np.arange(len(layer_roles)),
            "layer_roles": ("layers", layer_roles),
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
