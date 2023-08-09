"""The :mod:`~virtual_rainforest.models.litter.litter_model` module creates a
:class:`~virtual_rainforest.models.litter.litter_model.LitterModel` class as a child of
the :class:`~virtual_rainforest.core.base_model.BaseModel` class. At present a lot of
the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.setup` and
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.litter.litter_model.LitterModel.from_config` exists in
a more complete state, and unpacks a small number of parameters from our currently
pretty minimal configuration dictionary. These parameters are then used to generate a
class instance. If errors crop here when converting the information from the config
dictionary to the required types (e.g. :class:`~numpy.timedelta64`) they are caught and
then logged, and at the end of the unpacking an error is thrown. This error should be
caught and handled by downstream functions so that all model configuration failures can
be reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import numpy as np
from pint import Quantity

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import check_valid_constant_names, set_layer_roles
from virtual_rainforest.models.litter.constants import LitterConsts
from virtual_rainforest.models.litter.litter_pools import calculate_litter_pool_updates


class LitterModel(BaseModel):
    """A class defining the litter model.

    This model can be configured based on the data object and a config dictionary. At
    present the underlying model this class wraps is quite simple (i.e. two litter
    pools), but this will get more complex as the Virtual Rainforest develops.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The number of canopy layers to be modelled.
        constants: Set of constants for the litter model.
    """

    model_name = "litter"
    """An internal name used to register the model and schema"""
    lower_bound_on_time_scale = "30 minutes"
    """Shortest time scale that the litter model can sensibly capture."""
    upper_bound_on_time_scale = "3 months"
    """Longest time scale that the litter model can sensibly capture."""
    required_init_vars = (
        ("litter_pool_above_metabolic", ("spatial",)),
        ("litter_pool_above_structural", ("spatial",)),
        ("litter_pool_woody", ("spatial",)),
    )
    """Required initialisation variables for the litter model.

    This is a set of variables that must be present in the data object used to create a
    LitterModel , along with any core axes that those variables must map on to."""
    vars_updated = [
        "litter_pool_above_metabolic",
        "litter_pool_above_structural",
        "litter_pool_woody",
    ]
    """Variables updated by the litter model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: int,
        canopy_layers: int,
        constants: LitterConsts,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        # Check that litter pool data is appropriately bounded
        if (
            np.any(data["litter_pool_above_metabolic"] < 0.0)
            or np.any(data["litter_pool_above_structural"] < 0.0)
            or np.any(data["litter_pool_woody"] < 0.0)
        ):
            to_raise = InitialisationError(
                "Initial litter pools contain at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.constants = constants
        """Set of constants for the litter model"""

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)
        # Find first soil layer from the list of layer roles
        self.top_soil_layer_index = next(
            i for i, v in enumerate(layer_roles) if v == "soil"
        )
        """The layer in the data object representing the first soil layer."""
        # Find first soil layer from the list of layer roles
        self.surface_layer_index = next(
            i for i, v in enumerate(layer_roles) if v == "surface"
        )
        """The layer in the data object representing the surface layer."""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> LitterModel:
        """Factory function to initialise the litter model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]

        # Check if any constants have been supplied
        if "litter" in config and "constants" in config["litter"]:
            # Checks that constants in config are as expected
            check_valid_constant_names(config, "litter", "LitterConsts")
            # If an error isn't raised then generate the dataclass
            constants = LitterConsts(**config["litter"]["constants"]["LitterConsts"])
        else:
            # If no constants are supplied then the defaults should be used
            constants = LitterConsts()

        LOGGER.info(
            "Information required to initialise the litter model successfully "
            "extracted."
        )
        return cls(data, update_interval, soil_layers, canopy_layers, constants)

    def setup(self) -> None:
        """Placeholder function to setup up the litter model."""

        # TODO - At some point this could be used to calculate an initial litter input
        # rate so that the soil model can be run before the litter model. Think we need
        # to decide how we are handling model order first though.

    def spinup(self) -> None:
        """Placeholder function to spin up the litter model."""

    def update(self, time_index: int) -> None:
        """Calculate changes in the litter pools and use them to update the pools.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        # Find litter pool updates using the litter pool update function
        updated_litter_pools = calculate_litter_pool_updates(
            surface_temp=self.data["air_temperature"][
                self.surface_layer_index
            ].to_numpy(),
            constants=self.constants,
            update_interval=self.update_interval.to("day").magnitude,
            above_metabolic=self.data["litter_pool_above_metabolic"].to_numpy(),
            above_structural=self.data["litter_pool_above_structural"].to_numpy(),
            woody=self.data["litter_pool_woody"].to_numpy(),
        )

        # Update the litter pools
        self.data.add_from_dict(updated_litter_pools)

    def cleanup(self) -> None:
        """Placeholder function for litter model cleanup."""
