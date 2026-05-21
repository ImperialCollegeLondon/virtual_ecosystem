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

# Set custom variables.
"""Python version, can be written as "3.14" or "3_14"."""
ver = "3.12"
ver = ver.replace(".", "_")

"""How many steps to run (negative values means no truncation)."""
truncation = 3

"""The OS you are running the code on. Options: "windows", "linux", "mac"."""
user_os = "mac"


# Designate the path from the root directory.
from pathlib import Path

path = Path.cwd() / "data" / "ve_example"

# Check example data exists to start the simulation.
if not (config_path := path / "config").exists():
    raise FileNotFoundError(
        f"Config folder not found at {config_path}. Please ensure the path variable is"
        " correctly set and the config folder exists."
    )

# Create a folder for the cProfile outputs.
profiler_folder = path / "cProfile_outputs"
profiler_folder.mkdir(parents=True, exist_ok=True)

# Create a folder for the VE outputs, removing it first if it exists already.
if (out_folder := path / "out").exists():
    shutil.rmtree(out_folder)
out_folder.mkdir(parents=True)

# Clear the current ./out folder.
for filename in os.listdir(out_folder):
    file_path = os.path.join(out_folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")


# Note: the `time_stamp` variable cannot contain colons (:) in Windows as these are not
# valid characters for that OS.
time_stamp = (datetime.datetime.now()).strftime("%Y-%m-%d_at_%H-%M")

command_options = {
    "windows": f".\\.venv\\Python{ver}\\Scripts\\python.exe",
    "linux": f"./.venv/Python{ver}/bin/python",
}
command_options["mac"] = command_options["linux"]

command = command_options.get(user_os, None)
if command is None:
    raise ValueError(
        "Invalid user_os value. Please choose from 'windows', 'linux', or 'mac'."
    )

# Identify the version of the virtual ecosystem being run.
command_ve_version = [
    command,
    "-c",
    "import virtual_ecosystem as ve; print(ve.__version__)",
]
ve_version = subprocess.check_output(command_ve_version, text=True).strip().replace(
    ".",
    "_",
)
print(f"Virtual Ecosystem v{ve_version}")
# Generate terminal command to run `ve_run_cli()` via cProfile.
output_name = f"VE_{ve_version}__py{ver}__truncated_at_step_{truncation}"
profiler_output = os.path.join(profiler_folder, f"{output_name}.prof")
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

# Copy over the output to a nested folder sorted by Python version for historic runs.
nested_profiler_folder = f"{profiler_folder}/python{ver}"
if not os.path.exists(nested_profiler_folder):
    os.makedirs(nested_profiler_folder)
shutil.copy(
    profiler_output,
    f"{nested_profiler_folder}/{time_stamp}__{output_name}.prof",
)
