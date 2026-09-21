"""Run the minimal two-year full Virtual Ecosystem palm simulation.

Run this file from the repository root with::

    poetry run python tests/models/palms/run_full_palm_test.py

The simulation uses the 9x9 example climate, elevation, soil, hydrology and litter
configuration, but replaces the example tree plant inputs with the canonical palm
inputs in ``tests/data``:

* ``palm_pfts.csv`` contains the palm traits used by the palm validator.
* ``palm_cohort_data.csv`` contains one cohort in each of the 81 cells.
* ``palm_plant_data.nc`` contains palm plant forcing and zero animal/herbivory fluxes.

The animal model is deliberately not configured. The zero animal and herbivory arrays
in ``palm_plant_data.nc`` satisfy the input contracts of the soil and litter models.
The run uses monthly updates from January 2020 through December 2021. Simulation
outputs, including ``plants_cohort_data.csv`` and ``model_data.zarr``, are written to
a temporary directory and deleted when the script exits. The script prints the final
minimum, maximum and mean palm height as a quick smoke-test result.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from virtual_ecosystem.main import Progress, ve_run

REPO_ROOT = Path(__file__).parents[3]
EXAMPLE_CONFIG = REPO_ROOT / "virtual_ecosystem" / "example_data" / "config"
PALM_DATA = REPO_ROOT / "tests" / "data"


def build_configuration(output_path: Path) -> str:
    """Build the run configuration using canonical inputs and example model configs.

    Args:
        output_path: Temporary directory receiving the model outputs.

    Returns:
        A TOML configuration string for the palm-specific parts of the run. The
        caller combines it with the example climate, hydrology, soil and litter
        configuration files when calling :func:`virtual_ecosystem.main.ve_run`.
    """
    plant_data_path = PALM_DATA / "palm_plant_data.nc"
    pft_path = PALM_DATA / "palm_pfts.csv"
    cohort_path = PALM_DATA / "palm_cohort_data.csv"

    variables = [
        "plant_pft_propagules",
        "downward_shortwave_radiation",
        "subcanopy_vegetation_biomass",
        "subcanopy_seedbank_biomass",
        "animal_pom_consumption_cnp",
        "fungal_fruiting_bodies_consumed_cnp",
        "decomposed_excrement_cnp",
        "decomposed_carcasses_cnp",
        "herbivory_waste_above_cnp",
        "herbivory_waste_below_cnp",
        "herbivory_waste_above_lignin",
        "herbivory_waste_below_lignin",
        "litter_consumed_above_metabolic_cnp",
        "litter_consumed_above_structural_cnp",
        "litter_consumed_woody_cnp",
        "litter_consumed_below_metabolic_cnp",
        "litter_consumed_below_structural_cnp",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
    ]
    data_config = "\n".join(
        f'[[core.data.variable]]\nfile_path = "{plant_data_path.as_posix()}"\n'
        f'var_name = "{variable}"\n'
        for variable in variables
    )

    return f"""
[core]
[core.grid]
cell_nx = 9
cell_ny = 9
[core.timing]
start_date = "2020-01-01"
update_interval = "1 month"
run_length = "2 years"
[core.data_output_options]
out_path = "{output_path.as_posix()}"

[palms]
pft_definitions_path = "{pft_path.as_posix()}"
cohort_data_path = "{cohort_path.as_posix()}"
[palms.community_data_export]
required_data = ["cohorts"]

{data_config}
"""


def main() -> None:
    """Run the full model and report the resulting palm height trajectory.

    Inputs remain in ``tests/data``. Only the generated TOML configuration and model
    outputs are temporary, so running this script does not modify repository data.
    """
    with TemporaryDirectory() as temporary_directory:
        output_path = Path(temporary_directory)
        config_path = output_path / "full_palm_config.toml"
        config_path.write_text(build_configuration(output_path))

        ve_run(
            cfg_paths=[
                EXAMPLE_CONFIG / "data_config.toml",
                EXAMPLE_CONFIG / "abiotic_simple_config.toml",
                EXAMPLE_CONFIG / "hydrology_config.toml",
                EXAMPLE_CONFIG / "soil_config.toml",
                EXAMPLE_CONFIG / "litter_config.toml",
                config_path,
            ],
            progress=Progress.SILENT,
        )

        cohort_output = pd.read_csv(output_path / "plants_cohort_data.csv")
        final = cohort_output[
            cohort_output["time_index"] == cohort_output["time_index"].max()
        ]
        print("SIM_OK full 9x9 palm run, monthly, two years")
        print(
            "final_height_m_min_max_mean="
            f"{final['stem_height_value'].min():.5f},"
            f"{final['stem_height_value'].max():.5f},"
            f"{final['stem_height_value'].mean():.5f}"
        )


if __name__ == "__main__":
    main()
