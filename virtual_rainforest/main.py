"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from copy import deepcopy
from typing import Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.model import MODEL_REGISTRY


# TODO - WORK OUT WHAT THIS FUNCTION SHOULD ACTUALLY RETURN
def select_models(model_list: list[str]) -> None:
    """TODO - WRITE A SENSIBLE DOCSTRING!"""

    # Remove "core" from model list as it is not a model
    if "core" in model_list:
        model_list.remove("core")

    # Then look for each model in the registry
    for model in model_list:
        print(MODEL_REGISTRY[model])

    # SOME KIND OF ERROR FOR MODEL NOT FOUND
    # IDEALLY CATCH THEM ALL IN ONE


# TODO - Add tests for this function
def vr_run(
    cfg_paths: Union[str, list[str]], output_folder: str, out_file_name: str
) -> None:
    """Perform a virtual rainforest simulation.

    This is a high-level function that runs a virtual rainforest simulation. At the
    moment this is fairly limited, and just involves validating an input configuration.
    Down the line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        output_folder: Folder to save combined configuration to
        out_file_name: Name for the combined configuration file
    """

    config = validate_config(cfg_paths, output_folder, out_file_name)

    # TODO - Add in additional model details

    # TODO -  SELECT MODELS TO BE RUN
    select_models(deepcopy(config["core"]["modules"]))

    # TODO - Save model state

    # TODO - Add timing loop
    # TODO - Find models to update
    # TODO - Solve models to steady state
    # TODO - Save model state

    LOGGER.info("Virtual rainforest model run completed!")
    print(config)


# TODO - Define command line entry point
