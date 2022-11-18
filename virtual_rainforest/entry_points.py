"""The `virtual_rainforest.entry_points` module.

This module defines the entry points to the virtual_rainforest package. At the moment a
single entry point is defined `vr_run`, which simply configures and runs a virtual
rainforest simulation based on a set of configuration files.
"""

import argparse
import textwrap

import virtual_rainforest as vr
from virtual_rainforest.main import vr_run


# TODO - WORK OUT THE TYPE HERE
def _vr_run_cli() -> None:
    """Configure and run a Virtual Rainforest simulation.

    This program sets up and runs a simulation of the Virtual Rainforest model. At
    present this is incomplete. At the moment a set of configuration files are read in
    based on user supplied paths, these are converted to a single configuration file,
    which is then output for further reference. This combined configuration is then used
    to initialise a set of models.
    """

    # Check function docstring exists, as -OO flag strips docstrings I believe
    desc = textwrap.dedent(_vr_run_cli.__doc__ or "Python in -OO mode: no docs")
    fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc, formatter_class=fmt)

    parser.add_argument(
        "cfg_paths", help="Paths to config files and/or folders.", nargs="*"
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        default=".",
        type=str,
        help="Folder that the output config file should be saved in.",
        dest="output_folder",
    )
    parser.add_argument(
        "-n",
        "--name_outfile",
        type=str,
        default="vr_full_model_configuration",
        help="Name that the output config file should be saved under.",
        dest="out_file_name",
    )

    # TODO - WORK OUT HOW TO ADD VERSION INFO HERE
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=vr.__version__),
    )

    args = parser.parse_args()

    # Run the virtual rainforest run function
    vr_run(args.cfg_paths, args.output_folder, args.out_file_name)
