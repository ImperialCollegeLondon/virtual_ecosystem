"""The :mod:`~virtual_rainforest.models.plants.functions` submodule provides the core
functions used to estimate the canopy model, productivity and growth.

NOTE - much of this will be outsourced to pyrealm.

"""  # noqa: D205, D415

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.plants.community import PlantCohort, PlantCommunities


def generate_canopy_model(
    community: list[PlantCohort], max_layers: int
) -> tuple[NDArray, NDArray]:
    """Generate the canopy structure for a plant community.

    This function takes a list of plant cohorts present in a community and uses the T
    Model to estimate the heights and crown areas of the individuals. It then uses the
    perfect plasticity approximation to calculate the closure heights of the canopy
    layers and the leaf area indices of each layer. These are returned as one
    dimensional arrays, right padded with ``np.nan`` to the provided maximum number of
    layers.

    Args:
        community: A list of plant cohorts.
        max_layers: The maximum number of permitted canopy layers.

    Returns:
        One dimensional numpy arrays giving the canopy layer heights and leaf area
        indices.

    Raises:
        ConfigurationError: where the actual canopy layers exceed the provided maximum
    """

    # TODO - actually calculate these
    layer_hght = np.array([30.0, 20.0, 10.0])
    layer_lai = np.array([1.0, 1.0, 1.0])

    # Check the number of layers and right pad to the maximum number of layers if needed
    n_pad = len(layer_hght) - max_layers

    if n_pad < 0:
        msg = "Generated canopy has more layers than the configured maximum."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    if n_pad > 0:
        layer_hght = np.pad(layer_hght, (0, n_pad), "constant", constant_values=np.nan)
        layer_lai = np.pad(layer_lai, (0, n_pad), "constant", constant_values=np.nan)

    return layer_hght, layer_lai


def build_canopy_arrays(
    communities: PlantCommunities, n_canopy_layers: int, n_soil_layers: int
) -> tuple[DataArray, DataArray]:
    """Converts the PlantCommunities data into canopy layer data arrays."""

    # TODO - this could be a method of PlantCommunities. Needs to avoid circular import
    # of PlantCohorts

    # TODO make this do something

    return DataArray(np.arange(1)), DataArray(np.arange(1))


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
