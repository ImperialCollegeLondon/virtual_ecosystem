"""The ``models.litter.inputs`` module handles the partitioning of plant matter into the
various pools of the litter model. This plant matter comes from both natural tissue
death as well as from mechanical inefficiencies in herbivory.
"""  # noqa: D205

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray, zeros_like

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.litter.model_config import LitterConstants


@dataclass(frozen=True)
class LitterInputs:
    """The full set input flows to the litter model."""

    leaf_mass: DataArray
    """Total leaf input rate to litter of each nutrient [kg m^-2 day^-1]"""
    root_mass: DataArray
    """Total root input rate to litter of each nutrient [kg m^-2 day^-1]"""
    deadwood_mass: DataArray
    """Total deadwood input rate to litter of each nutrient [kg m^-2 day^-1]"""

    leaf_lignin: DataArray
    """Lignin proportion of leaf input [kg{lignin C} kg{C}^-1]"""
    root_lignin: DataArray
    """Lignin proportion of root input [kg{lignin C} kg{C}^-1]"""
    stem_lignin: DataArray
    """Lignin proportion of deadwood input [kg{lignin C} kg{C}^-1]"""

    leaves_meta_split: DataArray
    """Fraction of leaf input that goes to metabolic litter [unitless]"""
    roots_meta_split: DataArray
    """Fraction of leaf input that goes to metabolic litter [unitless]"""

    woody: DataArray
    """Total input rate to the woody litter pool [kg{C} m^-2 day^-1]"""
    above_metabolic: DataArray
    """Total input rate to the above ground metabolic litter pool [kg{C} m^-2 day^-1]"""
    above_structural: DataArray
    """Total input rate to the above ground structural litter pool [kg{C} m^-2 day^-1]"""
    below_metabolic: DataArray
    """Total input rate to the below ground metabolic litter pool [kg{C} m^-2 day^-1]"""
    below_structural: DataArray
    """Total input rate to the below ground structural litter pool [kg{C} m^-2 day^-1]"""

    @classmethod
    def create_from_data(
        cls, data: Data, constants: LitterConstants, update_interval: float
    ) -> LitterInputs:
        """Factory method to populate the various litter input flows.

        This method first combines the two different input streams for dead plant matter
        (plant tissue death and herbivory waste) to find the total input of each plant
        biomass type. This is then used to find the split between metabolic and
        structural litter pools for each plant matter class (expect deadwood). Finally,
        the total rate of flow to each litter pool is calculated.

        Args:
            data: The `Data` object to be used to populate the litter input details.
            constants: Set of constants for the litter model.
            update_interval: The length of time over which the input is being added over
                [days]

        Returns:
            An LitterInputs instance containing the total input of each plant biomass
            type, the proportion of the input that goes to the relevant metabolic pool
            for each input type (expect deadwood) and the total input into each litter
            pool.
        """

        # Find the total input for each plant matter type
        total_input = combine_input_sources(data, update_interval=update_interval)

        # Find the plant inputs to each of the litter pools
        metabolic_splits = calculate_metabolic_proportions_of_input(
            total_input=total_input, constants=constants
        )

        plant_inputs = partion_plant_inputs_between_pools(
            total_input=total_input,
            metabolic_splits=metabolic_splits,
        )

        return LitterInputs(**metabolic_splits, **plant_inputs, **total_input)


def convert_to_input_masses_to_rates_per_area(
    input_mass: DataArray, cell_area: float, update_interval: float
) -> DataArray:
    """Helper function to convert input masses to rates per area.

    The plant model stores plant biomass in units of mass (kg) per grid square,
    whereas in the litter model we need everything as input rates per area.

    Args:
        input_mass: The mass of the input [kg]
        cell_area: The size of the grid cell [m^2]
        update_interval: The length of time over which the input is being added over
            [days]

    Returns:
        The input as a per area input rate [kg m^-2 day^-1]
    """
    return input_mass / (cell_area * update_interval)


