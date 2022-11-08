"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from copy import deepcopy
from typing import Any, Optional, Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.model import MODEL_REGISTRY, BaseModel


# TODO - ADD TESTS FOR THIS FUNCTION
def select_models(config: dict[str, Any]) -> Optional[list[BaseModel]]:
    """TODO - WRITE A SENSIBLE DOCSTRING!

    EXPLAIN BASIC IDEA, THEN WHAT HAPPENS IF IT SUCCEEDS, AND WHAT HAPPENS IF IT FAILS
    EXPLAIN ARGS AND RETURNS.
    """

    model_list = deepcopy(config["core"]["modules"])

    # Remove "core" from model list as it is not a model
    if "core" in model_list:
        model_list.remove("core")

    LOGGER.info(f"Attempting to configure the following models: {model_list}")

    # Make list of missing models, and return an error if necessary
    miss_model = [model for model in model_list if model not in MODEL_REGISTRY.keys()]
    if miss_model != []:
        LOGGER.error(
            f"The following models cannot be configured as they are not found in the "
            f"registry: {miss_model}"
        )
        return None

    # Then look for each model in the registry
    temp_models = [MODEL_REGISTRY[model] for model in model_list]

    # Use factory methods to configure the following models
    confd_models = [model.factory(config) for model in temp_models]

    return confd_models


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

    # TODO -  SELECT MODELS TO BE RUN
    models = select_models(config)
    # LOG INFO ON SUCCESS, OR OTHERWISE END THIS PROGRAM
    print(models)

    # TODO - Extract input data required to initialise the models

    # TODO - Initialise the set of configured models

    # TODO - Save model state

    # TODO - Add timing loop
    # TODO - Find models to update
    # TODO - Solve models to steady state
    # TODO - Save model state

    LOGGER.info("Virtual rainforest model run completed!")


# TODO - Define command line entry point
