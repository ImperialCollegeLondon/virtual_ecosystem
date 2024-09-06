"""The :mod:`~virtual_ecosystem.models.plants.canopy` submodule provides the core
functions used to estimate the canopy model.

NOTE - much of this will be outsourced to pyrealm.

"""  # noqa: D205

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.community import PlantCohort, PlantCommunities


def generate_canopy_model(
    community: list[PlantCohort],
) -> tuple[NDArray, NDArray, NDArray, NDArray]:
    """Generate the canopy structure for a plant community.

    This function takes a list of plant cohorts present in a community and uses the T
    Model to estimate the heights and crown areas of the individuals. It then uses the
    perfect plasticity approximation to calculate the closure heights of the canopy
    layers and the leaf area indices of each layer. The last step is then to use the
    Beer-Lambert law to estimate the fraction of absorbed photosynthetically active
    radiation (``fapar``, :math:`f_{APAR}`) for the canopy.

    This function also updates the input community data, by setting the
    :attr:`~virtual_ecosystem.models.plants.community.PlantCohort.canopy_area`
    attribute of each :attr:`~virtual_ecosystem.models.plants.community.PlantCohort`
    object to the area of canopy for that cohort within each of the canopy layers. These
    are then used to calculate the gross primary productivity of each cohort within the
    community.

    Warning:
        This function defines the API for generating canopy models but currently returns
        constant values for all inputs.

    Args:
        community: A list of plant cohorts.

    Returns:
        A tuple of one dimensional numpy arrays giving the layer heights along with the
        leaf area indices, :math:`f_{APAR}` and leaf masses from the canopy model.
    """

    # TODO - actually calculate these and think about whether pyrealm pads to a maximum
    #        canopy layer number.

    # TODO - Need to expose cohort details within the data object in order to allow
    #        animals to target specific PFT, size classes or layers

    # Calculate the canopy area within each layer for each cohort.
    for cohort in community:
        cohort.canopy_area = np.array([5.0, 5.0, 5.0])

    # Calculate the canopy wide summaries
    layer_heights = np.array([30.0, 20.0, 10.0], dtype=np.float32)
    layer_leaf_area_indices = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    layer_fapar = np.array([0.4, 0.2, 0.1], dtype=np.float32)
    layer_leaf_mass = np.array([10000.0, 10000.0, 10000.0], dtype=np.float32)

    return layer_heights, layer_leaf_area_indices, layer_fapar, layer_leaf_mass


def build_canopy_arrays(
    communities: PlantCommunities, n_canopy_layers: int
) -> tuple[NDArray, NDArray, NDArray, NDArray]:
    """Converts the PlantCommunities data into canopy layer data arrays.

    This function takes a list of plant cohorts present in a community and uses the T
    Model to estimate the heights and crown areas of the individuals. It then uses the
    perfect plasticity approximation to calculate the closure heights of the canopy
    layers and the leaf area indices of each layer.

    Args:
        communities: The PlantCommunities object to convert
        n_canopy_layers: The maximum number of permitted canopy layers.

    Returns:
        A tuple of two dimensional numpy arrays giving the canopy layer heights and then
        leaf area indices, :math:`f_{APAR}` and leaf mass by cell id.
    """

    # TODO - this could be a method of PlantCommunities but creates circular import of
    #        PlantCohorts

    # TODO - maybe return dict[str, NDArray] as the number of layers is only going to
    #        increase with the need for more resources and cohort data.

    # Initialise list of arrays
    layer_heights: list[NDArray[np.float32]] = []
    layer_leaf_area_index: list[NDArray[np.float32]] = []
    layer_fapar: list[NDArray[np.float32]] = []
    layer_leaf_mass: list[NDArray[np.float32]] = []
    cell_has_too_many_layers: list[int] = []

    # Loop over the communities in each cell
    for cell_id, community in communities.items():
        # Calculate the canopy model for the community in the cell and pad as needed
        # TODO - note that this allows generate_canopy_model to return different sized
        #        canopy layers, which may not be true, so n_pad may be constant across
        #        communities.
        canopy_layers = list(generate_canopy_model(community))
        n_pad = n_canopy_layers - len(canopy_layers[0])

        # Record cells where the canopy breaks the config
        if n_pad < 0:
            cell_has_too_many_layers.append(cell_id)
            continue

        # If padding is needed, then pad canopy layers and the cohort canopy areas.
        if n_pad > 0:
            for idx, var in enumerate(canopy_layers):
                canopy_layers[idx] = np.pad(
                    var, (0, n_pad), "constant", constant_values=np.nan
                )
            for cohort in community:
                cohort.canopy_area = np.pad(
                    cohort.canopy_area, (0, n_pad), "constant", constant_values=np.nan
                )

        layer_heights.append(canopy_layers[0])
        layer_leaf_area_index.append(canopy_layers[1])
        layer_fapar.append(canopy_layers[2])
        layer_leaf_mass.append(canopy_layers[3])

    # Bail if any cells had too many canopy layers
    if cell_has_too_many_layers:
        msg = (
            "Generated canopy has more layers than the configured maximum in "
            f"cells: {','.join(str(v) for v in cell_has_too_many_layers)}."
        )
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # Combine lists of layers by cell_id into canopy layers x cell_id arrays
    return (
        np.stack(layer_heights, axis=1),
        np.stack(layer_leaf_area_index, axis=1),
        np.stack(layer_fapar, axis=1),
        np.stack(layer_leaf_mass, axis=1),
    )


def initialise_canopy_layers(data: Data, layer_structure: LayerStructure) -> Data:
    """Initialise the canopy layer height and leaf area index data.

    This function initialises the following data arrays describing the plant canopy
    structure and soil layer structure within a Data object: ``layer_heights``,
    ``leaf_area_index``, ``layer_fapar``, ``layer_leaf_mass`` and ``canopy_absorption``.

    Args:
        data: A Data object to update.
        layer_structure: A layer structure object containing the layer configuration

    Returns:
        A data object with the layers added.

    Raises:
        InitialisationError: if the layers already exist in the data object
    """

    # TODO - maybe this should happen somewhere before models start to be defined?
    #        The other models rely on it

    # Check that layers do not already exist
    layers_to_create = (
        "layer_heights",
        "leaf_area_index",
        "layer_fapar",
        "layer_leaf_mass",
        "canopy_absorption",
    )

    layers_found = set(layers_to_create).intersection(data.data.variables)
    if layers_found:
        msg = (
            "Cannot initialise canopy layers, already "
            f"present: {','.join(str(x) for x in layers_found)}"
        )
        LOGGER.critical(msg)
        raise InitialisationError(msg)

    # Initialise a data array for each layer from the layer structure template
    for each_layer_name in layers_to_create:
        data[each_layer_name] = layer_structure.from_template()

    # Initialise the fixed layer heights
    # TODO: See issue #442 about centralising the layer_heights variable initialisation
    data["layer_heights"].loc[dict(layers=layer_structure.index_all_soil)] = (
        layer_structure.soil_layer_depths.reshape(-1, 1)
    )

    data["layer_heights"].loc[dict(layers=layer_structure.index_surface)] = (
        layer_structure.surface_layer_height
    )

    return data
