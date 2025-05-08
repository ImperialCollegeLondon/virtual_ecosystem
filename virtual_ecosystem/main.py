"""The :mod:`~virtual_ecosystem.main` module defines the function used to run a full
simulation of the model, along with helper functions to validate and configure the
model.
"""  # noqa: D205

import os
from collections.abc import Sequence
from itertools import chain
from pathlib import Path
from typing import Any

from tqdm import tqdm

from virtual_ecosystem.core import variables
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data, merge_continuous_data_files
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER, add_file_logger, remove_file_logger


def initialise_models(
    config: Config,
    data: Data,
    core_components: CoreComponents,
    models: dict[str, Any],  # FIXME -> dict[str, Type[BaseModel]]
) -> dict[str, Any]:  # FIXME -> dict[str, Type[BaseModel]]
    """Initialise a set of models for use in a `virtual_ecosystem` simulation.

    Args:
        config: A validated Virtual Ecosystem model configuration object.
        data: A Data instance.
        core_components: A CoreComponents instance.
        models: A dictionary of models to be configured.

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    LOGGER.info("Initialising models: {}".format(",".join(models.keys())))

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = {}
    for model_name, model_class in models.items():
        try:
            this_model = model_class.from_config(data, core_components, config)
            models_cfd[model_name] = this_model
        except (InitialisationError, ConfigurationError):
            failed_models.append(model_name)

    # If any models fail to configure inform the user about it
    if failed_models:
        to_raise = InitialisationError(
            f"Configuration failed for models: {','.join(failed_models)}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return models_cfd


def ve_run(
    cfg_paths: str | Path | Sequence[str | Path] = [],
    cfg_strings: str | list[str] = [],
    override_params: dict[str, Any] = {},
    logfile: Path | None = None,
    progress: bool = False,
) -> None:
    """Perform a Virtual Ecosystem simulation.

    This is a high-level function that runs a Virtual Ecosystem simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        cfg_strings: An alternate string providing TOML formatted configuration data
        override_params: Extra parameters provided by the user
        logfile: An optional path to a log file, otherwise logging will print to the
            console.
        progress: A logical switch to turn on simple progress reporting, mostly for
            visual confirmation of progress when the log is not printed to the console.
    """

    if progress:
        print("Starting Virtual Ecosystem simulation.")

    # Switch from console logging to file logging
    if logfile is not None:
        add_file_logger(logfile)
        if progress:
            print(f"* Logging to: {logfile}")

    if progress:
        print("* Loading configuration")

    variables.register_all_variables()
    config = Config(
        cfg_paths=cfg_paths, cfg_strings=cfg_strings, override_params=override_params
    )

    # Save the merged config if requested
    data_opt = config["core"]["data_output_options"]
    if data_opt["save_merged_config"]:
        outfile = Path(data_opt["out_path"]) / data_opt["out_merge_file_name"]
        config.export_config(outfile)
        if progress:
            print(f"* Saved compiled configuration: {outfile}")

    # Build core elements
    grid = Grid.from_config(config)
    core_components = CoreComponents(config=config)
    if progress:
        print("* Built core model components")

    data = Data(grid)
    data.load_data_config(config)
    if progress:
        print("* Initial data loaded")

    # Setup the variables for the requested modules and verify consistency
    variables.setup_variables(
        list(config.model_classes.values()), list(data.data.keys())
    )

    # Verify that all variables have the correct axis
    variables.verify_variables_axis()

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    # Get the model initialisation sequence and initialise
    init_sequence = {
        model_name: config.model_classes[model_name]
        for model_name in variables.get_model_order("init")
    }

    models_init = initialise_models(
        config=config,
        data=data,
        core_components=core_components,
        models=init_sequence,
    )
    if progress:
        print(f"* Models initialised: {', '.join(init_sequence.keys())}")

    LOGGER.info("All models successfully intialised.")

    # TODO - A model spin up might be needed here in future

    # Create output folder if it does not exist
    out_path = Path(config["core"]["data_output_options"]["out_path"])
    os.makedirs(out_path, exist_ok=True)

    # Save the initial state of the model
    if config["core"]["data_output_options"]["save_initial_state"]:
        data.save_to_netcdf(
            out_path / config["core"]["data_output_options"]["out_initial_file_name"]
        )
        if progress:
            print("* Saved model inital state")

    # If no path for saving continuous data is specified, fall back on using out_path
    if "out_folder_continuous" not in config["core"]["data_output_options"]:
        config["core"]["data_output_options"]["out_folder_continuous"] = str(out_path)

    # Container to store paths to continuous data files
    continuous_data_files = []

    # Only variables in the data object that are updated by a model should be output
    all_variables = (model.vars_updated for model in models_init.values())
    # Then flatten the list to generate list of variables to output
    variables_to_save = list(chain.from_iterable(all_variables))

    # Take the models in their current execution sequence and change to the model update
    # sequence
    models_update = {
        model_name: models_init[model_name]
        for model_name in variables.get_model_order("update")
    }
    if progress:
        print("* Starting simulation")

    # Setup the timing loop
    pbar = tqdm(total=core_components.model_timing.n_updates)
    time_index = 0
    current_time = core_components.model_timing.start_time
    while current_time < core_components.model_timing.end_time:
        LOGGER.info(f"Starting update {time_index}: {current_time}")

        current_time += core_components.model_timing.update_interval

        # Run update() method for every model
        for model in models_update.values():
            LOGGER.info(f"Updating model {model.model_name}")
            model.update(time_index)

        # With updates complete increment the time_index
        time_index += 1

        # Append updated data to the continuous data file
        if config["core"]["data_output_options"]["save_continuous_data"]:
            outfile_path = data.output_current_state(
                variables_to_save, config["core"]["data_output_options"], time_index
            )
            continuous_data_files.append(outfile_path)

        pbar.update(n=1)

    pbar.close()

    if progress:
        print("* Simulation completed")

    # Merge all files together based on a list
    if config["core"]["data_output_options"]["save_continuous_data"]:
        merge_continuous_data_files(
            config["core"]["data_output_options"], continuous_data_files
        )
        if progress:
            print("* Merged time series data")

    # Save the final model state
    if config["core"]["data_output_options"]["save_final_state"]:
        data.save_to_netcdf(
            out_path / config["core"]["data_output_options"]["out_final_file_name"]
        )
        if progress:
            print("* Saved final model state")

    LOGGER.info("Virtual Ecosystem model run completed!")

    # Restore default logging settings
    if logfile is not None:
        remove_file_logger()

    if progress:
        print("Virtual Ecosystem run complete.")
