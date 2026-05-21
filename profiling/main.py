"""Running `cProfile` on the Virtual Ecosystem via the `ve_run_cli()`.

Call this script in the terminal with `python profiling/main.py` after installing the
specified Python version in a virtual environment with dependencies.

Note: profiling uses the example data. Make sure the example data is installed at
data/ve_example (`ve_run --install-example data/`).
"""

import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

import virtual_ecosystem as ve

# Identify the Python version currently running in the venv:
ver = f"{sys.version_info.major}.{sys.version_info.minor}"

# How many timesteps to run for the profiling:
truncation = 3

# Designate the path from the root directory:
path = Path.cwd() / "data" / "ve_example"

# Check example data exists to start the simulation:
if not (config_path := path / "config").exists():
    raise FileNotFoundError(
        f"Config folder not found at {config_path}. Please ensure the path variable is"
        " correctly set and the config folder exists."
    )

# Create a folder for the cProfile outputs:
profiler_folder = path / "cProfile_outputs"
profiler_folder.mkdir(parents=True, exist_ok=True)

# Create a folder for the VE outputs, removing it first if it exists already:
if (out_folder := path / "out").exists():
    shutil.rmtree(out_folder)
out_folder.mkdir(parents=True)

# Get the command for the current Python version.
command = sys.executable

# Identify the version of the virtual ecosystem being run.
print(f"Virtual Ecosystem v{ve.__version__}")

# Create the name for the cProfile output file.
output_name = f"VE_{ve.__version__}__py{ver}__truncated_at_step_{truncation}"
profiler_output = os.path.join(profiler_folder, f"{output_name}.prof")

# Generate terminal command to run `ve_run_cli()` via cProfile.
command_ve_run = [
    command,
    "-m",
    "cProfile",
    "-o",
    profiler_output,
    "profiling/run.py",
    f"--ver={ver}",
    f"--path={path}",
    f"--truncate={truncation}",
]

# Run the terminal command within this script via the `subprocess` library.
subprocess.run(command_ve_run, check=True)

# The terminal command if you want to view the results table and/or visual breakdown.
print(f"python -m snakeviz {profiler_output}")

# Note: the `time_stamp` variable cannot contain colons (:) in Windows as these are not
# valid characters for that OS.
time_stamp = (datetime.datetime.now()).strftime("%Y-%m-%d_at_%H-%M")

# Copy over the output to a nested folder sorted by Python version for historic runs.
nested_profiler_folder = f"{profiler_folder}/python{ver}"
if not os.path.exists(nested_profiler_folder):
    os.makedirs(nested_profiler_folder)
shutil.copy(
    profiler_output,
    f"{nested_profiler_folder}/{time_stamp}__{output_name}.prof",
)
