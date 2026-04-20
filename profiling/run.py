"""Runs the virtual ecosystem `ve_run_cli()`.

This script is encapsulated on its own as to run the code with an intentionally specified version of Python version declared in the `main.py` file."""

import argparse
from virtual_ecosystem.entry_points import ve_run_cli


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script that runs VE via cProfile")
    parser.add_argument("--ver", required=True, type=str)
    parser.add_argument("--path", required=False, type=str)
    parser.add_argument("--truncate", required=False, type=int)
    args = parser.parse_args()

    ver = args.ver
    path = args.path if args.path else "."
    truncate = args.truncate

    ve_run_args = [
        f"{path}/config",
        "--out",
        f"{path}/out",
        "--logfile",
        f"{path}/logfile{ver}.log",
    ]
    if truncate >= 0:
        ve_run_args.extend(
            ["--config", f"core.debug.truncate_run_at_update={truncate}"]
        )

    ve_run_cli(ve_run_args)
