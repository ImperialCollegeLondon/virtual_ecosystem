"""This is a placeholder for the AbioticSimpleModel and includes only functions called
elsewhere.
"""  # noqa: D205, D415

from typing import List


def set_layer_roles(canopy_layers: int, soil_layers: int) -> List[str]:
    """Create a list of layer roles.

    This function creates a list of layer roles for the vertical dimension of the
    Virtual Rainforest. The layer above the canopy is defined as 0 (canopy height + 2m)
    and the index increases towards the bottom of the soil column. The canopy includes
    a maximum number of canopy layers (defined in config) which are filled from the top
    with canopy node heights from the plant module (the rest is set to NaN). Below the
    canopy, we currently set one subcanopy layer (around 1.5m above ground) and one
    surface layer (0.1 m above ground). Below ground, we include a maximum number of
    soil layers (defined in config); the deepest layer is currently set to 1 m as the
    temperature there is fairly constant and equals the mean annual temperature.

    Args:
        canopy_layers: number of canopy layers
        soil_layers: number of soil layers

    Returns:
        List of canopy layer roles
    """
    return (
        ["above"]
        + ["canopy"] * canopy_layers
        + ["subcanopy"]
        + ["surface"]
        + ["soil"] * soil_layers
    )
