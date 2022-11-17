"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from typing import Any, Type, Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.model import MODEL_REGISTRY, BaseModel, InitialisationError


def select_models(model_list: list[str]) -> list[Type[BaseModel]]:
    """Select the models to be run for a specific virtual rainforest simulation.

    This function looks for models from a list of models, if these models can all be
    found in the registry then they are returned. Otherwise an error is logged, which
    should be handled appropriately downstream.

    Args:
        model_list: A list of models to select

    Raises:
        InitialisationError: If one or more models cannot be found in the registry
    """

    # Remove "core" from model list as it is not a model
    model_list_ = set(model_list) - {"core"}

    LOGGER.info(
        "Attempting to configure the following models: %s" % sorted(model_list_)
    )

    # Make list of missing models, and return an error if necessary
    miss_model = [model for model in model_list_ if model not in MODEL_REGISTRY.keys()]
    if miss_model:
        log_and_raise(
            f"The following models cannot be configured as they are not found in the "
            f"registry: {miss_model}",
            InitialisationError,
        )

    # Then extract each model from the registry
    modules = [MODEL_REGISTRY[model] for model in model_list_]

    return modules


def configure_models(
    config: dict[str, Any], model_list: list[Type[BaseModel]]
) -> list[BaseModel]:
    """Configure a set of models for use in a `virtual_rainforest` simulation.

    Args:
        config: The full virtual rainforest configuration
        modules: A set of models to be configured

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = []
    for model in model_list:
        try:
            models_cfd.append(model.from_config(config))
        except InitialisationError:
            failed_models.append(model.name)

    # If any models fail to configure inform the user about it
    if failed_models:
        log_and_raise(
            f"Could not configure all the desired models, ending the simulation. The "
            f"following models failed: {failed_models}.",
            InitialisationError,
        )

    return models_cfd


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

    model_list = select_models(config["core"]["modules"])

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    models_cfd = configure_models(config, model_list)

    LOGGER.info(
        "All models successfully configured, now attempting to initialise them."
    )

    # This is just a step to pass flake8 checks (DELETE LATER)
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
