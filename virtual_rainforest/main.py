"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from typing import Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER


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

    print(config)

    LOGGER.info("Virtual rainforest model run completed!")


# def _vr_run_cli
