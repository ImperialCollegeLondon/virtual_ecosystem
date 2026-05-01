"""Running the Virtual Ecosystem via the `ve_run_cli()` with a specified Python version, then saving the profiling outs from `cProfile`.

Call this script in the terminal with `python profiling/main.py` after installing the specified Python version is installed in a virtual environment with dependencies.

Managing virtual environments:
1) Create a local `.venv/` folder.
2) To create a virtual environment for, e.g., Python 3.12, make sure you have it installed globally and then run the command `python3.12 -m venv .venv/Python3_12`.
3) To run the virtual-ecosystem with this virtual environment, activate it with a command like `source .venv/Python3_12/bin/activate` and then run `poetry install`.
* The specific command to activate your virtual environment will vary based on your OS.
4) Run `python profiling/main.py` in any Python terminal.

See the general Python docs for further information on virtual environments and installation: https://docs.python.org/dev/tutorial/venv.html#tut-venv
"""

import datetime
import os
import shutil
import subprocess

# Set custom variables.
"""Python version, can be written as "3.14" or "3_14"."""
ver = "3.13"
ver = ver.replace(".", "_")

"""How many steps to run, can be an integer where negative values means no truncation."""
truncation = 0

"""The OS you are running the code on. Options: "windows", "linux", "mac"."""
user_os = "windows"


# Designate the path from the root directory.
path = "data/ve_example"

# Check example data exists to start the simulation.
if not os.path.exists(f"{path}/config"):
    raise FileNotFoundError(
        f"Config folder not found at {path}/config. Please ensure the path variable is correctly set and the config folder exists."
    )

# Create a folder for the cProfile outputs.
profiler_folder = f"{path}/cProfile_outputs"
if not os.path.exists(profiler_folder):
    os.makedirs(profiler_folder)

# Create a folder for the VE outputs.
out_folder = f"{path}/out"
if not os.path.exists(out_folder):
    os.makedirs(out_folder)

# Clear the current ./out folder.
for filename in os.listdir(out_folder):
    file_path = os.path.join(out_folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print("Failed to delete %s. Reason: %s" % (file_path, e))


# Generate terminal command to run `ve_run_cli()` via cProfile.
output_name = f"VirEco__py{ver}__truncated_at_step_{truncation}"

# Note: the `time_stamp` variable cannot contain colons (:) in Windows as these are not valid characters for that OS.
time_stamp = (datetime.datetime.now()).strftime("%Y-%m-%d_at_%H-%M")

command_options = {
    "windows": f".\\.venv\\Python{ver}\\Scripts\\python.exe -m cProfile -o {profiler_folder}/{output_name}.prof profiling/run.py --ver={ver} --path={path} --truncate={truncation}",
    "linux": f"./.venv/Python{ver}/bin/python -m cProfile -o {profiler_folder}/{output_name}.prof profiling/run.py --ver={ver} --path={path} --truncate={truncation}",
}
command_options["mac"] = command_options["linux"]

command = command_options.get(user_os, None)
if command is None:
    raise ValueError(
        "Invalid user_os value. Please choose from 'windows', 'linux', or 'mac'."
    )

# Run the terminal command within this script via the `subprocess` library.
subprocess.run(command.split(), shell=True)


# The terminal command if you want to view the results table and/or visual breakdown.
print(f"python -m snakeviz {profiler_folder}/{output_name}.prof")

# Copy over the output to a nested outputs folder sorted by Python version types for historic runs.
nested_profiler_folder = f"{profiler_folder}/python{ver}"
if not os.path.exists(nested_profiler_folder):
    os.makedirs(nested_profiler_folder)
shutil.copy(
    f"{profiler_folder}/{output_name}.prof",
    f"{nested_profiler_folder}/{time_stamp}__{output_name}.prof",
)