def combine_input_sources(data: Data, update_interval: float) -> dict[str, DataArray]:
    """Combine the plant death and herbivory inputs into a single total input.

    The total input for each plant matter type (leaves, roots, deadwood) is returned,
    the chemical concentration of each of these new pools is also calculated.

    This function also converts the plant inputs from total inputs (over the model time
    step), to the (per area) input rates needed by the litter model.

    Args:
        data: The `Data` object to be used to populate the litter input streams.
        update_interval: The length of time over which the input is being added over
            [days]

    Returns:
        A dictionary containing the combined rate at which each input pools is added to
        [kg{C} m^-2 day^-1], as well as the carbon to nitrogen ratios [unitless], carbon
        to phosphorus ratios [unitless] and lignin proportions [kg{lignin C} kg{C}^-1]
        of each of these pools.
    """

    # Calculate totals for each plant matter type, collapsing PFTs for leaf inputs
    leaf_rates = convert_to_input_masses_to_rates_per_area(
        data["foliage_turnover_cnp"].sum(dim="pft") + data["herbivory_waste_leaf_cnp"],
        cell_area=data.grid.cell_area,
        update_interval=update_interval,
    )
    root_rates = convert_to_input_masses_to_rates_per_area(
        data["root_turnover_cnp"],
        cell_area=data.grid.cell_area,
        update_interval=update_interval,
    )
    deadwood_rates = convert_to_input_masses_to_rates_per_area(
        data["stem_turnover_cnp"],
        cell_area=data.grid.cell_area,
        update_interval=update_interval,
    )

    # Calculate lignin concentrations for each combined pool
    foliage_mass = data["foliage_turnover_cnp"].sel(element="C").sum(dim="pft")

    leaf_lignin = merge_input_lignin_proportions(
        turnover_mass=foliage_mass,
        herbivory_waste_mass=data["herbivory_waste_leaf_cnp"].sel(element="C"),
        total_mass=(foliage_mass + data["herbivory_waste_leaf_cnp"].sel(element="C")),
        turnover_lignin_proportion=data["senesced_leaf_lignin"],
        herbivory_waste_lignin_proportion=data["herbivory_waste_leaf_lignin"],
    )
    root_lignin = data["root_lignin"]
    stem_lignin = data["stem_lignin"]

    return {
        "leaf_mass": leaf_rates,
        "deadwood_mass": deadwood_rates,
        "root_mass": root_rates,
        "leaf_lignin": leaf_lignin,
        "root_lignin": root_lignin,
        "stem_lignin": stem_lignin,
    }


def calculate_metabolic_proportions_of_input(
    total_input: dict[str, DataArray], constants: LitterConstants
) -> dict[str, DataArray]:
    """Calculate the proportion of each input type that flows to the metabolic pool.

    This function is used for roots, leaves and reproductive tissue, but not deadwood
    because everything goes into a single woody litter pool. It is not used for animal
    inputs either as they all flow into just the metabolic pool.

    Args:
        total_input: The total amount of carbon in each input pools [kg{C} m^-3], as
            well as the nitrogen content [kg{N} m^-3], phosphorus content [kg{P} m^-3]
            and lignin proportions [kg{lignin C} kg{C}^-1] of each of these pools.
        constants: Set of constants for the litter model.

    Returns:
        A dictionary containing the proportion of the input that goes to the relevant
        metabolic pool. This is for three input types: leaves, reproductive tissues and
        roots [unitless]
    """

    # Calculate split of each input biomass type
    leaves_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        input_masses=total_input["leaf_mass"],
        lignin_proportion=total_input["leaf_lignin"],
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
    )

    roots_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        input_masses=total_input["root_mass"],
        lignin_proportion=total_input["root_lignin"],
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
    )

    return {
        "leaves_meta_split": leaves_metabolic_split,
        "roots_meta_split": roots_metabolic_split,
    }


