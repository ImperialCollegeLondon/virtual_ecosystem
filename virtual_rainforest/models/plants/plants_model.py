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
from virtual_rainforest.models.plants.community import PlantCommunities
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
        plant_functional_types: A set of plant functional types to be used in the model.
        constants: Set of constants for the plants model.
    """

    model_name = "plants"
    """An internal name used to register the model and schema"""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that plants model can sensibly capture."""
    upper_bound_on_time_scale = "1 year"
    """Longest time scale that plants model can sensibly capture."""
    required_init_vars = (
        ("plant_cohorts_cell_id", tuple()),
        ("plant_cohorts_pft", tuple()),
        ("plant_cohorts_n", tuple()),
        ("plant_cohorts_dbh", tuple()),
    )
    """Required initialisation variables for the plants model.

    This is the set of variables and their core axes that are required in the data
    object to create a PlantsModel instance. Four variables are used to set the initial
    plant cohorts used in the model:

    * ``plant_cohorts_cell_id``: The grid cell id containing the cohort
    * ``plant_cohorts_pft``: The plant functional type of the cohort
    * ``plant_cohorts_n``: The number of individuals in the cohort
    * ``plant_cohorts_dbh``: The diameter at breast height of the individuals.
    """

    # TODO - think about a shared "plant cohort" core axis that defines these, but the
    #        issue here is that the length of this is variable.

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

        # Save the class attributes
        self.pfts = plant_functional_types
        """The plant functional types used in the plants model."""
        self.constants = constants
        """Set of constants for the plants model"""

        self.communities = PlantCommunities(data, self.pfts)
        """Initialise the plant communities from the data object."""

        # TODO - initialise the canopy model

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
        """Placeholder function to set up the plants model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the plants model."""

    def update(self, time_index: int) -> None:
        """Update the plants model.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        # TODO - estimate gpp
        # TODO - estimate growth
        # TODO - recalculate canopy model

    def cleanup(self) -> None:
        """Placeholder function for plants model cleanup."""