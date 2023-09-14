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
from shutil import copytree, ignore_patterns
from typing import Any, Optional

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


def install_example_directory(install_dir: Path) -> None:
    """Install the example directory to a location.

    This function installs the example directory data files and configuration files
    provided within the package to a selected location. This allows users to look at the
    simulation directory structure and files more easily and avoids working with the
    original files inside the package tree.

    The files are installed to a ``vr_example`` directory within the provided install
    location.

    Args:
        install_dir: the installation path.
    """
    if not install_dir.is_dir():
        sys.stderr.write("--install-example path is not a valid directory.")

    example_dir = install_dir / "vr_example"
    if example_dir.exists():
        sys.stderr.write(
            "VR example directory already present in --install-example path.\n"
        )

    copytree(example_data_path, example_dir, ignore=ignore_patterns("__*"))

    print(f"Example directory created at:\n{example_dir}\n")


def vr_run_cli(args_list: Optional[list[str]] = None) -> None:
    """Configure and run a Virtual Rainforest simulation.

    This program sets up and runs a Virtual Rainforest simulation. The program expects
    to be provided with paths to TOML formatted configuration files for the simulation.
    The configuration is modular: a directory path can be used to add all TOML
    configuration files in the directory, or individual file paths can be used to select
    specific combinations of configuration files. These are combined and validated and
    then used to initialise and run the model.

    As an alternative to providing configuration paths, the `--install-example` option
    allows users to provide a location where a simple example set of datasets and
    configuration files provided with the Virtual Rainforest package can be installed.
    This option will create a `vr_example` directory in the location, and users can
    examine the input files and run the simulation from that directory:

    `vr_run /provided/install/path/vr_example`

    The output directory for simulation results is typically set in the configuration
    files, but can be overwritten using the `--outpath` option. A log file path can be
    provided for logging output - if this is not provided the log will be written to the
    console.

    The resolved complete configuration will then be written to a single consolidated
    config file in the output path with a default name of
    `vr_full_model_configuration.toml`. This can be disabled by setting the
    `core.data_output_options.save_merged_config` option to false.

    Args:
        args_list: This is a developer and testing facing argument that is used to
            simulate command line arguments, allowing this function to be called
            directly. For example, ``vr_run --install-example /usr/abc`` can be
            replicated by calling ``vr_run_cli(['--install-example', '/usr/abc/'])``.
    """

    # If no arguments list is provided
    if args_list is None:
        args_list = sys.argv[1:]

    # Check function docstring exists to safeguard against -OO mode, and strip off the
    # description of the function args_list, which should not be included in the command
    # line docs
    if vr_run_cli.__doc__ is not None:
        desc = textwrap.dedent("\n".join(vr_run_cli.__doc__.splitlines()[:-7]))
    else:
        desc = "Python in -OO mode: no docs"

    fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc, formatter_class=fmt)

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=vr.__version__),
    )

    parser.add_argument("cfg_paths", type=str, help="Paths to config files", nargs="*")

    parser.add_argument(
        "--install-example",
        type=Path,
        help="Install the Virtual Rainforest example data to the given location",
        dest="install_example",
    )

    parser.add_argument(
        "-o", "--outpath", type=str, help="Path for output files", dest="outpath"
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
        "--logfile",
        type=Path,
        help="A file path to use for logging a Virtual Rainforest simulation",
        default=None,
    )

    args = parser.parse_args(args=args_list)

    # Cannot use both install example and paths
    if args.cfg_paths and args.install_example:
        sys.stderr.write(
            "--install-example cannot be used in combination with configuration paths."
        )

    # Install the example directory to the provided empty location if requested
    if args.install_example:
        install_example_directory(args.install_example)
        return

    # Otherwise run with the provided  config paths
    override_params: dict[str, Any] = {}
    if args.outpath:
        # Set the output path
        outpath_opt = {"core": {"data_output_options": {"out_path": args.outpath}}}
        override_params, _ = config_merge(override_params, outpath_opt)
    if args.params:
        # Parse any extra parameters passed using the --param flag
        _parse_command_line_params(args.params, override_params)

    # Run the virtual rainforest run function
    vr_run(
        cfg_paths=args.cfg_paths,
        override_params=override_params,
        logfile=args.logfile,
    )

    print("VR run complete.\n")
