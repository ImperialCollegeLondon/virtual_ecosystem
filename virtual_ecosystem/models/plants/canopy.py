"""The :mod:`~virtual_ecosystem.models.plants.canopy` submodule provides functionality
to initialise the canopy layer data held in the simulation
:class:`~virtual_ecosystem.core.data.Data` instance and to generate
:class:`~pyrealm.demography.canopy.Canopy` instances from the plant community data
within each grid cell.
"""  # noqa: D205

from __future__ import annotations

from pyrealm.demography.canopy import Canopy
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.plants.communities import PlantCommunities


def initialise_canopy_layers(
    data: Data, layer_structure: LayerStructure
) -> dict[str, DataArray]:
    """Initialise the canopy layer height and leaf area index data.

    This function initialises the following data arrays describing the plant canopy
    structure and soil layer structure within a Data object: ``layer_heights``,
    ``leaf_area_index``, ``layer_fapar``, ``layer_leaf_mass`` and
    ``shortwave_absorption``.

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
        "shortwave_absorption",
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
    layers: dict[str, DataArray] = dict()
    for each_layer_name in layers_to_create:
        layers[each_layer_name] = layer_structure.from_template()

    # Initialise the fixed layer heights
    # TODO: See issue #442 about centralising the layer_heights variable initialisation
    layers["layer_heights"].loc[dict(layers=layer_structure.index_all_soil)] = (
        layer_structure.soil_layer_depths.reshape(-1, 1)
    )

    layers["layer_heights"].loc[dict(layers=layer_structure.index_surface)] = (
        layer_structure.surface_layer_height
    )

    return layers


def calculate_canopies(
    communities: PlantCommunities, max_canopy_layers: int
) -> dict[int, Canopy]:
    """Calculate the canopy structure of communities.

    This function takes a PlantCommunities object and calculates the canopy
    representation for each community, using the perfect plasticity approximation to
    calculate the closure heights of the canopy layers.

    Args:
        communities: The PlantCommunities object to convert
        max_canopy_layers: The maximum number of permitted canopy layers

    Returns:
        A dictionary of :class:`pyrealm.demography.canopy.Canopy` instances, keyed by
        grid cell id. There is a one-to-one mapping of canopy representations to grid
        cells.
    """

    # TODO - this could be a method of PlantCommunities but creates circular import of
    #        PlantCohorts

    # TODO - maybe return dict[str, NDArray] as the number of layers is only going to
    #        increase with the need for more resources and cohort data.

    # Loop over the communities in each cell
    canopies: dict[int, Canopy] = {}
    for cell_id, community in communities.items():
        # Calculate the PPA canopy model for the community in the cell
        canopies[cell_id] = Canopy(community, fit_ppa=True)

        # Fail if canopy representation has more layers than the configuration.
        n_canopy_layers = canopies[cell_id].heights.size
        if max_canopy_layers < n_canopy_layers:
            msg = (
                f"Canopy representation for the plant community in cell "
                f"{cell_id} has {n_canopy_layers} layers, "
                f"configured maximum is {max_canopy_layers}"
            )
            LOGGER.critical(msg)
            raise RuntimeError(msg)

    return canopies
