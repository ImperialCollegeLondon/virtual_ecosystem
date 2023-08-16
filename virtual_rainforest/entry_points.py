"""The :mod:`~virtual_rainforest.entry_points`  module defines the command line entry
points to the virtual_rainforest package. At the moment a single entry point is defined
`vr_run`, which simply configures and runs a virtual rainforest simulation based on a
set of configuration files.
"""  # noqa D210, D415
import argparse
import sys
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import virtual_rainforest as vr
from virtual_rainforest import example_data_path
from virtual_rainforest.core.config import config_merge
from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.main import vr_run

if sys.version_info[:2] >= (3, 11):
    import tomllib
    from tomllib import TOMLDecodeError
else:
    import tomli as tomllib
    from tomli import TOMLDecodeError


def _parse_param_str(s: str) -> dict[str, Any]:
    """Parse a single parameter string into a dict.

    For example: hydrology.initial_soil_moisture=0.3

    Raises:
        ConfigurationError: If the command-line parameters are not valid TOML
    """
    try:
        return tomllib.loads(s)
    except TOMLDecodeError:
        to_raise = ConfigurationError("Invalid format for command-line parameters")
        LOGGER.critical(to_raise)
        raise to_raise


def _parse_command_line_params(
    params_str: Sequence[str], override_params: dict[str, Any]
) -> None:
    """Parse extra parameters provided with command-line arguments.

    Args:
        params_str: Extra parameters in string format (e.g. my.parameter=0.2)
        override_params: Dictionary to be appended to with additional parameters

    Raises:
        ConfigurationError: Invalid format for parameters or conflicting values supplied
    """
    conflicts: tuple = ()
    for param_str in params_str:
        param_dict = _parse_param_str(param_str)
        override_params, conflicts = config_merge(
            override_params, param_dict, conflicts
        )

    if conflicts:
        to_raise = ConfigurationError(
            "Conflicting values supplied for command-line arguments"
        )
        LOGGER.critical(to_raise)
        raise to_raise


def vr_run_cli() -> None:
    """Configure and run a Virtual Rainforest simulation.

    This program sets up and runs a simulation of the Virtual Rainforest model. At
    present this is incomplete. At the moment a set of configuration files are read in
    based on user supplied paths, these are converted to a single configuration file,
    which is then output for further reference. This combined configuration is then used
    to initialise a set of models.

    The command accepts one or more paths to config files or folders containing config
    files (cfg_paths). The set of config files found in those locations are then
    combined and validated to make sure that they contain a complete and consistent
    configuration for a virtual_rainforest simulation. The resolved complete
    configuration is then written to a single consolidated config file (--merge). If a
    specific location isn't provided via the --merge option, the consolidated file is
    saved in the folder `vr_run` was called in under the name
    `vr_full_model_configuration.toml`.
    """

    # Check function docstring exists, as -OO flag strips docstrings I believe
    desc = textwrap.dedent(vr_run_cli.__doc__ or "Python in -OO mode: no docs")
    fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc, formatter_class=fmt)

    parser.add_argument("cfg_paths", type=str, help="Paths to config files", nargs="*")
    parser.add_argument(
        "-o", "--outpath", type=str, help="Path for output files", dest="outpath"
    )
    parser.add_argument(
        "-m",
        "--merge",
        type=str,
        default="./vr_full_model_configuration.toml",
        help="Path for merged config file.",
        dest="merge_file_path",
    )
    parser.add_argument(
        "-p",
        "--param",
        type=str,
        action="append",
        help="Value for additional parameter (in the form parameter.name=something)",
        dest="params",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run Virtual Rainforest with example data",
        dest="example",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=vr.__version__),
    )

    args = parser.parse_args()

    cfg_paths: list[str] = []
    if args.example:
        cfg_paths.append(example_data_path)
    if args.cfg_paths:
        cfg_paths.extend(args.cfg_paths)

    if not cfg_paths:
        to_raise = ConfigurationError(
            "Configuration paths must be provided! See vr_run --help"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    override_params: dict[str, Any] = {}
    if args.outpath:
        # Set the output path
        override_params |= {"core": {"data_output_options": {"out_path": args.outpath}}}
    if args.params:
        # Parse any extra parameters passed using the --param flag
        _parse_command_line_params(args.params, override_params)

    # Run the virtual rainforest run function
    vr_run(cfg_paths, override_params, Path(args.merge_file_path))
