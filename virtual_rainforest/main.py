"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from copy import deepcopy
from typing import Any, Optional, Type, Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.model import MODEL_REGISTRY, BaseModel, InitialisationError


def select_models(model_list: list[str]) -> Optional[list[Type[BaseModel]]]:
    """Select the models to be run for a specific virtual rainforest simulation.

    This function looks for models from a list of models, if these models can all be
    found in the registry then they are returned. Otherwise an error is logged, which
    should be handled appropriately downstream.

    Args:
        model_list: A list of models to select

    Returns:
        modules: A set of models to be configured
    """

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
    modules = [MODEL_REGISTRY[model] for model in model_list]

    return modules


def configure_models(
    config: dict[str, Any], model_list: list[Type[BaseModel]]
) -> list[BaseModel]:
    """Configure a set of models for use in a `virtual_rainforest` simulation.

    Args:
        config: The full virtual rainforest configuration
        modules: A set of models to be configured

    Returns:
        models_cfd: A set of configured models
    """

    # Use factory methods to configure the desired models
    models_cfd = [model.factory(config) for model in model_list]
    return models_cfd


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

    model_list = select_models(deepcopy(config["core"]["modules"]))

    if model_list is None:
        log_and_raise(
            "Could not find all the desired models, ending the simulation.",
            InitialisationError,
        )
        return
    else:
        LOGGER.info(
            "All models found in the registry, now attempting to configure them."
        )

    models_cfd = configure_models(config, model_list)

    # TODO - DECIDE WHETHER TO CONTINUE HERE
    # IS THIS A POINT FOR A TRY, EXPECT, FINALLY?
    # NEED TO CHECK AT A LOWER LEVEL TO SEE IF ERRORS CAN BE BETTER HANDLED

    print(models_cfd)

    # TODO - Extract input data required to initialise the models

    # TODO - Initialise the set of configured models

    # TODO - Save model state

    # TODO - Add timing loop
    # TODO - Find models to update
    # TODO - Solve models to steady state
    # TODO - Save model state

    LOGGER.info("Virtual rainforest model run completed!")


# TODO - Define command line entry point