def partion_plant_inputs_between_pools(
    total_input: dict[str, DataArray],
    metabolic_splits: dict[str, DataArray],
) -> dict[str, DataArray]:
    """Function to partition input biomass between the various litter pools.

    All deadwood is added to the woody litter pool. Leaf biomass is split between the
    above ground metabolic and structural pools based on lignin concentration and carbon
    nitrogen ratios. Root biomass is split between the below ground metabolic and
    structural pools based on lignin concentration and carbon nitrogen ratios.

    Args:
        total_input: The the total pool size for each input pools [kg{C} m^-3], as
            well as the carbon to nitrogen ratios [unitless], carbon to phosphorus
            ratios [unitless] and lignin proportions [kg{lignin C} kg{C}^-1] of each of
            these pools.
        metabolic_splits: Dictionary containing the proportion of each input that
            goes to the relevant metabolic pool. This is for three input types:
            leaves, reproductive tissues and roots [unitless]

    Returns:
        A dictionary containing the rate of biomass flow into each of the five litter
        pools (woody, above ground metabolic, above ground structural, below ground
        metabolic and below ground structural) [kg{C} m^-2 day^-1]
    """

    # Calculate input to each of the five litter pools
    woody_input = total_input["deadwood_mass"].sel(element="C")
    above_ground_metabolic_input = metabolic_splits["leaves_meta_split"] * total_input[
        "leaf_mass"
    ].sel(element="C")
    above_ground_strutural_input = (
        1 - metabolic_splits["leaves_meta_split"]
    ) * total_input["leaf_mass"].sel(element="C")
    below_ground_metabolic_input = metabolic_splits["roots_meta_split"] * total_input[
        "root_mass"
    ].sel(element="C")
    below_ground_structural_input = (
        1 - metabolic_splits["roots_meta_split"]
    ) * total_input["root_mass"].sel(element="C")

    return {
        "woody": woody_input,
        "above_metabolic": above_ground_metabolic_input,
        "above_structural": above_ground_strutural_input,
        "below_metabolic": below_ground_metabolic_input,
        "below_structural": below_ground_structural_input,
    }


def split_pool_into_metabolic_and_structural_litter(
    input_masses: DataArray,
    lignin_proportion: DataArray,
    max_metabolic_fraction: float,
    split_sensitivity_nitrogen: float,
    split_sensitivity_phosphorus: float,
):
    """Calculate the split of input biomass between metabolic and structural pools.

    This division depends on the lignin, nitrogen and phosphorus contents of the input
    biomass, the functional form is taken from :cite:t:`parton_dynamics_1988`.

    Args:
        input_masses: Mass of each nutrient in the input biomass [kg{C} m^-2]
        lignin_proportion: Proportion of input biomass carbon that is lignin
            [kg{lignin C} kg{C}^-1]
        max_metabolic_fraction: Fraction of pool that becomes metabolic litter for the
            easiest to breakdown case, i.e. no lignin, ample nitrogen [unitless]
        split_sensitivity_nitrogen: Sets how rapidly the split changes in response to
            changing lignin and nitrogen contents [unitless]
        split_sensitivity_phosphorus: Sets how rapidly the split changes in response to
            changing lignin and phosphorus contents [unitless]

    Raises:
        ValueError: If any values of lignin proportion are not between zero and one
            (which breaks the logic of this function)

    Returns:
        The fraction of the biomass that goes to the metabolic pool [unitless]
    """

    # First check that lignin proportions are between zero and one (if they aren't that
    # screws up the logic)
    if np.any((lignin_proportion < 0.0) | (lignin_proportion > 1.0)):
        to_raise = ValueError("Lignin proportion not between 0 and 1 (inclusive)!")
        LOGGER.error(to_raise)
        raise to_raise

    # Extract the specific nutrient masses from the summary
    input_carbon = input_masses.sel(element="C").to_numpy()
    input_nitrogen = input_masses.sel(element="N").to_numpy()
    input_phosphorus = input_masses.sel(element="P").to_numpy()

    # Calculate carbon:nitrogen and carbon:phosphorus ratios based on the input
    # biomasses
    carbon_nitrogen_ratio = np.divide(
        input_carbon,
        input_nitrogen,
        out=np.full_like(input_carbon, np.inf, dtype=float),
        where=input_nitrogen != 0,
    )
    carbon_phosphorus_ratio = np.divide(
        input_carbon,
        input_phosphorus,
        out=np.full_like(input_carbon, np.inf, dtype=float),
        where=input_phosphorus != 0,
    )

    metabolic_fraction = max_metabolic_fraction - lignin_proportion * (
        split_sensitivity_nitrogen * carbon_nitrogen_ratio
        + split_sensitivity_phosphorus * carbon_phosphorus_ratio
    )

    # This is a naive prevention of negative metabolic fraction rates.
    # TODO: full solution in Issue #1010.
    metabolic_fraction = np.where(metabolic_fraction < 0, 0.0, metabolic_fraction)
    # Another naive prevention of metabolic fractions that are so large that all lignin
    # cannot flow to the structural pool
    # TODO: full solution again in Issue #1010.
    metabolic_fraction = np.where(
        metabolic_fraction > 1 - lignin_proportion,
        1 - lignin_proportion,
        metabolic_fraction,
    )

    return metabolic_fraction


