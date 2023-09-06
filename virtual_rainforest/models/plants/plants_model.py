"""The :mod:`~virtual_rainforest.models.plants.plants_model` module creates
:class:`~virtual_rainforest.models.plants.plants_model.PlantsModel` class as a child of
the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import numpy as np
from pint import Quantity

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.constants import load_constants
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.plants.canopy import (
    build_canopy_arrays,
    initialise_canopy_layers,
)
from virtual_rainforest.models.plants.community import PlantCommunities
from virtual_rainforest.models.plants.constants import PlantsConsts
from virtual_rainforest.models.plants.functional_types import Flora

# from virtual_rainforest.core.config import Config


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
    * ``plant_cohorts_dbh``: The diameter at breast height of the individuals in metres.
    """

    # TODO - think about a shared "plant cohort" core axis that defines these, but the
    #        issue here is that the length of this is variable.

    vars_updated = (
        "leaf_area_index",  # NOTE - LAI is integrated into the full layer roles
        "layer_heights",  # NOTE - includes soil, canopy and above canopy heights
        "layer_fapar",
        "herbivory",
        "transpiration",
        "canopy_evaporation",
    )
    """Variables updated by the plants model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        flora: Flora,
        canopy_layers: int,
        soil_layers: int,
        constants: PlantsConsts = PlantsConsts(),
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        # Save the class attributes
        self.flora = flora
        """A flora containing the plant functional types used in the plants model."""
        self.constants = constants
        """Set of constants for the plants model"""
        self.communities = PlantCommunities(data, self.flora)
        """Initialise the plant communities from the data object."""
        self.canopy_layers = canopy_layers
        """The maximum number of canopy layers."""
        self.soil_layers = soil_layers
        """The number of soil layers."""

        # Initialise and then update the canopy layers.
        # TODO - this initialisation step may move somewhere else at some point.
        self.data = initialise_canopy_layers(
            data=data,
            n_canopy_layers=self.canopy_layers,
            n_soil_layers=self.soil_layers,
        )
        """A reference to the global data object."""
        self.update_canopy_layers()

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

        # Get required init arguments from config
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]

        # Load in the relevant constants
        constants = load_constants(config, "plants", "PlantsConsts")

        # Generate the flora
        flora = Flora.from_config(config=config)

        # Try and create the instance - safeguard against exceptions from __init__
        try:
            inst = cls(
                data=data,
                update_interval=update_interval,
                flora=flora,
                constants=constants,
                canopy_layers=canopy_layers,
                soil_layers=soil_layers,
            )
        except Exception as excep:
            LOGGER.critical(
                f"Error creating plants model from configuration: {str(excep)}"
            )
            raise excep

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
        self.update_canopy_layers()

    def cleanup(self) -> None:
        """Placeholder function for plants model cleanup."""

    def update_canopy_layers(self) -> None:
        """Update the canopy structure for the plant communities.

        This method calculates the canopy structure from the current state of the plant
        communities and then updates the ``layer_heights`` and ``leaf_area_index``
        arrays in the data object.
        """
        # Retrive the canopy model arrays and insert into the data object.
        canopy_heights, canopy_lai, canopy_fapar = build_canopy_arrays(
            self.communities,
            n_canopy_layers=self.canopy_layers,
        )

        # Insert the canopy layers into the data objects
        canopy_idx = np.arange(1, self.canopy_layers + 1)
        self.data["leaf_fapar"][canopy_idx, :] = canopy_fapar
        self.data["layer_heights"][canopy_idx, :] = canopy_heights
        self.data["leaf_area_index"][canopy_idx, :] = canopy_lai
