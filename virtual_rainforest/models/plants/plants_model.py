"""The :mod:`~virtual_rainforest.models.plants.plants_model` module creates
:class:`~virtual_rainforest.models.plants.plants_model.PlantsModel` class as a child of
the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

# import numpy as np
# from numpy.typing import NDArray
from pint import Quantity

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data

# from virtual_rainforest.core.config import Config
# from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import check_valid_constant_names
from virtual_rainforest.models.plants.constants import PlantsConsts
from virtual_rainforest.models.plants.functional_types import PlantFunctionalTypes

# from xarray import DataArray


class PlantsModel(BaseModel):
    """A class defining the plants model.

    This is currently a basic placeholder to define the main interfaces between the
    plants model and other models.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        constants: Set of constants for the soil model.
    """

    model_name = "plants"
    """An internal name used to register the model and schema"""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that plants model can sensibly capture."""
    upper_bound_on_time_scale = "1 year"
    """Longest time scale that plants model can sensibly capture."""
    required_init_vars = (("initial_plant_communities", ("spatial",)),)
    """Required initialisation variables for the plants model.

    This is the set of variables and their core axes that are required in the data
    object to create a PlantsModel instance."""

    required_update_vars = (
        ("vapour_pressure_deficit", ("spatial",)),
        ("air_temperature", ("spatial",)),
        ("atmospheric_co2", ("spatial",)),
        ("atmospheric_pressure", ("spatial",)),
        ("ppfd", ("spatial",)),
        ("fapar", ("spatial",)),
    )
    """Required initialisation variables to update PlantsModel.

    NOTE - this is just a placeholder at the moment. This is not a valid BaseModel
    attribute. """

    vars_updated = (
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "herbivory",
    )
    """Variables updated by the plants model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        plant_functional_types: PlantFunctionalTypes,
        constants: PlantsConsts,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        # TODO - Check data bounding

        self.constants = constants
        """Set of constants for the plants model"""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> PlantsModel:
        """Factory function to initialise a plants model from configuration.

        This function returns a PlantsModel instance based on the provided configuration
        and data, raising an exception if the configuration is invalid.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: A validated :class:`~virtual_rainforest.core.config.Config`
                instance.
            update_interval: Frequency with which all models are updated
        """

        # Check if any constants have been supplied
        if "plants" in config and "constants" in config["plants"]:
            # Checks that constants is config are as expected
            check_valid_constant_names(config, "plants", "PlantsConsts")
            # If an error isn't raised then generate the dataclass
            constants = PlantsConsts(**config["soil"]["constants"]["SoilConsts"])
        else:
            # If no constants are supplied then the defaults should be used
            constants = PlantsConsts()

        # Generate the plant functional types
        pfts = PlantFunctionalTypes.from_config(config=config)

        # Try and create the instance - safeguard against exceptions
        try:
            inst = cls(data, update_interval, pfts, constants)
        except Exception as excep:
            LOGGER.critical(
                f"Error creating plants model from configuration: {str(excep)}"
            )

        LOGGER.info("Plants model instance generated from configuration.")
        return inst

    def setup(self) -> None:
        """Set up a PlantsModel instance.

        This function takes the input data for a plants model instance and calculates
        the initial canopy structure from the plant functional type and community data.
        """

        pass

    def spinup(self) -> None:
        """Placeholder function to spin up the plants model."""

    def update(self, time_index: int) -> None:
        """Update the plants model.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        # Update the layers
        pass

    def cleanup(self) -> None:
        """Placeholder function for plants model cleanup."""