def merge_input_lignin_proportions(
    turnover_mass: DataArray,
    herbivory_waste_mass: DataArray,
    total_mass: DataArray,
    turnover_lignin_proportion: DataArray,
    herbivory_waste_lignin_proportion: DataArray,
) -> DataArray:
    """Merge the lignin proportions of two input sources to the same litter pool.

    Args:
        turnover_mass: Input mass coming from the natural turnover of plant tissue
            [kg{C}]
        herbivory_waste_mass: Input mass coming from the mechanical inefficiencies of
            herbivory [kg{C}]
        total_mass: The combined mass of the two input sources [kg{C}]
        turnover_lignin_proportion: Proportion of lignin in the input mass from
            natural plant turnover [unitless]
        herbivory_waste_lignin_proportion: Proportion of lignin in the input mass from
            mechanical inefficiencies of herbivory [unitless]

    Returns:
        The proportion of carbon that is lignin carbon in the total mass of the new
        combined input stream [kg{lignin C} kg{C}^-1]
    """

    return (
        turnover_lignin_proportion * turnover_mass
        + herbivory_waste_lignin_proportion * herbivory_waste_mass
    ) / (total_mass)


def average_nutrient_ratios(
    mass_1: NDArray[np.floating],
    mass_2: NDArray[np.floating],
    nutrient_ratio_1: NDArray[np.floating],
    nutrient_ratio_2: NDArray[np.floating],
):
    """Average carbon to nutrient ratios weighted by their carbon content.

    Args:
        mass_1: Total carbon mass of the first pool/input stream
            [kg{C} m^-2 or kg{C} m^-2]
        mass_2: Total carbon mass of the second pool/input stream
            [kg{C} m^-2 or kg{C} m^-2]
        nutrient_ratio_1: Carbon to nutrient ratio of the first pool/input stream
            [unitless]
        nutrient_ratio_2: Carbon to nutrient ratio of the second pool/input stream
            [unitless]

    Returns:
        The nutrient ratio of the new combined pool/input stream [unitless]
    """

    return (mass_1 + mass_2) / (
        (mass_1 / nutrient_ratio_1) + (mass_2 / nutrient_ratio_2)
    )


