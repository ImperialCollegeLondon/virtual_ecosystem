#!/usr/bin/env bash
# Bash script to update all notebooks used in the documentation.
# To reduce build times the notebooks included in the documentation don't update
# automatically when the documentation runs and instead just show their saved output.
# However, if major changes are made to model we would want to update all of the relevant
# notebooks, so this script exists to simplify the process.

# This should be kept upto date manually as we may want to add notebooks that never get
# updated, in which case we wouldn't want to use autodiscovery
NOTEBOOKS=(
  "./using_the_ve/virtual_ecosystem_in_static_mode.ipynb"
  "./using_the_ve/virtual_ecosystem_in_use.ipynb"
)

# Loop over notebooks, loading, executing and saving each one in turn
for notebook in "${NOTEBOOKS[@]}"; do

  jupyter nbconvert \
    --to notebook \
    --execute \
    --inplace \
    --ExecutePreprocessor.timeout=600 \
    --ExecutePreprocessor.kernel_name=python3 \
    "${notebook}"
done