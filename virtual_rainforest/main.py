"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from copy import deepcopy
from typing import Any, Optional, Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.model import MODEL_REGISTRY


# TODO - WORK OUT WHAT THIS FUNCTION SHOULD ACTUALLY RETURN
# SHOULD BE A LIST But question is what type the list should contain
# TODO - ADD TESTS FOR THIS FUNCTION
def select_models(config: dict[str, Any]) -> Optional[list]:
    """TODO - WRITE A SENSIBLE DOCSTRING!"""

    model_list = deepcopy(config["core"]["modules"])

    # Remove "core" from model list as it is not a model
    if "core" in model_list:
        model_list.remove("core")

    # Make list of missing models, and return an error if necessary
    miss_model = [model for model in model_list if model not in MODEL_REGISTRY.keys()]
    if miss_model != []:
        LOGGER.error(
            f"The following models cannot be configured as they are not found in the "
            f"registry: {miss_model}"
        )
    return None

    # Then look for each model in the registry
    for model in model_list:
        # CAN ALL OF THESE BE DONE IN ONE STEP???
        # OR DOES FACTORY HAVE TO BE DONE ONE BY ONE??
        print(MODEL_REGISTRY[model])


# TODO - Add tests for this function
def vr_run(
    cfg_paths: Union[str, list[str]], output_folder: str, out_file_name: str
) -> None:
    """Perform a virtual rainforest simulation.

    This is a high-level function that runs a virtual rainforest simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        output_folder: Folder to save combined configuration to
        out_file_name: Name for the combined configuration file
    """

    config = validate_config(cfg_paths, output_folder, out_file_name)

    # TODO - Extract input data required to initialise the models

    # TODO -  SELECT MODELS TO BE RUN
    select_models(config)

    # TODO - Initialise the set of configured models

    # TODO - Save model state

    # TODO - Add timing loop
    # TODO - Find models to update
    # TODO - Solve models to steady state
    # TODO - Save model state

    LOGGER.info("Virtual rainforest model run completed!")


# TODO - Define command line entry point