@dataclass(frozen=True)
class InputChemistries:
    """Dataclass containing the chemistry for the input to each litter pool."""

    above_metabolic_nitrogen: DataArray
    """Nitrogen input rate to the aboveground metabolic pool [kg{N} m^-2 day^-1]"""
    above_structural_nitrogen: DataArray
    """Nitrogen input rate to the aboveground structural pool [kg{N} m^-2 day^-1]"""
    woody_nitrogen: DataArray
    """Nitrogen input rate to the woody pool [kg{N} m^-2 day^-1]"""
    below_metabolic_nitrogen: DataArray
    """Nitrogen input rate to the belowground metabolic pool [kg{N} m^-2 day^-1]"""
    below_structural_nitrogen: DataArray
    """Nitrogen input rate to the belowground structural pool [kg{N} m^-2 day^-1]"""

    above_metabolic_phosphorus: DataArray
    """Phosphorus input rate to the aboveground metabolic pool [kg{P} m^-2 day^-1]"""
    above_structural_phosphorus: DataArray
    """Phosphorus input rate to the aboveground structural pool [kg{P} m^-2 day^-1]"""
    woody_phosphorus: DataArray
    """Phosphorus input rate to the woody pool [kg{P} m^-2 day^-1]"""
    below_metabolic_phosphorus: DataArray
    """Phosphorus input rate to the belowground metabolic pool [kg{P} m^-2 day^-1]"""
    below_structural_phosphorus: DataArray
    """Phosphorus input rate to the belowground structural pool [kg{P} m^-2 day^-1]"""

    above_structural_lignin: DataArray
    """Lignin proportion of input to the aboveground structural pool.
    
    Units of [kg{lignin C} kg{C}^-1]
    """
    woody_lignin: DataArray
    """Lignin proportion of input to the woody pool [kg{lignin C} kg{C}^-1]"""
    below_structural_lignin: DataArray
    """Lignin proportion of input to the belowground structural pool.
     
    Units of [kg{lignin C} kg{C}^-1]
    """


def calculate_input_chemistries(
    litter_inputs: LitterInputs,
    meta_to_struct_nitrogen_ratio: float,
    meta_to_struct_phosphorus_ratio: float,
) -> InputChemistries:
    """Calculate the chemistries of the input to each litter pool.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.
        meta_to_struct_nitrogen_ratio: Ratio of nitrogen concentrations for inputs to
            the metabolic and structural litter pools [unitless]
        meta_to_struct_phosphorus_ratio: Ratio of phosphorus concentrations for inputs
            to the metabolic and structural litter pools [unitless]

    Returns:
        An InputChemistries instance containing the input chemistry for each litter pool
    """

    # Find lignin and nitrogen contents of the litter input flows
    input_lignin = calculate_litter_input_lignin_concentrations(
        litter_inputs=litter_inputs,
    )
    input_c_n_ratios = calculate_litter_input_nutrient_masses(
        litter_inputs=litter_inputs,
        meta_to_struct_nutrient_ratio=meta_to_struct_nitrogen_ratio,
        nutrient="nitrogen",
    )
    input_c_p_ratios = calculate_litter_input_nutrient_masses(
        litter_inputs=litter_inputs,
        meta_to_struct_nutrient_ratio=meta_to_struct_phosphorus_ratio,
        nutrient="phosphorus",
    )

    return InputChemistries(**input_lignin, **input_c_n_ratios, **input_c_p_ratios)


def calculate_litter_input_lignin_concentrations(
    litter_inputs: LitterInputs,
) -> dict[str, DataArray]:
    """Calculate the concentration of lignin for each plant biomass to litter flow.

    By definition the metabolic litter pools do not contain lignin, so all input
    lignin flows to the structural and woody pools. As the input biomass gets split
    between pools, the lignin concentration of the input to the structural pools
    will be higher than it was in the input biomass.

    For the woody litter there's no structural-metabolic split so the lignin
    concentration of the litter input is the same as that of the dead wood
    production. For the below ground structural litter, the total lignin content of
    root input must be found, this is then converted back into a concentration
    relative to the input into the below structural litter pool. For the above
    ground structural litter pool, the same approach is taken using leaf lignin.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.

    Returns:
        Dictionary containing the lignin concentration of the input to each of the
        three lignin containing litter pools (woody, above and below ground
        structural) [kg{lignin C} kg{C}^-1]
    """

    lignin_proportion_woody = litter_inputs.stem_lignin

    lignin_proportion_below_structural = (
        litter_inputs.root_lignin
        * litter_inputs.root_mass.sel(element="C")
        / litter_inputs.below_structural
    )

    lignin_proportion_above_structural = (
        litter_inputs.leaf_lignin
        * litter_inputs.leaf_mass.sel(element="C")
        / litter_inputs.above_structural
    )

    return {
        "woody_lignin": lignin_proportion_woody,
        "below_structural_lignin": lignin_proportion_below_structural,
        "above_structural_lignin": lignin_proportion_above_structural,
    }


