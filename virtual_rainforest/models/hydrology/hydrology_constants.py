"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_constants` module contains
constants and paratemters for the hydrology model. This is a temporary solution.
"""  # noqa: D205, D415

from typing import Dict

HydrologyParameters: Dict[str, float] = {
    "soil_moisture_capacity": 0.9,
    "water_interception_factor": 0.1,
}
"""Parameters for hydrology model."""

# TODO move bounds to core.bound_checking once that is implemented and introduce method
# to conserve energy and matter
