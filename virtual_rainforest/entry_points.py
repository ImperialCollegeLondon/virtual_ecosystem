"""The :mod:`~virtual_rainforest.entry_points`  module defines the command line entry
points to the virtual_rainforest package. At the moment a single entry point is defined
`vr_run`, which simply configures and runs a virtual rainforest simulation based on a
set of configuration files.
"""  # noqa D210, D415

import argparse
import textwrap
from pathlib import Path

import virtual_rainforest as vr
from virtual_rainforest.core.config import ConfigurationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.main import vr_run


def _vr_run_cli() -> None:
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
    desc = textwrap.dedent(_vr_run_cli.__doc__ or "Python in -OO mode: no docs")
    fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc, formatter_class=fmt)

    parser.add_argument("cfg_paths", type=str, help="Paths to config files", nargs="*")
    parser.add_argument(
        "-m",
        "--merge",
        type=str,
        default="./vr_full_model_configuration.toml",
        help="Path for merged config file.",
        dest="merge_file_path",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=vr.__version__),
    )

    args = parser.parse_args()

    if not args.cfg_paths:
        to_raise = ConfigurationError(
            "Configuration paths must be provided! See vr_run --help"
        )
        LOGGER.critical(to_raise)
        raise to_raise
    else:
        # Run the virtual rainforest run function
        vr_run(args.cfg_paths, Path(args.merge_file_path))