def calculate_litter_input_nutrient_masses(
    litter_inputs: LitterInputs, meta_to_struct_nutrient_ratio: float, nutrient: str
) -> dict[str, DataArray]:
    """Calculate the nutrient mass for each plant biomass to litter flow.

    Input to the woody litter pool just matches the nutrient masses of the
    deadwood input. For the other pools, the split of nutrient flows from root/leaf
    turnover between the metabolic and structural pools is calculated.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.
        meta_to_struct_nutrient_ratio: Ratio of the nutrient concentrations (relative to
            carbon mass) for the inputs to the metabolic and structural litter pools
            [unitless]
        nutrient: Nutrient to calculate flows for (options are nitrogen and phosphorus)

    Returns:
        Dictionary containing input rates of the nutrients (nitrogen or phosphorus) into
        each of the pools [kg{nutrient} m^-2 day^-1]
    """

    if nutrient not in {"nitrogen", "phosphorus"}:
        to_raise = ValueError(f"{nutrient} is not an element we currently track!")
        LOGGER.error(to_raise)
        raise to_raise

    # TODO - This will need a more sophisticated approach if we start tracking potassium
    element_symbol = nutrient[0].upper()

    # Calculate nutrient split for each (non-wood) input biomass type
    root_nutrient_meta, root_nutrient_struct = find_nutrient_split_between_litter_pools(
        input_carbon_rate=litter_inputs.root_mass.sel(element="C"),
        input_nutrient_rate=litter_inputs.root_mass.sel(element=element_symbol),
        metabolic_split=litter_inputs.roots_meta_split,
        meta_to_struct_nutrient_ratio=meta_to_struct_nutrient_ratio,
    )

    leaf_nutrient_meta, leaf_nutrient_struct = find_nutrient_split_between_litter_pools(
        input_carbon_rate=litter_inputs.leaf_mass.sel(element="C"),
        input_nutrient_rate=litter_inputs.leaf_mass.sel(element=element_symbol),
        metabolic_split=litter_inputs.leaves_meta_split,
        meta_to_struct_nutrient_ratio=meta_to_struct_nutrient_ratio,
    )

    return {
        f"woody_{nutrient}": litter_inputs.deadwood_mass.sel(element=element_symbol),
        f"below_metabolic_{nutrient}": root_nutrient_meta,
        f"below_structural_{nutrient}": root_nutrient_struct,
        f"above_metabolic_{nutrient}": leaf_nutrient_meta,
        f"above_structural_{nutrient}": leaf_nutrient_struct,
    }


def find_nutrient_split_between_litter_pools(
    input_carbon_rate: DataArray,
    input_nutrient_rate: DataArray,
    metabolic_split: DataArray,
    meta_to_struct_nutrient_ratio: float,
) -> tuple[DataArray, DataArray]:
    """Function to find the split of input nutrients between litter pools.

    Following :cite:t:`kirschbaum_modelling_2002`, we assume that the nutrient
    concentrations of inputs to the structural and metabolic litter pools are in a fixed
    proportion. This ratio can vary between nutrients but doesn't vary between above and
    below ground pools. This simplifying assumption allows us to capture litter
    mineralisation dynamics for specific elements without having to build (and
    parametrise) a model where every nutrient effects decay rate of every pool.

    This function explicitly handle the edge case where there is no carbon flow to
    structural litter. How this is done depends on whether there is a carbon flow to
    metabolic litter. If there is, then all nutrient flow goes to the metabolic litter.
    If there isn't, then there is no nutrient flow to either pool.

    Args:
        input_carbon_rate: Rate of carbon input [kg{C} m^-2 day^-1]
        input_nutrient_rate: Rate of nutrient input [kg{nutrient} m^-2 day^-1]
        metabolic_split: Proportion of organic matter input that flows to the metabolic
            litter pool [unitless]
        meta_to_struct_nutrient_ratio: Ratio of the nutrient concentrations (relative to
            carbon mass) for the inputs to the metabolic and structural litter pools
            [unitless]

    Returns:
        A tuple containing the nutrient input rate to the metabolic and structural
        litter pools [kg{nutrient} m^-2 day^-1], in that order.
    """

    # Calculate rate of carbon input to each pool
    carbon_input_meta = input_carbon_rate * metabolic_split
    carbon_input_struct = input_carbon_rate * (1 - metabolic_split)

    meta_nutrient_mass = zeros_like(carbon_input_meta)
    struct_nutrient_mass = zeros_like(carbon_input_struct)

    # Defining masks to avoid zero flow edge cases
    struct_input = carbon_input_struct != 0
    only_meta_input = (carbon_input_meta != 0) & (carbon_input_struct == 0)

    # Calculate actual split in cases where there is flow to the structural pool
    meta_nutrient, struct_nutrient = calculate_nutrient_split(
        carbon_input_meta.where(struct_input),
        carbon_input_struct.where(struct_input),
        input_nutrient_rate.where(struct_input),
        meta_to_struct_nutrient_ratio,
    )

    # Zero values get replaced if there is a flow to that pool (otherwise kept as zero)
    meta_nutrient_mass = meta_nutrient_mass.where(~struct_input, other=meta_nutrient)
    struct_nutrient_mass = struct_nutrient_mass.where(
        ~struct_input, other=struct_nutrient
    )

    # If all carbon goes to metabolic litter all nutrients do as well
    meta_nutrient_mass = meta_nutrient_mass.where(
        ~only_meta_input, input_nutrient_rate.where(only_meta_input)
    )

    return (meta_nutrient_mass, struct_nutrient_mass)


def calculate_nutrient_split(
    carbon_input_meta: DataArray,
    carbon_input_struct: DataArray,
    input_nutrient_rate: DataArray,
    meta_to_struct_nutrient_ratio: float,
) -> tuple[DataArray, DataArray]:
    """Calculate the split of nutrients between metabolic and structural litter pools.

    The calculation of this split derives from :cite:t:`kirschbaum_modelling_2002`, and
    assumes that the nutrient concentrations of inputs to the structural and metabolic
    litter pools are in a fixed proportion.

    Args:
        carbon_input_meta: Rate of carbon input to the metabolic pool
            [kg{C} m^-2 day^-1]
        carbon_input_struct: Rate of carbon input to the structural pool
            [kg{C} m^-2 day^-1]
        input_nutrient_rate: Total rate of nutrient input [kg{nutrient} m^-2 day^-1]
        meta_to_struct_nutrient_ratio: Ratio of the nutrient concentrations (relative to
            carbon mass) for the inputs to the metabolic and structural litter pools
            [unitless]

    Returns:
        A tuple containing the rate of nutrient flow to the metabolic and structural
        litter pools, respectively [kg{nutrient} m^-2 day^-1]
    """

    # Find ratio of the carbon contents of the two pools
    ratio_meta_to_struct = carbon_input_meta / carbon_input_struct

    # The product of the ratio of carbon inputs and the ratio of the nutrient
    # concentrations is found and used to calculate the nutrient mass in each litter
    # pool
    product_of_ratios = ratio_meta_to_struct * meta_to_struct_nutrient_ratio

    struct_nutrient_mass = input_nutrient_rate / (1 + product_of_ratios)
    meta_nutrient_mass = product_of_ratios * struct_nutrient_mass

    return meta_nutrient_mass, struct_nutrient_mass
